"""
直播流并发测速与有效性检验模块
通过直连请求（屏蔽本地代理）真实检测播放可达性与响应延迟
"""
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MAX_WORKERS, REQUEST_TIMEOUT, USER_AGENTS
from parser import ChannelStream


def test_single_stream(stream: ChannelStream, timeout: float = REQUEST_TIMEOUT) -> ChannelStream:
    """
    测试单个直播源的可用性与延迟
    """
    t0 = time.time()
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "*/*",
        "Connection": "close"
    }

    # 针对某些防盗链运营商源，尝试携带对应 Host
    session = requests.Session()
    # 关键：禁用代理环境变量，保证本地 IPv6 直连不被 Clash / V2Ray 等 IPv4 本地代理截断
    session.trust_env = False

    try:
        # stream=True 允许只读取响应头及前几个分片，避免下载完整视频流导致网络阻塞
        response = session.get(
            stream.url,
            headers=headers,
            timeout=timeout,
            stream=True,
            allow_redirects=True
        )
        latency = int((time.time() - t0) * 1000)

        # 检查 HTTP 状态码
        if response.status_code in [200, 206]:
            content_type = response.headers.get("Content-Type", "").lower()

            # 读取前 512 字节验证真实性，防止运营商重定向到 200 OK 的 HTML 拦截报错页面
            chunk = next(response.iter_content(512), b"")
            response.close()

            if len(chunk) > 0:
                chunk_str = chunk.decode("utf-8", errors="ignore").lower()
                # 排除 HTML 错误页 (如 <html><head><title>404</title>)
                if "<html" in chunk_str and ("error" in chunk_str or "forbidden" in chunk_str or "404" in chunk_str):
                    stream.is_active = False
                    stream.latency = -1
                    return stream

                # 判定为有效可用流
                stream.is_active = True
                stream.latency = latency
                return stream

    except Exception:
        pass

    stream.is_active = False
    stream.latency = -1
    return stream


def verify_streams_batch(
    streams: list[ChannelStream],
    max_workers: int = MAX_WORKERS,
    timeout: float = REQUEST_TIMEOUT,
    progress_callback=None
) -> list[ChannelStream]:
    """
    批量多线程测速与验效
    """
    active_streams = []
    total = len(streams)
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {executor.submit(test_single_stream, s, timeout): s for s in streams}

        for future in as_completed(future_map):
            completed += 1
            result_stream = future.result()
            if result_stream.is_active:
                active_streams.append(result_stream)

            if progress_callback:
                progress_callback(completed, total, len(active_streams), result_stream)

    return active_streams

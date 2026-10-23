"""
直播流并发测速与真实有效性检验模块
执行真实请求，严格检验 HTTP 状态与首段音视频切片数据，杜绝失效死链与拦截页
"""
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MAX_WORKERS, REQUEST_TIMEOUT, USER_AGENTS
from parser import ChannelStream


def test_single_stream(stream: ChannelStream, timeout: float = REQUEST_TIMEOUT) -> ChannelStream:
    """
    真实探测单个直播源的可用性与延迟
    """
    t0 = time.time()
    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "*/*",
        "Connection": "close"
    }

    session = requests.Session()
    session.trust_env = False

    try:
        response = session.get(
            stream.url,
            headers=headers,
            timeout=timeout,
            stream=True,
            allow_redirects=True
        )
        latency = int((time.time() - t0) * 1000)

        # 1. 严格检查状态码必须为 200 或 206
        if response.status_code in [200, 206]:
            content_type = response.headers.get("Content-Type", "").lower()

            # 2. 读取前 1024 字节内容进行真实流切片校验
            chunk = next(response.iter_content(1024), b"")
            response.close()

            if len(chunk) > 10:
                chunk_lower = chunk.lower()

                # 排除 HTML 报错与运营商拦截伪 200 页面
                if b"<html" in chunk_lower or b"<!doctype" in chunk_lower:
                    stream.is_active = False
                    stream.latency = -1
                    return stream

                # 必须符合流媒体规范（M3U8 包含 #EXT 标识，或 TS 包含 0x47 同步字节，或 flv 包含 FLV 头）
                is_valid_media = (
                    b"#ext" in chunk_lower or
                    chunk.startswith(b"\x47") or
                    chunk.startswith(b"FLV") or
                    "mpegurl" in content_type or
                    "video" in content_type or
                    "octet-stream" in content_type
                )

                if is_valid_media:
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
    """批量多线程测速与验效，仅返回通过实测的真有效流"""
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

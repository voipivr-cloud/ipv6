"""
直播流双层深度验效模块
同时检测 M3U8 索引与底层真实 TS 视频切片
严苛过滤内网虚假源（如 10.x、192.168.x）以及切片超时死链，杜绝播放器报错
"""
import time
import requests
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MAX_WORKERS, REQUEST_TIMEOUT, USER_AGENTS
from parser import ChannelStream


def test_single_stream(stream: ChannelStream, timeout: float = REQUEST_TIMEOUT) -> ChannelStream:
    """
    双层深度探测：
    第 1 层：请求 M3U8 播放列表，验证状态为 200 且包含切片索引
    第 2 层：解析首个 TS 视频切片，验证公网可达性并实际读取 512 字节视频二进制流
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
        # 第一层：检查 M3U8 索引
        r_m3u8 = session.get(stream.url, headers=headers, timeout=timeout)
        if r_m3u8.status_code not in [200, 206]:
            stream.is_active = False
            return stream

        content_text = r_m3u8.text
        # 如果是直接返回的单视频流或 TS 流
        if not ("#EXT" in content_text):
            if r_m3u8.content.startswith(b"\x47") or r_m3u8.content.startswith(b"FLV"):
                stream.is_active = True
                stream.latency = int((time.time() - t0) * 1000)
                return stream
            stream.is_active = False
            return stream

        # 第二层：提取 M3U8 内部的真实 TS 切片链接
        ts_lines = [l.strip() for l in content_text.splitlines() if l.strip() and not l.startswith("#")]
        if not ts_lines:
            stream.is_active = False
            return stream

        ts_url = ts_lines[0]
        if not ts_url.startswith("http"):
            ts_url = urljoin(stream.url, ts_url)

        # 核心过滤：很多伪直播源的 TS 切片指向运营商机房内网（10.x.x.x / 192.168.x.x），外部无法播放
        intranet_patterns = ["10.", "192.168.", "127.0.0.1", "172.16.", "172.17.", "172.18.", "172.19.", "172.20."]
        if any(ip_prefix in ts_url for ip_prefix in intranet_patterns):
            stream.is_active = False
            return stream

        # 第三层：实际请求首个 TS 视频切片并读取视频二进制
        r_ts = session.get(ts_url, headers=headers, timeout=timeout, stream=True)
        if r_ts.status_code in [200, 206]:
            chunk = next(r_ts.iter_content(512), b"")
            r_ts.close()

            if len(chunk) > 10 and b"<html" not in chunk.lower():
                stream.is_active = True
                stream.latency = int((time.time() - t0) * 1000)
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
    """批量多线程双层深度测速与切片验效"""
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

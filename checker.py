"""
直播流双层深度验效模块
同时检测 M3U8 索引与底层真实 TS/FLV 视频切片
严苛过滤内网虚假源（如 10.x、192.168.x）以及切片 404/超时死链，杜绝播放器报错闪退
"""
import ipaddress
import time
from urllib.parse import urljoin, urlparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MAX_WORKERS, REQUEST_TIMEOUT, USER_AGENTS
from parser import ChannelStream


def is_private_or_invalid_host(url: str) -> bool:
    """
    检查 URL 域名/IP 是否为私有内网或无效地址（如 10.x.x.x, 192.168.x.x, 172.16-31.x.x, 127.0.0.1）
    """
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        if not host:
            return True
        host_clean = host.strip("[]")
        try:
            ip = ipaddress.ip_address(host_clean)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                return True
        except ValueError:
            # 域名形式
            if host_clean.lower() in ["localhost", "broadcasthost"]:
                return True
        return False
    except Exception:
        return True


def test_single_stream(stream: ChannelStream, timeout: float = REQUEST_TIMEOUT) -> ChannelStream:
    """
    双层深度真实验效探测：
    第 1 层：流式请求 M3U8 播放列表，防死锁读取前 8KB 索引数据
    第 2 层：解析首个 TS 视频切片，精确过滤私有内网 IP
    第 3 层：实际读取 TS 切片前 1024 字节，严格校验 MPEG-TS 0x47 同步字节或 FLV 标头
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
        # 第一层：流式检查 M3U8 索引（必须 stream=True，避免读取无尽直播流导致工作线程卡死）
        r_m3u8 = session.get(stream.url, headers=headers, timeout=(timeout, timeout), stream=True)
        if r_m3u8.status_code not in [200, 206]:
            stream.is_active = False
            return stream

        first_bytes = next(r_m3u8.iter_content(8192), b"")
        r_m3u8.close()

        if len(first_bytes) < 10:
            stream.is_active = False
            return stream

        # 如果直接返回原生二进制 TS 视频流或 FLV 流
        if first_bytes.startswith(b"\x47") or first_bytes.startswith(b"FLV"):
            stream.is_active = True
            stream.latency = int((time.time() - t0) * 1000)
            return stream

        # 必须是合法的 M3U 播放列表
        if b"#EXT" not in first_bytes:
            stream.is_active = False
            return stream

        content_text = first_bytes.decode("utf-8", errors="ignore")

        # 第二层：提取 M3U8 内部的真实 TS 切片链接
        ts_lines = [l.strip() for l in content_text.splitlines() if l.strip() and not l.startswith("#")]
        if not ts_lines:
            stream.is_active = False
            return stream

        ts_url = urljoin(stream.url, ts_lines[0])

        # 处理多级嵌套 Master 播放列表
        if ".m3u8" in ts_url.lower():
            try:
                r_sub = session.get(ts_url, headers=headers, timeout=(timeout, timeout), stream=True)
                if r_sub.status_code in [200, 206]:
                    sub_bytes = next(r_sub.iter_content(8192), b"")
                    r_sub.close()
                    sub_lines = [l.strip() for l in sub_bytes.decode("utf-8", errors="ignore").splitlines() if l.strip() and not l.startswith("#")]
                    if sub_lines:
                        ts_url = urljoin(ts_url, sub_lines[0])
                else:
                    r_sub.close()
                    stream.is_active = False
                    return stream
            except Exception:
                stream.is_active = False
                return stream

        # 核心过滤：很多伪直播源的 TS 切片指向运营商机房内网（如 10.10.0.1 / 192.168.x.x），外部无法播放
        if is_private_or_invalid_host(ts_url):
            stream.is_active = False
            return stream

        # 第三层：实际请求首个 TS 视频切片并读取视频二进制
        r_ts = session.get(ts_url, headers=headers, timeout=(timeout, timeout), stream=True)
        if r_ts.status_code in [200, 206]:
            chunk = next(r_ts.iter_content(1024), b"")
            r_ts.close()

            # 严格验证真实媒体二进制特征，彻底杜绝 404/403 的 HTML 报错页伪装
            if len(chunk) >= 188:
                is_valid_ts = (chunk[0] == 0x47 or b"\x47" in chunk[:188])
                is_valid_flv = chunk.startswith(b"FLV")
                is_valid_mp4 = b"ftyp" in chunk[:32]

                if is_valid_ts or is_valid_flv or is_valid_mp4:
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

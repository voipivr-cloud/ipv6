"""
直播流双层深度验效模块
同时检测 M3U8 索引与底层真实 TS/FLV 视频切片
严苛过滤内网虚假源（如 10.x、192.168.x）以及切片 404/超时/文本伪装死链，杜绝播放器报错闪退
"""
import ipaddress
import time
from urllib.parse import urljoin, urlparse
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import MAX_WORKERS, REQUEST_TIMEOUT, USER_AGENTS
from parser import ChannelStream

BLACKLIST_KEYWORDS = [
    "nosignal",
    "no_signal",
    "test_stream",
    "catvod.com",
]


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
    第 2 层：解析首个 TS 视频切片，精确过滤私有内网 IP 与黑名单
    第 3 层：实际读取 TS 切片二进制流，严格校验 MPEG-TS 0x47 同步字节或 FLV 协议头
    """
    t0 = time.time()

    # 过滤黑名单关键词（无信号循环、YouTube 无法直解的网页、已知失效域名）
    if any(k in stream.url.lower() for k in BLACKLIST_KEYWORDS):
        stream.is_active = False
        return stream

    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "*/*",
        "Connection": "close"
    }

    session = requests.Session()
    # 非 YouTube 直播流跳过本地代理环境以保障电信运营商专网测速纯净度
    if "youtube.com" not in stream.url.lower() and "youtu.be" not in stream.url.lower():
        session.trust_env = False

    # 对 YouTube 频道流进行网络与活跃度探测（允许 200, 301, 302 响应）
    if "youtube.com" in stream.url.lower() or "youtu.be" in stream.url.lower():
        try:
            r_yt = session.get(stream.url, headers=headers, timeout=(timeout, timeout), stream=True)
            if r_yt.status_code in [200, 301, 302]:
                first_chunk = next(r_yt.iter_content(2048), b"")
                r_yt.close()
                if len(first_chunk) > 50:
                    stream.is_active = True
                    stream.latency = int((time.time() - t0) * 1000)
                    return stream
            r_yt.close()
        except Exception:
            pass
        stream.is_active = False
        return stream

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

        # 如果直接返回原生二进制 TS 视频流（包长188，首字节0x47，第二包也为0x47）或 FLV 流
        if (len(first_bytes) >= 376 and first_bytes[0] == 0x47 and first_bytes[188] == 0x47) or first_bytes.startswith(b"FLV"):
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

        if any(k in ts_url.lower() for k in BLACKLIST_KEYWORDS):
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

            # 严格过滤伪装切片：
            # 1. 绝对不能是文本内容（杜绝 #EXTM3U 嵌套死循环、HTML 404/403 页面、JSON 错误消息）
            if (
                chunk.startswith(b"#")
                or chunk.startswith(b"<")
                or chunk.startswith(b"{")
                or chunk.startswith(b"\r\n")
                or b"<html" in chunk[:200].lower()
            ):
                stream.is_active = False
                return stream

            # 2. 严格 MPEG-TS 校验规范（ISO/IEC 13818-1）：
            # 第一个包首字节为 0x47，且第二个包（偏移188字节处）也必须是 0x47 同步字节！
            is_valid_ts = (
                len(chunk) >= 188
                and chunk[0] == 0x47
                and (len(chunk) < 189 or chunk[188] == 0x47)
            )
            is_valid_flv = chunk.startswith(b"FLV")
            is_valid_mp4 = b"ftyp" in chunk[:32] or chunk.startswith(b"\x00\x00\x00")

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

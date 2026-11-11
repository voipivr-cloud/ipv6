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
    "youtube.com",
    "youtu.be",
    "googlevideo.com",
    "nosignal",
    "no_signal",
    "test_stream",
    "catvod.com",
    "/static/sailei",
]


def _is_blocked_or_private(url: str) -> bool:
    if not url or any(c.isspace() for c in url):
        return True
    if any(k in url.lower() for k in BLACKLIST_KEYWORDS):
        return True
    return is_private_or_invalid_host(url)


def _read_stream_prefix(resp, max_bytes: int = 16384, stop_on_binary: bool = False) -> bytes:
    """安全读取流前 max_bytes 字节，兼容 chunked 传输分片，对无限二进制流读取 512B 即安全截断"""
    buf = bytearray()
    for chunk in resp.iter_content(2048):
        if not chunk:
            continue
        buf.extend(chunk)
        if len(buf) >= max_bytes:
            break
        if stop_on_binary and len(buf) >= 512:
            if (buf[0] == 0x47 and buf[188] == 0x47) or buf[:3] == b"FLV":
                break
            if not buf.lstrip(b"\xef\xbb\xbf\r\n\t ").startswith(b"#EXT") and b"<" not in buf[:64]:
                # 非文本列表且非 HTML 的其他流媒体二进制头，读满 1024B 即可交给切片校验
                if len(buf) >= 1024:
                    break
    return bytes(buf[:max_bytes])


def _starts_with_extm3u(data: bytes) -> bool:
    return data.lstrip(b"\xef\xbb\xbf\r\n\t ").startswith(b"#EXTM3U")


def _extract_first_media_uri(m3u8_text: str, base_url: str) -> str:
    for raw_line in m3u8_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        return urljoin(base_url, line)
    return ""


def _is_valid_media_chunk(chunk: bytes) -> bool:
    if len(chunk) < 32:
        return False
    lower_head = chunk[:256].lstrip().lower()
    if (
        lower_head.startswith((b"#", b"<", b"{"))
        or chunk.startswith((b"\r", b"\n"))
        or b"<html" in lower_head
        or b"<!doctype" in lower_head
    ):
        return False

    is_valid_ts = (
        len(chunk) >= 188
        and chunk[0] == 0x47
        and (len(chunk) < 189 or chunk[188] == 0x47)
    )
    is_valid_flv = chunk.startswith(b"FLV")
    is_valid_mp4 = (
        b"ftyp" in chunk[:64]
        or b"styp" in chunk[:64]
        or b"moof" in chunk[:64]
        or b"sidx" in chunk[:64]
        or chunk.startswith(b"\x00\x00\x00")
    )
    return is_valid_ts or is_valid_flv or is_valid_mp4


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
    第 1 层：严格校验播放列表必须以标准 #EXTM3U 开头（或为原生 TS/FLV 流），杜绝网页/HTML 触发播放器 PARSING_MANIFEST_MALFORMED
    第 2 层：解析 Master/Variant M3U8 嵌套子列表并校验每一跳最终地址，过滤私有内网 IP、YouTube 网页与黑名单
    第 3 层：实际读取首个视频切片二进制，严格校验 MPEG-TS (0x47/0x47)、FLV 或 fMP4 协议头
    """
    t0 = time.time()

    if _is_blocked_or_private(stream.url):
        stream.is_active = False
        return stream

    headers = {
        "User-Agent": USER_AGENTS[0],
        "Accept": "*/*",
        "Connection": "close"
    }

    session = requests.Session()
    session.trust_env = False

    try:
        current_url = stream.url
        segment_url = ""

        # 最多跟随 3 级 M3U8 播放列表（支持 Master Playlist 与无 .m3u8 后缀的动态代理）
        for _ in range(3):
            if _is_blocked_or_private(current_url):
                stream.is_active = False
                return stream

            resp = session.get(current_url, headers=headers, timeout=(timeout, timeout), stream=True)
            final_url = resp.url or current_url
            if resp.status_code not in [200, 206] or _is_blocked_or_private(final_url):
                resp.close()
                stream.is_active = False
                return stream

            first_bytes = _read_stream_prefix(resp, max_bytes=16384, stop_on_binary=True)
            resp.close()

            if len(first_bytes) < 10:
                stream.is_active = False
                return stream

            # 直接返回原生二进制 TS/FLV 流（通常仅在首跳即可直接命中）
            if (len(first_bytes) >= 376 and first_bytes[0] == 0x47 and first_bytes[188] == 0x47) or first_bytes.startswith(b"FLV"):
                stream.is_active = True
                stream.latency = int((time.time() - t0) * 1000)
                return stream

            # Media3 HlsPlaylistParser 严格要求以 #EXTM3U 开头
            if not _starts_with_extm3u(first_bytes):
                # 如果已经从外层 M3U8 跳到真正的二进制切片（如无明显扩展名的 .mp4/.ts 分片），直接做二进制切片验证
                if segment_url and _is_valid_media_chunk(first_bytes):
                    stream.is_active = True
                    stream.latency = int((time.time() - t0) * 1000)
                    return stream
                stream.is_active = False
                return stream

            content_text = first_bytes.decode("utf-8", errors="ignore")
            next_uri = _extract_first_media_uri(content_text, final_url)
            if not next_uri or _is_blocked_or_private(next_uri):
                stream.is_active = False
                return stream

            segment_url = next_uri
            # 若明确为 Master Playlist 或下一跳仍指向 m3u8，则继续深入；否则跳出并按切片读取
            if "#EXT-X-STREAM-INF" in content_text or ".m3u8" in next_uri.lower():
                current_url = next_uri
                continue
            break

        if not segment_url or _is_blocked_or_private(segment_url):
            stream.is_active = False
            return stream

        # 第 3 层：实际请求首个视频切片并读取二进制头
        r_ts = session.get(segment_url, headers=headers, timeout=(timeout, timeout), stream=True)
        final_seg_url = r_ts.url or segment_url
        if r_ts.status_code in [200, 206] and not _is_blocked_or_private(final_seg_url):
            chunk = _read_stream_prefix(r_ts, max_bytes=1024)
            r_ts.close()

            # 若切片地址本身意外返回了嵌套 #EXTM3U（例如多级无 .m3u8 后缀子列表），再跟进一跳真实切片
            if _starts_with_extm3u(chunk):
                nested_text = chunk.decode("utf-8", errors="ignore")
                nested_uri = _extract_first_media_uri(nested_text, final_seg_url)
                if not nested_uri or _is_blocked_or_private(nested_uri):
                    stream.is_active = False
                    return stream
                r_ts2 = session.get(nested_uri, headers=headers, timeout=(timeout, timeout), stream=True)
                final_seg_url2 = r_ts2.url or nested_uri
                if r_ts2.status_code not in [200, 206] or _is_blocked_or_private(final_seg_url2):
                    r_ts2.close()
                    stream.is_active = False
                    return stream
                chunk = _read_stream_prefix(r_ts2, max_bytes=1024)
                r_ts2.close()

            if _is_valid_media_chunk(chunk):
                stream.is_active = True
                stream.latency = int((time.time() - t0) * 1000)
                return stream
        else:
            r_ts.close()

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

"""
直播源解析与规范化模块
支持 M3U / M3U8 与 TXT 格式的解析与数据结构转换
"""
import re
from dataclasses import dataclass, field
from config import CHANNEL_ALIASES, CLEAN_PATTERNS, GROUP_RULES, LOGO_BASE_URL
from ipv6_detector import is_ipv6_url


@dataclass
class ChannelStream:
    """直播源条目数据结构"""
    name: str                   # 规范化频道名称（如 CCTV-1）
    raw_name: str               # 原始名称（如 CCTV-1 综合[1080P]）
    url: str                    # 直播源播放地址
    group: str = "其他频道"      # 分组类别
    tvg_id: str = ""            # EPG 匹配 ID
    tvg_name: str = ""          # EPG 匹配名称
    tvg_logo: str = ""          # 台标 Logo URL
    is_ipv6: bool = False       # 是否为 IPv6 源
    ipv6_type: str = "none"     # literal / domain / none
    isp_info: str = ""          # 运营商说明
    latency: int = -1           # 测速延迟（毫秒），-1 表示未测速
    is_active: bool = False     # 是否有效可用


def normalize_channel_name(raw_name: str) -> str:
    """
    清洗并规范化频道名称
    例如: "CCTV-1 综合 [超清]" -> "CCTV-1"
    """
    if not raw_name:
        return "未知频道"

    name = raw_name.strip()

    # 1. 优先别名直接匹配（如 CCTV1 -> CCTV-1）
    cleaned_simple = re.sub(r"\s+", "", name).upper()
    if cleaned_simple in CHANNEL_ALIASES:
        return CHANNEL_ALIASES[cleaned_simple]

    # 2. 过滤清晰度标签、特殊括号内容
    cleaned = name
    for pattern in CLEAN_PATTERNS:
        cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)

    cleaned = cleaned.strip()
    cleaned_upper = cleaned.upper().replace("-", "")

    # 3. 再次检查别名
    if cleaned_upper in CHANNEL_ALIASES:
        return CHANNEL_ALIASES[cleaned_upper]

    return cleaned if cleaned else name


def classify_group(channel_name: str, existing_group: str = "") -> str:
    """
    根据频道名称和原有分组，自动划分标准类别
    """
    # 1. 优先根据频道名称匹配明确分类（如 CCTV 始终归入 央视频道，湖南卫视归入 卫视频道）
    for group_name, rule_regex in GROUP_RULES:
        if re.search(rule_regex, channel_name, re.IGNORECASE):
            return group_name

    # 2. 如果频道名无法明确匹配，但原始分组存在，清洗并使用原始分组
    if existing_group and existing_group not in ["其他频道", "未分类", "Undefined"]:
        clean_grp = re.sub(r"[^\w\u4e00-\u9fa5]", "", existing_group)
        if "央视" in clean_grp:
            return "央视频道"
        if "卫视" in clean_grp:
            return "卫视频道"
        if any(w in clean_grp for w in ["影", "剧", "片", "电影"]):
            return "影视轮播"
        if "体育" in clean_grp:
            return "体育赛事"
        if any(w in clean_grp for w in ["少儿", "动画", "卡通"]):
            return "儿童少儿"
        if "地方" in clean_grp:
            return "地方频道"
        if clean_grp:
            return clean_grp

    return "地方频道" if "台" in channel_name else "其他频道"


def parse_extinf_attributes(extinf_line: str) -> dict:
    """
    解析 #EXTINF 行中的各种 key="value" 属性及频道标题
    """
    attrs = {
        "tvg-id": "",
        "tvg-name": "",
        "tvg-logo": "",
        "group-title": "",
        "title": ""
    }

    # 提取 key="value" 或 key=value
    matches = re.findall(r'([a-zA-Z0-9_\-]+)=(?:["\'](.*?)["\']|([^,\s]+))', extinf_line)
    for key, val1, val2 in matches:
        val = val1 if val1 else val2
        attrs[key.lower()] = val.strip()

    # 提取逗号后面的频道名称
    parts = extinf_line.split(",", 1)
    if len(parts) > 1:
        attrs["title"] = parts[1].strip()

    return attrs


def parse_m3u_content(content: str, filter_ipv6: bool = True, resolve_dns: bool = True) -> list[ChannelStream]:
    """
    解析 M3U / M3U8 文本内容
    """
    streams = []
    lines = content.splitlines()

    current_meta = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("#EXTINF:"):
            current_meta = parse_extinf_attributes(line)
        elif line.startswith("http://") or line.startswith("https://") or line.startswith("rtmp://"):
            raw_title = current_meta.get("title", "") if current_meta else ""
            if not raw_title:
                raw_title = line.split("/")[-1].split("?")[0]

            norm_name = normalize_channel_name(raw_title)
            group = classify_group(norm_name, current_meta.get("group-title", "") if current_meta else "")

            # IPv6 检测
            is_v6, v6_type, isp_info = is_ipv6_url(line, resolve_dns=resolve_dns)
            if filter_ipv6 and not is_v6:
                current_meta = None
                continue

            stream = ChannelStream(
                name=norm_name,
                raw_name=raw_title,
                url=line,
                group=group,
                tvg_id=current_meta.get("tvg-id", "") if current_meta else norm_name,
                tvg_name=current_meta.get("tvg-name", "") if current_meta else norm_name,
                tvg_logo=current_meta.get("tvg-logo", "") if current_meta and current_meta.get("tvg-logo") else LOGO_BASE_URL.format(name=norm_name),
                is_ipv6=is_v6,
                ipv6_type=v6_type,
                isp_info=isp_info
            )
            streams.append(stream)
            current_meta = None

    return streams


def parse_txt_content(content: str, filter_ipv6: bool = True, resolve_dns: bool = True) -> list[ChannelStream]:
    """
    解析 TXT 格式的直播源列表（形如: 频道名称,http://...）
    """
    streams = []
    current_group = "央视频道"

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        # 分类标签: 央视频道,#genre#
        if ",#genre#" in line or "，#genre#" in line:
            current_group = line.split(",")[0].split("，")[0].strip()
            continue

        if "," in line or "，" in line:
            delim = "," if "," in line else "，"
            parts = line.split(delim, 1)
            raw_title = parts[0].strip()
            url = parts[1].strip()

            if not (url.startswith("http://") or url.startswith("https://")):
                continue

            norm_name = normalize_channel_name(raw_title)
            group = classify_group(norm_name, current_group)

            is_v6, v6_type, isp_info = is_ipv6_url(url, resolve_dns=resolve_dns)
            if filter_ipv6 and not is_v6:
                continue

            stream = ChannelStream(
                name=norm_name,
                raw_name=raw_title,
                url=url,
                group=group,
                tvg_id=norm_name,
                tvg_name=norm_name,
                tvg_logo=LOGO_BASE_URL.format(name=norm_name),
                is_ipv6=is_v6,
                ipv6_type=v6_type,
                isp_info=isp_info
            )
            streams.append(stream)

    return streams

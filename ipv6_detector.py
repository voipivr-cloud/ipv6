"""
IPv6 地址检测与识别模块
支持字面量 IPv6 格式与域名 AAAA 记录解析
"""
import re
import socket
from urllib.parse import urlparse

# IPv6 字面量正则（匹配形如 http://[2409:8087:...]:6610/path）
IPV6_LITERAL_REGEX = re.compile(
    r"^https?://\[([0-9a-fA-F:]+)\](?::\d+)?(?:/.*)?$",
    re.IGNORECASE
)

# 常见国内运营商 IPv6 地址前缀
ISP_IPV6_PREFIXES = [
    ("2408:", "中国联通"),
    ("2409:", "中国移动"),
    ("240e:", "中国电信"),
    ("2400:", "中国广电/亚太APNIC"),
    ("2001:250:", "中国教育科研网CERNET"),
    ("2001:da8:", "中国教育科研网CERNET2"),
]

# 域名解析缓存
_DNS_CACHE = {}


def check_local_ipv6_support() -> bool:
    """
    检测当前运行机器是否具备 IPv6 外部连通性
    """
    try:
        s = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        # 尝试连接 Google 公共 IPv6 DNS，不发送实际网络包
        s.connect(("2001:4860:4860::8888", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return bool(local_ip)
    except Exception:
        return False


def get_isp_name(ipv6_addr: str) -> str:
    """
    根据 IPv6 地址前缀识别运营商
    """
    addr_lower = ipv6_addr.lower()
    for prefix, isp in ISP_IPV6_PREFIXES:
        if addr_lower.startswith(prefix.lower()):
            return isp
    return "公网IPv6/未知"


def is_ipv6_url(url: str, resolve_dns: bool = True) -> tuple[bool, str, str]:
    """
    检测 URL 是否属于 IPv6 直播源

    返回: (is_ipv6: bool, mode: 'literal'|'domain'|'none', info: str)
    """
    if not url or not isinstance(url, str):
        return False, "none", ""

    url = url.strip()

    # 1. 优先检查字面量 IPv6 格式: http://[2409:8087:...]:...
    match = IPV6_LITERAL_REGEX.match(url)
    if match:
        ip = match.group(1)
        isp = get_isp_name(ip)
        return True, "literal", f"原生IPv6 ({isp}: {ip})"

    # 2. 如果包含中括号但不完全匹配正则，再次提取
    bracket_match = re.search(r"https?://\[([0-9a-fA-F:]+)\]", url)
    if bracket_match:
        ip = bracket_match.group(1)
        isp = get_isp_name(ip)
        return True, "literal", f"原生IPv6 ({isp}: {ip})"

    # 3. 对普通域名形式，可选进行 DNS AAAA 记录解析
    if resolve_dns:
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname
            if not hostname:
                return False, "none", ""

            # 排除已知 IPv4 纯数字 IP
            if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", hostname):
                return False, "none", ""

            if hostname in _DNS_CACHE:
                return _DNS_CACHE[hostname]

            # 查询 AAAA 解析记录
            addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET6)
            if addr_info:
                first_ipv6 = addr_info[0][4][0]
                isp = get_isp_name(first_ipv6)
                res = (True, "domain", f"双栈/IPv6域名 ({hostname} -> {isp})")
                _DNS_CACHE[hostname] = res
                return res
        except Exception:
            _DNS_CACHE[hostname] = (False, "none", "")
            return False, "none", ""

    return False, "none", ""

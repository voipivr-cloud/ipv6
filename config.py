"""
配置文件：多源采集、分组规则、严格验效与网络请求参数
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

OUTPUT_M3U = os.path.join(OUTPUT_DIR, "live_ipv6.m3u")
OUTPUT_TXT = os.path.join(OUTPUT_DIR, "live_ipv6.txt")
OUTPUT_REPORT = os.path.join(OUTPUT_DIR, "report.json")

EPG_URLS = [
    "https://live.fanmingming.cn/e.xml",
    "https://epg.112114.xyz/pp.xml.gz"
]
LOGO_BASE_URL = "https://live.fanmingming.cn/tv/{name}.png"

# 覆盖全网活跃更新的源池（涵盖运营商专线、高校开源、公网 CDN 源）
SOURCE_URLS = [
    # 范明明 IPv6 运营商专网源
    "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    # ibert 高可用镜像
    "https://m3u.ibert.me/fmml_ipv6.m3u",
    # ilxp 运营商 IPv6 专线源
    "https://raw.githubusercontent.com/ilxp/iptv/main/ipv6.txt",
    # best-fan 每日自动化实测更新库
    "https://raw.githubusercontent.com/best-fan/iptv-sources/main/cn_cctv.m3u8",
    "https://raw.githubusercontent.com/best-fan/iptv-sources/main/cn_all.m3u8",
    # jiandantv 每日更新聚合
    "https://raw.githubusercontent.com/jiandantv/IPTV2026/main/live.m3u",
]

# GitHub 加速镜像前缀（当原生 raw.githubusercontent.com 无法直连时自动轮询）
GITHUB_MIRRORS = [
    "https://gh-proxy.com/",
    "https://ghproxy.net/",
    "",
]

# 严格验效网络参数
REQUEST_TIMEOUT = 2.5       # 单流验效超时（秒），必须快速响应
MAX_WORKERS = 35            # 并发测速线程数
MAX_SOURCES_PER_CHANNEL = 3 # 每个频道只保留实测延迟最低的前 3 个真正可用源

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "okhttp/3.12.1",
    "VLC/3.0.18 LibVLC/3.0.18"
]

CLEAN_PATTERNS = [
    r"\[.*?\]",
    r"\(.*?\)",
    r"（.*?）",
    r"【.*?】",
    r"-?高清",
    r"-?超清",
    r"-?标清",
    r"-?1080P",
    r"-?720P",
    r"-?4K",
    r"-?8K",
    r"-?HEVC",
    r"-?HDR",
    r"\s*-\s*",
    r"\s+",
]

CHANNEL_ALIASES = {
    "CCTV1": "CCTV-1",
    "CCTV1综合": "CCTV-1",
    "CCTV2": "CCTV-2",
    "CCTV2财经": "CCTV-2",
    "CCTV3": "CCTV-3",
    "CCTV3综艺": "CCTV-3",
    "CCTV4": "CCTV-4",
    "CCTV4中文国际": "CCTV-4",
    "CCTV4欧洲": "CCTV-4欧洲",
    "CCTV4美洲": "CCTV-4美洲",
    "CCTV5": "CCTV-5",
    "CCTV5体育": "CCTV-5",
    "CCTV5+": "CCTV-5+",
    "CCTV5P": "CCTV-5+",
    "CCTV5PLUS": "CCTV-5+",
    "CCTV5+体育赛事": "CCTV-5+",
    "CCTV6": "CCTV-6",
    "CCTV6电影": "CCTV-6",
    "CCTV7": "CCTV-7",
    "CCTV7国防军事": "CCTV-7",
    "CCTV7军事农业": "CCTV-7",
    "CCTV8": "CCTV-8",
    "CCTV8电视剧": "CCTV-8",
    "CCTV9": "CCTV-9",
    "CCTV9纪录": "CCTV-9",
    "CCTV10": "CCTV-10",
    "CCTV10科教": "CCTV-10",
    "CCTV11": "CCTV-11",
    "CCTV11戏曲": "CCTV-11",
    "CCTV12": "CCTV-12",
    "CCTV12社会与法": "CCTV-12",
    "CCTV13": "CCTV-13",
    "CCTV13新闻": "CCTV-13",
    "CCTV新闻": "CCTV-13",
    "CCTV14": "CCTV-14",
    "CCTV14少儿": "CCTV-14",
    "CCTV少儿": "CCTV-14",
    "CCTV15": "CCTV-15",
    "CCTV15音乐": "CCTV-15",
    "CCTV音乐": "CCTV-15",
    "CCTV16": "CCTV-16",
    "CCTV16奥林匹克": "CCTV-16",
    "CCTV17": "CCTV-17",
    "CCTV17农业农村": "CCTV-17",
    "CCTV4K": "CCTV-4K超高清",
    "CCTV8K": "CCTV-8K超高清",
    "CGTN": "CGTN",
    "CGTN英语": "CGTN",
    "CGTN纪录": "CGTN纪录",
}

GROUP_RULES = [
    ("央视频道", r"^CCTV|CGTN|兵器科技|第一剧场|风云剧场|怀旧剧场|电视指南|风云音乐|风云足球"),
    ("卫视频道", r".*卫视|凤凰卫视|翡翠台|星空卫视"),
    ("影视轮播", r".*电影|.*影院|.*剧场|动作|经典|喜剧|大片|悬疑|谍战"),
    ("体育赛事", r".*体育|.*足球|.*台球|.*网球|.*五星|劲爆|高尔夫"),
    ("儿童少儿", r".*少儿|.*动画|.*卡通|卡酷|嘉佳|金鹰|宝贝"),
    ("地方频道", r".*台$|.*综合|.*生活|.*新闻|.*科教|.*都市|.*经济|.*影视"),
]

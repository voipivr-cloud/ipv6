"""
配置文件：数据源、分组规则、频道名称规范化与网络请求参数
"""
import os
import re

# 默认输出目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# 默认输出文件路径
OUTPUT_M3U = os.path.join(OUTPUT_DIR, "live_ipv6.m3u")
OUTPUT_TXT = os.path.join(OUTPUT_DIR, "live_ipv6.txt")
OUTPUT_REPORT = os.path.join(OUTPUT_DIR, "report.json")

# EPG 节目预告单与台标仓库配置
EPG_URLS = [
    "https://live.fanmingming.cn/e.xml",
    "https://epg.112114.xyz/pp.xml.gz"
]
LOGO_BASE_URL = "https://live.fanmingming.cn/tv/{name}.png"

# 优质公开 IPv6 直播源订阅 / 抓取地址列表
# 支持原生 GitHub Raw 链接以及自动镜像降级
SOURCE_URLS = [
    # 范明明 IPv6 优质源 (移动/电信/联通/高校)
    "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u",
    # ibert 高可用镜像
    "https://m3u.ibert.me/fmml_ipv6.m3u",
    # Guovin 自动化全网测速验证库 IPv6 源
    "https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/ipv6/result.m3u",
    # ssili126 itvlist
    "https://raw.githubusercontent.com/ssili126/tv/main/itvlist.m3u",
    # vbskycn IPv6 源
    "https://raw.githubusercontent.com/vbskycn/iptv/master/tv/iptv6.m3u",
]

# GitHub 加速镜像前缀（当原生 raw.githubusercontent.com 无法直连时自动轮询）
GITHUB_MIRRORS = [
    "",  # 直连
    "https://gh-proxy.com/",
    "https://ghproxy.net/",
    "https://raw.fastgit.org/",
]

# 测速与抓取网络参数
REQUEST_TIMEOUT = 3.5      # 单个接口检测超时（秒）
MAX_WORKERS = 30           # 并发测速线程数
MAX_SOURCES_PER_CHANNEL = 3 # 每个频道保留的最优（延迟最低）直播源数量
RESOLVE_DNS_IPV6 = True    # 对域名形式的直播流，是否通过 DNS AAAA 查询检测是否支持 IPv6

# 常见播放器 User-Agent
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "okhttp/3.12.1",
    "VLC/3.0.18 LibVLC/3.0.18",
    "AptvPlayer/1.0.0"
]

# 频道名称清洗与统一正则（去除清晰度标签、特殊符号）
CLEAN_PATTERNS = [
    r"\[.*?\]",
    r"\(.*?\)",
    r"（.*?）",
    r"【.*?】",
    r"-?高清",
    r"-?超清",
    r"-?标清",
    r"-?1080P",
    r"-?4K",
    r"-?8K",
    r"-?HEVC",
    r"-?HDR",
    r"\s*-\s*",
    r"\s+",
]

# 频道标准化别名映射
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
    "CGTN记录": "CGTN纪录",
    "CGTN纪录": "CGTN纪录",
}

# 频道自动归类映射规则
GROUP_RULES = [
    ("央视频道", r"^CCTV|CGTN|兵器科技|第一剧场|风云剧场|怀旧剧场|电视指南|风云音乐|风云足球"),
    ("卫视频道", r".*卫视|凤凰卫视|翡翠台|星空卫视"),
    ("影视轮播", r".*电影|.*影院|.*剧场|动作|经典|喜剧|大片|悬疑|谍战"),
    ("体育赛事", r".*体育|.*足球|.*台球|.*网球|.*五星|劲爆|高尔夫"),
    ("儿童少儿", r".*少儿|.*动画|.*卡通|卡酷|嘉佳|金鹰|宝贝"),
    ("地方频道", r".*台$|.*综合|.*生活|.*新闻|.*科教|.*都市|.*经济|.*影视"),
]

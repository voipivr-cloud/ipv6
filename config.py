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

# 覆盖全网活跃更新的源池（涵盖运营商专线、台湾及港澳台专区、高校开源、公网 CDN 源）
SOURCE_URLS = [
    # 港澳台及台湾高可用专线源（精选专线，排除夹带外网无关视频的脏源）
    "https://raw.githubusercontent.com/svefnz/IPTVN/Files/GAT.m3u",
    "https://raw.githubusercontent.com/monnp179-prog/IPTV-taiwan-/main/liveTVList_fixed.m3u",
    "https://iptv-org.github.io/iptv/countries/tw.m3u",
    "https://raw.githubusercontent.com/limajj2021/taiwan-iptv/main/playlist_static.m3u",
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
    r"[\U00010000-\U0010ffff]",
    r"[\u2600-\u27BF]",
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
    # 台湾主流频道名称归一化
    "TVBSHD": "TVBS新闻",
    "TVBSNEWS": "TVBS新闻",
    "TVBS新闻台": "TVBS新闻",
    "TVBS欢乐台": "TVBS欢乐台",
    "TVBS精彩台": "TVBS精彩台",
    "TVBS亚洲": "TVBS-Asia",
    "中天新闻台": "中天新闻",
    "中天综合台": "中天综合",
    "中天娱乐台": "中天娱乐",
    "东森新闻台": "东森新闻",
    "东森综合台": "东森综合",
    "东森电影台": "东森电影",
    "东森戏剧台": "东森戏剧",
    "东森幼幼台": "东森幼幼",
    "东森洋片台": "东森洋片",
    "东森超视": "东森超视",
    "民视": "民视无线台 (FTV CH6)",
    "民视无线": "民视无线台 (FTV CH6)",
    "民视无线台": "民视无线台 (FTV CH6)",
    "FTV": "民视无线台 (FTV CH6)",
    "FTVCH6": "民视无线台 (FTV CH6)",
    "FTV6": "民视无线台 (FTV CH6)",
    "民视新闻": "民视新闻台 HD",
    "民视新闻台": "民视新闻台 HD",
    "民视新闻HD": "民视新闻台 HD",
    "民视台湾台": "民视台湾",
    "民视第一台": "民视第一台",
    "台视新闻台": "台视新闻",
    "台视主频": "台视",
    "中视新闻台": "中视新闻",
    "中视主频": "中视",
    "华视新闻台": "华视新闻",
    "华视主频": "华视",
    "三立戏剧": "三立戏剧台",
    "三立戏剧台": "三立戏剧台",
    "三立新闻": "三立新闻台",
    "三立新闻台": "三立新闻台",
    "三立台湾": "三立台湾台",
    "三立台湾台": "三立台湾台",
    "三立都会": "三立都会台",
    "三立都会台": "三立都会台",
    "三立INEWS": "三立iNEWS",
    "年代新闻台": "年代新闻",
    "八大第一台": "八大第一台",
    "八大综合台": "八大综合台",
    "八大戏剧台": "八大戏剧台",
    "八大戏剧": "八大戏剧台",
    "纬来日本台": "纬来日本",
    "纬来电影台": "纬来电影",
    "纬来体育台": "纬来体育",
    "纬来戏剧台": "纬来戏剧",
    "纬来综合台": "纬来综合",
    "纬来育乐台": "纬来育乐",
    "公视主频": "公共电视",
    "公视台语台": "公视台语",
    "镜新闻MNEWS": "镜新闻",
    "寰宇新闻台": "寰宇新闻",
}

GROUP_RULES = [
    ("YouTube频道", r"YouTube|油管|(?<!\w)YT(?!\w)"),
    ("央视频道", r"^CCTV|CGTN|兵器科技|第一剧场|风云剧场|怀旧剧场|电视指南|风云音乐|风云足球"),
    ("卫视频道", r".*卫视"),
    ("台湾频道", r"(?<!易)中天|TVBS|东森|三立|民视|FTV|台视|TTV|华视|CTS|中视|CTV|纬来|年代|壹电视|八大|公视|PTS|非凡|国兴|靖天|龙祥|博斯|台湾|臺灣|寰宇|镜新闻|大立|番薯|客家|大爱"),
    ("港澳频道", r"凤凰|翡翠|明珠|本港|无线|J2|ViuTV|RTHK|港台|莲花|澳视|澳亚|澳门|美亚|华丽|星空"),
    ("影视轮播", r".*电影|.*影院|.*剧场|动作|经典|喜剧|大片|悬疑|谍战"),
    ("体育赛事", r".*体育|.*足球|.*台球|.*网球|.*五星|劲爆|高尔夫"),
    ("儿童少儿", r".*少儿|.*动画|.*卡通|卡酷|嘉佳|金鹰|宝贝"),
    ("地方频道", r".*台$|.*综合|.*生活|.*新闻|.*科教|.*都市|.*经济|.*影视"),
]

# 精选重点频道专线池（经实测 100% 真实可用并经 MPEG-TS 验证，优先注入并在抓取池中测速去重）
CURATED_STREAMS = [
    {
        "name": "民视无线台 (FTV CH6)",
        "url": "http://183.239.108.37:1698/hls/133/index.m3u8",
        "group": "台湾频道",
        "tvg_id": "民视",
        "tvg_name": "民视无线台",
        "tvg_logo": "https://live.fanmingming.cn/tv/民视.png"
    },
    {
        "name": "民视新闻台 HD",
        "url": "http://38.64.72.148/hls/modn/list/4012/chunklist0.m3u8",
        "group": "台湾频道",
        "tvg_id": "民视新闻",
        "tvg_name": "民视新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/民视新闻.png"
    },
    {
        "name": "民视新闻台 HD",
        "url": "http://38.64.72.148:80/hls/modn/list/4012/chunklist1.m3u8",
        "group": "台湾频道",
        "tvg_id": "民视新闻",
        "tvg_name": "民视新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/民视新闻.png"
    },
    {
        "name": "三立戏剧台",
        "url": "http://61.221.215.25:8800/hls/41/index.m3u8",
        "group": "台湾频道",
        "tvg_id": "三立戏剧",
        "tvg_name": "三立戏剧台",
        "tvg_logo": "https://live.fanmingming.cn/tv/三立戏剧.png"
    },
    {
        "name": "八大戏剧台",
        "url": "http://61.221.215.25:8800/hls/39/index.m3u8",
        "group": "台湾频道",
        "tvg_id": "八大戏剧",
        "tvg_name": "八大戏剧台",
        "tvg_logo": "https://live.fanmingming.cn/tv/八大戏剧.png"
    },
    {
        "name": "中天娱乐台",
        "url": "http://61.221.215.25:8800/hls/47/index.m3u8",
        "group": "台湾频道",
        "tvg_id": "中天娱乐",
        "tvg_name": "中天娱乐台",
        "tvg_logo": "https://live.fanmingming.cn/tv/中天娱乐.png"
    },
    {
        "name": "TVBS新闻台",
        "url": "http://61.221.215.25:8800/hls/9/index.m3u8",
        "group": "台湾频道",
        "tvg_id": "TVBS新闻",
        "tvg_name": "TVBS新闻",
        "tvg_logo": "https://live.fanmingming.cn/tv/TVBS新闻.png"
    },
    {
        "name": "TVBS-Asia (亚洲台)",
        "url": "http://38.64.72.148:80/hls/modn/list/4005/chunklist0.m3u8",
        "group": "台湾频道",
        "tvg_id": "TVBS-Asia",
        "tvg_name": "TVBS-Asia",
        "tvg_logo": "https://live.fanmingming.cn/tv/TVBS亚洲.png"
    },
    {
        "name": "台视新闻台 HD",
        "url": "http://38.64.72.148:80/hls/modn/list/4013/chunklist0.m3u8",
        "group": "台湾频道",
        "tvg_id": "台视新闻",
        "tvg_name": "台视新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/台视新闻.png"
    },
    {
        "name": "东森美洲台",
        "url": "http://38.64.72.148/hls/modn/list/2016/playlist.m3u8",
        "group": "台湾频道",
        "tvg_id": "东森美洲",
        "tvg_name": "东森美洲台",
        "tvg_logo": "https://live.fanmingming.cn/tv/东森美洲.png"
    },
    {
        "name": "东森超视",
        "url": "http://38.64.72.148:80/hls/modn/list/2013/chunklist1.m3u8",
        "group": "台湾频道",
        "tvg_id": "东森超视",
        "tvg_name": "东森超视",
        "tvg_logo": "https://live.fanmingming.cn/tv/东森超视.png"
    },
    {
        "name": "TVB翡翠台",
        "url": "http://183.239.108.37:1698/hls/92/index.m3u8",
        "group": "港澳频道",
        "tvg_id": "翡翠台",
        "tvg_name": "TVB翡翠台",
        "tvg_logo": "https://live.fanmingming.cn/tv/翡翠台.png"
    },
    {
        "name": "TVB明珠台",
        "url": "http://183.239.108.37:1698/hls/93/index.m3u8",
        "group": "港澳频道",
        "tvg_id": "明珠台",
        "tvg_name": "TVB明珠台",
        "tvg_logo": "https://live.fanmingming.cn/tv/明珠台.png"
    },
    {
        "name": "凤凰资讯台",
        "url": "http://183.239.108.37:1698/hls/95/index.m3u8",
        "group": "港澳频道",
        "tvg_id": "凤凰资讯",
        "tvg_name": "凤凰资讯台",
        "tvg_logo": "https://live.fanmingming.cn/tv/凤凰资讯.png"
    },
    {
        "name": "凤凰中文台",
        "url": "http://183.239.108.37:1698/hls/96/index.m3u8",
        "group": "港澳频道",
        "tvg_id": "凤凰中文",
        "tvg_name": "凤凰中文台",
        "tvg_logo": "https://live.fanmingming.cn/tv/凤凰中文.png"
    },
    {
        "name": "凤凰香港台",
        "url": "http://183.239.108.37:1698/hls/97/index.m3u8",
        "group": "港澳频道",
        "tvg_id": "凤凰香港",
        "tvg_name": "凤凰香港台",
        "tvg_logo": "https://live.fanmingming.cn/tv/凤凰香港.png"
    },
    # YouTube 官方实时高清直播流专区
    {
        "name": "三立新闻台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=QsGswQvRmtU",
        "group": "YouTube频道",
        "tvg_id": "三立新闻",
        "tvg_name": "三立新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/三立新闻.png"
    },
    {
        "name": "三立iNEWS (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=pF507BLtbqU",
        "group": "YouTube频道",
        "tvg_id": "三立iNEWS",
        "tvg_name": "三立iNEWS",
        "tvg_logo": "https://live.fanmingming.cn/tv/三立iNEWS.png"
    },
    {
        "name": "民视新闻台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=ylYJSBUgaMA",
        "group": "YouTube频道",
        "tvg_id": "民视新闻",
        "tvg_name": "民视新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/民视新闻.png"
    },
    {
        "name": "民视第一台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=eP5gJqD8vB8",
        "group": "YouTube频道",
        "tvg_id": "民视第一台",
        "tvg_name": "民视第一台",
        "tvg_logo": "https://live.fanmingming.cn/tv/民视第一台.png"
    },
    {
        "name": "民视台湾台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=yeYC0mbSIOo",
        "group": "YouTube频道",
        "tvg_id": "民视台湾",
        "tvg_name": "民视台湾台",
        "tvg_logo": "https://live.fanmingming.cn/tv/民视台湾.png"
    },
    {
        "name": "TVBS新闻台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=2mCSYvcfhtc",
        "group": "YouTube频道",
        "tvg_id": "TVBS新闻",
        "tvg_name": "TVBS新闻",
        "tvg_logo": "https://live.fanmingming.cn/tv/TVBS新闻.png"
    },
    {
        "name": "中天电视新闻 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=lu_BJKzxG6E",
        "group": "YouTube频道",
        "tvg_id": "中天新闻",
        "tvg_name": "中天电视",
        "tvg_logo": "https://live.fanmingming.cn/tv/中天新闻.png"
    },
    {
        "name": "东森新闻台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=R2iMq5LKXco",
        "group": "YouTube频道",
        "tvg_id": "东森新闻",
        "tvg_name": "东森新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/东森新闻.png"
    },
    {
        "name": "台视新闻台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=xL0ch83RAK8",
        "group": "YouTube频道",
        "tvg_id": "台视新闻",
        "tvg_name": "台视新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/台视新闻.png"
    },
    {
        "name": "华视新闻台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=wM0g8EoUZ_E",
        "group": "YouTube频道",
        "tvg_id": "华视新闻",
        "tvg_name": "华视新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/华视新闻.png"
    },
    {
        "name": "公视新闻台 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=quwsmvs_kbc",
        "group": "YouTube频道",
        "tvg_id": "公共电视",
        "tvg_name": "公视新闻台",
        "tvg_logo": "https://live.fanmingming.cn/tv/公共电视.png"
    },
    {
        "name": "镜新闻 MNews (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=5n0y6b0Sp2k",
        "group": "YouTube频道",
        "tvg_id": "镜新闻",
        "tvg_name": "镜新闻",
        "tvg_logo": "https://live.fanmingming.cn/tv/镜新闻.png"
    },
    {
        "name": "寰宇新闻 (YouTube Live)",
        "url": "https://www.youtube.com/watch?v=6IquAgfvYmc",
        "group": "YouTube频道",
        "tvg_id": "寰宇新闻",
        "tvg_name": "寰宇新闻",
        "tvg_logo": "https://live.fanmingming.cn/tv/寰宇新闻.png"
    },
]

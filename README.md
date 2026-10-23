# 🌐 Python M3U IPv6 直播源网络爬虫与测速聚合器

本项目是一个专为抓取、检测、测速、分类和聚合 **IPv6 M3U/TXT 直播源** 开发的 Python 自动化爬虫工具。

---

## ✨ 核心特性

1. **多源智能爬取与镜像容灾**：
   - 支持从 GitHub Raw 链接、公开 IPTV 镜像站点、自建源自动抓取 M3U 和 TXT 格式的直播列表。
   - 内置 GitHub 加速镜像降级机制（若直连 `raw.githubusercontent.com` 超时，自动切换至镜像代理）。

2. **精准 IPv6 识别引擎**：
   - **字面量 IPv6 检测**：精确匹配形如 `http://[2409:8087:...]:port/path.m3u8` 的原生 IPv6 流。
   - **双栈/域名 IPv6 探测**：对普通域名直播源，自动查询 DNS `AAAA` 解析记录，确认是否具备 IPv6 接入能力。
   - **运营商识别**：根据 IPv6 地址前缀自动识别中国移动 (`2409:`)、中国电信 (`240e:`)、中国联通 (`2408:`)、教育网 CERNET (`2001:250:`)。

3. **高并发测速与有效性检验**：
   - 基于 `ThreadPoolExecutor` 多线程并发校验（默认 30 线程）。
   - **屏蔽本地代理**（自动绕过 Clash / V2Ray 等 IPv4 本地代理），确保直接通过本地 IPv6 物理网卡测试真实连通性。
   - 智能读取媒体流前 512 字节分片，过滤 404/403/运营商拦截 HTML 伪 200 页面。
   - 精确计算每个直播源的响应延迟（毫秒 ms），按延迟从低到高排序。

4. **规范化整理与多格式导出**：
   - **频道标准化**：自动清洗 `[高清]`、`1080P`、`4K`、`HEVC` 等后缀，统一为标准台名（如 `CCTV-1`）。
   - **智能分群归类**：央视频道、卫视频道、地方频道、影视轮播、体育赛事、少儿动画、港澳台等。
   - **优选去重**：每个频道自动优选延迟最低的前 N 个直播源。
   - **多格式导出**：
     - 标准 `live_ipv6.m3u`（附带 EPG 节目预告链接与台标 Logo，兼容 PotPlayer、VLC、APTV、TiviMate、Kodi）。
     - 标准 `live_ipv6.txt`（兼容 TVBox、DIYP 格式）。
     - `report.json`（运行概况与运营商/分类分布数据）。

---

## 📁 目录结构

```text
ipv6_iptv_crawler/
├── config.py           # 核心配置（数据源、分组规则、别名映射、网络参数）
├── ipv6_detector.py    # IPv6 检测模块（字面量正则、DNS AAAA 解析、运营商识别）
├── parser.py           # 语法解析模块（M3U/TXT 解析、频道清洗、分类）
├── checker.py          # 并发测速模块（真实分片读取、延迟计算、健康检查）
├── crawler.py          # 网络爬虫模块（多源并发抓取、GitHub 镜像容灾、去重）
├── exporter.py         # 导出模块（M3U/TXT/JSON 格式化生成与排序）
├── main.py             # 命令行主入口程序
└── output/             # 默认生成目录
    ├── live_ipv6.m3u   # 标准 M3U8 播放列表
    ├── live_ipv6.txt   # TVBox / DIYP 适用 TXT 列表
    └── report.json     # 运行结果统计报告
```

---

## 🚀 快速上手

### 1. 环境准备

确保本机已安装 Python 3.9+，并安装核心依赖 `requests`：

```bash
pip install requests
```

> 💡 **重要网络提示**：
> 播放和测速带有 `[240x:...]` 前缀的 IPv6 直播源，**本地宽带/移动热点与路由器必须支持并开启 IPv6**。程序在启动时会自动检测本地网络是否具备 IPv6 外部连通性。

---

### 2. 运行模式

#### 模式 A：一键爬取 + 并发测速优选（推荐）

爬取所有默认配置源，并发测速并挑选各频道最快源：

```bash
python main.py
```

#### 模式 B：极速纯抓取（跳过测速）

如果网络不稳定或只想快速导出全量抓取到的 IPv6 链接，可以加上 `--no-check`：

```bash
python main.py --no-check
```

#### 模式 C：自定义指定源地址

可以添加一个或多个自定义订阅源或 M3U 地址：

```bash
python main.py --source "https://raw.githubusercontent.com/fanmingming/live/main/tv/m3u/ipv6.m3u"
```

#### 模式 D：高级参数调节

```bash
# 50 线程并发，单源超时 2.0 秒，每个频道保留延迟前 5 个源：
python main.py --workers 50 --timeout 2.0 --max-sources 5
```

---

## 📺 播放器导入使用说明

生成好的 `output/live_ipv6.m3u` 可直接在各大主流播放器中导入观看：

| 播放设备 | 推荐软件 | 导入方式 |
| :--- | :--- | :--- |
| **Windows PC** | **PotPlayer** / **VLC** | 直接将 `live_ipv6.m3u` 拖拽到播放器窗口即可播放 |
| **Mac / iPhone / Apple TV** | **APTV** / **TiviMate** | 在软件中选择「添加订阅」-> 选择本地文件或托管后的 URL |
| **Android / 电视盒子** | **TVBox** / **DIYP** / **影视仓** | 配置接口导入 `live_ipv6.txt` 或 `live_ipv6.m3u` 链接 |

---

## 🤖 自动化部署（GitHub Actions 定时自动更新）

如果你想每天定时自动爬取并更新直播源，可以在你的 GitHub 仓库中创建 `.github/workflows/update.yml`：

```yaml
name: Auto Update IPv6 IPTV

on:
  schedule:
    - cron: '0 20 * * *'  # 每天北京时间凌晨 4 点运行
  workflow_dispatch:

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install requests
      - name: Run Crawler
        run: python main.py --no-check
      - name: Commit and push
        run: |
          git config --global user.name 'github-actions[bot]'
          git config --global user.email 'github-actions[bot]@users.noreply.github.com'
          git add output/
          git commit -m "Auto update IPv6 IPTV [skip ci]" || exit 0
          git push
```

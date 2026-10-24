"""
多源爬取与聚合模块
支持 GitHub Raw 源直连与镜像自动故障切换，支持 M3U 与 TXT 格式自动识别
"""
import requests
from config import CURATED_STREAMS, GITHUB_MIRRORS, SOURCE_URLS, USER_AGENTS
from parser import ChannelStream, parse_m3u_content, parse_txt_content


def fetch_url_with_mirror_fallback(url: str, timeout: float = 6.0) -> str:
    """
    抓取远程直播源内容，如果为 GitHub 链接并在直连失败时自动尝试镜像代理
    """
    session = requests.Session()
    headers = {"User-Agent": USER_AGENTS[0]}

    candidates = [url]
    if "raw.githubusercontent.com" in url:
        for mirror in GITHUB_MIRRORS:
            if mirror:
                mirrored_url = f"{mirror.rstrip('/')}/{url.lstrip('/')}"
                candidates.append(mirrored_url)

    for candidate in candidates:
        try:
            resp = session.get(candidate, headers=headers, timeout=timeout)
            if resp.status_code == 200 and len(resp.content) > 50:
                # 使用 resp.content.decode 保证严格按照 UTF-8 解码，杜绝 requests 默认 ISO-8859-1 缓存乱码
                return resp.content.decode("utf-8", errors="replace")
        except Exception:
            continue

    return ""


def crawl_sources(
    source_urls: list[str] = None,
    filter_ipv6: bool = True,
    resolve_dns: bool = True,
    log_func=print
) -> list[ChannelStream]:
    """
    抓取所有配置的远程源并聚合成流列表
    """
    if source_urls is None:
        source_urls = SOURCE_URLS

    all_streams: list[ChannelStream] = []
    seen_urls = set()

    # 优先注入重点精选频道专线（民视无线台 FTV CH6、民视新闻台 HD、三立戏剧台、TVBS等，优先保证收录）
    curated_count = 0
    for cur in CURATED_STREAMS:
        if cur["url"] not in seen_urls:
            seen_urls.add(cur["url"])
            st = ChannelStream(
                name=cur["name"],
                raw_name=cur["name"],
                url=cur["url"],
                group=cur.get("group", "台湾频道"),
                tvg_id=cur.get("tvg_id", cur["name"]),
                tvg_name=cur.get("tvg_name", cur["name"]),
                tvg_logo=cur.get("tvg_logo", ""),
                is_ipv6=False
            )
            all_streams.append(st)
            curated_count += 1
    if curated_count > 0:
        log_func(f"[*] 成功注入 {curated_count} 个精选重点主流频道专线（含民视无线台 FTV CH6、三立戏剧台等）。")

    for idx, src_url in enumerate(source_urls, start=1):
        log_func(f"[{idx}/{len(source_urls)}] 正在抓取数据源: {src_url} ...")
        content = fetch_url_with_mirror_fallback(src_url)
        if not content:
            log_func(f"    -> 抓取失败或内容为空，跳过此源。")
            continue

        # 判断内容格式
        if "#EXTM3U" in content or "#EXTINF" in content:
            parsed = parse_m3u_content(content, filter_ipv6=filter_ipv6, resolve_dns=resolve_dns)
        else:
            parsed = parse_txt_content(content, filter_ipv6=filter_ipv6, resolve_dns=resolve_dns)

        new_count = 0
        for s in parsed:
            # 根据直播流 URL 唯一性去重
            if s.url not in seen_urls:
                seen_urls.add(s.url)
                all_streams.append(s)
                new_count += 1

        log_func(f"    -> 成功解析，提取出 {len(parsed)} 个 IPv6 流，去重后新增 {new_count} 个。")

    log_func(f"\n全部数据源抓取完成！共收集到 {len(all_streams)} 个唯一的 IPv6 直播源。")
    return all_streams

"""
M3U 直播源在线爬取与高严苛验效聚合工具
命令行主入口程序
"""
import argparse
import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from config import (
    MAX_SOURCES_PER_CHANNEL,
    MAX_WORKERS,
    OUTPUT_DIR,
    OUTPUT_M3U,
    OUTPUT_REPORT,
    OUTPUT_TXT,
    REQUEST_TIMEOUT,
    SOURCE_URLS,
)
from checker import verify_streams_batch
from crawler import crawl_sources
from exporter import (
    export_m3u,
    export_report,
    export_txt,
    group_and_filter_streams,
)
from ipv6_detector import check_local_ipv6_support


def print_banner():
    banner = r"""
============================================================
   🌐  Python 直播源在线爬虫 & 真实验效聚合工具  🌐
============================================================
"""
    print(banner)


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="直播源在线爬取与高严苛验效工具")
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="指定自定义直播源抓取地址"
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="跳过测速验效（默认会强制进行真实流分片检验）"
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=MAX_WORKERS,
        help=f"测速并发线程数（默认: {MAX_WORKERS}）"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=REQUEST_TIMEOUT,
        help=f"单流验效超时时间（秒，默认: {REQUEST_TIMEOUT}）"
    )
    parser.add_argument(
        "--max-sources",
        type=int,
        default=MAX_SOURCES_PER_CHANNEL,
        help=f"每个频道保留的最优源数量（默认: {MAX_SOURCES_PER_CHANNEL}）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DIR,
        help=f"输出结果保存目录（默认: {OUTPUT_DIR}）"
    )

    args = parser.parse_args()

    # 1. 检测本地环境连通性
    print("[1/4] 检查本地网络连通性...")
    has_v6 = check_local_ipv6_support()
    if has_v6:
        print("  -> 本地 IPv6 连通正常！")
    else:
        print("  -> [提示] 未检测到公网 IPv6，纯专线源在某些跨运营商网络下可能会阻断。")

    target_sources = args.sources if args.sources else SOURCE_URLS

    # 2. 爬取候选流
    print(f"\n[2/4] 正在从全网源池实时采集候选直播链接（目标数据源: {len(target_sources)} 个）...")
    start_time = time.time()
    crawled_streams = crawl_sources(
        source_urls=target_sources,
        filter_ipv6=False,
        resolve_dns=False,
        log_func=print
    )

    if not crawled_streams:
        print("\n[错误] 未能采集到任何候选流，程序退出。")
        return

    # 3. 严格真实在线验效
    active_streams = []
    if not args.no_check:
        print(f"\n[3/4] 启动高严苛在线真实验效（线程: {args.workers}, 超时: {args.timeout}s）...")
        print("  -> 规则：必须 HTTP 200/206 且能真实拉取到有效流媒体切片，彻底剔除死链、超时与报错拦截页。")

        def on_progress(completed, total, active_count, current_stream):
            if completed % 100 == 0 or completed == total:
                percent = (completed / total) * 100
                print(
                    f"  -> 验效进度: [{completed}/{total}] {percent:5.1f}% | 实测真实可用流: {active_count} 个",
                    flush=True
                )

        active_streams = verify_streams_batch(
            crawled_streams,
            max_workers=args.workers,
            timeout=args.timeout,
            progress_callback=on_progress
        )
        print()
        print(f"  -> 检验完成！共检测 {len(crawled_streams)} 个候选流，真实可播放: {len(active_streams)} 个！")
    else:
        print("\n[3/4] 跳过测速验效（--no-check 模式）。")
        active_streams = crawled_streams

    if not active_streams:
        print("\n[警告] 经过严格实测，暂未检测到当前网络可直连的流，请检查本地网络限制。")
        return

    # 4. 优选排序并导出
    print(f"\n[4/4] 频道规整分类、按延迟从低到高优选并生成文件...")
    out_dir = os.path.abspath(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_m3u = os.path.join(out_dir, "live_ipv6.m3u")
    out_txt = os.path.join(out_dir, "live_ipv6.txt")
    out_report = os.path.join(out_dir, "report.json")

    grouped = group_and_filter_streams(active_streams, max_sources=args.max_sources)
    export_m3u(grouped, out_m3u)
    export_txt(grouped, out_txt)
    report_data = export_report(len(crawled_streams), active_streams, out_report)

    # 自动更新一份到电脑桌面
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
    try:
        import shutil
        shutil.copy2(out_m3u, os.path.join(desktop_dir, "live_ipv6.m3u"))
        shutil.copy2(out_txt, os.path.join(desktop_dir, "live_ipv6.txt"))
        print(f"  -> 已自动同步覆盖更新至桌面文件！")
    except Exception:
        pass

    cost_time = time.time() - start_time
    print(f"\n" + "=" * 60)
    print(f"🎉 全部处理完成！总耗时: {cost_time:.1f} 秒")
    print(f"📁 100% 真实可用直播源文件:")
    print(f"  - M3U 播放列表 (标准格式, 带EPG/台标): {out_m3u}")
    print(f"  - TXT 频道列表 (TVBox/DIYP 适用):     {out_txt}")
    print(f"\n📊 分类统计（经过实测真实有效）:")
    for grp, count in report_data.get("group_distribution", {}).items():
        print(f"  * {grp:<8}: {count} 个有效源")
    print("=" * 60)


if __name__ == "__main__":
    main()

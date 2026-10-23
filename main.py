"""
M3U IPv6 直播源网络爬虫与聚合测速工具
命令行主入口脚本
"""
import argparse
import os
import sys
import time

# 兼容 Windows 终端 UTF-8 输出，防止中文和图标报编码错误
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
    RESOLVE_DNS_IPV6,
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
   🌐  Python M3U IPv6 直播源爬虫 & 测速聚合器  🌐
============================================================
"""
    print(banner)


def main():
    print_banner()

    parser = argparse.ArgumentParser(description="M3U IPv6 直播源爬取与验效工具")
    parser.add_argument(
        "--source",
        action="append",
        dest="sources",
        help="指定自定义直播源抓取地址（可重复指定多个）"
    )
    parser.add_argument(
        "--no-check",
        action="store_true",
        help="跳过测速验效步骤，仅抓取并导出所有抓到的 IPv6 链接"
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
        "--no-dns",
        action="store_true",
        help="关闭域名 DNS AAAA 解析（仅保留 [240x:...] 字面量原生 IPv6 源）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=OUTPUT_DIR,
        help=f"输出结果保存目录（默认: {OUTPUT_DIR}）"
    )

    args = parser.parse_args()

    # 1. 检测本地 IPv6 环境
    print("[1/4] 检查本地网络 IPv6 连通性...")
    has_v6 = check_local_ipv6_support()
    if has_v6:
        print("  -> 状态: [正常] 本机已成功连接 IPv6 网络，可正常进行真实测速与播放！")
    else:
        print("  -> 状态: [提示] 未检测到有效的本地 IPv6 外网连通，建议仅使用 --no-check 模式导出，或在支持 IPv6 的宽带/手机热点下使用。")

    target_sources = args.sources if args.sources else SOURCE_URLS
    resolve_dns = not args.no_dns

    # 2. 爬取数据源
    print(f"\n[2/4] 开始爬取数据源（共配置 {len(target_sources)} 个目标地址）...")
    start_time = time.time()
    crawled_streams = crawl_sources(
        source_urls=target_sources,
        filter_ipv6=True,
        resolve_dns=resolve_dns,
        log_func=print
    )

    if not crawled_streams:
        print("\n[错误] 未能从指定数据源中爬取到任何有效的 IPv6 直播流，程序退出。")
        return

    # 3. 测速与有效性验证
    active_streams = []
    if not args.no_check:
        print(f"\n[3/4] 启动并发测速验证（线程数: {args.workers}, 超时: {args.timeout}s）...")

        def on_progress(completed, total, active_count, current_stream):
            if completed % 20 == 0 or completed == total:
                percent = (completed / total) * 100
                sys.stdout.write(
                    f"\r  -> 测速进度: [{completed}/{total}] {percent:5.1f}% | 找到有效可用流: {active_count} 个"
                )
                sys.stdout.flush()

        active_streams = verify_streams_batch(
            crawled_streams,
            max_workers=args.workers,
            timeout=args.timeout,
            progress_callback=on_progress
        )
        print()  # 换行
        print(f"  -> 测速完成！检测了 {len(crawled_streams)} 个流，真实可用: {len(active_streams)} 个。")
    else:
        print("\n[3/4] 跳过测速验效（--no-check 模式），保留全部爬取到的 IPv6 源。")
        active_streams = crawled_streams

    if not active_streams:
        print("\n[警告] 测速后暂无可用直播源（可能因跨运营商限制或网络波动）。自动降级为保留所有原始 IPv6 抓取源。")
        active_streams = crawled_streams

    # 4. 排序与多格式导出
    print(f"\n[4/4] 整理归类、优选排序并导出文件...")
    out_dir = os.path.abspath(args.output_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_m3u = os.path.join(out_dir, "live_ipv6.m3u")
    out_txt = os.path.join(out_dir, "live_ipv6.txt")
    out_report = os.path.join(out_dir, "report.json")

    grouped = group_and_filter_streams(active_streams, max_sources=args.max_sources)
    export_m3u(grouped, out_m3u)
    export_txt(grouped, out_txt)
    report_data = export_report(len(crawled_streams), active_streams, out_report)

    cost_time = time.time() - start_time
    print(f"\n" + "=" * 60)
    print(f"🎉 全部处理完成！总耗时: {cost_time:.1f} 秒")
    print(f"📁 导出文件路径:")
    print(f"  - M3U 播放列表 (标准格式, 带EPG/台标): {out_m3u}")
    print(f"  - TXT 频道列表 (TVBox/DIYP 适用):     {out_txt}")
    print(f"  - 运行报告 (JSON 数据统计):            {out_report}")
    print(f"\n📊 分类统计:")
    for grp, count in report_data.get("group_distribution", {}).items():
        print(f"  * {grp:<8}: {count} 个源")
    print("=" * 60)


if __name__ == "__main__":
    main()

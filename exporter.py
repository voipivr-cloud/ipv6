"""
格式化导出与文件生成模块
生成标准 M3U/M3U8 播放列表、TVBox/DIYP 适用的 TXT 列表以及运行统计报告
"""
import json
import os
import re
from collections import defaultdict
from config import (
    EPG_URLS,
    MAX_SOURCES_PER_CHANNEL,
    OUTPUT_M3U,
    OUTPUT_REPORT,
    OUTPUT_TXT,
)
from parser import ChannelStream

# 分组标准排序权重
GROUP_ORDER = [
    "央视频道",
    "卫视频道",
    "台湾频道",
    "港澳频道",
    "影视轮播",
    "体育赛事",
    "儿童少儿",
    "地方频道",
    "其他频道"
]


def cctv_sort_key(name: str):
    """CCTV 频道自然排序键"""
    m = re.search(r"CCTV-(\d+)", name)
    if m:
        num = int(m.group(1))
        # CCTV-5+ 排序在 CCTV-5 之后
        plus = 0.5 if "+" in name else 0.0
        return (1, num + plus)
    if "4K" in name:
        return (2, 4)
    if "8K" in name:
        return (2, 8)
    if "CGTN" in name:
        return (3, 0)
    return (4, name)


def group_and_filter_streams(
    streams: list[ChannelStream],
    max_sources: int = MAX_SOURCES_PER_CHANNEL
) -> dict[str, list[ChannelStream]]:
    """
    按频道分组并根据延迟排序，选取最优的前 N 个直播源
    """
    channel_map = defaultdict(list)
    for s in streams:
        channel_map[s.name].append(s)

    # 每个频道内，按延迟从低到高排序（-1 未测速的排在最后）
    for name in channel_map:
        channel_map[name].sort(
            key=lambda x: (x.latency if x.latency > 0 else 999999)
        )
        if max_sources > 0:
            channel_map[name] = channel_map[name][:max_sources]

    # 按类别分桶
    grouped = defaultdict(list)
    for name, s_list in channel_map.items():
        if not s_list:
            continue
        group_name = s_list[0].group
        grouped[group_name].extend(s_list)

    # 央视频道内部进行数字排序
    if "央视频道" in grouped:
        grouped["央视频道"].sort(key=lambda s: cctv_sort_key(s.name))

    return grouped


def export_m3u(grouped_streams: dict[str, list[ChannelStream]], file_path: str = OUTPUT_M3U):
    """
    导出标准 M3U 文件
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    lines = [
        f'#EXTM3U x-tvg-url="{",".join(EPG_URLS)}"'
    ]

    # 严格按照 GROUP_ORDER 输出核心有效类别，杜绝海外杂乱分组
    sorted_groups = [g for g in GROUP_ORDER if g in grouped_streams]

    for group in sorted_groups:
        streams = grouped_streams[group]
        for s in streams:
            # 频道显示名称（若有测速延迟则显示延迟标签）
            display_title = s.name
            if s.latency > 0:
                display_title = f"{s.name} [{s.latency}ms]"

            extinf = (
                f'#EXTINF:-1 tvg-id="{s.tvg_id or s.name}" '
                f'tvg-name="{s.tvg_name or s.name}" '
                f'tvg-logo="{s.tvg_logo}" '
                f'group-title="{s.group}",{display_title}'
            )
            lines.append(extinf)
            lines.append(s.url)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def export_txt(grouped_streams: dict[str, list[ChannelStream]], file_path: str = OUTPUT_TXT):
    """
    导出 TVBox / DIYP 适用的 TXT 格式文件
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    lines = []

    # 严格按照 GROUP_ORDER 输出核心有效类别，杜绝海外杂乱分组
    sorted_groups = [g for g in GROUP_ORDER if g in grouped_streams]

    for group in sorted_groups:
        lines.append(f"{group},#genre#")
        streams = grouped_streams[group]
        for s in streams:
            lines.append(f"{s.name},{s.url}")
        lines.append("")  # 空行分隔类别

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).strip() + "\n")


def export_report(
    total_crawled: int,
    active_streams: list[ChannelStream],
    file_path: str = OUTPUT_REPORT
):
    """
    生成运行统计与运营商分布报告
    """
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    isp_stats = defaultdict(int)
    group_stats = defaultdict(int)

    for s in active_streams:
        isp_stats[s.isp_info or "其他"] += 1
        group_stats[s.group] += 1

    report_data = {
        "total_crawled": total_crawled,
        "total_active": len(active_streams),
        "available_rate": f"{(len(active_streams) / max(total_crawled, 1)) * 100:.1f}%",
        "isp_distribution": dict(isp_stats),
        "group_distribution": dict(group_stats),
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    return report_data

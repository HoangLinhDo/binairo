#!/usr/bin/env python3
"""
Plot benchmark-style comparison charts from play_game solve logs.

Usage:
    python plot_play_logs.py
    python plot_play_logs.py --log-dir results/play_logs
    python plot_play_logs.py --include-failed
    python plot_play_logs.py --no-show
    python plot_play_logs.py --save-plot results/play_logs_comparison.png
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

try:
    import matplotlib.pyplot as plt
    import numpy as np
except ImportError as exc:
    raise SystemExit(
        "matplotlib is required. Install with: pip install matplotlib"
    ) from exc


def load_logs(log_dir: Path) -> List[dict]:
    """Load solve records from JSON log files."""
    if not log_dir.exists():
        return []

    records: List[dict] = []
    for file_path in sorted(log_dir.glob("*.json")):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    records.append(data)
        except Exception:
            continue

    return records


def aggregate(records: List[dict], include_failed: bool = False) -> Dict[Tuple[str, int], dict]:
    """Aggregate average time/memory/steps by algorithm and board size."""
    grouped: Dict[Tuple[str, int], List[dict]] = {}

    for rec in records:
        algorithm = str(rec.get("algorithm", "")).lower().strip()
        size = rec.get("size")
        solved = bool(rec.get("solved", False))

        if algorithm not in {"dfs", "heuristic"}:
            continue
        if not isinstance(size, int):
            continue
        if not include_failed and not solved:
            continue

        grouped.setdefault((algorithm, size), []).append(rec)

    summary: Dict[Tuple[str, int], dict] = {}
    for key, items in grouped.items():
        times = [float(x.get("time_seconds", 0.0)) for x in items]
        memories = [float(x.get("memory_peak_mb", 0.0)) for x in items]
        steps = [float(x.get("steps", 0)) for x in items]
        solved_count = sum(1 for x in items if x.get("solved", False))

        summary[key] = {
            "count": len(items),
            "avg_time_seconds": sum(times) / len(times) if times else 0.0,
            "avg_memory_peak_mb": sum(memories) / len(memories) if memories else 0.0,
            "avg_steps": sum(steps) / len(steps) if steps else 0.0,
            "success_rate": solved_count / len(items) if items else 0.0,
        }

    return summary


def print_summary(summary: Dict[Tuple[str, int], dict]) -> None:
    """Print textual summary similar to benchmark output."""
    if not summary:
        print("No summary data available.")
        return

    sizes = sorted({size for _, size in summary.keys()})
    algorithms = ["dfs", "heuristic"]

    print("\n" + "=" * 80)
    print("PLAY LOG SUMMARY")
    print("=" * 80)

    print("\nAverage Time (seconds):")
    for size in sizes:
        row = f"{size}x{size:<8}"
        for algo in algorithms:
            item = summary.get((algo, size))
            if item:
                row += f"| {item['avg_time_seconds']:>10.4f}s {' ':>13}"
            else:
                row += f"| {'N/A':>25} "
        print(row)

    print("\nAverage Peak Memory (MB):")
    for size in sizes:
        row = f"{size}x{size:<8}"
        for algo in algorithms:
            item = summary.get((algo, size))
            if item:
                row += f"| {item['avg_memory_peak_mb']:>10.2f} MB {' ':>10}"
            else:
                row += f"| {'N/A':>25} "
        print(row)

    print("\nAverage Steps:")
    for size in sizes:
        row = f"{size}x{size:<8}"
        for algo in algorithms:
            item = summary.get((algo, size))
            if item:
                row += f"| {item['avg_steps']:>15.0f} {' ':>9}"
            else:
                row += f"| {'N/A':>25} "
        print(row)

    print("\nSuccess Rate (%):")
    for size in sizes:
        row = f"{size}x{size:<8}"
        for algo in algorithms:
            item = summary.get((algo, size))
            if item:
                row += f"| {item['success_rate'] * 100:>10.1f}% {' ':>12}"
            else:
                row += f"| {'N/A':>25} "
        print(row)

    print("=" * 80)


def plot_summary(summary: Dict[Tuple[str, int], dict], save_path: Optional[str] = None, show: bool = True) -> None:
    """Create benchmark-like comparison charts from aggregated play logs."""
    if not summary:
        print("No data to plot.")
        return

    algorithms = ["dfs", "heuristic"]
    labels = {"dfs": "DFS", "heuristic": "Heuristic Search (HS)"}
    colors = {"dfs": "#3498db", "heuristic": "#e74c3c"}
    sizes = sorted({size for _, size in summary.keys()})

    x = np.arange(len(sizes))
    width = 0.35

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    fig.suptitle("Binairo Play Logs: DFS vs Heuristic Search", fontsize=14, fontweight="bold")

    metric_defs = [
        ("avg_time_seconds", "Average Time (seconds)", "Time (s)"),
        ("avg_memory_peak_mb", "Average Peak Memory (MB)", "Memory (MB)"),
        ("avg_steps", "Average Steps", "Steps"),
    ]

    for ax, (metric, title, y_label) in zip(axes, metric_defs):
        for i, algo in enumerate(algorithms):
            values = []
            for size in sizes:
                item = summary.get((algo, size))
                values.append(item[metric] if item else 0)

            offset = width * (i - 0.5)
            bars = ax.bar(x + offset, values, width, label=labels[algo], color=colors[algo])

            for bar, val in zip(bars, values):
                if val > 0:
                    y = bar.get_height()
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        y,
                        f"{val:.3f}" if metric != "avg_steps" else f"{int(val)}",
                        ha="center",
                        va="bottom",
                        fontsize=8,
                    )

        ax.set_title(title)
        ax.set_xlabel("Board Size")
        ax.set_ylabel(y_label)
        ax.set_xticks(x)
        ax.set_xticklabels([f"{s}x{s}" for s in sizes])
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

    plt.tight_layout()

    if save_path:
        Path(save_path).parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(save_path, dpi=300, bbox_inches="tight")
        print(f"Saved plot to: {save_path}")

    if show:
        plt.show()


def parse_args():
    parser = argparse.ArgumentParser(description="Plot benchmark-style graphs from play_game solve logs")
    parser.add_argument(
        "--log-dir",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "results", "play_logs"),
        help="Directory containing solve log JSON files",
    )
    parser.add_argument(
        "--include-failed",
        action="store_true",
        help="Include failed solves in averages",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not display plot window",
    )
    parser.add_argument(
        "--save-plot",
        type=str,
        default=os.path.join(os.path.dirname(__file__), "results", "play_logs_comparison.png"),
        help="Path to save generated chart image",
    )
    parser.add_argument(
        "--output-json",
        type=str,
        default=None,
        help="Optional path to save aggregated summary JSON",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    log_dir = Path(args.log_dir)
    print(f"Loading logs from: {log_dir}")
    records = load_logs(log_dir)

    if not records:
        print(f"No log files found in: {log_dir}")
        return

    summary = aggregate(records, include_failed=args.include_failed)

    if not summary:
        print("No valid records found after filtering.")
        return

    print(f"Loaded {len(records)} log files from: {log_dir}")
    print_summary(summary)

    if args.output_json:
        output_path = Path(args.output_json)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        flattened = []
        for (algorithm, size), item in sorted(summary.items(), key=lambda x: (x[0][1], x[0][0])):
            flattened.append({"algorithm": algorithm, "size": size, **item})
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(flattened, f, indent=2)
        print(f"Saved summary JSON to: {output_path}")

    plot_summary(summary, save_path=args.save_plot, show=not args.no_show)


if __name__ == "__main__":
    main()

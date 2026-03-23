"""
Benchmark module for Binairo solver.
Runs benchmarks and generates comparison graphs.
"""

import json
import os
import sys
import time
import tracemalloc
import gc
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Preferred when running as package: `python -m nmai_binairo.benchmark`
    from nmai_binairo.solver_dfs import DFSSolver
    from nmai_binairo.solver_heuristic import HeuristicSolver
    from nmai_binairo.board import BinairoBoard
except Exception:
    # Fallback when running script directly from inside the package folder:
    # `cd nmai_binairo && python benchmark.py`
    from solver_dfs import DFSSolver
    from solver_heuristic import HeuristicSolver
    from board import BinairoBoard

try:
    import matplotlib.pyplot as plt
    import numpy as np
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Warning: matplotlib not available. Install with: pip install matplotlib")


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""
    algorithm: str
    size: int
    puzzle_id: int
    time_seconds: float
    memory_peak_mb: float
    steps: int  # nodes explored
    backtracks: int
    solved: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            'algorithm': self.algorithm,
            'size': self.size,
            'puzzle_id': self.puzzle_id,
            'time_seconds': self.time_seconds,
            'memory_peak_mb': self.memory_peak_mb,
            'steps': self.steps,
            'backtracks': self.backtracks,
            'solved': self.solved
        }


@dataclass
class BenchmarkSummary:
    """Summary of benchmark results for an algorithm/size combination."""
    algorithm: str
    size: int
    num_puzzles: int
    avg_time_seconds: float
    avg_memory_peak_mb: float
    avg_steps: float
    avg_backtracks: float
    success_rate: float
    all_times: List[float] = field(default_factory=list)
    all_memories: List[float] = field(default_factory=list)
    all_steps: List[int] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'algorithm': self.algorithm,
            'size': self.size,
            'num_puzzles': self.num_puzzles,
            'avg_time_seconds': self.avg_time_seconds,
            'avg_memory_peak_mb': self.avg_memory_peak_mb,
            'avg_steps': self.avg_steps,
            'avg_backtracks': self.avg_backtracks,
            'success_rate': self.success_rate
        }


class Benchmark:
    """
    Benchmark runner for Binairo solvers.
    """

    def __init__(self, results_dir: Optional[str] = None):
        """
        Initialize benchmark runner.

        Args:
            results_dir: Directory to save results
        """
        if results_dir is None:
            results_dir = os.path.join(os.path.dirname(__file__), "results")
        self.results_dir = Path(results_dir)
        self.results_dir.mkdir(parents=True, exist_ok=True)

        self.results: List[BenchmarkResult] = []
        self.summaries: Dict[Tuple[str, int], BenchmarkSummary] = {}

    def run_single_benchmark(self, puzzle: List[List], algorithm: str,
                             puzzle_id: int = 0) -> BenchmarkResult:
        """
        Run a single benchmark.

        Args:
            puzzle: The puzzle to solve
            algorithm: 'dfs' or 'heuristic'
            puzzle_id: Identifier for this puzzle

        Returns:
            BenchmarkResult
        """
        size = len(puzzle)

        # Select solver
        if algorithm.lower() in ['dfs', 'depth-first']:
            solver = DFSSolver()
        else:
            solver = HeuristicSolver()

        # Run garbage collection
        gc.collect()

        # Measure performance
        tracemalloc.start()
        start_time = time.perf_counter()

        try:
            solution, stats = solver.solve([row[:] for row in puzzle])
            solved = solution is not None
        except Exception as e:
            solved = False
            stats = {'nodes_explored': 0, 'backtracks': 0}

        end_time = time.perf_counter()
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        result = BenchmarkResult(
            algorithm=algorithm,
            size=size,
            puzzle_id=puzzle_id,
            time_seconds=end_time - start_time,
            memory_peak_mb=peak / (1024 * 1024),
            steps=stats.get('nodes_explored', 0),
            backtracks=stats.get('backtracks', 0),
            solved=solved
        )

        self.results.append(result)
        return result

    def run_benchmarks(self, puzzles: Dict[int, List[List[List]]],
                       algorithms: List[str] = None,
                       verbose: bool = True) -> Dict[Tuple[str, int], BenchmarkSummary]:
        """
        Run benchmarks on multiple puzzles.

        Args:
            puzzles: Dictionary mapping size to list of puzzles
            algorithms: List of algorithms to test
            verbose: Print progress

        Returns:
            Dictionary of summaries
        """
        algorithms = algorithms or ['dfs', 'heuristic']

        self.results = []
        self.summaries = {}

        for algo in algorithms:
            for size, puzzle_list in puzzles.items():
                if verbose:
                    print(f"\nRunning {algo.upper()} on {size}x{size} puzzles...")

                for i, puzzle in enumerate(puzzle_list):
                    result = self.run_single_benchmark(puzzle, algo, i)
                    if verbose:
                        status = "OK" if result.solved else "FAILED"
                        print(f"  Puzzle {i+1}/{len(puzzle_list)}: {result.time_seconds:.4f}s, "
                              f"{result.memory_peak_mb:.2f}MB, {result.steps} steps [{status}]")

                # Calculate summary
                algo_results = [r for r in self.results
                               if r.algorithm == algo and r.size == size]

                if algo_results:
                    success_count = sum(1 for r in algo_results if r.solved)
                    all_times = [r.time_seconds for r in algo_results if r.solved]
                    all_memories = [r.memory_peak_mb for r in algo_results if r.solved]
                    all_steps = [r.steps for r in algo_results if r.solved]
                    all_backtracks = [r.backtracks for r in algo_results if r.solved]

                    summary = BenchmarkSummary(
                        algorithm=algo,
                        size=size,
                        num_puzzles=len(algo_results),
                        avg_time_seconds=sum(all_times) / len(all_times) if all_times else 0,
                        avg_memory_peak_mb=sum(all_memories) / len(all_memories) if all_memories else 0,
                        avg_steps=sum(all_steps) / len(all_steps) if all_steps else 0,
                        avg_backtracks=sum(all_backtracks) / len(all_backtracks) if all_backtracks else 0,
                        success_rate=success_count / len(algo_results),
                        all_times=all_times,
                        all_memories=all_memories,
                        all_steps=all_steps
                    )
                    self.summaries[(algo, size)] = summary

        return self.summaries

    def print_summary(self):
        """Print a formatted summary of results."""
        print("\n" + "=" * 80)
        print("BENCHMARK SUMMARY")
        print("=" * 80)

        # Get unique sizes and algorithms
        sizes = sorted(set(s[1] for s in self.summaries.keys()))
        algorithms = sorted(set(s[0] for s in self.summaries.keys()))

        # Print header
        header = f"{'Size':<10}"
        for algo in algorithms:
            header += f"| {algo.upper():<25} "
        print(header)
        print("-" * 80)

        # Print time comparison
        print("\nAverage Time (seconds):")
        for size in sizes:
            row = f"{size}x{size:<8}"
            for algo in algorithms:
                key = (algo, size)
                if key in self.summaries:
                    row += f"| {self.summaries[key].avg_time_seconds:>10.4f}s {' ':>13}"
                else:
                    row += f"| {'N/A':>25} "
            print(row)

        # Print memory comparison
        print("\nAverage Peak Memory (MB):")
        for size in sizes:
            row = f"{size}x{size:<8}"
            for algo in algorithms:
                key = (algo, size)
                if key in self.summaries:
                    row += f"| {self.summaries[key].avg_memory_peak_mb:>10.2f} MB {' ':>10}"
                else:
                    row += f"| {'N/A':>25} "
            print(row)

        # Print steps comparison
        print("\nAverage Steps (Nodes Explored):")
        for size in sizes:
            row = f"{size}x{size:<8}"
            for algo in algorithms:
                key = (algo, size)
                if key in self.summaries:
                    row += f"| {self.summaries[key].avg_steps:>15.0f} {' ':>9}"
                else:
                    row += f"| {'N/A':>25} "
            print(row)

        print("\n" + "=" * 80)

    def plot_results(self, save_path: Optional[str] = None, show: bool = True):
        """
        Plot benchmark results as bar charts comparing DFS and Heuristic.

        Args:
            save_path: Path to save the plot (optional)
            show: Whether to display the plot
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Error: matplotlib not available for plotting")
            return

        sizes = sorted(set(s[1] for s in self.summaries.keys()))
        algorithms = ['dfs', 'heuristic']
        algo_labels = {'dfs': 'DFS', 'heuristic': 'Heuristic Search (HS)'}
        colors = {'dfs': '#3498db', 'heuristic': '#e74c3c'}

        # Create figure with 3 subplots (time, memory, steps)
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        fig.suptitle('Binairo Solver Benchmark: DFS vs Heuristic Search', fontsize=14, fontweight='bold')

        x = np.arange(len(sizes))
        width = 0.35

        # Plot 1: Average Time
        ax1 = axes[0]
        for i, algo in enumerate(algorithms):
            times = []
            for size in sizes:
                key = (algo, size)
                if key in self.summaries:
                    times.append(self.summaries[key].avg_time_seconds)
                else:
                    times.append(0)

            offset = width * (i - 0.5)
            bars = ax1.bar(x + offset, times, width, label=algo_labels[algo], color=colors[algo])

            # Add value labels on bars
            for bar, val in zip(bars, times):
                height = bar.get_height()
                ax1.annotate(f'{val:.3f}s',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)

        ax1.set_xlabel('Board Size', fontweight='bold')
        ax1.set_ylabel('Average Time (seconds)', fontweight='bold')
        ax1.set_title('Average Solving Time Comparison')
        ax1.set_xticks(x)
        ax1.set_xticklabels([f'{s}x{s}' for s in sizes])
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # Plot 2: Average Memory
        ax2 = axes[1]
        for i, algo in enumerate(algorithms):
            memories = []
            for size in sizes:
                key = (algo, size)
                if key in self.summaries:
                    memories.append(self.summaries[key].avg_memory_peak_mb)
                else:
                    memories.append(0)

            offset = width * (i - 0.5)
            bars = ax2.bar(x + offset, memories, width, label=algo_labels[algo], color=colors[algo])

            # Add value labels on bars
            for bar, val in zip(bars, memories):
                height = bar.get_height()
                ax2.annotate(f'{val:.2f}MB',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)

        ax2.set_xlabel('Board Size', fontweight='bold')
        ax2.set_ylabel('Average Memory (MB)', fontweight='bold')
        ax2.set_title('Average Peak Memory Comparison')
        ax2.set_xticks(x)
        ax2.set_xticklabels([f'{s}x{s}' for s in sizes])
        ax2.legend()
        ax2.grid(axis='y', alpha=0.3)

        # Plot 3: Average Steps (Nodes Explored)
        ax3 = axes[2]
        for i, algo in enumerate(algorithms):
            steps = []
            for size in sizes:
                key = (algo, size)
                if key in self.summaries:
                    steps.append(self.summaries[key].avg_steps)
                else:
                    steps.append(0)

            offset = width * (i - 0.5)
            bars = ax3.bar(x + offset, steps, width, label=algo_labels[algo], color=colors[algo])

            # Add value labels on bars
            for bar, val in zip(bars, steps):
                height = bar.get_height()
                ax3.annotate(f'{int(val)}',
                           xy=(bar.get_x() + bar.get_width() / 2, height),
                           xytext=(0, 3),
                           textcoords="offset points",
                           ha='center', va='bottom', fontsize=8)

        ax3.set_xlabel('Board Size', fontweight='bold')
        ax3.set_ylabel('Average Steps (Nodes Explored)', fontweight='bold')
        ax3.set_title('Average Steps Comparison')
        ax3.set_xticks(x)
        ax3.set_xticklabels([f'{s}x{s}' for s in sizes])
        ax3.legend()
        ax3.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")

        if show:
            plt.show()

    def plot_detailed_results(self, save_path: Optional[str] = None, show: bool = True):
        """
        Plot detailed benchmark results with all 3 metrics.

        Args:
            save_path: Path to save the plot
            show: Whether to display the plot
        """
        if not MATPLOTLIB_AVAILABLE:
            print("Error: matplotlib not available for plotting")
            return

        sizes = sorted(set(s[1] for s in self.summaries.keys()))
        algorithms = ['dfs', 'heuristic']
        algo_labels = {'dfs': 'DFS', 'heuristic': 'Heuristic Search'}
        colors = {'dfs': '#3498db', 'heuristic': '#e74c3c'}

        # Create figure with 3 subplots
        fig, axes = plt.subplots(1, 3, figsize=(16, 5))
        fig.suptitle('Binairo Solver Detailed Benchmark Results', fontsize=14, fontweight='bold')

        x = np.arange(len(sizes))
        width = 0.35

        metrics = [
            ('avg_time_seconds', 'Time (seconds)', 'Average Solving Time'),
            ('avg_memory_peak_mb', 'Memory (MB)', 'Peak Memory Usage'),
            ('avg_steps', 'Steps', 'Nodes Explored'),
        ]

        for ax, (metric, ylabel, title) in zip(axes, metrics):
            for i, algo in enumerate(algorithms):
                values = []
                for size in sizes:
                    key = (algo, size)
                    if key in self.summaries:
                        values.append(getattr(self.summaries[key], metric))
                    else:
                        values.append(0)

                offset = width * (i - 0.5)
                bars = ax.bar(x + offset, values, width, label=algo_labels[algo], color=colors[algo])

                # Add value labels
                for bar, val in zip(bars, values):
                    height = bar.get_height()
                    if metric == 'avg_steps':
                        label = f'{int(val)}'
                    elif metric == 'avg_time_seconds':
                        label = f'{val:.3f}'
                    else:
                        label = f'{val:.2f}'
                    ax.annotate(label,
                               xy=(bar.get_x() + bar.get_width() / 2, height),
                               xytext=(0, 3),
                               textcoords="offset points",
                               ha='center', va='bottom', fontsize=7)

            ax.set_xlabel('Board Size', fontweight='bold')
            ax.set_ylabel(ylabel, fontweight='bold')
            ax.set_title(title)
            ax.set_xticks(x)
            ax.set_xticklabels([f'{s}x{s}' for s in sizes])
            ax.legend()
            ax.grid(axis='y', alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=150, bbox_inches='tight')
            print(f"Plot saved to: {save_path}")

        if show:
            plt.show()

    def save_results(self, filename: str = "benchmark_results.json"):
        """Save results to JSON file."""
        filepath = self.results_dir / filename

        data = {
            'results': [r.to_dict() for r in self.results],
            'summaries': {f"{k[0]}_{k[1]}": v.to_dict() for k, v in self.summaries.items()}
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"Results saved to: {filepath}")

    def load_results(self, filename: str = "benchmark_results.json") -> bool:
        """Load results from JSON file."""
        filepath = self.results_dir / filename

        if not filepath.exists():
            return False

        with open(filepath, 'r') as f:
            data = json.load(f)

        self.results = [BenchmarkResult(**r) for r in data['results']]

        self.summaries = {}
        for key, value in data['summaries'].items():
            algo, size = key.rsplit('_', 1)
            self.summaries[(algo, int(size))] = BenchmarkSummary(**value)

        return True


def run_benchmark_cli():
    """Run benchmark from command line."""
    import argparse

    parser = argparse.ArgumentParser(description='Binairo Solver Benchmark')
    parser.add_argument('--sizes', type=int, nargs='+', default=[6, 8, 10],
                        help='Board sizes to test (default: 6 8 10)')
    parser.add_argument('--count', type=int, default=5,
                        help='Number of puzzles per size (default: 5)')
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard', 'very_hard'],
                        default='medium', help='Puzzle difficulty (default: medium)')
    parser.add_argument('--algorithms', nargs='+', default=['dfs', 'heuristic'],
                        choices=['dfs', 'heuristic'],
                        help='Algorithms to benchmark (default: dfs heuristic)')
    parser.add_argument('--no-plot', action='store_true',
                        help='Skip plotting results')
    parser.add_argument('--save-plot', type=str, default=None,
                        help='Path to save plot image')
    parser.add_argument('--output', type=str, default='benchmark_results.json',
                        help='Output file for results')

    args = parser.parse_args()

    print("=" * 60)
    print("BINAIRO SOLVER BENCHMARK")
    print("=" * 60)
    print(f"Sizes: {args.sizes}")
    print(f"Puzzles per size: {args.count}")
    print(f"Difficulty: {args.difficulty}")
    print(f"Algorithms: {args.algorithms}")
    print("=" * 60)

    # Generate test puzzles
    try:
        from nmai_binairo.testcases import TestCases
    except Exception:
        from testcases import TestCases
    tc = TestCases()

    print("\nGenerating test puzzles...")
    puzzles = tc.get_test_puzzles(sizes=args.sizes, count=args.count, difficulty=args.difficulty)

    # Run benchmarks
    benchmark = Benchmark()
    benchmark.run_benchmarks(puzzles, algorithms=args.algorithms)

    # Print summary
    benchmark.print_summary()

    # Save results
    benchmark.save_results(args.output)

    # Plot results
    if not args.no_plot:
        save_path = args.save_plot or str(benchmark.results_dir / "benchmark_plot.png")
        benchmark.plot_results(save_path=save_path, show=True)


if __name__ == "__main__":
    run_benchmark_cli()

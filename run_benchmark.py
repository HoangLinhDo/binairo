#!/usr/bin/env python3
"""
Benchmark Runner for Binairo Solver

Runs benchmarks comparing DFS and Heuristic Search algorithms.
Generates graphs comparing average results like in the report.

Usage:
    python run_benchmark.py                           # Run default benchmark
    python run_benchmark.py --sizes 6 8 10 14        # Custom sizes
    python run_benchmark.py --count 10               # 10 puzzles per size
    python run_benchmark.py --no-plot                # Skip plotting
    python run_benchmark.py --save-plot results.png  # Save plot to file
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmai_binairo.benchmark import Benchmark, run_benchmark_cli
from nmai_binairo.testcases import TestCases


def run_quick_benchmark():
    """Run a quick benchmark for demonstration."""
    print("=" * 60)
    print("QUICK BINAIRO BENCHMARK")
    print("=" * 60)
    print()

    sizes = [6, 8]
    count = 3

    print(f"Sizes: {sizes}")
    print(f"Puzzles per size: {count}")
    print()

    # Generate puzzles
    tc = TestCases()
    puzzles = tc.get_test_puzzles(sizes=sizes, count=count, difficulty='medium')

    # Run benchmark
    benchmark = Benchmark()
    benchmark.run_benchmarks(puzzles, algorithms=['dfs', 'heuristic'])

    # Print summary
    benchmark.print_summary()

    # Plot results
    try:
        benchmark.plot_results(show=True)
    except Exception as e:
        print(f"\nCouldn't show plot: {e}")
        print("Install matplotlib with: pip install matplotlib")


def run_full_benchmark(args):
    """Run full benchmark with command line arguments."""
    print("=" * 60)
    print("BINAIRO SOLVER BENCHMARK")
    print("=" * 60)
    print(f"Sizes: {args.sizes}")
    print(f"Puzzles per size: {args.count}")
    print(f"Difficulty: {args.difficulty}")
    print(f"Algorithms: {args.algorithms}")
    print("=" * 60)
    print()

    # Generate puzzles
    print("Generating test puzzles...")
    tc = TestCases()
    puzzles = tc.get_test_puzzles(
        sizes=args.sizes,
        count=args.count,
        difficulty=args.difficulty
    )

    # Run benchmark
    benchmark = Benchmark()
    benchmark.run_benchmarks(puzzles, algorithms=args.algorithms)

    # Print summary
    benchmark.print_summary()

    # Save results
    if args.output:
        benchmark.save_results(args.output)

    # Plot results
    if not args.no_plot:
        try:
            save_path = args.save_plot
            if save_path is None and not args.no_save:
                save_path = os.path.join(
                    os.path.dirname(__file__),
                    'results',
                    'benchmark_comparison.png'
                )
                os.makedirs(os.path.dirname(save_path), exist_ok=True)

            # Generate both basic and detailed plots
            benchmark.plot_results(save_path=save_path, show=not args.no_show)

            if args.detailed_plot:
                detailed_path = save_path.replace('.png', '_detailed.png') if save_path else None
                benchmark.plot_detailed_results(save_path=detailed_path, show=not args.no_show)

        except Exception as e:
            print(f"\nCouldn't create plot: {e}")
            print("Install matplotlib with: pip install matplotlib")


def main():
    parser = argparse.ArgumentParser(
        description='Run Binairo Solver Benchmarks',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmark.py                      # Run default benchmark
  python run_benchmark.py --quick              # Quick demo benchmark
  python run_benchmark.py --sizes 6 8 10 14   # Custom board sizes
  python run_benchmark.py --count 20          # 20 puzzles per size
  python run_benchmark.py --difficulty hard   # Hard difficulty puzzles
  python run_benchmark.py --no-show           # Save plot but don't show
  python run_benchmark.py --detailed-plot     # Generate detailed 3-metric plot

Output:
  The benchmark will generate:
  - Console summary with time/memory/steps comparison
  - Bar chart comparing DFS vs Heuristic Search (saved to results/)
  - JSON results file (if --output specified)
        """
    )

    parser.add_argument('--quick', action='store_true',
                        help='Run quick demo benchmark')
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
                        help='Skip generating plots')
    parser.add_argument('--no-show', action='store_true',
                        help='Don\'t display plot (only save)')
    parser.add_argument('--no-save', action='store_true',
                        help='Don\'t save plot to file')
    parser.add_argument('--save-plot', type=str, default=None,
                        help='Path to save plot image')
    parser.add_argument('--detailed-plot', action='store_true',
                        help='Generate detailed plot with all 3 metrics')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file for JSON results')

    args = parser.parse_args()

    if args.quick:
        run_quick_benchmark()
    else:
        run_full_benchmark(args)


if __name__ == "__main__":
    main()

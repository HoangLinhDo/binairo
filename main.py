"""
Main entry point for the improved Binairo solver.
Provides CLI interface and benchmark runner.
"""

import argparse
import sys
import os
import json
from typing import Optional, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nmai_binairo.board import BinairoBoard
from nmai_binairo.constraints import BinairoConstraints
from nmai_binairo.solver_dfs import DFSSolver, solve_dfs
from nmai_binairo.solver_heuristic import HeuristicSolver, AdvancedHeuristicSolver, solve_heuristic
from nmai_binairo.benchmark_utils import measure_performance, PerformanceStats

try:
    from testcases.puzzle_generator import PuzzleGenerator
    from testcases.test_cases import TestCases
    from testcases.benchmark import Benchmark
    TESTCASES_AVAILABLE = True
except ImportError:
    TESTCASES_AVAILABLE = False


def solve_puzzle(puzzle: List[List], algorithm: str = 'heuristic', verbose: bool = True) -> Optional[List[List]]:
    """
    Solve a Binairo puzzle.

    Args:
        puzzle: 2D list with None for empty cells
        algorithm: 'dfs', 'heuristic', or 'advanced'
        verbose: Print progress information

    Returns:
        Solution or None if no solution found
    """
    if algorithm == 'dfs':
        solver = DFSSolver()
    elif algorithm == 'advanced':
        solver = AdvancedHeuristicSolver()
    else:
        solver = HeuristicSolver()

    if verbose:
        print(f"Solving with {algorithm}...")
        board = BinairoBoard(board=puzzle)
        print("Initial puzzle:")
        print(board)
        print()

    solution, stats = solver.solve(puzzle)

    if verbose:
        if solution:
            print("Solution found!")
            result_board = BinairoBoard(board=solution)
            print(result_board)
            print()
            print("Statistics:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print("No solution found.")

    return solution


def run_benchmark(sizes: List[int] = None, algorithms: List[str] = None,
                  runs: int = 3, output_file: Optional[str] = None):
    """
    Run benchmarks on multiple puzzle sizes and algorithms.

    Args:
        sizes: List of board sizes to test
        algorithms: List of algorithms to test
        runs: Number of runs per test
        output_file: Optional file to save results
    """
    if not TESTCASES_AVAILABLE:
        print("Error: testcases module not available")
        return

    sizes = sizes or [6, 8, 10]
    algorithms = algorithms or ['dfs', 'heuristic', 'advanced']

    print("=" * 70)
    print("BINAIRO SOLVER BENCHMARK")
    print("=" * 70)
    print(f"Sizes: {sizes}")
    print(f"Algorithms: {algorithms}")
    print(f"Runs per test: {runs}")
    print("=" * 70)
    print()

    results = []
    benchmark = Benchmark()
    generator = PuzzleGenerator(seed=42)

    for size in sizes:
        print(f"\n{'='*50}")
        print(f"Testing {size}x{size} puzzles")
        print(f"{'='*50}")

        # Generate a puzzle
        puzzle, _ = generator.generate_puzzle(size, difficulty=0.6)
        board = BinairoBoard(board=puzzle)
        print("Puzzle:")
        print(board.to_string())
        print(f"Empty cells: {board.get_empty_count()}")
        print()

        size_results = {'size': size, 'puzzles': 1}

        for algo in algorithms:
            print(f"\n--- {algo.upper()} ---")

            if algo == 'dfs':
                solver = DFSSolver()
            elif algo == 'advanced':
                solver = AdvancedHeuristicSolver()
            else:
                solver = HeuristicSolver()

            # Run multiple times
            times = []
            memories = []
            nodes_list = []
            success = True

            for run in range(runs):
                result, stats = measure_performance(
                    solver.solve,
                    [row[:] for row in puzzle]  # Fresh copy each run
                )

                solution, solver_stats = result
                if solution is None:
                    success = False
                    break

                times.append(stats.time_seconds)
                memories.append(stats.memory_peak_mb)
                nodes_list.append(solver_stats.get('nodes_explored', 0))

            if success:
                avg_time = sum(times) / len(times)
                avg_memory = sum(memories) / len(memories)
                avg_nodes = sum(nodes_list) / len(nodes_list)

                print(f"  Success: Yes")
                print(f"  Time: {avg_time:.4f}s (avg over {runs} runs)")
                print(f"  Memory (peak): {avg_memory:.2f} MB")
                print(f"  Nodes explored: {int(avg_nodes)}")

                size_results[algo] = {
                    'success': True,
                    'time_avg': avg_time,
                    'time_all': times,
                    'memory_peak': avg_memory,
                    'nodes_explored': int(avg_nodes)
                }
            else:
                print(f"  Success: No")
                size_results[algo] = {'success': False}

        results.append(size_results)

    # Print summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    header = f"{'Size':<10}"
    for algo in algorithms:
        header += f"{algo.upper():<20}"
    print(header)
    print("-" * 70)

    for result in results:
        row = f"{result['size']}x{result['size']:<8}"
        for algo in algorithms:
            if algo in result and result[algo]['success']:
                time_str = f"{result[algo]['time_avg']:.4f}s"
                row += f"{time_str:<20}"
            else:
                row += f"{'Failed':<20}"
        print(row)

    # Save results if requested
    if output_file:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {output_file}")


def compare_with_original():
    """Compare improved solver with original Binairo_Game_represent."""
    if not TESTCASES_AVAILABLE:
        print("Error: testcases module not available")
        return

    print("=" * 70)
    print("COMPARISON: Improved vs Original Solver")
    print("=" * 70)
    print()

    generator = PuzzleGenerator(seed=42)
    benchmark = Benchmark()

    sizes = [6, 8, 10]

    for size in sizes:
        print(f"\n--- {size}x{size} Puzzle ---")

        puzzle, _ = generator.generate_puzzle(size, difficulty=0.6)

        # Improved DFS
        dfs_solver = DFSSolver()
        _, dfs_stats = measure_performance(dfs_solver.solve, [row[:] for row in puzzle])
        dfs_solution, dfs_solver_stats = dfs_stats.result

        # Improved Heuristic
        heu_solver = HeuristicSolver()
        _, heu_stats = measure_performance(heu_solver.solve, [row[:] for row in puzzle])
        heu_solution, heu_solver_stats = heu_stats.result

        # Advanced Heuristic
        adv_solver = AdvancedHeuristicSolver()
        _, adv_stats = measure_performance(adv_solver.solve, [row[:] for row in puzzle])
        adv_solution, adv_solver_stats = adv_stats.result

        print(f"{'Solver':<25} {'Time':<15} {'Memory':<15} {'Nodes':<15}")
        print("-" * 70)

        if dfs_solution:
            print(f"{'DFS':<25} {dfs_stats.time_seconds:.4f}s{'':<7} "
                  f"{dfs_stats.memory_peak_mb:.2f} MB{'':<7} "
                  f"{dfs_solver_stats['nodes_explored']}")

        if heu_solution:
            print(f"{'Heuristic (MRV)':<25} {heu_stats.time_seconds:.4f}s{'':<7} "
                  f"{heu_stats.memory_peak_mb:.2f} MB{'':<7} "
                  f"{heu_solver_stats['nodes_explored']}")

        if adv_solution:
            print(f"{'Advanced (MRV+FC)':<25} {adv_stats.time_seconds:.4f}s{'':<7} "
                  f"{adv_stats.memory_peak_mb:.2f} MB{'':<7} "
                  f"{adv_solver_stats['nodes_explored']}")


def run_gui():
    """Run the GUI visualizer."""
    try:
        from nmai_binairo.visualizer import BinairoVisualizer
        vis = BinairoVisualizer(board_size=6)

        if TESTCASES_AVAILABLE:
            from testcases.puzzle_generator import PuzzleGenerator
            gen = PuzzleGenerator()
            puzzle, _ = gen.generate_puzzle(6, difficulty=0.6)
            vis.set_puzzle(puzzle)

        vis.run()
    except ImportError as e:
        print(f"Error: Could not start GUI. {e}")
        print("Make sure pygame is installed: pip install pygame")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Improved Binairo Solver with DFS and Heuristic Search",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --gui                    # Run GUI
  python main.py --solve 6 --algo dfs     # Solve a 6x6 puzzle with DFS
  python main.py --benchmark              # Run benchmarks
  python main.py --compare                # Compare solvers
        """
    )

    parser.add_argument('--gui', action='store_true', help='Run GUI visualizer')
    parser.add_argument('--solve', type=int, help='Generate and solve a puzzle of given size')
    parser.add_argument('--algo', choices=['dfs', 'heuristic', 'advanced'], default='heuristic',
                        help='Algorithm to use (default: heuristic)')
    parser.add_argument('--benchmark', action='store_true', help='Run benchmarks')
    parser.add_argument('--sizes', type=int, nargs='+', default=[6, 8, 10],
                        help='Puzzle sizes for benchmark')
    parser.add_argument('--runs', type=int, default=3, help='Number of runs per benchmark')
    parser.add_argument('--output', type=str, help='Output file for benchmark results')
    parser.add_argument('--compare', action='store_true', help='Compare all solvers')
    parser.add_argument('--puzzle', type=str, help='Puzzle string to solve (. for empty, 0, 1)')

    args = parser.parse_args()

    if args.gui:
        run_gui()
    elif args.benchmark:
        run_benchmark(sizes=args.sizes, runs=args.runs, output_file=args.output)
    elif args.compare:
        compare_with_original()
    elif args.solve:
        if TESTCASES_AVAILABLE:
            generator = PuzzleGenerator()
            puzzle, _ = generator.generate_puzzle(args.solve, difficulty=0.6)
        else:
            print("Error: testcases module not available")
            return
        solve_puzzle(puzzle, algorithm=args.algo)
    elif args.puzzle:
        board = BinairoBoard.from_string(args.puzzle)
        solve_puzzle(board.to_list(), algorithm=args.algo)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

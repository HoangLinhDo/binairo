"""
NMAI Binairo Solver Package

A complete Binairo puzzle solver implementing DFS and Heuristic Search algorithms.

Features:
- DFS (Depth-First Search) solver
- Heuristic solver with constraint propagation
- Benchmark utilities with plotting
- Pygame visualization
- Testcase generation

Usage:
    from nmai_binairo import BinairoBoard, DFSSolver, HeuristicSolver

    puzzle = [[None, 1, ...], ...]
    solver = HeuristicSolver()
    solution, stats = solver.solve(puzzle)
"""

from .board import BinairoBoard
from .constraints import BinairoConstraints
from .solver_dfs import DFSSolver, solve_dfs
from .solver_heuristic import HeuristicSolver, AdvancedHeuristicSolver, solve_heuristic
from .benchmark_utils import measure_performance, PerformanceStats, PerformanceMonitor

__version__ = '1.0.0'

__all__ = [
    # Board
    'BinairoBoard',
    'BinairoConstraints',
    # Solvers
    'DFSSolver',
    'HeuristicSolver',
    'AdvancedHeuristicSolver',
    'solve_dfs',
    'solve_heuristic',
    # Benchmark
    'measure_performance',
    'PerformanceStats',
    'PerformanceMonitor',
]

# NMAI Binairo Solver

A complete Binairo puzzle solver implementing **DFS (Depth-First Search)** and **Heuristic Search** algorithms for the NMAI course project.

## Features

- **Two Solving Algorithms**:
  - DFS (Depth-First Search) - Blind backtracking search
  - Heuristic Search - Constraint propagation with logical deductions

- **Interactive Game**: Play Binairo puzzles with a Pygame GUI
- **Benchmarking**: Compare algorithm performance with graphs
- **Testcase Generation**: Generate puzzles of various sizes and difficulties

## Project Structure

```
nmai_binairo/
├── __init__.py           # Package initialization
├── board.py              # Board representation
├── constraints.py        # Constraint validation
├── solver_dfs.py         # DFS solver implementation
├── solver_heuristic.py   # Heuristic solver implementation
├── benchmark.py          # Benchmark utilities with plotting
├── benchmark_utils.py    # Performance measurement utilities
├── visualizer.py         # Pygame visualization
├── play_game.py          # Interactive game script
├── fetch_testcases.py    # Testcase generator script
├── run_benchmark.py      # Benchmark runner script
├── testcases/            # Test cases and cache
│   ├── __init__.py
│   ├── puzzle_generator.py
│   └── test_cases.py
└── results/              # Benchmark results
```

## Installation

```bash
# Install dependencies
pip install pygame matplotlib numpy requests

# Or use requirements.txt
pip install -r requirements.txt
```

## Quick Start

### 1. Play the Game

```bash
# Start with default 6x6 puzzle
python play_game.py

# Start with specific size
python play_game.py --size 10

# Start with hard difficulty
python play_game.py --difficulty hard
```

**Game Controls**:
- Left click: Place White (1) or clear
- Right click: Place Black (0) or clear
- N key: New puzzle
- R key: Reset puzzle
- V key: Validate board

### 2. Generate Testcases

```bash
# Generate default testcases (5 puzzles each for 6x6, 8x8, 10x10)
python fetch_testcases.py

# Generate custom testcases
python fetch_testcases.py --sizes 6 8 10 14 --count 10 --difficulty hard

# List existing testcases
python fetch_testcases.py --list

# Show a specific puzzle
python fetch_testcases.py --show 6 1
```

### 3. Run Benchmarks

```bash
# Quick benchmark demo
python run_benchmark.py --quick

# Full benchmark with graphs
python run_benchmark.py

# Custom benchmark
python run_benchmark.py --sizes 6 8 10 14 --count 10 --difficulty medium

# Benchmark with detailed 3-metric plot
python run_benchmark.py --detailed-plot

# Save results without showing
python run_benchmark.py --no-show --save-plot benchmark.png
```

## Benchmark Output

The benchmark generates:
1. **Console Summary**: Time, memory, and steps comparison
2. **Comparison Graphs**: Bar charts comparing DFS vs Heuristic Search
3. **JSON Results**: Detailed results saved to file

Example output:
```
================================================================================
BENCHMARK SUMMARY
================================================================================

Average Time (seconds):
6x6       |     0.0012s           |     0.0008s
8x8       |     0.0234s           |     0.0045s
10x10     |     0.5672s           |     0.0123s

Average Peak Memory (MB):
6x6       |       0.12 MB         |       0.08 MB
8x8       |       0.45 MB         |       0.15 MB
10x10     |       2.34 MB         |       0.32 MB

Average Steps (Nodes Explored):
6x6       |             245       |              32
8x8       |           12456       |             156
10x10     |          456789       |             512
```

## Algorithm Details

### DFS (Depth-First Search)
- Pure backtracking algorithm
- Tries values (0, 1) at each empty cell
- Validates constraints after each placement
- Backtracks when constraint violation detected

### Heuristic Search
- Uses constraint propagation before guessing
- Applies logical deductions:
  - No-triple rule: If XX?, fill opposite
  - Balance rule: If row has n/2 of one value, fill rest with other
- Reduces search space significantly

## Metrics Tracked

1. **Time (seconds)**: Wall clock solving time
2. **Memory (MB)**: Peak memory usage during solving
3. **Steps**: Number of nodes explored (cell assignments tried)

## API Usage

```python
from nmai_binairo import BinairoBoard, DFSSolver, HeuristicSolver, measure_performance

# Create a puzzle
puzzle = [
    [None, 1, None, None, 0, None],
    [0, None, None, None, None, None],
    [None, None, 0, None, None, 1],
    [1, None, None, 0, None, None],
    [None, None, None, None, None, 0],
    [None, 0, None, 1, None, None],
]

# Solve with DFS
dfs_solver = DFSSolver()
solution, stats = dfs_solver.solve(puzzle)
print(f"DFS: {stats['nodes_explored']} nodes, solved: {solution is not None}")

# Solve with Heuristic
heu_solver = HeuristicSolver()
solution, stats = heu_solver.solve(puzzle)
print(f"Heuristic: {stats['nodes_explored']} nodes, solved: {solution is not None}")

# Measure performance
result, perf = measure_performance(heu_solver.solve, puzzle)
print(f"Time: {perf.time_seconds:.4f}s, Memory: {perf.memory_peak_mb:.2f}MB")
```

## Scripts Summary

| Script | Purpose | Example |
|--------|---------|---------|
| `play_game.py` | Interactive Pygame game | `python play_game.py --size 8` |
| `fetch_testcases.py` | Generate/manage testcases | `python fetch_testcases.py --count 10` |
| `run_benchmark.py` | Run benchmarks with graphs | `python run_benchmark.py --detailed-plot` |

## Requirements

- Python 3.8+
- pygame (for interactive game)
- matplotlib (for benchmark graphs)
- numpy (for graph plotting)

## License

ME hehe

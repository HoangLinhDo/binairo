# NMAI Binairo Solver

Binairo/Takuzu solver and tooling for the NMAI project.

This repository includes:

- A playable Pygame app
- DFS and heuristic solvers
- Testcase generation/fetching utilities
- Benchmarking with time/memory/step comparisons and plots

## What Is Included

- `DFSSolver`: backtracking depth-first search
- `HeuristicSolver`: constraint propagation + guided search
- `AdvancedHeuristicSolver`: optimized heuristic variant
- Interactive game in `play_game.py`
- CLI solver and comparison entrypoint in `main.py`
- Benchmark runner in `run_benchmark.py`
- Testcase manager in `fetch_testcases.py`

## Requirements

- Python 3.8+
- Dependencies from `requirements.txt`:
  - `pygame`
  - `matplotlib`
  - `numpy`
  - `requests`

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Modes

Most scripts support both styles:

1. Run directly from this folder
2. Run as a package module

Examples:

```bash
# Direct script mode
python play_game.py

# Package mode
python -m nmai_binairo.play_game
```

## Quick Start

### 1. Play The Game

```bash
python play_game.py
python play_game.py --size 10
python play_game.py --difficulty hard
```

Controls:

- Left click: place white (1) / clear
- Right click: place black (0) / clear
- `N`: new puzzle
- `R`: reset puzzle
- `V`: validate current board

Solver buttons in the UI:

- `Solve DFS`
- `Solve HS`
- `Step DFS`
- `Step HS`
- `Compare`

When a puzzle is completed, a modal is shown with:

- Time
- Peak memory
- Steps

Close the modal with click, `Esc`, `Enter`, or `Space`.

### 2. Generate Or Inspect Testcases

```bash
# Generate defaults (sizes 6, 8, 10; count 5)
python fetch_testcases.py

# Custom generation
python fetch_testcases.py --sizes 6 8 10 14 --count 10 --difficulty hard

# Choose source: online | local | hybrid
python fetch_testcases.py --source hybrid

# List available puzzles in a testcase file
python fetch_testcases.py --list --input testcases.json

# Show puzzle by size and index
python fetch_testcases.py --show 6 1 --input testcases.json
```

### 3. Run Benchmarks

```bash
# Quick demo
python run_benchmark.py --quick

# Full benchmark
python run_benchmark.py

# Custom benchmark
python run_benchmark.py --sizes 6 8 10 14 --count 10 --difficulty medium

# Generate detailed 3-metric plot
python run_benchmark.py --detailed-plot

# Save plot without showing window
python run_benchmark.py --no-show --save-plot results/benchmark.png

# Save JSON benchmark output
python run_benchmark.py --output results/benchmark.json
```

## Main CLI (Solver/Compare)

`main.py` provides a compact command interface:

```bash
# Open visualizer
python main.py --gui

# Solve generated puzzle
python main.py --solve 8 --algo heuristic
python main.py --solve 8 --algo dfs
python main.py --solve 8 --algo advanced

# Solve from puzzle string (. means empty)
python main.py --puzzle ".1..0..." --algo heuristic

# Benchmark via main entrypoint
python main.py --benchmark --sizes 6 8 10 --runs 3

# Compare all solvers
python main.py --compare
```

## Metrics

The project reports three key metrics:

1. Time (seconds)
2. Peak memory (MB)
3. Steps (search effort)

Notes:

- In benchmark/game logs, step semantics are normalized per solver implementation.
- Compare solver results using the same puzzle set and difficulty for fairness.

## Python API Example

```python
from nmai_binairo import DFSSolver, HeuristicSolver, measure_performance

puzzle = [
    [None, 1, None, None, 0, None],
    [0, None, None, None, None, None],
    [None, None, 0, None, None, 1],
    [1, None, None, 0, None, None],
    [None, None, None, None, None, 0],
    [None, 0, None, 1, None, None],
]

dfs_solver = DFSSolver()
dfs_solution, dfs_stats = dfs_solver.solve([row[:] for row in puzzle])
print("DFS solved:", dfs_solution is not None, "nodes:", dfs_stats.get("nodes_explored", 0))

heu_solver = HeuristicSolver()
heu_solution, heu_stats = heu_solver.solve([row[:] for row in puzzle])
print("HS solved:", heu_solution is not None, "nodes:", heu_stats.get("nodes_explored", 0))

(_, perf) = measure_performance(heu_solver.solve, [row[:] for row in puzzle])
print(f"time={perf.time_seconds:.6f}s peak_mem={perf.memory_peak_mb:.4f}MB")
```

## Project Layout

```text
nmai_binairo/
  board.py
  constraints.py
  solver_dfs.py
  solver_heuristic.py
  play_game.py
  main.py
  benchmark.py
  run_benchmark.py
  fetch_testcases.py
  benchmark_utils.py
  visualizer.py
  testcases/
  results/
```

## License

Course project repository (NMAI).

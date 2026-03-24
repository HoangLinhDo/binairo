#!/usr/bin/env python3
"""
Binairo Game - Interactive Pygame Interface

Run this script to play Binairo interactively.
You can also watch the AI solve puzzles step by step.

Usage:
    python play_game.py                    # Start with 6x6 puzzle
    python play_game.py --size 10          # Start with 10x10 puzzle
    python play_game.py --difficulty hard  # Start with hard difficulty
"""

import sys
import os
import json
import argparse
import time
import gc
import tracemalloc
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("Error: pygame not installed. Install with: pip install pygame")

try:
    # Preferred when running as package: `python -m nmai_binairo.play_game`
    from nmai_binairo.board import BinairoBoard
    from nmai_binairo.solver_dfs import DFSSolver
    from nmai_binairo.solver_heuristic import HeuristicSolver
    from nmai_binairo.testcases.puzzle_generator import PuzzleGenerator
    from nmai_binairo.testcases.test_cases import TestcaseFetcher
except Exception:
    # Fallback when running script directly from inside the package folder:
    # `cd nmai_binairo && python play_game.py`
    from board import BinairoBoard
    from solver_dfs import DFSSolver
    from solver_heuristic import HeuristicSolver
    from testcases.puzzle_generator import PuzzleGenerator
    from testcases.test_cases import TestcaseFetcher

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
RED = (255, 0, 0)
GREEN = (0, 200, 0)
BLUE = (0, 128, 255)
YELLOW = (255, 255, 0)
BOARD_COLOR = (128, 98, 82)
BACKGROUND_COLOR = (45, 45, 60)
GRID_COLOR = (0, 180, 0)
BUTTON_COLOR = (0, 128, 255)
MODAL_BG = (18, 18, 28, 230)
MODAL_PANEL = (52, 58, 76)
MODAL_ACCENT = (0, 170, 120)


class BinairoGame:
    """Interactive Binairo game with Pygame."""

    CELL_SIZE = 50
    GRID_THICKNESS = 3
    BORDER_THICKNESS = 8
    BUTTON_HEIGHT = 45
    BUTTON_WIDTH = 150
    BUTTON_MARGIN = 8
    PADDING = 20

    # Keep large boards usable by shrinking cell size.
    LARGE_BOARD_CELL_SIZE = {
        20: 24,
        14: 32,
        10: 42,
    }

    def __init__(self, size: int = 6, difficulty: str = "medium"):
        if not PYGAME_AVAILABLE:
            raise ImportError("pygame is required")

        self.generator = PuzzleGenerator()
        self.fetcher = TestcaseFetcher()
        self.board_size = size
        self.difficulty = difficulty
        self.board = None
        self.original_board = None
        self.solution = None
        self.selected_cell = None
        self.solving = False
        self.delay_ms = 100
        self.player_steps = 0
        self.puzzle_start_time = time.perf_counter()
        self.puzzle_completed = False
        self.completion_modal = None

        # Difficulty mapping
        self.difficulty_map = {
            "easy": 0.4,
            "medium": 0.55,
            "hard": 0.65,
            "very_hard": 0.75,
        }

        self._calculate_dimensions()
        self._init_pygame()
        self._create_buttons()
        self._new_puzzle()

    @property
    def puzzle_type(self) -> str:
        """Return a compact puzzle type label used in logs."""
        return f"{self.board_size}x{self.board_size}_{self.difficulty}"

    def _compute_steps(self, algorithm: str, stats: dict) -> int:
        """Normalize step metric across solvers."""
        if algorithm == 'heuristic':
            return stats.get('nodes_explored', 0) + stats.get('propagations', 0)
        return stats.get('nodes_explored', 0)

    def _run_solver_with_metrics(self, algorithm: str, puzzle: list):
        """Run a solver while measuring elapsed time and peak memory."""
        solver = DFSSolver() if algorithm == 'dfs' else HeuristicSolver()

        gc.collect()
        was_tracing = tracemalloc.is_tracing()
        if not was_tracing:
            tracemalloc.start()
        else:
            tracemalloc.reset_peak()
        start_time = time.perf_counter()

        try:
            solution, stats = solver.solve([row[:] for row in puzzle])
            solved = solution is not None
        except Exception:
            solution = None
            stats = {'nodes_explored': 0, 'propagations': 0}
            solved = False

        elapsed = time.perf_counter() - start_time
        _, peak = tracemalloc.get_traced_memory()
        if not was_tracing:
            tracemalloc.stop()

        peak_mb = peak / (1024 * 1024)
        steps = self._compute_steps(algorithm, stats)
        return solution, stats, solved, elapsed, peak_mb, steps

    def _start_puzzle_tracking(self):
        """Reset counters for a fresh puzzle attempt."""
        self.player_steps = 0
        self.puzzle_start_time = time.perf_counter()
        self.puzzle_completed = False
        self.completion_modal = None
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        tracemalloc.reset_peak()

    def _show_completion_modal(self, mode: str, elapsed: float, peak_mb: float, steps: int):
        """Open completion modal with puzzle statistics."""
        self.completion_modal = {
            "title": "Puzzle Completed",
            "mode": mode,
            "time": elapsed,
            "memory": peak_mb,
            "steps": steps,
        }
        self.puzzle_completed = True

    def _draw_completion_modal(self):
        """Draw completion modal if available."""
        if not self.completion_modal:
            return

        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill(MODAL_BG)
        self.screen.blit(overlay, (0, 0))

        panel_w = min(520, self.screen_width - 80)
        panel_h = 260
        panel_x = (self.screen_width - panel_w) // 2
        panel_y = (self.screen_height - panel_h) // 2

        panel_rect = pygame.Rect(panel_x, panel_y, panel_w, panel_h)
        pygame.draw.rect(self.screen, MODAL_PANEL, panel_rect, border_radius=14)
        pygame.draw.rect(self.screen, MODAL_ACCENT, panel_rect, width=3, border_radius=14)

        title_text = self.title_font.render(self.completion_modal["title"], True, WHITE)
        title_rect = title_text.get_rect(center=(self.screen_width // 2, panel_y + 45))
        self.screen.blit(title_text, title_rect)

        mode_text = self.font.render(f"Mode: {self.completion_modal['mode']}", True, LIGHT_GRAY)
        self.screen.blit(mode_text, (panel_x + 30, panel_y + 90))

        time_text = self.font.render(f"Time: {self.completion_modal['time']:.6f}s", True, WHITE)
        mem_text = self.font.render(f"Memory: {self.completion_modal['memory']:.4f} MB", True, WHITE)
        steps_text = self.font.render(f"Steps: {self.completion_modal['steps']}", True, WHITE)

        self.screen.blit(time_text, (panel_x + 30, panel_y + 125))
        self.screen.blit(mem_text, (panel_x + 30, panel_y + 160))
        self.screen.blit(steps_text, (panel_x + 30, panel_y + 195))

        hint_text = self.small_font.render("Press ESC/ENTER or click to close", True, LIGHT_GRAY)
        hint_rect = hint_text.get_rect(center=(self.screen_width // 2, panel_y + panel_h - 25))
        self.screen.blit(hint_text, hint_rect)

    def _save_solve_log(self, algorithm: str, mode: str, solved: bool,
                        steps: int, elapsed: float, peak_mb: float) -> Path:
        """Persist one solve run to a JSON file."""
        log_dir = Path(__file__).resolve().parent / "results" / "play_logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        record = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "algorithm": algorithm,
            "mode": mode,
            "size": self.board_size,
            "difficulty": self.difficulty,
            "puzzle_type": self.puzzle_type,
            "time_seconds": elapsed,
            "memory_peak_mb": peak_mb,
            "steps": steps,
            "solved": solved,
        }

        filename = f"solve_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:8]}.json"
        file_path = log_dir / filename

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2)

        return file_path

    def _calculate_dimensions(self):
        """Calculate screen dimensions."""
        self.cell_size = self.LARGE_BOARD_CELL_SIZE.get(self.board_size, self.CELL_SIZE)
        self.grid_thickness = self.GRID_THICKNESS
        self.board_pixel_size = self.board_size * (self.cell_size + self.grid_thickness) + self.grid_thickness
        self.screen_width = max(self.board_pixel_size + 2 * self.PADDING,
                                5 * (self.BUTTON_WIDTH + self.BUTTON_MARGIN))
        self.screen_height = (self.board_pixel_size + 3 * self.BUTTON_HEIGHT +
                              5 * self.BUTTON_MARGIN + 3 * self.PADDING + 30)
        self.board_x = (self.screen_width - self.board_pixel_size) // 2
        self.board_y = self.PADDING

    def _init_pygame(self):
        """Initialize Pygame."""
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Binairo Game - NMAI Project")
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 22)
        self.title_font = pygame.font.Font(None, 36)

    def _create_buttons(self):
        """Create UI buttons."""
        self.buttons = []
        button_y = self.board_y + self.board_pixel_size + self.PADDING

        # Row 1: Size buttons
        sizes = [6, 8, 10, 14, 20]
        start_x = (self.screen_width - (len(sizes) * (self.BUTTON_WIDTH + self.BUTTON_MARGIN))) // 2

        for i, size in enumerate(sizes):
            rect = pygame.Rect(
                start_x + i * (self.BUTTON_WIDTH + self.BUTTON_MARGIN),
                button_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT
            )
            color = GREEN if size == self.board_size else BUTTON_COLOR
            self.buttons.append((rect, f"{size}x{size}", ('size', size), color))

        # Row 2: Solver buttons
        button_y += self.BUTTON_HEIGHT + self.BUTTON_MARGIN
        solver_buttons = [
            ("Solve DFS", ('solve', 'dfs'), BLUE),
            ("Solve HS", ('solve', 'heuristic'), BLUE),
            ("Step DFS", ('step', 'dfs'), (100, 100, 200)),
            ("Step HS", ('step', 'heuristic'), (100, 100, 200)),
            ("Compare", ('compare', None), (200, 100, 100)),
        ]

        for i, (label, action, color) in enumerate(solver_buttons):
            rect = pygame.Rect(
                start_x + i * (self.BUTTON_WIDTH + self.BUTTON_MARGIN),
                button_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT
            )
            self.buttons.append((rect, label, action, color))

        # Row 3: Control buttons
        button_y += self.BUTTON_HEIGHT + self.BUTTON_MARGIN
        control_buttons = [
            ("New Puzzle", ('new', None), GREEN),
            ("Reset", ('reset', None), YELLOW),
            ("Validate", ('validate', None), (200, 150, 0)),
        ]

        # Calculate start_x for Row 3 (3 buttons instead of 5)
        start_x_row3 = (self.screen_width - (len(control_buttons) * (self.BUTTON_WIDTH + self.BUTTON_MARGIN))) // 2

        for i, (label, action, color) in enumerate(control_buttons):
            rect = pygame.Rect(
                start_x_row3 + i * (self.BUTTON_WIDTH + self.BUTTON_MARGIN),
                button_y, self.BUTTON_WIDTH, self.BUTTON_HEIGHT
            )
            self.buttons.append((rect, label, action, color))

    def _new_puzzle(self):
        """Generate a new puzzle (prefer request source, then local fallback)."""
        diff_value = self.difficulty_map.get(self.difficulty, 0.55)

        puzzle = None
        solution = None

        # 1) Prefer online source (same behavior as fetch_testcases)
        try:
            puzzle = self.fetcher.fetch_random_puzzle(size=self.board_size, difficulty=self.difficulty)
        except Exception as e:
            print(f"Online fetch failed: {type(e).__name__}: {e}")

        # 2) If online source fails, try local generator
        if puzzle is None:
            try:
                puzzle, solution = self.generator.generate_puzzle(self.board_size, diff_value)
            except Exception as e:
                print(f"Local generation failed: {type(e).__name__}: {e}")

        # 3) Last resort: load from cached testcases file to keep game running
        if puzzle is None:
            puzzle = self._load_cached_puzzle(self.board_size)

        # 4) Absolute last fallback: empty board (prevents startup crash)
        if puzzle is None:
            puzzle = [[None for _ in range(self.board_size)] for _ in range(self.board_size)]

        self.board = [row[:] for row in puzzle]
        self.original_board = [row[:] for row in puzzle]
        self.solution = solution
        self.selected_cell = None
        self._start_puzzle_tracking()

    def _load_cached_puzzle(self, size: int):
        """Load one puzzle from testcases.json as a safe fallback."""
        try:
            path = os.path.join(os.path.dirname(__file__), "testcases", "testcases.json")
            if not os.path.exists(path):
                return None

            with open(path, "r") as f:
                data = json.load(f)

            puzzles = data.get(str(size), [])
            if not puzzles:
                return None

            return puzzles[0].get("puzzle")
        except Exception:
            return None

    def _reset_puzzle(self):
        """Reset puzzle to original state."""
        if self.original_board:
            self.board = [row[:] for row in self.original_board]
            self.selected_cell = None
            self._start_puzzle_tracking()

    def _validate(self) -> tuple:
        """Validate current board state. Returns (is_valid, message)."""
        n = self.board_size

        # Check for empty cells
        has_empty = any(cell is None for row in self.board for cell in row)

        # Check no triple rule
        for i in range(n):
            for j in range(n - 2):
                # Row triples
                if (self.board[i][j] is not None and
                    self.board[i][j] == self.board[i][j+1] == self.board[i][j+2]):
                    return False, f"Triple at row {i+1}"
                # Column triples
                if (self.board[j][i] is not None and
                    self.board[j][i] == self.board[j+1][i] == self.board[j+2][i]):
                    return False, f"Triple at col {i+1}"

        if has_empty:
            return True, "Valid so far (incomplete)"

        # Check counts
        for i in range(n):
            if sum(self.board[i]) != n // 2:
                return False, f"Row {i+1} count wrong"
            col_sum = sum(self.board[r][i] for r in range(n))
            if col_sum != n // 2:
                return False, f"Col {i+1} count wrong"

        # Check uniqueness
        rows = [tuple(row) for row in self.board]
        if len(rows) != len(set(rows)):
            return False, "Duplicate rows"

        cols = [tuple(self.board[r][c] for r in range(n)) for c in range(n)]
        if len(cols) != len(set(cols)):
            return False, "Duplicate columns"

        return True, "Valid solution!"

    def _draw_board(self):
        """Draw the game board."""
        # Draw board background
        pygame.draw.rect(self.screen, BOARD_COLOR,
                        (self.board_x, self.board_y,
                         self.board_pixel_size, self.board_pixel_size))

        # Draw border
        pygame.draw.rect(self.screen, RED,
                        (self.board_x - self.BORDER_THICKNESS,
                         self.board_y - self.BORDER_THICKNESS,
                         self.board_pixel_size + 2 * self.BORDER_THICKNESS,
                         self.board_pixel_size + 2 * self.BORDER_THICKNESS),
                        self.BORDER_THICKNESS)

        # Draw grid
        for i in range(self.board_size + 1):
            y = self.board_y + i * (self.cell_size + self.grid_thickness)
            pygame.draw.line(self.screen, GRID_COLOR,
                           (self.board_x, y + self.grid_thickness // 2),
                           (self.board_x + self.board_pixel_size, y + self.grid_thickness // 2),
                           self.grid_thickness)

            x = self.board_x + i * (self.cell_size + self.grid_thickness)
            pygame.draw.line(self.screen, GRID_COLOR,
                           (x + self.grid_thickness // 2, self.board_y),
                           (x + self.grid_thickness // 2, self.board_y + self.board_pixel_size),
                           self.grid_thickness)

        # Draw cells
        for row in range(self.board_size):
            for col in range(self.board_size):
                val = self.board[row][col]
                if val is not None:
                    self._draw_cell(row, col, val)

                # Highlight selected cell
                if self.selected_cell == (row, col):
                    self._draw_highlight(row, col)

    def _draw_cell(self, row: int, col: int, value: int):
        """Draw a cell value."""
        cell_x = self.board_x + col * (self.cell_size + self.grid_thickness) + self.grid_thickness
        cell_y = self.board_y + row * (self.cell_size + self.grid_thickness) + self.grid_thickness

        center_x = cell_x + self.cell_size // 2
        center_y = cell_y + self.cell_size // 2
        radius = max(4, self.cell_size // 2 - 4)

        color = WHITE if value == 1 else BLACK
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)

        # Draw marker for original cells
        if self.original_board and self.original_board[row][col] is not None:
            pygame.draw.rect(self.screen, RED, (center_x - 2, center_y - 2, 4, 4))

    def _draw_highlight(self, row: int, col: int):
        """Draw highlight on selected cell."""
        cell_x = self.board_x + col * (self.cell_size + self.grid_thickness) + self.grid_thickness
        cell_y = self.board_y + row * (self.cell_size + self.grid_thickness) + self.grid_thickness

        highlight = pygame.Surface((self.cell_size, self.cell_size), pygame.SRCALPHA)
        highlight.fill((255, 255, 0, 100))
        self.screen.blit(highlight, (cell_x, cell_y))

    def _draw_buttons(self):
        """Draw all buttons."""
        for rect, label, action, color in self.buttons:
            # Highlight size button if it's the current size
            if action[0] == 'size':
                color = GREEN if action[1] == self.board_size else BUTTON_COLOR

            pygame.draw.rect(self.screen, color, rect)
            pygame.draw.rect(self.screen, WHITE, rect, 2)

            text = self.font.render(label, True, WHITE)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def _draw_status(self, message: str = ""):
        """Draw status bar."""
        status_y = self.screen_height - self.PADDING - 10

        # Draw status background
        pygame.draw.rect(self.screen, (30, 30, 40),
                        (0, status_y - 10, self.screen_width, 30))

        # Draw instructions
        instructions = f"Left click: White (1) | Right click: Black (0)"
        inst_text = self.small_font.render(instructions, True, LIGHT_GRAY)
        self.screen.blit(inst_text, (self.PADDING, status_y))

        # Draw message
        if message:
            msg_text = self.font.render(message, True, WHITE)
            self.screen.blit(msg_text, (self.screen_width - msg_text.get_width() - self.PADDING, status_y))

    def _handle_click(self, pos: tuple, button: int):
        """Handle mouse click."""
        if self.completion_modal:
            self.completion_modal = None
            return ""

        x, y = pos

        # Check button clicks
        for rect, _, action, _ in self.buttons:
            if rect.collidepoint(pos):
                return self._handle_button_action(action)

        # Check board clicks
        if (self.board_x <= x <= self.board_x + self.board_pixel_size and
            self.board_y <= y <= self.board_y + self.board_pixel_size):

            rel_x = x - self.board_x - self.grid_thickness // 2
            rel_y = y - self.board_y - self.grid_thickness // 2

            col = rel_x // (self.cell_size + self.grid_thickness)
            row = rel_y // (self.cell_size + self.grid_thickness)

            if 0 <= row < self.board_size and 0 <= col < self.board_size:
                # Only modify cells that were originally empty
                if self.original_board[row][col] is None:
                    previous = self.board[row][col]
                    if button == 1:  # Left click = White (1)
                        self.board[row][col] = 1 if self.board[row][col] != 1 else None
                    elif button == 3:  # Right click = Black (0)
                        self.board[row][col] = 0 if self.board[row][col] != 0 else None

                    if self.board[row][col] != previous:
                        self.player_steps += 1

                        if (not self.puzzle_completed and
                            all(cell is not None for row_vals in self.board for cell in row_vals)):
                            is_valid, _ = self._validate()
                            if is_valid:
                                elapsed = time.perf_counter() - self.puzzle_start_time
                                peak_mb = 0.0
                                if tracemalloc.is_tracing():
                                    _, peak = tracemalloc.get_traced_memory()
                                    peak_mb = peak / (1024 * 1024)
                                self._show_completion_modal(
                                    mode="Manual Play",
                                    elapsed=elapsed,
                                    peak_mb=peak_mb,
                                    steps=self.player_steps,
                                )
                self.selected_cell = (row, col)

        return ""

    def _handle_button_action(self, action: tuple) -> str:
        """Handle button action and return status message."""
        action_type, action_value = action

        if action_type == 'size':
            self.board_size = action_value
            self._calculate_dimensions()
            self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
            self._create_buttons()
            self._new_puzzle()
            return f"New {action_value}x{action_value} puzzle"

        elif action_type == 'new':
            self._new_puzzle()
            return "New puzzle generated"

        elif action_type == 'reset':
            self._reset_puzzle()
            return "Puzzle reset"

        elif action_type == 'validate':
            is_valid, msg = self._validate()
            return msg

        elif action_type == 'solve':
            self._reset_puzzle()
            solution, _, solved, elapsed, peak_mb, steps = self._run_solver_with_metrics(
                action_value,
                self.board,
            )
            log_path = self._save_solve_log(
                algorithm=action_value,
                mode='solve',
                solved=solved,
                steps=steps,
                elapsed=elapsed,
                peak_mb=peak_mb,
            )

            if solution:
                self.board = solution
                self._show_completion_modal(
                    mode=f"Solve {action_value.upper()}",
                    elapsed=elapsed,
                    peak_mb=peak_mb,
                    steps=steps,
                )
                return (
                    f"Solved! Steps: {steps} | Time: {elapsed:.6f}s | "
                    f"Mem: {peak_mb:.4f}MB | Log: {log_path.name}"
                )
            return f"No solution found | Log: {log_path.name}"

        elif action_type == 'step':
            self._reset_puzzle()
            gc.collect()
            was_tracing = tracemalloc.is_tracing()
            if not was_tracing:
                tracemalloc.start()
            else:
                tracemalloc.reset_peak()
            start_time = time.perf_counter()

            solved, steps, msg = self._solve_step_by_step(action_value)

            elapsed = time.perf_counter() - start_time
            _, peak = tracemalloc.get_traced_memory()
            if not was_tracing:
                tracemalloc.stop()
            peak_mb = peak / (1024 * 1024)

            log_path = self._save_solve_log(
                algorithm=action_value,
                mode='step',
                solved=solved,
                steps=steps,
                elapsed=elapsed,
                peak_mb=peak_mb,
            )
            if solved:
                self._show_completion_modal(
                    mode=f"Step {action_value.upper()}",
                    elapsed=elapsed,
                    peak_mb=peak_mb,
                    steps=steps,
                )
            return f"{msg} | Time: {elapsed:.6f}s | Mem: {peak_mb:.4f}MB | Log: {log_path.name}"

        elif action_type == 'compare':
            self._reset_puzzle()
            puzzle = [row[:] for row in self.board]

            _, _, dfs_solved, dfs_elapsed, dfs_peak_mb, dfs_steps = self._run_solver_with_metrics('dfs', puzzle)
            _, _, hs_solved, hs_elapsed, hs_peak_mb, heu_steps = self._run_solver_with_metrics('heuristic', puzzle)

            self._save_solve_log(
                algorithm='dfs',
                mode='compare',
                solved=dfs_solved,
                steps=dfs_steps,
                elapsed=dfs_elapsed,
                peak_mb=dfs_peak_mb,
            )
            self._save_solve_log(
                algorithm='heuristic',
                mode='compare',
                solved=hs_solved,
                steps=heu_steps,
                elapsed=hs_elapsed,
                peak_mb=hs_peak_mb,
            )

            return (
                f"DFS: {dfs_steps} steps ({dfs_elapsed:.6f}s) | "
                f"HS: {heu_steps} steps ({hs_elapsed:.6f}s)"
            )

        return ""

    def _solve_step_by_step(self, algorithm: str):
        """Solve with step-by-step visualization."""
        if algorithm == 'dfs':
            return self._step_dfs()
        else:
            return self._step_heuristic()

    def _step_dfs(self):
        """Step-by-step DFS solving."""
        n = self.board_size
        board = [row[:] for row in self.board]
        steps = 0

        def is_valid(row, col):
            val = board[row][col]
            if val is None:
                return True

            # Check row streaks
            for i in range(max(0, col-2), min(n-3, col)+1):
                if board[row][i] == board[row][i+1] == board[row][i+2] is not None:
                    return False

            # Check column streaks
            for i in range(max(0, row-2), min(n-3, row)+1):
                if board[i][col] == board[i+1][col] == board[i+2][col] is not None:
                    return False

            # Check row complete
            if None not in board[row]:
                if sum(board[row]) != n // 2:
                    return False
                for other in range(n):
                    if other != row and board[other] == board[row]:
                        return False

            # Check column complete
            col_vals = [board[r][col] for r in range(n)]
            if None not in col_vals:
                if sum(col_vals) != n // 2:
                    return False
                for other in range(n):
                    other_col = [board[r][other] for r in range(n)]
                    if other != col and other_col == col_vals:
                        return False

            return True

        def solve(pos):
            nonlocal steps
            while pos < n * n:
                row, col = pos // n, pos % n
                if board[row][col] is None:
                    break
                pos += 1

            if pos >= n * n:
                return True

            row, col = pos // n, pos % n

            for val in [0, 1]:
                board[row][col] = val
                steps += 1
                self.board = [r[:] for r in board]
                self._draw()
                self._draw_status(f"Step {steps}: Trying {val} at ({row},{col})")
                pygame.display.flip()
                time.sleep(self.delay_ms / 1000.0)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False

                if is_valid(row, col) and solve(pos + 1):
                    return True

                board[row][col] = None

            return False

        if solve(0):
            self.board = board
            return True, steps, f"Solved with DFS! Steps: {steps}"
        return False, steps, "No solution"

    def _step_heuristic(self):
        """Step-by-step heuristic solving."""
        n = self.board_size
        board = [row[:] for row in self.board]
        steps = 0

        def is_valid(row, col):
            val = board[row][col]
            if val is None:
                return True

            for i in range(max(0, col-2), min(n-3, col)+1):
                if board[row][i] == board[row][i+1] == board[row][i+2] is not None:
                    return False

            for i in range(max(0, row-2), min(n-3, row)+1):
                if board[i][col] == board[i+1][col] == board[i+2][col] is not None:
                    return False

            if None not in board[row]:
                if sum(board[row]) != n // 2:
                    return False
                for other in range(n):
                    if other != row and board[other] == board[row]:
                        return False

            col_vals = [board[r][col] for r in range(n)]
            if None not in col_vals:
                if sum(col_vals) != n // 2:
                    return False
                for other in range(n):
                    other_col = [board[r][other] for r in range(n)]
                    if other != col and other_col == col_vals:
                        return False

            return True

        def apply_logical():
            nonlocal steps
            progress = True
            while progress:
                progress = False
                for row in range(n):
                    for col in range(n):
                        if board[row][col] is not None:
                            continue

                        # Check triple patterns
                        if col > 1 and board[row][col-1] is not None and board[row][col-1] == board[row][col-2]:
                            board[row][col] = 1 - board[row][col-1]
                            steps += 1
                            progress = True
                            continue

                        if col < n-2 and board[row][col+1] is not None and board[row][col+1] == board[row][col+2]:
                            board[row][col] = 1 - board[row][col+1]
                            steps += 1
                            progress = True
                            continue

                        if 0 < col < n-1 and board[row][col-1] is not None and board[row][col-1] == board[row][col+1]:
                            board[row][col] = 1 - board[row][col-1]
                            steps += 1
                            progress = True
                            continue

                        if row > 1 and board[row-1][col] is not None and board[row-1][col] == board[row-2][col]:
                            board[row][col] = 1 - board[row-1][col]
                            steps += 1
                            progress = True
                            continue

                        if row < n-2 and board[row+1][col] is not None and board[row+1][col] == board[row+2][col]:
                            board[row][col] = 1 - board[row+1][col]
                            steps += 1
                            progress = True
                            continue

                        if 0 < row < n-1 and board[row-1][col] is not None and board[row-1][col] == board[row+1][col]:
                            board[row][col] = 1 - board[row-1][col]
                            steps += 1
                            progress = True
                            continue

                        # Row balance
                        row_0 = board[row].count(0)
                        row_1 = board[row].count(1)
                        if row_0 == n // 2:
                            for c in range(n):
                                if board[row][c] is None:
                                    board[row][c] = 1
                                    steps += 1
                            progress = True
                            continue
                        if row_1 == n // 2:
                            for c in range(n):
                                if board[row][c] is None:
                                    board[row][c] = 0
                                    steps += 1
                            progress = True
                            continue

                        # Column balance
                        col_0 = sum(1 for r in range(n) if board[r][col] == 0)
                        col_1 = sum(1 for r in range(n) if board[r][col] == 1)
                        if col_0 == n // 2:
                            for r in range(n):
                                if board[r][col] is None:
                                    board[r][col] = 1
                                    steps += 1
                            progress = True
                            continue
                        if col_1 == n // 2:
                            for r in range(n):
                                if board[r][col] is None:
                                    board[r][col] = 0
                                    steps += 1
                            progress = True
                            continue

                self.board = [r[:] for r in board]
                self._draw()
                self._draw_status(f"Propagating... Steps: {steps}")
                pygame.display.flip()
                time.sleep(self.delay_ms / 1000.0)

                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        return False
            return True

        def solve():
            nonlocal steps
            saved = [r[:] for r in board]

            if not apply_logical():
                return False

            # Find empty cell
            for row in range(n):
                for col in range(n):
                    if board[row][col] is None:
                        for val in [0, 1]:
                            board[row][col] = val
                            steps += 1
                            self.board = [r[:] for r in board]
                            self._draw()
                            self._draw_status(f"Step {steps}: Trying {val} at ({row},{col})")
                            pygame.display.flip()
                            time.sleep(self.delay_ms / 1000.0)

                            for event in pygame.event.get():
                                if event.type == pygame.QUIT:
                                    return False

                            if is_valid(row, col) and solve():
                                return True

                            for r in range(n):
                                for c in range(n):
                                    board[r][c] = saved[r][c]
                        return False

            return True

        if solve():
            self.board = board
            return True, steps, f"Solved with HS! Steps: {steps}"
        return False, steps, "No solution"

    def _draw(self):
        """Draw everything."""
        self.screen.fill(BACKGROUND_COLOR)
        self._draw_board()
        self._draw_buttons()

    def run(self):
        """Run the game loop."""
        running = True
        status_message = "Click cells to play or buttons to solve"

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button in [1, 3]:
                        status_message = self._handle_click(event.pos, event.button) or status_message

                elif event.type == pygame.KEYDOWN:
                    if self.completion_modal and event.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
                        self.completion_modal = None
                        continue
                    if event.key == pygame.K_r:
                        self._reset_puzzle()
                        status_message = "Puzzle reset"
                    elif event.key == pygame.K_n:
                        self._new_puzzle()
                        status_message = "New puzzle"
                    elif event.key == pygame.K_v:
                        _, status_message = self._validate()

            self._draw()
            self._draw_status(status_message)
            self._draw_completion_modal()
            pygame.display.flip()

        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description='Play Binairo interactively')
    parser.add_argument('--size', type=int, default=6, choices=[6, 8, 10, 14, 20],
                        help='Board size (default: 6)')
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard', 'very_hard'],
                        default='medium', help='Puzzle difficulty (default: medium)')

    args = parser.parse_args()

    print("=" * 50)
    print("BINAIRO GAME - NMAI Project")
    print("=" * 50)
    print(f"Board size: {args.size}x{args.size}")
    print(f"Difficulty: {args.difficulty}")
    print()
    print("Controls:")
    print("  Left click  : Place White (1) or clear")
    print("  Right click : Place Black (0) or clear")
    print("  N key       : New puzzle")
    print("  R key       : Reset puzzle")
    print("  V key       : Validate")
    print("=" * 50)

    game = BinairoGame(size=args.size, difficulty=args.difficulty)
    game.run()


if __name__ == "__main__":
    main()

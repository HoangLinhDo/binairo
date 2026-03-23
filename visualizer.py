"""
Pygame visualization for Binairo puzzles.
Provides step-by-step solving visualization and interactive UI.
"""

import time
import threading
from typing import Optional, Callable, List, Tuple

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False

try:
    from nmai_binairo.board import BinairoBoard
    from nmai_binairo.constraints import BinairoConstraints
    from nmai_binairo.solver_dfs import DFSSolver
    from nmai_binairo.solver_heuristic import HeuristicSolver, AdvancedHeuristicSolver
except ImportError:
    from board import BinairoBoard
    from constraints import BinairoConstraints
    from solver_dfs import DFSSolver
    from solver_heuristic import HeuristicSolver, AdvancedHeuristicSolver


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (64, 64, 64)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 128, 255)
BOARD_COLOR = (128, 98, 82)
BACKGROUND_COLOR = (45, 45, 45)
GRID_COLOR = (0, 180, 0)
HIGHLIGHT_COLOR = (255, 255, 0, 128)


class BinairoVisualizer:
    """
    Pygame-based visualizer for Binairo puzzles.
    """

    # Display settings
    CELL_SIZE = 50
    GRID_THICKNESS = 3
    BORDER_THICKNESS = 8
    BUTTON_HEIGHT = 45
    BUTTON_WIDTH = 180
    BUTTON_MARGIN = 10
    PADDING = 20

    def __init__(self, board_size: int = 6):
        """
        Initialize the visualizer.

        Args:
            board_size: Initial board size
        """
        if not PYGAME_AVAILABLE:
            raise ImportError("Pygame is required for visualization. Install with: pip install pygame")

        self.board_size = board_size
        self.board: Optional[BinairoBoard] = None
        self.original_board: Optional[List[List]] = None
        self.solving = False
        self.delay_ms = 100
        self.highlight_cell: Optional[Tuple[int, int]] = None

        # Calculate dimensions
        self._calculate_dimensions()

        # Initialize pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Binairo Solver - Improved Version")
        self.font = pygame.font.Font(None, 32)
        self.small_font = pygame.font.Font(None, 24)

        # Buttons
        self.buttons = []
        self._create_buttons()

    def _calculate_dimensions(self):
        """Calculate screen dimensions based on board size."""
        self.board_pixel_size = self.board_size * (self.CELL_SIZE + self.GRID_THICKNESS) + self.GRID_THICKNESS
        self.screen_width = max(self.board_pixel_size + 2 * self.PADDING,
                                5 * (self.BUTTON_WIDTH + self.BUTTON_MARGIN) + self.PADDING)
        self.screen_height = (self.board_pixel_size + 4 * self.BUTTON_HEIGHT +
                              6 * self.BUTTON_MARGIN + 3 * self.PADDING)

        self.board_x = (self.screen_width - self.board_pixel_size) // 2
        self.board_y = self.PADDING

    def _create_buttons(self):
        """Create UI buttons."""
        self.buttons = []

        # Row 1: Size buttons
        button_y = self.board_y + self.board_pixel_size + self.PADDING
        sizes = [6, 8, 10, 14, 20]
        start_x = (self.screen_width - (len(sizes) * (self.BUTTON_WIDTH + self.BUTTON_MARGIN) - self.BUTTON_MARGIN)) // 2

        for i, size in enumerate(sizes):
            rect = pygame.Rect(
                start_x + i * (self.BUTTON_WIDTH + self.BUTTON_MARGIN),
                button_y,
                self.BUTTON_WIDTH,
                self.BUTTON_HEIGHT
            )
            self.buttons.append((rect, f"{size}x{size}", ('size', size)))

        # Row 2: Solver buttons
        button_y += self.BUTTON_HEIGHT + self.BUTTON_MARGIN
        solver_buttons = [
            ("Solve DFS", ('solve', 'dfs')),
            ("Solve Heuristic", ('solve', 'heuristic')),
            ("Step DFS", ('step', 'dfs')),
            ("Step Heuristic", ('step', 'heuristic')),
            ("Compare", ('compare', None))
        ]

        for i, (label, action) in enumerate(solver_buttons):
            rect = pygame.Rect(
                start_x + i * (self.BUTTON_WIDTH + self.BUTTON_MARGIN),
                button_y,
                self.BUTTON_WIDTH,
                self.BUTTON_HEIGHT
            )
            self.buttons.append((rect, label, action))

        # Row 3: Control buttons
        button_y += self.BUTTON_HEIGHT + self.BUTTON_MARGIN
        control_buttons = [
            ("Reset", ('reset', None)),
            ("New Puzzle", ('new', None)),
            ("Speed -", ('speed', -50)),
            ("Speed +", ('speed', 50)),
            ("Quit", ('quit', None))
        ]

        for i, (label, action) in enumerate(control_buttons):
            rect = pygame.Rect(
                start_x + i * (self.BUTTON_WIDTH + self.BUTTON_MARGIN),
                button_y,
                self.BUTTON_WIDTH,
                self.BUTTON_HEIGHT
            )
            self.buttons.append((rect, label, action))

    def set_puzzle(self, puzzle: List[List]):
        """Set the puzzle to visualize."""
        self.board = BinairoBoard(board=puzzle)
        self.original_board = [row[:] for row in puzzle]
        self.board_size = len(puzzle)
        self._calculate_dimensions()
        self._create_buttons()
        # Resize window if needed
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))

    def reset_puzzle(self):
        """Reset to original puzzle state."""
        if self.original_board:
            self.board = BinairoBoard(board=self.original_board)

    def draw_board(self):
        """Draw the game board."""
        if self.board is None:
            return

        # Draw board background
        pygame.draw.rect(
            self.screen, BOARD_COLOR,
            (self.board_x, self.board_y, self.board_pixel_size, self.board_pixel_size)
        )

        # Draw border
        pygame.draw.rect(
            self.screen, RED,
            (self.board_x - self.BORDER_THICKNESS,
             self.board_y - self.BORDER_THICKNESS,
             self.board_pixel_size + 2 * self.BORDER_THICKNESS,
             self.board_pixel_size + 2 * self.BORDER_THICKNESS),
            self.BORDER_THICKNESS
        )

        # Draw grid lines
        for i in range(self.board_size + 1):
            # Horizontal
            y = self.board_y + i * (self.CELL_SIZE + self.GRID_THICKNESS)
            pygame.draw.line(
                self.screen, GRID_COLOR,
                (self.board_x, y + self.GRID_THICKNESS // 2),
                (self.board_x + self.board_pixel_size, y + self.GRID_THICKNESS // 2),
                self.GRID_THICKNESS
            )
            # Vertical
            x = self.board_x + i * (self.CELL_SIZE + self.GRID_THICKNESS)
            pygame.draw.line(
                self.screen, GRID_COLOR,
                (x + self.GRID_THICKNESS // 2, self.board_y),
                (x + self.GRID_THICKNESS // 2, self.board_y + self.board_pixel_size),
                self.GRID_THICKNESS
            )

        # Draw cells
        for row in range(self.board_size):
            for col in range(self.board_size):
                val = self.board.get(row, col)
                if val is not None:
                    self._draw_cell(row, col, val)

        # Draw highlight
        if self.highlight_cell:
            self._draw_highlight(self.highlight_cell[0], self.highlight_cell[1])

    def _draw_cell(self, row: int, col: int, value: int):
        """Draw a cell with a value."""
        cell_x = self.board_x + col * (self.CELL_SIZE + self.GRID_THICKNESS) + self.GRID_THICKNESS
        cell_y = self.board_y + row * (self.CELL_SIZE + self.GRID_THICKNESS) + self.GRID_THICKNESS

        center_x = cell_x + self.CELL_SIZE // 2
        center_y = cell_y + self.CELL_SIZE // 2
        radius = self.CELL_SIZE // 2 - 4

        color = BLACK if value == 1 else WHITE
        pygame.draw.circle(self.screen, color, (center_x, center_y), radius)

        # Draw indicator for original cells
        if self.original_board and self.original_board[row][col] is not None:
            pygame.draw.rect(
                self.screen, RED,
                (center_x - 2, center_y - 2, 4, 4)
            )

    def _draw_highlight(self, row: int, col: int):
        """Draw highlight on a cell."""
        cell_x = self.board_x + col * (self.CELL_SIZE + self.GRID_THICKNESS) + self.GRID_THICKNESS
        cell_y = self.board_y + row * (self.CELL_SIZE + self.GRID_THICKNESS) + self.GRID_THICKNESS

        # Create a semi-transparent surface
        highlight = pygame.Surface((self.CELL_SIZE, self.CELL_SIZE), pygame.SRCALPHA)
        highlight.fill((255, 255, 0, 100))
        self.screen.blit(highlight, (cell_x, cell_y))

    def draw_buttons(self):
        """Draw all buttons."""
        for rect, label, _ in self.buttons:
            pygame.draw.rect(self.screen, BLUE, rect)
            pygame.draw.rect(self.screen, WHITE, rect, 2)

            text = self.font.render(label, True, WHITE)
            text_rect = text.get_rect(center=rect.center)
            self.screen.blit(text, text_rect)

    def draw_status(self, message: str = ""):
        """Draw status message."""
        status_y = self.screen_height - self.PADDING - 20

        # Clear status area
        pygame.draw.rect(self.screen, BACKGROUND_COLOR,
                        (0, status_y - 5, self.screen_width, 30))

        # Draw delay info
        delay_text = self.small_font.render(f"Delay: {self.delay_ms}ms", True, LIGHT_GRAY)
        self.screen.blit(delay_text, (self.PADDING, status_y))

        # Draw message
        if message:
            msg_text = self.small_font.render(message, True, WHITE)
            self.screen.blit(msg_text, (self.screen_width // 2 - msg_text.get_width() // 2, status_y))

    def draw_loading_screen(self, message: str):
        """Draw a loading screen with message."""
        self.screen.fill(BACKGROUND_COLOR)

        # Draw semi-transparent overlay
        overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Draw loading message
        font_large = pygame.font.Font(None, 48)
        text = font_large.render(message, True, WHITE)
        text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
        self.screen.blit(text, text_rect)

        # Draw smaller message
        small_text = self.small_font.render("Please wait...", True, LIGHT_GRAY)
        small_rect = small_text.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 50))
        self.screen.blit(small_text, small_rect)

        pygame.display.flip()

    def generate_puzzle_with_progress(self, size: int, difficulty: float = 0.6):
        """Generate puzzle with loading screen and responsive UI."""
        from testcases.test_cases import TestcaseFetcher

        # Result container for thread
        result = {'puzzle': None, 'solution': None, 'done': False, 'error': None}

        # Map difficulty float to string
        difficulty_str = "medium"
        if difficulty <= 0.45:
            difficulty_str = "easy"
        elif difficulty <= 0.6:
            difficulty_str = "medium"
        elif difficulty <= 0.7:
            difficulty_str = "hard"
        else:
            difficulty_str = "very_hard"

        def generate_in_thread():
            try:
                fetcher = TestcaseFetcher()
                puzzle = fetcher.fetch_random_puzzle(size, difficulty_str)
                result['puzzle'] = puzzle
            except Exception as e:
                result['error'] = str(e)
            finally:
                result['done'] = True

        # Start generation in background thread
        thread = threading.Thread(target=generate_in_thread, daemon=True)
        thread.start()

        # Show loading screen and keep UI responsive
        clock = pygame.time.Clock()
        dots = 0
        max_wait = 90  # 90 seconds max
        wait_time = 0

        while not result['done'] and wait_time < max_wait:
            # Show animated loading screen
            message = f"Generating {size}x{size} puzzle" + "." * (dots % 4)
            if size >= 14:
                message += f" (this may take up to {30 if size <= 14 else 60}s)"
            self.draw_loading_screen(message)

            # Process events to keep window responsive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit

            dots += 1
            wait_time += 0.2
            clock.tick(5)  # 5 FPS for animation

        # Check for timeout
        if not result['done']:
            result['error'] = f"Puzzle generation timed out after {max_wait}s. Try a smaller board size."

        # Check for errors
        if result['error']:
            print(f"Error generating puzzle: {result['error']}")
            # Show error on screen
            self.draw_loading_screen(f"Error: {result['error'][:50]}")
            pygame.display.flip()
            time.sleep(3)
            return None

        return result['puzzle']

    def update(self):
        """Update the display."""
        self.screen.fill(BACKGROUND_COLOR)
        self.draw_board()
        self.draw_buttons()
        pygame.display.flip()

    def handle_click(self, pos: Tuple[int, int]) -> Optional[Tuple]:
        """Handle mouse click and return action if button clicked."""
        for rect, _, action in self.buttons:
            if rect.collidepoint(pos):
                return action
        return None

    def get_cell_from_pos(self, pos: Tuple[int, int]) -> Optional[Tuple[int, int]]:
        """Convert screen position to board cell coordinates."""
        if self.board is None:
            return None

        x, y = pos

        # Check if click is within board boundaries
        if (x < self.board_x or x > self.board_x + self.board_pixel_size or
            y < self.board_y or y > self.board_y + self.board_pixel_size):
            return None

        # Calculate cell coordinates
        rel_x = x - self.board_x
        rel_y = y - self.board_y

        col = rel_x // (self.CELL_SIZE + self.GRID_THICKNESS)
        row = rel_y // (self.CELL_SIZE + self.GRID_THICKNESS)

        # Validate cell coordinates
        if 0 <= row < self.board_size and 0 <= col < self.board_size:
            return (row, col)

        return None

    def handle_cell_click(self, row: int, col: int):
        """Handle click on a cell - cycle through None -> 1 -> 0 -> None."""
        if self.board is None or self.original_board is None:
            return

        # Don't allow modification of original puzzle cells
        if self.original_board[row][col] is not None:
            return

        current_value = self.board.get(row, col)

        # Cycle: None -> 1 (black) -> 0 (white) -> None
        if current_value is None:
            new_value = 1
        elif current_value == 1:
            new_value = 0
        else:
            new_value = None

        self.board.set(row, col, new_value)

    def visualization_callback(self, board: BinairoBoard, row: int, col: int, value: int):
        """Callback for solver visualization."""
        # Update internal board state
        for r in range(board.size):
            for c in range(board.size):
                self.board.set(r, c, board.get(r, c))

        self.highlight_cell = (row, col)
        self.update()
        self.draw_status(f"Trying {value} at ({row}, {col})")
        pygame.display.flip()
        time.sleep(self.delay_ms / 1000.0)

        # Process events to keep UI responsive
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                raise SystemExit

    def solve_with_visualization(self, algorithm: str = 'heuristic'):
        """Solve with step-by-step visualization."""
        if self.board is None:
            return

        if algorithm == 'dfs':
            solver = DFSSolver()
        else:
            solver = HeuristicSolver()

        puzzle = self.board.to_list()
        solution, stats = solver.solve(puzzle, callback=self.visualization_callback)

        self.highlight_cell = None

        if solution:
            self.board = BinairoBoard(board=solution)
            self.update()
            self.draw_status(f"Solved! Nodes: {stats['nodes_explored']}, Backtracks: {stats['backtracks']}")
        else:
            self.draw_status("No solution found!")

        pygame.display.flip()
        return solution, stats

    def run(self, initial_puzzle: Optional[List[List]] = None):
        """Run the visualizer main loop."""
        if initial_puzzle:
            self.set_puzzle(initial_puzzle)
        else:
            # Generate a default puzzle using the fetcher
            from testcases.test_cases import TestcaseFetcher
            fetcher = TestcaseFetcher()
            puzzle = fetcher.fetch_random_puzzle(self.board_size, "medium")
            self.set_puzzle(puzzle)

        running = True
        status_message = "Click a button to start"

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    # Handle both left (1) and right (3) clicks
                    if event.button in (1, 3):
                        action = None

                        # Only check for button clicks on left click
                        if event.button == 1:
                            action = self.handle_click(event.pos)

                        if action:
                            action_type, action_value = action

                            if action_type == 'quit':
                                running = False

                            elif action_type == 'size':
                                puzzle = self.generate_puzzle_with_progress(action_value, difficulty=0.6)
                                if puzzle:
                                    self.set_puzzle(puzzle)
                                    status_message = f"Generated {action_value}x{action_value} puzzle"

                            elif action_type == 'new':
                                puzzle = self.generate_puzzle_with_progress(self.board_size, difficulty=0.6)
                                if puzzle:
                                    self.set_puzzle(puzzle)
                                    status_message = "New puzzle generated"

                            elif action_type == 'reset':
                                self.reset_puzzle()
                                status_message = "Puzzle reset"

                            elif action_type == 'speed':
                                self.delay_ms = max(10, min(500, self.delay_ms + action_value))
                                status_message = f"Speed adjusted: {self.delay_ms}ms"

                            elif action_type == 'solve':
                                status_message = f"Solving with {action_value}..."
                                self.reset_puzzle()
                                self.update()
                                pygame.display.flip()

                                if action_value == 'dfs':
                                    solver = DFSSolver()
                                else:
                                    solver = HeuristicSolver()

                                solution, stats = solver.solve(self.board.to_list())
                                if solution:
                                    self.board = BinairoBoard(board=solution)
                                    status_message = f"Solved! Nodes: {stats['nodes_explored']}"
                                else:
                                    status_message = "No solution found"

                            elif action_type == 'step':
                                status_message = f"Step solving with {action_value}..."
                                self.reset_puzzle()
                                self.solve_with_visualization(action_value)

                            elif action_type == 'compare':
                                self.reset_puzzle()
                                puzzle = self.board.to_list()

                                # DFS
                                dfs_solver = DFSSolver()
                                _, dfs_stats = dfs_solver.solve([r[:] for r in puzzle])

                                # Heuristic
                                heu_solver = HeuristicSolver()
                                _, heu_stats = heu_solver.solve([r[:] for r in puzzle])

                                status_message = (
                                    f"DFS: {dfs_stats['nodes_explored']} nodes | "
                                    f"Heuristic: {heu_stats['nodes_explored']} nodes"
                                )
                        else:
                            # No button clicked (or right click), check if a cell was clicked
                            cell = self.get_cell_from_pos(event.pos)
                            if cell:
                                row, col = cell
                                self.handle_cell_click(row, col)
                                status_message = f"Cell ({row}, {col}) modified"

            self.update()
            self.draw_status(status_message)
            pygame.display.flip()

        pygame.quit()


def run_visualizer(puzzle: Optional[List[List]] = None, size: int = 6):
    """Convenience function to run the visualizer."""
    vis = BinairoVisualizer(board_size=size)
    vis.run(initial_puzzle=puzzle)


if __name__ == "__main__":
    run_visualizer()

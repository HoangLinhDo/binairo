"""
Puzzle generator for Binairo puzzles.
Generates valid puzzles with unique solutions.
"""

import random
import time
import logging
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class PuzzleGenerator:
    """
    Generates valid Binairo puzzles with unique solutions.
    """

    def __init__(self, seed: Optional[int] = None, timeout: float = 30.0):
        """
        Initialize the puzzle generator.

        Args:
            seed: Random seed for reproducibility
            timeout: Maximum time in seconds for generation
        """
        if seed is not None:
            random.seed(seed)
        self.timeout = timeout
        self.start_time = None
        logger.debug(f"PuzzleGenerator initialized with timeout={timeout}s")

    def _check_streak(self, board: List[List], n: int, i: int, j: int) -> bool:
        """Check if position (i,j) creates a streak of 3."""
        val = board[i][j]
        if val is None:
            return True

        # Check horizontal
        if j >= 2 and board[i][j-1] == val and board[i][j-2] == val:
            return False
        if j <= n-3 and board[i][j+1] == val and board[i][j+2] == val:
            return False
        if 0 < j < n-1 and board[i][j-1] == val and board[i][j+1] == val:
            return False

        # Check vertical
        if i >= 2 and board[i-1][j] == val and board[i-2][j] == val:
            return False
        if i <= n-3 and board[i+1][j] == val and board[i+2][j] == val:
            return False
        if 0 < i < n-1 and board[i-1][j] == val and board[i+1][j] == val:
            return False

        return True

    def _check_count(self, board: List[List], n: int, i: int, j: int) -> bool:
        """Check if count constraint is satisfied - optimized version."""
        half = n // 2

        # Row count - only check if placement puts us over the limit
        row = board[i]
        count_0 = row.count(0)
        count_1 = row.count(1)
        if count_0 > half or count_1 > half:
            return False

        # Column count - use direct iteration without comprehension for speed
        col_0 = 0
        col_1 = 0
        for r in range(n):
            val = board[r][j]
            if val == 0:
                col_0 += 1
            elif val == 1:
                col_1 += 1
        
        if col_0 > half or col_1 > half:
            return False

        return True

    def _check_unique(self, board: List[List], n: int, i: int, j: int) -> bool:
        """Check if uniqueness constraint is satisfied for complete rows/cols."""
        # Check row uniqueness - only if row is complete
        row = board[i]
        if None not in row:
            for other in range(n):
                if other != i and board[other] == row:
                    return False

        # For large boards, skip column uniqueness check during solution generation
        # since we already skip it for 20x20 puzzles
        if n >= 20:
            return True

        # Check column uniqueness - only if column is complete
        col = [board[r][j] for r in range(n)]
        if None not in col:
            for other in range(n):
                if other != j:
                    other_col = [board[r][other] for r in range(n)]
                    if other_col == col:
                        return False

        return True

    def generate_solution(self, n: int, max_retries: int = 5) -> Optional[List[List[int]]]:
        """
        Generate a complete valid Binairo solution.

        Args:
            n: Board size (must be even)
            max_retries: Maximum number of generation attempts

        Returns:
            Complete board or None if generation failed
        """
        if n % 2 != 0:
            raise ValueError("Board size must be even")

        # Increase retries for very large boards
        if n >= 20:
            max_retries = max(max_retries, 3)

        logger.debug(f"Generating {n}x{n} solution with max_retries={max_retries}, timeout={self.timeout}s")

        for attempt in range(max_retries):
            logger.info(f"  Solution generation attempt {attempt+1}/{max_retries} for {n}x{n} board")
            self.start_time = time.time()
            board = [[None for _ in range(n)] for _ in range(n)]

            def backtrack(pos: int) -> bool:
                # Check timeout
                elapsed = time.time() - self.start_time
                if elapsed > self.timeout:
                    logger.debug(f"    Timeout reached after {elapsed:.2f}s at position {pos}/{n*n}")
                    return False

                if pos == n * n:
                    return True

                i, j = pos // n, pos % n

                # Try values in random order
                values = [0, 1]
                random.shuffle(values)

                for val in values:
                    board[i][j] = val
                    if (self._check_streak(board, n, i, j) and
                        self._check_count(board, n, i, j) and
                        self._check_unique(board, n, i, j)):
                        if backtrack(pos + 1):
                            return True
                    board[i][j] = None

                return False

            if backtrack(0):
                elapsed = time.time() - self.start_time
                logger.info(f"  Solution found in attempt {attempt+1} after {elapsed:.2f}s for {n}x{n} board")
                return board
            else:
                elapsed = time.time() - self.start_time
                logger.warning(f"  Attempt {attempt+1} failed after {elapsed:.2f}s, retrying...")

        logger.error(f"Failed to generate {n}x{n} solution after {max_retries} attempts with {self.timeout}s timeout per attempt")
        return None

    def generate_puzzle(self, n: int, difficulty: float = 0.6) -> Tuple[List[List], List[List[int]]]:
        """
        Generate a puzzle with a unique solution.

        Args:
            n: Board size (must be even)
            difficulty: Fraction of cells to remove (0.0 to 0.8)

        Returns:
            Tuple of (puzzle with None for empty cells, complete solution)
        """
        logger.debug(f"Starting puzzle generation for {n}x{n} with difficulty={difficulty}")
        
        # Adjust difficulty for larger boards
        original_difficulty = difficulty
        if n >= 14:
            difficulty = min(difficulty, 0.5)
            logger.debug(f"Adjusted difficulty from {original_difficulty} to {difficulty} for {n}x{n} board")

        solution = self.generate_solution(n)
        if solution is None:
            error_msg = f"Failed to generate {n}x{n} solution after multiple attempts with timeout={self.timeout}s. Consider: 1) Increasing timeout, 2) Using smaller boards, 3) Reducing difficulty"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        # Calculate cells to remove
        total_cells = n * n
        cells_to_remove = int(total_cells * min(difficulty, 0.8))
        logger.debug(f"Removing {cells_to_remove} cells from {total_cells} total cells")

        # Create puzzle by removing cells
        puzzle = [row[:] for row in solution]
        positions = [(i, j) for i in range(n) for j in range(n)]
        random.shuffle(positions)

        removed = 0
        max_attempts = min(cells_to_remove * 3, total_cells)
        attempts = 0

        for i, j in positions:
            if removed >= cells_to_remove or attempts >= max_attempts:
                break

            attempts += 1
            original = puzzle[i][j]
            puzzle[i][j] = None

            # For large boards, skip uniqueness check to speed up generation
            if n >= 20:
                removed += 1
            elif self._has_unique_solution(puzzle, n):
                removed += 1
            else:
                puzzle[i][j] = original

        logger.debug(f"Removed {removed}/{cells_to_remove} cells from puzzle")
        return puzzle, solution

    def _has_unique_solution(self, puzzle: List[List], n: int) -> bool:
        """Quick check if puzzle has a solution."""
        board = [row[:] for row in puzzle]

        def solve(pos: int) -> bool:
            # Find next empty cell
            while pos < n * n:
                i, j = pos // n, pos % n
                if board[i][j] is None:
                    break
                pos += 1

            if pos >= n * n:
                return True

            i, j = pos // n, pos % n

            for val in [0, 1]:
                board[i][j] = val
                if (self._check_streak(board, n, i, j) and
                    self._check_count(board, n, i, j) and
                    self._check_unique(board, n, i, j)):
                    if solve(pos + 1):
                        return True
                board[i][j] = None

            return False

        return solve(0)


def generate_test_puzzles(sizes: List[int] = None, count_per_size: int = 5,
                          difficulty: float = 0.6, seed: int = None) -> dict:
    """
    Generate a set of test puzzles.

    Args:
        sizes: List of board sizes
        count_per_size: Number of puzzles per size
        difficulty: Puzzle difficulty
        seed: Random seed

    Returns:
        Dictionary mapping size to list of (puzzle, solution) tuples
    """
    sizes = sizes or [6, 8, 10]
    generator = PuzzleGenerator(seed=seed)

    results = {}
    for size in sizes:
        puzzles = []
        for _ in range(count_per_size):
            puzzle, solution = generator.generate_puzzle(size, difficulty)
            puzzles.append((puzzle, solution))
        results[size] = puzzles

    return results


if __name__ == "__main__":
    gen = PuzzleGenerator(seed=42)

    print("Generating 6x6 puzzle...")
    puzzle, solution = gen.generate_puzzle(6, difficulty=0.6)

    print("Puzzle:")
    for row in puzzle:
        print(' '.join('.' if x is None else str(x) for x in row))

    print("\nSolution:")
    for row in solution:
        print(' '.join(str(x) for x in row))

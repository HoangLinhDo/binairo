"""
DFS (Depth-First Search) solver for Binairo puzzles.
This is a blind search algorithm that explores solutions by trying values recursively.
"""

from typing import Optional, Tuple, Callable, Dict, Any, List
from .board import BinairoBoard
from .constraints import BinairoConstraints


class OptimizedDFSSolver:
    """
    Optimized DFS solver that works directly with lists.
    Designed to match or beat the original Binairo_Game_represent DFS.
    """

    def __init__(self):
        """Initialize the optimized DFS solver."""
        self.nodes_explored = 0
        self.backtracks = 0

    def reset_stats(self):
        """Reset statistics counters."""
        self.nodes_explored = 0
        self.backtracks = 0

    def get_stats(self) -> Dict[str, Any]:
        """Get solver statistics."""
        return {
            'nodes_explored': self.nodes_explored,
            'backtracks': self.backtracks,
            'algorithm': 'Optimized DFS'
        }

    def solve(self, puzzle: List[List], callback: Optional[Callable] = None) -> Tuple[Optional[List[List]], Dict[str, Any]]:
        """Solve a Binairo puzzle using optimized DFS."""
        self.reset_stats()

        # Work with a copy
        board = [row[:] for row in puzzle]
        n = len(board)

        if self._dfs(board, n, 0, 0):
            return board, self.get_stats()
        else:
            return None, self.get_stats()

    def _is_valid_move(self, board: List[List], n: int, row: int, col: int) -> bool:
        """Ultra-fast validity check for a move at (row, col)."""
        half = n // 2
        row_list = board[row]

        # Check row streaks (no three consecutive same values)
        start = max(0, col - 2)
        end = min(n - 3, col) + 1
        for i in range(start, end):
            if row_list[i] == row_list[i + 1] == row_list[i + 2] is not None:
                return False

        # Check column streaks
        start = max(0, row - 2)
        end = min(n - 3, row) + 1
        for i in range(start, end):
            if board[i][col] == board[i + 1][col] == board[i + 2][col] is not None:
                return False

        # Check row count and uniqueness if complete
        if None not in row_list:
            if sum(row_list) != half:
                return False
            for other_row in range(n):
                if other_row != row and board[other_row] == row_list:
                    return False

        # Check column count and uniqueness if complete
        col_values = [board[r][col] for r in range(n)]
        if None not in col_values:
            if sum(col_values) != half:
                return False
            for other_col in range(n):
                if other_col != col:
                    other_col_values = [board[r][other_col] for r in range(n)]
                    if other_col_values == col_values:
                        return False

        return True

    def _dfs(self, board: List[List], n: int, row: int, col: int) -> bool:
        """Recursive DFS solving."""
        # Find first empty cell starting from current position
        while row < n:
            if board[row][col] is None:
                break
            col += 1
            if col >= n:
                col = 0
                row += 1
        else:
            return True  # No empty cells - solved

        if row >= n:
            return True

        # Calculate next position
        next_col = col + 1
        next_row = row
        if next_col >= n:
            next_col = 0
            next_row += 1

        # Try both values
        for value in [0, 1]:
            self.nodes_explored += 1
            board[row][col] = value

            if self._is_valid_move(board, n, row, col):
                if self._dfs(board, n, next_row, next_col):
                    return True

            board[row][col] = None
            self.backtracks += 1

        return False


class DFSSolver:
    """
    Depth-First Search solver for Binairo.

    This is a pure backtracking algorithm (blind search) that:
    1. Finds the first empty cell (row-major order)
    2. Tries 0 and 1 in order
    3. Recursively solves the remaining board
    4. Backtracks if no valid solution found
    """

    def __init__(self):
        """Initialize the DFS solver."""
        # Use the optimized solver internally
        self._optimized = OptimizedDFSSolver()

    def reset_stats(self):
        """Reset statistics counters."""
        self._optimized.reset_stats()

    def get_stats(self) -> Dict[str, Any]:
        """Get solver statistics."""
        return self._optimized.get_stats()

    @property
    def nodes_explored(self):
        return self._optimized.nodes_explored

    @property
    def backtracks(self):
        return self._optimized.backtracks

    def solve(
        self,
        puzzle: List[List],
        callback: Optional[Callable] = None
    ) -> Tuple[Optional[List[List]], Dict[str, Any]]:
        """
        Solve a Binairo puzzle using DFS.

        Args:
            puzzle: 2D list representing the puzzle (None for empty cells)
            callback: Optional callback function(board, row, col, value) for visualization

        Returns:
            Tuple of (solution, stats) where solution is None if no solution found
        """
        return self._optimized.solve(puzzle, callback)


def solve_dfs(puzzle: List[List], **kwargs) -> Tuple[Optional[List[List]], Dict[str, Any]]:
    """
    Convenience function to solve a puzzle with DFS.

    Args:
        puzzle: 2D list representing the puzzle
        **kwargs: Additional arguments (callback for visualization)

    Returns:
        Tuple of (solution, stats)
    """
    solver = DFSSolver()
    return solver.solve(puzzle, **kwargs)


if __name__ == "__main__":
    # Test the DFS solver
    puzzle_str = """
    .1..0.
    0.....
    ..0..1
    1..0..
    .....0
    .0.1..
    """

    board = BinairoBoard.from_string(puzzle_str)
    print("Initial puzzle:")
    print(board)
    print()

    # Solve
    solver = DFSSolver()
    solution, stats = solver.solve(board.to_list())

    if solution:
        print("Solution found!")
        result_board = BinairoBoard(board=solution)
        print(result_board)
        print()
        print(f"Stats: {stats}")
    else:
        print("No solution found")
        print(f"Stats: {stats}")

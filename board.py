"""
Board state representation for Binairo puzzle.
Provides efficient operations for puzzles.
"""

from typing import Optional, Iterator, Tuple, List
import copy


class BinairoBoard:
    """
    Represents a Binairo board state.

    Values:
        - None (or EMPTY): Empty cell
        - 0: Black/Zero
        - 1: White/One
    """

    EMPTY = None
    BLACK = 0
    WHITE = 1

    def __init__(self, size: int = 6, board: Optional[List[List]] = None):
        """
        Initialize a Binairo board.

        Args:
            size: Board size (must be even)
            board: Optional initial board state (2D list)
        """
        if board is not None:
            self._board = [row[:] for row in board]  # Deep copy
            self._size = len(board)
        else:
            if size % 2 != 0:
                raise ValueError("Board size must be even")
            self._size = size
            self._board = [[self.EMPTY for _ in range(size)] for _ in range(size)]

        # Cache for empty cells count
        self._empty_count = None
        self._invalidate_cache()

    def _invalidate_cache(self):
        """Invalidate cached values."""
        self._empty_count = None

    @property
    def size(self) -> int:
        """Get board size."""
        return self._size

    @property
    def board(self) -> List[List]:
        """Get the raw board (for compatibility)."""
        return self._board

    def get(self, row: int, col: int) -> Optional[int]:
        """Get value at position."""
        return self._board[row][col]

    def set(self, row: int, col: int, value: Optional[int]):
        """Set value at position."""
        self._board[row][col] = value
        self._invalidate_cache()

    def clear(self, row: int, col: int):
        """Clear a cell (set to EMPTY)."""
        self.set(row, col, self.EMPTY)

    def is_empty(self, row: int, col: int) -> bool:
        """Check if a cell is empty."""
        return self._board[row][col] is None

    def get_row(self, row: int) -> List:
        """Get a row."""
        return self._board[row][:]

    def get_col(self, col: int) -> List:
        """Get a column."""
        return [self._board[row][col] for row in range(self._size)]

    def count_in_row(self, row: int, value: int) -> int:
        """Count occurrences of a value in a row."""
        return self._board[row].count(value)

    def count_in_col(self, col: int, value: int) -> int:
        """Count occurrences of a value in a column."""
        return sum(1 for r in range(self._size) if self._board[r][col] == value)

    def count_empty_in_row(self, row: int) -> int:
        """Count empty cells in a row."""
        return self._board[row].count(self.EMPTY)

    def count_empty_in_col(self, col: int) -> int:
        """Count empty cells in a column."""
        return sum(1 for r in range(self._size) if self._board[r][col] is None)

    def get_empty_count(self) -> int:
        """Get total number of empty cells (cached)."""
        if self._empty_count is None:
            self._empty_count = sum(
                1 for row in self._board for cell in row if cell is None
            )
        return self._empty_count

    def is_complete(self) -> bool:
        """Check if board is completely filled."""
        return self.get_empty_count() == 0

    def get_empty_cells(self) -> List[Tuple[int, int]]:
        """Get list of all empty cell positions."""
        return [
            (row, col)
            for row in range(self._size)
            for col in range(self._size)
            if self._board[row][col] is None
        ]

    def get_first_empty(self) -> Optional[Tuple[int, int]]:
        """Get the first empty cell (row-major order)."""
        for row in range(self._size):
            for col in range(self._size):
                if self._board[row][col] is None:
                    return (row, col)
        return None

    def iter_cells(self) -> Iterator[Tuple[int, int, Optional[int]]]:
        """Iterate over all cells: yields (row, col, value)."""
        for row in range(self._size):
            for col in range(self._size):
                yield row, col, self._board[row][col]

    def copy(self) -> 'BinairoBoard':
        """Create a deep copy of the board."""
        return BinairoBoard(board=self._board)

    def to_list(self) -> List[List]:
        """Convert to 2D list."""
        return [row[:] for row in self._board]

    @classmethod
    def from_list(cls, board: List[List]) -> 'BinairoBoard':
        """Create a board from a 2D list."""
        return cls(board=board)

    @classmethod
    def from_string(cls, s: str) -> 'BinairoBoard':
        """
        Create a board from a string representation.

        Format: Each row on a new line, '.' for empty, '0' for black, '1' for white.
        """
        board = []
        for line in s.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            row = []
            for c in line:
                if c == '.':
                    row.append(None)
                elif c in '01':
                    row.append(int(c))
            if row:
                board.append(row)
        return cls(board=board)

    def to_string(self) -> str:
        """Convert to string representation."""
        lines = []
        for row in self._board:
            line = ''.join(
                '.' if cell is None else str(cell)
                for cell in row
            )
            lines.append(line)
        return '\n'.join(lines)

    def __str__(self) -> str:
        """String representation with grid."""
        lines = []
        lines.append('┌' + '─' * (self._size * 2 + 1) + '┐')
        for row in self._board:
            cells = ' '.join(
                '·' if cell is None else ('○' if cell == 1 else '●')
                for cell in row
            )
            lines.append(f'│ {cells} │')
        lines.append('└' + '─' * (self._size * 2 + 1) + '┘')
        return '\n'.join(lines)

    def __repr__(self) -> str:
        return f"BinairoBoard(size={self._size})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, BinairoBoard):
            return False
        return self._board == other._board

    def __hash__(self):
        """Hash for use in sets/dicts."""
        return hash(tuple(tuple(row) for row in self._board))

    # Row/Column comparison for uniqueness checking
    def row_as_tuple(self, row: int) -> Optional[Tuple]:
        """Get row as tuple (for comparison). Returns None if incomplete."""
        r = self._board[row]
        if None in r:
            return None
        return tuple(r)

    def col_as_tuple(self, col: int) -> Optional[Tuple]:
        """Get column as tuple (for comparison). Returns None if incomplete."""
        c = self.get_col(col)
        if None in c:
            return None
        return tuple(c)

    def get_all_complete_rows(self) -> List[Tuple[int, Tuple]]:
        """Get all complete rows as (index, tuple) pairs."""
        result = []
        for i in range(self._size):
            row_tuple = self.row_as_tuple(i)
            if row_tuple is not None:
                result.append((i, row_tuple))
        return result

    def get_all_complete_cols(self) -> List[Tuple[int, Tuple]]:
        """Get all complete columns as (index, tuple) pairs."""
        result = []
        for j in range(self._size):
            col_tuple = self.col_as_tuple(j)
            if col_tuple is not None:
                result.append((j, col_tuple))
        return result


if __name__ == "__main__":
    # Test the board
    puzzle_str = """
    .1..0.
    0.....
    ..0..1
    1..0..
    .....0
    .0.1..
    """

    board = BinairoBoard.from_string(puzzle_str)
    print("Board:")
    print(board)
    print(f"\nSize: {board.size}")
    print(f"Empty cells: {board.get_empty_count()}")
    print(f"Empty positions: {board.get_empty_cells()}")
    print(f"\nRow 0: {board.get_row(0)}")
    print(f"Col 1: {board.get_col(1)}")
    print(f"\nCount of 1s in row 0: {board.count_in_row(0, 1)}")
    print(f"Count of 0s in col 1: {board.count_in_col(1, 0)}")

    # Test copy
    board_copy = board.copy()
    board_copy.set(0, 0, 0)
    print(f"\nOriginal (0,0): {board.get(0, 0)}")
    print(f"Copy (0,0): {board_copy.get(0, 0)}")

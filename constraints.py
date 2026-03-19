"""
Constraint validation for Binairo puzzles.
Provides modular constraint checking functions.

Binairo Rules:
1. Each cell contains either 0 or 1
2. No more than two consecutive 0s or 1s in any row or column
3. Each row and column must have equal counts of 0s and 1s (n/2 each)
4. All rows must be unique
5. All columns must be unique
"""

from typing import List, Optional, Tuple, Set
from .board import BinairoBoard


class BinairoConstraints:
    """
    Constraint checker for Binairo puzzles.

    All methods are static for easy reuse.
    """

    @staticmethod
    def check_no_triple_at(board: BinairoBoard, row: int, col: int) -> bool:
        """
        Check if placing value at (row, col) violates the no-triple rule.

        Returns True if valid (no violation), False if invalid.
        """
        val = board.get(row, col)
        if val is None:
            return True

        n = board.size

        # Check horizontal (row) - look for triples containing this cell
        # Start positions that would include col in a triple: col-2, col-1, col
        for start_col in range(max(0, col - 2), min(n - 2, col + 1)):
            if start_col + 2 < n:
                if (board.get(row, start_col) == val and
                    board.get(row, start_col + 1) == val and
                    board.get(row, start_col + 2) == val):
                    return False

        # Check vertical (column)
        for start_row in range(max(0, row - 2), min(n - 2, row + 1)):
            if start_row + 2 < n:
                if (board.get(start_row, col) == val and
                    board.get(start_row + 1, col) == val and
                    board.get(start_row + 2, col) == val):
                    return False

        return True

    @staticmethod
    def check_no_triple_row(board: BinairoBoard, row: int) -> bool:
        """Check entire row for triple violations."""
        n = board.size
        for col in range(n - 2):
            val = board.get(row, col)
            if val is not None:
                if board.get(row, col + 1) == val and board.get(row, col + 2) == val:
                    return False
        return True

    @staticmethod
    def check_no_triple_col(board: BinairoBoard, col: int) -> bool:
        """Check entire column for triple violations."""
        n = board.size
        for row in range(n - 2):
            val = board.get(row, col)
            if val is not None:
                if board.get(row + 1, col) == val and board.get(row + 2, col) == val:
                    return False
        return True

    @staticmethod
    def check_no_triple_all(board: BinairoBoard) -> bool:
        """Check all rows and columns for triple violations."""
        for i in range(board.size):
            if not BinairoConstraints.check_no_triple_row(board, i):
                return False
            if not BinairoConstraints.check_no_triple_col(board, i):
                return False
        return True

    @staticmethod
    def check_count_at(board: BinairoBoard, row: int, col: int) -> bool:
        """
        Check if count constraint is still satisfiable at (row, col).

        Returns True if valid, False if the row/column already has too many 0s or 1s.
        """
        n = board.size
        half = n // 2

        # Check row counts
        if board.count_in_row(row, 0) > half or board.count_in_row(row, 1) > half:
            return False

        # Check column counts
        if board.count_in_col(col, 0) > half or board.count_in_col(col, 1) > half:
            return False

        return True

    @staticmethod
    def check_count_row(board: BinairoBoard, row: int) -> bool:
        """Check if row count constraint is valid (for complete rows)."""
        n = board.size
        half = n // 2
        row_data = board.get_row(row)

        if None in row_data:
            # Incomplete row - just check not exceeded
            return row_data.count(0) <= half and row_data.count(1) <= half
        else:
            # Complete row - must be exactly half
            return row_data.count(0) == half and row_data.count(1) == half

    @staticmethod
    def check_count_col(board: BinairoBoard, col: int) -> bool:
        """Check if column count constraint is valid (for complete columns)."""
        n = board.size
        half = n // 2
        col_data = board.get_col(col)

        if None in col_data:
            return col_data.count(0) <= half and col_data.count(1) <= half
        else:
            return col_data.count(0) == half and col_data.count(1) == half

    @staticmethod
    def check_unique_row(board: BinairoBoard, row: int) -> bool:
        """Check if the row (when complete) is unique."""
        row_tuple = board.row_as_tuple(row)
        if row_tuple is None:
            return True  # Incomplete rows are always valid

        for other_row in range(board.size):
            if other_row != row:
                other_tuple = board.row_as_tuple(other_row)
                if other_tuple == row_tuple:
                    return False
        return True

    @staticmethod
    def check_unique_col(board: BinairoBoard, col: int) -> bool:
        """Check if the column (when complete) is unique."""
        col_tuple = board.col_as_tuple(col)
        if col_tuple is None:
            return True  # Incomplete columns are always valid

        for other_col in range(board.size):
            if other_col != col:
                other_tuple = board.col_as_tuple(other_col)
                if other_tuple == col_tuple:
                    return False
        return True

    @staticmethod
    def check_unique_at(board: BinairoBoard, row: int, col: int) -> bool:
        """Check uniqueness constraint for the row and column at (row, col)."""
        return (BinairoConstraints.check_unique_row(board, row) and
                BinairoConstraints.check_unique_col(board, col))

    @staticmethod
    def check_all_unique_rows(board: BinairoBoard) -> bool:
        """Check if all complete rows are unique."""
        complete_rows = board.get_all_complete_rows()
        row_tuples = [t for _, t in complete_rows]
        return len(row_tuples) == len(set(row_tuples))

    @staticmethod
    def check_all_unique_cols(board: BinairoBoard) -> bool:
        """Check if all complete columns are unique."""
        complete_cols = board.get_all_complete_cols()
        col_tuples = [t for _, t in complete_cols]
        return len(col_tuples) == len(set(col_tuples))

    @staticmethod
    def is_valid_move(board: BinairoBoard, row: int, col: int) -> bool:
        """
        Check if the current value at (row, col) is valid.

        Combines all constraint checks for a single cell placement.
        """
        return (BinairoConstraints.check_no_triple_at(board, row, col) and
                BinairoConstraints.check_count_at(board, row, col) and
                BinairoConstraints.check_unique_at(board, row, col))

    @staticmethod
    def is_valid_board(board: BinairoBoard) -> bool:
        """
        Check if the entire board is valid.

        Returns True if all constraints are satisfied.
        """
        # Check triple constraint for all cells
        if not BinairoConstraints.check_no_triple_all(board):
            return False

        # Check count constraints for all rows/columns
        for i in range(board.size):
            if not BinairoConstraints.check_count_row(board, i):
                return False
            if not BinairoConstraints.check_count_col(board, i):
                return False

        # Check uniqueness
        if not BinairoConstraints.check_all_unique_rows(board):
            return False
        if not BinairoConstraints.check_all_unique_cols(board):
            return False

        return True

    @staticmethod
    def is_complete_and_valid(board: BinairoBoard) -> bool:
        """Check if the board is completely filled and valid."""
        return board.is_complete() and BinairoConstraints.is_valid_board(board)

    @staticmethod
    def get_possible_values(board: BinairoBoard, row: int, col: int) -> List[int]:
        """
        Get possible values for a cell.

        Returns a list of values (0, 1) that don't immediately violate constraints.
        """
        if board.get(row, col) is not None:
            return []  # Cell already filled

        possible = []
        for val in [0, 1]:
            board.set(row, col, val)
            if BinairoConstraints.is_valid_move(board, row, col):
                possible.append(val)
            board.clear(row, col)

        return possible

    @staticmethod
    def count_possible_values(board: BinairoBoard, row: int, col: int) -> int:
        """Count possible values for a cell (returns 0, 1, or 2)."""
        return len(BinairoConstraints.get_possible_values(board, row, col))

    @staticmethod
    def get_forced_value(board: BinairoBoard, row: int, col: int) -> Optional[int]:
        """
        Get the forced value for a cell if only one option is valid.

        Returns the value if forced, None otherwise.
        """
        possible = BinairoConstraints.get_possible_values(board, row, col)
        if len(possible) == 1:
            return possible[0]
        return None

    @staticmethod
    def would_create_triple(board: BinairoBoard, row: int, col: int, val: int) -> bool:
        """Check if placing val at (row, col) would create a triple."""
        original = board.get(row, col)
        board.set(row, col, val)
        result = not BinairoConstraints.check_no_triple_at(board, row, col)
        board.set(row, col, original)
        return result


# Convenience aliases
check_valid_move = BinairoConstraints.is_valid_move
check_valid_board = BinairoConstraints.is_valid_board
get_possible = BinairoConstraints.get_possible_values


if __name__ == "__main__":
    # Test the constraints
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

    print("\nConstraint checks:")
    print(f"Valid board: {BinairoConstraints.is_valid_board(board)}")
    print(f"Complete: {board.is_complete()}")

    # Test possible values for empty cells
    print("\nPossible values for empty cells:")
    for row, col in board.get_empty_cells()[:5]:  # First 5 empty cells
        possible = BinairoConstraints.get_possible_values(board, row, col)
        print(f"  ({row}, {col}): {possible}")

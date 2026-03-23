"""
Testcases module for Binairo solver.
Provides puzzle generation and test case management.
"""

try:
    from nmai_binairo.testcases.puzzle_generator import PuzzleGenerator, generate_test_puzzles
    from nmai_binairo.testcases.test_cases import TestCases, TestcaseFetcher
except ImportError:
    from .puzzle_generator import PuzzleGenerator, generate_test_puzzles
    from .test_cases import TestCases, TestcaseFetcher

__all__ = [
    'PuzzleGenerator',
    'generate_test_puzzles',
    'TestCases',
    'TestcaseFetcher',
]

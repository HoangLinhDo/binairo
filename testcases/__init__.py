"""
Testcases module for Binairo solver.
Provides puzzle generation and test case management.
"""

from .puzzle_generator import PuzzleGenerator, generate_test_puzzles
from .test_cases import TestCases, TestcaseFetcher

__all__ = [
    'PuzzleGenerator',
    'generate_test_puzzles',
    'TestCases',
    'TestcaseFetcher',
]

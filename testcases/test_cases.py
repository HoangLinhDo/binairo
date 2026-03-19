"""
Testcase fetcher for Binairo puzzles.
Fetches puzzles from online sources.
"""

import json
import os
import re
from typing import List, Tuple, Optional
from pathlib import Path

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class TestcaseFetcher:
    """
    Fetches Binairo puzzles from online sources.
    """

    # Base URL for binary puzzle
    BASE_URL = "https://www.binarypuzzle.com"

    # Size mapping
    SIZE_MAP = {
        6: "6x6",
        8: "8x8",
        10: "10x10",
        12: "12x12",
        14: "14x14",
        20: "20x20",
    }

    # Difficulty mapping
    DIFFICULTY_MAP = {
        "easy": "easy",
        "medium": "medium",
        "hard": "hard",
        "very_hard": "very-hard",
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the testcase fetcher.

        Args:
            cache_dir: Directory to cache fetched puzzles
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch_puzzle_from_url(self, url: str) -> Optional[Tuple[List[List], int]]:
        """
        Fetch a puzzle from a URL.

        Args:
            url: URL to fetch from

        Returns:
            Tuple of (puzzle, size) or None if failed
        """
        if not REQUESTS_AVAILABLE:
            print("Error: requests library not available. Install with: pip install requests")
            return None

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return self._parse_puzzle_html(response.text)
        except Exception as e:
            print(f"Error fetching puzzle: {e}")
            return None

    def _parse_puzzle_html(self, html: str) -> Optional[Tuple[List[List], int]]:
        """
        Parse puzzle from HTML content.

        Returns:
            Tuple of (puzzle, size) or None if parsing failed
        """
        # Look for puzzle data in the HTML
        # Pattern for binary puzzle site
        pattern = r'puzzle\s*=\s*\[([\s\S]*?)\];'
        match = re.search(pattern, html)

        if match:
            try:
                puzzle_data = match.group(1)
                # Parse the array
                rows = re.findall(r'\[([\d,\s]+)\]', puzzle_data)
                puzzle = []
                for row_str in rows:
                    row = []
                    for val in row_str.split(','):
                        val = val.strip()
                        if val == '0':
                            row.append(0)
                        elif val == '1':
                            row.append(1)
                        else:
                            row.append(None)
                    if row:
                        puzzle.append(row)

                if puzzle:
                    return puzzle, len(puzzle)
            except Exception:
                pass

        # Alternative pattern
        pattern = r'<td[^>]*class="[^"]*cell[^"]*"[^>]*>([01\s]*)</td>'
        cells = re.findall(pattern, html, re.IGNORECASE)

        if cells:
            # Determine board size
            size = int(len(cells) ** 0.5)
            if size * size == len(cells):
                puzzle = []
                for i in range(size):
                    row = []
                    for j in range(size):
                        cell = cells[i * size + j].strip()
                        if cell == '0':
                            row.append(0)
                        elif cell == '1':
                            row.append(1)
                        else:
                            row.append(None)
                    puzzle.append(row)
                return puzzle, size

        return None

    def fetch_random_puzzle(self, size: int = 6, difficulty: str = "medium") -> Optional[List[List]]:
        """
        Fetch a random puzzle from online.

        Args:
            size: Board size
            difficulty: Difficulty level

        Returns:
            Puzzle or None if failed
        """
        if not REQUESTS_AVAILABLE:
            print("Warning: requests library not available. Falling back to local generation.")
            return self._generate_locally(size, difficulty)

        # Try to fetch from API
        size_str = self.SIZE_MAP.get(size)
        diff_str = self.DIFFICULTY_MAP.get(difficulty, "medium")

        if size_str:
            # Try binarypuzzle.com API
            try:
                import random
                puzzle_id = random.randint(1, 1000)
                url = f"{self.BASE_URL}/puzzles.php?size={size_str}&level={diff_str}&nr={puzzle_id}"
                print(f"Fetching puzzle from API: {size}x{size} {difficulty}...")

                response = requests.get(url, timeout=15)
                response.raise_for_status()

                result = self._parse_puzzle_html(response.text)
                if result:
                    puzzle, parsed_size = result
                    if parsed_size == size:
                        print(f"Successfully fetched {size}x{size} puzzle from API")
                        return puzzle
            except Exception as e:
                print(f"API fetch failed: {e}")

        # Fall back to local generation
        print(f"Falling back to local generation for {size}x{size} puzzle...")
        return self._generate_locally(size, difficulty)

    def _generate_locally(self, size: int, difficulty: str) -> Optional[List[List]]:
        """Generate puzzle locally as fallback."""
        from .puzzle_generator import PuzzleGenerator

        difficulty_map = {
            "easy": 0.4,
            "medium": 0.55,
            "hard": 0.65,
            "very_hard": 0.75,
        }

        gen = PuzzleGenerator()
        puzzle, _ = gen.generate_puzzle(size, difficulty_map.get(difficulty, 0.55))
        return puzzle

    def save_puzzle(self, puzzle: List[List], filename: str):
        """Save puzzle to cache."""
        filepath = self.cache_dir / filename
        with open(filepath, 'w') as f:
            json.dump(puzzle, f)
        print(f"Saved puzzle to {filepath}")

    def load_puzzle(self, filename: str) -> Optional[List[List]]:
        """Load puzzle from cache."""
        filepath = self.cache_dir / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return None

    def list_cached_puzzles(self) -> List[str]:
        """List all cached puzzles."""
        return [f.name for f in self.cache_dir.glob("*.json")]


class TestCases:
    """
    Manages test cases for benchmarking.
    """

    def __init__(self, testcases_dir: Optional[str] = None):
        """
        Initialize test cases manager.

        Args:
            testcases_dir: Directory containing test cases
        """
        if testcases_dir is None:
            testcases_dir = os.path.dirname(__file__)
        self.testcases_dir = Path(testcases_dir)
        self.fetcher = TestcaseFetcher(cache_dir=str(self.testcases_dir / "cache"))

    def get_test_puzzles(self, sizes: List[int] = None, count: int = 5,
                         difficulty: str = "medium") -> dict:
        """
        Get test puzzles for benchmarking.

        Args:
            sizes: List of board sizes
            count: Number of puzzles per size
            difficulty: Difficulty level

        Returns:
            Dictionary mapping size to list of puzzles
        """
        sizes = sizes or [6, 8, 10]

        from .puzzle_generator import PuzzleGenerator

        difficulty_map = {
            "easy": 0.4,
            "medium": 0.55,
            "hard": 0.65,
            "very_hard": 0.75,
        }
        diff_value = difficulty_map.get(difficulty, 0.55)

        results = {}
        for size in sizes:
            puzzles = []
            for i in range(count):
                # Try to load from cache first
                cache_file = f"puzzle_{size}x{size}_{difficulty}_{i}.json"
                puzzle = self.fetcher.load_puzzle(cache_file)

                if puzzle is None:
                    # Generate new puzzle
                    gen = PuzzleGenerator(seed=42 + i * 100 + size)
                    puzzle, _ = gen.generate_puzzle(size, diff_value)
                    self.fetcher.save_puzzle(puzzle, cache_file)

                puzzles.append(puzzle)

            results[size] = puzzles

        return results

    def save_testcases(self, testcases: dict, filename: str = "testcases.json"):
        """Save all testcases to a file."""
        filepath = self.testcases_dir / filename
        # Convert to serializable format
        serializable = {}
        for size, puzzles in testcases.items():
            serializable[str(size)] = puzzles

        with open(filepath, 'w') as f:
            json.dump(serializable, f, indent=2)
        print(f"Saved test cases to {filepath}")

    def load_testcases(self, filename: str = "testcases.json") -> Optional[dict]:
        """Load testcases from a file."""
        filepath = self.testcases_dir / filename
        if filepath.exists():
            with open(filepath, 'r') as f:
                data = json.load(f)
                # Convert keys back to integers
                return {int(k): v for k, v in data.items()}
        return None


if __name__ == "__main__":
    # Test the fetcher
    tc = TestCases()

    print("Generating test puzzles...")
    puzzles = tc.get_test_puzzles(sizes=[6, 8], count=3)

    for size, puzzle_list in puzzles.items():
        print(f"\n{size}x{size} puzzles: {len(puzzle_list)}")
        for i, puzzle in enumerate(puzzle_list):
            empty = sum(1 for row in puzzle for cell in row if cell is None)
            print(f"  Puzzle {i+1}: {empty} empty cells")

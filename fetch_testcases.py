#!/usr/bin/env python3
"""
Testcase Generator/Fetcher for Binairo Puzzles

Generates or fetches puzzles for benchmarking.

Usage:
    python fetch_testcases.py                      # Generate default testcases
    python fetch_testcases.py --sizes 6 8 10      # Specific sizes
    python fetch_testcases.py --count 10          # 10 puzzles per size
    python fetch_testcases.py --difficulty hard   # Hard difficulty
    python fetch_testcases.py --output puzzles.json  # Custom output file
"""

import sys
import os
import json
import argparse
import logging
from typing import List, Dict
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fetch_testcases.log')
    ]
)
logger = logging.getLogger(__name__)

from nmai_binairo.testcases.puzzle_generator import PuzzleGenerator
from nmai_binairo.testcases.test_cases import TestCases


def generate_testcases(sizes: List[int], count: int, difficulty: str,
                       output_file: str, seed: int = None):
    """
    Generate test cases and save them.

    Args:
        sizes: List of board sizes
        count: Number of puzzles per size
        difficulty: Difficulty level
        output_file: Output file path
        seed: Random seed for reproducibility
    """
    logger.info("=" * 60)
    logger.info("BINAIRO TESTCASE GENERATOR")
    logger.info("=" * 60)
    logger.info(f"Sizes: {sizes}")
    logger.info(f"Puzzles per size: {count}")
    logger.info(f"Difficulty: {difficulty}")
    logger.info(f"Output: {output_file}")
    if seed is not None:
        logger.info(f"Seed: {seed}")
    logger.info("=" * 60)
    
    print("=" * 60)
    print("BINAIRO TESTCASE GENERATOR")
    print("=" * 60)
    print(f"Sizes: {sizes}")
    print(f"Puzzles per size: {count}")
    print(f"Difficulty: {difficulty}")
    print(f"Output: {output_file}")
    if seed is not None:
        print(f"Seed: {seed}")
    print("=" * 60)
    print()

    # Difficulty mapping
    difficulty_map = {
        "easy": 0.4,
        "medium": 0.55,
        "hard": 0.65,
        "very_hard": 0.75,
    }
    diff_value = difficulty_map.get(difficulty, 0.55)

    all_puzzles = {}
    total_generated = 0

    for size in sizes:
        logger.info(f"\nGenerating {count} {size}x{size} puzzles...")
        print(f"\nGenerating {count} {size}x{size} puzzles...")
        puzzles = []

        # Calculate appropriate timeout based on board size
        # Larger boards need MUCH more time for generation
        if size <= 8:
            timeout = 30.0
        elif size <= 12:
            timeout = 60.0
        elif size <= 14:
            timeout = 180.0
        elif size <= 18:
            timeout = 240.0
        else:  # 20+
            timeout = 300.0
        
        logger.info(f"Using timeout: {timeout}s for {size}x{size} boards")
        generator = PuzzleGenerator(seed=seed, timeout=timeout)

        for i in range(count):
            try:
                logger.debug(f"  [{i+1}/{count}] Starting generation...")
                puzzle, solution = generator.generate_puzzle(size, diff_value)
                empty_cells = sum(1 for row in puzzle for cell in row if cell is None)
                puzzles.append({
                    'puzzle': puzzle,
                    'solution': solution,
                    'size': size,
                    'difficulty': difficulty,
                    'empty_cells': empty_cells
                })
                total_generated += 1
                msg = f"  [{i+1}/{count}] Generated puzzle with {empty_cells} empty cells"
                logger.info(msg)
                print(msg)

                # Update seed for next puzzle
                if seed is not None:
                    seed += 1

            except Exception as e:
                error_msg = f"  [{i+1}/{count}] Failed to generate puzzle: {type(e).__name__}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                print(error_msg)

        all_puzzles[str(size)] = puzzles

    # Save to file
    output_path = os.path.join(os.path.dirname(__file__), 'testcases', output_file)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(all_puzzles, f, indent=2)

    summary = f"COMPLETE: Generated {total_generated} puzzles\nSaved to: {output_path}"
    logger.info(summary)
    print()
    print("=" * 60)
    print(summary)
    print("=" * 60)

    return all_puzzles


def display_puzzle(puzzle: List[List]):
    """Display a puzzle in ASCII format."""
    for row in puzzle:
        line = ' '.join('.' if cell is None else str(cell) for cell in row)
        print(f"  {line}")


def list_testcases(input_file: str):
    """List existing test cases."""
    input_path = os.path.join(os.path.dirname(__file__), 'testcases', input_file)

    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    with open(input_path, 'r') as f:
        data = json.load(f)

    print("=" * 60)
    print("AVAILABLE TESTCASES")
    print("=" * 60)
    print(f"File: {input_path}")
    print()

    for size, puzzles in sorted(data.items(), key=lambda x: int(x[0])):
        print(f"{size}x{size} puzzles: {len(puzzles)}")
        for i, p in enumerate(puzzles):
            empty = p.get('empty_cells', '?')
            diff = p.get('difficulty', 'unknown')
            print(f"  Puzzle {i+1}: {empty} empty cells, {diff}")

    print()
    print(f"Total: {sum(len(p) for p in data.values())} puzzles")
    print("=" * 60)


def show_puzzle(input_file: str, size: int, index: int):
    """Show a specific puzzle."""
    input_path = os.path.join(os.path.dirname(__file__), 'testcases', input_file)

    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return

    with open(input_path, 'r') as f:
        data = json.load(f)

    key = str(size)
    if key not in data:
        print(f"No puzzles of size {size}x{size}")
        return

    puzzles = data[key]
    if index < 1 or index > len(puzzles):
        print(f"Invalid index. Available: 1-{len(puzzles)}")
        return

    puzzle_data = puzzles[index - 1]

    print(f"\n{size}x{size} Puzzle #{index}")
    print("-" * 30)
    print("\nPuzzle:")
    display_puzzle(puzzle_data['puzzle'])

    print("\nSolution:")
    display_puzzle(puzzle_data['solution'])


def main():
    parser = argparse.ArgumentParser(
        description='Generate or manage Binairo testcases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python fetch_testcases.py                     # Generate default testcases
  python fetch_testcases.py --sizes 6 8 10 14  # Specific sizes
  python fetch_testcases.py --count 20         # 20 puzzles per size
  python fetch_testcases.py --list             # List existing testcases
  python fetch_testcases.py --show 6 1         # Show puzzle 1 of size 6x6
        """
    )

    parser.add_argument('--sizes', type=int, nargs='+', default=[6, 8, 10],
                        help='Board sizes to generate (default: 6 8 10)')
    parser.add_argument('--count', type=int, default=5,
                        help='Number of puzzles per size (default: 5)')
    parser.add_argument('--difficulty', choices=['easy', 'medium', 'hard', 'very_hard'],
                        default='medium', help='Puzzle difficulty (default: medium)')
    parser.add_argument('--output', type=str, default='testcases.json',
                        help='Output file name (default: testcases.json)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducibility')
    parser.add_argument('--list', action='store_true',
                        help='List existing testcases')
    parser.add_argument('--show', type=int, nargs=2, metavar=('SIZE', 'INDEX'),
                        help='Show a specific puzzle (size, index)')
    parser.add_argument('--input', type=str, default='testcases.json',
                        help='Input file for --list or --show')

    args = parser.parse_args()

    if args.list:
        list_testcases(args.input)
    elif args.show:
        show_puzzle(args.input, args.show[0], args.show[1])
    else:
        generate_testcases(
            sizes=args.sizes,
            count=args.count,
            difficulty=args.difficulty,
            output_file=args.output,
            seed=args.seed
        )


if __name__ == "__main__":
    main()

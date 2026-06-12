"""Level grid loading, parsing, and formatting utilities.

A level segment is plain text: one row per line, one tile per character. These
helpers keep every tool from reimplementing the same parsing. They are agnostic
to the tile vocabulary itself; validation of the vocabulary lives in the analysis
tools.
"""

from __future__ import annotations

from pathlib import Path


def load_level(path: str | Path) -> str:
    """Load a level segment from a text file, trimming trailing blank lines."""
    return Path(path).read_text(encoding="utf-8").rstrip("\n")


def save_level(level_text: str, path: str | Path) -> None:
    """Save a level segment to a text file, creating parent directories as needed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(level_text.rstrip("\n") + "\n", encoding="utf-8")


def parse_level(level_text: str) -> list[list[str]]:
    """Parse level text into a grid of single character tiles, one list per row."""
    return [list(line) for line in level_text.rstrip("\n").split("\n")]


def format_level(grid: list[list[str]]) -> str:
    """Format a tile grid back into level text."""
    return "\n".join("".join(row) for row in grid)


def get_level_dimensions(level_text: str) -> tuple[int, int]:
    """Return the (height, width) of a level as (row count, first row length)."""
    grid = parse_level(level_text)
    height = len(grid)
    width = len(grid[0]) if grid else 0
    return height, width

"""Reference level library for similarity.

Loads the curated reference level segments (hand authored Mario style 14 by 32
segments, inspired by the VGLC Super Mario Bros corpus) from
data/reference_levels/ so the novelty tool can measure how derivative a candidate
is. The repository is self contained; the reference set ships with it.
"""

from __future__ import annotations

from pathlib import Path

from src.level_io import load_level

REFERENCE_DIR = "data/reference_levels"


def load_reference_levels(reference_dir: str | Path = REFERENCE_DIR) -> list[str]:
    """Load every reference level segment (sorted by filename) as raw text."""
    directory = Path(reference_dir)
    return [load_level(path) for path in sorted(directory.glob("*.txt"))]

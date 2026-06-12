"""Adapter tests for the real Project 5 generator.

These load the trained checkpoint and sample real level chunks, so they are slower
than the rest of the suite (a few seconds per generated level on CPU). Real
generations are kept to a minimum; the service level generation command is tested
separately with the fast mock generator.
"""

from __future__ import annotations

import pytest

from ai_level_director.adapters.project5_generator import Project5GeneratorAdapter

VALID_TILES = set("-<>?BEQSX[]bo")


def test_generation_is_deterministic_and_well_formed():
    adapter = Project5GeneratorAdapter()
    first = adapter.generate("easy", n=1, temperature=1.0, seed=7)[0]
    second = adapter.generate("easy", n=1, temperature=1.0, seed=7)[0]

    assert first == second  # same seed reproduces the same chunk

    rows = first.split("\n")
    assert len(rows) == 14
    assert all(len(row) == 32 for row in rows)
    assert set(first.replace("\n", "")) <= VALID_TILES  # no control tokens leaked


def test_unknown_difficulty_raises():
    adapter = Project5GeneratorAdapter()
    with pytest.raises(ValueError):
        adapter.generate("impossible", n=1)


def test_non_positive_temperature_raises():
    adapter = Project5GeneratorAdapter()
    with pytest.raises(ValueError):
        adapter.generate("easy", n=1, temperature=0.0)

"""Unit tests for the ASCII renderer.

Rendering is for preview only, so these check that the grid is tidied without
altering tiles. Image based rendering is a deferred polish feature and is not
tested here.
"""

from __future__ import annotations

from ai_level_director.rendering.ascii_renderer import render_level_ascii

LEVEL = "----\nXX-X\n--E-"


def test_ascii_strips_trailing_whitespace_and_blank_lines():
    text = "----  \nXX-X\n\n  \n"
    assert render_level_ascii(text) == "----\nXX-X"


def test_ascii_preserves_tiles():
    assert render_level_ascii(LEVEL) == LEVEL


def test_ascii_empty_input():
    assert render_level_ascii("") == ""

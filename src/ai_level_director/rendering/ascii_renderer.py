"""ASCII rendering of a level: a clean monospace tile grid.

This is the simplest preview. It tidies the raw tile text into a grid that
displays well in monospace contexts (the notebook, the UI, reports) without
changing any tiles. The raw text stays the source of truth.
"""

from __future__ import annotations


def render_level_ascii(level_text: str) -> str:
    """Return the level as a clean monospace grid.

    Trailing whitespace is stripped from each row and trailing blank lines are
    removed. Tiles themselves are never modified.
    """
    rows = [row.rstrip() for row in level_text.splitlines()]
    while rows and rows[-1] == "":
        rows.pop()
    return "\n".join(rows)

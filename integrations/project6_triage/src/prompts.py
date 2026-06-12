"""Prompt template loading.

Agent instructions are stored as templates under prompt_templates/<variant>/ so they
are transparent, version controlled, and swappable. PROMPT_VARIANT selects the set:
"tuned" is the shipped system; "baseline" is the untuned prompts used in the model
selection comparison, kept so that experiment stays reproducible (set
PROMPT_VARIANT=baseline to run the agents on the original prompts).
"""

from __future__ import annotations

import os
from pathlib import Path

PROMPT_VARIANT = os.environ.get("PROMPT_VARIANT", "tuned")
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "prompt_templates"


def load_prompt(name: str, variant: str | None = None) -> str:
    """Load an agent instruction template by name and variant (default PROMPT_VARIANT)."""
    chosen = variant or PROMPT_VARIANT
    return (_TEMPLATE_DIR / chosen / f"{name}.md").read_text(encoding="utf-8").strip()

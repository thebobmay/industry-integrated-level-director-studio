"""Environment configuration loading.

The project reads credentials and settings from the repository ``.env``. By
default ``python-dotenv`` does not override variables already present in the
process environment, so a stale shell or system value (for example an old API key)
would silently win. ``load_environment`` loads the local ``.env`` with
``override=True`` so the repository's own ``.env`` is always the source of truth.
"""

from __future__ import annotations

from pathlib import Path

from dotenv import load_dotenv

# config.py -> ai_level_director -> src -> repo root.
_REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = _REPO_ROOT / ".env"


def load_environment(env_path: Path | str = ENV_PATH, override: bool = True) -> bool:
    """Load the repository ``.env`` so it takes precedence over the process env.

    ``override=True`` ensures the local ``.env`` wins over any variable already set
    in the shell or system environment, which keeps the project reproducible from
    its own ``.env`` and avoids stale system credentials shadowing it. Returns
    whether a file was found and loaded.
    """
    return load_dotenv(env_path, override=override)

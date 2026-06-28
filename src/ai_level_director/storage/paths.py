"""Filesystem layout for session artifacts.

Every output path is derived here so the rest of the system never hardcodes a
location. The base output directory defaults to ``outputs/`` but is configurable,
which lets tests write to a temporary directory and keeps the real outputs clean.
"""

from __future__ import annotations

from pathlib import Path

DEFAULT_OUTPUT_ROOT = Path("outputs")


def session_path(session_id: str, root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    """Return the path to a session's JSON snapshot."""
    return root / "sessions" / f"{session_id}.json"


def event_log_path(session_id: str, root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    """Return the path to a session's JSONL event log."""
    return root / "logs" / f"{session_id}_events.jsonl"


def candidate_path(session_id: str, candidate_id: str, root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    """Return the path to a candidate's saved level text file."""
    return root / "candidates" / session_id / f"{candidate_id}.txt"


def rendered_preview_path(session_id: str, candidate_id: str, root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    """Return the path to a candidate's rendered preview image."""
    return root / "rendered_levels" / session_id / f"{candidate_id}.png"


def report_path(session_id: str, root: Path = DEFAULT_OUTPUT_ROOT) -> Path:
    """Return the path to a session's Markdown report."""
    return root / "reports" / f"{session_id}_report.md"


def triage_transcript_path(
    session_id: str, candidate_id: str, iteration: int, root: Path = DEFAULT_OUTPUT_ROOT
) -> Path:
    """Return the path to a triage run's full deliberation transcript.

    The iteration number keeps repeated triage runs on the same candidate from
    overwriting each other, so every pass leaves its own auditable transcript.
    """
    return root / "triage_transcripts" / session_id / f"{candidate_id}-r{iteration}.md"


def triage_report_path(
    session_id: str, candidate_id: str, iteration: int, root: Path = DEFAULT_OUTPUT_ROOT
) -> Path:
    """Return the path to a triage run's designer facing report."""
    return root / "triage_reports" / session_id / f"{candidate_id}-r{iteration}.md"

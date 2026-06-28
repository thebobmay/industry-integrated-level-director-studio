"""JSON session persistence and the append only JSONL event log.

The session JSON is the current state of the workspace. The JSONL log is the
historical audit trail, one event per line, appended and never rewritten. They
serve different purposes and are stored separately, which is the core of the
system's transparency. Persistence uses local files rather than a database for
simplicity and reviewer friendly reproducibility.
"""

from __future__ import annotations

from pathlib import Path

from ai_level_director.domain.events import CandidateEvent
from ai_level_director.domain.models import DesignSession
from ai_level_director.storage import paths


class SessionStore:
    """Saves and loads design sessions and appends candidate events.

    The output root is configurable so tests can persist to a temporary directory
    without touching the real ``outputs/`` tree.
    """

    def __init__(self, output_root: Path | str = paths.DEFAULT_OUTPUT_ROOT) -> None:
        """Create a store rooted at the given output directory."""
        self.output_root = Path(output_root)

    def save_session(self, session: DesignSession) -> Path:
        """Write the session snapshot as formatted JSON and return its path."""
        target = paths.session_path(session.session_id, self.output_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(session.model_dump_json(indent=2), encoding="utf-8")
        return target

    def load_session(self, session_id: str) -> DesignSession:
        """Load and validate a session snapshot from disk."""
        target = paths.session_path(session_id, self.output_root)
        return DesignSession.model_validate_json(target.read_text(encoding="utf-8"))

    def session_exists(self, session_id: str) -> bool:
        """Return whether a saved snapshot exists for the session id."""
        return paths.session_path(session_id, self.output_root).exists()

    def list_sessions(self) -> list[str]:
        """Return the ids of all saved sessions, newest modified first.

        Reads the sessions directory rather than a database. Returns an empty list
        if no sessions have been saved yet.
        """
        sessions_dir = paths.session_path("_", self.output_root).parent
        if not sessions_dir.exists():
            return []
        files = sorted(
            sessions_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True
        )
        return [p.stem for p in files]

    def append_event(self, session_id: str, event: CandidateEvent) -> Path:
        """Append one event to the session's JSONL event log and return its path."""
        target = paths.event_log_path(session_id, self.output_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("a", encoding="utf-8") as handle:
            handle.write(event.model_dump_json() + "\n")
        return target

    def read_events(self, session_id: str) -> list[CandidateEvent]:
        """Read all events for a session from its JSONL log, in order.

        Returns an empty list if no log exists yet. Blank lines are skipped so a
        trailing newline does not produce a spurious entry.
        """
        target = paths.event_log_path(session_id, self.output_root)
        if not target.exists():
            return []
        events: list[CandidateEvent] = []
        for line in target.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped:
                events.append(CandidateEvent.model_validate_json(stripped))
        return events

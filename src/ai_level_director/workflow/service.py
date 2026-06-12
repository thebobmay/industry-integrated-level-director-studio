"""The LevelDirectorService facade.

This is the single backend entry point the notebook and the Gradio UI call. It
follows a command style: each operation loads the session from the store, performs
one change, saves the updated session, and returns it. Keeping all callers behind
this facade is what keeps the UI and notebook from touching prior project
internals or persistence details directly.

This module covers the session lifecycle and candidate management. The triage,
playtest, and feedback commands are added once the adapter interface is in place.
"""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from ai_level_director.domain.models import DesignSession, LevelCandidate
from ai_level_director.storage import paths
from ai_level_director.storage.session_store import SessionStore
from ai_level_director.workflow.candidate_sources import (
    make_sample_candidate,
    make_uploaded_candidate,
    next_candidate_id,
    save_candidate_artifacts,
    utc_now_iso,
)


def _new_session_id() -> str:
    """Generate a short, unique session id."""
    return f"session-{uuid4().hex[:8]}"


class LevelDirectorService:
    """Facade over the session store and candidate operations.

    The output root is configurable so tests run against a temporary directory.
    """

    def __init__(self, output_root: Path | str = paths.DEFAULT_OUTPUT_ROOT) -> None:
        """Create the service rooted at the given output directory."""
        self.output_root = Path(output_root)
        self.store = SessionStore(self.output_root)

    def start_session(
        self,
        design_brief: str,
        target_difficulty: str | None = None,
        novelty_preference: str | None = None,
        session_id: str | None = None,
    ) -> DesignSession:
        """Create a new design session, persist it, and return it."""
        now = utc_now_iso()
        session = DesignSession(
            session_id=session_id or _new_session_id(),
            design_brief=design_brief,
            target_difficulty=target_difficulty,
            novelty_preference=novelty_preference,
            created_at=now,
            updated_at=now,
        )
        self.store.save_session(session)
        return session

    def load_session(self, session_id: str) -> DesignSession:
        """Load a session snapshot from the store."""
        return self.store.load_session(session_id)

    def save_session(self, session: DesignSession) -> Path:
        """Persist a session snapshot to the store."""
        return self.store.save_session(session)

    def add_uploaded_candidate(
        self, session_id: str, level_text: str, title: str | None = None
    ) -> DesignSession:
        """Add a designer uploaded candidate to the session and return it."""
        session = self.load_session(session_id)
        candidate_id = next_candidate_id(
            [c.candidate_id for c in session.candidates], "uploaded"
        )
        candidate = make_uploaded_candidate(level_text, candidate_id, title)
        return self._attach_candidate(session, candidate)

    def add_sample_candidate(
        self, session_id: str, level_text: str, title: str | None = None
    ) -> DesignSession:
        """Add a bundled sample candidate to the session and return it."""
        session = self.load_session(session_id)
        candidate_id = next_candidate_id(
            [c.candidate_id for c in session.candidates], "sample"
        )
        candidate = make_sample_candidate(level_text, candidate_id, title)
        return self._attach_candidate(session, candidate)

    def _attach_candidate(
        self, session: DesignSession, candidate: LevelCandidate
    ) -> DesignSession:
        """Save a candidate's artifacts, add it to the session, log, and persist."""
        candidate = save_candidate_artifacts(candidate, session.session_id, self.output_root)
        session.candidates.append(candidate)
        session.updated_at = utc_now_iso()
        self.store.save_session(session)
        for event in candidate.history:
            self.store.append_event(session.session_id, event)
        return session

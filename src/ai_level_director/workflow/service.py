"""The LevelDirectorService facade.

This is the single backend entry point the notebook and the Gradio UI call. It
follows a command style: each operation loads the session from the store, performs
one change, saves the updated session, and returns it. Keeping all callers behind
this facade is what keeps the UI and notebook from touching prior project
internals or persistence details directly.

Triage and feedback are delegated to injected adapters that satisfy the interfaces
in ``adapters.interfaces``. The service depends on those interfaces, not concrete
adapters, so mock adapters and the real prior project adapters are interchangeable.
"""

from __future__ import annotations

import re
from pathlib import Path
from uuid import uuid4

from ai_level_director.adapters.interfaces import (
    FeedbackAdapter,
    GeneratorAdapter,
    TriageAdapter,
)
from ai_level_director.domain.events import CandidateEvent
from ai_level_director.domain.models import (
    DesignSession,
    LevelCandidate,
    PlaytestRecord,
    TriageResult,
)
from ai_level_director.storage import paths
from ai_level_director.storage.session_store import SessionStore
from ai_level_director.reporting.report_builder import build_session_report
from ai_level_director.workflow.candidate_sources import (
    make_generated_candidate,
    make_revised_candidate,
    make_sample_candidate,
    make_uploaded_candidate,
    next_candidate_id,
    save_candidate_artifacts,
    utc_now_iso,
)
from ai_level_director.workflow.transitions import (
    InvalidTransitionError,
    ensure_transition,
    state_for_feedback,
    state_for_triage_action,
)

# Designer override actions (mark complete, archive) may act from any non terminal
# state, since they are explicit human decisions rather than automated lifecycle
# steps. These are the terminal states they cannot act on.
_TERMINAL_STATES = {"complete", "archived", "structural_rejected"}

# Project 3's analysis found the classifier is markedly less reliable on short reviews:
# it misreads roughly 30% of short negative reviews as positive. Following that paper's
# own recommendation, feedback below this length is flagged so the designer scrutinizes
# the text rather than trusting the label. Short is 3 to 24 words; long is 25 or more.
SHORT_REVIEW_WORD_COUNT = 25


def _new_session_id() -> str:
    """Generate a short, unique session id."""
    return f"session-{uuid4().hex[:8]}"


def _slugify(text: str) -> str:
    """Turn a session name into a filesystem and url safe id stem."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "session"


class LevelDirectorService:
    """Facade over the session store, candidate operations, and adapters.

    The output root is configurable so tests run against a temporary directory.
    Triage and feedback adapters are injected; they default to ``None`` and the
    corresponding commands raise if their adapter is missing.
    """

    def __init__(
        self,
        output_root: Path | str = paths.DEFAULT_OUTPUT_ROOT,
        triage_adapter: TriageAdapter | None = None,
        feedback_adapter: FeedbackAdapter | None = None,
        generator_adapter: GeneratorAdapter | None = None,
    ) -> None:
        """Create the service rooted at the given output directory."""
        self.output_root = Path(output_root)
        self.store = SessionStore(self.output_root)
        self.triage_adapter = triage_adapter
        self.feedback_adapter = feedback_adapter
        self.generator_adapter = generator_adapter

    # Session lifecycle ----------------------------------------------------

    def start_session(
        self,
        design_brief: str,
        target_difficulty: str | None = None,
        novelty_preference: str | None = None,
        session_id: str | None = None,
        session_name: str | None = None,
    ) -> DesignSession:
        """Create a new design session, persist it, and return it.

        When a name is given and no explicit id, the id is a unique slug of the
        name so files and the load list read clearly. The display name is stored
        and falls back to the id when unnamed.
        """
        name = session_name.strip() if session_name and session_name.strip() else None
        if session_id is None:
            session_id = self._unique_session_id(_slugify(name)) if name else _new_session_id()
        now = utc_now_iso()
        session = DesignSession(
            session_id=session_id,
            session_name=name or session_id,
            design_brief=design_brief,
            target_difficulty=target_difficulty,
            novelty_preference=novelty_preference,
            created_at=now,
            updated_at=now,
        )
        self.store.save_session(session)
        return session

    def _unique_session_id(self, base: str) -> str:
        """Return base, or base-2, base-3, ... so a named session never overwrites one."""
        candidate = base
        suffix = 2
        while self.store.session_exists(candidate):
            candidate = f"{base}-{suffix}"
            suffix += 1
        return candidate

    def update_session_brief(
        self,
        session_id: str,
        design_brief: str,
        target_difficulty: str | None = None,
        novelty_preference: str | None = None,
    ) -> DesignSession:
        """Update the session's brief and targets, persist, and log the change.

        The brief is fixed when a session starts, so this is how a designer responds
        to a clarification request: refine the intent, then re-triage a candidate
        against it. Existing candidates and their history are untouched.
        """
        session = self.load_session(session_id)
        session.design_brief = design_brief
        session.target_difficulty = target_difficulty
        session.novelty_preference = novelty_preference
        session.updated_at = utc_now_iso()
        event = CandidateEvent(
            event_id=f"{session_id}-brief-{utc_now_iso()}",
            timestamp=utc_now_iso(),
            event_type="brief_updated",
            candidate_id=None,
            summary="Design brief updated.",
        )
        self._persist(session, event)
        return session

    def load_session(self, session_id: str) -> DesignSession:
        """Load a session snapshot from the store."""
        return self.store.load_session(session_id)

    def save_session(self, session: DesignSession) -> Path:
        """Persist a session snapshot to the store."""
        return self.store.save_session(session)

    # Candidate management -------------------------------------------------

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

    def add_generated_candidate(
        self,
        session_id: str,
        target_difficulty: str | None = None,
        n: int = 1,
        temperature: float = 1.2,
        seed: int | None = None,
    ) -> DesignSession:
        """Generate n candidates with the generator adapter and add them.

        The difficulty defaults to the session's target difficulty, then to
        medium. Generation provenance is recorded on each candidate so reports can
        disclose that the content is a generated draft.
        """
        if self.generator_adapter is None:
            raise RuntimeError("No generator adapter configured.")
        session = self.load_session(session_id)
        difficulty = target_difficulty or session.target_difficulty or "medium"
        level_texts = self.generator_adapter.generate(
            difficulty, n=n, temperature=temperature, seed=seed
        )
        for level_text in level_texts:
            candidate_id = next_candidate_id(
                [c.candidate_id for c in session.candidates], "generated"
            )
            metadata = {
                "source_project": "Project 5",
                "target_difficulty": difficulty,
                "temperature": temperature,
                "seed": seed,
            }
            candidate = make_generated_candidate(
                level_text, candidate_id, generation_metadata=metadata
            )
            self._attach_candidate(session, candidate)
        return session

    # Workflow commands ----------------------------------------------------

    def run_triage(self, session_id: str, candidate_id: str) -> DesignSession:
        """Triage a candidate through the triage adapter and update its state."""
        if self.triage_adapter is None:
            raise RuntimeError("No triage adapter configured.")
        session = self.load_session(session_id)
        candidate = self._get_candidate(session, candidate_id)

        result = self.triage_adapter.triage(
            design_brief=session.design_brief,
            level_text=candidate.level_text,
            target_difficulty=session.target_difficulty,
            novelty_preference=session.novelty_preference,
        )
        new_state = state_for_triage_action(result.action)
        ensure_transition(candidate.workflow_state, new_state)

        self._save_triage_artifacts(session.session_id, candidate, result)
        candidate.triage_result = result

        payload = {"action": result.action, "readiness": result.readiness}
        if result.transcript_path:
            payload["transcript_path"] = result.transcript_path
        if result.report_path:
            payload["report_path"] = result.report_path
        event = self._record_state_change(
            session,
            candidate,
            new_state,
            event_type="triaged",
            summary=f"Triaged: {result.action} -> {new_state}.",
            payload=payload,
        )
        self._persist(session, event)
        return session

    def send_to_playtest(self, session_id: str, candidate_id: str) -> DesignSession:
        """Send a ready candidate to the playtester view."""
        session = self.load_session(session_id)
        candidate = self._get_candidate(session, candidate_id)
        ensure_transition(candidate.workflow_state, "sent_to_playtest")
        event = self._record_state_change(
            session,
            candidate,
            "sent_to_playtest",
            event_type="sent_to_playtest",
            summary=f"Candidate {candidate_id} sent to playtest.",
        )
        self._persist(session, event)
        return session

    def submit_feedback(
        self, session_id: str, candidate_id: str, feedback_text: str
    ) -> DesignSession:
        """Submit playtester feedback, classify it, and update candidate state.

        Empty or blank feedback cannot be classified, so it routes to human review
        as an input check rather than through the classifier.
        """
        if self.feedback_adapter is None:
            raise RuntimeError("No feedback adapter configured.")
        session = self.load_session(session_id)
        candidate = self._get_candidate(session, candidate_id)
        ensure_transition(candidate.workflow_state, "feedback_received")
        candidate.workflow_state = "feedback_received"

        if not feedback_text.strip():
            new_state = "human_review_needed"
            summary = f"Empty feedback for {candidate_id}; routed to human review."
            payload = {"classified": False}
        else:
            feedback_result = self.feedback_adapter.classify(feedback_text)
            new_state = state_for_feedback(feedback_result.sentiment)
            word_count = len(feedback_text.split())
            warning = None
            if word_count < SHORT_REVIEW_WORD_COUNT:
                warning = (
                    f"Short feedback ({word_count} words). The classifier is less reliable "
                    f"on short reviews and can misread short negative feedback as positive, "
                    f"so review the text before trusting this label."
                )
            record = PlaytestRecord(
                playtest_id=f"{candidate_id}-pt-{len(candidate.feedback_records) + 1}",
                candidate_id=candidate_id,
                submitted_at=utc_now_iso(),
                feedback_text=feedback_text,
                feedback_result=feedback_result,
                status_after_feedback=new_state,
                warning=warning,
            )
            candidate.feedback_records.append(record)
            summary = f"Feedback classified {feedback_result.sentiment} -> {new_state}."
            payload = {"classified": True, "sentiment": feedback_result.sentiment}
            if warning:
                summary += " Short review, flagged for designer review."
                payload["short_review"] = True

        ensure_transition("feedback_received", new_state)
        event = self._record_state_change(
            session, candidate, new_state, event_type="feedback_submitted",
            summary=summary, payload=payload,
        )
        self._persist(session, event)
        return session

    def mark_complete(self, session_id: str, candidate_id: str) -> DesignSession:
        """Mark a candidate complete. A designer override, allowed unless terminal."""
        session = self.load_session(session_id)
        candidate = self._get_candidate(session, candidate_id)
        if candidate.workflow_state in _TERMINAL_STATES:
            raise InvalidTransitionError(
                f"Cannot complete a candidate already in '{candidate.workflow_state}'."
            )
        event = self._record_state_change(
            session, candidate, "complete", event_type="completed",
            summary=f"Candidate {candidate_id} marked complete (designer override).",
        )
        self._persist(session, event)
        return session

    def archive_candidate(self, session_id: str, candidate_id: str) -> DesignSession:
        """Archive a candidate the designer is setting aside. A designer override."""
        session = self.load_session(session_id)
        candidate = self._get_candidate(session, candidate_id)
        if candidate.workflow_state == "archived":
            raise InvalidTransitionError("Candidate is already archived.")
        event = self._record_state_change(
            session, candidate, "archived", event_type="archived",
            summary=f"Candidate {candidate_id} archived.",
        )
        self._persist(session, event)
        return session

    def override_feedback(
        self, session_id: str, candidate_id: str, corrected_sentiment: str
    ) -> DesignSession:
        """Let the designer override the classifier's feedback sentiment.

        The classifier is advisory, so after reading the playtester text the designer
        can correct its call. The classifier's original label is preserved on the
        record for the audit trail; the correction is recorded as its own event and
        moves the candidate to the state matching the corrected sentiment. This is a
        designer override and bypasses the automated transition guard, like
        mark_complete and archive.
        """
        if corrected_sentiment not in ("positive", "negative"):
            raise ValueError(f"Invalid sentiment: '{corrected_sentiment}'.")
        session = self.load_session(session_id)
        candidate = self._get_candidate(session, candidate_id)
        if not candidate.feedback_records:
            raise InvalidTransitionError(
                "Cannot override feedback before any feedback has been classified."
            )
        record = candidate.feedback_records[-1]
        record.designer_override = corrected_sentiment
        new_state = state_for_feedback(corrected_sentiment)
        event = self._record_state_change(
            session,
            candidate,
            new_state,
            event_type="feedback_overridden",
            summary=(
                f"Designer overrode feedback from {record.feedback_result.sentiment} "
                f"to {corrected_sentiment} -> {new_state}."
            ),
            payload={
                "classifier_sentiment": record.feedback_result.sentiment,
                "designer_sentiment": corrected_sentiment,
            },
        )
        self._persist(session, event)
        return session

    def create_revised_candidate(
        self,
        session_id: str,
        parent_candidate_id: str,
        revised_level_text: str,
        notes: str = "",
    ) -> DesignSession:
        """Create a new revised candidate linked to its parent and add it.

        The revision is a new draft candidate carrying the parent id and an
        incremented iteration number, so the iteration history is preserved rather
        than overwriting the original.
        """
        session = self.load_session(session_id)
        parent = self._get_candidate(session, parent_candidate_id)
        candidate_id = next_candidate_id(
            [c.candidate_id for c in session.candidates], "revised"
        )
        candidate = make_revised_candidate(
            revised_level_text,
            candidate_id,
            parent_candidate_id=parent_candidate_id,
            iteration_number=parent.iteration_number + 1,
        )
        if notes:
            session.session_notes.append(f"{candidate_id}: {notes}")
        return self._attach_candidate(session, candidate)

    def build_session_report(self, session_id: str) -> Path:
        """Generate the Markdown session report, save it, and return its path."""
        session = self.load_session(session_id)
        report = build_session_report(session)
        target = paths.report_path(session_id, self.output_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report, encoding="utf-8")
        event = CandidateEvent(
            event_id=f"{session_id}-report-{utc_now_iso()}",
            timestamp=utc_now_iso(),
            event_type="report_generated",
            candidate_id=None,
            summary=f"Session report generated at {target}.",
        )
        self.store.append_event(session_id, event)
        return target

    # Internal helpers -----------------------------------------------------

    def _save_triage_artifacts(
        self, session_id: str, candidate: LevelCandidate, result: TriageResult
    ) -> None:
        """Persist the triage transcript and report, recording their paths on the result.

        The agent's full deliberation is written to its own file so any triage
        recommendation can be audited later. The iteration number is the count of
        prior triage runs on this candidate plus one, so repeated runs each leave a
        separate transcript instead of overwriting one another.
        """
        iteration = sum(1 for e in candidate.history if e.event_type == "triaged") + 1
        if result.transcript_text:
            target = paths.triage_transcript_path(
                session_id, candidate.candidate_id, iteration, self.output_root
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(result.transcript_text, encoding="utf-8")
            result.transcript_path = str(target)
        if result.report_text:
            target = paths.triage_report_path(
                session_id, candidate.candidate_id, iteration, self.output_root
            )
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(result.report_text, encoding="utf-8")
            result.report_path = str(target)

    def _get_candidate(self, session: DesignSession, candidate_id: str) -> LevelCandidate:
        """Return the named candidate or raise if it is not in the session."""
        for candidate in session.candidates:
            if candidate.candidate_id == candidate_id:
                return candidate
        raise KeyError(f"No candidate '{candidate_id}' in session '{session.session_id}'.")

    def _record_state_change(
        self,
        session: DesignSession,
        candidate: LevelCandidate,
        new_state: str,
        event_type: str,
        summary: str,
        payload: dict | None = None,
    ) -> CandidateEvent:
        """Apply a state change to a candidate and append a history event to it."""
        now = utc_now_iso()
        candidate.workflow_state = new_state
        candidate.updated_at = now
        event = CandidateEvent(
            event_id=f"{candidate.candidate_id}-evt-{len(candidate.history) + 1}",
            timestamp=now,
            event_type=event_type,
            candidate_id=candidate.candidate_id,
            summary=summary,
            payload=payload or {},
        )
        candidate.history.append(event)
        session.updated_at = now
        return event

    def _persist(self, session: DesignSession, event: CandidateEvent) -> None:
        """Save the session snapshot and append one event to the log."""
        self.store.save_session(session)
        self.store.append_event(session.session_id, event)

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

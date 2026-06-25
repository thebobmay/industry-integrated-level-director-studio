"""UI callbacks.

Each callback takes the LevelDirectorService explicitly, performs one command, and
returns plain view models and a status string. They import no Gradio, so they run
and test outside the event loop; ``app.py`` wraps them and binds them to
components. Service errors (for example an invalid transition) are caught and
returned as a status message rather than raised, so the UI stays responsive.
"""

from __future__ import annotations

from pathlib import Path

from ai_level_director.domain.models import DesignSession
from ai_level_director.storage import paths
from ai_level_director.ui.view_models import (
    candidate_board_view,
    candidate_detail_view,
    candidate_ids,
    event_timeline_markdown,
    playtest_queue_view,
    session_summary_view,
)
from ai_level_director.workflow.service import LevelDirectorService

_SAMPLE_DIR = Path(__file__).resolve().parents[3] / "data" / "sample_levels"


def list_sample_levels() -> list[str]:
    """List the names (without extension) of the bundled sample levels."""
    return [p.stem for p in sorted(_SAMPLE_DIR.glob("*.txt"))]


def _sample_text(name: str) -> str:
    """Read a bundled sample level's tile text by name."""
    return (_SAMPLE_DIR / f"{name}.txt").read_text(encoding="utf-8")


def _views(service: LevelDirectorService, session_id: str):
    """Return the standard refresh bundle: board, candidate ids, playtest queue."""
    session = service.load_session(session_id)
    return candidate_board_view(session), candidate_ids(session), playtest_queue_view(session)


def start_session(
    service: LevelDirectorService,
    brief: str,
    target_difficulty: str,
    novelty_preference: str,
    session_name: str = "",
):
    """Create a session and return its id with the initial views."""
    difficulty = None if target_difficulty in ("", "unspecified") else target_difficulty
    novelty = None if novelty_preference in ("", "unspecified") else novelty_preference
    if not (brief or "").strip():
        return None, candidate_board_view_empty(), [], playtest_queue_view_empty(), "Enter a design brief first."
    session = service.start_session(brief, difficulty, novelty, session_name=session_name or None)
    board, ids, queue = _views(service, session.session_id)
    return session.session_id, board, ids, queue, f"Started session '{session.session_name}'."


_EMPTY_SESSION = DesignSession(session_id="", design_brief="", created_at="", updated_at="")


def list_saved_sessions(service: LevelDirectorService) -> list[str]:
    """Return the ids of saved sessions, newest first, for the load control."""
    return service.store.list_sessions()


def list_saved_session_choices(service: LevelDirectorService) -> list[tuple[str, str]]:
    """Return (label, id) pairs for the load dropdown, labeled by friendly name.

    The label shows the session name, with the id appended when they differ, so a
    named session reads clearly while still loading by its stable id.
    """
    choices: list[tuple[str, str]] = []
    for sid in service.store.list_sessions():
        try:
            name = service.load_session(sid).session_name or sid
        except Exception:
            name = sid
        label = sid if name == sid else f"{name} ({sid})"
        choices.append((label, sid))
    return choices


def load_existing_session(service: LevelDirectorService, session_id: str):
    """Load a saved session and return its id with the initial views."""
    if not session_id:
        return None, candidate_board_view_empty(), [], playtest_queue_view_empty(), "Pick a session to load."
    if not service.store.session_exists(session_id):
        return None, candidate_board_view_empty(), [], playtest_queue_view_empty(), f"Session {session_id} not found."
    board, ids, queue = _views(service, session_id)
    return session_id, board, ids, queue, f"Loaded session {session_id}."


def cancel_session():
    """Clear the workspace back to no active session."""
    return None, candidate_board_view_empty(), [], playtest_queue_view_empty(), "Session cleared. Start or load a session."


def update_brief(
    service: LevelDirectorService, session_id: str, brief: str, target_difficulty: str, novelty_preference: str
):
    """Update the session brief and targets, then return refreshed views."""
    if not session_id:
        return candidate_board_view_empty(), [], playtest_queue_view_empty(), "Start or load a session first."
    if not (brief or "").strip():
        board, ids, queue = _views(service, session_id)
        return board, ids, queue, "Enter a brief before updating."
    difficulty = None if target_difficulty in ("", "unspecified") else target_difficulty
    novelty = None if novelty_preference in ("", "unspecified") else novelty_preference
    return _action(
        service, session_id,
        lambda: service.update_session_brief(session_id, brief, difficulty, novelty),
        "Brief updated. Re-triage a candidate to re-evaluate it against the new brief.",
    )


def candidate_board_view_empty():
    """An empty candidate board (used before a session exists)."""
    return candidate_board_view(_EMPTY_SESSION)


def playtest_queue_view_empty():
    """An empty playtest queue."""
    return playtest_queue_view(_EMPTY_SESSION)


def _action(service, session_id, fn, success):
    """Run a state changing service command and return the refreshed views."""
    if not session_id:
        board, ids, queue = _views_safe(service, session_id)
        return board, ids, queue, "Start or load a session first."
    try:
        fn()
        status = success
    except Exception as exc:  # surfaced to the UI, never crashes the app
        status = f"Error: {exc}"
    board, ids, queue = _views(service, session_id)
    return board, ids, queue, status


def _views_safe(service, session_id):
    """Views that tolerate a missing session id."""
    if not session_id:
        return candidate_board_view_empty(), [], playtest_queue_view_empty()
    return _views(service, session_id)


def upload_candidate(service, session_id, level_text, title):
    """Add an uploaded candidate from pasted tile text."""
    return _action(
        service, session_id,
        lambda: service.add_uploaded_candidate(session_id, level_text, title or None),
        "Uploaded candidate added.",
    )


def upload_candidate_file(service, session_id, file_path, title):
    """Add an uploaded candidate by reading a tile grid text file from disk."""
    if not file_path:
        board, ids, queue = _views_safe(service, session_id)
        return board, ids, queue, "Choose a tile grid (.txt) file first."
    try:
        level_text = Path(file_path).read_text(encoding="utf-8")
    except OSError as exc:
        board, ids, queue = _views_safe(service, session_id)
        return board, ids, queue, f"Could not read file: {exc}"
    chosen_title = title or Path(file_path).stem
    return _action(
        service, session_id,
        lambda: service.add_uploaded_candidate(session_id, level_text, chosen_title),
        f"Uploaded candidate from {Path(file_path).name}.",
    )


def load_sample(service, session_id, sample_name):
    """Add a bundled sample candidate."""
    return _action(
        service, session_id,
        lambda: service.add_sample_candidate(session_id, _sample_text(sample_name), sample_name),
        f"Sample '{sample_name}' added.",
    )


def generate_candidates(service, session_id, n, temperature, seed):
    """Generate candidates with the configured generator adapter."""
    seed_val = int(seed) if seed not in (None, "") else None
    return _action(
        service, session_id,
        lambda: service.add_generated_candidate(
            session_id, n=int(n), temperature=float(temperature), seed=seed_val
        ),
        f"Generated {int(n)} candidate(s).",
    )


def run_triage(service, session_id, candidate_id):
    """Triage a selected candidate."""
    return _action(
        service, session_id,
        lambda: service.run_triage(session_id, candidate_id),
        f"Triaged {candidate_id}.",
    )


def run_triage_all_drafts(service, session_id):
    """Triage every candidate currently in the draft state."""
    def do():
        session = service.load_session(session_id)
        for c in [c for c in session.candidates if c.workflow_state == "draft"]:
            service.run_triage(session_id, c.candidate_id)

    return _action(service, session_id, do, "Triaged all draft candidates.")


def send_to_playtest(service, session_id, candidate_id):
    """Send a ready candidate to the playtester view."""
    return _action(
        service, session_id,
        lambda: service.send_to_playtest(session_id, candidate_id),
        f"Sent {candidate_id} to playtest.",
    )


def submit_feedback(service, session_id, candidate_id, feedback_text):
    """Submit playtester feedback for a candidate."""
    return _action(
        service, session_id,
        lambda: service.submit_feedback(session_id, candidate_id, feedback_text),
        f"Feedback submitted for {candidate_id}.",
    )


def override_feedback(service, session_id, candidate_id, corrected_sentiment):
    """Designer override of the classifier's feedback sentiment after reading the text."""
    return _action(
        service, session_id,
        lambda: service.override_feedback(session_id, candidate_id, corrected_sentiment),
        f"Feedback for {candidate_id} set to {corrected_sentiment} by designer.",
    )


def mark_complete(service, session_id, candidate_id):
    """Mark a candidate complete."""
    return _action(
        service, session_id,
        lambda: service.mark_complete(session_id, candidate_id),
        f"Marked {candidate_id} complete.",
    )


def archive_candidate(service, session_id, candidate_id):
    """Archive a candidate."""
    return _action(
        service, session_id,
        lambda: service.archive_candidate(session_id, candidate_id),
        f"Archived {candidate_id}.",
    )


def create_revised_candidate(service, session_id, parent_candidate_id, revised_text, notes):
    """Create a revised candidate from a parent."""
    return _action(
        service, session_id,
        lambda: service.create_revised_candidate(
            session_id, parent_candidate_id, revised_text, notes or ""
        ),
        f"Created a revision of {parent_candidate_id}.",
    )


def candidate_detail(service, session_id, candidate_id) -> dict:
    """Return the detail panel blocks for a candidate."""
    if not session_id:
        return candidate_detail_view(_EMPTY_SESSION, None)
    session = service.load_session(session_id)
    return candidate_detail_view(session, candidate_id)


def _read_artifact(path: str | None) -> str:
    """Read a saved text artifact for display, returning '' if it is missing."""
    if not path:
        return ""
    target = Path(path)
    return target.read_text(encoding="utf-8") if target.is_file() else ""


def triage_artifacts(service, session_id, candidate_id) -> dict:
    """Return the saved triage report and deliberation transcript for a candidate.

    Reads the artifacts the triage run persisted so the Candidate Detail view can
    display them and offer them for download. Paths are returned only when the file
    exists, and texts are empty when a candidate has not been triaged. This is how a
    reviewer inspects the reasoning behind a triage recommendation.
    """
    empty = {"report_text": "", "report_path": None, "transcript_text": "", "transcript_path": None}
    if not session_id or not candidate_id:
        return empty
    session = service.load_session(session_id)
    candidate = next((c for c in session.candidates if c.candidate_id == candidate_id), None)
    if candidate is None or candidate.triage_result is None:
        return empty
    result = candidate.triage_result
    return {
        "report_text": _read_artifact(result.report_path),
        "report_path": result.report_path if _read_artifact(result.report_path) else None,
        "transcript_text": _read_artifact(result.transcript_path),
        "transcript_path": result.transcript_path if _read_artifact(result.transcript_path) else None,
    }


def build_report(service, session_id):
    """Generate the session report and return its text and downloadable paths."""
    if not session_id:
        return "", None, None, "Start or load a session first."
    path = service.build_session_report(session_id)
    session = service.load_session(session_id)
    report_text = path.read_text(encoding="utf-8")
    timeline = event_timeline_markdown(service.store.read_events(session_id))
    session_json = str(paths.session_path(session_id, service.output_root))
    return report_text, str(path), session_json, timeline, f"Report written to {path}."


def session_summary(service, session_id) -> str:
    """Return a Markdown summary of the current session."""
    if not session_id:
        return "_No session._"
    return session_summary_view(service.load_session(session_id))

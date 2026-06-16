"""End to end workflow tests against mock adapters.

These run the full loop without any prior project: create a session, add a
candidate, triage it, send it to playtest, and submit feedback. Because the
adapters are deterministic mocks, the assertions are about the orchestration and
state machine, not model behavior.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ai_level_director.adapters.mocks import MockFeedbackAdapter, MockTriageAdapter
from ai_level_director.workflow.service import LevelDirectorService
from ai_level_director.workflow.transitions import InvalidTransitionError

LEVEL = "----\nXXXX"


def make_service(tmp_path, action="accept_for_playtest") -> LevelDirectorService:
    """Build a service wired with mock triage and feedback adapters."""
    return LevelDirectorService(
        output_root=tmp_path,
        triage_adapter=MockTriageAdapter(action=action),
        feedback_adapter=MockFeedbackAdapter(),
    )


def seeded_session(service, session_id="S1"):
    """Start a session and add one uploaded candidate, returning its id."""
    service.start_session("An easy beginner segment.", session_id=session_id)
    service.add_uploaded_candidate(session_id, LEVEL)
    return session_id


def test_mock_feedback_keyword_classification():
    adapter = MockFeedbackAdapter()
    assert adapter.classify("This was fun and fair.").sentiment == "positive"
    assert adapter.classify("The first jump felt unfair.").sentiment == "negative"


def test_run_triage_requires_adapter(tmp_path):
    service = LevelDirectorService(output_root=tmp_path)  # no adapters
    seeded_session(service)
    with pytest.raises(RuntimeError):
        service.run_triage("S1", "U-001")


@pytest.mark.parametrize(
    "action,expected_state",
    [
        ("accept_for_playtest", "ready_for_playtest"),
        ("recommend_revision", "revision_needed"),
        ("request_clarification", "clarification_needed"),
        ("reject_structural", "structural_rejected"),
        ("flag_as_derivative_draft", "derivative_review_needed"),
        ("request_human_review", "human_review_needed"),
    ],
)
def test_triage_maps_action_to_state(tmp_path, action, expected_state):
    service = make_service(tmp_path, action=action)
    seeded_session(service)
    session = service.run_triage("S1", "U-001")
    candidate = session.candidates[0]
    assert candidate.workflow_state == expected_state
    assert candidate.triage_result is not None
    assert candidate.triage_result.action == action


def test_send_to_playtest_requires_ready_state(tmp_path):
    # A freshly added draft candidate cannot be sent to playtest.
    service = make_service(tmp_path)
    seeded_session(service)
    with pytest.raises(InvalidTransitionError):
        service.send_to_playtest("S1", "U-001")


def test_positive_feedback_completes_candidate(tmp_path):
    service = make_service(tmp_path, action="accept_for_playtest")
    seeded_session(service)
    service.run_triage("S1", "U-001")
    service.send_to_playtest("S1", "U-001")
    session = service.submit_feedback("S1", "U-001", "This was fun and fair.")

    candidate = session.candidates[0]
    assert candidate.workflow_state == "complete"
    assert len(candidate.feedback_records) == 1
    assert candidate.feedback_records[0].feedback_result.sentiment == "positive"


def test_negative_feedback_needs_revision(tmp_path):
    service = make_service(tmp_path, action="accept_for_playtest")
    seeded_session(service)
    service.run_triage("S1", "U-001")
    service.send_to_playtest("S1", "U-001")
    session = service.submit_feedback("S1", "U-001", "The first jump felt unfair.")

    candidate = session.candidates[0]
    assert candidate.workflow_state == "revision_needed"
    assert candidate.feedback_records[0].feedback_result.sentiment == "negative"


def test_empty_feedback_routes_to_human_review(tmp_path):
    service = make_service(tmp_path, action="accept_for_playtest")
    seeded_session(service)
    service.run_triage("S1", "U-001")
    service.send_to_playtest("S1", "U-001")
    session = service.submit_feedback("S1", "U-001", "   ")

    candidate = session.candidates[0]
    assert candidate.workflow_state == "human_review_needed"
    assert candidate.feedback_records == []  # nothing was classified


def test_triage_persists_transcript_and_report(tmp_path):
    service = make_service(tmp_path, action="accept_for_playtest")
    seeded_session(service)
    session = service.run_triage("S1", "U-001")

    result = session.candidates[0].triage_result
    # Paths are recorded and the artifacts exist on disk.
    assert result.transcript_path is not None
    assert result.report_path is not None
    transcript = Path(result.transcript_path)
    report = Path(result.report_path)
    assert transcript.is_file() and transcript.read_text(encoding="utf-8").strip()
    assert report.is_file() and report.read_text(encoding="utf-8").strip()

    # The triaged event indexes the transcript so the audit trail links to it.
    triaged = [e for e in service.store.read_events("S1") if e.event_type == "triaged"][0]
    assert triaged.payload["transcript_path"] == result.transcript_path
    assert triaged.payload["report_path"] == result.report_path

    # The full transcript text is not bloated into the session snapshot; only the
    # path persists, and the saved file is the record.
    reloaded = service.load_session("S1").candidates[0].triage_result
    assert reloaded.transcript_path == result.transcript_path
    assert reloaded.transcript_text is None


def test_repeated_triage_writes_separate_transcripts(tmp_path):
    # A revision returns to draft, so the parent and its revision each triage and
    # must not overwrite each other's transcript.
    service = make_service(tmp_path, action="recommend_revision")
    seeded_session(service)
    service.run_triage("S1", "U-001")  # U-001 -> revision_needed
    service.create_revised_candidate("S1", "U-001", LEVEL)
    session = service.run_triage("S1", "R-001")

    paths_seen = {c.triage_result.transcript_path for c in session.candidates if c.triage_result}
    assert len(paths_seen) == 2  # distinct transcript files


def test_full_happy_path_event_log(tmp_path):
    service = make_service(tmp_path, action="accept_for_playtest")
    seeded_session(service)
    service.run_triage("S1", "U-001")
    service.send_to_playtest("S1", "U-001")
    service.submit_feedback("S1", "U-001", "Great pacing, felt fair.")

    events = [e.event_type for e in service.store.read_events("S1")]
    assert events == ["uploaded", "triaged", "sent_to_playtest", "feedback_submitted"]

    # The final persisted state reflects the whole loop.
    reloaded = service.load_session("S1")
    assert reloaded.candidates[0].workflow_state == "complete"

"""Tests for the UI callbacks, driven with the mock adapter service.

Callbacks take the service explicitly and return plain view models, so they run
outside the Gradio event loop. These confirm the full clickable loop and that
service errors come back as status strings rather than exceptions.
"""

from __future__ import annotations

from ai_level_director.adapters.mocks import (
    MockFeedbackAdapter,
    MockGeneratorAdapter,
    MockTriageAdapter,
)
from ai_level_director.ui import callbacks as cb
from ai_level_director.workflow.service import LevelDirectorService

LEVEL = "----\nXXXX"


def make_service(tmp_path, action="accept_for_playtest") -> LevelDirectorService:
    return LevelDirectorService(
        output_root=tmp_path,
        triage_adapter=MockTriageAdapter(action),
        feedback_adapter=MockFeedbackAdapter(),
        generator_adapter=MockGeneratorAdapter(),
    )


def test_start_session_requires_brief(tmp_path):
    service = make_service(tmp_path)
    session_id, board, ids, queue, status = cb.start_session(service, "  ", "easy", "")
    assert session_id is None
    assert "design brief" in status.lower()


def test_start_and_upload(tmp_path):
    service = make_service(tmp_path)
    session_id, board, ids, queue, status = cb.start_session(service, "brief", "easy", "balanced")
    assert session_id
    board, ids, queue, status = cb.upload_candidate(service, session_id, LEVEL, "My level")
    assert ids == ["U-001"]
    assert board.iloc[0]["candidate_id"] == "U-001"


def test_list_and_load_sample(tmp_path):
    service = make_service(tmp_path)
    samples = cb.list_sample_levels()
    assert "easy_opener" in samples
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    board, ids, queue, status = cb.load_sample(service, sid, "easy_opener")
    assert ids == ["S-001"]
    assert "easy_opener" in status


def test_generate_then_triage(tmp_path):
    service = make_service(tmp_path)
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    cb.generate_candidates(service, sid, n=2, temperature=1.0, seed=1)
    board, ids, queue, status = cb.run_triage(service, sid, "G-001")
    assert "Triaged G-001" in status
    state = board.set_index("candidate_id").loc["G-001", "state"]
    assert state == "ready_for_playtest"


def test_triage_artifacts_returns_saved_files(tmp_path):
    service = make_service(tmp_path)
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    cb.upload_candidate(service, sid, LEVEL, "L")
    cb.run_triage(service, sid, "U-001")

    arts = cb.triage_artifacts(service, sid, "U-001")
    assert arts["transcript_path"] and arts["transcript_text"]
    assert arts["report_path"] and arts["report_text"]


def test_triage_artifacts_empty_before_triage(tmp_path):
    service = make_service(tmp_path)
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    cb.upload_candidate(service, sid, LEVEL, "L")

    arts = cb.triage_artifacts(service, sid, "U-001")
    assert arts["transcript_path"] is None and arts["transcript_text"] == ""
    assert arts["report_path"] is None


def test_full_loop_to_complete(tmp_path):
    service = make_service(tmp_path, action="accept_for_playtest")
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    cb.upload_candidate(service, sid, LEVEL, "L")
    cb.run_triage(service, sid, "U-001")
    board, ids, queue, status = cb.send_to_playtest(service, sid, "U-001")
    assert list(queue["candidate_id"]) == ["U-001"]  # appears in playtest queue
    board, ids, queue, status = cb.submit_feedback(service, sid, "U-001", "Fun and fair!")
    assert board.set_index("candidate_id").loc["U-001", "state"] == "complete"
    assert list(queue["candidate_id"]) == []  # left the queue


def test_invalid_action_returns_status_not_exception(tmp_path):
    service = make_service(tmp_path)
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    cb.upload_candidate(service, sid, LEVEL, "L")
    # Sending a draft straight to playtest is invalid; should surface as status.
    board, ids, queue, status = cb.send_to_playtest(service, sid, "U-001")
    assert status.startswith("Error:")
    assert board.iloc[0]["state"] == "draft"  # unchanged


def test_build_report_callback(tmp_path):
    service = make_service(tmp_path)
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    cb.upload_candidate(service, sid, LEVEL, "L")
    report_text, report_path, session_json, timeline, status = cb.build_report(service, sid)
    assert "Session Report" in report_text
    assert report_path and session_json
    assert "report" in status.lower()


def test_action_without_session(tmp_path):
    service = make_service(tmp_path)
    board, ids, queue, status = cb.run_triage(service, None, "U-001")
    assert "session" in status.lower()

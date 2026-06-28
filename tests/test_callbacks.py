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


def test_list_and_load_saved_session(tmp_path):
    service = make_service(tmp_path)
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    cb.upload_candidate(service, sid, LEVEL, "L")

    assert sid in cb.list_saved_sessions(service)
    loaded_id, board, ids, queue, status = cb.load_existing_session(service, sid)
    assert loaded_id == sid
    assert ids == ["U-001"]
    assert "Loaded" in status


def test_named_session_appears_in_load_choices(tmp_path):
    service = make_service(tmp_path)
    cb.start_session(service, "brief", "easy", "", "My Easy Opener")
    choices = cb.list_saved_session_choices(service)
    labels = [label for label, _id in choices]
    ids = [sid for _label, sid in choices]
    assert "my-easy-opener" in ids
    assert any("My Easy Opener" in label for label in labels)


def test_load_missing_session_reports_error(tmp_path):
    service = make_service(tmp_path)
    loaded_id, board, ids, queue, status = cb.load_existing_session(service, "nope")
    assert loaded_id is None
    assert "not found" in status.lower()


def test_cancel_session_clears_state():
    sid, board, ids, queue, status = cb.cancel_session()
    assert sid is None
    assert ids == []
    assert "cleared" in status.lower()


def test_update_brief_then_retriage(tmp_path):
    service = make_service(tmp_path, action="request_clarification")
    sid, *_ = cb.start_session(service, "vague", "", "")
    cb.upload_candidate(service, sid, LEVEL, "L")
    cb.run_triage(service, sid, "U-001")  # -> clarification_needed

    board, ids, queue, status = cb.update_brief(service, sid, "A clearer brief", "easy", "balanced")
    assert "updated" in status.lower()
    assert service.load_session(sid).design_brief == "A clearer brief"


def test_upload_candidate_file(tmp_path):
    service = make_service(tmp_path)
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    grid = tmp_path / "my_level.txt"
    grid.write_text(LEVEL, encoding="utf-8")

    board, ids, queue, status = cb.upload_candidate_file(service, sid, str(grid), None)
    assert ids == ["U-001"]
    assert "my_level" in status


def test_detail_switches_between_candidates_after_playtest(tmp_path):
    # Regression for the Candidate Detail lock: after a playtest loop bumps state,
    # selecting either candidate must still return that candidate's own detail. The
    # UI selector is rendered independently of the selection so it never locks; this
    # guards the data path it feeds.
    service = make_service(tmp_path)
    sid, *_ = cb.start_session(service, "brief", "easy", "")
    cb.upload_candidate(service, sid, LEVEL, "First")
    cb.upload_candidate(service, sid, LEVEL, "Second")
    cb.run_triage(service, sid, "U-001")
    cb.send_to_playtest(service, sid, "U-001")
    cb.submit_feedback(service, sid, "U-001", "Fun and fair!")

    first = cb.candidate_detail(service, sid, "U-001")
    second = cb.candidate_detail(service, sid, "U-002")
    assert "U-001" in first["metadata_markdown"]
    assert "U-002" in second["metadata_markdown"]
    assert first["metadata_markdown"] != second["metadata_markdown"]


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


def test_build_report_without_session_returns_five_values(tmp_path):
    # The Reports button can fire with no active session; the callback must return the
    # same 5-tuple shape so the UI unpack does not raise.
    service = make_service(tmp_path)
    result = cb.build_report(service, None)
    assert len(result) == 5
    report_text, report_path, session_json, timeline, status = result
    assert report_path is None and session_json is None
    assert "start or load" in status.lower()


def test_action_without_session(tmp_path):
    service = make_service(tmp_path)
    board, ids, queue, status = cb.run_triage(service, None, "U-001")
    assert "session" in status.lower()

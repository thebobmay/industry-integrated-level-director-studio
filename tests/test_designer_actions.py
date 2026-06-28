"""Tests for the designer override service actions.

mark_complete and archive are human authority overrides: allowed from any non
terminal state, blocked once terminal. create_revised_candidate adds a linked
revision without overwriting the parent.
"""

from __future__ import annotations

import pytest

from ai_level_director.adapters.mocks import MockFeedbackAdapter, MockTriageAdapter
from ai_level_director.workflow.service import LevelDirectorService
from ai_level_director.workflow.transitions import InvalidTransitionError

LEVEL = "----\nXXXX"


def make_service(tmp_path) -> LevelDirectorService:
    return LevelDirectorService(
        output_root=tmp_path,
        triage_adapter=MockTriageAdapter("recommend_revision"),
        feedback_adapter=MockFeedbackAdapter(),
    )


def test_mark_complete_from_non_terminal_state(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    service.run_triage("S1", "U-001")  # -> revision_needed
    session = service.mark_complete("S1", "U-001")
    assert session.candidates[0].workflow_state == "complete"


def test_mark_complete_blocked_when_terminal(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    service.run_triage("S1", "U-001")
    service.mark_complete("S1", "U-001")
    with pytest.raises(InvalidTransitionError):
        service.mark_complete("S1", "U-001")  # already complete


def test_archive_candidate(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    session = service.archive_candidate("S1", "U-001")  # from draft
    assert session.candidates[0].workflow_state == "archived"


def test_create_revised_candidate_links_parent(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    service.run_triage("S1", "U-001")  # parent -> revision_needed
    session = service.create_revised_candidate("S1", "U-001", "----\nXX-X", notes="moved enemy")

    revised = session.candidates[-1]
    assert revised.candidate_id == "R-001"
    assert revised.source == "revised"
    assert revised.parent_candidate_id == "U-001"
    assert revised.iteration_number == 2
    assert revised.workflow_state == "draft"
    # The original candidate is untouched (still present).
    assert session.candidates[0].candidate_id == "U-001"
    assert any("moved enemy" in n for n in session.session_notes)

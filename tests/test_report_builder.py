"""Tests for the Markdown session report builder.

The report is pure formatting over session state, so these check that the key
sections, the candidate table, per candidate detail, and the fixed limitations
disclosures all appear, and that the service writes the report to disk.
"""

from __future__ import annotations

from ai_level_director.adapters.mocks import MockFeedbackAdapter, MockTriageAdapter
from ai_level_director.domain.models import DesignSession, LevelCandidate, TriageResult
from ai_level_director.reporting.report_builder import build_session_report
from ai_level_director.workflow.service import LevelDirectorService

TS = "2026-06-12T12:00:00+00:00"
LEVEL = "----\nXXXX"


def _session_with_candidate() -> DesignSession:
    candidate = LevelCandidate(
        candidate_id="U-001",
        title="Opener",
        source="uploaded",
        level_text=LEVEL,
        workflow_state="revision_needed",
        created_at=TS,
        updated_at=TS,
        triage_result=TriageResult(
            action="recommend_revision",
            readiness="revise_before_playtest",
            rationale="An enemy sits on the first landing.",
            warnings=["Localized difficulty spike detected."],
            revision_recommendations=["Move the enemy back two tiles."],
            playtest_questions=["Does the first jump feel fair?"],
        ),
    )
    return DesignSession(
        session_id="S1",
        design_brief="An easy beginner segment.",
        target_difficulty="easy",
        candidates=[candidate],
        created_at=TS,
        updated_at=TS,
    )


def test_report_has_core_sections():
    report = build_session_report(_session_with_candidate())
    assert "# AI Level Director Studio Session Report" in report
    assert "## Session" in report
    assert "## Candidate Summary" in report
    assert "## Candidate Details" in report
    assert "## Limitations and Responsible Use" in report


def test_report_includes_candidate_and_triage_detail():
    report = build_session_report(_session_with_candidate())
    assert "U-001" in report
    assert "recommend_revision" in report
    assert "Move the enemy back two tiles." in report
    assert "Does the first jump feel fair?" in report
    assert "Localized difficulty spike detected." in report


def test_report_always_discloses_limitations():
    # Even an empty session carries the responsible use disclosures.
    empty = DesignSession(
        session_id="S0", design_brief="b", created_at=TS, updated_at=TS
    )
    report = build_session_report(empty)
    assert "advisory and designer governed" in report
    assert "drafts, not final assets" in report
    assert "No candidates yet." in report


def test_service_writes_report_file(tmp_path):
    service = LevelDirectorService(
        output_root=tmp_path,
        triage_adapter=MockTriageAdapter("accept_for_playtest"),
        feedback_adapter=MockFeedbackAdapter(),
    )
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    path = service.build_session_report("S1")
    assert path.exists()
    assert "Session Report" in path.read_text(encoding="utf-8")
    # A report_generated event was logged.
    events = service.store.read_events("S1")
    assert any(e.event_type == "report_generated" for e in events)

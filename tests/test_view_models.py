"""Tests for the UI view models (pure, no Gradio)."""

from __future__ import annotations

from ai_level_director.domain.models import (
    DesignSession,
    FeedbackResult,
    LevelCandidate,
    PlaytestRecord,
    TriageResult,
)
from ai_level_director.ui.view_models import (
    BOARD_COLUMNS,
    candidate_board_view,
    candidate_detail_view,
    playtest_queue_view,
    session_summary_view,
)

TS = "2026-06-12T12:00:00+00:00"


def _feedback_record(sentiment, override=None) -> PlaytestRecord:
    return PlaytestRecord(
        playtest_id="P-001", candidate_id="U-001", submitted_at=TS,
        feedback_text="Looks pretty fun.",
        feedback_result=FeedbackResult(
            feedback_text="Looks pretty fun.", sentiment=sentiment, model_name="test",
        ),
        status_after_feedback="complete", designer_override=override,
    )


def _candidate(cid="U-001", state="draft", triage=None) -> LevelCandidate:
    return LevelCandidate(
        candidate_id=cid, title=f"Title {cid}", source="uploaded", level_text="----\nXXXX",
        workflow_state=state, created_at=TS, updated_at=TS, triage_result=triage,
    )


def _session(candidates) -> DesignSession:
    return DesignSession(
        session_id="S1", design_brief="An easy segment.", target_difficulty="easy",
        candidates=candidates, created_at=TS, updated_at=TS,
    )


def test_board_view_columns_and_rows():
    triage = TriageResult(action="accept_for_playtest", readiness="ready_for_playtest",
                          rationale="ok", warnings=["spike"])
    df = candidate_board_view(_session([_candidate(state="ready_for_playtest", triage=triage)]))
    assert list(df.columns) == BOARD_COLUMNS
    assert df.iloc[0]["candidate_id"] == "U-001"
    assert df.iloc[0]["triage_action"] == "accept_for_playtest"
    assert df.iloc[0]["main_warning"] == "spike"
    assert df.iloc[0]["next_step"] == "Send to playtest"


def test_board_feedback_reflects_designer_override():
    # After the designer overrides the classifier, the board must show the decision of
    # record, not the model's original label.
    cand = _candidate(state="revision_needed")
    cand.feedback_records.append(_feedback_record("positive", override="negative"))
    df = candidate_board_view(_session([cand]))
    assert df.iloc[0]["feedback"] == "negative (override)"


def test_board_feedback_without_override_shows_classifier_label():
    cand = _candidate(state="complete")
    cand.feedback_records.append(_feedback_record("positive"))
    df = candidate_board_view(_session([cand]))
    assert df.iloc[0]["feedback"] == "positive"


def test_board_view_empty_session_has_columns():
    df = candidate_board_view(_session([]))
    assert list(df.columns) == BOARD_COLUMNS
    assert len(df) == 0


def test_playtest_queue_filters_to_sent():
    candidates = [_candidate("U-001", "draft"), _candidate("U-002", "sent_to_playtest")]
    df = playtest_queue_view(_session(candidates))
    assert list(df["candidate_id"]) == ["U-002"]


def test_candidate_detail_blocks():
    triage = TriageResult(action="recommend_revision", readiness="revise_before_playtest",
                          rationale="enemy on landing", warnings=["spike"],
                          revision_recommendations=["move enemy"], playtest_questions=["fair?"])
    detail = candidate_detail_view(_session([_candidate(triage=triage)]), "U-001")
    assert "U-001" in detail["metadata_markdown"]
    assert "recommend_revision" in detail["triage_markdown"]
    assert "move enemy" in detail["triage_markdown"]
    assert detail["raw_level_text"]  # ascii preview present


def test_candidate_detail_none_selected():
    detail = candidate_detail_view(_session([]), None)
    assert detail["metadata_markdown"] == "_No candidate selected._"


def test_session_summary():
    summary = session_summary_view(_session([_candidate()]))
    assert "S1" in summary and "Candidates: 1" in summary

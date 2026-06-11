"""Unit tests for the domain models.

These confirm the data shapes: defaults, value constraints, and that a fully
populated session survives a JSON round trip unchanged. The models carry no
behavior, so these tests are about structure and validation, not workflow logic.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ai_level_director.domain import (
    CandidateEvent,
    DesignSession,
    FeedbackResult,
    LevelCandidate,
    PlaytestRecord,
    TriageResult,
)

TS = "2026-06-11T12:00:00+00:00"


def make_candidate(**overrides) -> LevelCandidate:
    """Build a minimal valid candidate, with optional field overrides."""
    fields = {
        "candidate_id": "G-001",
        "title": "Test candidate",
        "source": "generated",
        "level_text": "----\nXXXX",
        "created_at": TS,
        "updated_at": TS,
    }
    fields.update(overrides)
    return LevelCandidate(**fields)


def make_session(**overrides) -> DesignSession:
    """Build a minimal valid design session, with optional field overrides."""
    fields = {
        "session_id": "S-001",
        "design_brief": "An easy beginner friendly segment.",
        "created_at": TS,
        "updated_at": TS,
    }
    fields.update(overrides)
    return DesignSession(**fields)


def test_candidate_defaults():
    candidate = make_candidate()
    assert candidate.workflow_state == "draft"
    assert candidate.iteration_number == 1
    assert candidate.triage_result is None
    assert candidate.feedback_records == []
    assert candidate.history == []


def test_candidate_default_collections_are_independent():
    # default_factory must give each instance its own list, not a shared one.
    a = make_candidate(candidate_id="G-001")
    b = make_candidate(candidate_id="G-002")
    a.history.append(
        CandidateEvent(event_id="E1", timestamp=TS, event_type="created", summary="created")
    )
    assert a.history and b.history == []


def test_session_defaults():
    session = make_session()
    assert session.project_name == "AI Level Director Studio"
    assert session.session_status == "active"
    assert session.candidates == []
    assert session.selected_candidate_id is None


def test_invalid_candidate_state_is_rejected():
    with pytest.raises(ValidationError):
        make_candidate(workflow_state="not_a_real_state")


def test_invalid_candidate_source_is_rejected():
    with pytest.raises(ValidationError):
        make_candidate(source="invented_source")


def test_invalid_feedback_sentiment_is_rejected():
    with pytest.raises(ValidationError):
        FeedbackResult(feedback_text="ok", sentiment="neutral", model_name="m")


def test_full_session_json_round_trip():
    feedback = FeedbackResult(
        feedback_text="The first jump felt unfair.",
        sentiment="negative",
        model_name="linear_svm",
    )
    record = PlaytestRecord(
        playtest_id="PT-001",
        candidate_id="G-001",
        submitted_at=TS,
        feedback_text="The first jump felt unfair.",
        feedback_result=feedback,
        status_after_feedback="revision_needed",
    )
    triage = TriageResult(
        action="recommend_revision",
        readiness="revise_before_playtest",
        rationale="An enemy sits on the first landing.",
        warnings=["opening difficulty spike"],
        revision_recommendations=["move the enemy two tiles right"],
        playtest_questions=["Does the first jump feel fair?"],
    )
    event = CandidateEvent(
        event_id="E1", timestamp=TS, event_type="triaged",
        candidate_id="G-001", summary="Triaged: recommend_revision",
    )
    candidate = make_candidate(
        workflow_state="revision_needed",
        triage_result=triage,
        feedback_records=[record],
        history=[event],
    )
    session = make_session(candidates=[candidate], selected_candidate_id="G-001")

    restored = DesignSession.model_validate_json(session.model_dump_json())
    assert restored == session
    assert restored.candidates[0].triage_result.action == "recommend_revision"
    assert restored.candidates[0].feedback_records[0].feedback_result.sentiment == "negative"

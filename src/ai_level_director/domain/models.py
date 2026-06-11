"""Core domain models: the design session and its level candidates.

These are pure data models. They carry no workflow behavior. State transitions,
the adapters, persistence, and reporting are implemented in their own modules and
operate on these structures. Mutable fields use ``default_factory`` so each
instance gets its own list or dict rather than a shared one.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from ai_level_director.domain.events import CandidateEvent
from ai_level_director.domain.states import (
    CandidateSource,
    CandidateState,
    FeedbackSentiment,
    SessionStatus,
)


class TriageResult(BaseModel):
    """Normalized result of a Project 6 triage pass over one candidate.

    Project 6 is the triage authority. This model is the narrow, stable shape the
    rest of Project 7 depends on, decoupled from Project 6's internal schema. The
    full Project 6 output is preserved in ``raw_payload`` for auditing.
    """

    action: str
    readiness: str
    rationale: str
    warnings: list[str] = Field(default_factory=list)
    revision_recommendations: list[str] = Field(default_factory=list)
    playtest_questions: list[str] = Field(default_factory=list)
    transcript_path: str | None = None
    report_path: str | None = None
    raw_payload: dict = Field(default_factory=dict)


class FeedbackResult(BaseModel):
    """Normalized result of a Project 3 feedback classification.

    This is a broad reception signal, positive or negative, not a complete
    playtest analysis. ``confidence`` and ``model_name`` are recorded so the
    workflow can route low confidence results to human review and so reports can
    disclose which model produced the label.
    """

    feedback_text: str
    sentiment: FeedbackSentiment
    confidence: float
    model_name: str
    label_source: str = "project3_feedback_classifier"


class PlaytestRecord(BaseModel):
    """A single playtest submission and the feedback classification it produced."""

    playtest_id: str
    candidate_id: str
    submitted_at: str
    feedback_text: str
    feedback_result: FeedbackResult
    status_after_feedback: CandidateState


class LevelCandidate(BaseModel):
    """One candidate level segment and its full workflow state.

    Each candidate owns its own lifecycle state, triage result, feedback records,
    and event history, so many candidates in different states can coexist in one
    design session. A revised candidate is a new candidate that points back to its
    source through ``parent_candidate_id`` rather than overwriting the original,
    which preserves the iteration history.
    """

    candidate_id: str
    title: str
    source: CandidateSource
    level_text: str
    level_path: str | None = None
    rendered_preview_path: str | None = None

    workflow_state: CandidateState = "draft"
    parent_candidate_id: str | None = None
    iteration_number: int = 1

    generation_metadata: dict = Field(default_factory=dict)
    triage_result: TriageResult | None = None
    feedback_records: list[PlaytestRecord] = Field(default_factory=list)

    created_at: str
    updated_at: str
    history: list[CandidateEvent] = Field(default_factory=list)


class DesignSession(BaseModel):
    """A design workspace: the brief plus its collection of level candidates.

    The session is the unit that gets saved to and loaded from JSON. It holds the
    designer's brief and targets, the candidate collection, and which candidate is
    currently selected in the UI.
    """

    session_id: str
    project_name: str = "AI Level Director Studio"
    design_brief: str
    target_difficulty: str | None = None
    novelty_preference: str | None = None
    session_status: SessionStatus = "active"

    candidates: list[LevelCandidate] = Field(default_factory=list)
    selected_candidate_id: str | None = None

    created_at: str
    updated_at: str
    session_notes: list[str] = Field(default_factory=list)

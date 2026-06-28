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

    # Rendered deliberation text carried from the adapter to the service, which
    # writes it to a file and records the path above. Excluded from serialization
    # so the full transcript never bloats the session JSON snapshot; the saved file
    # is the persistent record.
    transcript_text: str | None = Field(default=None, exclude=True)
    report_text: str | None = Field(default=None, exclude=True)


class FeedbackResult(BaseModel):
    """Normalized result of a Project 3 feedback classification.

    This is a broad reception signal, positive or negative, not a complete
    playtest analysis. The underlying classifier is a linear SVM that returns only
    a label and no probability, so no confidence score is recorded; fabricating
    one would misrepresent the model. ``model_name`` is kept so reports can
    disclose which model produced the label. See Decision 12 in the decision log.
    """

    feedback_text: str
    sentiment: FeedbackSentiment
    model_name: str
    label_source: str = "project3_feedback_classifier"


class PlaytestRecord(BaseModel):
    """A single playtest submission and the feedback classification it produced.

    ``warning`` carries an integration level reliability note (for example that the
    feedback was too short for the classifier to be trusted). It is advisory text for
    the designer, not a classifier output, so it lives here rather than on
    ``FeedbackResult``.
    """

    playtest_id: str
    candidate_id: str
    submitted_at: str
    feedback_text: str
    feedback_result: FeedbackResult
    status_after_feedback: CandidateState
    warning: str | None = None
    # The designer's corrected sentiment, when they override the classifier after
    # reading the text. The classifier's own label stays in feedback_result for the
    # audit trail; this records that a human disagreed.
    designer_override: FeedbackSentiment | None = None

    @property
    def decision_sentiment(self) -> str:
        """The sentiment of record for display.

        A designer override supersedes the classifier's label, so every view shows the
        human decision rather than the model's original call. When the designer
        overrode, the label carries an ``(override)`` marker; otherwise it is the
        classifier's own label. The classifier label stays in ``feedback_result`` for
        the audit trail regardless.
        """
        if self.designer_override and self.designer_override != self.feedback_result.sentiment:
            return f"{self.designer_override} (override)"
        return self.feedback_result.sentiment


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
    session_name: str | None = None
    design_brief: str
    target_difficulty: str | None = None
    novelty_preference: str | None = None
    session_status: SessionStatus = "active"

    candidates: list[LevelCandidate] = Field(default_factory=list)
    selected_candidate_id: str | None = None

    created_at: str
    updated_at: str
    session_notes: list[str] = Field(default_factory=list)

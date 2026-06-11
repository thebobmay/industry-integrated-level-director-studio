"""Candidate lifecycle events for the append only audit trail.

Every meaningful action in the workflow appends a ``CandidateEvent`` to the
candidate's history and to the session event log. Events are never mutated, so a
candidate's history stays a complete, ordered record of what happened to it. This
is what gives the system its transparency.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

CandidateEventType = Literal[
    "created",
    "generated",
    "uploaded",
    "triaged",
    "sent_to_playtest",
    "feedback_submitted",
    "state_changed",
    "revision_created",
    "completed",
    "archived",
    "report_generated",
]


class CandidateEvent(BaseModel):
    """One recorded event in a candidate's history.

    Attributes
    ----------
    event_id:
        Unique identifier for this event.
    timestamp:
        ISO 8601 timestamp of when the event occurred.
    event_type:
        The kind of event, constrained to the known lifecycle event types.
    candidate_id:
        The candidate the event belongs to, or ``None`` for session level events.
    summary:
        Short human readable description of what happened.
    payload:
        Optional structured detail (for example the triage action or feedback
        sentiment) for downstream inspection.
    """

    event_id: str
    timestamp: str
    event_type: CandidateEventType
    candidate_id: str | None = None
    summary: str
    payload: dict = Field(default_factory=dict)

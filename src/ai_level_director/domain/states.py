"""Constrained string types that the rest of the domain is built on.

These ``Literal`` types are the shared vocabulary for candidate lifecycle states,
candidate sources, session status, and feedback sentiment. Defining them in one
place means the state machine, the adapters, the report builder, and the UI all
refer to a single source of truth for the allowed values, and a typo becomes a
type error rather than a silent bug.
"""

from __future__ import annotations

from typing import Literal

# Every state a single candidate can occupy. A candidate owns its own state, so
# several candidates in different states can coexist in one design session.
CandidateState = Literal[
    "draft",
    "triaged",
    "clarification_needed",
    "revision_needed",
    "structural_rejected",
    "derivative_review_needed",
    "ready_for_playtest",
    "sent_to_playtest",
    "feedback_received",
    "complete",
    "human_review_needed",
    "archived",
]

# Where a candidate came from. A revised candidate is a new candidate that points
# back to its source rather than overwriting the original.
CandidateSource = Literal["generated", "uploaded", "sample", "revised"]

# Overall status of the design session (the workspace).
SessionStatus = Literal["active", "complete", "archived"]

# The two reception classes the Project 3 feedback classifier returns.
FeedbackSentiment = Literal["positive", "negative"]

"""Candidate lifecycle transition rules and the prior project to state mappings.

This module is the candidate state machine. It owns three things in one auditable
place:

- the allowed transitions between candidate states,
- the mapping from a Project 6 triage action to the resulting candidate state,
- the mapping from a Project 3 feedback result to the resulting candidate state.

The workflow controller calls these helpers. Keeping the rules here, rather than
scattering them through the service, is what makes the candidate lifecycle in the
architecture diagram enforceable: an unlisted transition is rejected instead of
silently corrupting candidate state.
"""

from __future__ import annotations

from ai_level_director.domain.states import CandidateState, FeedbackSentiment

# Project 6 triage action -> resulting candidate state.
TRIAGE_ACTION_TO_STATE: dict[str, CandidateState] = {
    "accept_for_playtest": "ready_for_playtest",
    "recommend_revision": "revision_needed",
    "request_clarification": "clarification_needed",
    "reject_structural": "structural_rejected",
    "flag_as_derivative_draft": "derivative_review_needed",
    "request_human_review": "human_review_needed",
}


# The six states a triage pass can produce. Defined from the action map so the two
# never drift apart.
TRIAGE_OUTCOME_STATES: set[CandidateState] = set(TRIAGE_ACTION_TO_STATE.values())

# Allowed transitions between candidate states. A transition not listed here is
# rejected. Keys are the current state; values are the states reachable from it.
# Triage moves a draft candidate directly to one of the six mapped states above,
# so "triaged" is reserved and not used as a destination.
#
# The three soft pre playtest states (clarification_needed, revision_needed,
# human_review_needed) also allow the triage outcome states, so a candidate can be
# re-triaged in place after the designer edits the brief or the candidate. This is
# what lets a clarification request be resolved without abandoning the candidate.
ALLOWED_TRANSITIONS: dict[CandidateState, set[CandidateState]] = {
    "draft": set(TRIAGE_OUTCOME_STATES),
    "triaged": set(),
    "ready_for_playtest": {"sent_to_playtest", "archived"},
    "derivative_review_needed": {"sent_to_playtest", "archived", "human_review_needed"},
    "sent_to_playtest": {"feedback_received"},
    "feedback_received": {"complete", "revision_needed", "human_review_needed"},
    "revision_needed": {"draft", "archived"} | TRIAGE_OUTCOME_STATES,
    "clarification_needed": {"draft", "archived"} | TRIAGE_OUTCOME_STATES,
    "human_review_needed": {"draft", "archived"} | TRIAGE_OUTCOME_STATES,
    "structural_rejected": {"archived"},
    "complete": {"archived"},
    "archived": set(),
}


class InvalidTransitionError(ValueError):
    """Raised when a candidate state transition is not allowed."""


def can_transition(current: CandidateState, target: CandidateState) -> bool:
    """Return whether moving from current to target is an allowed transition."""
    return target in ALLOWED_TRANSITIONS.get(current, set())


def ensure_transition(current: CandidateState, target: CandidateState) -> CandidateState:
    """Return target if the transition is allowed, otherwise raise.

    The controller uses this as a guard so an invalid lifecycle jump fails loudly
    rather than silently corrupting candidate state.
    """
    if not can_transition(current, target):
        raise InvalidTransitionError(
            f"Cannot move candidate from '{current}' to '{target}'."
        )
    return target


def state_for_triage_action(action: str) -> CandidateState:
    """Map a Project 6 triage action to the resulting candidate state."""
    try:
        return TRIAGE_ACTION_TO_STATE[action]
    except KeyError as exc:
        raise ValueError(f"Unknown triage action: '{action}'.") from exc


def state_for_feedback(sentiment: FeedbackSentiment) -> CandidateState:
    """Map a Project 3 feedback result to the resulting candidate state.

    The Project 3 classifier returns only a label, positive or negative, with no
    probability or confidence score, so the mapping is direct: positive completes
    the candidate and negative sends it back for revision. Feedback that cannot be
    classified at all (for example empty or missing text) is caught upstream by
    the playtest service and routed to human_review_needed; that is an input
    check, not a classifier confidence judgment. See Decision 12 in the decision
    log.
    """
    return "complete" if sentiment == "positive" else "revision_needed"

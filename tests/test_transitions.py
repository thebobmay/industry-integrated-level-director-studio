"""Unit tests for the candidate state machine.

These cover the three responsibilities of the transitions module: the triage
action mapping, the feedback mapping, and the allowed transition guard. The
Project 3 classifier returns only a label, so there is no confidence routing. The
consistency tests assert that every state a
mapping can produce is actually reachable by the transition rules, so the two
halves of the state machine cannot drift apart.
"""

from __future__ import annotations

import pytest

from ai_level_director.workflow.transitions import (
    TRIAGE_ACTION_TO_STATE,
    InvalidTransitionError,
    can_transition,
    ensure_transition,
    state_for_feedback,
    state_for_triage_action,
)


def test_triage_action_mapping_is_complete():
    assert TRIAGE_ACTION_TO_STATE == {
        "accept_for_playtest": "ready_for_playtest",
        "recommend_revision": "revision_needed",
        "request_clarification": "clarification_needed",
        "reject_structural": "structural_rejected",
        "flag_as_derivative_draft": "derivative_review_needed",
        "request_human_review": "human_review_needed",
    }


def test_state_for_triage_action_known_and_unknown():
    assert state_for_triage_action("accept_for_playtest") == "ready_for_playtest"
    with pytest.raises(ValueError):
        state_for_triage_action("not_an_action")


def test_feedback_positive_completes():
    assert state_for_feedback("positive") == "complete"


def test_feedback_negative_needs_revision():
    assert state_for_feedback("negative") == "revision_needed"


@pytest.mark.parametrize(
    "current,target",
    [
        ("draft", "ready_for_playtest"),
        ("draft", "revision_needed"),
        ("ready_for_playtest", "sent_to_playtest"),
        ("derivative_review_needed", "sent_to_playtest"),
        ("sent_to_playtest", "feedback_received"),
        ("feedback_received", "complete"),
        ("feedback_received", "revision_needed"),
        ("revision_needed", "draft"),
        ("complete", "archived"),
    ],
)
def test_allowed_transitions(current, target):
    assert can_transition(current, target)


@pytest.mark.parametrize(
    "current,target",
    [
        ("draft", "complete"),
        ("draft", "sent_to_playtest"),
        ("ready_for_playtest", "complete"),
        ("complete", "draft"),
        ("archived", "draft"),
        ("sent_to_playtest", "complete"),
    ],
)
def test_disallowed_transitions(current, target):
    assert not can_transition(current, target)


def test_ensure_transition_guard():
    assert ensure_transition("draft", "ready_for_playtest") == "ready_for_playtest"
    with pytest.raises(InvalidTransitionError):
        ensure_transition("draft", "complete")


def test_every_triage_target_is_reachable_from_draft():
    # Triage operates on a draft candidate, so each mapped state must be a valid
    # transition out of draft. This keeps the mapping and the transitions in sync.
    for target in TRIAGE_ACTION_TO_STATE.values():
        assert can_transition("draft", target)


def test_every_feedback_target_is_reachable_from_feedback_received():
    targets = {state_for_feedback("positive"), state_for_feedback("negative")}
    for target in targets:
        assert can_transition("feedback_received", target)

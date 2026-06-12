"""The thin deterministic safety floor.

The agents make the decision. This floor only enforces hard facts and escalation
over their result, and it can only move the outcome toward the safe side. It never
re decides the happy path and never computes readiness from a metric.

Four rules:
1. A structurally invalid candidate is never accepted or called ready.
2. An explicit critic escalation forces human review.
3. An unresolved critic dispute at the round cap escalates to human review.
4. A clarification request forces not_ready: revision cannot be prescribed before
   the designer's intent is known.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from src.models import Critique, LevelFacts, ReadinessLevel, TriageAction, TriageRecommendation

MAX_ROUNDS = 5


class SafetyOutcome(BaseModel):
    """The final action and readiness after the safety floor, with any interventions."""

    action: TriageAction = Field(description="The final triage action.")
    readiness: ReadinessLevel = Field(description="The final playtest readiness.")
    interventions: list[str] = Field(
        default_factory=list,
        description="Reasons the floor changed the agents' result, for the audit log.",
    )


def apply_safety_floor(
    recommendation: TriageRecommendation,
    facts: LevelFacts,
    critique: Critique | None,
    round_count: int,
    max_rounds: int = MAX_ROUNDS,
) -> SafetyOutcome:
    """Enforce the hard safety rules over the agents' recommendation and return the outcome."""
    action: TriageAction = recommendation.action
    readiness: ReadinessLevel = recommendation.playtest_readiness
    interventions: list[str] = []

    # Rule 1: a structurally invalid candidate cannot go to playtest regardless of the
    # brief or the agents' choice. Reject for structural reasons and stop, so this is
    # not overridden by the escalation rules below.
    if not facts.validation.is_valid:
        if action != "reject_structural":
            interventions.append(f"overrode {action}: candidate is structurally invalid")
            action = "reject_structural"
        if readiness != "not_ready":
            interventions.append("forced not_ready: candidate is structurally invalid")
            readiness = "not_ready"
        return SafetyOutcome(action=action, readiness=readiness, interventions=interventions)

    # Rule 2: an explicit critic escalation forces human review.
    if critique is not None and critique.verdict == "escalate" and action != "request_human_review":
        action = "request_human_review"
        interventions.append("escalated to human review: the critic escalated")

    # Rule 3: an unresolved dispute at the round cap escalates to human review.
    if (
        critique is not None
        and critique.verdict != "approve"
        and round_count >= max_rounds
        and action != "request_human_review"
    ):
        action = "request_human_review"
        interventions.append(
            "escalated to human review: unresolved critic dispute at the round cap"
        )

    # Rule 4: clarification means the intent is unknown, so revision cannot be
    # prescribed yet. Force not_ready regardless of what the agent chose.
    if action == "request_clarification" and readiness != "not_ready":
        interventions.append("forced not_ready: action is request_clarification, intent unknown")
        readiness = "not_ready"

    # Keep readiness consistent with a human review outcome.
    if action == "request_human_review" and readiness == "ready_for_playtest":
        readiness = "revise_before_playtest"
        interventions.append("downgraded readiness: action is request_human_review")

    return SafetyOutcome(action=action, readiness=readiness, interventions=interventions)

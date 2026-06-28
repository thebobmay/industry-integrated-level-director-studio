"""Evaluation suite built on pydantic-evals.

Because the triage action is a judgment under interpreted intent, this suite
evaluates the workflow by invariants and required properties rather than exact
action matching: the action and readiness are in their allowed sets and
consistent, the safety invariants hold (an invalid candidate is never accepted or
ready, a revision recommendation carries a prescription), and the recommendation
is complete. Exact agreement with each scenario's expected action is recorded as a
score for visibility, not asserted.

The invariant evaluators run offline. An optional LLM judge for narrative
grounding is added only when EVAL_LLM_JUDGE is set, so the suite runs without
credentials by default. Tests override the agents with TestModel; run_evals.py
runs the real agents and saves the report.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic_evals import Case, Dataset
from pydantic_evals.evaluators import Evaluator, EvaluatorContext

from src.models import ScenarioDefinition, TriageSession
from src.scenarios import build_triage_request, load_scenarios
from src.workflow import triage_candidate

ALLOWED_ACTIONS = {
    "accept_for_playtest",
    "recommend_revision",
    "request_clarification",
    "flag_as_derivative_draft",
    "reject_structural",
    "request_human_review",
}
ALLOWED_READINESS = {"ready_for_playtest", "revise_before_playtest", "not_ready"}
_ESCALATIONS = {"reject_structural", "request_human_review", "request_clarification"}
# Actions that green light playtest. A derivative draft is structurally valid and
# playable; the flag is a novelty concern, not a playtest blocker, so it may be ready.
_PLAYTEST_READY_ACTIONS = {"accept_for_playtest", "flag_as_derivative_draft"}


def _is_valid(session: TriageSession) -> bool:
    """Validity of the candidate the recommendation is about."""
    return bool(session.facts and session.facts.validation.is_valid)


@dataclass
class ActionAndReadinessValid(Evaluator):
    """Action and readiness are in their allowed sets and mutually consistent."""

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool]:
        """Check the action and readiness are in their allowed sets and consistent."""
        session: TriageSession = ctx.output
        rec = session.recommendation
        checks = {
            "action_in_set": session.decision in ALLOWED_ACTIONS,
            "readiness_in_set": bool(rec) and rec.playtest_readiness in ALLOWED_READINESS,
        }
        if rec is not None:
            if rec.playtest_readiness == "ready_for_playtest":
                checks["ready_only_when_playtestable"] = session.decision in _PLAYTEST_READY_ACTIONS
            if session.decision in _ESCALATIONS:
                checks["escalation_not_ready"] = rec.playtest_readiness != "ready_for_playtest"
        return checks


@dataclass
class SafetyInvariants(Evaluator):
    """The hard safety invariants hold over the agents' result."""

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool]:
        """Check the hard safety invariants over the agents' result hold."""
        session: TriageSession = ctx.output
        checks: dict[str, bool] = {}
        if not _is_valid(session):
            checks["invalid_not_accepted"] = session.decision != "accept_for_playtest"
            checks["invalid_not_ready"] = (
                session.recommendation is None
                or session.recommendation.playtest_readiness != "ready_for_playtest"
            )
        if session.decision == "recommend_revision" and session.recommendation is not None:
            checks["revision_has_prescription"] = session.recommendation.prescription is not None
        return checks


@dataclass
class RecommendationComplete(Evaluator):
    """The recommendation is present and carries a non-empty diagnosis."""

    def evaluate(self, ctx: EvaluatorContext) -> dict[str, bool]:
        """Check the recommendation is present and carries a non-empty diagnosis."""
        rec = ctx.output.recommendation
        if rec is None:
            return {"recommendation_present": False}
        return {
            "recommendation_present": True,
            "diagnosis_nonempty": bool(rec.diagnosis.strip()),
        }


@dataclass
class ExpectedActionMatch(Evaluator):
    """Record whether the action matched the scenario expectation, as a score."""

    def evaluate(self, ctx: EvaluatorContext) -> float:
        """Score 1.0 when the action matches the scenario expectation, else 0.0."""
        return 1.0 if ctx.output.decision == ctx.expected_output else 0.0


def _invariant_evaluators() -> list[Evaluator]:
    """The offline invariant and property evaluators shared by every case."""
    return [
        ActionAndReadinessValid(),
        SafetyInvariants(),
        RecommendationComplete(),
        ExpectedActionMatch(),
    ]


def _maybe_llm_judge() -> list[Evaluator]:
    """Add the optional LLM judge only when EVAL_LLM_JUDGE is set."""
    if not os.environ.get("EVAL_LLM_JUDGE"):
        return []
    from pydantic_evals.evaluators import LLMJudge

    rubric = (
        "The output is a level design triage session. Judge only whether the recommendation's "
        "diagnosis and reasoning are grounded in and consistent with the recorded facts and the "
        "interpreted intent. Do not judge whether the level is fun."
    )
    model = os.environ.get("EVAL_JUDGE_MODEL", os.environ.get("TRIAGE_MODEL", "openai-chat:gpt-4o-mini"))
    return [LLMJudge(rubric=rubric, model=model, include_input=True)]


def build_dataset(scenarios: list[ScenarioDefinition] | None = None) -> Dataset:
    """Build the evaluation dataset from the scenario fixtures."""
    scenarios = scenarios if scenarios is not None else load_scenarios()
    cases = [
        Case(
            name=scenario.scenario_id,
            inputs=scenario,
            expected_output=scenario.expected_action,
            metadata={"name": scenario.name},
        )
        for scenario in scenarios
    ]
    return Dataset(
        name="triage_scenarios",
        cases=cases,
        evaluators=_invariant_evaluators() + _maybe_llm_judge(),
    )


def make_task(reference_levels: list[str]):
    """Build the eval task: run one scenario through the workflow."""

    def run_case(scenario: ScenarioDefinition) -> TriageSession:
        """Run the triage workflow for a single scenario."""
        return triage_candidate(build_triage_request(scenario), reference_levels)

    return run_case


def run_eval_suite(
    reference_levels: list[str],
    scenarios: list[ScenarioDefinition] | None = None,
):
    """Run the full eval suite and return the pydantic-evals EvaluationReport."""
    dataset = build_dataset(scenarios)
    return dataset.evaluate_sync(make_task(reference_levels), max_concurrency=1)

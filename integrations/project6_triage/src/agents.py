"""Pydantic AI agents for the triage system.

Three agents do the judgment:

- The Intent Interpreter turns a natural language brief into a structured
  DesignIntentProfile and detects conflicts in the request itself.
- The Triage Director (optimizer, ReAct) calls the deterministic analysis tools
  for facts, reasons about intent versus facts and tradeoffs in context, and
  chooses one triage action with its narrative and any revision prescription.
- The Critic (evaluator, independent) judges whether the Director's recommendation
  is sound and constraint respecting, and can approve, send it back, or escalate.

The agents are grounded in the curated design knowledge. The model is set by
TRIAGE_MODEL (default openai-chat:gpt-4.1) at temperature 0. defer_model_check
lets the module import without credentials; tests override the model with TestModel.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.usage import RunUsage, UsageLimits

from src.design_knowledge import get_design_guidance
from src.prompts import load_prompt
from src.models import (
    Critique,
    DesignIntentProfile,
    DifficultyResult,
    LevelFacts,
    NoveltyResult,
    PacingResult,
    SafeZoneResult,
    SpikeResult,
    TriageRecommendation,
    ValidationResult,
)
from src.tools import (
    ToolLog,
    Transcript,
    analyze_candidate_pacing,
    detect_candidate_safe_zone,
    detect_candidate_spike,
    estimate_candidate_difficulty,
    measure_candidate_novelty,
    validate_candidate_level,
)

DEFAULT_MODEL = os.environ.get("TRIAGE_MODEL", "openai-chat:gpt-4.1")


# Intent Interpreter -----------------------------------------------------------

intent_interpreter = Agent(
    DEFAULT_MODEL,
    output_type=DesignIntentProfile,
    instructions=load_prompt("intent_interpreter"),
    output_retries=2,
    defer_model_check=True,
)


def run_intent_interpreter(
    brief_text: str,
    model: str | None = None,
    model_settings: dict | None = None,
    usage: RunUsage | None = None,
    usage_limits: UsageLimits | None = None,
    transcript: Transcript | None = None,
) -> DesignIntentProfile:
    """Interpret a design brief into a structured intent profile."""
    prompt = f"Design brief:\n{brief_text}\n\nInterpret this brief into a design intent profile."
    result = intent_interpreter.run_sync(
        prompt, model=model, model_settings=model_settings, usage_limits=usage_limits
    )
    if usage is not None:
        usage.incr(result.usage)
    if transcript is not None:
        transcript.add_messages(result.all_messages(), agent="intent_interpreter")
    return result.output


# Triage Director (optimizer) --------------------------------------------------

@dataclass
class DirectorDeps:
    """Injected dependencies for the Triage Director's tools."""

    candidate_level: str
    reference_levels: list[str]
    tool_log: ToolLog


triage_director = Agent(
    DEFAULT_MODEL,
    deps_type=DirectorDeps,
    output_type=TriageRecommendation,
    instructions=load_prompt("triage_director") + "\n\n" + get_design_guidance(),
    output_retries=2,
    defer_model_check=True,
)


@triage_director.tool
def check_validity(ctx: RunContext[DirectorDeps]) -> ValidationResult:
    """Validate the candidate's structure, vocabulary, dimensions, and pipe integrity."""
    result = validate_candidate_level(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("validate_candidate_level", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_difficulty(ctx: RunContext[DirectorDeps]) -> DifficultyResult:
    """Estimate the candidate's heuristic structural difficulty."""
    result = estimate_candidate_difficulty(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("estimate_candidate_difficulty", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_novelty(ctx: RunContext[DirectorDeps]) -> NoveltyResult:
    """Measure the candidate's novelty against the reference library."""
    result = measure_candidate_novelty(ctx.deps.candidate_level, ctx.deps.reference_levels)
    ctx.deps.tool_log.record("measure_candidate_novelty", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_pacing(ctx: RunContext[DirectorDeps]) -> PacingResult:
    """Analyze the candidate's challenge pacing across the segment."""
    result = analyze_candidate_pacing(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("analyze_candidate_pacing", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_safe_zone(ctx: RunContext[DirectorDeps]) -> SafeZoneResult:
    """Check whether the candidate opens with a safe zone before the first challenge."""
    result = detect_candidate_safe_zone(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("detect_candidate_safe_zone", {"level": "candidate"}, result)
    return result


@triage_director.tool
def check_spike(ctx: RunContext[DirectorDeps]) -> SpikeResult:
    """Detect a localized difficulty spike (a gap combined with an enemy or cannon)."""
    result = detect_candidate_spike(ctx.deps.candidate_level)
    ctx.deps.tool_log.record("detect_candidate_spike", {"level": "candidate"}, result)
    return result


def run_triage_director(
    intent: DesignIntentProfile,
    candidate_level: str,
    reference_levels: list[str],
    tool_log: ToolLog,
    prior_feedback: list[str] | None = None,
    model: str | None = None,
    model_settings: dict | None = None,
    usage: RunUsage | None = None,
    usage_limits: UsageLimits | None = None,
    transcript: Transcript | None = None,
    round_num: int | None = None,
) -> TriageRecommendation:
    """Run the Triage Director over the candidate, optionally with prior critic feedback."""
    deps = DirectorDeps(
        candidate_level=candidate_level,
        reference_levels=reference_levels,
        tool_log=tool_log,
    )
    lines = [
        "Interpreted design intent:",
        intent.model_dump_json(indent=2),
        "",
        "Candidate level (14 rows by 32 columns):",
        candidate_level,
    ]
    if prior_feedback:
        lines += [
            "",
            "A critic returned your previous recommendation for revision. Address this feedback:",
            *[f"- {item}" for item in prior_feedback],
        ]
    lines += ["", "Gather facts with your tools, then choose one action and explain it."]
    result = triage_director.run_sync(
        "\n".join(lines),
        deps=deps,
        model=model,
        model_settings=model_settings,
        usage_limits=usage_limits,
    )
    if usage is not None:
        usage.incr(result.usage)
    if transcript is not None:
        transcript.add_messages(result.all_messages(), agent="triage_director", round=round_num)
    return result.output


# Critic (evaluator) -----------------------------------------------------------

critic_agent = Agent(
    DEFAULT_MODEL,
    output_type=Critique,
    instructions=load_prompt("critic") + "\n\n" + get_design_guidance(),
    output_retries=2,
    defer_model_check=True,
)


def run_critic(
    intent: DesignIntentProfile,
    candidate_level: str,
    facts: LevelFacts,
    recommendation: TriageRecommendation,
    model: str | None = None,
    model_settings: dict | None = None,
    usage: RunUsage | None = None,
    usage_limits: UsageLimits | None = None,
    transcript: Transcript | None = None,
    round_num: int | None = None,
) -> Critique:
    """Run the Critic to independently evaluate the Director's recommendation."""
    lines = [
        "Interpreted design intent:",
        intent.model_dump_json(indent=2),
        "",
        "Gathered facts:",
        facts.model_dump_json(indent=2),
        "",
        "Candidate level (14 rows by 32 columns):",
        candidate_level,
        "",
        "The Triage Director's recommendation:",
        recommendation.model_dump_json(indent=2),
        "",
        "Evaluate the recommendation and return your verdict.",
    ]
    result = critic_agent.run_sync(
        "\n".join(lines),
        model=model,
        model_settings=model_settings,
        usage_limits=usage_limits,
    )
    if usage is not None:
        usage.incr(result.usage)
    if transcript is not None:
        transcript.add_messages(result.all_messages(), agent="critic", round=round_num)
    return result.output

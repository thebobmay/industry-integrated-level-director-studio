"""Pydantic schemas and session state for the triage agent.

Defines the typed contracts that flow through the system: the design intent
profile, the deterministic fact result models and their bundle, the triage
recommendation and the revision prescription, the critic's verdict, the session
state that serves as working memory, and the terminal triage action set. These
contracts are the foundation the tools, agents, safety floor, and report build on.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

# Shared label and enum types.
DifficultyLabel = Literal["easy", "medium", "hard"]
NoveltyLabel = Literal["low", "medium", "high"]
ConfidenceLevel = Literal["low", "moderate", "high"]
TargetAudience = Literal["beginner", "intermediate", "expert", "general"]
PacingFlag = Literal["balanced", "front_loaded", "back_loaded", "flat"]
ReadinessLevel = Literal["ready_for_playtest", "revise_before_playtest", "not_ready"]

# The six terminal triage actions the agent can recommend.
TriageAction = Literal[
    "accept_for_playtest",
    "recommend_revision",
    "request_clarification",
    "flag_as_derivative_draft",
    "reject_structural",
    "request_human_review",
]

# The critic's verdict on the Director's recommendation.
CriticVerdict = Literal["approve", "revise", "escalate"]


class TriageRequest(BaseModel):
    """One triage request: a natural language design brief and a candidate level."""

    brief_text: str = Field(description="The designer's design brief in natural language.")
    candidate_level: str = Field(description="Raw tile grid text of the candidate level.")


class DesignIntentProfile(BaseModel):
    """Structured interpretation of the designer's brief.

    This is the Intent Interpreter's output. It converts a messy natural language
    brief into typed intent and surfaces any conflicts found in the request itself.
    """

    target_audience: TargetAudience = Field(description="Who the segment is for.")
    desired_feel: list[str] = Field(
        default_factory=list,
        description="Qualitative feel descriptors drawn from the brief, for example exciting or calm.",
    )
    difficulty_target: DifficultyLabel = Field(description="Interpreted difficulty target.")
    novelty_preference: NoveltyLabel = Field(
        description="How much originality the designer wants, for example low for style consistency.",
    )
    hard_constraints: list[str] = Field(
        default_factory=list,
        description="Non negotiable constraints, for example preserve the core layout.",
    )
    soft_preferences: list[str] = Field(
        default_factory=list,
        description="Preferences that are nice to honor but not mandatory.",
    )
    detected_conflicts: list[str] = Field(
        default_factory=list,
        description="Conflicts the interpreter found within the request, for example accessible but punishing.",
    )


class ValidationResult(BaseModel):
    """Structural validation outcome for a candidate level (a fact, not a judgment)."""

    is_valid: bool = Field(description="True when no fatal errors were found.")
    warnings: list[str] = Field(default_factory=list, description="Non fatal issues to surface.")
    fatal_errors: list[str] = Field(
        default_factory=list,
        description="Errors that make the level structurally invalid.",
    )


class DifficultyResult(BaseModel):
    """Heuristic difficulty estimate from engineered structural features.

    This is structural difficulty only. It is not player validated difficulty.
    """

    difficulty_label: DifficultyLabel = Field(description="Bucketed difficulty label.")
    difficulty_score: float = Field(description="Continuous heuristic difficulty score.")
    enemy_density: float = Field(description="Fraction of tiles that are enemies.")
    hazard_density: float = Field(description="Fraction of tiles that are hazards.")
    longest_gap: int = Field(description="Longest run of floor gap columns.")
    solid_ratio: float = Field(description="Fraction of tiles that are solid ground.")
    collectible_density: float = Field(description="Fraction of tiles that are collectibles.")


class NoveltyResult(BaseModel):
    """Novelty estimate relative to the reference library."""

    nearest_neighbor_similarity: float = Field(
        description="Similarity to the most similar reference level, 0 to 1.",
    )
    novelty_label: NoveltyLabel = Field(description="Bucketed novelty label.")
    warning: str | None = Field(
        default=None,
        description="Memorization or derivative warning when similarity is high.",
    )


class PacingResult(BaseModel):
    """Challenge pacing across the opening, middle, and final thirds of the segment."""

    flag: PacingFlag = Field(description="Overall pacing shape.")
    opening_intensity: int = Field(description="Challenge intensity in the opening third.")
    middle_intensity: int = Field(description="Challenge intensity in the middle third.")
    final_intensity: int = Field(description="Challenge intensity in the final third.")
    detail: str = Field(default="", description="Human readable description of the pacing.")


class SafeZoneResult(BaseModel):
    """Whether the segment opens with a safe zone before the first challenge."""

    has_opening_safe_zone: bool = Field(description="True when the opening is safe long enough.")
    first_challenge_column: int = Field(
        description="Column index of the first challenge, or the width if there is none.",
    )
    detail: str = Field(default="", description="Human readable description of the opening.")


class SpikeResult(BaseModel):
    """A localized low leniency window that combines a gap with an enemy or hazard."""

    has_spike: bool = Field(description="True when a local difficulty spike was found.")
    location_column: int | None = Field(
        default=None,
        description="Column where the spike begins, if any.",
    )
    detail: str = Field(default="", description="Human readable description of the spike.")


class LevelFacts(BaseModel):
    """The bundle of deterministic facts about a candidate level."""

    validation: ValidationResult
    difficulty: DifficultyResult
    novelty: NoveltyResult
    pacing: PacingResult
    safe_zone: SafeZoneResult
    spike: SpikeResult


class PrescribedEdit(BaseModel):
    """A single suggested edit in a revision prescription (advice, not applied)."""

    description: str = Field(description="The concrete edit the designer could make.")
    reason: str = Field(description="Why this edit serves the interpreted intent.")


class RevisionPrescription(BaseModel):
    """An ordered set of suggested edits the designer applies, plus a playtest question.

    The agent never applies these. The prescription is advice that respects the
    hard constraints.
    """

    suggested_edits: list[PrescribedEdit] = Field(
        default_factory=list,
        description="Ordered, reasoned suggested edits.",
    )
    playtest_question: str = Field(
        description="A targeted question to ask after the designer revises.",
    )


class TriageRecommendation(BaseModel):
    """The Triage Director's reasoned recommendation."""

    action: TriageAction = Field(description="The chosen triage action.")
    diagnosis: str = Field(description="What is right or wrong with the candidate, given the intent.")
    tradeoff_reasoning: list[str] = Field(
        default_factory=list,
        description="Ordered reasons that weigh intent against the facts.",
    )
    prescription: RevisionPrescription | None = Field(
        default=None,
        description="Present only when the action is recommend_revision.",
    )
    playtest_readiness: ReadinessLevel = Field(description="The agent's readiness judgment.")
    playtest_questions: list[str] = Field(
        default_factory=list,
        description="Targeted playtest questions for the designer.",
    )
    confidence: ConfidenceLevel = Field(description="Confidence in the recommendation.")


class Critique(BaseModel):
    """The Critic's independent evaluation of the Director's recommendation."""

    verdict: CriticVerdict = Field(
        description="approve to finalize, revise to send back, escalate to request human review.",
    )
    remaining_issues: list[str] = Field(
        default_factory=list,
        description="Issues the critic still sees, if any.",
    )
    constraint_violations: list[str] = Field(
        default_factory=list,
        description="Hard constraints the recommendation would violate, if any.",
    )
    assessment: str = Field(description="Short independent assessment.")
    confidence: ConfidenceLevel = Field(description="Confidence in the assessment.")


class ToolCallLogEntry(BaseModel):
    """A single logged tool invocation for transparency and the audit log."""

    tool_name: str = Field(description="Name of the tool that was called.")
    inputs: dict[str, Any] = Field(default_factory=dict, description="Inputs passed to the tool.")
    outputs: dict[str, Any] = Field(default_factory=dict, description="Outputs returned by the tool.")


class MessageEntry(BaseModel):
    """One step in the full system transcript, in chat message form.

    The transcript is the running record of everything that happened in a pass:
    each agent's prompt, its reasoning text, every tool call with its arguments,
    every tool result, and the deterministic workflow events and final decision.
    """

    step: int = Field(description="Ordinal position of this entry in the pass.")
    agent: str = Field(description="Which agent or stage produced this entry.")
    role: str = Field(description="Chat role: system, user, assistant, or tool.")
    round: int | None = Field(default=None, description="Evaluator-optimizer round, when applicable.")
    content: str | None = Field(default=None, description="Message text, reasoning, or tool result.")
    tool_name: str | None = Field(default=None, description="Tool name for a tool call or its result.")
    tool_args: dict[str, Any] | None = Field(default=None, description="Arguments for a tool call.")
    tool_call_id: str | None = Field(default=None, description="Correlates a tool call with its result.")


class TokenUsage(BaseModel):
    """Token usage accumulated across every agent call in one triage pass."""

    input_tokens: int = Field(default=0, description="Total input (prompt) tokens.")
    output_tokens: int = Field(default=0, description="Total output tokens, including reasoning tokens.")
    total_tokens: int = Field(default=0, description="Total tokens.")
    requests: int = Field(default=0, description="Number of model requests made.")


class TriageSession(BaseModel):
    """Working memory that persists through one triage pass.

    Carries the brief, the interpreted intent, the gathered facts, the evolving
    recommendation, the critic's feedback, and the round counter, so the optimizer
    can revise across rounds. The tool call log feeds the persisted audit log.
    """

    brief_text: str
    candidate_level: str
    intent: DesignIntentProfile | None = None
    facts: LevelFacts | None = None
    recommendation: TriageRecommendation | None = None
    critique: Critique | None = None
    round_count: int = Field(default=1, description="Number of triage rounds run.")
    critic_feedback_history: list[str] = Field(
        default_factory=list,
        description="The critic's feedback from each round that sent the recommendation back.",
    )
    decision: TriageAction | None = Field(
        default=None,
        description="The final action after the safety floor.",
    )
    tool_call_log: list[ToolCallLogEntry] = Field(default_factory=list)
    transcript: list[MessageEntry] = Field(
        default_factory=list,
        description="Full chat style transcript of every agent message, tool call, and decision.",
    )
    token_usage: TokenUsage | None = Field(
        default=None,
        description="Token usage accumulated across the pass, for cost tracking.",
    )


class ScenarioDefinition(BaseModel):
    """A controlled evaluation scenario: a brief, a candidate, and expected behavior."""

    scenario_id: str = Field(description="Stable identifier such as S1.")
    name: str = Field(description="Short human readable scenario name.")
    brief_text: str = Field(description="The natural language design brief.")
    candidate_file: str = Field(description="Candidate level filename under data/candidate_levels.")
    expected_action: TriageAction = Field(description="The action the scenario is expected to yield.")
    acceptable_actions: list[TriageAction] = Field(
        default_factory=list,
        description="Defensible actions for fair scoring; empty means only the expected action counts.",
    )
    notes: str = Field(default="", description="What the scenario is meant to exercise.")


class ScenarioResult(BaseModel):
    """Outcome of running one scenario through the triage workflow."""

    scenario_id: str
    name: str
    expected_action: TriageAction
    actual_action: TriageAction
    readiness: ReadinessLevel
    match_expected: bool = Field(description="True when actual_action equals expected_action.")
    rounds: int = Field(description="Number of triage rounds the pass took.")
    key_reason: str = Field(description="One line summary of the driving rationale.")

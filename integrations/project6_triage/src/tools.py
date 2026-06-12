"""Agent facing tool layer and tool call logging.

Exposes the deterministic analysis tools under clear agent facing names, bundles
them into a single LevelFacts gather, lists them in a registry for the notebook,
and records every tool call (inputs and outputs) for the audit log. The tools
report facts only; they never decide and never edit the level.
"""

from __future__ import annotations

from typing import Any

from pydantic_ai.messages import (
    RetryPromptPart,
    SystemPromptPart,
    TextPart,
    ThinkingPart,
    ToolCallPart,
    ToolReturnPart,
    UserPromptPart,
)

from src.analysis_tools import (
    analyze_pacing,
    detect_difficulty_spike,
    detect_safe_zone,
    estimate_difficulty,
    measure_novelty,
    validate_level,
)
from src.models import (
    DifficultyResult,
    LevelFacts,
    MessageEntry,
    NoveltyResult,
    PacingResult,
    SafeZoneResult,
    SpikeResult,
    ToolCallLogEntry,
    ValidationResult,
)

_MAX_CONTENT = 4000


def validate_candidate_level(level_text: str) -> ValidationResult:
    """Validate the candidate's structure, vocabulary, dimensions, and pipe integrity."""
    return validate_level(level_text)


def estimate_candidate_difficulty(level_text: str) -> DifficultyResult:
    """Estimate the candidate's heuristic, structural difficulty (not player validated)."""
    return estimate_difficulty(level_text)


def measure_candidate_novelty(level_text: str, reference_levels: list[str]) -> NoveltyResult:
    """Measure the candidate's novelty against the reference library."""
    return measure_novelty(level_text, reference_levels)


def analyze_candidate_pacing(level_text: str) -> PacingResult:
    """Analyze the candidate's challenge pacing across the opening, middle, and final thirds."""
    return analyze_pacing(level_text)


def detect_candidate_safe_zone(level_text: str) -> SafeZoneResult:
    """Check whether the candidate opens with a safe zone before the first challenge."""
    return detect_safe_zone(level_text)


def detect_candidate_spike(level_text: str) -> SpikeResult:
    """Detect a localized difficulty spike (a gap combined with an enemy or cannon)."""
    return detect_difficulty_spike(level_text)


def gather_facts(level_text: str, reference_levels: list[str]) -> LevelFacts:
    """Run every analysis tool and return the bundled facts about the candidate."""
    return LevelFacts(
        validation=validate_candidate_level(level_text),
        difficulty=estimate_candidate_difficulty(level_text),
        novelty=measure_candidate_novelty(level_text, reference_levels),
        pacing=analyze_candidate_pacing(level_text),
        safe_zone=detect_candidate_safe_zone(level_text),
        spike=detect_candidate_spike(level_text),
    )


TOOL_REGISTRY: list[dict[str, str]] = [
    {"tool": "validate_candidate_level", "purpose": "Check structure, vocabulary, dimensions, and pipe integrity"},
    {"tool": "estimate_candidate_difficulty", "purpose": "Estimate heuristic, structural difficulty"},
    {"tool": "measure_candidate_novelty", "purpose": "Measure similarity and derivative risk vs the reference library"},
    {"tool": "analyze_candidate_pacing", "purpose": "Describe challenge pacing across the segment"},
    {"tool": "detect_candidate_safe_zone", "purpose": "Check for an opening safe zone for beginners"},
    {"tool": "detect_candidate_spike", "purpose": "Find a localized low leniency difficulty spike"},
]


class ToolLog:
    """Records each tool call for transparency and the persisted audit log."""

    def __init__(self) -> None:
        """Start an empty tool call log."""
        self.entries: list[ToolCallLogEntry] = []

    def record(self, tool_name: str, inputs: dict[str, Any], output: Any) -> None:
        """Record one tool call, serializing a Pydantic output to a plain dict."""
        if hasattr(output, "model_dump"):
            outputs = output.model_dump()
        elif isinstance(output, dict):
            outputs = output
        else:
            outputs = {"value": output}
        self.entries.append(
            ToolCallLogEntry(tool_name=tool_name, inputs=inputs, outputs=outputs)
        )


def _as_text(content: Any) -> str:
    """Coerce any message content to a readable, length capped string."""
    text = content if isinstance(content, str) else str(content)
    return text if len(text) <= _MAX_CONTENT else text[:_MAX_CONTENT] + " ...[truncated]"


def _tool_args(part: ToolCallPart) -> dict[str, Any]:
    """Best effort extraction of a tool call's arguments as a dict."""
    try:
        return part.args_as_dict()
    except Exception:
        return {"raw": _as_text(part.args)}


class Transcript:
    """Accumulates the full chat style transcript of one triage pass.

    It normalizes the Pydantic AI message history from each agent run into chat
    style entries (system, user, assistant, tool) and interleaves deterministic
    workflow events, so the session carries a complete record of what happened.
    """

    def __init__(self) -> None:
        """Start an empty transcript."""
        self.entries: list[MessageEntry] = []
        self._system_recorded: set[str] = set()

    def _add(self, agent: str, role: str, **fields: Any) -> None:
        """Append one entry with the next step number."""
        self.entries.append(MessageEntry(step=len(self.entries) + 1, agent=agent, role=role, **fields))

    def add_event(self, agent: str, content: str, role: str = "system", round: int | None = None) -> None:
        """Record a deterministic workflow event (facts, decision, safety floor)."""
        self._add(agent, role, round=round, content=content)

    def add_messages(self, messages: list[Any], agent: str, round: int | None = None) -> None:
        """Normalize Pydantic AI model messages into transcript entries.

        Each agent's static system prompt is recorded only once per pass to keep
        the log focused on the dynamic activity across rounds.
        """
        for message in messages:
            for part in getattr(message, "parts", []):
                if isinstance(part, SystemPromptPart):
                    if agent not in self._system_recorded:
                        self._system_recorded.add(agent)
                        self._add(agent, "system", round=round, content=_as_text(part.content))
                elif isinstance(part, UserPromptPart):
                    self._add(agent, "user", round=round, content=_as_text(part.content))
                elif isinstance(part, (ToolReturnPart, RetryPromptPart)):
                    self._add(
                        agent, "tool", round=round,
                        content=_as_text(part.content),
                        tool_name=part.tool_name,
                        tool_call_id=part.tool_call_id,
                    )
                elif isinstance(part, ThinkingPart):
                    if part.content and part.content.strip():
                        self._add(agent, "assistant", round=round, content="[thinking] " + _as_text(part.content))
                elif isinstance(part, TextPart):
                    if part.content and part.content.strip():
                        self._add(agent, "assistant", round=round, content=_as_text(part.content))
                elif isinstance(part, ToolCallPart):
                    self._add(
                        agent, "assistant", round=round,
                        tool_name=part.tool_name,
                        tool_args=_tool_args(part),
                        tool_call_id=part.tool_call_id,
                    )

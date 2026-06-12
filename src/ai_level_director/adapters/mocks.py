"""Mock adapters for building and testing the workflow without prior projects.

These return deterministic results so the whole orchestration can be exercised
without API keys, model loads, or GPU. The real Project 6 and Project 3 adapters
replace them later and must satisfy the same interfaces. The mock feedback adapter
uses a small keyword rule so demo feedback classifies in an intuitive way.
"""

from __future__ import annotations

from ai_level_director.domain.models import FeedbackResult, TriageResult

# Cues that make the mock classify feedback as negative; anything else is positive.
_NEGATIVE_CUES = (
    "unfair",
    "frustrating",
    "frustrate",
    "boring",
    "too hard",
    "too easy",
    "annoying",
    "hate",
    "bad",
    "broken",
    "confusing",
)

# Readiness label paired with each triage action for the mock result.
_READINESS_FOR_ACTION = {
    "accept_for_playtest": "ready_for_playtest",
    "flag_as_derivative_draft": "ready_for_playtest",
    "recommend_revision": "revise_before_playtest",
    "request_clarification": "not_ready",
    "reject_structural": "not_ready",
    "request_human_review": "not_ready",
}


class MockTriageAdapter:
    """A triage adapter that returns a configurable, deterministic result."""

    def __init__(self, action: str = "accept_for_playtest") -> None:
        """Create the mock with the triage action it should always return."""
        self.action = action

    def triage(
        self,
        design_brief: str,
        level_text: str,
        target_difficulty: str | None = None,
        novelty_preference: str | None = None,
    ) -> TriageResult:
        """Return a fixed triage result for the configured action."""
        return TriageResult(
            action=self.action,
            readiness=_READINESS_FOR_ACTION.get(self.action, "not_ready"),
            rationale="(mock) Deterministic triage result for workflow testing.",
            warnings=[],
            revision_recommendations=(
                ["(mock) Move the opening enemy back two tiles."]
                if self.action == "recommend_revision"
                else []
            ),
            playtest_questions=["(mock) Does the first jump feel fair?"],
            raw_payload={"mock": True, "action": self.action},
        )


class MockFeedbackAdapter:
    """A feedback adapter that classifies by a simple keyword rule."""

    def classify(self, feedback_text: str) -> FeedbackResult:
        """Return a positive or negative label based on negative keyword cues."""
        lowered = feedback_text.lower()
        sentiment = "negative" if any(cue in lowered for cue in _NEGATIVE_CUES) else "positive"
        return FeedbackResult(
            feedback_text=feedback_text,
            sentiment=sentiment,
            model_name="mock-feedback",
        )


class MockGeneratorAdapter:
    """A generator adapter that returns canned, valid level chunks instantly.

    It produces deterministic 14 row by 32 column grids so the service generation
    command can be tested without the real Project 5 model.
    """

    def generate(
        self,
        target_difficulty: str,
        n: int = 1,
        temperature: float = 1.2,
        seed: int | None = None,
    ) -> list[str]:
        """Return n simple valid level chunks."""
        chunk = "\n".join(["-" * 32] * 13 + ["X" * 32])
        return [chunk for _ in range(n)]

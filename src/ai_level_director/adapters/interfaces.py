"""Adapter interfaces for the integrated prior projects.

These are structural ``Protocol`` types: any object with matching methods satisfies
them, so a mock adapter and a real prior project adapter are interchangeable
without inheritance. The service depends on these interfaces, not on concrete
adapters, which is what lets the workflow be built and tested against mocks first
and have the real Project 6, 3, and 5 adapters slotted in later unchanged.
"""

from __future__ import annotations

from typing import Protocol

from ai_level_director.domain.models import FeedbackResult, TriageResult


class TriageAdapter(Protocol):
    """Triage a single candidate against the design brief (Project 6)."""

    def triage(
        self,
        design_brief: str,
        level_text: str,
        target_difficulty: str | None = None,
        novelty_preference: str | None = None,
    ) -> TriageResult:
        """Return a normalized triage result for the candidate."""
        ...


class FeedbackAdapter(Protocol):
    """Classify playtester feedback into a reception signal (Project 3)."""

    def classify(self, feedback_text: str) -> FeedbackResult:
        """Return a normalized feedback result for the text."""
        ...


class GeneratorAdapter(Protocol):
    """Generate candidate level chunks (Project 5)."""

    def generate(
        self,
        target_difficulty: str,
        n: int = 1,
        temperature: float = 1.2,
        seed: int | None = None,
    ) -> list[str]:
        """Return n generated candidate level texts for the target difficulty."""
        ...

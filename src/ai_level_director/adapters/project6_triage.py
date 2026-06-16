"""Project 6 triage adapter.

Wraps the Project 6 agentic triage system behind the TriageAdapter interface.
Project 6 is vendored under ``integrations/project6_triage/`` and imports its own
modules as ``from src.X``, so the adapter adds that directory to ``sys.path`` and
imports ``triage_candidate``. Project 6 stays the single triage authority; this
adapter only translates its rich ``TriageSession`` into the narrow Project 7
``TriageResult`` that the rest of the system depends on.

Live triage calls an OpenAI model and needs ``OPENAI_API_KEY`` (and optionally
``TRIAGE_MODEL``). The mock triage adapter remains the offline path for tests.
"""

from __future__ import annotations

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from ai_level_director.domain.models import TriageResult

# Repo root is three levels up: adapters -> ai_level_director -> src.
_REPO_ROOT = Path(__file__).resolve().parents[3]
_VENDOR_DIR = _REPO_ROOT / "integrations" / "project6_triage"
DEFAULT_REFERENCE_DIR = _VENDOR_DIR / "reference_levels"

# Project 6 chat models pin temperature 0 for reproducibility.
_DEFAULT_MODEL_SETTINGS = {"temperature": 0.0}


def _ensure_p6_importable() -> None:
    """Put the vendored Project 6 directory on the path so ``src`` resolves to it."""
    if str(_VENDOR_DIR) not in sys.path:
        sys.path.insert(0, str(_VENDOR_DIR))


def _load_reference_levels(reference_dir: Path | str) -> list[str]:
    """Load the reference library text files used by the novelty tool."""
    return [path.read_text(encoding="utf-8") for path in sorted(Path(reference_dir).glob("*.txt"))]


def _warnings_from_facts(facts) -> list[str]:
    """Derive short structural warnings from the deterministic facts."""
    warnings: list[str] = []
    if facts is None:
        return warnings
    if not facts.validation.is_valid:
        warnings.extend(facts.validation.fatal_errors)
    if facts.spike.has_spike:
        warnings.append("Localized difficulty spike detected.")
    if not facts.safe_zone.has_opening_safe_zone:
        warnings.append("No opening safe zone for the player to settle into.")
    return warnings


def map_session_to_result(session) -> TriageResult:
    """Translate a Project 6 TriageSession into a Project 7 TriageResult.

    The final action is the session decision (post safety floor), falling back to
    the recommendation's action. Revision edits and the prescription playtest
    question are flattened into the result's lists. The full Project 6 session is
    kept in ``raw_payload`` (minus the bulky transcript) for auditing. This stays a
    pure field mapping; the deliberation transcript and report are rendered in the
    adapter's ``triage`` method, where Project 6 is on the path.
    """
    recommendation = session.recommendation
    prescription = recommendation.prescription if recommendation else None

    revision_recommendations = (
        [edit.description for edit in prescription.suggested_edits] if prescription else []
    )
    playtest_questions = list(recommendation.playtest_questions) if recommendation else []
    if prescription and prescription.playtest_question:
        playtest_questions.append(prescription.playtest_question)

    action = session.decision or (recommendation.action if recommendation else "request_human_review")

    return TriageResult(
        action=str(action),
        readiness=str(recommendation.playtest_readiness) if recommendation else "not_ready",
        rationale=recommendation.diagnosis if recommendation else "",
        warnings=_warnings_from_facts(session.facts),
        revision_recommendations=revision_recommendations,
        playtest_questions=playtest_questions,
        raw_payload=session.model_dump(mode="json", exclude={"transcript"}),
    )


def _render_artifacts(session) -> tuple[str | None, str | None]:
    """Render the deliberation transcript and designer report from a triage session.

    These are supplementary observability artifacts. A rendering failure returns
    ``None`` so the triage decision itself is never lost to a reporting problem.
    """
    try:
        from src.report import format_transcript, generate_report  # vendored Project 6

        return format_transcript(session), generate_report(session)
    except Exception:
        return None, None


class Project6TriageAdapter:
    """Run a candidate through the Project 6 triage agent and normalize the result."""

    def __init__(
        self,
        reference_levels: list[str] | None = None,
        reference_dir: Path | str = DEFAULT_REFERENCE_DIR,
        model: str | None = None,
        model_settings: dict | None = _DEFAULT_MODEL_SETTINGS,
    ) -> None:
        """Load the vendored Project 6 entry point and the reference library."""
        # Force the local .env to win over any stale system credentials before the
        # agent constructs its OpenAI client.
        from ai_level_director.config import load_environment

        load_environment()
        _ensure_p6_importable()
        from src.models import TriageRequest  # vendored Project 6
        from src.workflow import triage_candidate  # vendored Project 6

        self._triage_candidate = triage_candidate
        self._TriageRequest = TriageRequest
        self._reference_levels = (
            reference_levels if reference_levels is not None else _load_reference_levels(reference_dir)
        )
        self.model = model
        self.model_settings = model_settings

    def triage(
        self,
        design_brief: str,
        level_text: str,
        target_difficulty: str | None = None,
        novelty_preference: str | None = None,
    ) -> TriageResult:
        """Triage one candidate and return a normalized TriageResult.

        The session's target difficulty and novelty preference, when provided, are
        appended to the brief so the Project 6 intent interpreter can use them.
        """
        brief = self._augment_brief(design_brief, target_difficulty, novelty_preference)
        request = self._TriageRequest(brief_text=brief, candidate_level=level_text)
        session = self._run_pass(request)
        result = map_session_to_result(session)
        result.transcript_text, result.report_text = _render_artifacts(session)
        return result

    def _run_pass(self, request):
        """Run the Project 6 triage pass, off thread if an event loop is running.

        Project 6 uses Pydantic AI's ``run_sync``, which cannot run inside an
        already running event loop (a Jupyter kernel, for example). When a loop is
        running, the pass executes in a worker thread that gets its own fresh loop;
        otherwise it runs directly (scripts and the Gradio worker threads). This
        adapts Project 6's synchronous API to async callers without modifying it.
        """
        def _call():
            return self._triage_candidate(
                request,
                self._reference_levels,
                model=self.model,
                model_settings=self.model_settings,
            )

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return _call()
        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(_call).result()

    @staticmethod
    def _augment_brief(
        brief: str, target_difficulty: str | None, novelty_preference: str | None
    ) -> str:
        """Append difficulty and novelty context to the brief when provided."""
        extras = []
        if target_difficulty:
            extras.append(f"Target difficulty: {target_difficulty}.")
        if novelty_preference:
            extras.append(f"Novelty preference: {novelty_preference}.")
        return brief if not extras else f"{brief}\n\n{' '.join(extras)}"

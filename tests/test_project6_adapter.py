"""Tests for the Project 6 triage adapter.

The session to result mapping is tested with a lightweight fake session, so it
needs no Project 6 import and no API call. A separate test constructs the real
adapter offline to confirm the vendored Project 6 imports and the reference
library loads. The live triage call (which needs an API key and costs money) is
not exercised here; the mock triage adapter covers the workflow offline.
"""

from __future__ import annotations

from types import SimpleNamespace

from ai_level_director.adapters.project6_triage import (
    Project6TriageAdapter,
    map_session_to_result,
)


def fake_session(decision="recommend_revision", with_prescription=True, is_valid=True):
    """Build a duck typed stand in for a Project 6 TriageSession."""
    prescription = None
    if with_prescription:
        edit = SimpleNamespace(description="Move the opening enemy back two tiles.", reason="fairness")
        prescription = SimpleNamespace(
            suggested_edits=[edit],
            playtest_question="Does the first jump feel fair?",
        )
    recommendation = SimpleNamespace(
        action="recommend_revision",
        diagnosis="An enemy sits on the first landing.",
        tradeoff_reasoning=["low novelty is acceptable here"],
        prescription=prescription,
        playtest_readiness="revise_before_playtest",
        playtest_questions=["Is the pacing right?"],
        confidence="moderate",
    )
    facts = SimpleNamespace(
        validation=SimpleNamespace(is_valid=is_valid, fatal_errors=[] if is_valid else ["broken pipe"]),
        spike=SimpleNamespace(has_spike=True),
        safe_zone=SimpleNamespace(has_opening_safe_zone=False),
    )
    session = SimpleNamespace(decision=decision, recommendation=recommendation, facts=facts)
    session.model_dump = lambda **kwargs: {"decision": decision}
    return session


def test_mapping_core_fields():
    result = map_session_to_result(fake_session())
    assert result.action == "recommend_revision"
    assert result.readiness == "revise_before_playtest"
    assert result.rationale == "An enemy sits on the first landing."
    assert result.raw_payload == {"decision": "recommend_revision"}


def test_mapping_flattens_prescription():
    result = map_session_to_result(fake_session())
    assert result.revision_recommendations == ["Move the opening enemy back two tiles."]
    # The recommendation questions plus the prescription question.
    assert result.playtest_questions == ["Is the pacing right?", "Does the first jump feel fair?"]


def test_mapping_without_prescription():
    result = map_session_to_result(fake_session(with_prescription=False))
    assert result.revision_recommendations == []
    assert result.playtest_questions == ["Is the pacing right?"]


def test_warnings_from_facts():
    result = map_session_to_result(fake_session(is_valid=False))
    assert "broken pipe" in result.warnings
    assert any("difficulty spike" in w for w in result.warnings)
    assert any("safe zone" in w for w in result.warnings)


def test_decision_falls_back_to_recommendation_action():
    result = map_session_to_result(fake_session(decision=None))
    assert result.action == "recommend_revision"


def _has_running_loop() -> bool:
    import asyncio

    try:
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        return False


def test_triage_dispatches_off_a_running_event_loop():
    # Inside a running loop (like a Jupyter kernel), the pass must run in a worker
    # thread that has no running loop, so Pydantic AI run_sync works. The P6 pass is
    # stubbed so no API call is made.
    import asyncio

    adapter = Project6TriageAdapter()
    captured = {}

    def fake_pass(request, refs, model=None, model_settings=None):
        captured["loop_in_worker"] = _has_running_loop()
        return fake_session()

    adapter._triage_candidate = fake_pass

    async def driver():
        return adapter.triage("brief", "----\nXXXX")

    result = asyncio.run(driver())
    assert result.action == "recommend_revision"  # mapped from the fake session
    assert captured["loop_in_worker"] is False  # ran in a fresh thread, no loop


def test_real_adapter_constructs_offline():
    # Constructs the real adapter: imports the vendored Project 6 and loads the
    # reference library. No API call is made.
    adapter = Project6TriageAdapter()
    assert len(adapter._reference_levels) == 10
    assert callable(adapter._triage_candidate)
    assert hasattr(adapter, "triage")

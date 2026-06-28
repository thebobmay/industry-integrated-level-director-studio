"""Service tests for adding generated candidates, using the mock generator.

These verify the service wiring (the generation command, id assignment, source,
and provenance metadata) without the cost of the real Project 5 model. The mock
generator returns canned valid chunks instantly. The real generator is covered in
its own adapter test.
"""

from __future__ import annotations

import pytest

from ai_level_director.adapters.mocks import MockGeneratorAdapter, MockTriageAdapter
from ai_level_director.workflow.service import LevelDirectorService


def make_service(tmp_path) -> LevelDirectorService:
    """Build a service wired with the mock generator and triage adapters."""
    return LevelDirectorService(
        output_root=tmp_path,
        generator_adapter=MockGeneratorAdapter(),
        triage_adapter=MockTriageAdapter("accept_for_playtest"),
    )


def test_add_generated_requires_adapter(tmp_path):
    service = LevelDirectorService(output_root=tmp_path)  # no generator
    service.start_session("brief", session_id="S1")
    with pytest.raises(RuntimeError):
        service.add_generated_candidate("S1")


def test_add_generated_candidates(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", target_difficulty="easy", session_id="S1")
    session = service.add_generated_candidate("S1", n=2, seed=1)

    generated = [c for c in session.candidates if c.source == "generated"]
    assert [c.candidate_id for c in generated] == ["G-001", "G-002"]
    assert all(c.workflow_state == "draft" for c in generated)
    assert generated[0].level_path  # artifact saved


def test_generated_candidate_records_provenance(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", target_difficulty="easy", session_id="S1")
    session = service.add_generated_candidate("S1", n=1, temperature=1.1, seed=42)

    meta = session.candidates[0].generation_metadata
    assert meta["source_project"] == "Project 5"
    assert meta["target_difficulty"] == "easy"
    assert meta["temperature"] == 1.1
    assert meta["seed"] == 42


def test_difficulty_defaults_to_session_target(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", target_difficulty="hard", session_id="S1")
    session = service.add_generated_candidate("S1", n=1)
    assert session.candidates[0].generation_metadata["target_difficulty"] == "hard"


def test_generated_candidate_can_be_triaged(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", target_difficulty="easy", session_id="S1")
    service.add_generated_candidate("S1", n=1, seed=1)
    session = service.run_triage("S1", "G-001")
    assert session.candidates[0].workflow_state == "ready_for_playtest"

"""Unit tests for candidate creation from uploaded and sample sources.

These check id assignment, the shape of a newly created candidate (draft state, a
single creation event), and that saving artifacts writes the level text and a
preview image and records their paths on the candidate.
"""

from __future__ import annotations

from pathlib import Path

from ai_level_director.workflow.candidate_sources import (
    make_sample_candidate,
    make_uploaded_candidate,
    next_candidate_id,
    save_candidate_artifacts,
)

TS = "2026-06-11T12:00:00+00:00"
LEVEL = "----\nXXXX"


def test_next_candidate_id_starts_at_one():
    assert next_candidate_id([], "uploaded") == "U-001"
    assert next_candidate_id([], "sample") == "S-001"


def test_next_candidate_id_numbers_per_source_independently():
    existing = ["U-001", "U-002", "S-001", "G-001"]
    assert next_candidate_id(existing, "uploaded") == "U-003"
    assert next_candidate_id(existing, "sample") == "S-002"
    assert next_candidate_id(existing, "generated") == "G-002"


def test_uploaded_candidate_shape():
    candidate = make_uploaded_candidate(LEVEL, "U-001", created_at=TS)
    assert candidate.source == "uploaded"
    assert candidate.workflow_state == "draft"
    assert candidate.iteration_number == 1
    assert candidate.created_at == TS and candidate.updated_at == TS
    assert len(candidate.history) == 1
    assert candidate.history[0].event_type == "uploaded"
    assert candidate.history[0].candidate_id == "U-001"


def test_sample_candidate_records_created_event():
    candidate = make_sample_candidate(LEVEL, "S-001", created_at=TS)
    assert candidate.source == "sample"
    assert candidate.history[0].event_type == "created"


def test_build_candidate_defaults_timestamp_when_absent():
    candidate = make_uploaded_candidate(LEVEL, "U-001")
    assert candidate.created_at  # a timestamp was generated
    assert candidate.created_at == candidate.updated_at


def test_save_candidate_artifacts_writes_text(tmp_path):
    candidate = make_uploaded_candidate(LEVEL, "U-001", created_at=TS)
    saved = save_candidate_artifacts(candidate, "S-001", output_root=tmp_path)

    assert saved.level_path and Path(saved.level_path).exists()
    assert Path(saved.level_path).read_text(encoding="utf-8") == LEVEL
    # Image previews are deferred, so no preview path is set yet.
    assert saved.rendered_preview_path is None
    # The original candidate is unchanged; a copy carries the new path.
    assert candidate.level_path is None

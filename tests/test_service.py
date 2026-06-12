"""Integration tests for the LevelDirectorService session lifecycle.

These exercise the facade end to end against a temporary output root: a session is
created and persisted, candidates are added from the uploaded and sample sources,
state is saved after each command, and creation events reach the event log.
"""

from __future__ import annotations

import pytest

from ai_level_director.workflow.service import LevelDirectorService

LEVEL = "----\nXXXX"


def make_service(tmp_path) -> LevelDirectorService:
    """Build a service rooted at the test's temporary directory."""
    return LevelDirectorService(output_root=tmp_path)


def test_start_session_persists_and_returns(tmp_path):
    service = make_service(tmp_path)
    session = service.start_session("An easy beginner segment.", target_difficulty="easy")
    assert session.session_status == "active"
    assert session.candidates == []
    # The session was saved and reloads to an equal object.
    assert service.load_session(session.session_id) == session


def test_start_session_accepts_explicit_id(tmp_path):
    service = make_service(tmp_path)
    session = service.start_session("brief", session_id="S-FIXED")
    assert session.session_id == "S-FIXED"
    assert service.store.session_exists("S-FIXED")


def test_add_uploaded_candidate(tmp_path):
    service = make_service(tmp_path)
    session = service.start_session("brief", session_id="S1")
    updated = service.add_uploaded_candidate("S1", LEVEL, title="My level")

    assert len(updated.candidates) == 1
    candidate = updated.candidates[0]
    assert candidate.candidate_id == "U-001"
    assert candidate.source == "uploaded"
    assert candidate.title == "My level"
    assert candidate.level_path  # artifact path recorded


def test_added_candidate_is_persisted(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    # A fresh load from the store reflects the added candidate.
    reloaded = service.load_session("S1")
    assert [c.candidate_id for c in reloaded.candidates] == ["U-001"]


def test_candidate_numbering_per_source(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    service.add_uploaded_candidate("S1", LEVEL)
    session = service.add_sample_candidate("S1", LEVEL)
    ids = [c.candidate_id for c in session.candidates]
    assert ids == ["U-001", "U-002", "S-001"]


def test_creation_events_reach_the_event_log(tmp_path):
    service = make_service(tmp_path)
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    service.add_sample_candidate("S1", LEVEL)

    events = service.store.read_events("S1")
    assert [e.event_type for e in events] == ["uploaded", "created"]
    assert [e.candidate_id for e in events] == ["U-001", "S-001"]


def test_load_missing_session_raises(tmp_path):
    service = make_service(tmp_path)
    with pytest.raises(FileNotFoundError):
        service.load_session("nope")

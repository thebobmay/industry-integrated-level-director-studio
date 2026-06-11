"""Unit tests for the session store and path helpers.

Every test writes to pytest's ``tmp_path`` so the real ``outputs/`` tree is never
touched. The key guarantees: a session survives a save and load round trip
unchanged, the event log is append only, and reading an absent log is safe.
"""

from __future__ import annotations

import pytest

from ai_level_director.domain.events import CandidateEvent
from ai_level_director.domain.models import DesignSession, LevelCandidate
from ai_level_director.storage import paths
from ai_level_director.storage.session_store import SessionStore

TS = "2026-06-11T12:00:00+00:00"


def make_session() -> DesignSession:
    """Build a session with one candidate for persistence tests."""
    candidate = LevelCandidate(
        candidate_id="G-001",
        title="Test candidate",
        source="generated",
        level_text="----\nXXXX",
        created_at=TS,
        updated_at=TS,
    )
    return DesignSession(
        session_id="S-001",
        design_brief="An easy beginner friendly segment.",
        candidates=[candidate],
        created_at=TS,
        updated_at=TS,
    )


def make_event(event_id: str, event_type="created", summary="created") -> CandidateEvent:
    """Build a candidate event for event log tests."""
    return CandidateEvent(
        event_id=event_id,
        timestamp=TS,
        event_type=event_type,
        candidate_id="G-001",
        summary=summary,
    )


def test_save_writes_under_configured_root(tmp_path):
    store = SessionStore(tmp_path)
    path = store.save_session(make_session())
    assert path == paths.session_path("S-001", tmp_path)
    assert path.exists()


def test_save_and_load_round_trip(tmp_path):
    store = SessionStore(tmp_path)
    session = make_session()
    store.save_session(session)
    restored = store.load_session("S-001")
    assert restored == session


def test_session_exists(tmp_path):
    store = SessionStore(tmp_path)
    assert not store.session_exists("S-001")
    store.save_session(make_session())
    assert store.session_exists("S-001")


def test_load_missing_session_raises(tmp_path):
    store = SessionStore(tmp_path)
    with pytest.raises(FileNotFoundError):
        store.load_session("does-not-exist")


def test_append_event_is_append_only(tmp_path):
    store = SessionStore(tmp_path)
    store.append_event("S-001", make_event("E1", summary="first"))
    store.append_event("S-001", make_event("E2", event_type="triaged", summary="second"))

    events = store.read_events("S-001")
    assert [e.event_id for e in events] == ["E1", "E2"]
    assert events[1].event_type == "triaged"


def test_read_events_empty_when_no_log(tmp_path):
    store = SessionStore(tmp_path)
    assert store.read_events("S-001") == []


def test_event_log_and_session_are_separate_files(tmp_path):
    store = SessionStore(tmp_path)
    store.save_session(make_session())
    store.append_event("S-001", make_event("E1"))
    assert paths.session_path("S-001", tmp_path).exists()
    assert paths.event_log_path("S-001", tmp_path).exists()

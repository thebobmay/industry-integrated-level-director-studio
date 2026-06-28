"""Adapter tests for the real Project 3 feedback classifier.

These load the actual trained artifacts from ``models/project3_feedback/``, so they
exercise the real model, not a mock. The phrases were verified to classify stably.
They also confirm the adapter satisfies the FeedbackAdapter interface well enough to
drive the service end to end (positive completes, negative needs revision).
"""

from __future__ import annotations

from ai_level_director.adapters.project3_feedback import Project3FeedbackAdapter
from ai_level_director.workflow.service import LevelDirectorService

LEVEL = "----\nXXXX"


def test_positive_feedback_classified_positive():
    adapter = Project3FeedbackAdapter()
    result = adapter.classify("This level was fun and fair, I really enjoyed it.")
    assert result.sentiment == "positive"
    assert result.model_name == "project3-tfidf-linear-svm"


def test_negative_feedback_classified_negative():
    adapter = Project3FeedbackAdapter()
    result = adapter.classify("The first jump felt unfair and frustrating.")
    assert result.sentiment == "negative"


def test_result_has_no_confidence_field():
    # The LinearSVC has no calibrated probability, so FeedbackResult carries none.
    result = Project3FeedbackAdapter().classify("A solid, enjoyable segment.")
    assert not hasattr(result, "confidence")


def test_real_adapter_drives_service_to_complete(tmp_path):
    # The real adapter is interchangeable with the mock via the FeedbackAdapter
    # interface, so the full loop runs to completion on positive feedback.
    from ai_level_director.adapters.mocks import MockTriageAdapter

    service = LevelDirectorService(
        output_root=tmp_path,
        triage_adapter=MockTriageAdapter("accept_for_playtest"),
        feedback_adapter=Project3FeedbackAdapter(),
    )
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    service.run_triage("S1", "U-001")
    service.send_to_playtest("S1", "U-001")
    session = service.submit_feedback("S1", "U-001", "Great pacing, smooth and rewarding.")
    assert session.candidates[0].workflow_state == "complete"


def test_real_adapter_drives_service_to_revision(tmp_path):
    from ai_level_director.adapters.mocks import MockTriageAdapter

    service = LevelDirectorService(
        output_root=tmp_path,
        triage_adapter=MockTriageAdapter("accept_for_playtest"),
        feedback_adapter=Project3FeedbackAdapter(),
    )
    service.start_session("brief", session_id="S1")
    service.add_uploaded_candidate("S1", LEVEL)
    service.run_triage("S1", "U-001")
    service.send_to_playtest("S1", "U-001")
    session = service.submit_feedback("S1", "U-001", "Boring and way too hard, I hated it.")
    assert session.candidates[0].workflow_state == "revision_needed"

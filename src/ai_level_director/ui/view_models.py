"""View models for the Gradio UI.

These convert domain objects into the tables and Markdown the UI displays. They are
pure functions over session state, so the UI callbacks stay thin and these can be
unit tested without Gradio.
"""

from __future__ import annotations

import pandas as pd

from ai_level_director.domain.models import DesignSession, LevelCandidate
from ai_level_director.rendering.ascii_renderer import render_level_ascii

BOARD_COLUMNS = [
    "candidate_id",
    "title",
    "source",
    "state",
    "triage_action",
    "readiness",
    "feedback",
    "main_warning",
    "next_step",
]

# UI facing next step suggestion per candidate state.
_NEXT_STEP = {
    "draft": "Run triage",
    "triaged": "Review triage result",
    "ready_for_playtest": "Send to playtest",
    "sent_to_playtest": "Awaiting playtester feedback",
    "feedback_received": "Review feedback",
    "revision_needed": "Create a revised candidate",
    "clarification_needed": "Clarify the brief, then revise",
    "structural_rejected": "Rejected for structural reasons",
    "derivative_review_needed": "Human originality review",
    "human_review_needed": "Human review",
    "complete": "Complete",
    "archived": "Archived",
}


def _latest_feedback(candidate: LevelCandidate) -> str:
    """Most recent effective feedback sentiment, or a dash.

    A designer override takes precedence over the classifier label, so the board
    shows the decision of record rather than the model's original call.
    """
    if not candidate.feedback_records:
        return "-"
    return candidate.feedback_records[-1].decision_sentiment


def _main_warning(candidate: LevelCandidate) -> str:
    """First triage warning, or a dash."""
    triage = candidate.triage_result
    if triage and triage.warnings:
        return triage.warnings[0]
    return "-"


def _board_row(candidate: LevelCandidate) -> dict:
    """Build one candidate board row."""
    triage = candidate.triage_result
    return {
        "candidate_id": candidate.candidate_id,
        "title": candidate.title,
        "source": candidate.source,
        "state": candidate.workflow_state,
        "triage_action": triage.action if triage else "-",
        "readiness": triage.readiness if triage else "-",
        "feedback": _latest_feedback(candidate),
        "main_warning": _main_warning(candidate),
        "next_step": _NEXT_STEP.get(candidate.workflow_state, "-"),
    }


def candidate_board_view(session: DesignSession) -> pd.DataFrame:
    """Return the candidate board as a DataFrame, one row per candidate."""
    rows = [_board_row(c) for c in session.candidates]
    return pd.DataFrame(rows, columns=BOARD_COLUMNS)


def playtest_queue_view(session: DesignSession) -> pd.DataFrame:
    """Return only the candidates currently sent to playtest."""
    rows = [
        _board_row(c) for c in session.candidates if c.workflow_state == "sent_to_playtest"
    ]
    return pd.DataFrame(rows, columns=BOARD_COLUMNS)


def candidate_ids(session: DesignSession) -> list[str]:
    """List all candidate ids in the session."""
    return [c.candidate_id for c in session.candidates]


def find_candidate(session: DesignSession, candidate_id: str) -> LevelCandidate | None:
    """Return the named candidate, or None."""
    for candidate in session.candidates:
        if candidate.candidate_id == candidate_id:
            return candidate
    return None


def candidate_detail_view(session: DesignSession, candidate_id: str | None) -> dict:
    """Return the Markdown blocks and raw level text for a candidate detail panel."""
    blank = {
        "metadata_markdown": "_No candidate selected._",
        "raw_level_text": "",
        "triage_markdown": "",
        "feedback_markdown": "",
        "history_markdown": "",
    }
    if not candidate_id:
        return blank
    candidate = find_candidate(session, candidate_id)
    if candidate is None:
        return blank

    meta = [
        f"### {candidate.candidate_id}: {candidate.title}",
        f"- Source: {candidate.source}",
        f"- State: {candidate.workflow_state}",
        f"- Iteration: {candidate.iteration_number}",
    ]
    if candidate.parent_candidate_id:
        meta.append(f"- Revised from: {candidate.parent_candidate_id}")
    if candidate.source == "generated" and candidate.generation_metadata:
        meta.append(f"- Generation: {candidate.generation_metadata}")

    triage = candidate.triage_result
    if triage:
        triage_lines = [
            f"**Triage:** {triage.action} (readiness: {triage.readiness})",
            "",
            triage.rationale,
        ]
        if triage.warnings:
            triage_lines += ["", "**Warnings**"] + [f"- {w}" for w in triage.warnings]
        if triage.revision_recommendations:
            triage_lines += ["", "**Revision recommendations**"] + [
                f"- {r}" for r in triage.revision_recommendations
            ]
        if triage.playtest_questions:
            triage_lines += ["", "**Playtest questions**"] + [
                f"- {q}" for q in triage.playtest_questions
            ]
        triage_markdown = "\n".join(triage_lines)
    else:
        triage_markdown = "_Not triaged yet._"

    if candidate.feedback_records:
        feedback_lines = []
        for r in candidate.feedback_records:
            feedback_lines.append(f"- [{r.feedback_result.sentiment}] {r.feedback_text}")
            if r.warning:
                feedback_lines.append(f"  - *{r.warning}*")
            if r.designer_override and r.designer_override != r.feedback_result.sentiment:
                feedback_lines.append(
                    f"  - *Designer corrected this to {r.designer_override}.*"
                )
        feedback_markdown = "\n".join(feedback_lines)
    else:
        feedback_markdown = "_No feedback yet._"

    if candidate.history:
        history_markdown = "\n".join(
            f"- {e.timestamp} {e.event_type}: {e.summary}" for e in candidate.history
        )
    else:
        history_markdown = "_No history._"

    return {
        "metadata_markdown": "\n".join(meta),
        "raw_level_text": render_level_ascii(candidate.level_text),
        "triage_markdown": triage_markdown,
        "feedback_markdown": feedback_markdown,
        "history_markdown": history_markdown,
    }


def session_summary_view(session: DesignSession) -> str:
    """Return a short Markdown summary of the session for the reports tab."""
    states = ", ".join(f"{c.candidate_id}: {c.workflow_state}" for c in session.candidates)
    return "\n".join(
        [
            f"**Session** `{session.session_id}` ({session.session_status})",
            f"- Brief: {session.design_brief}",
            f"- Target difficulty: {session.target_difficulty or 'unspecified'}",
            f"- Candidates: {len(session.candidates)}",
            f"- States: {states or 'none yet'}",
        ]
    )


def event_timeline_markdown(events) -> str:
    """Render a session event log (list of CandidateEvent) as a Markdown timeline."""
    if not events:
        return "_No events yet._"
    return "\n".join(
        f"- {e.timestamp} {(e.candidate_id or '-')} {e.event_type}: {e.summary}"
        for e in events
    )

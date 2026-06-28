"""Markdown session report assembly.

Builds a reviewer facing report from a DesignSession: a session summary, a
candidate table, per candidate detail, and a fixed limitations section. This is
pure formatting over the session state, with no model calls, so the numbers in the
report are ground truth from the stored session.
"""

from __future__ import annotations

from collections import Counter

from ai_level_director.domain.models import DesignSession, LevelCandidate

# Fixed responsible use disclosures included in every report.
_LIMITATIONS = [
    "Generated candidates are drafts, not final assets. They can be derivative or "
    "too similar to the generator's training corpus, so novelty and derivative risk "
    "are flagged rather than hidden.",
    "Playtest feedback classification is a broad reception signal, not a complete "
    "playtest analysis. It returns a label only, with no calibrated confidence, and "
    "does not explain exact design causes.",
    "Heuristic difficulty is a structural estimate, not player validated difficulty.",
    "The system is advisory and designer governed. It never edits or finalizes a "
    "level on its own, and it does not claim to predict whether a level is fun.",
]


def _summary_section(session: DesignSession) -> str:
    """Render the session level summary block."""
    lines = [
        "## Session",
        "",
        f"- Session ID: `{session.session_id}`",
        f"- Status: {session.session_status}",
        f"- Design brief: {session.design_brief}",
        f"- Target difficulty: {session.target_difficulty or 'unspecified'}",
        f"- Novelty preference: {session.novelty_preference or 'unspecified'}",
        f"- Candidates: {len(session.candidates)}",
        f"- Created: {session.created_at}",
        f"- Updated: {session.updated_at}",
    ]
    return "\n".join(lines)


def _state_counts_section(session: DesignSession) -> str:
    """Render a count of candidates by workflow state."""
    counts = Counter(c.workflow_state for c in session.candidates)
    lines = ["## Candidates by State", ""]
    if not counts:
        lines.append("No candidates yet.")
        return "\n".join(lines)
    for state, count in sorted(counts.items()):
        lines.append(f"- {state}: {count}")
    return "\n".join(lines)


def _main_warning(candidate: LevelCandidate) -> str:
    """Pick a single short warning for the candidate table."""
    triage = candidate.triage_result
    if triage and triage.warnings:
        return triage.warnings[0]
    return ""


def _latest_feedback(candidate: LevelCandidate) -> str:
    """Return the most recent effective feedback sentiment, or a dash.

    A designer override is the decision of record, so it takes precedence over the
    classifier's original label.
    """
    if not candidate.feedback_records:
        return "-"
    return candidate.feedback_records[-1].decision_sentiment


def _candidate_table(session: DesignSession) -> str:
    """Render the candidate board as a Markdown table."""
    header = (
        "| ID | Title | Source | State | Triage | Readiness | Feedback | Warning |\n"
        "|---|---|---|---|---|---|---|---|"
    )
    if not session.candidates:
        return "## Candidate Summary\n\nNo candidates yet."
    rows = []
    for c in session.candidates:
        triage = c.triage_result
        rows.append(
            f"| {c.candidate_id} | {c.title} | {c.source} | {c.workflow_state} | "
            f"{triage.action if triage else '-'} | {triage.readiness if triage else '-'} | "
            f"{_latest_feedback(c)} | {_main_warning(c) or '-'} |"
        )
    return "## Candidate Summary\n\n" + header + "\n" + "\n".join(rows)


def _candidate_detail(candidate: LevelCandidate) -> str:
    """Render the full detail block for one candidate."""
    lines = [
        f"### {candidate.candidate_id}: {candidate.title} ({candidate.source})",
        "",
        f"- State: {candidate.workflow_state}",
        f"- Iteration: {candidate.iteration_number}",
    ]
    if candidate.parent_candidate_id:
        lines.append(f"- Revised from: {candidate.parent_candidate_id}")
    if candidate.source == "generated" and candidate.generation_metadata:
        meta = candidate.generation_metadata
        lines.append(f"- Generation: {meta}")

    triage = candidate.triage_result
    if triage:
        lines += [
            "",
            f"**Triage:** {triage.action} (readiness: {triage.readiness})",
            "",
            f"{triage.rationale}",
        ]
        if triage.warnings:
            lines += ["", "Warnings:"] + [f"- {w}" for w in triage.warnings]
        if triage.revision_recommendations:
            lines += ["", "Revision recommendations:"] + [
                f"- {r}" for r in triage.revision_recommendations
            ]
        if triage.playtest_questions:
            lines += ["", "Playtest questions:"] + [
                f"- {q}" for q in triage.playtest_questions
            ]

    if candidate.feedback_records:
        lines += ["", "Feedback:"]
        for record in candidate.feedback_records:
            lines.append(
                f"- [{record.feedback_result.sentiment}] {record.feedback_text}"
            )
            if record.warning:
                lines.append(f"  - {record.warning}")
            if record.designer_override and record.designer_override != record.feedback_result.sentiment:
                lines.append(f"  - Designer corrected this to {record.designer_override}.")

    if candidate.history:
        lines += ["", "History:"]
        for event in candidate.history:
            lines.append(f"- {event.timestamp} {event.event_type}: {event.summary}")

    return "\n".join(lines)


def _limitations_section() -> str:
    """Render the fixed responsible use and limitations block."""
    lines = ["## Limitations and Responsible Use", ""]
    lines += [f"- {item}" for item in _LIMITATIONS]
    return "\n".join(lines)


def build_session_report(session: DesignSession) -> str:
    """Assemble the full Markdown session report from session state."""
    sections = [
        f"# AI Level Director Studio Session Report",
        _summary_section(session),
        _candidate_table(session),
        _state_counts_section(session),
    ]
    if session.candidates:
        details = ["## Candidate Details", ""]
        details += [_candidate_detail(c) for c in session.candidates]
        sections.append("\n\n".join(details))
    sections.append(_limitations_section())
    return "\n\n".join(sections) + "\n"

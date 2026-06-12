"""Report assembly.

Assembles the designer facing triage report from agent authored prose (the
Director's diagnosis, tradeoff reasoning, prescription, and playtest questions, and
the Critic's assessment) plus a deterministic factual appendix (exact metrics, the
tool call log, and the level grid). This module generates no narrative prose of its
own; it only lays out the agents' text and the ground truth facts, so reported
numbers cannot be hallucinated. Section headers and the fixed limitations notice
are the only static text.
"""

from __future__ import annotations

from pathlib import Path

from src.models import TriageSession

_LIMITATIONS = [
    "Difficulty is heuristic and structural, not player validated.",
    "This system is advisory. It never edits the level; the designer makes every change.",
    "The human designer makes the final decision.",
]


def _bullets(items: list[str]) -> str:
    """Render a list as markdown bullets, or a placeholder when empty."""
    return "\n".join(f"- {item}" for item in items) if items else "- (none)"


def generate_report(session: TriageSession) -> str:
    """Render a triage report for a completed session."""
    lines: list[str] = ["# AI Level Design Triage Report", ""]

    lines += ["## Design Brief", session.brief_text, ""]

    intent = session.intent
    if intent is not None:
        lines += [
            "## Interpreted Intent",
            f"- Target audience: {intent.target_audience}",
            f"- Difficulty target: {intent.difficulty_target}",
            f"- Novelty preference: {intent.novelty_preference}",
            f"- Desired feel: {', '.join(intent.desired_feel) or '(none)'}",
            f"- Hard constraints: {', '.join(intent.hard_constraints) or '(none)'}",
            f"- Soft preferences: {', '.join(intent.soft_preferences) or '(none)'}",
            f"- Detected conflicts: {', '.join(intent.detected_conflicts) or '(none)'}",
            "",
        ]

    rec = session.recommendation
    if rec is not None:
        lines += [
            "## Triage Decision",
            f"- Action: {session.decision}",
            f"- Playtest readiness: {rec.playtest_readiness}",
            f"- Confidence: {rec.confidence}",
            f"- Rounds: {session.round_count}",
            "",
            "## Diagnosis",
            rec.diagnosis,
            "",
            "## Tradeoff Reasoning",
            _bullets(rec.tradeoff_reasoning),
            "",
        ]
        if rec.prescription is not None:
            edits = [f"{edit.description} ({edit.reason})" for edit in rec.prescription.suggested_edits]
            lines += [
                "## Revision Prescription",
                _bullets(edits),
                "",
                f"Playtest question: {rec.prescription.playtest_question}",
                "",
            ]
        if rec.playtest_questions:
            lines += ["## Playtest Questions", _bullets(rec.playtest_questions), ""]

    critique = session.critique
    if critique is not None:
        lines += [
            "## Independent Critic",
            f"- Verdict: {critique.verdict}",
            critique.assessment,
        ]
        if critique.remaining_issues:
            lines += ["- Remaining issues:", *[f"  - {i}" for i in critique.remaining_issues]]
        if critique.constraint_violations:
            lines += ["- Constraint violations:", *[f"  - {v}" for v in critique.constraint_violations]]
        lines.append("")

    lines += _factual_appendix(session)
    lines += ["## Limitations", _bullets(_LIMITATIONS), ""]

    return "\n".join(lines).rstrip() + "\n"


def _factual_appendix(session: TriageSession) -> list[str]:
    """Render the deterministic factual appendix (facts, tool log, level grid)."""
    lines = ["## Factual Appendix (deterministic)"]
    facts = session.facts
    if facts is not None:
        d, n, p, sz, sp = facts.difficulty, facts.novelty, facts.pacing, facts.safe_zone, facts.spike
        lines += [
            "### Measured facts",
            f"- Valid: {facts.validation.is_valid}",
        ]
        if facts.validation.fatal_errors:
            lines.append(f"- Fatal errors: {', '.join(facts.validation.fatal_errors)}")
        if facts.validation.warnings:
            lines.append(f"- Warnings: {', '.join(facts.validation.warnings)}")
        lines += [
            f"- Difficulty: {d.difficulty_label} (score {d.difficulty_score}, longest gap {d.longest_gap})",
            f"- Novelty: {n.novelty_label} (nearest neighbour similarity {n.nearest_neighbor_similarity})",
            f"- Pacing: {p.flag} (opening {p.opening_intensity}, middle {p.middle_intensity}, final {p.final_intensity})",
            f"- Safe zone: {sz.has_opening_safe_zone} (first challenge column {sz.first_challenge_column})",
            f"- Difficulty spike: {sp.has_spike}",
        ]

    if session.tool_call_log:
        lines.append("### Tool call log")
        lines += [f"- {entry.tool_name}" for entry in session.tool_call_log]

    lines += [
        "### Candidate level",
        "```text",
        session.candidate_level,
        "```",
        "",
    ]
    return lines


def save_report(report_text: str, path: str | Path) -> None:
    """Write a report to a file, creating parent directories as needed."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(report_text, encoding="utf-8")


def format_transcript(session: TriageSession) -> str:
    """Render the full session transcript as a readable chat style log."""
    lines: list[str] = ["# Triage Transcript", "", f"Brief: {session.brief_text}", ""]
    for entry in session.transcript:
        tag = entry.agent if entry.round is None else f"{entry.agent} r{entry.round}"
        header = f"## [{entry.step}] {entry.role} ({tag})"
        if entry.tool_name and entry.tool_args is not None:
            lines += [header, f"tool call: {entry.tool_name}({entry.tool_args})", ""]
        elif entry.tool_name:
            lines += [header, f"tool result: {entry.tool_name}", "```text", entry.content or "", "```", ""]
        else:
            lines += [header, entry.content or "", ""]
    return "\n".join(lines)


def save_transcript(session: TriageSession, path: str | Path) -> None:
    """Write the readable session transcript to a file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(format_transcript(session), encoding="utf-8")

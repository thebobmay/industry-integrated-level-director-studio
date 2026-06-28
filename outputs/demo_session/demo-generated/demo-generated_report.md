# AI Level Director Studio Session Report

## Session

- Session ID: `demo-generated`
- Status: active
- Design brief: An easy, beginner friendly opening segment with a gentle first jump.
- Target difficulty: easy
- Novelty preference: unspecified
- Candidates: 1
- Created: 2026-06-27T22:56:32.515242+00:00
- Updated: 2026-06-27T22:56:47.344493+00:00

## Candidate Summary

| ID | Title | Source | State | Triage | Readiness | Feedback | Warning |
|---|---|---|---|---|---|---|---|
| G-001 | Generated candidate | generated | structural_rejected | reject_structural | not_ready | - | pipe top without a body or ground support |

## Candidates by State

- structural_rejected: 1

## Candidate Details



### G-001: Generated candidate (generated)

- State: structural_rejected
- Iteration: 1
- Generation: {'source_project': 'Project 5', 'target_difficulty': 'easy', 'temperature': 1.2, 'seed': 42}

**Triage:** reject_structural (readiness: not_ready)

The candidate level contains a structural error: a pipe top is present without a corresponding body or ground support. This is a fatal integrity issue that prevents playtesting.

Warnings:
- pipe top without a body or ground support

History:
- 2026-06-27T22:56:38.394087+00:00 generated: Candidate G-001 created from generated source.
- 2026-06-27T22:56:47.344493+00:00 triaged: Triaged: reject_structural -> structural_rejected.

## Limitations and Responsible Use

- Generated candidates are drafts, not final assets. They can be derivative or too similar to the generator's training corpus, so novelty and derivative risk are flagged rather than hidden.
- Playtest feedback classification is a broad reception signal, not a complete playtest analysis. It returns a label only, with no calibrated confidence, and does not explain exact design causes.
- Heuristic difficulty is a structural estimate, not player validated difficulty.
- The system is advisory and designer governed. It never edits or finalizes a level on its own, and it does not claim to predict whether a level is fun.

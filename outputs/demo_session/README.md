# Curated Demo Session

These are committed example outputs from real runs of AI Level Director Studio, so a
reviewer can inspect the system's artifacts without running it. Each folder holds one
session's session snapshot (JSON), append only event log (JSONL), Markdown session
report, candidate level text, and the triage deliberation transcript and report.

- **demo-generated** , a Project 5 generated candidate is triaged and rejected for a
  structural integrity error before playtest. Shows generation plus the structural
  safeguard.
- **demo-derivative** , a candidate that duplicates a known reference level is caught as
  highly derivative and routed back rather than accepted. Shows the originality
  safeguard.
- **demo-negative** , the full loop: a candidate is triaged, sent to playtest, receives
  negative feedback, and a linked revision (R-001) is created from the original.

These were produced with the real prior project adapters. The app and the notebook can
regenerate equivalent outputs.

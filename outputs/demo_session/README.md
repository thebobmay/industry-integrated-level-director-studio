# Curated Demo Session

These are committed example outputs from real runs of AI Level Director Studio, so a
reviewer can inspect the system's artifacts without running it. Each folder holds one
session's snapshot (JSON), append only event log (JSONL), Markdown session report,
candidate level text, and the triage deliberation transcript and report. Together they
cover the seven evaluation scenarios (A, A2, B through F).

- **demo-generated** (Scenario A, generated candidate path): a Project 5 generated
  candidate is triaged and rejected for a structural integrity error before playtest.
  Shows generation plus the structural safeguard.
- **demo-derivative** (Scenario A2, originality safeguard): a candidate that duplicates
  a known reference level is caught as highly derivative and routed back rather than
  accepted.
- **demo-uploaded** (Scenario B, uploaded candidate path): a designer uploaded candidate
  is triaged and accepted for playtest.
- **demo-positive** (Scenario C, positive feedback): an accepted candidate is sent to
  playtest and completed after positive feedback from the Project 3 classifier.
- **demo-negative** (Scenario D, revision loop): a candidate gets negative feedback and a
  linked revision (R-001) is created from the original.
- **demo-conflicting** (Scenario E, responsible control): a self contradictory brief
  makes the triage agent request clarification rather than force a recommendation.
- **demo-override** (Scenario F, feedback safeguards): short playtest feedback is flagged
  as low reliability, and the designer overrides the classifier's positive call to
  negative; the classifier's original label is kept on the record. The event log shows
  the feedback classification and the designer override.

These were produced with the real prior project adapters. The app and the notebook can
regenerate equivalent outputs.

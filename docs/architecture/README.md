# AI Level Director Studio — Architecture

This folder holds the system architecture documentation for AI Level Director
Studio. Each diagram lives in its own file so it can be referenced and exported
independently. The diagrams are authored in Mermaid and reflect the current
implementation in `src/ai_level_director/`.

## Diagrams

1. [System Architecture](01_system_architecture.md) — the layered view: users, UI,
   service facade, workflow, domain, persistence, adapters, and prior projects.
2. [Candidate Lifecycle State Machine](02_candidate_lifecycle_state_machine.md) —
   the states a single candidate moves through and the transitions allowed between
   them.
3. [End to End Workflow Sequence](03_end_to_end_sequence.md) — the order of calls
   from brief to candidate to triage to playtest feedback to report.
4. [Integration Boundaries](04_integration_boundaries.md) — the high level view of
   what each prior project contributes across the integration boundary.

## Architecture Notes

- Project 7 does not build a new model or a new agent. It integrates prior capstone
  components through adapters.
- There is no separate controller class. `LevelDirectorService` is the facade and
  command layer the UI and notebook call, and the `transitions` module is the
  candidate state machine it delegates to.
- Project 6 remains the single candidate triage authority. Its validity, difficulty,
  novelty, and pacing reasoning is not duplicated anywhere in Project 7.
- Project 3 runs only after a candidate is sent to playtest. It returns a sentiment
  label only, positive or negative, with no probability or confidence score.
- Project 5 provides candidate drafts, not final production ready content. Its
  novelty and derivative risk are disclosed rather than hidden.
- Candidate lifecycle state belongs to each candidate, not to the whole session, so
  several candidates in different states coexist in one session.
- Designer override actions, `mark_complete` and `archive_candidate`, act outside the
  automated transition guard and can be applied from any non terminal state. The
  terminal states are `complete`, `archived`, and `structural_rejected`.
- Rendering is an ASCII monospace tile grid called by the UI and view models. Image
  and sprite previews are a deferred polish feature; the `rendered_preview_path`
  field exists on the model but is left unset.
- JSON session snapshots and JSONL event logs provide transparency and
  reproducibility in place of a database.
- The Gradio UI is a thin interaction layer over the service facade, reached through
  framework agnostic callbacks and view models that can be tested outside the UI.

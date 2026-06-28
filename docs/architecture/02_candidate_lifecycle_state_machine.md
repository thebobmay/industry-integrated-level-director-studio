# Candidate Lifecycle State Machine

Each candidate owns its own state. Several candidates in different states coexist in
one design session. A draft candidate moves directly to one of the six triage outcome
states. Designer overrides can complete or archive a candidate outside the automated
guard. The transitions below match `ALLOWED_TRANSITIONS` in
`workflow/transitions.py`.

```mermaid
stateDiagram-v2
    [*] --> draft

    draft --> ready_for_playtest: P6 accept_for_playtest
    draft --> revision_needed: P6 recommend_revision
    draft --> clarification_needed: P6 request_clarification
    draft --> structural_rejected: P6 reject_structural
    draft --> derivative_review_needed: P6 flag_as_derivative_draft
    draft --> human_review_needed: P6 request_human_review

    ready_for_playtest --> sent_to_playtest: Designer sends candidate
    ready_for_playtest --> archived: Designer archives

    derivative_review_needed --> sent_to_playtest: Designer approves playtest
    derivative_review_needed --> archived: Designer rejects originality risk
    derivative_review_needed --> human_review_needed: Designer requests review

    sent_to_playtest --> feedback_received: Playtester submits feedback

    feedback_received --> complete: P3 positive feedback
    feedback_received --> revision_needed: P3 negative feedback
    feedback_received --> human_review_needed: Empty or unclassifiable feedback (input check)

    revision_needed --> draft: Designer creates revised candidate
    revision_needed --> archived: Designer archives
    clarification_needed --> draft: Designer clarifies or creates new candidate
    clarification_needed --> archived: Designer archives
    human_review_needed --> draft: Designer resolves and creates new candidate
    human_review_needed --> archived: Designer archives

    complete --> archived: Designer archives
    structural_rejected --> archived: Designer archives

    complete --> [*]
    archived --> [*]
    structural_rejected --> [*]

    note right of draft
        Designer overrides: mark_complete and archive_candidate
        may act from any non terminal state, bypassing the
        automated transition guard. The terminal states are
        complete, archived, and structural_rejected.
    end note
```

## Triage action to state

`run_triage` maps a Project 6 action to the resulting candidate state through
`TRIAGE_ACTION_TO_STATE`, then validates the move with `ensure_transition`.

| Project 6 action | Candidate state |
|---|---|
| `accept_for_playtest` | `ready_for_playtest` |
| `recommend_revision` | `revision_needed` |
| `request_clarification` | `clarification_needed` |
| `reject_structural` | `structural_rejected` |
| `flag_as_derivative_draft` | `derivative_review_needed` |
| `request_human_review` | `human_review_needed` |

## Feedback to state

`submit_feedback` first moves the candidate to `feedback_received`, then maps the
result. The Project 3 classifier returns a label only with no confidence score, so
the mapping is direct. Empty or blank feedback cannot be classified, so it is caught
as an input check and routed to human review rather than through the classifier.

| Feedback | Candidate state |
|---|---|
| Positive | `complete` |
| Negative | `revision_needed` |
| Empty or unclassifiable text | `human_review_needed` |

## Notes

- A revised candidate is a new candidate with `source="revised"` and a
  `parent_candidate_id`. Revisions never overwrite the original, so the iteration
  history is preserved.
- The `triaged` state exists in the `CandidateState` vocabulary but is reserved and
  unused. Triage moves a draft directly to one of the six mapped states above, so
  nothing transitions into `triaged`.

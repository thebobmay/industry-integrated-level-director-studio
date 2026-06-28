# End to End Workflow Sequence

The order of calls for a full pass through the workflow: start a session, add a
candidate, run triage, send a ready candidate to playtest, classify the feedback, and
generate a report. The participant names and method names match
`workflow/service.py`.

```mermaid
sequenceDiagram
    actor D as Designer
    actor T as Playtester
    participant UI as Gradio UI / Notebook
    participant S as LevelDirectorService
    participant P5 as Project5GeneratorAdapter
    participant P6 as Project6TriageAdapter
    participant P3 as Project3FeedbackAdapter
    participant Store as SessionStore / EventLog

    D->>UI: Create design session and brief
    UI->>S: start_session(brief, target_difficulty, novelty)
    S->>Store: save session JSON + event

    alt Generate candidate
        D->>UI: Generate candidates
        UI->>S: add_generated_candidate(session_id, n, temperature, seed)
        S->>P5: generate(target_difficulty, n, temperature, seed)
        P5-->>S: candidate level text(s)
        S->>Store: save candidate TXT + session update
    else Upload or sample candidate
        D->>UI: Upload, paste, or pick a sample
        UI->>S: add_uploaded_candidate / add_sample_candidate(session_id, level_text)
        S->>Store: save candidate TXT + session update
    end

    D->>UI: Run triage on the selected candidate
    UI->>S: run_triage(session_id, candidate_id)
    S->>P6: triage(brief, level_text, target_difficulty, novelty)
    P6-->>S: action + rationale + warnings + questions + transcript + report
    S->>S: state_for_triage_action + ensure_transition
    S->>Store: save triage transcript + report artifacts
    S->>Store: update candidate state + log event (with artifact paths)

    alt Candidate ready (ready_for_playtest or derivative_review_needed)
        D->>UI: Send to playtest
        UI->>S: send_to_playtest(session_id, candidate_id)
        S->>Store: state = sent_to_playtest
        T->>UI: Enter feedback
        UI->>S: submit_feedback(session_id, candidate_id, text)
        S->>P3: classify(feedback_text)
        P3-->>S: sentiment label (positive or negative, no confidence)
        S->>Store: update candidate state + log feedback
    else Not ready (revision, clarification, or review)
        S-->>UI: Show recommendation. Designer revises or archives
    end

    D->>UI: Generate session report
    UI->>S: build_session_report(session_id)
    S->>Store: save report artifact + event
    S-->>UI: report path + summary
```

## Notes

- Every command persists before returning: the service saves the session snapshot and
  appends an event to the JSONL log, so the UI can recover after a restart.
- `submit_feedback` always moves the candidate to `feedback_received` first, then to
  the mapped outcome. Empty feedback is routed to human review without calling the
  classifier.
- Triage and feedback are reached only through adapters, so the same sequence runs
  against mock adapters or the real prior projects without changing the service.
- Each triage run also persists the agent's full deliberation transcript and a designer
  facing report as their own files, and the `triaged` event records their paths. The
  event log stays a scannable audit index that links to the full reasoning behind every
  triage recommendation.

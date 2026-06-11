# AI Level Director Studio — System Architecture Diagram

## Main System Architecture

```mermaid
flowchart TD
    %% Users
    Designer[Designer]
    Playtester[Playtester / Simulated Tester]
    Reviewer[Reviewer / Mentor]

    %% UI
    UI[Gradio UI<br/>Design Session · Candidate Board · Candidate Detail · Playtester View · Reports]

    %% Service Layer
    Service[LevelDirectorService<br/>Facade for UI and notebook]
    Controller[Workflow Controller<br/>Commands + candidate lifecycle transitions]
    ViewModels[UI View Models<br/>Tables · Markdown · preview payloads]

    %% Domain and Persistence
    Session[DesignSession<br/>Workspace metadata + candidate collection]
    Candidate[LevelCandidate<br/>state · history · triage · feedback]
    Store[SessionStore<br/>JSON snapshots]
    EventLog[Event Log<br/>JSONL history]
    Reports[ReportBuilder<br/>Markdown session reports]
    Renderer[LevelRenderer<br/>ASCII · tile image · optional sprites]

    %% Adapters
    P5Adapter[Project5GeneratorAdapter<br/>Candidate generation]
    P6Adapter[Project6TriageAdapter<br/>Single-candidate triage]
    P3Adapter[Project3FeedbackAdapter<br/>Playtest feedback classification]

    %% Prior Projects
    P5[Project 5<br/>Conditional Transformer Level Generator]
    P6[Project 6<br/>Agentic Level Design Triage Agent]
    P3[Project 3<br/>Steam Review Sentiment Classifier]

    %% Artifacts
    CandidateFiles[Candidate TXT Files]
    RenderedFiles[Rendered Level PNGs]
    ReportFiles[Session Report MD/PDF]
    CachedFixtures[Cached Demo Fixtures]

    %% User interactions
    Designer --> UI
    Playtester --> UI
    Reviewer --> UI

    %% UI to backend
    UI --> ViewModels
    UI --> Service
    Service --> Controller

    %% Controller/domain
    Controller --> Session
    Session --> Candidate

    %% Candidate source
    Controller --> P5Adapter
    P5Adapter --> P5
    P5Adapter --> Candidate

    %% Triage
    Controller --> P6Adapter
    P6Adapter --> P6
    P6Adapter --> Candidate

    %% Playtest feedback
    Controller --> P3Adapter
    P3Adapter --> P3
    P3Adapter --> Candidate

    %% Persistence and artifacts
    Controller --> Store
    Controller --> EventLog
    Controller --> Renderer
    Controller --> Reports

    Store --> CandidateFiles
    Renderer --> RenderedFiles
    Reports --> ReportFiles
    Store --> CachedFixtures

    %% UI outputs
    ViewModels --> UI
    CandidateFiles --> UI
    RenderedFiles --> UI
    ReportFiles --> UI
```

---

## Candidate Lifecycle State Machine

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
    derivative_review_needed --> sent_to_playtest: Designer approves playtest
    derivative_review_needed --> archived: Designer rejects originality risk
    derivative_review_needed --> human_review_needed: Designer requests review

    sent_to_playtest --> feedback_received: Playtester submits feedback

    feedback_received --> complete: P3 positive feedback
    feedback_received --> revision_needed: P3 negative feedback
    feedback_received --> human_review_needed: P3 low confidence / unclear

    revision_needed --> draft: Designer creates revised candidate
    clarification_needed --> draft: Designer clarifies brief or creates new candidate
    human_review_needed --> draft: Designer resolves issue and creates new candidate

    complete --> [*]
    archived --> [*]
    structural_rejected --> [*]
```

---

## End-to-End Workflow Sequence

```mermaid
sequenceDiagram
    actor D as Designer
    actor T as Playtester
    participant UI as Gradio UI
    participant S as LevelDirectorService
    participant P5 as Project 5 Adapter
    participant P6 as Project 6 Adapter
    participant P3 as Project 3 Adapter
    participant Store as SessionStore / EventLog

    D->>UI: Create design session and brief
    UI->>S: start_session(brief)
    S->>Store: save session JSON + event

    alt Generate candidate
        D->>UI: Generate candidates
        UI->>S: generate_candidates(session_id, n)
        S->>P5: generate(target_difficulty, n, temperature)
        P5-->>S: candidate level text(s)
        S->>Store: save candidate TXT + session update
    else Upload candidate
        D->>UI: Upload/paste candidate level
        UI->>S: upload_candidate(session_id, level_text)
        S->>Store: save candidate TXT + session update
    end

    D->>UI: Run triage on selected candidate
    UI->>S: run_triage(session_id, candidate_id)
    S->>P6: triage(brief, level_text)
    P6-->>S: triage action + rationale + questions
    S->>Store: update candidate state + log event

    alt Candidate ready
        D->>UI: Send to playtest
        UI->>S: send_to_playtest(session_id, candidate_id)
        S->>Store: state = sent_to_playtest
        T->>UI: Enter feedback
        UI->>S: submit_feedback(session_id, candidate_id, text)
        S->>P3: classify(feedback_text)
        P3-->>S: sentiment + confidence
        S->>Store: update candidate state + log feedback
    else Candidate not ready
        S-->>UI: Show revision / clarification / review recommendation
    end

    D->>UI: Generate session report
    UI->>S: build_session_report(session_id)
    S->>Store: save report artifact
    S-->>UI: report path + summary
```

---

## Integration Boundary Summary

```mermaid
flowchart LR
    P7[Project 7<br/>New Integration Layer]

    P5[Project 5<br/>Generative AI]
    P6[Project 6<br/>Agentic AI]
    P3[Project 3<br/>Applied ML]

    P5 -->|candidate drafts| P7
    P6 -->|triage action + rationale| P7
    P3 -->|feedback sentiment signal| P7

    P7 -->|candidate lifecycle state| UI[Designer UI]
    P7 -->|session JSON + events| Artifacts[Reviewable Artifacts]
    P7 -->|session report| Paper[Reflective Synthesis Evidence]
```

---

## Architecture Notes

- Project 7 does not build a new model or new agent.
- Project 7 integrates prior capstone components through adapters.
- Project 6 remains the single-candidate triage authority.
- Project 3 is used only after playtest feedback exists.
- Project 5 provides candidate drafts, not final production-ready content.
- Candidate lifecycle state belongs to each candidate, not to the whole session.
- JSON sessions and JSONL logs provide transparency and reproducibility.
- The Gradio UI is a thin interaction layer over the backend service facade.

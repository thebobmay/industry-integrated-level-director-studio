# System Architecture

The layered view of AI Level Director Studio. The Gradio UI and the reproducible
notebook both call one service facade. The facade holds the command logic, delegates
lifecycle rules to the state machine and candidate construction to the candidate
sources, and reaches each prior project only through an adapter. Persistence is local
JSON and JSONL, and each triage run also saves its full deliberation transcript and a
report for audit. The ASCII renderer is a display utility used by the UI and the view
models, not by the service.

```mermaid
flowchart TD
    %% Users
    Designer[Designer]
    Playtester[Playtester / Simulated Tester]
    Reviewer[Reviewer / Mentor]

    %% UI layer
    UI[Gradio UI<br/>Design Session · Candidate Board · Candidate Detail · Playtester View · Reports]
    Callbacks[UI Callbacks<br/>Command style, framework agnostic]
    ViewModels[UI View Models<br/>Tables · Markdown · ASCII previews]
    Renderer[ASCII Renderer<br/>Monospace tile grid]

    %% Service and workflow
    Service[LevelDirectorService<br/>Facade + command logic for UI and notebook]
    Transitions[Transitions<br/>Candidate state machine + triage/feedback mappings]
    Sources[Candidate Sources<br/>Builders: uploaded · sample · generated · revised]

    %% Domain
    Session[DesignSession<br/>Workspace metadata + candidate collection]
    Candidate[LevelCandidate<br/>state · history · triage · feedback]

    %% Persistence and output
    Store[SessionStore<br/>JSON snapshots]
    EventLog[Event Log<br/>JSONL history]
    Reports[ReportBuilder<br/>Markdown session reports]

    %% Adapters
    P5Adapter[Project5GeneratorAdapter<br/>Candidate generation]
    P6Adapter[Project6TriageAdapter<br/>Single candidate triage]
    P3Adapter[Project3FeedbackAdapter<br/>Feedback classification]

    %% Prior projects
    P5[Project 5<br/>Conditional Transformer Level Generator]
    P6[Project 6<br/>Agentic Level Design Triage Agent]
    P3[Project 3<br/>Player Feedback Classifier · TF-IDF + LinearSVC]

    %% Artifacts
    CandidateFiles[Candidate TXT Files]
    ReportFiles[Session Report MD]
    TriageFiles[Triage Transcript + Report<br/>Per run audit MD]

    %% User interactions
    Designer --> UI
    Playtester --> UI
    Reviewer --> UI

    %% UI to backend
    UI --> Callbacks
    UI --> Renderer
    Callbacks --> Service
    Callbacks --> ViewModels
    ViewModels --> Renderer

    %% Service delegates
    Service --> Transitions
    Service --> Sources
    Service --> Session
    Session --> Candidate

    %% Candidate source
    Service --> P5Adapter
    P5Adapter --> P5
    P5Adapter --> Candidate

    %% Triage
    Service --> P6Adapter
    P6Adapter --> P6
    P6Adapter --> Candidate

    %% Feedback
    Service --> P3Adapter
    P3Adapter --> P3
    P3Adapter --> Candidate

    %% Persistence and artifacts
    Service --> Store
    Service --> EventLog
    Service --> Reports
    Service --> TriageFiles
    Store --> CandidateFiles
    Reports --> ReportFiles

    %% Outputs back to UI
    ViewModels --> UI
    CandidateFiles --> UI
    ReportFiles --> UI
    TriageFiles --> UI
```

## Layer responsibilities

- **UI (`app.py`, `ui/`):** Gradio tabs render the workspace and forward designer and
  playtester actions to framework agnostic callbacks. View models convert domain
  objects into tables and Markdown, and the ASCII renderer produces the tile grid
  previews. No UI code touches prior project internals or persistence directly.
- **Service (`workflow/service.py`):** the single backend entry point. Each command
  loads the session, performs one change, saves the session, and returns it. It owns
  no lifecycle rules itself; it delegates them.
- **State machine (`workflow/transitions.py`):** the allowed transitions plus the
  mappings from a triage action and a feedback result to a candidate state.
- **Candidate sources (`workflow/candidate_sources.py`):** builders for uploaded,
  sample, generated, and revised candidates, plus artifact saving.
- **Domain (`domain/`):** Pydantic models for the session, candidate, triage result,
  feedback result, playtest record, and candidate events.
- **Adapters (`adapters/`):** the only code that knows how each prior project loads
  and runs. They return Project 7 domain objects, so mock and real adapters are
  interchangeable behind the `Protocol` interfaces.
- **Persistence (`storage/`):** JSON session snapshots and an append only JSONL event
  log, plus a per run triage transcript and report for audit, with all output paths
  defined in one place.

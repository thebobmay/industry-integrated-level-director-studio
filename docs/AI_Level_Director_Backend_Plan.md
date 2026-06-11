# AI Level Director Studio — Backend Infrastructure Plan

## 1. Purpose

AI Level Director Studio is the final integrated artifact for Project 7. The backend is responsible for orchestrating prior capstone components into a coherent, designer-governed level-iteration workflow.

The backend does **not** introduce a new intelligence layer. Its main job is to coordinate:

- Project 5 — candidate level generation,
- Project 6 — candidate triage and design-readiness recommendation,
- Project 3 — playtest feedback classification,
- Project 7 — session management, candidate lifecycle tracking, reporting, and UI-facing orchestration.

The system should demonstrate intentional integration, observable behavior, realistic constraints, and responsible AI design.

---

## 2. Backend Design Principles

### 2.1 Integrate, do not rewrite

Project 7 should wrap prior capstone work behind adapters rather than copy implementation details into the UI or controller.

```text
Project 5 generator      → Project5GeneratorAdapter
Project 6 triage agent   → Project6TriageAdapter
Project 3 classifier     → Project3FeedbackAdapter
```

The Project 7 backend owns orchestration, state, persistence, and reporting. It should not duplicate Project 6 triage logic or create a new evaluation agent.

### 2.2 Candidate-level workflow state

The session represents the design workspace. Each level candidate owns its own lifecycle state.

This supports multiple candidates in the same design session:

```text
Candidate A = complete
Candidate B = revision_needed
Candidate C = sent_to_playtest
Candidate D = derivative_review_needed
```

This is more realistic than a single global session state and maps naturally to a UI with candidate cards.

### 2.3 Designer-governed workflow

The system recommends and routes. It does not claim final creative authority.

Human checkpoints include:

- designer chooses generated vs uploaded candidate source,
- designer selects which candidates to triage,
- designer decides whether to send a candidate to playtest,
- playtester provides feedback,
- designer revises or marks complete.

### 2.4 Persistence without database overhead

Use local JSON, JSONL, TXT, PNG, and Markdown artifacts.

A full database is unnecessary for the capstone. JSON-backed persistence is transparent, reproducible, and reviewer-friendly.

### 2.5 Thin UI, strong backend

The Gradio UI should call backend services, not prior project internals.

Bad:

```python
# app.py
torch.load(...)
pickle.load(...)
triage_candidate(...)
```

Good:

```python
# app.py
service.generate_candidates(...)
service.run_triage(...)
service.submit_feedback(...)
```

---

## 3. System Design Patterns

| Pattern | Use in Project 7 |
|---|---|
| Adapter | Wrap Project 3, Project 5, and Project 6 components behind stable interfaces |
| Facade | Expose one `LevelDirectorService` to the UI |
| Candidate-level State Machine | Track each candidate through draft, triage, playtest, feedback, and completion |
| Strategy | Support generated, uploaded, sample, and revised candidate sources |
| Repository / Session Store | Persist session snapshots and artifacts without a database |
| Event Log | Record candidate lifecycle events in JSONL |
| Command-style UI callbacks | Each UI action loads session, performs one command, saves state, returns view models |
| View Model | Convert domain models into UI tables, cards, Markdown summaries, and previews |
| Report Builder | Generate consistent Markdown reports from session state |

---

## 4. Proposed Repository Structure

```text
ai-level-director-studio/
├── app.py
├── integrated_system.ipynb
├── README.md
├── requirements.txt
├── .env.example
│
├── docs/
│   ├── backend_plan.md
│   ├── frontend_plan.md
│   ├── project_plan.md
│   ├── system_architecture_diagram.md
│   ├── research_foundation.md
│   └── integrated_project_synopsis.md
│
├── src/
│   └── ai_level_director/
│       ├── __init__.py
│       │
│       ├── domain/
│       │   ├── models.py
│       │   ├── states.py
│       │   └── events.py
│       │
│       ├── adapters/
│       │   ├── project5_generator.py
│       │   ├── project6_triage.py
│       │   └── project3_feedback.py
│       │
│       ├── workflow/
│       │   ├── service.py
│       │   ├── controller.py
│       │   ├── transitions.py
│       │   └── commands.py
│       │
│       ├── storage/
│       │   ├── session_store.py
│       │   └── paths.py
│       │
│       ├── rendering/
│       │   ├── ascii_renderer.py
│       │   ├── image_renderer.py
│       │   └── sprite_renderer.py
│       │
│       ├── reporting/
│       │   ├── report_builder.py
│       │   └── templates.py
│       │
│       └── ui/
│           ├── callbacks.py
│           └── view_models.py
│
├── integrations/
│   ├── project3_feedback/
│   ├── project5_generator/
│   └── project6_triage/
│
├── data/
│   ├── sample_levels/
│   ├── uploaded_levels/
│   ├── generated_candidates/
│   └── scenarios/
│
├── models/
│   ├── project3_feedback/
│   └── project5_generator/
│
├── outputs/
│   ├── sessions/
│   ├── candidates/
│   ├── reports/
│   ├── logs/
│   ├── generated_levels/
│   ├── rendered_levels/
│   └── screenshots/
│
└── tests/
    ├── test_session_store.py
    ├── test_transitions.py
    ├── test_project3_adapter.py
    ├── test_project5_adapter.py
    ├── test_project6_adapter.py
    ├── test_service.py
    ├── test_report_builder.py
    └── test_rendering.py
```

---

## 5. Domain Models

Use Pydantic models for predictable validation, serialization, and UI compatibility.

### 5.1 `DesignSession`

```python
class DesignSession(BaseModel):
    session_id: str
    project_name: str = "AI Level Director Studio"
    design_brief: str
    target_difficulty: str | None = None
    novelty_preference: str | None = None
    session_status: Literal["active", "complete", "archived"] = "active"

    candidates: list[LevelCandidate] = []
    selected_candidate_id: str | None = None

    created_at: str
    updated_at: str
    session_notes: list[str] = []
```

### 5.2 `LevelCandidate`

```python
class LevelCandidate(BaseModel):
    candidate_id: str
    title: str
    source: Literal["generated", "uploaded", "sample", "revised"]
    level_text: str
    level_path: str | None = None
    rendered_preview_path: str | None = None

    workflow_state: CandidateState = "draft"
    parent_candidate_id: str | None = None
    iteration_number: int = 1

    generation_metadata: dict = {}
    triage_result: TriageResult | None = None
    feedback_records: list[PlaytestRecord] = []

    created_at: str
    updated_at: str
    history: list[CandidateEvent] = []
```

### 5.3 `CandidateState`

```python
CandidateState = Literal[
    "draft",
    "triaged",
    "clarification_needed",
    "revision_needed",
    "structural_rejected",
    "derivative_review_needed",
    "ready_for_playtest",
    "sent_to_playtest",
    "feedback_received",
    "complete",
    "human_review_needed",
    "archived",
]
```

### 5.4 `TriageResult`

```python
class TriageResult(BaseModel):
    action: str
    readiness: str
    rationale: str
    warnings: list[str] = []
    revision_recommendations: list[str] = []
    playtest_questions: list[str] = []
    transcript_path: str | None = None
    report_path: str | None = None
    raw_payload: dict = {}
```

### 5.5 `FeedbackResult`

```python
class FeedbackResult(BaseModel):
    feedback_text: str
    sentiment: Literal["positive", "negative"]
    confidence: float
    model_name: str
    label_source: str = "project3_feedback_classifier"
```

### 5.6 `PlaytestRecord`

```python
class PlaytestRecord(BaseModel):
    playtest_id: str
    candidate_id: str
    submitted_at: str
    feedback_text: str
    feedback_result: FeedbackResult
    status_after_feedback: CandidateState
```

### 5.7 `CandidateEvent`

```python
class CandidateEvent(BaseModel):
    event_id: str
    timestamp: str
    event_type: Literal[
        "created",
        "generated",
        "uploaded",
        "triaged",
        "sent_to_playtest",
        "feedback_submitted",
        "state_changed",
        "revision_created",
        "completed",
        "archived",
        "report_generated",
    ]
    candidate_id: str | None = None
    summary: str
    payload: dict = {}
```

---

## 6. Candidate State Machine

### 6.1 P6 triage action mapping

| Project 6 Action | Project 7 Candidate State |
|---|---|
| `accept_for_playtest` | `ready_for_playtest` |
| `recommend_revision` | `revision_needed` |
| `request_clarification` | `clarification_needed` |
| `reject_structural` | `structural_rejected` |
| `flag_as_derivative_draft` | `derivative_review_needed` |
| `request_human_review` | `human_review_needed` |

### 6.2 Designer action mapping

| Designer Action | Candidate State |
|---|---|
| Send to playtester | `sent_to_playtest` |
| Create revised candidate | New candidate with `source="revised"` and `parent_candidate_id` |
| Mark complete manually | `complete` |
| Archive candidate | `archived` |

### 6.3 Project 3 feedback mapping

| Feedback Result | Candidate State |
|---|---|
| Positive | `complete` |
| Negative | `revision_needed` |
| Low confidence / empty / unclear | `human_review_needed` |

### 6.4 Allowed transitions

```text
draft → ready_for_playtest
draft → revision_needed
draft → clarification_needed
draft → structural_rejected
draft → derivative_review_needed
draft → human_review_needed

ready_for_playtest → sent_to_playtest
sent_to_playtest → feedback_received
feedback_received → complete
feedback_received → revision_needed
feedback_received → human_review_needed

revision_needed → draft          # via new revised candidate
derivative_review_needed → sent_to_playtest | archived | human_review_needed
clarification_needed → draft     # after revised brief or new candidate
```

---

## 7. Backend Services

### 7.1 `LevelDirectorService`

The service is the facade used by the UI and notebook.

```python
class LevelDirectorService:
    def start_session(self, design_brief, target_difficulty=None, novelty_preference=None) -> DesignSession: ...

    def load_session(self, session_id: str) -> DesignSession: ...

    def save_session(self, session: DesignSession) -> Path: ...

    def generate_candidates(self, session_id: str, n: int, temperature: float, seed: int | None = None) -> DesignSession: ...

    def upload_candidate(self, session_id: str, level_text: str, title: str | None = None) -> DesignSession: ...

    def run_triage(self, session_id: str, candidate_id: str) -> DesignSession: ...

    def send_to_playtest(self, session_id: str, candidate_id: str) -> DesignSession: ...

    def submit_feedback(self, session_id: str, candidate_id: str, feedback_text: str) -> DesignSession: ...

    def create_revised_candidate(self, session_id: str, parent_candidate_id: str, revised_level_text: str, notes: str) -> DesignSession: ...

    def build_session_report(self, session_id: str) -> Path: ...
```

### 7.2 Candidate source service

Responsible for creating candidates from generated, uploaded, sample, or revised sources.

```python
create_generated_candidates(...)
create_uploaded_candidate(...)
create_sample_candidate(...)
create_revised_candidate(...)
```

### 7.3 Triage service

Responsible for calling Project 6 and applying state transition rules.

```python
run_candidate_triage(session_id, candidate_id)
```

### 7.4 Playtest service

Responsible for sending a candidate to the simulated playtester workflow and routing feedback.

```python
send_to_playtest(session_id, candidate_id)
submit_playtest_feedback(session_id, candidate_id, feedback_text)
```

### 7.5 Report service

Responsible for producing a Markdown report from session state.

```python
build_session_report(session_id)
```

---

## 8. Adapter Contracts

### 8.1 Project 5 generator adapter

```python
class Project5GeneratorAdapter:
    def generate(
        self,
        target_difficulty: str,
        n: int = 1,
        temperature: float = 1.2,
        seed: int | None = None,
    ) -> list[str]:
        ...
```

Expected metadata:

```text
difficulty_token
temperature
seed
model_path
tokenizer_path
generation_timestamp
source_project = "Project 5 — Generative AI"
```

Project 5 should only produce candidate text. It does not understand the full design brief and does not decide whether the result is usable.

### 8.2 Project 6 triage adapter

```python
class Project6TriageAdapter:
    def triage(
        self,
        design_brief: str,
        level_text: str,
        target_difficulty: str | None = None,
        novelty_preference: str | None = None,
    ) -> TriageResult:
        ...
```

Project 6 is the candidate evaluation and design-readiness authority. Project 7 should not duplicate Project 6’s validity, difficulty, novelty, pacing, or design-triage reasoning.

### 8.3 Project 3 feedback adapter

```python
class Project3FeedbackAdapter:
    def classify(self, feedback_text: str) -> FeedbackResult:
        ...
```

Project 3 provides a feedback signal only. It does not explain exact design causes and should not directly override designer judgment.

---

## 9. Persistence and Artifacts

### 9.1 Storage layout

```text
outputs/
├── sessions/
│   └── {session_id}.json
├── logs/
│   └── {session_id}_events.jsonl
├── candidates/
│   └── {session_id}/
│       ├── G-001.txt
│       ├── G-002.txt
│       └── U-001.txt
├── rendered_levels/
│   └── {session_id}/
│       ├── G-001.png
│       └── U-001.png
└── reports/
    └── {session_id}_report.md
```

### 9.2 Session snapshot

The session JSON is the current state of the workspace.

### 9.3 Event log

The JSONL event log is the historical audit trail. Every meaningful command appends an event.

Example events:

```text
session_created
candidate_generated
candidate_uploaded
triage_completed
sent_to_playtest
feedback_submitted
candidate_completed
revision_created
report_generated
```

### 9.4 Candidate files

Every candidate level should also be saved as a `.txt` file for review and reproducibility.

### 9.5 Rendered previews

Rendered previews should start as simple tile images. Sprite rendering is optional polish.

---

## 10. Rendering Pipeline

### 10.1 MVP rendering

The first renderer should support:

```python
render_level_ascii(level_text) -> str
render_level_image(level_text) -> PIL.Image
```

The image renderer can use simple colored tiles or icons.

### 10.2 Optional polish

If time allows:

```python
render_level_with_sprites(level_text, tileset_path) -> PIL.Image
```

Use only free or appropriately licensed assets. Avoid actual Nintendo/Mario sprites.

### 10.3 Tile mapping

| VGLC Tile | Semantic Render Category |
|---|---|
| `-` | sky/background |
| `X`, `S` | ground/solid |
| `?`, `Q` | question/item block |
| `o` | collectible/coin |
| `E` | enemy |
| `<`, `>` | pipe top |
| `[`, `]` | pipe body |
| `B`, `b` | block/hazard-like structure depending on retained semantics |

---

## 11. Cached Demo Mode

The backend should support both live and cached paths.

### 11.1 Live mode

Calls Project 5, Project 6, and Project 3 directly.

### 11.2 Cached mode

Loads stored candidates, triage outputs, feedback outputs, and reports from `outputs/` or `data/scenarios/`.

Cached mode protects the demo from:

- API outages,
- model variance,
- slow generation,
- missing GPU,
- temporary artifact-path issues.

The report should clearly state whether a scenario used live or cached outputs.

---

## 12. Testing Strategy

### 12.1 Unit tests

Test:

- state transitions,
- JSON session serialization,
- event logging,
- report generation,
- renderer output shape,
- adapter fallback behavior.

### 12.2 Adapter tests

Use fixtures and cached artifacts when possible.

Test:

- Project 3 classifier loads and returns sentiment,
- Project 5 generator adapter returns valid candidate strings or cached candidates,
- Project 6 triage adapter returns a valid `TriageResult`.

### 12.3 Integration tests

Test complete workflows:

1. Uploaded candidate → triage → ready for playtest.
2. Ready candidate → sent to playtest → positive feedback → complete.
3. Ready candidate → sent to playtest → negative feedback → revision needed.
4. Generated candidate → triage → derivative review or ready for playtest.
5. Revision-needed candidate → revised candidate created → new candidate returns to draft.

### 12.4 UI smoke tests

At minimum, verify callback functions run outside the Gradio event loop.

---

## 13. Evaluation Scenarios

The final system should demonstrate realistic scenario behavior.

### Scenario 1 — Generated candidate becomes ready for playtest

```text
Brief: Create an easy beginner-friendly platformer segment.
Source: Project 5 generator.
Expected: Candidate generated, triaged by P6, and either accepted for playtest or flagged with clear warnings.
```

### Scenario 2 — Generated candidate flagged as derivative

```text
Brief: Create a familiar platformer segment in the existing style.
Source: Project 5 generator.
Expected: Candidate may be playable but flagged as derivative or originality-risk if similarity is high.
```

### Scenario 3 — Uploaded candidate with positive feedback

```text
Brief: Preserve layout and test whether the segment feels fair.
Source: Uploaded candidate.
Expected: P6 accepts for playtest; playtester feedback is positive; P3 marks positive; candidate becomes complete.
```

### Scenario 4 — Uploaded candidate with negative feedback

```text
Brief: Beginner-friendly segment that should not feel frustrating.
Source: Uploaded or revised candidate.
Feedback: "The first jump felt unfair and frustrating."
Expected: P3 marks negative; candidate becomes revision_needed; designer can create a revised candidate.
```

---

## 14. Backend Definition of Done

Backend MVP is complete when:

1. A design session can be created and saved as JSON.
2. Multiple candidates can be added to the same session.
3. Each candidate has an independent lifecycle state.
4. Candidate levels are saved as files.
5. Basic rendered previews are generated.
6. A candidate can be triaged through Project 6.
7. A ready candidate can be sent to the playtester view.
8. Feedback can be submitted and classified through Project 3.
9. Candidate state updates correctly after feedback.
10. Revised candidate versions can be created.
11. A session report can be generated.
12. A cached demo scenario can be run without live model calls.

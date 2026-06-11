# AI Level Director Studio — Complete Project Plan

## 1. Working Title

**AI Level Director Studio: A Designer-Governed Workflow for 2D Platformer Level Iteration**

---

## 2. Project Goal

Build an integrated, industry-focused AI artifact for the creative industries / game development sector.

The system helps a level designer manage candidate 2D platformer level segments through a structured iteration workflow:

```text
design brief
→ generated or uploaded candidates
→ agentic triage
→ playtest decision
→ feedback classification
→ complete or revise
```

The final artifact should demonstrate system-level integration, not a single isolated model.

---

## 3. Rubric Alignment Summary

The final project must produce an industry-specific AI artifact that integrates at least three prior capstone projects, demonstrates intentional system design, explains tradeoffs and responsible-use concerns, and supports a reflective synthesis paper and mentor defense.

This plan aligns to those requirements by producing:

| Requirement | Planned Evidence |
|---|---|
| Industry-specific artifact | Game development / level design workflow |
| Real-world problem | Resource-constrained teams need faster, safer level iteration |
| At least three prior projects integrated | Project 5 generator, Project 6 triage agent, Project 3 feedback classifier |
| Coherent system design | Adapter-based backend, candidate lifecycle state machine, Gradio UI |
| Observable outputs | Candidate cards, triage results, feedback results, session reports |
| Ethical and responsible reasoning | Designer control, novelty-risk disclosure, feedback limitations, no autonomous final authority |
| Supporting documentation | Backend plan, frontend plan, architecture diagram, research foundation, synthesis paper |
| Reproducibility | requirements.txt, JSON session snapshots, event logs, cached demos |

---

## 4. Industry Context and Problem Definition

### 4.1 Industry

Creative industries, specifically independent and small-team game development.

### 4.2 Problem

Small game teams need to iterate quickly on level design ideas, but level design review and playtesting can be expensive and time-consuming. Generative AI can produce candidate content, but raw generated levels may be derivative, structurally flawed, misaligned with design intent, or unsuitable for playtest.

### 4.3 System need

The need is not an autonomous level generator. The need is a designer-governed workflow that helps a human:

- generate or provide level candidates,
- inspect candidate state,
- triage candidates before playtesting,
- send candidates to playtest,
- interpret playtester feedback,
- decide whether to complete, revise, reject, or rerun the workflow.

---

## 5. Integrated Prior Projects

### 5.1 Project 5 — Generative AI

**Role in Project 7:** Candidate source.

Project 5 generates 2D platformer level candidates using a conditional Transformer trained on VGLC Mario-style tile data.

**Important lesson:** The generator can create structurally valid, difficulty-controlled candidates, but high nearest-neighbor similarity means outputs should be treated as candidate drafts rather than final production assets.

**Integration:** Project 7 wraps Project 5 behind `Project5GeneratorAdapter`.

### 5.2 Project 6 — Agentic AI

**Role in Project 7:** Candidate triage and design-decision layer.

Project 6 interprets a natural-language design brief, analyzes one candidate level with tools, and recommends one of the following actions:

- accept for playtest,
- recommend revision,
- request clarification,
- flag as derivative draft,
- reject for structural reasons,
- request human review.

**Integration:** Project 7 wraps Project 6 behind `Project6TriageAdapter`.

### 5.3 Project 3 — Applied Machine Learning

**Role in Project 7:** Post-playtest feedback signal.

Project 3 classifies player/playtester text feedback into positive or negative reception.

**Important limitation:** The classifier should be treated as a broad reception signal, not a complete playtest-analysis system.

**Integration:** Project 7 wraps Project 3 behind `Project3FeedbackAdapter`.

### 5.4 Supporting prior work

| Project | Use in Project 7 |
|---|---|
| Project 1 — Programming Foundations | Data-scope caution, market/context framing, reproducible workflow habits |
| Project 2 — Statistical Analysis | Reminder that significant signals may have weak practical value; supports multi-signal advisory design |
| Project 4 — Deep Learning | Future live telemetry extension; not required for MVP runtime |

---

## 6. System Thesis

> AI Level Director Studio is a designer-governed workflow for 2D platformer level iteration. It combines a candidate source, agentic level triage, playtest feedback classification, candidate-level state tracking, and a lightweight UI to help a human designer decide whether to accept, revise, regenerate, clarify, or reject a level candidate.

---

## 7. Scope

### 7.1 In scope

- Gradio prototype UI,
- generated candidate path using Project 5,
- uploaded/designer candidate path,
- multiple candidates per design session,
- candidate-level workflow state,
- P6 triage integration,
- P3 feedback classification integration,
- simulated playtester tab,
- JSON session persistence,
- event logs,
- basic level rendering,
- session report generation,
- notebook or script walkthrough,
- reflective synthesis paper,
- architecture diagram,
- mentor presentation.

### 7.2 Out of scope

- full game engine integration,
- playable level simulation,
- automated level editing,
- real user accounts,
- database backend,
- real multiplayer playtesting,
- production deployment,
- live telemetry integration from Project 4,
- using copyrighted Mario sprites,
- claiming the system predicts fun or guarantees quality.

---

## 8. High-Level Workflow

```text
Designer creates a design session
    ↓
Designer generates or uploads multiple candidates
    ↓
Each candidate appears on the Candidate Board
    ↓
Designer runs Project 6 triage on selected candidates
    ↓
Candidate state updates
    ↓
Designer sends ready candidate to Playtester View
    ↓
Playtester enters feedback
    ↓
Project 3 classifies feedback
    ↓
Candidate becomes complete, revision_needed, or human_review_needed
    ↓
Designer may create a revised candidate and loop again
```

---

## 9. Candidate Lifecycle

```text
draft
→ ready_for_playtest
→ sent_to_playtest
→ feedback_received
→ complete
```

Alternate outcomes:

```text
clarification_needed
revision_needed
structural_rejected
derivative_review_needed
human_review_needed
archived
```

Each candidate owns its own lifecycle state.

---

## 10. Backend Plan

### 10.1 Main components

| Component | Responsibility |
|---|---|
| `LevelDirectorService` | Facade used by UI and notebook |
| `SessionStore` | Save/load JSON sessions and event logs |
| `Project5GeneratorAdapter` | Generate candidate levels |
| `Project6TriageAdapter` | Run P6 triage |
| `Project3FeedbackAdapter` | Classify playtest feedback |
| `ReportBuilder` | Generate Markdown session report |
| `LevelRenderer` | Render candidate previews |
| `ViewModels` | Convert session state into UI tables and Markdown |

### 10.2 Storage

Use local files:

```text
outputs/sessions/{session_id}.json
outputs/logs/{session_id}_events.jsonl
outputs/candidates/{session_id}/{candidate_id}.txt
outputs/rendered_levels/{session_id}/{candidate_id}.png
outputs/reports/{session_id}_report.md
```

---

## 11. Frontend Plan

### 11.1 Gradio tabs

1. Design Session
2. Candidate Board
3. Candidate Detail
4. Playtester View
5. Reports / Session History

### 11.2 UI goal

The UI should make candidate state visible and demonstrate the complete loop.

### 11.3 UI MVP

The UI is complete when it supports:

- creating/loading a session,
- generating or uploading candidates,
- showing candidate cards/table,
- running triage,
- sending a candidate to playtest,
- entering feedback,
- updating candidate state,
- generating a report.

---

## 12. Implementation Phases

### Phase 0 — Planning and scaffold

Deliverables:

- project README,
- research foundation,
- backend plan,
- frontend plan,
- architecture diagram,
- project structure.

### Phase 1 — Domain models and storage

Build:

- `DesignSession`,
- `LevelCandidate`,
- `CandidateState`,
- `CandidateEvent`,
- `SessionStore`,
- JSON save/load,
- event logging.

Exit criteria:

- create session,
- add candidate,
- save/load session,
- append event.

### Phase 2 — Candidate sources

Build:

- upload candidate path,
- sample candidate path,
- candidate artifact saving,
- basic rendering.

Exit criteria:

- candidate appears in session and has preview.

### Phase 3 — Project 6 triage adapter

Build:

- Project 6 adapter,
- triage service,
- P6 action to P7 candidate state mapping,
- candidate history update.

Exit criteria:

- uploaded/sample candidate can be triaged and state updates.

### Phase 4 — Playtest and Project 3 feedback adapter

Build:

- send-to-playtest transition,
- feedback submission,
- Project 3 adapter,
- positive/negative state mapping.

Exit criteria:

- feedback changes candidate state to complete or revision_needed.

### Phase 5 — Project 5 generation adapter

Build:

- Project 5 generator adapter,
- generated candidate storage,
- generated metadata,
- optional cached generation mode.

Exit criteria:

- generate one or more candidate levels and pass them to P6.

### Phase 6 — Report builder

Build:

- session report,
- candidate summary table,
- candidate histories,
- triage and feedback summaries,
- warnings and limitations.

Exit criteria:

- session report generated from JSON state.

### Phase 7 — Gradio UI

Build:

- tabs,
- candidate board,
- candidate detail,
- playtester view,
- report download.

Exit criteria:

- end-to-end demo through UI.

### Phase 8 — Notebook / script walkthrough

Build:

- integrated notebook or script,
- component checks,
- generated candidate scenario,
- uploaded candidate scenario,
- feedback loop scenario.

Exit criteria:

- reproducible execution artifact.

### Phase 9 — Evaluation and polish

Build:

- scenario outputs,
- cached demo fixtures,
- tests,
- screenshots,
- optional sprite rendering.

Exit criteria:

- final project is demo-ready.

### Phase 10 — Reflective synthesis paper and defense

Build:

- `Reflective_Synthesis_Paper.pdf`,
- mentor presentation,
- final artifact checklist.

Exit criteria:

- 1,500–2,000 word paper,
- citations,
- references,
- defense-ready slides.

---

## 13. Testing Plan

### 13.1 Unit tests

- domain model validation,
- allowed transitions,
- session store,
- event logging,
- report builder,
- basic renderer.

### 13.2 Adapter tests

- Project 3 classifier loads or cached output works,
- Project 5 generator produces/caches candidate,
- Project 6 triage returns valid action.

### 13.3 Integration tests

- uploaded candidate → triage → ready for playtest,
- generated candidate → triage,
- candidate sent to playtest → positive feedback → complete,
- candidate sent to playtest → negative feedback → revision needed,
- revision-needed candidate → revised candidate created.

### 13.4 UI callback tests

Test callbacks outside the Gradio event loop where possible.

---

## 14. Evaluation Plan

Evaluate realistic system scenarios.

### Scenario A — Generated candidate path

Goal: demonstrate Project 5 + Project 6 integration.

Expected:

- candidate generated,
- triage run,
- state updated,
- warning/next step shown.

### Scenario B — Uploaded candidate path

Goal: demonstrate designer-provided candidate support.

Expected:

- candidate uploaded,
- triage run,
- state updated.

### Scenario C — Positive playtest feedback

Goal: demonstrate Project 3 feedback loop.

Expected:

- candidate sent to playtest,
- feedback classified positive,
- candidate marked complete.

### Scenario D — Negative playtest feedback

Goal: demonstrate revision loop.

Expected:

- feedback classified negative,
- candidate state becomes revision_needed,
- revised candidate can be created.

### Scenario E — Ambiguous or contradictory brief

Goal: demonstrate responsible control.

Expected:

- P6 requests clarification or human review,
- system avoids forcing a recommendation.

---

## 15. Ethical and Responsible AI Considerations

### 15.1 Generated content risk

Generated candidates may be derivative or too similar to training examples. The system should expose novelty/derivative risk rather than hide it.

### 15.2 Feedback classifier limits

Project 3 feedback classification is a broad sentiment signal, not a complete playtest analysis. It should not be used as final proof of quality.

### 15.3 Human creative authority

The system should not automatically edit or finalize levels. Designers choose whether to revise, complete, reject, or continue.

### 15.4 Transparency

The system should persist:

- candidate source,
- triage action,
- feedback classification,
- event history,
- reports.

### 15.5 Responsible deployment

Real-world deployment would require more playtesting, broader data, user privacy controls, asset-license review, and professional QA.

---

## 16. Key Tradeoffs

| Tradeoff | Decision |
|---|---|
| Notebook vs UI | Build both: Gradio for workflow demo, notebook/script for reproducibility |
| Database vs JSON | Use JSON/JSONL for transparency and simplicity |
| Generated-only vs upload support | Support both to reduce dependence on limited generator |
| Ranking vs comparison | Start with candidate comparison; avoid new scoring system unless needed |
| Automatic editing vs recommendations | No automatic edits; designer creates revised candidate |
| Sprite rendering vs simple rendering | Simple renderer first; sprite polish only if time permits |
| Full Project 4 integration | Keep as future extension |

---

## 17. Required Final Artifacts

- Gradio app or executable workflow artifact,
- integrated notebook or script,
- source code,
- supporting docs,
- architecture diagram,
- session outputs and reports,
- cached demo artifacts,
- requirements.txt,
- Reflective_Synthesis_Paper.pdf,
- mentor presentation.

---

## 18. Definition of Done

The project is ready for submission when:

1. The system integrates at least Project 3, Project 5, and Project 6.
2. The integrated workflow produces observable outputs.
3. The UI demonstrates candidate-level workflow states.
4. A generated candidate path works.
5. An uploaded candidate path works.
6. A playtester feedback loop works.
7. Session JSON and reports are generated.
8. The architecture diagram is included.
9. The paper ties design decisions to prior projects.
10. Ethical considerations are specific to this system.
11. requirements.txt is generated.
12. The mentor presentation can be delivered in 15 minutes.

---

## 19. Defense Talking Points

- The system is not an autonomous level generator.
- Project 5 is useful as a candidate source but not final authority.
- Project 6 is the design-triage decision layer.
- Project 3 makes post-playtest feedback usable in the loop.
- Project 7 contributes orchestration, candidate lifecycle management, UI, persistence, and reporting.
- The system is designer-governed and transparent.
- The limitations of prior models directly informed the final design.

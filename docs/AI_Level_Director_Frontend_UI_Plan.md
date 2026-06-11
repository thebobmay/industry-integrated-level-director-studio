# AI Level Director Studio — Frontend / Gradio UI Plan

## 1. Purpose

The frontend should make the integrated workflow understandable and usable. A notebook can prove the pipeline works, but the final system is naturally a designer-facing workflow:

```text
brief → candidates → triage → playtest → feedback → complete or revise
```

A lightweight Gradio UI makes the system's human decision points visible and supports the final project's industry-focused, portfolio-ready narrative.

The UI should be functional, not overbuilt. It should help the reviewer see:

1. what the designer is trying to build,
2. which candidate levels exist,
3. where each candidate is in the workflow,
4. what the system recommends next,
5. how playtest feedback changes candidate state.

---

## 2. UI Design Principles

### 2.1 Designer-governed

The UI should make it clear that the designer controls the workflow:

- chooses generated vs uploaded candidates,
- selects which candidates to triage,
- decides whether to send candidates to playtest,
- reviews feedback and revision needs,
- marks candidates complete or creates revised versions.

### 2.2 Candidate-centered

The main UI object is the `LevelCandidate`, not the session.

The session is a workspace. Each candidate has its own state, history, triage result, feedback records, and next action.

### 2.3 Transparent

Every candidate should show:

- source,
- current state,
- P6 triage action,
- warnings,
- playtest readiness,
- feedback status,
- next step,
- history.

### 2.4 Light but functional

Do not build a full editor or game engine preview. The UI only needs enough functionality to demonstrate the integrated workflow.

---

## 3. User Roles

### 3.1 Designer

The designer:

- starts a design session,
- enters a brief,
- generates or uploads candidates,
- runs triage,
- sends selected candidates to playtest,
- reviews playtest results,
- creates revised candidate versions,
- downloads session reports.

### 3.2 Playtester

The playtester:

- sees candidates sent to playtest,
- reads playtest questions,
- enters feedback,
- submits feedback for Project 3 classification.

### 3.3 Reviewer / Mentor

The reviewer:

- observes the complete workflow,
- inspects candidate histories,
- downloads reports and session JSON,
- sees how prior projects integrate.

---

## 4. Recommended UI Structure

Use `gr.Blocks` with tabs.

```python
with gr.Blocks(title="AI Level Director Studio") as demo:
    gr.Markdown("# AI Level Director Studio")
    gr.Markdown("Designer-governed workflow for 2D platformer level iteration.")

    session_state = gr.State()

    with gr.Tab("Design Session"):
        ...

    with gr.Tab("Candidate Board"):
        ...

    with gr.Tab("Candidate Detail"):
        ...

    with gr.Tab("Playtester View"):
        ...

    with gr.Tab("Reports"):
        ...
```

---

## 5. Tab 1 — Design Session

### Purpose

Create or load a design workspace.

### Inputs

| Control | Type | Purpose |
|---|---|---|
| Design brief | Textbox | Natural language goal |
| Target difficulty | Dropdown | easy / medium / hard / unspecified |
| Novelty preference | Dropdown | style-consistent / balanced / original / unspecified |
| Candidate source | Radio | Generate / Upload / Sample |
| Number of generated candidates | Slider | Candidate batch size |
| Temperature | Slider | Project 5 sampling control |
| Session JSON upload | File | Load previous session |

### Buttons

- Start New Session
- Load Session JSON
- Save Session
- Generate Candidates
- Upload Candidate
- Load Sample Candidate

### Outputs

- Session ID
- Current design brief
- Candidate count
- Last action/status message

---

## 6. Tab 2 — Candidate Board

### Purpose

The Candidate Board is the main workspace. It should present candidates like cards, even if the implementation uses a DataFrame.

### Candidate board columns

| Column | Meaning |
|---|---|
| Candidate ID | Stable identifier |
| Title | Human-readable label |
| Source | generated / uploaded / sample / revised |
| State | candidate lifecycle state |
| Triage Action | P6 result |
| Readiness | ready / not ready / review needed |
| Feedback | none / positive / negative / unclear |
| Main Warning | Short warning summary |
| Next Step | UI-facing action recommendation |

### Actions

- Select Candidate
- Run Triage
- Run Triage on All Drafts
- Send to Playtest
- Create Revised Candidate
- Mark Complete
- Archive Candidate
- View Report

### Candidate card concept

Even if displayed in a table, each row should be understood as a card.

Example:

```text
G-001 — Generated
State: ready_for_playtest
Triage: accept_for_playtest
Warning: medium novelty risk
Next step: send to playtester
```

Example:

```text
G-002 — Generated
State: derivative_review_needed
Triage: flag_as_derivative_draft
Warning: high similarity to reference levels
Next step: human originality review
```

Example:

```text
U-001 — Uploaded
State: revision_needed
Triage: recommend_revision
Warning: opening difficulty spike
Next step: designer revision
```

### Outputs after selecting a candidate

- rendered level preview,
- raw tile text,
- P6 triage rationale,
- warnings,
- revision recommendations,
- playtest questions,
- candidate event history.

---

## 7. Tab 3 — Candidate Detail

### Purpose

Provide transparency and depth for a selected candidate.

### Display

| Section | Content |
|---|---|
| Candidate metadata | ID, source, state, iteration number, parent candidate |
| Rendered preview | Basic tile image or optional sprite image |
| Raw level text | Monospace tile grid |
| Triage summary | P6 action, readiness, rationale |
| Warnings | Novelty, difficulty, structure, ambiguity |
| Revision recommendation | Ordered suggestions from P6 |
| Playtest questions | Questions to send to tester |
| Feedback records | Project 3 results |
| History | Candidate event timeline |

### Buttons

- Download Level TXT
- Download Candidate Report
- View Triage Transcript
- Create Revised Candidate
- Send to Playtest

---

## 8. Tab 4 — Playtester View

### Purpose

Simulate the human playtesting step without building a playable game.

Only candidates in `sent_to_playtest` should appear here.

### Playtester sees

- candidate ID and title,
- rendered preview,
- design brief,
- playtest questions from P6,
- optional raw tile text,
- feedback textbox.

### Actions

- Submit Feedback
- Clear Feedback
- Return to Candidate Board

### Behavior after feedback

1. Project 3 classifier runs.
2. Feedback record is saved.
3. Candidate state updates:

| P3 Result | Candidate State |
|---|---|
| Positive | complete |
| Negative | revision_needed |
| Low confidence / unclear | human_review_needed |

### Example feedback

```text
The first jump felt unfair and frustrating, especially with the enemy close to the landing.
```

Expected state change:

```text
sent_to_playtest → revision_needed
```

---

## 9. Tab 5 — Reports / Session History

### Purpose

Generate reviewable artifacts for the final report and defense.

### Display

- session summary,
- candidate count by state,
- candidate table,
- completed candidates,
- candidates needing revision,
- playtest feedback summary,
- full event timeline,
- latest generated report preview.

### Buttons

- Generate Session Report
- Download Session JSON
- Download Markdown Report
- Download Candidate ZIP
- Export Screenshots / Preview Images

---

## 10. Level Rendering

### 10.1 MVP rendering

Start with:

- monospace raw tile grid,
- simple colored tile image.

### 10.2 Optional polish

At the end, if time permits, add sprite rendering with free or permissively licensed assets.

Important:

- do not use actual Mario/Nintendo sprites,
- document asset source and license,
- keep sprite rendering optional and replaceable.

### 10.3 UI rendering locations

| UI Location | Render Type |
|---|---|
| Candidate Board | small thumbnail or no image |
| Candidate Detail | full rendered image + raw text |
| Playtester View | full rendered image |
| Report | rendered preview image path |

---

## 11. Gradio View Models

The UI should consume view models, not raw domain objects.

### 11.1 Candidate board view

```python
def candidate_board_view(session: DesignSession) -> pd.DataFrame:
    ...
```

Columns:

```text
candidate_id
title
source
state
triage_action
readiness
feedback
main_warning
next_step
```

### 11.2 Candidate detail view

```python
def candidate_detail_view(session: DesignSession, candidate_id: str) -> dict:
    ...
```

Returns:

```text
metadata_markdown
rendered_preview_path
raw_level_text
triage_markdown
feedback_markdown
history_markdown
```

### 11.3 Playtest queue view

```python
def playtest_queue_view(session: DesignSession) -> pd.DataFrame:
    ...
```

Filters candidates where:

```text
workflow_state == "sent_to_playtest"
```

### 11.4 Session summary view

```python
def session_summary_view(session: DesignSession) -> str:
    ...
```

Returns Markdown summary for Reports tab.

---

## 12. UI Callback Design

Each UI button maps to one backend service command.

### Example callback structure

```python
def run_triage_ui(session_id: str, candidate_id: str):
    session = service.run_triage(session_id, candidate_id)
    return (
        session,
        candidate_board_view(session),
        candidate_detail_view(session, candidate_id),
        "Triage complete."
    )
```

### Callback rule

Callbacks should:

1. load or receive the current session,
2. call a backend service method,
3. save updated state,
4. return updated view models.

Callbacks should not directly load PyTorch models, pickle files, or P6 agent internals.

---

## 13. UI State Management

Use Gradio `State` for the active session object or session ID.

Recommended:

```python
active_session_id = gr.State(None)
selected_candidate_id = gr.State(None)
```

The backend should always save session JSON after meaningful actions so the UI can recover from restarts.

---

## 14. Human-in-the-Loop Demonstration

The UI makes the human role concrete:

1. Designer creates the brief.
2. Designer selects candidate source.
3. Designer chooses which candidates to triage.
4. Designer sends candidates to playtest.
5. Playtester provides feedback.
6. System updates candidate state.
7. Designer decides whether to revise, complete, or archive.

This supports the final paper's claim that the system is designer-governed rather than autonomous.

---

## 15. MVP UI Definition of Done

The frontend MVP is complete when:

1. A user can start a session.
2. A user can generate or upload candidates.
3. Candidates appear in a board/table with states.
4. A user can select a candidate and view details.
5. A user can run P6 triage from the UI.
6. A candidate can be sent to playtest.
7. The playtester tab accepts feedback.
8. Project 3 feedback changes candidate state.
9. A report can be generated and downloaded.
10. The app can reload an existing JSON session.

---

## 16. UI Polish Backlog

Add only after the core loop works:

- sprite-based level rendering,
- state badge colors,
- candidate thumbnail images,
- nicer card styling,
- screenshot export,
- richer candidate comparison,
- cached demo selector,
- example scenario buttons.

Avoid:

- full tile editor,
- drag-and-drop workflow board,
- Unity integration,
- playable game preview,
- login/user accounts,
- database-backed persistence,
- real-time multiplayer playtesting.

---

## 17. Presentation Demo Script

A five-to-seven-minute demo should show:

1. Start a session with a brief.
2. Generate three candidates or upload one candidate.
3. Run triage on candidates.
4. Send one candidate to the Playtester View.
5. Enter negative feedback.
6. Show candidate state changing to `revision_needed`.
7. Create a revised candidate.
8. Run triage again or show generated final report.

This demonstrates all three integrated prior projects and the new Project 7 workflow.

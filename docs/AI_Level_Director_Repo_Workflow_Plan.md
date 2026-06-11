# AI Level Director Studio — Repository Workflow Plan

## Purpose

This document defines the Git and repository workflow for the **AI Level Director Studio** final integrated capstone project. The project is more complex than earlier capstones because it combines multiple prior systems into a new integrated artifact:

- Project 5 generative level candidate creation
- Project 6 agentic candidate triage
- Project 3 playtest feedback classification
- Project 7 orchestration, UI, state management, session persistence, reporting, and synthesis documentation

The repository workflow should support professional development discipline without adding unnecessary process overhead. The goal is to keep the project stable, reviewable, reproducible, and easy to defend during the final mentor presentation.

---

## Repository Workflow Philosophy

Use a **structured trunk-based workflow with a `dev` integration branch**, short-lived feature branches, milestone tags, and a final release branch.

This is lighter than full enterprise GitFlow but more disciplined than committing everything directly to `main`.

The workflow should ensure:

1. `main` always represents a stable, submission-safe version.
2. `dev` serves as the working integration branch.
3. Feature branches isolate meaningful chunks of work.
4. Documentation, experiments, and release prep are separated clearly.
5. Milestone tags preserve recoverable checkpoints.
6. Pull requests create a visible review trail, even for solo work.

---

## Branch Model

### Long-Lived Branches

| Branch | Purpose | Rules |
|---|---|---|
| `main` | Stable, tested, submission-safe project state | Do not commit directly. Merge only from `dev` or `release/*`. |
| `dev` | Integration branch for completed features | Feature branches merge here first. Should remain runnable. |

### Short-Lived Branch Prefixes

| Prefix | Purpose | Example |
|---|---|---|
| `feature/*` | New backend, frontend, notebook, adapter, or test functionality | `feature/session-store` |
| `docs/*` | Planning docs, synthesis paper, README, mentor presentation materials | `docs/synthesis-paper` |
| `fix/*` | Small bug fixes | `fix/session-load-path` |
| `experiment/*` | Risky or optional exploratory work | `experiment/sprite-renderer` |
| `release/*` | Final packaging and submission stabilization | `release/final-submission` |
| `archive/*` | Optional preserved dead-end branches | `archive/old-ui-layout` |

---

## Recommended Branch Structure

```text
main
└── dev
    ├── docs/planning-documents
    ├── feature/project-scaffold
    ├── feature/domain-models
    ├── feature/session-store
    ├── feature/candidate-state-machine
    ├── feature/event-log
    ├── feature/mock-adapters
    ├── feature/basic-renderer
    ├── feature/report-builder
    ├── feature/project3-feedback-adapter
    ├── feature/project5-generator-adapter
    ├── feature/project6-triage-adapter
    ├── feature/notebook-demo
    ├── feature/gradio-ui
    ├── docs/synthesis-paper
    ├── docs/mentor-defense
    └── release/final-submission
```

---

## Initial Repository Setup

Create or clone the repository, then initialize the stable branches.

```bash
git checkout main
git pull

git checkout -b dev
git push -u origin dev
```

Set a personal rule:

```text
Never commit directly to main.
Never use main for experiments.
Never merge to main unless dev is runnable and tested.
```

If using GitHub branch protection, protect `main` from direct pushes.

---

## Development Workflow

### 1. Start from `dev`

```bash
git checkout dev
git pull
```

### 2. Create a feature branch

```bash
git checkout -b feature/session-store
```

### 3. Work in small logical units

Good feature branch size:

- one adapter
- one domain model module
- one state transition module
- one UI tab
- one report builder feature
- one notebook section
- one test fixture group

Avoid branches that contain unrelated backend, frontend, report, and paper edits all at once.

### 4. Commit regularly

```bash
git status
git add src/ai_level_director/storage/session_store.py tests/test_session_store.py
git commit -m "Add JSON session store"
```

### 5. Validate before merge

At minimum:

```bash
pytest
python -m compileall src
```

If the branch touches the notebook or UI, also run the relevant demo manually.

### 6. Merge into `dev`

```bash
git checkout dev
git pull
git merge feature/session-store
git push
```

Alternatively, open a GitHub pull request into `dev` and merge after reviewing the diff.

### 7. Delete merged feature branches

```bash
git branch -d feature/session-store
git push origin --delete feature/session-store
```

---

## Pull Request Workflow

Use pull requests even as a solo developer. PRs create a professional review trail and help prepare final report notes.

### Pull Request Target Rules

| Source Branch | Target Branch |
|---|---|
| `feature/*` | `dev` |
| `docs/*` | `dev` |
| `fix/*` | `dev` or `main`, depending on urgency |
| `release/*` | `main` |

### Suggested PR Template

```markdown
## Summary
What changed in this branch?

## Project Area
- [ ] Backend
- [ ] Frontend / Gradio UI
- [ ] Notebook demo
- [ ] Prior project integration
- [ ] Documentation
- [ ] Tests
- [ ] Report / presentation support

## Validation
How was this tested?

## Outputs / Artifacts
What files, screenshots, reports, or session outputs were produced?

## Notes / Risks
What is incomplete, risky, or deferred?
```

---

## Commit Message Style

Use concise, specific commit messages.

### Good Examples

```text
Add candidate domain models
Add JSON session persistence
Implement candidate state transition rules
Add mock project adapters
Add basic tile renderer
Wire Project 3 feedback adapter
Add Gradio candidate board tab
Add notebook demo scenario A
Generate session report from saved state
Update README with setup instructions
```

### Avoid

```text
updates
stuff
fixed things
final changes
work in progress
```

A commit should describe the change clearly enough that it helps future review and defense preparation.

---

## Project Build Phases and Branches

## Phase 0 — Planning and Scaffold

### Branches

```text
docs/planning-documents
feature/project-scaffold
```

### Work Items

- Add planning documents under `docs/`
- Add project README skeleton
- Add package structure
- Add placeholder `app.py`
- Add placeholder `integrated_system_demo.ipynb`
- Add `.gitignore`
- Add initial `requirements.txt` placeholder or environment note

### Completion Criteria

- Repository structure is clear
- Planning docs are committed
- Project can be opened cleanly in the IDE
- `main` and `dev` branches exist

### Suggested Tag

```bash
git tag -a v0.1-planning-complete -m "Planning documents and repository scaffold complete"
git push origin v0.1-planning-complete
```

---

## Phase 1 — Core Backend Foundation

### Branches

```text
feature/domain-models
feature/session-store
feature/candidate-state-machine
feature/event-log
```

### Work Items

- Define `DesignSession`
- Define `LevelCandidate`
- Define `TriageResult`
- Define `FeedbackResult`
- Define `CandidateEvent`
- Implement candidate state enum / literals
- Implement allowed state transitions
- Implement JSON session saving and loading
- Implement JSONL event logging
- Add unit tests for state transitions and session persistence

### Completion Criteria

- A design session can be created, saved, loaded, and updated
- Multiple candidates can exist within one session
- Each candidate maintains its own state and event history
- Invalid transitions are blocked or handled intentionally

### Suggested Tag

```bash
git tag -a v0.2-backend-skeleton -m "Core domain models and state workflow complete"
git push origin v0.2-backend-skeleton
```

---

## Phase 2 — Mock Workflow Demo

### Branches

```text
feature/mock-adapters
feature/basic-renderer
feature/report-builder
```

### Work Items

- Add mock Project 5 generator adapter
- Add mock Project 6 triage adapter
- Add mock Project 3 feedback adapter
- Add basic ASCII renderer
- Add simple image renderer using generated tile colors or symbols
- Add Markdown report builder
- Add a mocked full workflow test

### Why This Phase Matters

The system should work end-to-end before live prior project integrations are added. Mock adapters allow the backend workflow, UI callbacks, and notebook demo to be tested without being blocked by model paths, API keys, GPU requirements, or agent variability.

### Completion Criteria

- Start session
- Create multiple mock candidates
- Run mock triage
- Send candidate to playtest
- Submit mock feedback
- Update candidate state
- Generate session report

### Suggested Tag

```bash
git tag -a v0.3-mock-demo-working -m "End-to-end workflow works with mock adapters"
git push origin v0.3-mock-demo-working
```

---

## Phase 3 — Prior Project Integrations

### Branches

```text
feature/project3-feedback-adapter
feature/project5-generator-adapter
feature/project6-triage-adapter
```

### Work Items

- Wrap Project 3 feedback classifier behind `Project3FeedbackAdapter`
- Wrap Project 5 generator behind `Project5GeneratorAdapter`
- Wrap Project 6 triage system behind `Project6TriageAdapter`
- Add adapter-level tests
- Add cached fixture outputs for reproducibility
- Support live mode and cached mode where practical

### Integration Principles

- Project 7 should not rewrite prior project logic
- Adapters should hide model loading and internal implementation details
- The backend service should call simple adapter methods
- UI and notebook should never directly call prior project internals

### Completion Criteria

- Each adapter can be called independently
- Each adapter returns Project 7 domain objects or normalized outputs
- Cached demo mode works without live model execution
- Live mode works where environment and credentials permit

### Suggested Tag

```bash
git tag -a v0.4-integrations-working -m "Prior project adapters integrated"
git push origin v0.4-integrations-working
```

---

## Phase 4 — Notebook and Frontend Artifacts

### Branches

```text
feature/notebook-demo
feature/gradio-ui
feature/session-report-export
```

### Work Items

- Build `integrated_system_demo.ipynb`
- Build Gradio app in `app.py`
- Add candidate board table
- Add candidate detail view
- Add playtester tab
- Add session report tab
- Add download/export outputs
- Add screenshots or saved demo artifacts

### Notebook Principle

The notebook should call the same backend service as the Gradio UI.

```text
Notebook -> LevelDirectorService
Gradio   -> LevelDirectorService
```

Avoid duplicating workflow logic inside the notebook.

### Completion Criteria

- Notebook runs step by step from session creation to final report
- Gradio app can demonstrate the same workflow interactively
- Candidate state changes are visible in both artifacts
- Saved outputs can be inspected after execution

### Suggested Tag

```bash
git tag -a v0.5-demo-artifacts-working -m "Notebook and Gradio demos working"
git push origin v0.5-demo-artifacts-working
```

---

## Phase 5 — Final Documentation and Submission

### Branches

```text
docs/synthesis-paper
docs/mentor-defense
release/final-submission
```

### Work Items

- Write `Reflective_Synthesis_Paper.pdf`
- Prepare mentor defense presentation
- Finalize README
- Finalize architecture diagram
- Finalize backend/frontend docs
- Confirm requirements file
- Confirm notebook execution
- Confirm Gradio launch instructions
- Confirm demo outputs and reports
- Clean unneeded files

### Completion Criteria

- All required artifacts are present
- Notebook and/or app produces observable outputs
- `requirements.txt` exists
- Documentation explains how to run and understand the system
- Final paper meets 1,500–2,000 word requirement
- Final artifact clearly integrates at least three prior projects

### Suggested Tag

```bash
git tag -a v1.0-submission -m "Final integrated capstone submission"
git push origin v1.0-submission
```

---

## Milestone Tag Plan

| Tag | Meaning |
|---|---|
| `v0.1-planning-complete` | Planning docs and repository scaffold complete |
| `v0.2-backend-skeleton` | Domain models, candidate states, and session persistence complete |
| `v0.3-mock-demo-working` | End-to-end workflow works with mock adapters |
| `v0.4-integrations-working` | Prior project adapters integrated |
| `v0.5-demo-artifacts-working` | Notebook and Gradio demos working |
| `v0.6-report-ready` | Final report and documentation ready for review |
| `v1.0-submission` | Final submission state |

---

## Experiment Branches

Use `experiment/*` for risky or optional polish.

Examples:

```text
experiment/sprite-renderer
experiment/gradio-card-layout
experiment/project5-loading-optimization
experiment/candidate-thumbnail-grid
```

Rules:

1. Experiments branch from `dev`.
2. Experiments do not merge directly to `main`.
3. If an experiment succeeds, either merge into `dev` through PR or cherry-pick useful commits into a proper `feature/*` branch.
4. If an experiment fails, delete it or preserve it under `archive/*` only if it documents a meaningful design decision.

---

## Release Branch Workflow

When the system is mostly complete, create a release branch.

```bash
git checkout dev
git pull
git checkout -b release/final-submission
```

Use this branch only for:

- final cleanup
- documentation polish
- final notebook execution
- report export
- requirements generation
- packaging checks
- final artifact verification

After final validation:

```bash
git checkout main
git pull
git merge release/final-submission
git push

git tag -a v1.0-submission -m "Final integrated capstone submission"
git push origin v1.0-submission
```

---

## Recommended Repository Structure

```text
ai-level-director-studio/
├── app.py
├── integrated_system_demo.ipynb
├── README.md
├── requirements.txt
├── .env.example
├── .gitignore
│
├── docs/
│   ├── AI_Level_Director_Backend_Plan.md
│   ├── AI_Level_Director_Frontend_UI_Plan.md
│   ├── AI_Level_Director_Complete_Project_Plan.md
│   ├── AI_Level_Director_System_Architecture_Diagram.md
│   ├── AI_Level_Director_Research_Foundation.md
│   ├── AI_Level_Director_Repo_Workflow_Plan.md
│   └── Reflective_Synthesis_Paper.pdf
│
├── src/
│   └── ai_level_director/
│       ├── domain/
│       ├── workflow/
│       ├── adapters/
│       ├── storage/
│       ├── rendering/
│       ├── reporting/
│       └── ui/
│
├── integrations/
│   ├── project3_feedback/
│   ├── project5_generator/
│   └── project6_triage/
│
├── data/
│   ├── sample_levels/
│   ├── uploaded_levels/
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
│   ├── rendered_levels/
│   └── demo_session/
│
└── tests/
    ├── fixtures/
    ├── test_session_store.py
    ├── test_candidate_states.py
    ├── test_report_builder.py
    ├── test_project3_adapter.py
    ├── test_project5_adapter.py
    └── test_project6_adapter.py
```

---

## Files to Keep Out of Git

Use `.gitignore` to avoid committing unnecessary or sensitive files.

**Model artifacts are tracked in this project.** The prior project artifacts copied into `models/` (the Project 5 `.pt` checkpoint and tokenizer, the Project 3 classifier and vectorizer pickles) are small enough to fit well under GitHub's 100 MB per file limit, so they are committed to keep the repository self contained and reproducible. Do not gitignore `*.pt`, `*.pkl`, or `*.joblib`. Only exclude a model artifact if a specific file exceeds GitHub's size limit, in which case document where to obtain it instead.

Recommended exclusions:

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
venv/
.env

# Jupyter
.ipynb_checkpoints/

# Regenerated runtime outputs (keep the curated demo session and dir structure)
outputs/sessions/*
outputs/logs/*
outputs/candidates/*
outputs/rendered_levels/*
outputs/reports/*
outputs/screenshots/*
!**/.gitkeep
!outputs/demo_session/

# OS / IDE
.DS_Store
.vscode/
.cursor/
```

Model artifacts under `models/` are intentionally not excluded.

If saved demo outputs are needed for review, place a curated set under:

```text
outputs/demo_session/
```

and document them clearly.

---

## Review Checklist Before Merging to `dev`

Before merging any branch into `dev`, confirm:

- [ ] Code runs without syntax errors
- [ ] Relevant tests pass
- [ ] No secrets or API keys committed
- [ ] No unnecessary large artifacts committed
- [ ] README or docs updated if behavior changed
- [ ] Output files are either ignored or intentionally included
- [ ] Branch has a clear commit history

---

## Review Checklist Before Merging to `main`

Before merging `dev` or `release/final-submission` into `main`, confirm:

- [ ] Notebook demo runs or cached demo executes successfully
- [ ] Gradio app launches
- [ ] At least one full scenario produces observable outputs
- [ ] JSON session file is saved correctly
- [ ] Event log is saved correctly
- [ ] Markdown report is generated
- [ ] Architecture documentation is current
- [ ] `requirements.txt` exists
- [ ] Final paper and presentation assets are current if applicable
- [ ] No broken links in README

---

## Suggested First Branches

Start with documentation and scaffold.

```bash
git checkout dev
git checkout -b docs/planning-documents
```

Commit planning docs:

```bash
git add docs/
git commit -m "Add project planning documents"
git push -u origin docs/planning-documents
```

Then start the code scaffold:

```bash
git checkout dev
git pull
git checkout -b feature/project-scaffold
```

Add package directories, placeholder files, `.gitignore`, README skeleton, `app.py`, and notebook shell.

---

## Final Recommendation

Use this workflow throughout the project:

```text
feature branch -> pull request -> dev -> tested milestone -> main -> tag
```

This provides enough structure for a complex integrated capstone without slowing the project down with enterprise-level process. It also creates a visible professional development trail that supports the final synthesis paper, mentor defense, and portfolio presentation.

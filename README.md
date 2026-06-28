# AI Level Director Studio

A designer governed workflow for 2D platformer level iteration.

**Student:** Robert Mayfield

## Project Description

AI Level Director Studio is the final integrated capstone artifact. It is a compound AI system that helps a human level designer move candidate 2D platformer level segments through a structured loop: generate or upload candidates, triage them before playtesting, send a ready candidate to a playtester, classify the returned feedback, then decide whether to complete, revise, or review the candidate. The system is advisory and designer governed. It never edits a level, never finalizes a level on its own, and never claims to predict whether a level is fun.

It does not introduce a new model or agent. It contributes the orchestration layer, the candidate lifecycle, persistence, reporting, and a thin interface that turn three prior capstone projects into one coherent, auditable workflow.

## Industry Context and Problem

The target industry is independent and small team game development. These teams need to iterate quickly on level design ideas, but review and playtesting are expensive and raw generated content cannot be trusted as a finished asset. Generative AI can produce candidate content fast, yet a generated segment may be structurally invalid, misaligned with the design intent, or derivative of its training data. The real problem is the move from "an AI can produce a candidate" to "a designer can responsibly decide what to do with that candidate." This system addresses that gap by screening, triaging, and tracking candidates while keeping every creative decision in human hands and disclosing originality and intellectual property risk rather than hiding it.

## Integrated Prior Projects

The system integrates three prior capstone projects, each wrapped behind an adapter so the studio coordinates them without rewriting them.


| Prior project                                           | Role here            | Adapter                    | Lesson carried forward                                                                                                                                                                                                                                               |
| ------------------------------------------------------- | -------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Generative AI (conditional Transformer level generator) | Candidate source     | `Project5GeneratorAdapter` | Generated levels are drafts, not final assets; high similarity to training data is disclosed as derivative risk.                                                                                                                                                     |
| Agentic AI (level design triage agent)                  | Triage authority     | `Project6TriageAdapter`    | The agent owns design judgment, not facts; it is reused unchanged and its reasoning is never duplicated.                                                                                                                                                             |
| Machine Learning (player feedback classifier)           | Post playtest signal | `Project3FeedbackAdapter`  | The classifier is a broad reception signal, not a complete playtest analysis; it returns a label with no confidence. Short feedback is flagged as low reliability, and the designer can override the classifier's label while its original call stays on the record. |


The prior project code lives in a few places: the Agentic AI triage agent is vendored under `integrations/project6_triage/`, the Generative AI model architecture is under `src/ai_level_director/adapters/project5_model/`, and the trained Generative AI and Machine Learning model artifacts are under `models/`. Each adapter returns Project 7 domain objects, so the mock and real adapters are interchangeable.

## Files Included

```text
app.py                          Gradio app; calls the service facade only
integrated_system_demo.ipynb    Reproducible end to end walkthrough
src/ai_level_director/           Implementation package
  domain/                        Pydantic models, states, events
  workflow/                      Service facade, candidate state machine, sources
  adapters/                      Project 5, 6, 3 adapters, interfaces, mocks
    project5_model/              Generative AI model architecture (vendored)
  storage/                       JSON session store, JSONL event log, paths
  rendering/                     ASCII level renderer
  reporting/                     Markdown session report builder
  ui/                            View models and framework free callbacks
integrations/project6_triage/    Agentic AI triage agent (vendored)
data/                            Sample levels and scenarios
models/                          Trained Generative AI and Machine Learning artifacts
outputs/                         Sessions, logs, candidates, reports, triage transcripts
  demo_session/                  Curated example sessions, one per evaluation scenario
docs/architecture/               Architecture diagrams (Mermaid + rendered PNG)
docs/Reflective_Synthesis_Paper.pdf   The reflective synthesis paper
tests/                           Pytest suite
```



## How to Run

The project targets Python 3.13 and runs on CPU; no GPU is required.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS or Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (only needed for live mode)
copy .env.example .env         # Windows  (cp on macOS or Linux)
# then set OPENAI_API_KEY in .env
```

Environment variables (see `.env.example`):

- `OPENAI_API_KEY`: credentials for the Agentic AI triage agent (live mode only).
- `TRIAGE_MODEL`: model identifier for the triage agent, in provider:model form.
- `OPENAI_BASE_URL`: optional override for a compatible provider.

There is no offline environment switch. For a keyless run, launch `python app.py` and set the engine toggle to Mock, or run `pytest`.

Run the pieces:

```bash
python app.py        # launch the Gradio UI (toggle Live/Mock in the app)
pytest               # run the test suite
jupyter lab          # open integrated_system_demo.ipynb for the walkthrough
```

The Gradio app and the notebook both call the same `LevelDirectorService`, so they run the same workflow. Mock mode needs no API key and is instant, which is useful for trying the loop or running tests without cost.

### Bundled sample levels for demonstration

Load these from the **Bundled sample** dropdown in the app (no upload needed), then run triage:


| Sample                | What it demonstrates                                                                                                                                                       |
| --------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `easy_opener`         | A valid easy segment that accepts for playtest. The happy path: triage, send to playtest, classify feedback, complete.                                                     |
| `hard_segment`        | Structurally valid but reads hard (a wide pit); against an easy brief, triage recommends revision.                                                                         |
| `derivative_draft`    | A near duplicate of a known reference level; triage catches it as derivative and routes it back. Set the session novelty preference to `original` for the clearest result. |
| `structural_defect`   | A pipe top with no support; triage rejects it as structurally invalid before playtest.                                                                                     |
| `beginner_excitement` | A second valid segment, useful as an alternative or a revision target.                                                                                                     |


Two outcomes are not driven by the level:

- **Clarification:** enter a self contradictory brief, for example "a relaxing beginner segment that is also brutally hard," and triage requests clarification rather than forcing a recommendation.
- **Feedback override:** after a candidate reaches playtest, submit feedback on the Playtester tab, then override the classifier's label from the Candidate Detail tab.

Triage is a live language model, so the exact action can vary between runs, but the underlying facts (validity, difficulty, novelty similarity) are deterministic.

## Architecture Overview

The Gradio UI and the notebook call one service facade, `LevelDirectorService`. The facade holds the command logic, delegates lifecycle rules to the candidate state machine, and reaches each prior project only through an adapter. State is tracked per candidate, persisted as a JSON session snapshot plus an append only JSONL event log. Each triage run also saves the agent's full deliberation transcript and a designer report as separate files, indexed by the event log, so any recommendation can be audited.

```text
Designer / Playtester / Reviewer
      ↓
Gradio UI (tabs + callbacks + view models)
      ↓
LevelDirectorService (facade + command logic)
      ↓
Candidate state machine · Adapters (Project 5 · 6 · 3)
      ↓
SessionStore (JSON) · Event Log (JSONL) · ReportBuilder · ASCII Renderer
```

Full diagrams (system architecture, candidate lifecycle state machine, end to end sequence, and integration boundaries) are in `docs/architecture/`.

## Requirements

- Python 3.13, CPU only.
- Core libraries: Pydantic and Pydantic AI, Gradio, PyTorch (CPU build), scikit-learn, pandas. The pinned set is in `requirements.txt`.
- An OpenAI compatible API key is required only for live triage; mock mode runs offline.


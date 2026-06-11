# AI Level Director Studio

A designer governed workflow for 2D platformer level iteration.

**Student:** Robert Mayfield

## Project Description

AI Level Director Studio is the final integrated capstone artifact. It is a
compound AI system that helps a human level designer move candidate 2D platformer
level segments through a structured loop: generate or upload candidates, triage
them before playtesting, send a ready candidate to a playtester, classify the
returned feedback, then decide whether to complete, revise, or review the
candidate. The system is advisory and designer governed. It never edits a level,
never finalizes a level on its own, and never claims to predict whether a level
is fun.

## Industry Context and Problem

(To be written.) Small and resource constrained game teams need faster, safer
ways to evaluate and iterate on candidate level content. Generative AI can
produce candidates, but raw generated content can be derivative, structurally
flawed, or misaligned with design intent, so it cannot be trusted as final
output.

## Integrated Prior Projects

The system integrates three prior capstone projects, each wrapped behind an
adapter. Project 7 orchestrates them and does not rewrite their logic.

- **Project 5, Generative AI** (conditional Transformer level generator): a
  source of candidate level drafts.
- **Project 6, Agentic AI** (level design triage agent): the single candidate
  triage and design readiness authority.
- **Project 3, Applied ML** (feedback classifier): a post playtest reception
  signal, positive or negative.

## Files Included

(To be completed as the project is built.)

- `app.py` — Gradio UI for the designer workflow.
- `integrated_system_demo.ipynb` — reproducible end to end walkthrough.
- `src/ai_level_director/` — implementation package.
- `models/` — prior project artifacts (tracked for reproducibility).
- `docs/` — backend, frontend, architecture, repo workflow, and research docs.
- `outputs/` — session JSON, event logs, candidate files, reports, screenshots.
- `tests/` — pytest suite.

## How to Run

(To be completed.) The project targets Python 3.13.

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` for live Project 6 triage.
A cached mode is available for running the workflow without live model calls.

## Architecture Overview

The Gradio UI is a thin layer over a `LevelDirectorService` facade. A workflow
controller applies candidate lifecycle transitions and calls the three adapters.
Sessions are persisted as JSON, with a JSONL event log and Markdown reports. See
`docs/AI_Level_Director_System_Architecture_Diagram.md`.

## Requirements

Python 3.13. Generate `requirements.txt` from the working environment with
`pip freeze > requirements.txt` before submission.

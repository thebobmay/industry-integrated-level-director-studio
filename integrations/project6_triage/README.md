# Vendored Project 6 triage agent

`src/` here is a verbatim copy of the Project 6 repository
(`agentic-ai-level-design-triage-agent`) source, and `reference_levels/` is its
cited reference library used by the novelty tool. They are vendored so this repo is
self contained and the triage agent can be integrated as built.

Project 6 imports its own modules as `from src.X import ...`, so the
`Project6TriageAdapter` adds this directory to `sys.path` to make the `src` package
resolve, then imports `triage_candidate`. The code is not modified.

Live triage calls an OpenAI model (set `OPENAI_API_KEY` and optionally
`TRIAGE_MODEL`). The mock triage adapter remains the offline path for tests.

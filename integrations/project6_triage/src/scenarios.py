"""Scenario loading.

Loads the natural language design briefs and their paired candidate fixtures from
data/scenarios.json into typed objects, and builds a triage request for each.
"""

from __future__ import annotations

import json
from pathlib import Path

from src.level_io import load_level
from src.models import ScenarioDefinition, TriageRequest

SCENARIOS_PATH = "data/scenarios.json"
CANDIDATE_DIR = "data/candidate_levels"


def load_scenarios(path: str | Path = SCENARIOS_PATH) -> list[ScenarioDefinition]:
    """Load and validate the scenario definitions from the JSON fixture."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [ScenarioDefinition(**entry) for entry in raw]


def load_candidate(scenario: ScenarioDefinition, candidate_dir: str | Path = CANDIDATE_DIR) -> str:
    """Load the candidate level text for a scenario."""
    return load_level(Path(candidate_dir) / scenario.candidate_file)


def build_triage_request(
    scenario: ScenarioDefinition,
    candidate_dir: str | Path = CANDIDATE_DIR,
) -> TriageRequest:
    """Build a TriageRequest for a scenario by loading its candidate level."""
    return TriageRequest(
        brief_text=scenario.brief_text,
        candidate_level=load_candidate(scenario, candidate_dir),
    )


def acceptable_actions(scenario: ScenarioDefinition) -> set[str]:
    """Return the defensible actions for a scenario (the expected action if none given)."""
    return set(scenario.acceptable_actions) if scenario.acceptable_actions else {scenario.expected_action}

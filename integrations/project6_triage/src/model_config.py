"""Model configurations and pricing for the model selection experiment.

Each ModelConfig pairs a Pydantic AI model identifier with the settings
appropriate to its class (chat models pin temperature 0; reasoning models leave
settings unset) and its current API pricing, so the experiment can run every
model fairly and compute token cost. Prices are USD per one million tokens and are
editable; update them if the rates change. Raw token counts are reported
regardless of price.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelConfig:
    """A model to run: its id, per-run settings, and pricing for cost estimates."""

    label: str
    model: str
    settings: dict | None
    input_price_per_1m: float
    output_price_per_1m: float


# Chat models pin temperature 0 for reproducibility. gpt-5.1 is a reasoning model:
# it does not accept a forced temperature and runs through the Responses API, so its
# settings are left unset. Prices current as of June 2026 (see the report references).
GPT_4O_MINI = ModelConfig("gpt-4o-mini", "openai-chat:gpt-4o-mini", {"temperature": 0.0}, 0.15, 0.60)
GPT_4_1 = ModelConfig("gpt-4.1", "openai-chat:gpt-4.1", {"temperature": 0.0}, 2.00, 8.00)
GPT_5_1 = ModelConfig("gpt-5.1", "openai-responses:gpt-5.1", None, 1.25, 10.00)

# The experiment's cheapest baseline, used only as a default reference in this module.
# The deployed triage model is gpt-4.1, set by TRIAGE_MODEL in src/agents.py.
DEFAULT_MODEL_CONFIG = GPT_4O_MINI

# The three models compared in the model selection experiment.
EXPERIMENT_MODELS = [GPT_4O_MINI, GPT_4_1, GPT_5_1]


def estimate_cost(input_tokens: int, output_tokens: int, config: ModelConfig) -> float:
    """Estimate USD cost for a token count under a model's pricing."""
    return (
        input_tokens / 1_000_000 * config.input_price_per_1m
        + output_tokens / 1_000_000 * config.output_price_per_1m
    )

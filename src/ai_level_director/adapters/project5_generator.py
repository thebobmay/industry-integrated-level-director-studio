"""Project 5 generator adapter.

Wraps the Project 5 conditional Transformer level generator behind the
GeneratorAdapter interface. It rebuilds the model from the vendored architecture,
loads the trained weights from ``models/project5_generator/``, and samples
candidate level chunks autoregressively, conditioned on a difficulty control
token.

Generated levels are candidate drafts, not final assets. Project 5's known
limitation is high nearest neighbour similarity to its small training corpus, so
candidates still require triage before playtest. The model hyperparameters and
tile vocabulary reproduce the Project 5 training setup; the sampling loop is
implemented here because Project 5's generation code lived in its notebook.
"""

from __future__ import annotations

from pathlib import Path

import torch
import torch.nn.functional as F

from ai_level_director.adapters.project5_model.model import LevelTransformer
from ai_level_director.adapters.project5_model.tokenizer import (
    CONTROL_TOKENS,
    SEQ_LEN,
    VOCAB_SIZE,
    decode_sequence,
)

# Repo root is three levels up: adapters -> ai_level_director -> src.
_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_WEIGHTS_PATH = _REPO_ROOT / "models" / "project5_generator" / "level_generator.pt"

# Architecture of the trained level_generator.pt checkpoint (from the Project 5
# training config). The model was trained on the 448 token inputs, so its position
# embeddings are sized SEQ_LEN - 1.
_D_MODEL = 256
_N_HEADS = 8
_N_LAYERS = 4
_MODEL_SEQ_LEN = SEQ_LEN - 1

# Map the P7 difficulty vocabulary to Project 5 control token labels.
_DIFFICULTY_LABEL = {"easy": "Easy", "medium": "Medium", "hard": "Hard"}

MODEL_NAME = "project5-conditional-transformer"


class Project5GeneratorAdapter:
    """Generate candidate level chunks with the Project 5 conditional Transformer."""

    def __init__(self, weights_path: Path | str = DEFAULT_WEIGHTS_PATH) -> None:
        """Rebuild the model and load the trained weights in eval mode."""
        self._model = LevelTransformer(
            vocab_size=VOCAB_SIZE,
            d_model=_D_MODEL,
            n_heads=_N_HEADS,
            n_layers=_N_LAYERS,
            seq_len=_MODEL_SEQ_LEN,
        )
        state = torch.load(Path(weights_path), map_location="cpu", weights_only=True)
        self._model.load_state_dict(state)
        self._model.eval()

    def generate(
        self,
        target_difficulty: str,
        n: int = 1,
        temperature: float = 1.2,
        seed: int | None = None,
    ) -> list[str]:
        """Sample n candidate level chunks for the target difficulty.

        Returns a list of level texts, each a 14 row by 32 column tile grid. A seed
        makes sampling reproducible. The difficulty control tokens are masked
        during tile sampling so every generated tile is a valid level tile.
        """
        label = _DIFFICULTY_LABEL.get(target_difficulty.lower())
        if label is None:
            raise ValueError(f"Unknown target difficulty: '{target_difficulty}'.")
        if temperature <= 0:
            raise ValueError("Temperature must be greater than 0.")
        if seed is not None:
            torch.manual_seed(seed)
        control = CONTROL_TOKENS[label]
        return [self._sample_one(control, temperature) for _ in range(n)]

    def _sample_one(self, control: int, temperature: float) -> str:
        """Autoregressively sample one level chunk and return its tile text."""
        tokens = [control]
        control_ids = list(CONTROL_TOKENS.values())
        with torch.no_grad():
            while len(tokens) < SEQ_LEN:
                x = torch.tensor([tokens], dtype=torch.long)
                logits = self._model(x)[0, -1]
                logits[control_ids] = float("-inf")  # tiles are never control tokens
                probs = F.softmax(logits / temperature, dim=-1)
                tokens.append(int(torch.multinomial(probs, num_samples=1)))
        rows = decode_sequence(tokens)["rows"]
        return "\n".join(rows)

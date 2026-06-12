"""Vocabulary, tokenization, and PyTorch Dataset for VGLC level sequences."""
import torch
from torch.utils.data import Dataset

# VGLC SMB1 tile vocabulary in canonical sorted order
TILE_CHARS = ['-', '<', '>', '?', 'B', 'E', 'Q', 'S', 'X', '[', ']', 'b', 'o']

CHAR_TO_ID = {ch: i for i, ch in enumerate(TILE_CHARS)}
ID_TO_CHAR  = {i: ch for ch, i in CHAR_TO_ID.items()}

# Difficulty control tokens assigned IDs after the tile vocabulary
CONTROL_TOKENS      = {"Easy": 13, "Medium": 14, "Hard": 15}
CONTROL_TOKEN_NAMES = {v: k for k, v in CONTROL_TOKENS.items()}

VOCAB_SIZE = 16   # 13 tile characters + 3 control tokens
SEQ_LEN    = 449  # 1 control token + 14 rows x 32 columns


def tokenize_chunk(chunk: dict, difficulty_label: str) -> list[int]:
    """Convert a level chunk and difficulty label into a token sequence.

    The difficulty control token is prepended as the first element,
    followed by tile tokens read row by row from top to bottom.

    Parameters
    ----------
    chunk : dict
        Chunk dict with keys 'level_name', 'col_start', and 'rows'.
    difficulty_label : str
        One of 'Easy', 'Medium', or 'Hard'.

    Returns
    -------
    list[int]
        Integer token sequence of length SEQ_LEN (1 control + 14 x 32 tiles).
    """
    control = CONTROL_TOKENS[difficulty_label]
    tile_tokens = [CHAR_TO_ID[c] for row in chunk["rows"] for c in row]
    return [control] + tile_tokens


def decode_sequence(token_ids: list[int]) -> dict:
    """Decode a token sequence back to a difficulty label and level grid.

    Parameters
    ----------
    token_ids : list[int]
        Integer token sequence as produced by tokenize_chunk.

    Returns
    -------
    dict
        Keys: 'difficulty' (str) and 'rows' (list of str).
    """
    difficulty = CONTROL_TOKEN_NAMES[token_ids[0]]
    flat_tiles  = [ID_TO_CHAR[t] for t in token_ids[1:]]
    rows        = ["".join(flat_tiles[i * 32:(i + 1) * 32]) for i in range(14)]
    return {"difficulty": difficulty, "rows": rows}


class LevelChunkDataset(Dataset):
    """PyTorch Dataset for level chunk token sequences.

    Each item returns an (input, target) pair for next-token prediction.
    Input is tokens 0..N-2 and target is tokens 1..N-1.

    Parameters
    ----------
    sequences : list[list[int]]
        List of integer token sequences, all of equal length.
    """

    def __init__(self, sequences: list[list[int]]):
        self.data = [torch.tensor(s, dtype=torch.long) for s in sequences]

    def __len__(self) -> int:
        return len(self.data)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        seq = self.data[idx]
        return seq[:-1], seq[1:]

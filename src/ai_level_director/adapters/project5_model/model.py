"""Transformer model architecture for tile sequence generation."""
import torch
import torch.nn as nn


class LevelTransformer(nn.Module):
    """Decoder-only Transformer for autoregressive tile sequence generation.

    Uses learned token and positional embeddings, a stack of causal
    self-attention layers, and a linear output projection over the vocabulary.

    Parameters
    ----------
    vocab_size : int
        Number of distinct tokens (tiles + control tokens).
    d_model : int
        Embedding and hidden state dimension.
    n_heads : int
        Number of attention heads per layer.
    n_layers : int
        Number of Transformer encoder layers with causal masking.
    seq_len : int
        Maximum input sequence length (used to size positional embeddings).
    dropout : float
        Dropout rate applied within each Transformer layer.
    """

    def __init__(
        self,
        vocab_size: int,
        d_model: int,
        n_heads: int,
        n_layers: int,
        seq_len: int,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.token_emb = nn.Embedding(vocab_size, d_model)
        self.pos_emb   = nn.Embedding(seq_len, d_model)
        encoder_layer  = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=n_heads,
            dim_feedforward=d_model * 4,
            dropout=dropout,
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=n_layers)
        self.output_proj = nn.Linear(d_model, vocab_size)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass with causal self-attention mask.

        Parameters
        ----------
        x : torch.Tensor
            Integer token indices of shape (batch, seq_len).

        Returns
        -------
        torch.Tensor
            Logits of shape (batch, seq_len, vocab_size).
        """
        positions = torch.arange(x.size(1), device=x.device).unsqueeze(0)
        h = self.token_emb(x) + self.pos_emb(positions)
        mask = nn.Transformer.generate_square_subsequent_mask(x.size(1), device=x.device)
        h = self.transformer(h, mask=mask, is_causal=True)
        return self.output_proj(h)


def count_parameters(model: nn.Module) -> int:
    """Return the total number of trainable parameters in a model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)

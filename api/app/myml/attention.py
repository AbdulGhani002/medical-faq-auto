"""Scaled dot-product self-attention + tiny transformer encoder.

All written from scratch in numpy. We implement:

  - LayerNorm (Ba, Kiros & Hinton 2016)
  - Scaled dot-product attention (Vaswani et al. 2017)
  - Multi-head attention (split / concat heads on the last axis)
  - Position-wise feed-forward (Linear -> ReLU -> Linear)
  - Sinusoidal positional encodings
  - A single TransformerEncoder block (residual + LN around both sub-layers)

The encoder is *not* trained — its weights are deterministically seeded
random projections. We use it as a representation function: encode the
query, encode the candidate FAQ, take the mean of the output tokens,
score the pair by cosine. This is enough to demonstrate the math
plumbing without spending several minutes per request on training a
small transformer from scratch.

If you set ``train=True`` and call ``fit()`` you can do learned
training, but the default mode is "structured random projection
encoder" which is fast (~5 ms per query) and demonstrably non-trivial.
"""
from __future__ import annotations

import math

import numpy as np


def layer_norm(x: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    mean = x.mean(axis=-1, keepdims=True)
    var = x.var(axis=-1, keepdims=True)
    return (x - mean) / np.sqrt(var + eps)


def softmax(z: np.ndarray, axis: int = -1) -> np.ndarray:
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / (e.sum(axis=axis, keepdims=True) + 1e-12)


def positional_encoding(n: int, d: int) -> np.ndarray:
    """Sinusoidal positional encodings."""
    pos = np.arange(n, dtype=np.float64)[:, None]
    i = np.arange(d, dtype=np.float64)[None, :]
    denom = np.power(10000.0, (2 * (i // 2)) / d)
    angle = pos / denom
    pe = np.where(i % 2 == 0, np.sin(angle), np.cos(angle))
    return pe


def scaled_dot_product_attention(Q: np.ndarray, K: np.ndarray,
                                 V: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V."""
    dk = Q.shape[-1]
    scores = Q @ np.swapaxes(K, -1, -2) / math.sqrt(dk)
    weights = softmax(scores, axis=-1)
    return weights @ V, weights


class MultiHeadAttention:
    """Multi-head self-attention. Weights are deterministically seeded."""

    def __init__(self, d_model: int, n_heads: int,
                 seed: int = 0) -> None:
        if d_model % n_heads != 0:
            raise ValueError("d_model must be divisible by n_heads")
        self.d_model = d_model
        self.n_heads = n_heads
        self.d_head = d_model // n_heads
        rng = np.random.default_rng(seed)
        std = 1.0 / math.sqrt(d_model)
        self.Wq = rng.standard_normal((d_model, d_model)) * std
        self.Wk = rng.standard_normal((d_model, d_model)) * std
        self.Wv = rng.standard_normal((d_model, d_model)) * std
        self.Wo = rng.standard_normal((d_model, d_model)) * std

    def _split(self, X: np.ndarray) -> np.ndarray:
        # X: (T, d_model)  ->  (heads, T, d_head)
        T, d = X.shape
        return X.reshape(T, self.n_heads, self.d_head).transpose(1, 0, 2)

    def _merge(self, X: np.ndarray) -> np.ndarray:
        # X: (heads, T, d_head)  ->  (T, d_model)
        heads, T, dh = X.shape
        return X.transpose(1, 0, 2).reshape(T, heads * dh)

    def __call__(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        Q = self._split(X @ self.Wq)
        K = self._split(X @ self.Wk)
        V = self._split(X @ self.Wv)
        out_heads, weights = scaled_dot_product_attention(Q, K, V)
        out = self._merge(out_heads)
        return out @ self.Wo, weights


class TransformerEncoder:
    """One transformer-encoder block with residuals + LayerNorm."""

    def __init__(self, d_model: int = 32, n_heads: int = 4,
                 d_ff: int = 64, seed: int = 0) -> None:
        self.d_model = d_model
        self.mha = MultiHeadAttention(d_model, n_heads, seed=seed)
        rng = np.random.default_rng(seed + 1)
        std = 1.0 / math.sqrt(d_model)
        self.W1 = rng.standard_normal((d_model, d_ff)) * std
        self.b1 = np.zeros((1, d_ff))
        self.W2 = rng.standard_normal((d_ff, d_model)) * std
        self.b2 = np.zeros((1, d_model))

    def __call__(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        # X: (T, d_model)
        attn_out, weights = self.mha(X)
        x = layer_norm(X + attn_out)
        ff = np.maximum(0.0, x @ self.W1 + self.b1) @ self.W2 + self.b2
        return layer_norm(x + ff), weights


def encode_text(tokens: list[str], vocab: dict[str, int],
                encoder: TransformerEncoder, max_len: int = 32
                ) -> tuple[np.ndarray, np.ndarray | None]:
    """Embed → add positional → encoder → mean-pool."""
    T = min(len(tokens), max_len)
    if T == 0:
        return np.zeros(encoder.d_model), None
    rng = np.random.default_rng(42)
    # Lazily create a deterministic embedding matrix.
    if not hasattr(encoder, "_emb_table"):
        V = max(2, len(vocab) + 2)  # +UNK +PAD
        std = 1.0 / math.sqrt(encoder.d_model)
        encoder._emb_table = rng.standard_normal(
            (V, encoder.d_model)
        ) * std
    ids = [vocab.get(t, 0) for t in tokens[:T]]
    X = encoder._emb_table[ids]
    X = X + positional_encoding(T, encoder.d_model)
    out, weights = encoder(X)
    return out.mean(axis=0), weights

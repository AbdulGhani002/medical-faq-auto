"""Word2Vec skip-gram with negative sampling — pure numpy.

Original paper: Mikolov, Sutskever, Chen, Corrado, Dean (NeurIPS 2013).
This is the SGNS objective: for each (centre, context) positive pair we
draw ``k`` negative words from a unigram^0.75 noise distribution and
push them apart with sigmoid-cross-entropy.

Training loss for one (centre c, context o, negatives N):

    -log σ(v_o · u_c) - sum_{n in N} log σ(-v_n · u_c)

  u : centre vectors      (input embeddings,  W_in)
  v : context vectors     (output embeddings, W_out)

Gradients fall straight out of (σ(·) - target). We use vanilla SGD.

Frequent word subsampling (Mikolov §2.3): each token w is kept with
probability  P(w) = (sqrt(f(w) / t) + 1) * (t / f(w)),  t = 1e-4.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

import numpy as np


_TOK_RE = re.compile(r"[a-z0-9]+")

# Stopwords trimmed from training pairs only. On a 139-doc corpus, keeping
# them lets every word's nearest-neighbours collapse to {the, a, of, ...}.
_STOP = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "have", "has", "had",
    "i", "you", "he", "she", "we", "they", "it", "me", "him", "her", "us", "them",
    "my", "your", "his", "their", "our", "its",
    "and", "or", "but", "if", "so", "as", "than", "then", "of",
    "to", "in", "on", "at", "for", "with", "by", "from", "this", "that",
    "these", "those", "into", "no", "not", "yes", "can", "will", "would",
    "should", "could", "may", "might", "must", "shall", "also", "any",
    "some", "all", "more", "less", "very", "too", "such", "about", "over",
    "under", "while", "until", "before", "after", "during", "again",
}


def _sigmoid(x: np.ndarray) -> np.ndarray:
    # Clip to keep us inside double precision; σ becomes 0 or 1 quickly.
    x = np.clip(x, -30.0, 30.0)
    return 1.0 / (1.0 + np.exp(-x))


class Word2Vec:
    def __init__(self, dim: int = 64, window: int = 4,
                 min_count: int = 2, k_negatives: int = 5,
                 sample: float = 1e-4, lr: float = 0.025,
                 epochs: int = 5, random_state: int = 0) -> None:
        self.dim = int(dim)
        self.window = int(window)
        self.min_count = int(min_count)
        self.k_negatives = int(k_negatives)
        self.sample = float(sample)
        self.lr = float(lr)
        self.epochs = int(epochs)
        self.random_state = int(random_state)
        # Filled by fit().
        self.vocab_: list[str] = []
        self.word_to_idx: dict[str, int] = {}
        self.W_in: np.ndarray = np.empty((0, 0))
        self.W_out: np.ndarray = np.empty((0, 0))
        self._neg_table: np.ndarray = np.empty(0, dtype=np.int64)
        self._kept_prob: np.ndarray = np.empty(0)
        self.loss_curve_: list[float] = []
        self.trained = False

    # ---------------- preprocessing ----------------

    @staticmethod
    def _tokenise(text: str) -> list[str]:
        return [t for t in _TOK_RE.findall((text or "").lower())
                if t not in _STOP and len(t) > 1]

    def _build_vocab(self, sentences: Iterable[list[str]]) -> tuple[list[list[int]], np.ndarray]:
        counts: Counter = Counter()
        sents = []
        for s in sentences:
            sents.append(s)
            counts.update(s)
        self.vocab_ = [w for w, c in counts.items() if c >= self.min_count]
        self.word_to_idx = {w: i for i, w in enumerate(self.vocab_)}
        N = sum(counts[w] for w in self.vocab_)
        freqs = np.asarray([counts[w] / N for w in self.vocab_], dtype=np.float64)

        # Subsampling probability per word.
        t = self.sample
        with np.errstate(invalid="ignore", divide="ignore"):
            ratio = freqs / t
            kept = (np.sqrt(ratio) + 1.0) * (t / freqs)
            kept = np.clip(kept, 0.0, 1.0)
        self._kept_prob = kept

        # Encoded sentences with OOV stripped + subsampling applied later.
        rng = np.random.default_rng(self.random_state)
        encoded: list[list[int]] = []
        for s in sents:
            ids = []
            for w in s:
                idx = self.word_to_idx.get(w)
                if idx is None:
                    continue
                if rng.random() < self._kept_prob[idx]:
                    ids.append(idx)
            if ids:
                encoded.append(ids)
        return encoded, freqs

    def _build_neg_table(self, freqs: np.ndarray, table_size: int = 1_000_000) -> None:
        # P_n(w) ∝ f(w) ^ 0.75
        powered = np.power(freqs, 0.75)
        powered /= powered.sum()
        cum = np.cumsum(powered)
        idx = np.searchsorted(cum, np.linspace(0, 1, table_size, endpoint=False))
        self._neg_table = idx.astype(np.int64)

    # ---------------- training ----------------

    def fit(self, sentences: Iterable[str]) -> dict:
        rng = np.random.default_rng(self.random_state)
        token_sents = [self._tokenise(s) for s in sentences if s]
        encoded, freqs = self._build_vocab(token_sents)
        V = len(self.vocab_)
        if V == 0:
            return {"trained": False, "vocab": 0}

        # Initialise embeddings: centre vectors uniform in [-0.5/d, 0.5/d],
        # context vectors zero (Mikolov's reference recipe).
        scale = 0.5 / self.dim
        self.W_in = (rng.random((V, self.dim)) - 0.5) * 2 * scale
        self.W_out = np.zeros((V, self.dim), dtype=np.float64)

        self._build_neg_table(freqs)
        loss_curve: list[float] = []

        for epoch in range(self.epochs):
            total_loss = 0.0
            n_pairs = 0
            rng.shuffle(encoded)
            cur_lr = self.lr * (1.0 - epoch / max(1, self.epochs)) + 1e-4
            for ids in encoded:
                L = len(ids)
                for i, c in enumerate(ids):
                    win = int(rng.integers(1, self.window + 1))
                    lo = max(0, i - win)
                    hi = min(L, i + win + 1)
                    u = self.W_in[c]  # centre vector
                    for j in range(lo, hi):
                        if j == i:
                            continue
                        o = ids[j]
                        # Negative samples.
                        negs = self._neg_table[
                            rng.integers(0, len(self._neg_table),
                                         size=self.k_negatives)
                        ]
                        # Avoid sampling the positive as a negative.
                        negs = np.where(negs == o,
                                        (negs + 1) % V, negs)
                        # Stack target vectors: positive (label 1) + negatives (label 0).
                        targets_idx = np.concatenate(([o], negs))
                        labels = np.zeros(self.k_negatives + 1)
                        labels[0] = 1.0
                        V_t = self.W_out[targets_idx]  # (k+1, d)
                        scores = V_t @ u  # (k+1,)
                        sig = _sigmoid(scores)
                        # Cross-entropy.
                        eps = 1e-9
                        loss = -(labels * np.log(sig + eps)
                                 + (1 - labels) * np.log(1 - sig + eps)).sum()
                        total_loss += float(loss)
                        n_pairs += 1
                        # Gradients.
                        grad_scores = sig - labels  # (k+1,)
                        # dL/du = sum_t grad_t * V_t
                        grad_u = grad_scores @ V_t
                        # dL/dV_t = grad_t * u
                        grad_V = grad_scores[:, None] * u
                        # Updates.
                        self.W_out[targets_idx] -= cur_lr * grad_V
                        self.W_in[c] -= cur_lr * grad_u
                        u = self.W_in[c]  # refresh after update
            avg = total_loss / max(1, n_pairs)
            loss_curve.append(round(avg, 4))

        self.loss_curve_ = loss_curve
        self.trained = True
        # L2-normalise centre vectors so cosine becomes a dot product.
        norms = np.linalg.norm(self.W_in, axis=1, keepdims=True) + 1e-9
        self.W_in_normed = self.W_in / norms
        return {
            "trained": True, "vocab": V,
            "dim": self.dim, "epochs": self.epochs,
            "loss_curve": loss_curve, "final_loss": loss_curve[-1] if loss_curve else None,
        }

    # ---------------- inference ----------------

    def vector(self, word: str) -> np.ndarray:
        idx = self.word_to_idx.get(word.lower())
        if idx is None:
            return np.zeros(self.dim)
        return self.W_in_normed[idx]

    def doc_vector(self, text: str) -> np.ndarray:
        toks = self._tokenise(text)
        vecs = [self.vector(t) for t in toks if t in self.word_to_idx]
        if not vecs:
            return np.zeros(self.dim)
        v = np.mean(vecs, axis=0)
        n = np.linalg.norm(v) + 1e-9
        return v / n

    def most_similar(self, word: str, k: int = 5) -> list[tuple[str, float]]:
        idx = self.word_to_idx.get(word.lower())
        if idx is None or not self.trained:
            return []
        scores = self.W_in_normed @ self.W_in_normed[idx]
        order = np.argsort(-scores)
        out: list[tuple[str, float]] = []
        for i in order:
            w = self.vocab_[i]
            if w == word.lower():
                continue
            out.append((w, float(scores[i])))
            if len(out) >= k:
                break
        return out

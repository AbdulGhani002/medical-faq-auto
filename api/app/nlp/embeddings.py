"""Corpus word embeddings via PPMI + truncated SVD.

The classic Hyperspace Analog to Language / Levy-Goldberg result:
positive pointwise mutual information factored by SVD is equivalent to
word2vec's skip-gram-with-negative-sampling. We build the embeddings at
index time from the FAQ corpus (~90 documents) and expose a query →
document semantic-similarity channel for the retriever.

No transformer, no neural net, no external model download. Just numpy
+ scikit-learn TruncatedSVD.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import math

import numpy as np

from app.myml.svd import TruncatedSVD

from .lemmatize import canonical
from .normalize import _STOPWORDS, tokenize


class CorpusEmbeddings:
    """PPMI-factored co-occurrence word embeddings.

    Parameters
    ----------
    docs        list of strings (already cleaned)
    dim         number of latent dimensions (default 50)
    window      symmetric context window (default 4)
    min_count   ignore tokens with fewer than N occurrences (default 2)
    """

    def __init__(self, docs: list[str], dim: int = 50,
                 window: int = 4, min_count: int = 2) -> None:
        self.dim = dim
        self.window = window
        self.min_count = min_count

        token_streams = [self._stream(d) for d in docs]
        counts: Counter = Counter()
        for s in token_streams:
            counts.update(s)
        self.vocab: list[str] = [
            w for w, c in counts.items() if c >= min_count and len(w) > 2
        ]
        self.word_to_idx = {w: i for i, w in enumerate(self.vocab)}

        if len(self.vocab) < 5:
            # Tiny corpus -- skip the SVD step and use 1-hot fallback.
            self.vectors = np.eye(len(self.vocab) or 1)
            self.dim = self.vectors.shape[1]
            self._ready = False
            return

        cooc = self._cooccurrence(token_streams)
        ppmi = self._ppmi(cooc)
        n = min(dim, max(2, min(ppmi.shape) - 1))
        try:
            svd = TruncatedSVD(n_components=n, random_state=0)
            self.vectors = svd.fit_transform(ppmi)
            self.dim = self.vectors.shape[1]
            # L2-normalise so cosine becomes a dot product.
            norms = np.linalg.norm(self.vectors, axis=1, keepdims=True) + 1e-9
            self.vectors = self.vectors / norms
            self._ready = True
        except Exception:
            self.vectors = np.eye(len(self.vocab))
            self.dim = self.vectors.shape[1]
            self._ready = False

    # ---------------- internals ----------------

    @staticmethod
    def _stream(text: str) -> list[str]:
        return [
            canonical(t)
            for t in tokenize(text or "", drop_stopwords=True)
            if t not in _STOPWORDS and len(t) >= 2
        ]

    def _cooccurrence(self, streams: list[list[str]]) -> np.ndarray:
        V = len(self.vocab)
        mat = np.zeros((V, V), dtype=np.float32)
        idx = self.word_to_idx
        w = self.window
        for s in streams:
            ids = [idx[t] for t in s if t in idx]
            for i, a in enumerate(ids):
                lo = max(0, i - w)
                hi = min(len(ids), i + w + 1)
                for j in range(lo, hi):
                    if j == i:
                        continue
                    mat[a, ids[j]] += 1.0
        return mat

    @staticmethod
    def _ppmi(cooc: np.ndarray) -> np.ndarray:
        total = cooc.sum() + 1e-9
        row = cooc.sum(axis=1, keepdims=True) + 1e-9
        col = cooc.sum(axis=0, keepdims=True) + 1e-9
        expected = (row @ col) / total
        with np.errstate(divide="ignore", invalid="ignore"):
            ppmi = np.log((cooc * total) / (expected + 1e-9) + 1e-9)
        ppmi[~np.isfinite(ppmi)] = 0.0
        return np.maximum(ppmi, 0.0)

    # ---------------- public API ----------------

    def vector(self, token: str) -> np.ndarray:
        idx = self.word_to_idx.get(canonical(token))
        if idx is None:
            return np.zeros(self.dim, dtype=np.float32)
        return self.vectors[idx]

    def doc_vector(self, text: str) -> np.ndarray:
        toks = self._stream(text)
        vecs = [self.vector(t) for t in toks if t in self.word_to_idx]
        if not vecs:
            return np.zeros(self.dim, dtype=np.float32)
        v = np.mean(vecs, axis=0)
        n = np.linalg.norm(v) + 1e-9
        return v / n

    def doc_matrix(self, docs: list[str]) -> np.ndarray:
        rows = [self.doc_vector(d) for d in docs]
        if not rows:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.vstack(rows)

    def similarity(self, query: str, docs_matrix: np.ndarray) -> np.ndarray:
        qv = self.doc_vector(query)
        if not np.any(qv) or docs_matrix.size == 0:
            return np.zeros(docs_matrix.shape[0], dtype=np.float32)
        return docs_matrix @ qv

    def nearest_neighbours(self, token: str, k: int = 5) -> list[tuple[str, float]]:
        idx = self.word_to_idx.get(canonical(token))
        if idx is None:
            return []
        scores = self.vectors @ self.vectors[idx]
        order = np.argsort(-scores)
        out: list[tuple[str, float]] = []
        for i in order:
            w = self.vocab[i]
            if w == canonical(token):
                continue
            out.append((w, float(scores[i])))
            if len(out) >= k:
                break
        return out

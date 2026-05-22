"""BM25 Okapi from scratch.

The classical Robertson & Sparck-Jones formulation:

    score(D, q) = sum_{t in q} IDF(t) *
                  ( tf(t, D) * (k1 + 1) ) /
                  ( tf(t, D) + k1 * (1 - b + b * |D| / avgdl) )

with the smoothed IDF used by Lucene / rank_bm25:

    IDF(t) = ln( (N - df + 0.5) / (df + 0.5) + 1 )

API-compatible with ``rank_bm25.BM25Okapi`` for our purposes:

    bm = BM25(token_docs)
    scores = bm.get_scores(query_tokens)
"""
from __future__ import annotations

import math
from collections import Counter

import numpy as np


class BM25:
    def __init__(self, corpus: list[list[str]],
                 k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.corpus_size = len(corpus)
        self.doc_lens = np.asarray([len(d) for d in corpus], dtype=np.float64)
        self.avgdl = float(self.doc_lens.mean()) if self.corpus_size else 0.0

        # Per-doc term frequencies.
        self._doc_freqs: list[Counter] = [Counter(d) for d in corpus]

        # Document frequency of each term.
        df: Counter = Counter()
        for c in self._doc_freqs:
            for tok in c.keys():
                df[tok] += 1

        # Smoothed IDF.
        N = self.corpus_size
        self._idf: dict[str, float] = {
            tok: math.log(((N - dfi + 0.5) / (dfi + 0.5)) + 1.0)
            for tok, dfi in df.items()
        }

    def get_scores(self, query: list[str]) -> np.ndarray:
        if self.corpus_size == 0 or not query:
            return np.zeros(self.corpus_size, dtype=np.float64)
        scores = np.zeros(self.corpus_size, dtype=np.float64)
        for tok in query:
            idf = self._idf.get(tok)
            if idf is None:
                continue
            for i, freqs in enumerate(self._doc_freqs):
                tf = freqs.get(tok, 0)
                if tf == 0:
                    continue
                denom = tf + self.k1 * (
                    1 - self.b + self.b * (self.doc_lens[i] / self.avgdl)
                )
                scores[i] += idf * (tf * (self.k1 + 1.0)) / denom
        return scores


# Compatibility alias matching the rank_bm25 export name we currently use.
BM25Okapi = BM25

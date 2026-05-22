"""TF-IDF vectoriser, from scratch.

Drop-in replacement for ``sklearn.feature_extraction.text.TfidfVectorizer``
for the subset we use: ``analyzer in {"word", "char_wb"}``, ``ngram_range``,
``min_df``, ``sublinear_tf``.

We implement the IDF used by scikit-learn:

    idf(t) = ln((1 + N) / (1 + df(t))) + 1

Each row is L2-normalised after weighting so cosine similarity becomes
the dot product. Returns dense numpy matrices — our corpora are small
(under 1000 docs) so we do not bother with sparse storage.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from typing import Iterable

import numpy as np

from .linalg import l2_normalize


_WORD_RE = re.compile(r"[a-z0-9]+")


def _word_ngrams(text: str, lo: int, hi: int) -> list[str]:
    toks = _WORD_RE.findall((text or "").lower())
    out: list[str] = []
    for n in range(lo, hi + 1):
        if n == 1:
            out.extend(toks)
        else:
            out.extend(" ".join(toks[i:i + n]) for i in range(len(toks) - n + 1))
    return out


def _char_wb_ngrams(text: str, lo: int, hi: int) -> list[str]:
    """Char n-grams with word-boundary padding, matching sklearn's char_wb."""
    out: list[str] = []
    for tok in _WORD_RE.findall((text or "").lower()):
        s = " " + tok + " "
        for n in range(lo, hi + 1):
            if len(s) < n:
                continue
            out.extend(s[i:i + n] for i in range(len(s) - n + 1))
    return out


class TfidfVectorizer:
    def __init__(self, analyzer: str = "word",
                 ngram_range: tuple[int, int] = (1, 1),
                 min_df: int = 1,
                 sublinear_tf: bool = False) -> None:
        if analyzer not in ("word", "char_wb"):
            raise ValueError(f"analyzer must be word or char_wb, got {analyzer}")
        self.analyzer = analyzer
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.sublinear_tf = sublinear_tf
        self.vocabulary_: dict[str, int] = {}
        self.idf_: np.ndarray = np.zeros(0, dtype=np.float64)

    # ---------- internal ----------

    def _ngram(self, text: str) -> list[str]:
        lo, hi = self.ngram_range
        if self.analyzer == "word":
            return _word_ngrams(text, lo, hi)
        return _char_wb_ngrams(text, lo, hi)

    # ---------- public API ----------

    def fit(self, raw_docs: Iterable[str]) -> "TfidfVectorizer":
        docs = list(raw_docs)
        df: Counter = Counter()
        token_lists: list[list[str]] = []
        for d in docs:
            grams = self._ngram(d)
            token_lists.append(grams)
            for tok in set(grams):
                df[tok] += 1
        vocab: dict[str, int] = {}
        for tok, c in df.items():
            if c >= self.min_df:
                vocab[tok] = len(vocab)
        self.vocabulary_ = vocab
        N = len(docs)
        idf = np.zeros(len(vocab), dtype=np.float64)
        for tok, idx in vocab.items():
            idf[idx] = math.log((1 + N) / (1 + df[tok])) + 1.0
        self.idf_ = idf
        return self

    def transform(self, raw_docs: Iterable[str]) -> np.ndarray:
        docs = list(raw_docs)
        V = len(self.vocabulary_)
        out = np.zeros((len(docs), V), dtype=np.float64)
        for i, d in enumerate(docs):
            counts: Counter = Counter(self._ngram(d))
            for tok, c in counts.items():
                idx = self.vocabulary_.get(tok)
                if idx is None:
                    continue
                tf = (1.0 + math.log(c)) if (self.sublinear_tf and c > 0) else c
                out[i, idx] = tf * self.idf_[idx]
        return l2_normalize(out)

    def fit_transform(self, raw_docs: Iterable[str]) -> np.ndarray:
        self.fit(raw_docs)
        return self.transform(raw_docs)

    def get_feature_names_out(self) -> np.ndarray:
        inv = sorted(self.vocabulary_.items(), key=lambda kv: kv[1])
        return np.asarray([k for k, _ in inv])

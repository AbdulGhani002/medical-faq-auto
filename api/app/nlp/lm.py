"""Tri-/bi-/uni-gram language model with interpolated Kneser-Ney smoothing.

Trained at import time on the FAQ corpus + intent training corpus.
Used for:

  - perplexity scoring of incoming queries
  - LM-augmented spell correction (beam over edit candidates)
  - query autocompletion (n-gram continuations)

Pure Python + numpy. No neural net, no transformer. ~220 LoC.

The classical interpolated Kneser-Ney recursion (Chen & Goodman 1998):

  P_kn(w_i | w_{i-n+1..i-1}) =
        max(c(w_{i-n+1..i}) - D, 0) / c(w_{i-n+1..i-1})
      + lambda(w_{i-n+1..i-1}) * P_kn(w_i | w_{i-n+2..i-1})

with continuation probability at the unigram base.
"""
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

_TOK_RE = re.compile(r"[a-z0-9]+")
_BOS = "<s>"
_EOS = "</s>"
_UNK = "<unk>"

# Standard absolute-discount values.
_D1, _D2, _D3 = 0.1, 0.5, 0.8


def _tokenise(text: str) -> list[str]:
    return _TOK_RE.findall((text or "").lower())


class KneserNeyLM:
    def __init__(self, order: int = 3) -> None:
        self.order = order
        # Counts.
        self.unigram_count: Counter = Counter()
        self.bigram_count: dict[str, Counter] = defaultdict(Counter)
        self.trigram_count: dict[tuple[str, str], Counter] = defaultdict(Counter)
        # Continuation counts: how many unique left contexts a word appears in.
        self.cont_uni: Counter = Counter()
        self.cont_bi: dict[str, Counter] = defaultdict(Counter)
        self.vocab: set[str] = set()
        # Totals for normalisation.
        self.total_unigrams = 0
        self.unique_bigram_types = 0
        self.trained = False
        self.train_size = 0

    # ---------------- training ----------------

    def fit(self, sentences: Iterable[str]) -> dict:
        sent_count = 0
        for s in sentences:
            toks = [_BOS, _BOS] + _tokenise(s) + [_EOS]
            if len(toks) <= 3:
                continue
            sent_count += 1
            for i, w in enumerate(toks):
                self.unigram_count[w] += 1
                self.vocab.add(w)
                if i >= 1:
                    self.bigram_count[toks[i - 1]][w] += 1
                if i >= 2:
                    self.trigram_count[(toks[i - 2], toks[i - 1])][w] += 1
        # Continuation counts.
        bigram_types: set[tuple[str, str]] = set()
        for prev, nexts in self.bigram_count.items():
            for w in nexts:
                bigram_types.add((prev, w))
                self.cont_uni[w] += 1
        for (a, b), nexts in self.trigram_count.items():
            for w in nexts:
                self.cont_bi[b][w] += 1

        self.total_unigrams = sum(self.unigram_count.values())
        self.unique_bigram_types = len(bigram_types)
        self.trained = True
        self.train_size = sent_count
        return {
            "trained": True,
            "sentences": sent_count,
            "vocab": len(self.vocab),
            "unigrams": self.total_unigrams,
            "bigram_types": self.unique_bigram_types,
        }

    # ---------------- probability ----------------

    def _p_unigram_kn(self, w: str) -> float:
        """Continuation probability — P_KN at the unigram base."""
        if self.unique_bigram_types == 0:
            return 1.0 / max(1, len(self.vocab))
        return max(1, self.cont_uni.get(w, 0)) / self.unique_bigram_types

    def _p_bigram_kn(self, prev: str, w: str) -> float:
        b_total = sum(self.bigram_count.get(prev, {}).values())
        if b_total == 0:
            return self._p_unigram_kn(w)
        cont_w = self.bigram_count[prev].get(w, 0)
        # Treat the lower bigrams as continuations for KN.
        cont_w_seen = self.cont_bi.get(prev, Counter()).get(w, 0)
        # Discounted continuation count.
        first = max(cont_w_seen - _D2, 0.0) / b_total
        n_types = len(self.bigram_count[prev])
        lam = (_D2 * n_types) / b_total
        # Fall back to unigram continuation.
        return first + lam * self._p_unigram_kn(w)

    def p(self, w: str, history: tuple[str, ...] = ()) -> float:
        if not history:
            return self._p_unigram_kn(w)
        if len(history) == 1:
            return self._p_bigram_kn(history[0], w)
        prev = history[-2:]
        ctx = tuple(prev)
        nexts = self.trigram_count.get(ctx)
        if not nexts:
            return self._p_bigram_kn(prev[-1], w)
        total = sum(nexts.values())
        first = max(nexts.get(w, 0) - _D3, 0.0) / total
        n_types = len(nexts)
        lam = (_D3 * n_types) / total
        return first + lam * self._p_bigram_kn(prev[-1], w)

    # ---------------- public helpers ----------------

    def log_prob(self, text: str) -> float:
        toks = [_BOS, _BOS] + _tokenise(text) + [_EOS]
        if len(toks) <= 3:
            return 0.0
        lp = 0.0
        for i in range(2, len(toks)):
            history = (toks[i - 2], toks[i - 1])
            prob = max(1e-9, self.p(toks[i], history))
            lp += math.log(prob)
        return lp

    def perplexity(self, text: str) -> float:
        toks = _tokenise(text)
        if not toks:
            return float("inf")
        lp = self.log_prob(text)
        return math.exp(-lp / len(toks))

    def continuations(self, prefix: str, k: int = 5) -> list[tuple[str, float]]:
        """Top-k next tokens given a prefix (autocomplete)."""
        toks = _tokenise(prefix)
        if not toks:
            ctx = (_BOS, _BOS)
        elif len(toks) == 1:
            ctx = (_BOS, toks[-1])
        else:
            ctx = (toks[-2], toks[-1])
        scores: dict[str, float] = {}
        # Score every word seen as a continuation of either trigram or bigram.
        candidates = set(self.trigram_count.get(ctx, {}).keys())
        candidates.update(self.bigram_count.get(ctx[-1], {}).keys())
        if not candidates:
            candidates = set(self.unigram_count.keys()) - {_BOS, _EOS, _UNK}
        for w in candidates:
            if w in (_BOS, _EOS, _UNK):
                continue
            scores[w] = self.p(w, ctx)
        out = sorted(scores.items(), key=lambda kv: -kv[1])[:k]
        return [(w, round(p, 6)) for w, p in out]


# ---------------- module-level singleton ----------------


_MODEL: KneserNeyLM | None = None


def _training_corpus() -> list[str]:
    repo_root = Path(__file__).resolve().parents[3]
    sentences: list[str] = []
    # FAQs (each question + each sentence of the answer).
    for name in ("faqs_radiology.json", "faqs_physiotherapy.json",
                 "faqs_cardiovascular.json"):
        p = repo_root / "data" / name
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for rec in data:
            q = rec.get("question", "")
            if q:
                sentences.append(q)
            for s in re.split(r"(?<=[.!?])\s+", rec.get("answer", "")):
                s = s.strip()
                if s:
                    sentences.append(s)
    # Intent examples.
    p = repo_root / "data" / "intents.jsonl"
    if p.is_file():
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("text"):
                    sentences.append(rec["text"])
    return sentences


def get_model() -> KneserNeyLM:
    global _MODEL
    if _MODEL is None:
        m = KneserNeyLM(order=3)
        m.fit(_training_corpus())
        _MODEL = m
    return _MODEL


def perplexity(text: str) -> float:
    return get_model().perplexity(text)


def autocomplete(prefix: str, k: int = 5) -> list[tuple[str, float]]:
    return get_model().continuations(prefix, k=k)

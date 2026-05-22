"""Hidden Markov Model POS tagger with Viterbi decoding.

We train on silver labels produced by the lexicon tagger (``pos.tag``)
over the FAQ corpus. The HMM learns:

  - emission probabilities    P(token | tag)        — with Laplace smoothing
  - transition probabilities  P(tag_t | tag_{t-1})  — with Laplace smoothing
  - initial probabilities     P(tag_0)

At inference time we run Viterbi to find the most likely tag sequence.
For OOV tokens we back off to the lexicon tagger's prediction with a
small emission weight, so the HMM behaves gracefully on unseen words.

Pure Python + numpy. No neural net, no model download. ~180 LoC.
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

from .pos import tag as lexicon_tag, tag_token as lexicon_tag_token

# Tag inventory — must match `pos.py`.
TAGS: list[str] = [
    "NN", "VB", "JJ", "RB", "DT", "IN", "PRP", "WH",
    "CC", "MD", "CD", "UH",
]
TAG2ID = {t: i for i, t in enumerate(TAGS)}
N = len(TAGS)


def _logp(x: float) -> float:
    return math.log(x) if x > 0 else -1e9


class HMMPosTagger:
    def __init__(self) -> None:
        self.start_log = [0.0] * N
        self.trans_log = [[0.0] * N for _ in range(N)]
        self.emit_log: dict[str, list[float]] = {}
        self.unk_log = [0.0] * N  # backoff emission for OOV
        self.vocab: set[str] = set()
        self.trained = False
        self.train_size = 0

    # ---------------- training ----------------

    def fit(self, sentences: list[list[tuple[str, str]]],
            laplace: float = 0.1) -> dict:
        """Train on a list of [(token, tag), ...] sentences."""
        emit_counts: dict[str, list[float]] = defaultdict(
            lambda: [laplace] * N
        )
        trans_counts = [[laplace] * N for _ in range(N)]
        start_counts = [laplace] * N
        tag_totals = [0.0] * N
        for sent in sentences:
            if not sent:
                continue
            first_tag = sent[0][1]
            if first_tag in TAG2ID:
                start_counts[TAG2ID[first_tag]] += 1.0
            for i, (tok, tag) in enumerate(sent):
                if tag not in TAG2ID:
                    continue
                tid = TAG2ID[tag]
                emit_counts[tok.lower()][tid] += 1.0
                tag_totals[tid] += 1.0
                self.vocab.add(tok.lower())
                if i > 0:
                    prev_tag = sent[i - 1][1]
                    if prev_tag in TAG2ID:
                        trans_counts[TAG2ID[prev_tag]][tid] += 1.0

        # Normalise into log-probabilities.
        total_start = sum(start_counts)
        self.start_log = [_logp(c / total_start) for c in start_counts]
        for j in range(N):
            row_sum = sum(trans_counts[j])
            self.trans_log[j] = [_logp(c / row_sum) for c in trans_counts[j]]
        for tok, counts in emit_counts.items():
            row_sum = sum(counts)
            self.emit_log[tok] = [_logp(c / row_sum) for c in counts]
        # Backoff for OOV: uniform over tags, biased by tag totals.
        total_tags = sum(tag_totals) + 1e-9
        self.unk_log = [_logp(c / total_tags) for c in tag_totals]
        self.trained = True
        self.train_size = len(sentences)
        return {
            "trained": True,
            "n_sentences": len(sentences),
            "vocab_size": len(self.vocab),
            "tags": list(TAGS),
        }

    # ---------------- inference ----------------

    def _emit(self, token: str) -> list[float]:
        tl = token.lower()
        if tl in self.emit_log:
            return self.emit_log[tl]
        # Blend OOV backoff with the lexicon tagger's prediction.
        lex = lexicon_tag_token(token)
        if lex in TAG2ID:
            row = list(self.unk_log)
            row[TAG2ID[lex]] += 1.5  # nudge toward the lexicon tag
            return row
        return self.unk_log

    def viterbi(self, tokens: list[str]) -> list[str]:
        n = len(tokens)
        if n == 0:
            return []
        dp = [[-1e9] * N for _ in range(n)]
        back = [[0] * N for _ in range(n)]
        e0 = self._emit(tokens[0])
        for k in range(N):
            dp[0][k] = self.start_log[k] + e0[k]
        for i in range(1, n):
            e = self._emit(tokens[i])
            for k in range(N):
                best_prev = 0
                best_val = -1e18
                for j in range(N):
                    v = dp[i - 1][j] + self.trans_log[j][k]
                    if v > best_val:
                        best_val = v
                        best_prev = j
                dp[i][k] = best_val + e[k]
                back[i][k] = best_prev
        last = max(range(N), key=lambda k: dp[n - 1][k])
        out_ids = [last]
        for i in range(n - 1, 0, -1):
            out_ids.append(back[i][out_ids[-1]])
        out_ids.reverse()
        return [TAGS[k] for k in out_ids]

    def tag(self, tokens: list[str]) -> list[tuple[str, str]]:
        if not self.trained:
            return lexicon_tag(tokens)
        ids = self.viterbi(tokens)
        return list(zip(tokens, ids))

    # ---------------- training-data helpers ----------------

    def to_dict(self) -> dict:
        return {
            "start_log": self.start_log,
            "trans_log": self.trans_log,
            "emit_log": self.emit_log,
            "unk_log": self.unk_log,
            "vocab": list(self.vocab),
            "trained": self.trained,
            "train_size": self.train_size,
        }


def _silver_training_data(limit: int = 400) -> list[list[tuple[str, str]]]:
    """Build a training set by running the lexicon tagger over our FAQ
    corpus. These silver labels are good enough for a first HMM."""
    repo_root = Path(__file__).resolve().parents[3]
    out: list[list[tuple[str, str]]] = []
    for name in ("faqs_radiology.json", "faqs_physiotherapy.json",
                 "faqs_cardiovascular.json"):
        p = repo_root / "data" / name
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for rec in data:
            for sent in _sent_split(rec.get("question", "")
                                    + ". " + rec.get("answer", "")):
                toks = _whitespace(sent)
                if not toks:
                    continue
                tagged = lexicon_tag(toks)
                out.append(tagged)
                if len(out) >= limit:
                    return out
    return out


def _sent_split(text: str) -> list[str]:
    import re
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text or "")
            if s.strip()]


def _whitespace(s: str) -> list[str]:
    import re
    return [m.group(0).lower() for m in re.finditer(r"[a-zA-Z]+", s)]


# ---------------- singleton ----------------


_MODEL: HMMPosTagger | None = None


def get_model() -> HMMPosTagger:
    global _MODEL
    if _MODEL is None:
        m = HMMPosTagger()
        m.fit(_silver_training_data(limit=600))
        _MODEL = m
    return _MODEL


def hmm_tag(tokens: list[str]) -> list[tuple[str, str]]:
    return get_model().tag(tokens)

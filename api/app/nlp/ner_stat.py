"""Statistical NER: averaged structured perceptron + Viterbi decoding.

Trained on BIO-tagged sentences from ``data/ner_examples.jsonl`` plus
silver labels produced by the dictionary NER over the FAQ corpus, so we
get a much bigger training set than the 12 hand-annotated sentences.

The model is a classical structured perceptron with token-level features
(token text, prefixes/suffixes, shape, dictionary hits) plus a transition
score between consecutive tags. Inference uses Viterbi to find the
highest-scoring BIO tag sequence.

No neural network. No transformer. No external model download. About
260 lines of pure Python + numpy.
"""
from __future__ import annotations

import json
import math
import random
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable

from .ner import (
    BODY, CONDITION, DRUG, PERSON, PROCEDURE, SYMPTOM, TIME,
    extract_entities,
)

_TOK_RE = re.compile(r"\S+")
_DICT_LABELS = {
    "BODY": BODY, "SYMPTOM": SYMPTOM, "CONDITION": CONDITION,
    "DRUG": DRUG, "PROCEDURE": PROCEDURE, "TIME": TIME, "PERSON": PERSON,
}

# Possible labels in our BIO scheme.
TAGS: list[str] = ["O"]
for lab in ("BODY", "SYMPTOM", "CONDITION", "DRUG", "PROCEDURE",
            "TIME", "PERSON", "NUMBER"):
    TAGS.extend([f"B-{lab}", f"I-{lab}"])

TAG_TO_ID = {t: i for i, t in enumerate(TAGS)}


# ---------------------------------------------------------------- features


def _shape(t: str) -> str:
    out: list[str] = []
    last = ""
    for ch in t:
        if ch.isupper():
            c = "X"
        elif ch.islower():
            c = "x"
        elif ch.isdigit():
            c = "d"
        else:
            c = ch
        if c != last:
            out.append(c)
        last = c
    return "".join(out)


def _dict_hits(token_lc: str) -> list[str]:
    hits: list[str] = []
    for label, vocab in _DICT_LABELS.items():
        if token_lc in vocab:
            hits.append(f"dict={label}")
    if any(token_lc in v for v in _DICT_LABELS["BODY"] if " " in v):
        hits.append("dict=BODY_PHRASE")
    return hits


def features(tokens: list[str], i: int) -> list[str]:
    t = tokens[i]
    tl = t.lower()
    feats = [
        f"tok={tl}",
        f"shape={_shape(t)}",
        f"pref3={tl[:3]}",
        f"suf3={tl[-3:]}",
        f"suf4={tl[-4:]}" if len(tl) >= 4 else "suf4=__short",
        "first" if i == 0 else "not_first",
        "last" if i == len(tokens) - 1 else "not_last",
    ]
    feats.extend(_dict_hits(tl))
    if i > 0:
        prev = tokens[i - 1].lower()
        feats.append(f"prev={prev}")
    if i + 1 < len(tokens):
        feats.append(f"next={tokens[i + 1].lower()}")
    if any(c.isdigit() for c in t):
        feats.append("has_digit")
    if tl.endswith("ache") or tl.endswith("pain") or tl.endswith("itis"):
        feats.append("suf=medical")
    return feats


# ---------------------------------------------------------------- training


class StructuredPerceptron:
    """Averaged structured perceptron with Viterbi decoding."""

    def __init__(self) -> None:
        # Emission weights: feat -> tag -> float.
        self.w_emit: dict[str, list[float]] = defaultdict(
            lambda: [0.0] * len(TAGS)
        )
        # Transition weights: prev_tag x curr_tag.
        self.w_trans = [[0.0] * len(TAGS) for _ in range(len(TAGS))]
        # For averaging.
        self._totals_emit: dict[str, list[float]] = defaultdict(
            lambda: [0.0] * len(TAGS)
        )
        self._totals_trans = [[0.0] * len(TAGS) for _ in range(len(TAGS))]
        self.t = 0  # update counter
        self._trained = False

    # -------- inference --------

    def emit_score(self, feats: list[str], tag_id: int) -> float:
        s = 0.0
        for f in feats:
            if f in self.w_emit:
                s += self.w_emit[f][tag_id]
        return s

    def _emit_scores(self, feats: list[str]) -> list[float]:
        out = [0.0] * len(TAGS)
        for f in feats:
            row = self.w_emit.get(f)
            if row is None:
                continue
            for k in range(len(TAGS)):
                out[k] += row[k]
        return out

    def viterbi(self, tokens: list[str]) -> list[str]:
        n = len(tokens)
        if n == 0:
            return []
        T = len(TAGS)
        dp = [[-math.inf] * T for _ in range(n)]
        back = [[0] * T for _ in range(n)]

        first_feats = features(tokens, 0)
        first_emit = self._emit_scores(first_feats)
        for k in range(T):
            dp[0][k] = first_emit[k]
        for i in range(1, n):
            emit = self._emit_scores(features(tokens, i))
            for k in range(T):
                best_prev = 0
                best_val = -math.inf
                for j in range(T):
                    v = dp[i - 1][j] + self.w_trans[j][k]
                    if v > best_val:
                        best_val = v
                        best_prev = j
                dp[i][k] = best_val + emit[k]
                back[i][k] = best_prev
        # Backtrack.
        end_tag = max(range(T), key=lambda k: dp[n - 1][k])
        out_ids = [end_tag]
        for i in range(n - 1, 0, -1):
            out_ids.append(back[i][out_ids[-1]])
        out_ids.reverse()
        return [TAGS[k] for k in out_ids]

    # -------- training --------

    def _update_emit(self, feats: list[str], tag_id: int, delta: float) -> None:
        for f in feats:
            self.w_emit[f][tag_id] += delta
            self._totals_emit[f][tag_id] += delta * self.t

    def _update_trans(self, j: int, k: int, delta: float) -> None:
        self.w_trans[j][k] += delta
        self._totals_trans[j][k] += delta * self.t

    def fit(self, examples: list[tuple[list[str], list[str]]],
            epochs: int = 8, shuffle: bool = True) -> dict:
        rng = random.Random(0)
        history = []
        for ep in range(epochs):
            if shuffle:
                rng.shuffle(examples)
            errors = 0
            total = 0
            for tokens, gold in examples:
                pred = self.viterbi(tokens)
                self.t += 1
                if pred == gold:
                    total += len(tokens)
                    continue
                # Update on each disagreement.
                for i, (gt, pt) in enumerate(zip(gold, pred)):
                    feats = features(tokens, i)
                    gt_id = TAG_TO_ID.get(gt, 0)
                    pt_id = TAG_TO_ID.get(pt, 0)
                    if gt_id != pt_id:
                        self._update_emit(feats, gt_id, +1.0)
                        self._update_emit(feats, pt_id, -1.0)
                        errors += 1
                    if i > 0:
                        gp = TAG_TO_ID.get(gold[i - 1], 0)
                        pp = TAG_TO_ID.get(pred[i - 1], 0)
                        if (gp, gt_id) != (pp, pt_id):
                            self._update_trans(gp, gt_id, +1.0)
                            self._update_trans(pp, pt_id, -1.0)
                    total += 1
            history.append({"epoch": ep + 1, "errors": errors,
                            "tokens": total})
        # Apply averaging.
        for f, totals in self._totals_emit.items():
            for k in range(len(TAGS)):
                self.w_emit[f][k] -= totals[k] / max(1, self.t)
        for j in range(len(TAGS)):
            for k in range(len(TAGS)):
                self.w_trans[j][k] -= self._totals_trans[j][k] / max(1, self.t)
        self._trained = True
        return {"epochs": epochs, "history": history, "vocab_size": len(self.w_emit)}

    # -------- prediction --------

    def predict_entities(self, text: str) -> list[dict]:
        tokens, spans = _whitespace_tokenise(text)
        if not tokens:
            return []
        tags = self.viterbi(tokens)
        return _bio_to_entities(text, tokens, tags, spans)


# ---------------------------------------------------------------- helpers


def _whitespace_tokenise(text: str) -> tuple[list[str], list[tuple[int, int]]]:
    tokens: list[str] = []
    spans: list[tuple[int, int]] = []
    for m in _TOK_RE.finditer(text or ""):
        tokens.append(m.group(0))
        spans.append(m.span())
    return tokens, spans


def _bio_to_entities(
    text: str, tokens: list[str], tags: list[str],
    spans: list[tuple[int, int]]
) -> list[dict]:
    out: list[dict] = []
    cur_label: str | None = None
    cur_start: int = 0
    cur_end: int = 0
    for i, tag in enumerate(tags):
        if tag.startswith("B-"):
            if cur_label:
                out.append({"text": text[cur_start:cur_end],
                            "label": cur_label,
                            "start": cur_start, "end": cur_end})
            cur_label = tag[2:]
            cur_start, cur_end = spans[i]
        elif tag.startswith("I-") and cur_label == tag[2:]:
            cur_end = spans[i][1]
        else:
            if cur_label:
                out.append({"text": text[cur_start:cur_end],
                            "label": cur_label,
                            "start": cur_start, "end": cur_end})
            cur_label = None
    if cur_label:
        out.append({"text": text[cur_start:cur_end],
                    "label": cur_label,
                    "start": cur_start, "end": cur_end})
    return out


# ---------------------------------------------------------------- data prep


def _gold_from_dict(text: str) -> tuple[list[str], list[str]]:
    """Use the rule-based NER over FAQs to get silver-labelled examples."""
    tokens, spans = _whitespace_tokenise(text)
    tags = ["O"] * len(tokens)
    ents = extract_entities(text)
    for e in ents:
        first = True
        for i, (ts, te) in enumerate(spans):
            if te <= e["start"] or ts >= e["end"]:
                continue
            tags[i] = ("B-" if first else "I-") + e["label"]
            first = False
    return tokens, tags


def _load_gold_jsonl() -> list[tuple[list[str], list[str]]]:
    p = Path(__file__).resolve().parents[3] / "data" / "ner_examples.jsonl"
    out: list[tuple[list[str], list[str]]] = []
    if not p.is_file():
        return out
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "tokens" in rec and "tags" in rec:
                out.append((list(rec["tokens"]), list(rec["tags"])))
    return out


def _load_silver_from_faqs(limit: int = 200) -> list[tuple[list[str], list[str]]]:
    p = Path(__file__).resolve().parents[3] / "data" / "faqs.jsonl"
    out: list[tuple[list[str], list[str]]] = []
    if not p.is_file():
        return out
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if len(out) >= limit:
                break
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            q = rec.get("question", "")
            if q:
                out.append(_gold_from_dict(q))
    return out


# ---------------------------------------------------------------- module-level singleton


_MODEL: StructuredPerceptron | None = None


def get_model() -> StructuredPerceptron:
    global _MODEL
    if _MODEL is None:
        _MODEL = train_default()
    return _MODEL


def train_default() -> StructuredPerceptron:
    gold = _load_gold_jsonl()
    silver = _load_silver_from_faqs(limit=200)
    examples = gold + silver
    model = StructuredPerceptron()
    if examples:
        model.fit(examples, epochs=6)
    return model


# ---------------------------------------------------------------- evaluation


def entity_set(ents: Iterable[dict]) -> set[tuple[int, int, str]]:
    return {(e["start"], e["end"], e["label"]) for e in ents}


def evaluate(model: StructuredPerceptron,
             examples: list[tuple[list[str], list[str], str]]) -> dict:
    """Examples are (tokens, gold_tags, original_text) tuples."""
    tp = fp = fn = 0
    for tokens, gold, text in examples:
        gold_spans = _whitespace_tokenise(text)[1]
        gold_ents = _bio_to_entities(text, tokens, gold, gold_spans)
        pred_tags = model.viterbi(tokens)
        pred_ents = _bio_to_entities(text, tokens, pred_tags, gold_spans)
        gset = entity_set(gold_ents)
        pset = entity_set(pred_ents)
        tp += len(gset & pset)
        fp += len(pset - gset)
        fn += len(gset - pset)
    prec = tp / (tp + fp) if (tp + fp) else 0.0
    rec = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
    return {"precision": round(prec, 3), "recall": round(rec, 3),
            "f1": round(f1, 3), "tp": tp, "fp": fp, "fn": fn}

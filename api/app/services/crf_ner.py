"""Linear-chain CRF NER trained at import time.

Uses the BIO-tagged data in ``data/ner_examples.jsonl`` plus silver
labels from the dictionary NER over every FAQ question. Pure numpy via
``app.myml.crf``.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.myml.crf import LinearChainCRF
from app.nlp.ner import extract_entities


TAGS = [
    "O",
    "B-BODY", "I-BODY",
    "B-SYMPTOM", "I-SYMPTOM",
    "B-CONDITION", "I-CONDITION",
    "B-DRUG", "I-DRUG",
    "B-PROCEDURE", "I-PROCEDURE",
    "B-TIME", "I-TIME",
    "B-PERSON", "I-PERSON",
    "B-NUMBER", "I-NUMBER",
]


_TOK_RE = re.compile(r"\S+")


def _tokenise(text: str) -> tuple[list[str], list[tuple[int, int]]]:
    tokens, spans = [], []
    for m in _TOK_RE.finditer(text or ""):
        tokens.append(m.group(0))
        spans.append(m.span())
    return tokens, spans


def _gold_from_dict(text: str) -> tuple[list[str], list[str]]:
    tokens, spans = _tokenise(text)
    tags = ["O"] * len(tokens)
    for e in extract_entities(text):
        first = True
        for i, (ts, te) in enumerate(spans):
            if te <= e["start"] or ts >= e["end"]:
                continue
            tags[i] = ("B-" if first else "I-") + e["label"]
            first = False
    return tokens, tags


def _load_training() -> list[tuple[list[str], list[str]]]:
    repo_root = Path(__file__).resolve().parents[3]
    sentences: list[tuple[list[str], list[str]]] = []

    # 1. Hand-annotated examples.
    p = repo_root / "data" / "ner_examples.jsonl"
    if p.is_file():
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                if "tokens" in rec and "tags" in rec:
                    sentences.append((list(rec["tokens"]), list(rec["tags"])))

    # 2. Silver labels over FAQ questions (small + fast).
    pj = repo_root / "data" / "faqs.jsonl"
    if pj.is_file():
        with pj.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                q = rec.get("question", "")
                if q:
                    sentences.append(_gold_from_dict(q))
    return sentences


# ---------------- BIO -> entities ----------------


def _bio_to_entities(text: str, tokens: list[str], tags: list[str],
                     spans: list[tuple[int, int]]) -> list[dict]:
    out: list[dict] = []
    cur_label: str | None = None
    cur_start = 0
    cur_end = 0
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


# ---------------- training ----------------


_MODEL: LinearChainCRF | None = None
_STATS: dict = {}


def get_model() -> LinearChainCRF:
    global _MODEL, _STATS
    if _MODEL is None:
        m = LinearChainCRF(
            tags=TAGS, n_feature_bins=1 << 14,
            lr=0.05, l2=1e-4, epochs=6,
        )
        examples = _load_training()
        if examples:
            _STATS = m.fit(examples)
            _STATS["n_examples"] = len(examples)
        else:
            _STATS = {"trained": False, "n_examples": 0}
        _MODEL = m
    return _MODEL


def predict_entities(text: str) -> list[dict]:
    tokens, spans = _tokenise(text)
    if not tokens:
        return []
    tags = get_model().viterbi(tokens)
    return _bio_to_entities(text, tokens, tags, spans)


def stats() -> dict:
    get_model()
    return {
        "type": "linear-chain CRF (forward-backward + Viterbi)",
        "tags": TAGS,
        "n_features": 1 << 14,
        "n_examples": _STATS.get("n_examples", 0),
        "final_nll": _STATS.get("final_nll"),
    }

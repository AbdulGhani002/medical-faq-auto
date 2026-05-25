"""Machine-written answers — grounded in retrieval.

This module wraps the from-scratch seq2seq model (`app.myml.seq2seq`)
so the chat pipeline can emit *generated* answers by default instead
of returning the FAQ verbatim. Two safeguards keep generations honest:

  1. Grounding check: after generating, we compute the cosine
     similarity between the generated text and the top retrieved FAQ
     answer. If it falls below a threshold the retrieval text wins,
     so the bot never invents off-corpus content.

  2. Length / token sanity: if the generation collapses to noise
     (too short, no entity overlap with the retrieved FAQ) we again
     fall back to retrieval.

The model loads lazily on first request. If the checkpoint is missing
the service returns ``mode = "retrieval_only"`` and the chat falls
straight through to the retrieved FAQ.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.myml.linalg import cosine_similarity
from app.myml.tfidf import TfidfVectorizer

_ROOT = Path(__file__).resolve().parents[3]
_CHECKPOINT = _ROOT / "api" / "app" / "myml" / "checkpoints" / "seq2seq.pt"

_TRAINER: Any = None
_STATS: dict = {}
_GROUNDING_THRESHOLD = 0.30


def _try_load() -> Any:
    global _TRAINER, _STATS
    if _TRAINER is not None:
        return _TRAINER
    if not _CHECKPOINT.is_file():
        _STATS = {"loaded": False, "reason": "no checkpoint",
                  "expected_path": str(_CHECKPOINT)}
        return None
    try:
        from app.myml.seq2seq import Seq2SeqTrainer
        _TRAINER = Seq2SeqTrainer.load(_CHECKPOINT)
        _STATS = {
            "loaded": True,
            "device": _TRAINER.device,
            "vocab_size": len(_TRAINER.vocab),
            "max_src": _TRAINER.max_src,
            "max_tgt": _TRAINER.max_tgt,
            "architecture": (
                "Encoder bi-LSTM (d_hid=128) + Decoder LSTM "
                "+ Bahdanau attention + greedy decode"
            ),
        }
    except Exception as e:  # noqa: BLE001
        _STATS = {"loaded": False, "reason": f"load error: {e}"}
        _TRAINER = None
    return _TRAINER


def generate_answer(question: str) -> str:
    """Pure generation (no grounding). Used by the auto-FAQ miner
    when proposing a candidate answer."""
    t = _try_load()
    if t is None:
        return ""
    try:
        return t.generate(question)
    except Exception:
        return ""


def stats() -> dict:
    _try_load()
    return dict(_STATS)


_WORD_RE = re.compile(r"[a-z]+")


def _word_set(text: str) -> set[str]:
    return set(_WORD_RE.findall((text or "").lower()))


def grounded_generate(question: str, retrieved_answer: str) -> dict:
    """Generate an answer for ``question``, grounded by the retrieved
    FAQ answer. Returns a structured dict so the chat router can
    decide what to surface and how to label it."""
    t = _try_load()
    if t is None:
        return {
            "mode": "retrieval_only",
            "text": retrieved_answer,
            "grounding_similarity": None,
            "model": _STATS,
        }
    try:
        gen = t.generate(question)
    except Exception as e:
        return {
            "mode": "retrieval_only",
            "text": retrieved_answer,
            "grounding_similarity": None,
            "model": {**_STATS, "error": str(e)},
        }

    # Grounding score: cosine similarity in TF-IDF space.
    try:
        vec = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True,
        )
        X = vec.fit_transform([gen or "", retrieved_answer or ""])
        sim = float(cosine_similarity(X[0:1], X[1:2])[0, 0])
    except Exception:
        sim = 0.0

    # Sanity rules: too short / too few content words / poor overlap.
    gen_words = _word_set(gen)
    ret_words = _word_set(retrieved_answer)
    overlap = len(gen_words & ret_words) / max(1, len(gen_words))
    too_short = len(gen.split()) < 6

    if too_short or sim < _GROUNDING_THRESHOLD or overlap < 0.25:
        return {
            "mode": "retrieval_fallback",
            "text": retrieved_answer,
            "generated_text": gen,
            "grounding_similarity": round(sim, 3),
            "overlap": round(overlap, 3),
            "reason": (
                "too_short" if too_short else
                ("low_overlap" if overlap < 0.25 else "low_grounding")
            ),
            "model": _STATS,
        }

    return {
        "mode": "generated",
        "text": gen,
        "retrieved_text": retrieved_answer,
        "grounding_similarity": round(sim, 3),
        "overlap": round(overlap, 3),
        "model": _STATS,
    }

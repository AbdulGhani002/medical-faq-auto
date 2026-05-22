"""Lexicon-based sentiment with negation handling.

Inspired by VADER. Each lexicon entry has a polarity in [-3, +3]. We sum
contributions per token, flip polarity for tokens inside a negation
window, and apply intensifier / diminisher multipliers. Output is a
``compound`` score in [-1, 1] and a label.

Pure Python. No model. ~150 LoC.
"""
from __future__ import annotations

import math

from .negation import negation_flags, tokenise


POSITIVE: dict[str, float] = {
    "good": 1.5, "great": 2.0, "fine": 1.0, "okay": 0.8, "ok": 0.8,
    "better": 1.5, "best": 2.0, "thanks": 1.5, "thank": 1.5,
    "appreciate": 1.5, "helpful": 1.5, "helped": 1.5, "love": 2.5,
    "like": 1.0, "happy": 2.0, "calm": 1.0, "relieved": 1.5,
    "safe": 1.2, "easy": 1.0, "comfortable": 1.5, "improved": 1.5,
    "stable": 1.0, "healthy": 1.2, "strong": 1.0, "yes": 0.5,
    "fixed": 1.5, "recovered": 2.0, "clear": 1.0,
}

NEGATIVE: dict[str, float] = {
    "bad": -1.5, "worse": -2.0, "worst": -2.5, "useless": -2.5,
    "garbage": -2.5, "stupid": -2.0, "rubbish": -2.0, "sucks": -2.0,
    "terrible": -2.5, "awful": -2.5, "horrible": -2.5,
    "scared": -2.0, "scary": -2.0, "afraid": -2.0, "worried": -1.5,
    "worry": -1.5, "anxious": -1.5, "anxiety": -1.5, "frustrated": -1.8,
    "angry": -2.0, "annoyed": -1.5, "upset": -1.5, "sad": -1.5,
    "tired": -0.8, "fatigue": -0.8, "fatigued": -0.8, "weak": -0.8,
    "pain": -1.2, "ache": -1.0, "aching": -1.0, "hurts": -1.2,
    "hurt": -1.2, "sore": -0.8, "swelling": -0.6, "stiff": -0.6,
    "dizzy": -1.0, "fainting": -1.5, "nausea": -1.0, "vomiting": -1.5,
    "bleeding": -1.5, "blurred": -1.0, "numb": -1.0, "numbness": -1.0,
    "burning": -1.0, "tight": -0.6, "tightness": -1.0,
    "breathless": -1.5, "broken": -1.5, "broke": -1.5,
    "emergency": -2.0, "urgent": -1.5, "severe": -2.0,
    "no": -0.4,  # mild negative cue, also affects negation
}

INTENSIFIERS: dict[str, float] = {
    "very": 1.5, "really": 1.4, "super": 1.5, "extremely": 1.8,
    "so": 1.3, "too": 1.3, "much": 1.3, "lots": 1.3,
}
DIMINISHERS: dict[str, float] = {
    "slightly": 0.5, "a bit": 0.6, "a little": 0.6, "kind of": 0.6,
    "somewhat": 0.6, "barely": 0.4, "hardly": 0.4,
}


def _score_token(tok: str) -> float:
    if tok in POSITIVE:
        return POSITIVE[tok]
    if tok in NEGATIVE:
        return NEGATIVE[tok]
    return 0.0


def analyse(text: str) -> dict:
    """Return {compound, label, positives, negatives, intensified}."""
    toks = tokenise(text)
    flags = negation_flags(toks)
    pos_terms: list[str] = []
    neg_terms: list[str] = []
    intensifier_pending = 1.0

    score = 0.0
    for i, tok in enumerate(toks):
        if tok in INTENSIFIERS:
            intensifier_pending *= INTENSIFIERS[tok]
            continue
        if tok in DIMINISHERS:
            intensifier_pending *= DIMINISHERS[tok]
            continue

        raw = _score_token(tok)
        if raw == 0.0:
            intensifier_pending = 1.0
            continue
        if flags[i]:
            raw *= -1
        raw *= intensifier_pending
        intensifier_pending = 1.0
        score += raw
        if raw > 0:
            pos_terms.append(tok)
        else:
            neg_terms.append(tok)

    # Squash via a sigmoid-like curve to [-1, 1].
    compound = math.tanh(score / 4.0)

    if compound >= 0.25:
        label = "positive"
    elif compound <= -0.25:
        label = "negative"
    else:
        label = "neutral"

    return {
        "compound": round(compound, 3),
        "label": label,
        "positives": pos_terms,
        "negatives": neg_terms,
    }


def is_distressed(text: str) -> bool:
    return analyse(text)["compound"] <= -0.4

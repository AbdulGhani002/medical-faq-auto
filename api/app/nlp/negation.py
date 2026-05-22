"""Lightweight negation scope detection.

Implements a NegEx-style cue + window scope detector. Each negation cue
("not", "no", "without", "never", "n't" suffix, "cannot") flips the
polarity of up to N tokens to its right, stopping at a clause boundary
(',', '.', 'but', 'however', 'yet', '?').

We expose:
  detect_negations(text) -> list of (cue_token_index, scope_slice)
  negation_flags(tokens) -> per-token bool array
  is_negated(text)       -> True if any negation cue exists
"""
from __future__ import annotations

import re

_TOKEN_RE = re.compile(r"[a-zA-Z0-9']+|[.,;:?!]")

_CUES = {
    "not", "no", "never", "without", "cannot", "cant", "wont",
    "shouldnt", "couldnt", "doesnt", "didnt", "isnt", "arent",
    "wasnt", "werent", "havent", "hasnt", "hadnt", "dont",
    "none", "neither", "nor",
}

_BOUNDARY = {",", ".", ";", "?", "!", "but", "however", "yet",
             "although", "though", "while", "whereas", "except"}

_WINDOW = 4  # tokens after the cue stay negated


def tokenise(text: str) -> list[str]:
    """Negation-aware tokeniser that preserves punctuation."""
    raw = _TOKEN_RE.findall(text or "")
    out: list[str] = []
    for t in raw:
        tl = t.lower()
        # Normalise contractions: don't -> do n't but we drop apostrophe.
        if "'" in tl:
            base = tl.replace("'", "")
            out.append(base)
        else:
            out.append(tl)
    return out


def negation_flags(tokens: list[str]) -> list[bool]:
    """Return a list of bools, same length as tokens, True = negated."""
    flags = [False] * len(tokens)
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t in _CUES or t.endswith("nt") and t not in {"isnt"} and len(t) > 3:
            j = i + 1
            steps = 0
            while j < len(tokens) and steps < _WINDOW:
                if tokens[j] in _BOUNDARY:
                    break
                flags[j] = True
                j += 1
                steps += 1
        i += 1
    return flags


def detect_negations(text: str) -> list[dict]:
    """Return cue + scope spans as [{cue, scope: [tokens]}]."""
    toks = tokenise(text)
    flags = negation_flags(toks)
    out: list[dict] = []
    i = 0
    while i < len(toks):
        t = toks[i]
        if t in _CUES or (t.endswith("nt") and len(t) > 3):
            scope = []
            j = i + 1
            while j < len(toks) and flags[j]:
                if toks[j] not in _BOUNDARY:
                    scope.append(toks[j])
                j += 1
            out.append({"cue": t, "scope": scope})
            i = j
        else:
            i += 1
    return out


def is_negated(text: str) -> bool:
    return any(detect_negations(text))


def negated_tokens(text: str) -> list[str]:
    """The tokens whose polarity has been flipped."""
    toks = tokenise(text)
    flags = negation_flags(toks)
    return [t for t, f in zip(toks, flags) if f and t.isalpha()]

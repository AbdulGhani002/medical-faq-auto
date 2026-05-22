"""Highlight which words in the matched FAQ triggered the match.

We compute the set of stemmed query tokens, then for every token in the
FAQ question + answer mark the token as highlighted iff its stem is in
the query set. The frontend uses this to bold or underline the matched
spans, giving the user a transparent reason for the answer.
"""
from __future__ import annotations

import re

from .lemmatize import canonical
from .normalize import _STOPWORDS, expand_query

_TOK_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*")


def _query_stems(query: str) -> set[str]:
    expanded = expand_query(query)
    stems: set[str] = set()
    for tok in re.findall(r"[a-z0-9]+", expanded.lower()):
        if tok in _STOPWORDS or len(tok) < 2:
            continue
        stems.add(canonical(tok))
    return stems


def highlight_text(text: str, query: str) -> list[dict]:
    """Return [{text, hl}] segments preserving spaces and punctuation."""
    if not text:
        return []
    stems = _query_stems(query)
    out: list[dict] = []
    pos = 0
    for m in _TOK_RE.finditer(text):
        if m.start() > pos:
            out.append({"text": text[pos:m.start()], "hl": False})
        tok = m.group(0)
        cano = canonical(tok.lower())
        out.append({"text": tok, "hl": cano in stems})
        pos = m.end()
    if pos < len(text):
        out.append({"text": text[pos:], "hl": False})
    return out


def overlap_score(text: str, query: str) -> float:
    """Token-overlap ratio: how much of the query's content tokens appear
    in `text` (used as a quick sanity check)."""
    stems = _query_stems(query)
    if not stems:
        return 0.0
    text_stems = {
        canonical(t)
        for t in re.findall(r"[a-z0-9]+", text.lower())
        if t not in _STOPWORDS and len(t) >= 2
    }
    if not text_stems:
        return 0.0
    return len(stems & text_stems) / len(stems)

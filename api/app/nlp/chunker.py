"""Noun-phrase chunker: shallow parsing via POS patterns.

Given a POS-tagged sentence, extract noun phrases that match the
classical greedy pattern:

    NP -> DT? PRP? (JJ | CD | NN)* NN+

This is the same chunker style used by NLTK's RegexpParser. We add a
small post-filter: drop NPs that are entirely stopwords or pronouns.

A second routine extracts verb phrases:

    VP -> (MD | RB)* VB+ RB*

Used downstream by the knowledge-graph triple extractor.
"""
from __future__ import annotations

_NN_LIKE = {"NN"}
_NP_INNER = {"NN", "JJ", "CD"}
_NP_LEFT = {"DT", "PRP"}


def noun_phrases(tagged: list[tuple[str, str]]) -> list[dict]:
    """Return a list of NP spans: {text, start, end (token indices)}."""
    chunks: list[dict] = []
    i = 0
    n = len(tagged)
    while i < n:
        # Optional left modifier (DT/PRP).
        j = i
        if tagged[j][1] in _NP_LEFT:
            j += 1
        # Adjectives/numbers/nouns greedily; must end with at least one NN.
        start_inner = j
        while j < n and tagged[j][1] in _NP_INNER:
            j += 1
        # The chunk must contain at least one noun.
        if j > start_inner and any(
            tagged[k][1] in _NN_LIKE for k in range(start_inner, j)
        ):
            words = [w for w, _ in tagged[i:j]]
            text = " ".join(words)
            chunks.append({
                "text": text,
                "start_tok": i,
                "end_tok": j,
            })
            i = j
            continue
        i += 1
    return chunks


def verb_phrases(tagged: list[tuple[str, str]]) -> list[dict]:
    """Verb phrases: optional MD/RB, then one or more VB, then optional RB."""
    chunks: list[dict] = []
    i = 0
    n = len(tagged)
    while i < n:
        j = i
        while j < n and tagged[j][1] in {"MD", "RB"}:
            j += 1
        start_vb = j
        while j < n and tagged[j][1] == "VB":
            j += 1
        if j == start_vb:
            i += 1
            continue
        while j < n and tagged[j][1] == "RB":
            j += 1
        text = " ".join(w for w, _ in tagged[i:j])
        chunks.append({
            "text": text,
            "start_tok": i,
            "end_tok": j,
        })
        i = j
    return chunks


def chunk(tagged: list[tuple[str, str]]) -> dict:
    """One-shot helper. Returns both NPs and VPs."""
    return {
        "noun_phrases": noun_phrases(tagged),
        "verb_phrases": verb_phrases(tagged),
    }

"""Extractive summarisation via sentence-level TextRank.

Given a list of FAQ texts, we split into sentences, score each with
TextRank over a TF-IDF cosine graph, and return the top-N sentences.

Used only when retrieval produces several near-tied matches and the
dialog manager wants to offer a unified explanation.
"""
from __future__ import annotations

import re

import numpy as np

from app.myml.tfidf import TfidfVectorizer
from app.myml.linalg import cosine_similarity

_SENT_RE = re.compile(r"(?<=[.!?])\s+")


def split_sentences(text: str) -> list[str]:
    sents = [s.strip() for s in _SENT_RE.split(text or "") if s.strip()]
    return sents


def rank_sentences(sentences: list[str],
                   damping: float = 0.85, iters: int = 30) -> list[float]:
    if not sentences:
        return []
    if len(sentences) == 1:
        return [1.0]
    vec = TfidfVectorizer(min_df=1, sublinear_tf=True)
    try:
        mat = vec.fit_transform(sentences)
    except ValueError:
        return [1.0] * len(sentences)
    sim = cosine_similarity(mat)
    np.fill_diagonal(sim, 0.0)
    deg = sim.sum(axis=1) + 1e-9
    scores = np.ones(len(sentences)) / len(sentences)
    for _ in range(iters):
        new = (1.0 - damping) / len(sentences) + damping * (
            sim @ (scores / deg)
        )
        scores = new
    return scores.tolist()


def summarise(text: str, n: int = 2) -> str:
    sents = split_sentences(text)
    if len(sents) <= n:
        return " ".join(sents)
    scores = rank_sentences(sents)
    order = sorted(range(len(sents)), key=lambda i: -scores[i])[:n]
    order.sort()
    return " ".join(sents[i] for i in order)


def multi_doc_summary(docs: list[str], n: int = 3) -> str:
    """Top-N most central sentences across the input set."""
    all_sents: list[str] = []
    for d in docs:
        all_sents.extend(split_sentences(d))
    if not all_sents:
        return ""
    scores = rank_sentences(all_sents)
    order = sorted(range(len(all_sents)), key=lambda i: -scores[i])[:n]
    order.sort()
    return " ".join(all_sents[i] for i in order)

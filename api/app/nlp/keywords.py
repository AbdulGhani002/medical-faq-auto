"""TextRank-style keyword extraction.

We build a token-co-occurrence graph inside a sliding window and run
weighted PageRank for 30 iterations. The top-N nodes after convergence
are returned as keywords.

Pure Python. No model. Used for follow-up suggestion + topic summary.
"""
from __future__ import annotations

import re

from .normalize import _STOPWORDS

_TOK_RE = re.compile(r"[a-z][a-z]+")


def _tokens(text: str) -> list[str]:
    return [t for t in _TOK_RE.findall((text or "").lower())
            if t not in _STOPWORDS and len(t) > 2]


def extract(text: str, top_k: int = 6, window: int = 4,
            damping: float = 0.85, iters: int = 30) -> list[tuple[str, float]]:
    """Return [(keyword, score)] best first."""
    toks = _tokens(text)
    if len(toks) < 3:
        return [(t, 1.0) for t in toks[:top_k]]

    # Build co-occurrence weights.
    graph: dict[str, dict[str, float]] = {}
    for i, t in enumerate(toks):
        for j in range(i + 1, min(i + window, len(toks))):
            u = toks[j]
            if u == t:
                continue
            graph.setdefault(t, {})
            graph.setdefault(u, {})
            graph[t][u] = graph[t].get(u, 0.0) + 1.0
            graph[u][t] = graph[u].get(t, 0.0) + 1.0

    nodes = list(graph.keys())
    if not nodes:
        return []
    score = {n: 1.0 for n in nodes}
    for _ in range(iters):
        new_score = {}
        for n in nodes:
            s = (1.0 - damping)
            for nb, w in graph[n].items():
                deg = sum(graph[nb].values()) or 1.0
                s += damping * (w / deg) * score[nb]
            new_score[n] = s
        score = new_score

    ranked = sorted(score.items(), key=lambda kv: -kv[1])
    return [(k, round(v, 4)) for k, v in ranked[:top_k]]


def keywords(text: str, top_k: int = 6) -> list[str]:
    return [k for k, _ in extract(text, top_k=top_k)]

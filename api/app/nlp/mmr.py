"""Maximal Marginal Relevance for diverse alternative selection.

MMR(d) = lambda * sim(q, d) - (1 - lambda) * max_{d' in S} sim(d, d')

We use it after the initial retrieval to pick the top-k alternatives such
that they are simultaneously relevant to the query and dissimilar from
each other. This stops the "Did you mean?" card from showing three near
duplicates.
"""
from __future__ import annotations

import numpy as np


def mmr_select(
    candidate_indices: list[int],
    relevance: np.ndarray,
    similarity_matrix: np.ndarray,
    k: int = 3,
    lam: float = 0.7,
) -> list[int]:
    """Return up to `k` candidate indices ordered by MMR.

    Parameters
    ----------
    candidate_indices  ids of candidates to consider, best-first.
    relevance          relevance[i] for every doc id in the corpus.
    similarity_matrix  pairwise similarity over the corpus (symmetric).
    k                  how many to return.
    lam                trade-off relevance vs diversity in [0, 1].
    """
    if not candidate_indices:
        return []
    selected: list[int] = []
    remaining = list(candidate_indices)
    while remaining and len(selected) < k:
        if not selected:
            best = max(remaining, key=lambda i: relevance[i])
            selected.append(best)
            remaining.remove(best)
            continue
        # Penalise by maximum similarity to anything already selected.
        def _score(i: int) -> float:
            max_sim = max(similarity_matrix[i, s] for s in selected)
            return lam * relevance[i] - (1.0 - lam) * max_sim
        best = max(remaining, key=_score)
        selected.append(best)
        remaining.remove(best)
    return selected

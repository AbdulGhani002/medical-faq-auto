"""Word Mover's Distance via the relaxed (RWMD) formulation.

For two documents A and B with bag-of-words distributions over an
embedding vocabulary, the exact WMD is the optimal-transport cost. It
is O(|V|^3 log |V|) which is too slow at request time.

We use the classical *relaxed* WMD (Kusner et al. 2015) which gives a
tight lower bound in O(|V_A| · |V_B|) time:

    RWMD(A, B) = sum_{w in A} freq(w) · min_{w' in B} d(w, w')

We average the two directions (A→B + B→A) / 2. The "distance" is then
converted to a similarity in [0, 1] by exp(-distance).

Uses the corpus PPMI embeddings (``embeddings.CorpusEmbeddings``). No
external dependency, no LP solver, no neural net.
"""
from __future__ import annotations

import numpy as np

from .embeddings import CorpusEmbeddings


def _bow(tokens: list[str], emb: CorpusEmbeddings) -> tuple[list[int], np.ndarray]:
    """Convert tokens to (vocab_ids, weights) where weights sum to 1."""
    ids: list[int] = []
    counts: dict[int, float] = {}
    for t in tokens:
        from .lemmatize import canonical
        c = canonical(t)
        idx = emb.word_to_idx.get(c)
        if idx is None:
            continue
        counts[idx] = counts.get(idx, 0.0) + 1.0
    if not counts:
        return [], np.zeros(0, dtype=np.float32)
    ids = list(counts.keys())
    w = np.asarray([counts[i] for i in ids], dtype=np.float32)
    return ids, w / w.sum()


def relaxed_wmd(tokens_a: list[str], tokens_b: list[str],
                emb: CorpusEmbeddings) -> float:
    """Relaxed Word Mover's Distance (one-sided average)."""
    ids_a, wa = _bow(tokens_a, emb)
    ids_b, wb = _bow(tokens_b, emb)
    if not ids_a or not ids_b:
        return 1.0
    va = emb.vectors[ids_a]
    vb = emb.vectors[ids_b]
    # Cosine distance = 1 - cos. Vectors are L2-normalised by CorpusEmbeddings.
    cos = va @ vb.T  # (|A|, |B|)
    dist = 1.0 - cos
    a_to_b = float((wa * dist.min(axis=1)).sum())
    b_to_a = float((wb * dist.min(axis=0)).sum())
    return 0.5 * (a_to_b + b_to_a)


def similarity(tokens_a: list[str], tokens_b: list[str],
               emb: CorpusEmbeddings) -> float:
    """exp(-RWMD). Always in [0, 1]; 1 = identical, lower = more distant."""
    d = relaxed_wmd(tokens_a, tokens_b, emb)
    return float(np.exp(-d))

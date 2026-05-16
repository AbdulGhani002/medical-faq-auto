"""Rank fusion + confidence helpers."""
import numpy as np


def reciprocal_rank_fusion(
    rankings: dict[str, list[int]],
    k: int = 60,
) -> list[tuple[int, float]]:
    """Reciprocal rank fusion across multiple ranker outputs.

    Each value in `rankings` is a list of doc ids ordered best-first.
    Returns [(doc_id, fused_score)] sorted desc.
    """
    fused: dict[int, float] = {}
    for ranker_name, ids in rankings.items():
        for rank, doc_id in enumerate(ids):
            fused[doc_id] = fused.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    return sorted(fused.items(), key=lambda kv: -kv[1])


def to_confidence(blended_score: float) -> float:
    """Map an unbounded blended score to a 0..1 confidence using a soft curve.

    The curve saturates so very large scores still report as < 1, which
    looks honest in the UI. A blended score of 0.5 -> ~0.66 confidence.
    """
    s = max(0.0, float(blended_score))
    return s / (s + 0.25)


def best_match(
    scores: list[tuple[int, float, dict[str, float]]],
    accept_threshold: float = 0.18,
    soft_threshold: float = 0.08,
) -> dict:
    """Bucket the top candidate as ``confident``, ``best_guess``, or ``none``."""
    if not scores:
        return {"bucket": "none", "top": None}
    top_idx, top_score, top_per = scores[0]
    if top_score >= accept_threshold:
        bucket = "confident"
    elif top_score >= soft_threshold:
        bucket = "best_guess"
    else:
        bucket = "none"
    return {
        "bucket": bucket,
        "top": {"idx": top_idx, "score": top_score, "per_method": top_per},
        "alternatives": [
            {"idx": i, "score": s} for i, s, _ in scores[1:4]
        ],
    }


def rank_fusion(
    methods_scores: dict[str, np.ndarray], top_k: int = 10
) -> list[tuple[int, float]]:
    """Convenience: convert per-method score arrays into RRF result."""
    rankings: dict[str, list[int]] = {}
    for name, arr in methods_scores.items():
        order = np.argsort(-arr).tolist()
        rankings[name] = order[:top_k]
    return reciprocal_rank_fusion(rankings)

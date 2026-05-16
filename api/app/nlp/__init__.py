"""Classical NLP pipeline: tokenize -> expand -> index -> score.

No neural model, no LLM, no AI API. Pure Python + scikit-learn + rank_bm25.
"""
from .context import augment_with_context, is_followup
from .indexer import HybridIndex
from .normalize import expand_query, tokenize
from .scoring import rank_fusion

__all__ = [
    "HybridIndex",
    "augment_with_context",
    "expand_query",
    "is_followup",
    "rank_fusion",
    "tokenize",
]

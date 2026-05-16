"""Classical NLP pipeline.

Token level: normalize -> expand synonyms -> spell-correct against vocab.
Doc level:   word TF-IDF + char TF-IDF + BM25 -> blend.
Query level: intent classify -> pseudo-relevance feedback -> rerank.

No neural model, no LLM, no AI API. Pure Python + scikit-learn + rank_bm25.
"""
from .context import augment_with_context, is_followup
from .feedback import expand_with_feedback, jaccard, top_terms_from_docs
from .indexer import HybridIndex
from .intent import canned, classify
from .normalize import expand_query, tokenize
from .scoring import best_match, rank_fusion, to_confidence
from .spell import Corrector

__all__ = [
    "HybridIndex", "Corrector",
    "augment_with_context", "best_match", "canned", "classify",
    "expand_query", "expand_with_feedback", "is_followup", "jaccard",
    "rank_fusion", "to_confidence", "tokenize", "top_terms_from_docs",
]

"""Retrieval over the FAQ index. No LLM in the loop.

Embeds the user's question with the same model used by the pipeline and runs
a nearest-neighbour search on the per-specialty Qdrant collection.

Heavy deps (qdrant-client, sentence-transformers, torch) are imported lazily
so the API can still boot if they are not installed.
"""
from typing import Any, Optional, Tuple

from app.config import settings

_client: Optional[Any] = None
_model: Optional[Any] = None


def _get_client():
    global _client
    if _client is None:
        from qdrant_client import QdrantClient  # lazy
        _client = QdrantClient(
            host=settings.qdrant_host, port=settings.qdrant_port
        )
    return _client


def _get_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer  # lazy
        _model = SentenceTransformer(settings.embedding_model)
    return _model


async def retrieve_answer(
    specialty: str, text: str
) -> Tuple[str, Optional[str], float]:
    """Look up the closest stored answer for the user question.

    Returns (answer, faq_id, confidence). If the top hit is below the
    confidence threshold, returns a polite fallback message.
    """
    try:
        model = _get_model()
        client = _get_client()
    except Exception:
        return (
            "The retrieval service is starting up. Please try again in a moment.",
            None,
            0.0,
        )

    try:
        vec = model.encode(text, normalize_embeddings=True).tolist()
    except Exception:
        return (
            "Unable to embed your question right now. Please try again later.",
            None,
            0.0,
        )

    collection = f"faqs_{specialty}"
    try:
        hits = client.search(
            collection_name=collection,
            query_vector=vec,
            limit=settings.retrieval_top_k,
        )
    except Exception:
        return (
            "Sorry, the FAQ index is not ready yet. Please try again later.",
            None,
            0.0,
        )

    if not hits:
        return (
            "I do not have a stored answer for that yet. Please contact the "
            "clinic directly.",
            None,
            0.0,
        )

    top = hits[0]
    if top.score < settings.confidence_threshold:
        return (
            "I am not confident about an answer for that question. Please "
            "contact the clinic directly so a clinician can help.",
            None,
            float(top.score),
        )

    payload = top.payload or {}
    return (
        payload.get("answer", ""),
        payload.get("faq_id"),
        float(top.score),
    )

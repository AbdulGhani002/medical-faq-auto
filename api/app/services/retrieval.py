"""Hybrid lexical retrieval: TF-IDF (word + char) + BM25 + synonym expansion
+ conversation context. No neural model, no LLM, no AI API.
"""
from typing import Optional

from app.db import get_db
from app.nlp.context import augment_with_context
from app.nlp.indexer import HybridIndex
from app.nlp.scoring import best_match, to_confidence

_INDEX_CACHE: dict[str, HybridIndex] = {}
_FAQS_CACHE: dict[str, list[dict]] = {}


def invalidate_cache(specialty: str | None = None) -> None:
    if specialty:
        _INDEX_CACHE.pop(specialty, None)
        _FAQS_CACHE.pop(specialty, None)
        return
    _INDEX_CACHE.clear()
    _FAQS_CACHE.clear()


async def _load_corpus(specialty: str) -> list[dict]:
    db = get_db()
    cursor = db.faqs.find({"specialty": specialty, "approved": True})
    docs: list[dict] = []
    async for d in cursor:
        docs.append(d)
    return docs


async def _get_index(specialty: str) -> tuple[HybridIndex, list[dict]] | tuple[None, list]:
    if specialty in _INDEX_CACHE:
        return _INDEX_CACHE[specialty], _FAQS_CACHE[specialty]
    faqs = await _load_corpus(specialty)
    if not faqs:
        return None, []
    idx = HybridIndex(faqs)
    _INDEX_CACHE[specialty] = idx
    _FAQS_CACHE[specialty] = faqs
    return idx, faqs


async def _previous_user_text(session_id: str, current_text: str) -> Optional[str]:
    """Return the most recent user turn in this session whose text differs
    from the current message. None if no prior turn exists."""
    if not session_id:
        return None
    db = get_db()
    cursor = (
        db.chat_turns.find({"session_id": session_id, "role": "user"})
        .sort("timestamp", -1)
        .limit(4)
    )
    async for t in cursor:
        text = t.get("text", "")
        if text and text != current_text:
            return text
    return None


def _format_response(
    bucket_info: dict, faqs: list[dict], session_id: str | None
) -> dict:
    if bucket_info["bucket"] == "none" or bucket_info["top"] is None:
        return {
            "answer": (
                "I do not have a good match for that question. Try "
                "rephrasing, ask a simpler question, or pick one of the "
                "suggested topics below."
            ),
            "matched_faq_id": None,
            "confidence": 0.0,
            "alternatives": [],
            "bucket": "none",
        }
    top = bucket_info["top"]
    faq = faqs[top["idx"]]
    alternatives = [
        {
            "id": str(faqs[a["idx"]]["_id"]),
            "question": faqs[a["idx"]]["question"],
            "score": round(a["score"], 3),
        }
        for a in bucket_info.get("alternatives", [])
    ]
    intro = ""
    if bucket_info["bucket"] == "best_guess":
        intro = (
            "I am not fully sure, but my closest stored answer is:\n\n"
        )
    answer = intro + faq["answer"]
    return {
        "answer": answer,
        "matched_faq_id": str(faq["_id"]),
        "confidence": to_confidence(top["score"]),
        "alternatives": alternatives,
        "bucket": bucket_info["bucket"],
    }


async def retrieve_answer(
    specialty: str, text: str, session_id: str | None = None
) -> dict:
    """Main entry point. Returns a structured dict the chat router serialises.
    """
    idx, faqs = await _get_index(specialty)
    if idx is None:
        return {
            "answer": (
                "No FAQs are approved for this specialty yet. Please check "
                "back soon or contact the clinic."
            ),
            "matched_faq_id": None,
            "confidence": 0.0,
            "alternatives": [],
            "bucket": "none",
        }

    prev_text = await _previous_user_text(session_id or "", text)
    query = augment_with_context(text, prev_text)
    scores = idx.top_k(query, k=5)
    info = best_match(scores)
    return _format_response(info, faqs, session_id)

"""Sophisticated lexical retrieval pipeline. No neural model, no LLM.

For each request we run:
  1. Intent classification (greeting / thanks / frustration / help / question).
  2. Conversation context augmentation (follow-up detection).
  3. Spell correction over the FAQ vocabulary.
  4. Initial retrieval with TF-IDF word + TF-IDF char + BM25.
  5. Pseudo-relevance feedback re-ranking.
  6. Bucketing + alternatives + explainability returned to the client.
"""
from typing import Optional

from app.db import get_db
from app.nlp import (
    Corrector, HybridIndex,
    augment_with_context, best_match, canned, classify,
    tokenize, to_confidence,
)
from app.nlp.normalize import _STOPWORDS  # noqa: WPS437 - intentional

_INDEX_CACHE: dict[str, HybridIndex] = {}
_FAQS_CACHE: dict[str, list[dict]] = {}
_CORRECTOR_CACHE: dict[str, Corrector] = {}


def invalidate_cache(specialty: str | None = None) -> None:
    if specialty:
        _INDEX_CACHE.pop(specialty, None)
        _FAQS_CACHE.pop(specialty, None)
        _CORRECTOR_CACHE.pop(specialty, None)
        return
    _INDEX_CACHE.clear()
    _FAQS_CACHE.clear()
    _CORRECTOR_CACHE.clear()


async def _load_corpus(specialty: str) -> list[dict]:
    db = get_db()
    cursor = db.faqs.find({"specialty": specialty, "approved": True})
    docs: list[dict] = []
    async for d in cursor:
        docs.append(d)
    return docs


async def _ensure_index(specialty: str):
    if specialty in _INDEX_CACHE:
        return _INDEX_CACHE[specialty], _FAQS_CACHE[specialty], _CORRECTOR_CACHE[specialty]
    faqs = await _load_corpus(specialty)
    if not faqs:
        return None, [], None
    idx = HybridIndex(faqs)
    corr = Corrector(idx.vocabulary_stream())
    _INDEX_CACHE[specialty] = idx
    _FAQS_CACHE[specialty] = faqs
    _CORRECTOR_CACHE[specialty] = corr
    return idx, faqs, corr


async def _previous_user_text(session_id: str, current: str) -> Optional[str]:
    if not session_id:
        return None
    db = get_db()
    cursor = (
        db.chat_turns.find({"session_id": session_id, "role": "user"})
        .sort("timestamp", -1).limit(4)
    )
    async for t in cursor:
        text = t.get("text", "")
        if text and text != current:
            return text
    return None


def _empty_response(answer: str, intent: str = "question") -> dict:
    return {
        "answer": answer,
        "matched_faq_id": None,
        "confidence": 0.0,
        "alternatives": [],
        "bucket": "none",
        "intent": intent,
        "spell_corrections": [],
        "expanded_query": "",
        "added_terms": [],
        "score_breakdown": None,
    }


def _format(
    bucket_info: dict, faqs: list[dict], intent: str,
    fixes: list[tuple[str, str]], expanded: str, added: list[str],
) -> dict:
    if bucket_info["bucket"] == "none" or bucket_info["top"] is None:
        body = _empty_response(
            "I do not have a good match for that. Try rephrasing or pick "
            "a suggested topic below.", intent=intent,
        )
        body["spell_corrections"] = [
            {"original": o, "fixed": f} for o, f in fixes
        ]
        body["expanded_query"] = expanded
        body["added_terms"] = added
        return body
    top = bucket_info["top"]
    faq = faqs[top["idx"]]
    intro = ""
    if bucket_info["bucket"] == "best_guess":
        intro = "I am not fully sure, but the closest match is:\n\n"
    return {
        "answer": intro + faq["answer"],
        "matched_faq_id": str(faq["_id"]),
        "confidence": to_confidence(top["score"]),
        "alternatives": [
            {
                "id": str(faqs[a["idx"]]["_id"]),
                "question": faqs[a["idx"]]["question"],
                "score": round(a["score"], 3),
            }
            for a in bucket_info.get("alternatives", [])
        ],
        "bucket": bucket_info["bucket"],
        "intent": intent,
        "spell_corrections": [
            {"original": o, "fixed": f} for o, f in fixes
        ],
        "expanded_query": expanded,
        "added_terms": added,
        "score_breakdown": {
            "tfidf_word": round(top["per_method"]["tfidf_word"], 3),
            "tfidf_char": round(top["per_method"]["tfidf_char"], 3),
            "bm25": round(top["per_method"]["bm25"], 3),
            "blended": round(top["score"], 3),
            "matched_question": faq["question"],
        },
    }


async def retrieve_answer(
    specialty: str, text: str, session_id: str | None = None
) -> dict:
    # 1. Intent classification (non-questions get canned replies).
    intent = classify(text)
    if intent != "question":
        msg = canned(intent, specialty) or ""
        return {**_empty_response(msg, intent=intent), "confidence": 1.0,
                "bucket": "confident"}

    # 2. Load (or build) per-specialty index and corrector.
    idx, faqs, corr = await _ensure_index(specialty)
    if idx is None or corr is None:
        return _empty_response(
            "No FAQs are approved for this specialty yet. Please check "
            "back soon or contact the clinic.",
        )

    # 3. Context augmentation.
    prev_text = await _previous_user_text(session_id or "", text)
    contextual = augment_with_context(text, prev_text)

    # 4. Spell correction against FAQ vocabulary.
    # Skip stopwords entirely (they would be wrongly auto-corrected because
    # they are not present in the indexed vocabulary) and skip tokens shorter
    # than 4 characters where a single typo is hard to disambiguate.
    raw_tokens = tokenize(contextual, drop_stopwords=False)
    fix_targets = [
        t for t in raw_tokens if t not in _STOPWORDS and len(t) >= 4
    ]
    fixed_subset, fixes = corr.correct(fix_targets)
    fix_map = {orig: fixed for orig, fixed in zip(fix_targets, fixed_subset)}
    fixed_tokens = [fix_map.get(t, t) for t in raw_tokens]
    corrected = " ".join(fixed_tokens)

    # 5. Two-pass retrieval with pseudo-relevance feedback.
    scores, added_terms, expanded = idx.top_k_with_prf(corrected, k=5)
    info = best_match(scores)

    return _format(info, faqs, intent, fixes, expanded, added_terms)

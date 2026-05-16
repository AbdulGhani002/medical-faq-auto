"""Pure lexical retrieval using BM25. No neural model, no LLM, no AI.

BM25 is a 1990s statistical IR algorithm based on term frequency and document
length. It runs in pure Python on the FAQ corpus stored in MongoDB. Every
answer the user sees is a real clinician-reviewed reply from mongo.faqs.
"""
import re
from typing import Optional, Tuple

from app.config import settings
from app.db import get_db

try:
    from rank_bm25 import BM25Okapi
    _HAVE_BM25 = True
except ImportError:
    _HAVE_BM25 = False


_TOKEN_RE = re.compile(r"\w+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


async def _load_corpus(specialty: str) -> list[dict]:
    db = get_db()
    cursor = db.faqs.find({"specialty": specialty, "approved": True})
    docs: list[dict] = []
    async for d in cursor:
        docs.append(d)
    return docs


async def retrieve_answer(
    specialty: str, text: str
) -> Tuple[str, Optional[str], float]:
    """Return (answer, faq_id, normalized_confidence) for the user question.

    Uses BM25 against approved FAQs for this specialty. No neural model.
    """
    if not _HAVE_BM25:
        return (
            "The retrieval engine is not installed. Run "
            "`pip install rank_bm25` and try again.",
            None,
            0.0,
        )

    query_tokens = _tokenize(text)
    if not query_tokens:
        return ("Please type a question.", None, 0.0)

    docs = await _load_corpus(specialty)
    if not docs:
        return (
            "No FAQs are approved for this specialty yet. Please check back "
            "soon or contact the clinic.",
            None,
            0.0,
        )

    # BM25 over question+answer text for slightly better recall.
    corpus = [_tokenize(d["question"] + " " + d["answer"]) for d in docs]
    bm25 = BM25Okapi(corpus)
    scores = bm25.get_scores(query_tokens)
    best_idx = int(scores.argmax())
    best_score = float(scores[best_idx])

    # Normalise BM25 (which is unbounded) into 0..1 for the UI.
    confidence = best_score / (best_score + 1.0)

    if best_score < settings.bm25_min_score:
        return (
            "I do not have a stored answer for that question. Please rephrase, "
            "or contact the clinic directly.",
            None,
            confidence,
        )

    top = docs[best_idx]
    return top["answer"], str(top["_id"]), confidence

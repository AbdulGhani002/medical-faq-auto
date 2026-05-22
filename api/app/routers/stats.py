"""Aggregated statistics for the admin dashboard."""
from __future__ import annotations

from collections import Counter

from fastapi import APIRouter

from app.db import get_db
from app.services.analyzer import analyse as analyse_text

router = APIRouter()


@router.get("/overview")
async def overview() -> dict:
    """Counts per specialty + recent activity."""
    db = get_db()
    out: dict = {"specialties": []}
    for spec in ("radiology", "physiotherapy", "cardiovascular"):
        approved = await db.faqs.count_documents(
            {"specialty": spec, "approved": True})
        pending = await db.faqs.count_documents(
            {"specialty": spec, "approved": False, "rejected": {"$ne": True}})
        rejected = await db.faqs.count_documents(
            {"specialty": spec, "rejected": True})
        turns = await db.chat_turns.count_documents({"specialty": spec})
        out["specialties"].append({
            "specialty": spec, "approved": approved,
            "pending": pending, "rejected": rejected,
            "chat_turns": turns,
        })
    return out


@router.get("/chat_distribution/{specialty}")
async def chat_distribution(specialty: str, limit: int = 500) -> dict:
    """Run the analyser over the most recent user turns and bucket by
    intent / sentiment / triage / entity-label. Powers the dashboard
    charts."""
    db = get_db()
    cur = (
        db.chat_turns.find({"specialty": specialty, "role": "user"})
        .sort("timestamp", -1).limit(limit)
    )

    intent_counts: Counter = Counter()
    sentiment_counts: Counter = Counter()
    triage_counts: Counter = Counter()
    label_counts: Counter = Counter()
    qtype_counts: Counter = Counter()
    top_keywords: Counter = Counter()

    n = 0
    async for t in cur:
        text = t.get("text") or ""
        if not text.strip():
            continue
        try:
            a = analyse_text(text)
        except Exception:
            continue
        n += 1
        intent_counts[a["intent"]["label"]] += 1
        sentiment_counts[a["sentiment"]["label"]] += 1
        triage_counts[f"level-{a['triage']['level']}"] += 1
        qtype_counts[a["question_type"]] += 1
        for e in a["entities"]:
            label_counts[e["label"]] += 1
        for k in a["keywords"]:
            top_keywords[k["text"]] += 1

    def _top(c: Counter, k: int = 10) -> list[dict]:
        return [{"label": l, "count": v} for l, v in c.most_common(k)]

    return {
        "specialty": specialty,
        "n_turns_analysed": n,
        "intent": _top(intent_counts, 12),
        "sentiment": _top(sentiment_counts, 5),
        "triage": _top(triage_counts, 4),
        "entity_label": _top(label_counts, 8),
        "question_type": _top(qtype_counts, 8),
        "top_keywords": _top(top_keywords, 15),
    }

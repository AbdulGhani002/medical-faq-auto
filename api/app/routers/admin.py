"""Admin endpoints: approve, edit, reject candidate FAQs.

Every action that changes the approved set invalidates the retrieval
cache so the chatbot sees the new state on the next request.
"""
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_db
from app.services.retrieval import invalidate_cache

router = APIRouter()


class FAQEdit(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None


def _oid(faq_id: str) -> ObjectId:
    try:
        return ObjectId(faq_id)
    except Exception:
        raise HTTPException(400, "Invalid FAQ id")


async def _specialty_of(db, oid: ObjectId) -> str | None:
    doc = await db.faqs.find_one({"_id": oid}, projection={"specialty": 1})
    return doc.get("specialty") if doc else None


@router.post("/approve/{faq_id}")
async def approve(faq_id: str):
    db = get_db()
    oid = _oid(faq_id)
    spec = await _specialty_of(db, oid)
    r = await db.faqs.update_one(
        {"_id": oid}, {"$set": {"approved": True, "rejected": False}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "FAQ not found")
    invalidate_cache(spec)
    return {"ok": True}


@router.post("/edit/{faq_id}")
async def edit(faq_id: str, body: FAQEdit):
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(400, "No fields to update")
    db = get_db()
    oid = _oid(faq_id)
    spec = await _specialty_of(db, oid)
    r = await db.faqs.update_one({"_id": oid}, {"$set": update})
    if r.matched_count == 0:
        raise HTTPException(404, "FAQ not found")
    invalidate_cache(spec)
    return {"ok": True}


@router.post("/reject/{faq_id}")
async def reject(faq_id: str):
    db = get_db()
    oid = _oid(faq_id)
    spec = await _specialty_of(db, oid)
    r = await db.faqs.update_one(
        {"_id": oid}, {"$set": {"approved": False, "rejected": True}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "FAQ not found")
    invalidate_cache(spec)
    return {"ok": True}


@router.get("/candidates/{specialty}")
async def candidates(specialty: str, limit: int = 100):
    db = get_db()
    cursor = (
        db.faqs.find(
            {"specialty": specialty, "approved": False, "rejected": {"$ne": True}}
        ).sort("count", -1).limit(limit)
    )
    items = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return items


@router.post("/refresh-index/{specialty}")
async def refresh(specialty: str):
    invalidate_cache(specialty)
    return {"ok": True, "invalidated": specialty}


@router.get("/stats/{specialty}")
async def stats(specialty: str):
    db = get_db()
    return {
        "approved": await db.faqs.count_documents(
            {"specialty": specialty, "approved": True}
        ),
        "pending": await db.faqs.count_documents(
            {"specialty": specialty, "approved": False, "rejected": {"$ne": True}}
        ),
        "rejected": await db.faqs.count_documents(
            {"specialty": specialty, "rejected": True}
        ),
        "auto_generated_pending": await db.faqs.count_documents(
            {"specialty": specialty, "approved": False,
             "rejected": {"$ne": True}, "auto_generated": True}
        ),
        "chat_turns": await db.chat_turns.count_documents(
            {"specialty": specialty}
        ),
    }


# -------------- auto-FAQ mining --------------


@router.get("/mining/status")
async def mining_status():
    from app.services.auto_faq import queue_status
    return await queue_status()


@router.post("/mining/run/{specialty}")
async def mining_run(specialty: str):
    from app.services.auto_faq import force_cluster
    return await force_cluster(specialty)


@router.get("/generator/stats")
async def generator_stats():
    from app.services.generator import stats
    return stats()

"""Admin endpoints: approve, edit, reject candidate FAQs."""
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.db import get_db

router = APIRouter()


class FAQEdit(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None


def _oid(faq_id: str) -> ObjectId:
    try:
        return ObjectId(faq_id)
    except Exception:
        raise HTTPException(400, "Invalid FAQ id")


@router.post("/approve/{faq_id}")
async def approve(faq_id: str):
    db = get_db()
    r = await db.faqs.update_one(
        {"_id": _oid(faq_id)},
        {"$set": {"approved": True, "rejected": False}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "FAQ not found")
    return {"ok": True}


@router.post("/edit/{faq_id}")
async def edit(faq_id: str, body: FAQEdit):
    update = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update:
        raise HTTPException(400, "No fields to update")
    db = get_db()
    r = await db.faqs.update_one({"_id": _oid(faq_id)}, {"$set": update})
    if r.matched_count == 0:
        raise HTTPException(404, "FAQ not found")
    return {"ok": True}


@router.post("/reject/{faq_id}")
async def reject(faq_id: str):
    db = get_db()
    r = await db.faqs.update_one(
        {"_id": _oid(faq_id)},
        {"$set": {"approved": False, "rejected": True}},
    )
    if r.matched_count == 0:
        raise HTTPException(404, "FAQ not found")
    return {"ok": True}


@router.get("/candidates/{specialty}")
async def candidates(specialty: str, limit: int = 100):
    """List FAQs that are awaiting clinician review."""
    db = get_db()
    cursor = (
        db.faqs.find({"specialty": specialty, "approved": False, "rejected": {"$ne": True}})
        .sort("count", -1)
        .limit(limit)
    )
    items = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(doc)
    return items

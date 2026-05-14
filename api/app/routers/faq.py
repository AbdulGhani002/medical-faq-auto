"""FAQ endpoints: list approved FAQs per specialty."""
from typing import List

from fastapi import APIRouter

from app.db import get_db
from app.models import FAQItem

router = APIRouter()


@router.get("/{specialty}", response_model=List[FAQItem])
async def list_faqs(specialty: str, limit: int = 50):
    db = get_db()
    cursor = (
        db.faqs.find({"specialty": specialty, "approved": True})
        .sort("count", -1)
        .limit(limit)
    )
    items: List[FAQItem] = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        items.append(FAQItem(**doc))
    return items

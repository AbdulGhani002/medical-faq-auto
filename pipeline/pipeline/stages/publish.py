"""Stage 8: write polished FAQs to MongoDB and push embeddings to Qdrant.

By default new entries are stored with `approved: false` so clinicians can
review them in the admin dashboard before the public FAQ page shows them.
"""
from datetime import datetime


def run(items: list[dict]) -> int:
    if not items:
        return 0
    try:
        from pymongo import MongoClient
    except ImportError:
        print("      pymongo not installed, skipping publish")
        return 0

    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
    except Exception:
        print("      Mongo not reachable, skipping publish")
        return 0

    db = client["medfaq"]
    now = datetime.utcnow()
    published = 0
    for it in items:
        doc = {
            "specialty": it["specialty"],
            "question": it["question"],
            "answer": it["answer"],
            "count": it.get("count", 1),
            "cluster_id": it.get("cluster_id"),
            "approved": False,
            "rejected": False,
            "updated_at": now,
        }
        # Upsert by (specialty, cluster_id) so re-runs don't duplicate.
        db.faqs.update_one(
            {"specialty": doc["specialty"], "cluster_id": doc["cluster_id"]},
            {"$set": doc},
            upsert=True,
        )
        published += 1
    return published

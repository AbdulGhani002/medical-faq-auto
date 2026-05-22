"""Stage 8: persist polished FAQ candidates.

We try MongoDB first. If Mongo isn't reachable, we fall back to writing a
JSONL file at ``data/faq_candidates.jsonl`` so the run is still useful in
a dev / demo environment.

By default new entries are stored with ``approved: false`` so clinicians
can review them in the admin dashboard before the public FAQ page shows
them.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


def _publish_mongo(items: list[dict]) -> int:
    try:
        from pymongo import MongoClient
    except ImportError:
        return -1
    try:
        client = MongoClient(
            "mongodb://localhost:27017", serverSelectionTimeoutMS=1500
        )
        client.admin.command("ping")
    except Exception:
        return -1

    db = client["medfaq"]
    now = datetime.utcnow()
    published = 0
    for it in items:
        doc = {
            "specialty": it["specialty"],
            "question": it["question"],
            "answer": it["answer"],
            "count": it.get("count", 1),
            "cluster_id": str(it.get("cluster_id")),
            "approved": False,
            "rejected": False,
            "updated_at": now,
        }
        db.faqs.update_one(
            {"specialty": doc["specialty"],
             "cluster_id": doc["cluster_id"]},
            {"$set": doc},
            upsert=True,
        )
        published += 1
    return published


def _publish_jsonl(items: list[dict]) -> int:
    repo_root = Path(__file__).resolve().parents[3]
    out_path = repo_root / "data" / "faq_candidates.jsonl"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.utcnow().isoformat()
    with out_path.open("w", encoding="utf-8") as f:
        for i, it in enumerate(items):
            doc = {
                "id": f"cand-{it['specialty']}-{i:04d}",
                "specialty": it["specialty"],
                "question": it["question"],
                "answer": it["answer"],
                "count": it.get("count", 1),
                "cluster_id": str(it.get("cluster_id")),
                "members": it.get("member_questions", []),
                "approved": False,
                "rejected": False,
                "created_at": now,
            }
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    print(f"      wrote {out_path.relative_to(repo_root).as_posix()}")
    return len(items)


def run(items: list[dict]) -> int:
    if not items:
        return 0
    n = _publish_mongo(items)
    if n >= 0:
        return n
    return _publish_jsonl(items)

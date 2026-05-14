"""Load seed FAQs from data/seed_faqs.json into MongoDB.

Run this once after `docker compose up -d`. It populates the public
FAQ page with the 9 starter entries so the demo is not empty.

Usage:
    python api/seed.py
    python api/seed.py --reset    # wipe faqs collection first
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--reset", action="store_true",
                   help="Drop the faqs collection before inserting.")
    p.add_argument("--uri", default="mongodb://localhost:27017",
                   help="MongoDB connection URI.")
    p.add_argument("--db", default="medfaq", help="Database name.")
    args = p.parse_args()

    repo_root = Path(__file__).parent.parent
    seed_path = repo_root / "data" / "seed_faqs.json"
    if not seed_path.exists():
        print(f"Seed file not found: {seed_path}")
        return 1

    with seed_path.open("r", encoding="utf-8") as f:
        faqs = json.load(f)

    try:
        client = MongoClient(args.uri, serverSelectionTimeoutMS=3000)
        client.admin.command("ping")
    except ServerSelectionTimeoutError:
        print(f"Cannot reach MongoDB at {args.uri}.")
        print("Did you run `docker compose up -d`?")
        return 2

    db = client[args.db]

    if args.reset:
        n = db.faqs.delete_many({}).deleted_count
        print(f"Reset: dropped {n} existing FAQs.")

    now = datetime.utcnow()
    upserts = 0
    for i, faq in enumerate(faqs):
        doc = {
            "specialty": faq["specialty"],
            "question": faq["question"],
            "answer": faq["answer"],
            "count": faq.get("count", 1),
            "approved": faq.get("approved", True),
            "rejected": False,
            "cluster_id": f"seed-{i}",
            "updated_at": now,
        }
        db.faqs.update_one(
            {"specialty": doc["specialty"], "cluster_id": doc["cluster_id"]},
            {"$set": doc},
            upsert=True,
        )
        upserts += 1

    counts_by_specialty = {}
    for spec in {f["specialty"] for f in faqs}:
        counts_by_specialty[spec] = db.faqs.count_documents(
            {"specialty": spec, "approved": True}
        )

    print(f"Seeded {upserts} FAQs into {args.db}.faqs")
    for spec, n in sorted(counts_by_specialty.items()):
        print(f"  {spec}: {n} approved")
    return 0


if __name__ == "__main__":
    sys.exit(main())

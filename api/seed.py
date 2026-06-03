"""Load curated FAQs from data/faqs_*.json into MongoDB.

There are three per-specialty knowledge files (radiology, physiotherapy,
cardiovascular) with about 30 entries each. Run this once after
`docker compose up -d`. Re-run with --reset to wipe and reload.
"""
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

SOURCES = [
    "faqs_radiology.json",
    "faqs_physiotherapy.json",
    "faqs_cardiovascular.json",
]


def _load_all(repo_root: Path) -> list[dict]:
    items: list[dict] = []

    # 1. Prefer JSONL if present (one record per line).
    jsonl_path = repo_root / "data" / "faqs.jsonl"
    if jsonl_path.exists():
        with jsonl_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                items.append(json.loads(line))
        if items:
            print(f"  loaded {len(items):3d} from faqs.jsonl")
            return items

    # 2. Fall back to per-specialty JSON files.
    for name in SOURCES:
        path = repo_root / "data" / name
        if not path.exists():
            print(f"  skip {name} (missing)")
            continue
        with path.open("r", encoding="utf-8") as f:
            chunk = json.load(f)
        items.extend(chunk)
        print(f"  loaded {len(chunk):3d} from {name}")

    return items


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--reset", action="store_true",
                   help="Drop the faqs collection before inserting.")
    p.add_argument("--uri", default="mongodb://localhost:27017")
    p.add_argument("--db", default="medfaq")
    args = p.parse_args()

    repo_root = Path(__file__).parent.parent
    faqs = _load_all(repo_root)
    if not faqs:
        print("No FAQ data files found in data/.")
        return 1

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
        print(f"reset: dropped {n} existing FAQs.")

    now = datetime.utcnow()
    for i, faq in enumerate(faqs):
        doc = {
            "specialty": faq["specialty"],
            "question": faq["question"],
            "answer": faq["answer"],
            "count": faq.get("count", 0),
            "approved": faq.get("approved", True),
            "rejected": False,
            "cluster_id": f"seed-{faq['specialty']}-{i}",
            "updated_at": now,
        }
        db.faqs.update_one(
            {"specialty": doc["specialty"], "cluster_id": doc["cluster_id"]},
            {"$set": doc},
            upsert=True,
        )

    print(f"\nSeeded {len(faqs)} FAQs into {args.db}.faqs")
    for spec in sorted({f["specialty"] for f in faqs}):
        n = db.faqs.count_documents({"specialty": spec, "approved": True})
        print(f"  {spec:18s}: {n} approved")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Stage 1: ingest chat sessions from JSONL (fallback to Mongo).

Returns a list of session dicts:
    {"session_id": str, "specialty": str, "turns": [{"role", "text"}]}
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Optional


def _from_jsonl(path: Path, specialty: Optional[str]) -> list[dict]:
    sessions: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if specialty and rec.get("specialty") != specialty:
                continue
            sessions.append(rec)
    return sessions


def _from_mongo(specialty: Optional[str]) -> list[dict]:
    try:
        from pymongo import MongoClient
    except ImportError:
        return []
    try:
        client = MongoClient(
            "mongodb://localhost:27017", serverSelectionTimeoutMS=1500
        )
        client.admin.command("ping")
    except Exception:
        return []

    db = client["medfaq"]
    query: dict = {}
    if specialty:
        query["specialty"] = specialty
    sessions: dict[str, dict] = defaultdict(
        lambda: {"session_id": "", "specialty": "", "turns": []}
    )
    for turn in db.chat_turns.find(query).sort("timestamp", 1):
        sid = turn["session_id"]
        s = sessions[sid]
        s["session_id"] = sid
        s["specialty"] = turn["specialty"]
        s["turns"].append({"role": turn["role"], "text": turn["text"]})
    return list(sessions.values())


def run(specialty: Optional[str] = None) -> list[dict]:
    """Prefer ``data/chat_logs.jsonl`` if present, otherwise pull from Mongo."""
    repo_root = Path(__file__).resolve().parents[3]
    jsonl = repo_root / "data" / "chat_logs.jsonl"
    if jsonl.is_file():
        return _from_jsonl(jsonl, specialty)
    return _from_mongo(specialty)

"""Stage 1: pull chat sessions from MongoDB.

Returns a list of session dicts:
    {"session_id": str, "specialty": str, "turns": [{"role", "text", "timestamp"}]}
"""
from collections import defaultdict
from typing import Optional


def run(specialty: Optional[str] = None) -> list[dict]:
    """Pull sessions from Mongo. Returns [] if Mongo is unreachable."""
    try:
        from pymongo import MongoClient
    except ImportError:
        print("      pymongo not installed, returning empty list")
        return []

    try:
        client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
        client.admin.command("ping")
    except Exception:
        print("      Mongo not reachable, returning empty list")
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
        s["turns"].append(
            {
                "role": turn["role"],
                "text": turn["text"],
                "timestamp": turn.get("timestamp"),
            }
        )

    return list(sessions.values())

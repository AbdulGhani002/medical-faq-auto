"""Persist chat turns to MongoDB."""
from datetime import datetime

from app.db import get_db


async def log_turn(
    session_id: str, specialty: str, role: str, text: str
) -> None:
    db = get_db()
    await db.chat_turns.insert_one(
        {
            "session_id": session_id,
            "specialty": specialty,
            "role": role,
            "text": text,
            "timestamp": datetime.utcnow(),
        }
    )

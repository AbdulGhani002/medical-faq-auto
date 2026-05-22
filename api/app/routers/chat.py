"""Chat endpoint: take user message, log it, return a retrieval-based answer."""
from fastapi import APIRouter

from app.db import get_db
from app.models import ChatRequest, ChatResponse
from app.services.chat_logger import log_turn
from app.services.phi_scrub import scrub
from app.services.retrieval import reset_state, retrieve_answer, state_snapshot

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    clean_text = scrub(req.text)
    await log_turn(req.session_id, req.specialty, "user", clean_text)
    result = await retrieve_answer(req.specialty, clean_text, req.session_id)
    await log_turn(req.session_id, req.specialty, "bot", result["answer"])
    return ChatResponse(**result)


@router.post("/reset/{session_id}")
async def reset(session_id: str):
    reset_state(session_id)
    db = get_db()
    await db.chat_turns.delete_many({"session_id": session_id})
    return {"ok": True, "session_id": session_id}


@router.get("/state/{session_id}")
async def state(session_id: str):
    return {"session_id": session_id, "state": state_snapshot(session_id)}


@router.get("/history/{session_id}")
async def history(session_id: str, limit: int = 50):
    db = get_db()
    cur = (
        db.chat_turns.find({"session_id": session_id})
        .sort("timestamp", 1)
        .limit(limit)
    )
    out = []
    async for t in cur:
        out.append({
            "role": t.get("role"),
            "text": t.get("text"),
            "timestamp": str(t.get("timestamp")),
        })
    return {"session_id": session_id, "turns": out}

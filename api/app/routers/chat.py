"""Chat endpoint: take user message, log it, return a retrieval-based answer."""
from fastapi import APIRouter

from app.models import ChatRequest, ChatResponse
from app.services.chat_logger import log_turn
from app.services.phi_scrub import scrub
from app.services.retrieval import retrieve_answer

router = APIRouter()


@router.post("", response_model=ChatResponse)
async def chat(req: ChatRequest):
    clean_text = scrub(req.text)
    await log_turn(req.session_id, req.specialty, "user", clean_text)

    answer, faq_id, confidence = await retrieve_answer(req.specialty, clean_text)
    await log_turn(req.session_id, req.specialty, "bot", answer)

    return ChatResponse(
        answer=answer,
        matched_faq_id=faq_id,
        confidence=confidence,
    )

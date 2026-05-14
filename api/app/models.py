"""Pydantic v2 models exchanged by the API."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    specialty: str
    text: str


class ChatResponse(BaseModel):
    answer: str
    matched_faq_id: Optional[str] = None
    confidence: float


class FAQItem(BaseModel):
    id: str
    specialty: str
    question: str
    answer: str
    count: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ChatTurn(BaseModel):
    session_id: str
    specialty: str
    role: str  # "user" or "bot"
    text: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

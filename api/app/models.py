"""Pydantic v2 models exchanged by the API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str
    specialty: str
    text: str


class Alternative(BaseModel):
    id: str
    question: str
    score: float


class SpellCorrection(BaseModel):
    original: str
    fixed: str


class ScoreBreakdown(BaseModel):
    tfidf_word: float
    tfidf_char: float
    bm25: float
    blended: float
    matched_question: str


class ChatResponse(BaseModel):
    answer: str
    matched_faq_id: Optional[str] = None
    confidence: float
    alternatives: List[Alternative] = []
    bucket: str = "none"
    intent: str = "question"
    spell_corrections: List[SpellCorrection] = []
    expanded_query: str = ""
    added_terms: List[str] = []
    score_breakdown: Optional[ScoreBreakdown] = None


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


class ChatReaction(BaseModel):
    matched_faq_id: Optional[str] = None
    helpful: bool
    note: Optional[str] = None

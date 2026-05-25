"""Pydantic v2 models exchanged by the API."""
from datetime import datetime
from typing import Any, List, Optional

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
    lsa: float = 0.0
    embed: float = 0.0
    blended: float
    matched_question: str


class HighlightSegment(BaseModel):
    text: str
    hl: bool


class CorefEdit(BaseModel):
    original: str
    replacement: str


class Entity(BaseModel):
    text: str
    label: str
    start: int
    end: int


class Keyword(BaseModel):
    text: str
    score: float


class Negation(BaseModel):
    cue: str
    scope: List[str]


class Sentiment(BaseModel):
    compound: float
    label: str
    positives: List[str] = []
    negatives: List[str] = []


class TriageInfo(BaseModel):
    level: int = 0
    cues: List[str] = []


class IntentScore(BaseModel):
    label: str
    confidence: float
    top3: List[Any] = []


class POSToken(BaseModel):
    text: str
    tag: str


class Slots(BaseModel):
    body_part: Optional[str] = None
    symptom: Optional[str] = None
    condition: Optional[str] = None
    drug: Optional[str] = None
    procedure: Optional[str] = None
    person: Optional[str] = None
    duration: Optional[str] = None
    frequency: Optional[str] = None
    age: Optional[int] = None
    entities: List[Entity] = []


class Chunk(BaseModel):
    text: str
    start_tok: int
    end_tok: int


class Chunks(BaseModel):
    noun_phrases: List[Chunk] = []
    verb_phrases: List[Chunk] = []


class Triple(BaseModel):
    subject: str
    predicate: str
    object: str
    negated: bool = False
    sentence: str = ""


class NLPAnalysis(BaseModel):
    raw_text: str
    tokens: List[str]
    lemmas: List[str]
    pos: List[POSToken]
    pos_hmm: List[POSToken] = []
    intent: IntentScore
    question_type: str
    sentiment: Sentiment
    triage: TriageInfo
    negations: List[Negation]
    entities: List[Entity]
    slots: Slots
    keywords: List[Keyword]
    chunks: Chunks = Field(default_factory=Chunks)
    triples: List[Triple] = []
    lm_perplexity: Optional[float] = None


class RomanUrduEdit(BaseModel):
    original: str
    translated: str
    start: int
    end: int


class DialogMeta(BaseModel):
    opener: str = ""
    triage_level: int = 0
    triage_cues: List[str] = []
    banner: Optional[str] = None
    clarification: Optional[str] = None
    coref: List[CorefEdit] = []
    roman_urdu: List[RomanUrduEdit] = []
    disambiguation: Optional[List[Alternative]] = None
    active_topic: Optional[str] = None
    chitchat: bool = False
    ltr_used: bool = False


class GenerationInfo(BaseModel):
    mode: str
    text: Optional[str] = None
    generated_text: Optional[str] = None
    retrieved_text: Optional[str] = None
    grounding_similarity: Optional[float] = None
    overlap: Optional[float] = None
    reason: Optional[str] = None
    model: Any = None


class ChatResponse(BaseModel):
    answer: str
    matched_faq_id: Optional[str] = None
    matched_question: Optional[str] = None
    confidence: float
    alternatives: List[Alternative] = []
    bucket: str = "none"
    intent: str = "question"
    spell_corrections: List[SpellCorrection] = []
    expanded_query: str = ""
    added_terms: List[str] = []
    score_breakdown: Optional[ScoreBreakdown] = None
    highlighted: Optional[List[HighlightSegment]] = None
    nlp: Optional[NLPAnalysis] = None
    dialog: DialogMeta = Field(default_factory=DialogMeta)
    summary: Optional[str] = None
    generation: Optional[GenerationInfo] = None


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


class NLPAnalyzeRequest(BaseModel):
    text: str

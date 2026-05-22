"""Classical NLP pipeline.

Token level: normalize -> expand synonyms -> lemmatize -> spell-correct.
Doc level:   word TF-IDF + char TF-IDF + BM25 + LSA topic -> blend.
Query level: NB intent + POS + NER + negation + sentiment + triage +
             question-type + slot extraction + coref + dialog manager.
Result level: highlight matched spans + extractive summary + suggestions.

No neural model, no LLM, no AI API.
"""
from .context import augment_with_context, is_followup
from .coref import resolve as resolve_pronouns
from .embeddings import CorpusEmbeddings
from .mmr import mmr_select
from .roman_urdu import contains_roman_urdu, expand as expand_roman_urdu
from .dialog import (
    build_opener, needs_clarification, needs_disambiguation, update_state,
)
from .feedback import expand_with_feedback, jaccard, top_terms_from_docs
from .highlight import highlight_text, overlap_score
from .indexer import HybridIndex
from .intent import canned, classify as classify_rule_intent
from .keywords import extract as extract_keywords
from .keywords import keywords as keyword_list
from .lemmatize import canonical, lemmatize
from .nb_intent import classify as classify_nb_intent
from .nb_intent import is_chitchat
from .negation import detect_negations, is_negated, negation_flags
from .ner import entity_labels, extract_entities, primary_topic
from .normalize import canonical_tokens, expand_query, tokenize
from .pos import nouns, tag, verbs
from .qtype import classify as classify_question_type
from .scoring import best_match, rank_fusion, to_confidence
from .sentiment import analyse as analyse_sentiment
from .sentiment import is_distressed
from .slots import extract_slots, merge as merge_slots
from .spell import Corrector
from .stem import stem
from .summarize import multi_doc_summary, summarise
from .topic import LSATopicModel
from .triage import assess as assess_triage
from .triage import banner as triage_banner

__all__ = [
    "HybridIndex", "Corrector", "LSATopicModel", "CorpusEmbeddings",
    "augment_with_context", "best_match", "canned",
    "canonical", "canonical_tokens",
    "classify_nb_intent", "classify_question_type", "classify_rule_intent",
    "contains_roman_urdu", "expand_roman_urdu",
    "expand_query", "expand_with_feedback",
    "extract_entities", "entity_labels", "extract_keywords",
    "extract_slots", "merge_slots", "primary_topic", "keyword_list",
    "highlight_text", "overlap_score",
    "is_chitchat", "is_distressed", "is_followup", "is_negated",
    "jaccard", "lemmatize", "mmr_select",
    "multi_doc_summary", "summarise",
    "nouns", "verbs", "tag",
    "negation_flags", "detect_negations",
    "analyse_sentiment", "assess_triage", "triage_banner",
    "build_opener", "needs_clarification", "needs_disambiguation",
    "update_state", "resolve_pronouns",
    "rank_fusion", "stem", "to_confidence", "tokenize", "top_terms_from_docs",
]

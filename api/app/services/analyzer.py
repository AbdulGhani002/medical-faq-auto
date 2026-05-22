"""Run the full NLP analysis on a user utterance.

Returns a single dict consumed by the retrieval and dialog layers.
No LLM, no neural model. Everything is deterministic classical NLP.
"""
from __future__ import annotations

from app.nlp import (
    analyse_sentiment, assess_triage, classify_nb_intent,
    classify_question_type, detect_negations, extract_entities,
    extract_keywords, extract_slots, lemmatize, tag,
)
from app.nlp.chunker import chunk
from app.nlp.hmm_pos import hmm_tag
from app.nlp.kg import extract_triples
from app.nlp.lm import perplexity
from app.nlp.normalize import tokenize


def analyse(text: str) -> dict:
    text = text or ""
    toks = tokenize(text, drop_stopwords=False)
    tagged_lex = tag(toks)
    try:
        tagged_hmm = hmm_tag(toks)
    except Exception:
        tagged_hmm = tagged_lex

    intent = classify_nb_intent(text)
    qtype = classify_question_type(text)
    sentiment = analyse_sentiment(text)
    triage = assess_triage(text)
    negations = detect_negations(text)
    entities = extract_entities(text)
    slots = extract_slots(text)
    kws = extract_keywords(text, top_k=6)
    lemmas = [lemmatize(t) for t in toks]
    chunks = chunk(tagged_hmm) if tagged_hmm else {"noun_phrases": [], "verb_phrases": []}
    try:
        triples = extract_triples(text)
    except Exception:
        triples = []
    try:
        lm_perplexity = round(perplexity(text), 3)
    except Exception:
        lm_perplexity = None

    return {
        "raw_text": text,
        "tokens": toks,
        "lemmas": lemmas,
        "pos": [{"text": w, "tag": t} for w, t in tagged_lex],
        "pos_hmm": [{"text": w, "tag": t} for w, t in tagged_hmm],
        "intent": intent,
        "question_type": qtype,
        "sentiment": sentiment,
        "triage": triage,
        "negations": negations,
        "entities": entities,
        "slots": slots,
        "keywords": [{"text": k, "score": s} for k, s in kws],
        "chunks": chunks,
        "triples": triples,
        "lm_perplexity": lm_perplexity,
    }

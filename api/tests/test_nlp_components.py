"""Unit tests for the in-house NLP modules.

Each module gets a focused set of assertions covering both happy paths
and the trickier edge cases (negation flipping sentiment, multi-word
NER, Damerau transposition, etc.). Run with:

    cd api && pytest -q
"""
from __future__ import annotations

import pytest

from app.nlp.stem import stem
from app.nlp.lemmatize import lemmatize, canonical
from app.nlp.pos import tag_token, tag
from app.nlp.ner import extract_entities, primary_topic
from app.nlp.negation import detect_negations, is_negated, negated_tokens
from app.nlp.sentiment import analyse, is_distressed
from app.nlp.triage import assess
from app.nlp.qtype import classify as classify_qtype
from app.nlp.nb_intent import classify as classify_intent
from app.nlp.keywords import keywords
from app.nlp.coref import resolve
from app.nlp.roman_urdu import expand as expand_ru, contains_roman_urdu
from app.nlp.spell import Corrector, damerau_levenshtein
from app.nlp.mmr import mmr_select
from app.nlp.embeddings import CorpusEmbeddings


# ----- stemmer ---------------------------------------------------------------


@pytest.mark.parametrize("word,expected_prefix", [
    ("running", "run"),
    ("relational", "rel"),
    ("flies", "fli"),
    ("ponies", "poni"),
])
def test_stem_reduces_suffix(word, expected_prefix):
    assert stem(word).startswith(expected_prefix)


def test_stem_handles_short_words():
    assert stem("hi") == "hi"
    assert stem("be") == "be"


# ----- lemmatiser ------------------------------------------------------------


def test_lemmatize_irregular_verbs():
    assert lemmatize("went") == "go"
    assert lemmatize("ran") == "run"
    assert lemmatize("better") == "good"


def test_lemmatize_plurals():
    assert lemmatize("kidneys") == "kidney"
    assert lemmatize("children") == "child"


def test_canonical_falls_back_to_stem():
    assert canonical("running") == "run"
    # Unknown word stays the same after lemmatization but stem strips.
    assert canonical("medications") in {"medic", "medication"}


# ----- POS tagger ------------------------------------------------------------


def test_pos_tagger_known_words():
    assert tag_token("the") == "DT"
    assert tag_token("not") == "RB"
    assert tag_token("running") == "VB"
    assert tag_token("123") == "CD"


def test_pos_tagger_sentence_returns_pairs():
    pairs = tag(["the", "pain", "is", "sharp"])
    assert [t for _, t in pairs] == ["DT", "NN", "VB", "JJ"]


# ----- NER -------------------------------------------------------------------


def test_ner_finds_body_and_symptom():
    ents = extract_entities("my knee hurts after running")
    labels = sorted(e["label"] for e in ents)
    assert "BODY" in labels
    assert any(e["text"].lower() == "knee" for e in ents)


def test_ner_phrase_match_chest_pain():
    ents = extract_entities("I have severe chest pain")
    # "chest pain" must be matched as a single SYMPTOM phrase.
    assert any(
        e["label"] == "SYMPTOM" and e["text"].lower() == "chest pain"
        for e in ents
    )


def test_primary_topic_priority():
    ents = extract_entities("my knee hurts and I have angina")
    # CONDITION beats BODY by priority.
    assert primary_topic(ents) == "angina"


# ----- negation --------------------------------------------------------------


def test_negation_detects_cue_and_scope():
    out = detect_negations("I do not have any chest pain")
    assert out, "expected at least one negation"
    scope = out[0]["scope"]
    assert "chest" in " ".join(scope) or "pain" in " ".join(scope)


def test_negation_blanket_is_negated_flag():
    assert is_negated("no fever today")
    assert not is_negated("I have a fever today")


def test_negated_tokens_excludes_unnegated():
    toks = negated_tokens("no chest pain but I feel tired")
    assert "chest" in toks
    # 'tired' is after 'but' which closes the scope.
    assert "tired" not in toks


# ----- sentiment -------------------------------------------------------------


def test_sentiment_positive():
    a = analyse("thank you so much, I feel great")
    assert a["compound"] > 0.3
    assert a["label"] == "positive"


def test_sentiment_negative():
    a = analyse("I am really worried about my heart")
    assert a["compound"] < 0.0
    assert a["label"] == "negative"


def test_sentiment_negation_flips_polarity():
    a_pos = analyse("I feel good")
    a_neg = analyse("I do not feel good")
    assert a_pos["compound"] > 0
    assert a_neg["compound"] < a_pos["compound"]


def test_is_distressed():
    assert is_distressed("I am terrified and scared")
    assert not is_distressed("everything is fine")


# ----- triage ----------------------------------------------------------------


def test_triage_emergency():
    r = assess("I have crushing chest pain")
    assert r["level"] == 3
    assert any("crushing chest" in c for c in r["cues"])


def test_triage_moderate():
    r = assess("I have shortness of breath")
    assert r["level"] >= 2


def test_triage_no_cue():
    r = assess("when should I take aspirin")
    assert r["level"] == 0


# ----- question type ---------------------------------------------------------


@pytest.mark.parametrize("q,expected", [
    ("what is angina", "what"),
    ("why do I feel dizzy", "why"),
    ("how does an MRI work", "how"),
    ("do I need to fast", "yes_no"),
    ("can I drink coffee", "yes_no"),
    ("Should I get an MRI or CT for back pain?", "choice"),
])
def test_question_type(q, expected):
    assert classify_qtype(q) == expected


# ----- intent (NB) -----------------------------------------------------------


@pytest.mark.parametrize("text,expected", [
    ("hi there", "greeting"),
    ("thanks a lot", "thanks"),
    ("this is useless", "frustration"),
    ("what is angina", "ask_definition"),
    ("do i need to fast before my mri", "ask_preparation"),
])
def test_intent_classifier_high_confidence(text, expected):
    r = classify_intent(text)
    assert r["label"] == expected
    assert r["confidence"] > 0.15


# ----- keywords --------------------------------------------------------------


def test_keywords_picks_content_words():
    kws = keywords("my chest hurts after eating spicy food")
    assert "chest" in kws or "hurts" in kws or "spicy" in kws


# ----- coreference -----------------------------------------------------------


def test_coref_substitutes_it():
    out, edits = resolve("how do I treat it", "angina")
    assert "angina" in out
    assert edits and edits[0]["original"].lower() == "it"


def test_coref_no_topic_returns_input():
    out, edits = resolve("how do I treat it", None)
    assert out == "how do I treat it"
    assert edits == []


# ----- Roman-Urdu ------------------------------------------------------------


def test_roman_urdu_detected_and_expanded():
    assert contains_roman_urdu("sar mein dard ho raha hai")
    expanded, edits = expand_ru("sar mein dard ho raha hai")
    assert "head" in expanded
    assert "pain" in expanded
    assert any(e["original"] == "dard" for e in edits)


def test_roman_urdu_skip_for_pure_english():
    assert not contains_roman_urdu("my chest hurts a lot")


# ----- spell correction ------------------------------------------------------


def test_damerau_levenshtein_basics():
    assert damerau_levenshtein("kitten", "sitting") == 3
    # Transposition counted as one edit (Damerau).
    assert damerau_levenshtein("ab", "ba") == 1


def test_corrector_fixes_typo():
    vocab = ["chest", "pain", "heart", "attack", "stroke"]
    c = Corrector(vocab * 3)
    fixed, fixes = c.correct(["chesst", "panin"])
    assert "chest" in fixed
    assert "pain" in fixed
    assert len(fixes) >= 1


# ----- MMR -------------------------------------------------------------------


def test_mmr_picks_diverse_candidates():
    import numpy as np
    rel = np.array([0.9, 0.85, 0.5, 0.4])
    sim = np.array([
        [1.0, 0.95, 0.1, 0.1],
        [0.95, 1.0, 0.1, 0.1],
        [0.1, 0.1, 1.0, 0.2],
        [0.1, 0.1, 0.2, 1.0],
    ])
    chosen = mmr_select([0, 1, 2, 3], rel, sim, k=2, lam=0.5)
    # The top two are 0 and 1 by relevance, but they are near duplicates.
    # MMR with lam=0.5 should reject one of them in favour of 2 or 3.
    assert 0 in chosen
    assert chosen[1] in {2, 3}


# ----- PPMI embeddings -------------------------------------------------------


def test_embeddings_train_and_score(faq_corpus):
    docs = [f["question"] + " " + f["answer"] for f in faq_corpus]
    e = CorpusEmbeddings(docs, dim=8, window=4, min_count=1)
    assert len(e.vocab) > 5
    mat = e.doc_matrix(docs)
    sims = e.similarity("blood pressure medicine timing", mat)
    # The BP-medicine FAQ is index 1 (zero-based) in the fixture.
    assert sims.argmax() == 1

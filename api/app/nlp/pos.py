"""Tiny lexicon + heuristic part-of-speech tagger.

Tags we emit (Penn-style condensed):
  NN  - noun (default)
  VB  - verb (any form)
  JJ  - adjective
  RB  - adverb
  DT  - determiner
  IN  - preposition or subordinating conjunction
  PRP - pronoun
  WH  - WH-word (what / why / how / ...)
  CC  - coordinating conjunction
  MD  - modal verb
  CD  - cardinal number
  UH  - interjection

This is intentionally tiny (under 200 LoC). Good enough to power
slot-filling, question-type classification, and negation scoping.
"""
from __future__ import annotations

import re

_LEXICON: dict[str, str] = {}

_DT = {"a", "an", "the", "this", "that", "these", "those", "my",
       "your", "his", "her", "its", "our", "their", "some", "any",
       "every", "each", "no", "another"}
_PRP = {"i", "you", "he", "she", "it", "we", "they", "me", "him",
        "her", "us", "them", "myself", "yourself", "himself", "herself",
        "ourselves", "themselves"}
_IN = {"in", "on", "at", "of", "for", "with", "by", "from", "to",
       "into", "onto", "after", "before", "during", "under", "over",
       "between", "around", "near", "through", "without", "within",
       "about", "than", "while", "since", "until", "because", "if",
       "unless", "though", "although", "as"}
_CC = {"and", "or", "but", "nor", "so", "yet"}
_MD = {"can", "could", "will", "would", "shall", "should", "may",
       "might", "must", "ought"}
_WH = {"what", "why", "how", "when", "where", "who", "which",
       "whom", "whose"}
_UH = {"hi", "hello", "hey", "yo", "oh", "ah", "wow", "ouch",
       "ok", "okay", "yes", "no", "yeah", "nope", "thanks", "thank"}

# A small open-class lexicon for the common medical / chatbot domain.
_JJ = {"good", "bad", "high", "low", "safe", "unsafe", "normal",
       "abnormal", "severe", "mild", "moderate", "sharp", "dull",
       "constant", "intermittent", "sudden", "chronic", "acute",
       "tired", "sore", "stiff", "swollen", "dizzy", "weak",
       "painful", "comfortable", "uncomfortable", "regular",
       "irregular", "fast", "slow", "early", "late", "young",
       "old", "new", "able", "unable", "safe", "necessary",
       "dangerous", "important", "urgent", "right", "wrong",
       "left", "right", "okay", "fine"}
_VB = {"is", "are", "was", "were", "be", "been", "being", "am",
       "have", "has", "had", "do", "does", "did", "feel", "felt",
       "feeling", "take", "took", "taking", "taken", "go", "went",
       "gone", "going", "come", "came", "coming", "see", "saw",
       "seen", "want", "wanted", "wanting", "need", "needed",
       "needing", "tell", "told", "telling", "ask", "asked",
       "asking", "give", "gave", "given", "giving", "make", "made",
       "making", "happen", "happens", "happened", "occur", "occurs",
       "occurred", "stop", "stopped", "stopping", "start", "started",
       "starting", "help", "helped", "helping", "exercise",
       "exercising", "eat", "ate", "eating", "drink", "drank",
       "drinking", "sleep", "slept", "sleeping", "feel", "feels",
       "felt", "treat", "treated", "treating", "cure", "cured",
       "curing", "diagnose", "diagnosed", "diagnosing", "hurt",
       "hurts", "hurting", "ache", "aches", "aching", "swell",
       "swelled", "swelling", "bleed", "bled", "bleeding"}
_RB = {"not", "n't", "never", "always", "often", "sometimes",
       "usually", "rarely", "very", "really", "quite", "too",
       "also", "only", "even", "just", "well", "badly", "fast",
       "slowly", "soon", "later", "earlier", "still", "yet",
       "already", "today", "yesterday", "tomorrow", "now", "then"}

for w in _DT: _LEXICON[w] = "DT"
for w in _PRP: _LEXICON[w] = "PRP"
for w in _IN: _LEXICON[w] = "IN"
for w in _CC: _LEXICON[w] = "CC"
for w in _MD: _LEXICON[w] = "MD"
for w in _WH: _LEXICON[w] = "WH"
for w in _UH: _LEXICON[w] = "UH"
for w in _JJ: _LEXICON[w] = "JJ"
for w in _VB: _LEXICON[w] = "VB"
for w in _RB: _LEXICON[w] = "RB"


_NUM_RE = re.compile(r"^\d+(?:\.\d+)?$")


def tag_token(token: str, prev_tag: str | None = None) -> str:
    """Return the POS tag for one lowercase token."""
    t = (token or "").lower()
    if not t:
        return "NN"
    if _NUM_RE.match(t):
        return "CD"
    if t in _LEXICON:
        return _LEXICON[t]
    # Suffix heuristics.
    if t.endswith("ly") and len(t) > 3:
        return "RB"
    if t.endswith(("ous", "ive", "able", "ible", "ful", "less",
                   "ical", "ish", "ant", "ent")):
        return "JJ"
    if t.endswith("ing") and len(t) > 4:
        return "VB"
    if t.endswith("ed") and len(t) > 3:
        return "VB"
    if t.endswith("tion") or t.endswith("ness") or t.endswith("ment"):
        return "NN"
    if t.endswith("s") and len(t) > 3 and not t.endswith("ss"):
        # Could be plural noun or 3rd-person verb. Use prev tag context.
        if prev_tag in ("PRP", "DT"):
            return "NN"
        return "NN"  # Default to noun. Good enough for IR.
    # Default: noun.
    return "NN"


def tag(tokens: list[str]) -> list[tuple[str, str]]:
    """Tag a list of lowercase tokens, returning (token, tag) pairs."""
    out: list[tuple[str, str]] = []
    prev: str | None = None
    for tok in tokens:
        tg = tag_token(tok, prev)
        out.append((tok, tg))
        prev = tg
    return out


def nouns(tagged: list[tuple[str, str]]) -> list[str]:
    return [w for w, t in tagged if t == "NN"]


def verbs(tagged: list[tuple[str, str]]) -> list[str]:
    return [w for w, t in tagged if t == "VB"]

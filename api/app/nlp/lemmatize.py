"""Rule-based lemmatiser that handles common English morphology.

We try irregular forms first (dictionary), then heuristic rules for plurals,
verb tenses, and comparatives. If nothing fires, we fall back to the Porter
stemmer to at least canonicalise the token. No model, no LLM.
"""
from __future__ import annotations

from .stem import stem as porter_stem

# Irregular noun plurals + common medical exceptions.
_IRREGULAR_NOUNS = {
    "feet": "foot", "teeth": "tooth", "men": "man", "women": "woman",
    "children": "child", "people": "person", "mice": "mouse",
    "geese": "goose", "lice": "louse", "feet": "foot",
    # Greek/Latin medical plurals
    "vertebrae": "vertebra", "bacteria": "bacterium", "criteria": "criterion",
    "phenomena": "phenomenon", "diagnoses": "diagnosis",
    "prognoses": "prognosis", "stenoses": "stenosis", "fungi": "fungus",
    "nuclei": "nucleus", "stimuli": "stimulus", "indices": "index",
    "matrices": "matrix", "appendices": "appendix", "vertices": "vertex",
    "analyses": "analysis", "axes": "axis", "crises": "crisis",
    "theses": "thesis", "neuroses": "neurosis",
}

_IRREGULAR_VERBS = {
    "is": "be", "are": "be", "was": "be", "were": "be", "been": "be",
    "being": "be", "am": "be",
    "has": "have", "had": "have", "having": "have",
    "does": "do", "did": "do", "done": "do", "doing": "do",
    "went": "go", "gone": "go", "going": "go",
    "took": "take", "taken": "take", "taking": "take",
    "ran": "run", "running": "run",
    "ate": "eat", "eaten": "eat", "eating": "eat",
    "saw": "see", "seen": "see", "seeing": "see",
    "felt": "feel", "feeling": "feel",
    "thought": "think", "thinking": "think",
    "got": "get", "gotten": "get", "getting": "get",
    "made": "make", "making": "make",
    "broken": "break", "broke": "break", "breaking": "break",
    "felt": "feel", "fell": "fall", "fallen": "fall", "falling": "fall",
    "lost": "lose", "losing": "lose",
    "began": "begin", "begun": "begin", "beginning": "begin",
    "spoke": "speak", "spoken": "speak", "speaking": "speak",
    "hurt": "hurt", "hurting": "hurt",
    "ached": "ache", "aching": "ache",
    "swelled": "swell", "swollen": "swell", "swelling": "swell",
    "bled": "bleed", "bleeding": "bleed",
}

_IRREGULAR_ADJ = {
    "better": "good", "best": "good",
    "worse": "bad", "worst": "bad",
    "more": "many", "most": "many",
    "less": "little", "least": "little",
    "older": "old", "oldest": "old",
    "younger": "young", "youngest": "young",
    "easier": "easy", "easiest": "easy",
}


def _plural_rule(word: str) -> str | None:
    if word in _IRREGULAR_NOUNS:
        return _IRREGULAR_NOUNS[word]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ves") and len(word) > 4:
        return word[:-3] + "f"
    if word.endswith("ses") and len(word) > 4:
        return word[:-2]
    if word.endswith("xes") and len(word) > 4:
        return word[:-2]
    if word.endswith("zes") and len(word) > 4:
        return word[:-2]
    if word.endswith("ches") and len(word) > 5:
        return word[:-2]
    if word.endswith("shes") and len(word) > 5:
        return word[:-2]
    if (
        word.endswith("s")
        and not word.endswith("ss")
        and not word.endswith("us")
        and not word.endswith("is")
        and len(word) > 3
    ):
        return word[:-1]
    return None


def _verb_rule(word: str) -> str | None:
    if word in _IRREGULAR_VERBS:
        return _IRREGULAR_VERBS[word]
    if word.endswith("ying") and len(word) > 5:
        return word[:-4] + "y"
    if word.endswith("ing") and len(word) > 5:
        # doubled consonant: running -> run
        stem_part = word[:-3]
        if (
            len(stem_part) >= 2
            and stem_part[-1] == stem_part[-2]
            and stem_part[-1] not in "aeiou"
        ):
            stem_part = stem_part[:-1]
        return stem_part if len(stem_part) >= 2 else None
    if word.endswith("ied") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("ed") and len(word) > 4:
        stem_part = word[:-2]
        if (
            len(stem_part) >= 2
            and stem_part[-1] == stem_part[-2]
            and stem_part[-1] not in "aeiou"
        ):
            stem_part = stem_part[:-1]
        return stem_part if len(stem_part) >= 2 else None
    return None


def _adj_rule(word: str) -> str | None:
    if word in _IRREGULAR_ADJ:
        return _IRREGULAR_ADJ[word]
    if word.endswith("iest") and len(word) > 4:
        return word[:-4] + "y"
    if word.endswith("ier") and len(word) > 3:
        return word[:-3] + "y"
    if word.endswith("est") and len(word) > 4:
        return word[:-3]
    if word.endswith("er") and len(word) > 3:
        return word[:-2]
    return None


def lemmatize(word: str) -> str:
    """Return a best-guess lemma for a lowercase English token."""
    w = (word or "").lower()
    if len(w) <= 2:
        return w

    # Try rules in priority order. Verbs (ing/ed) are most specific.
    for rule in (_verb_rule, _plural_rule, _adj_rule):
        out = rule(w)
        if out and out != w:
            return out

    # Drop trailing 'ly' for clear adverbs.
    if w.endswith("ly") and len(w) > 4:
        return w[:-2]

    return w


def lemmatize_tokens(tokens: list[str]) -> list[str]:
    return [lemmatize(t) for t in tokens]


def canonical(token: str) -> str:
    """Lemmatize, fall back to Porter stem if the lemma is still inflected."""
    lem = lemmatize(token)
    if lem == token and len(token) > 4:
        return porter_stem(token)
    return lem

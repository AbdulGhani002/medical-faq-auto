"""Text normalisation: lower-case, strip punctuation, tokenize, expand."""
import re

from .synonyms import SYNONYMS, expand_term

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Small stopword list. We keep medical-relevant words like "before/after".
_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "do", "does", "did", "doing", "have", "has", "had",
    "i", "you", "he", "she", "we", "they", "it", "me", "him", "her", "us", "them",
    "my", "your", "his", "their", "our", "its",
    "and", "or", "but", "if", "so",
    "to", "of", "in", "on", "at", "for", "with", "by", "from",
    "this", "that", "these", "those",
    "as", "than", "then",
}


def basic_clean(text: str) -> str:
    return (text or "").lower().strip()


def tokenize(text: str, drop_stopwords: bool = True) -> list[str]:
    """Lowercase, strip, return tokens. Optionally drop a small stopword set."""
    toks = _TOKEN_RE.findall(basic_clean(text))
    if drop_stopwords:
        toks = [t for t in toks if t not in _STOPWORDS]
    return toks


def expand_query(text: str) -> str:
    """Return a query string with single-word synonyms appended for each
    in-vocabulary token. Multi-word phrases are also matched and expanded.
    """
    base = basic_clean(text)
    # Phrase expansions: look for any multi-word synonym key in the text.
    phrase_adds: list[str] = []
    for key, alts in SYNONYMS.items():
        if " " in key and key in base:
            phrase_adds.extend(alts)

    toks = _TOKEN_RE.findall(base)
    out: list[str] = list(toks)
    for t in toks:
        for alt in expand_term(t):
            if alt != t:
                out.append(alt)
    out.extend(phrase_adds)
    return " ".join(out)


def join_for_index(question: str, answer: str) -> str:
    """Documents are indexed as question + " " + answer with question
    appearing twice so its terms get a slight boost.
    """
    return f"{question} {question} {answer}"

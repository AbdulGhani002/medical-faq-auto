"""Conversation context: detect follow-up questions and augment the query."""
import re

_FOLLOWUP_STARTS = {
    "why", "how", "what", "when", "where", "who", "which",
    "and", "but", "so", "or",
    "more", "also", "again", "still", "even",
    "yes", "no", "ok", "okay",
}

_PRONOUNS = {"it", "that", "this", "those", "these", "they", "them"}

_FOLLOWUP_PHRASES = {
    "tell me more", "elaborate", "explain", "go on", "anything else",
    "what about", "how about", "and what",
}


def is_followup(text: str) -> bool:
    """Return True if `text` looks like a short follow-up rather than a
    standalone question. Heuristic, classical NLP only.
    """
    t = (text or "").lower().strip().rstrip("?!.")
    if not t:
        return False

    # Phrases first (cheap exact match).
    for phrase in _FOLLOWUP_PHRASES:
        if t.startswith(phrase):
            return True

    tokens = re.findall(r"[a-z0-9]+", t)
    if not tokens:
        return False

    # Very short queries are almost always follow-ups.
    if len(tokens) <= 2:
        return True

    first = tokens[0]
    if first in _FOLLOWUP_STARTS and len(tokens) <= 5:
        return True

    # Pronoun-led queries: "it hurts when i", "that does not"
    if first in _PRONOUNS:
        return True

    return False


def augment_with_context(
    current: str,
    previous_user_text: str | None,
) -> str:
    """If `current` is a follow-up and we have a previous user message,
    return a combined query that gives the retriever the right context.
    Otherwise return `current` unchanged.
    """
    if not previous_user_text:
        return current
    if not is_followup(current):
        return current
    # Mash them. The retriever will tokenise and expand.
    return f"{previous_user_text} {current}"


def topic_words(text: str) -> list[str]:
    """Pull capitalised or topic-like tokens out of `text` to use as
    a slim context cue if augmentation is undesirable.
    """
    raw = re.findall(r"[a-zA-Z]+", text or "")
    return [w for w in raw if len(w) >= 4][:5]

"""Conversation context: detect follow-up questions and augment the query.

Heuristics are deliberately conservative. A query is only treated as a
follow-up when there is little content of its own (a single question word,
a pronoun-led short phrase, or an explicit 'tell me more' style cue). A
specific question like 'what is sciatica' is never tagged as a follow-up.
"""
import re

_FOLLOWUP_STARTS = {
    "why", "how", "what", "when", "where", "who", "which",
    "and", "but", "so", "or",
    "yes", "no", "ok", "okay",
}

_PRONOUNS = {"it", "that", "this", "those", "these", "they", "them"}

_MORE_WORDS = {"more", "elaborate", "explain", "again", "also", "still"}

_FOLLOWUP_PHRASES = (
    "tell me more", "tell me about", "go on", "anything else",
    "what about", "how about", "and what", "and how",
)


def is_followup(text: str) -> bool:
    t = (text or "").lower().strip().rstrip("?!.")
    if not t:
        return False
    for phrase in _FOLLOWUP_PHRASES:
        if t.startswith(phrase):
            return True

    tokens = re.findall(r"[a-z0-9]+", t)
    if not tokens:
        return False

    # Single token like "why" or "more".
    if len(tokens) == 1 and (
        tokens[0] in _FOLLOWUP_STARTS or tokens[0] in _MORE_WORDS
    ):
        return True

    # Pronoun-led very short query, e.g. "it hurts", "that one".
    if tokens[0] in _PRONOUNS and len(tokens) <= 3:
        return True

    # Contains a 'more / explain' cue word in a short query.
    if len(tokens) <= 5 and any(t_ in _MORE_WORDS for t_ in tokens):
        return True

    return False


def augment_with_context(
    current: str,
    previous_user_text: str | None,
) -> str:
    if not previous_user_text:
        return current
    if not is_followup(current):
        return current
    return f"{previous_user_text} {current}"


def topic_words(text: str) -> list[str]:
    raw = re.findall(r"[a-zA-Z]+", text or "")
    return [w for w in raw if len(w) >= 4][:5]

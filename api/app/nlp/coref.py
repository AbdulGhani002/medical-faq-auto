"""Simple coreference resolution for short follow-ups.

If the current message starts with a pronoun ("it", "that", "those",
...), we substitute the pronoun with the most recent salient noun from
conversation state. This is the same idea used by classical dialog
systems before transformers.
"""
from __future__ import annotations

import re

_PRONOUNS = {
    "it": "the topic",
    "this": "the topic",
    "that": "the topic",
    "they": "the topic",
    "them": "the topic",
    "those": "the topic",
    "these": "the topic",
}


_TOK_RE = re.compile(r"\b\w+\b")


def resolve(text: str, last_topic: str | None) -> tuple[str, list[dict]]:
    """Substitute pronouns with `last_topic` when sensible."""
    if not last_topic or not text:
        return text, []
    t = text or ""
    edits: list[dict] = []

    def _sub(m: re.Match) -> str:
        w = m.group(0)
        wl = w.lower()
        if wl in _PRONOUNS:
            edits.append({"original": w, "replacement": last_topic})
            return last_topic
        return w

    out = _TOK_RE.sub(_sub, t)
    return out, edits

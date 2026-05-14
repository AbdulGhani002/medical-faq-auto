"""Stage 7: rule-based polish on the canonical answer.

No LLM. Just regex / Python string ops:
  - normalise whitespace
  - ensure a closing punctuation
  - trim to MAX_SENTENCES
  - prepend a friendly greeting if missing
"""
import re

MAX_SENTENCES = 4
GREETING_PREFIX = ""  # set to e.g. "Thanks for asking. " if you want one


def _polish_one(answer: str) -> str:
    a = re.sub(r"\s+", " ", answer or "").strip()
    if not a:
        return a
    if a[-1] not in ".!?":
        a += "."

    parts = re.split(r"(?<=[.!?])\s+", a)
    a = " ".join(parts[:MAX_SENTENCES])

    if GREETING_PREFIX and not a.lower().startswith(GREETING_PREFIX.lower()):
        a = GREETING_PREFIX + a

    # Capitalise first letter.
    if a:
        a = a[0].upper() + a[1:]
    return a


def run(items: list[dict]) -> list[dict]:
    for it in items:
        it["answer"] = _polish_one(it["answer"])
    return items

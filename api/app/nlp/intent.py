"""Rule-based intent classifier.

Distinguishes the four user-intent classes we handle: ``greeting``,
``thanks``, ``frustration``, and ``question`` (the default).
"""
import re

_GREETINGS = {
    "hi", "hello", "hey", "hiya", "yo", "salaam", "salam", "assalam",
    "good morning", "good afternoon", "good evening", "good night",
    "hi there", "hey there",
}

_THANKS = {
    "thanks", "thank you", "thx", "thankyou", "ty", "appreciate it",
    "appreciated", "much appreciated", "shukria", "shukriya", "cheers",
}

_FRUSTRATION = {
    "wtf", "wth", "ugh", "ffs", "useless", "stupid", "garbage",
    "this sucks", "this is bad", "rubbish", "useless bot",
    "you suck", "lame", "boring",
}

_HELP = {
    "help", "what can you do", "what do you do", "menu", "options",
    "topics", "categories",
}


def _normalise(text: str) -> str:
    t = (text or "").lower().strip().rstrip("?!.,")
    return re.sub(r"\s+", " ", t)


def classify(text: str) -> str:
    t = _normalise(text)
    if not t:
        return "question"

    if any(t == g or t.startswith(g + " ") for g in _GREETINGS):
        return "greeting"
    if any(t == g or t.startswith(g + " ") for g in _THANKS):
        return "thanks"
    if any(t == g or g in t for g in _FRUSTRATION):
        return "frustration"
    if any(t == g or t.startswith(g) for g in _HELP):
        return "help"
    return "question"


CANNED_REPLIES = {
    "greeting": (
        "Hi. I am a {specialty} assistant. Ask me anything about "
        "preparation, recovery, medications, or general care. I will "
        "look up a clinician-reviewed answer for you."
    ),
    "thanks": (
        "You are welcome. If you have another question on {specialty}, "
        "just ask."
    ),
    "frustration": (
        "Sorry that did not help. I only return real, clinician-reviewed "
        "answers and never invent text. Try rephrasing the question, or "
        "pick one of the suggested topics below. For anything urgent, "
        "please contact the clinic directly."
    ),
    "help": (
        "I can answer common {specialty} questions, for example: "
        "preparation before procedures, what to expect, medication timing, "
        "warning signs, and recovery. Try a phrase like 'how long does it "
        "take' or 'what should I avoid'."
    ),
}


def canned(intent: str, specialty: str) -> str | None:
    tpl = CANNED_REPLIES.get(intent)
    if tpl is None:
        return None
    return tpl.format(specialty=specialty)

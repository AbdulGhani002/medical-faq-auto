"""Out-of-scope detector.

The bot only covers radiology, physiotherapy, and cardiology. When the
user message is obviously about something else (sexual health,
financial advice, programming, food recipes, etc.) the retriever
should NOT pick the closest medical FAQ by accident. Instead we
politely deflect.

This is a small allow-list of off-topic phrases. We deliberately keep
it short and conservative so legitimate medical questions never fall
through. The deflection message names the three specialties we
actually cover.
"""
from __future__ import annotations

import re


# Words that strongly indicate the message is outside the three
# specialties this assistant covers. Most are sexual-health terms in
# English + Roman-Urdu. Anything in this set forces a polite
# deflection instead of running retrieval.
_OUT_OF_SCOPE_TOKENS = {
    # English sexual health / urology / fertility
    "erectile", "erection", "impotence", "viagra", "cialis",
    "penis", "vagina", "testicle", "prostate", "ejaculat",
    "intercourse", "orgasm", "porn", "masturbat",
    "sperm", "fertility", "infertility", "ivf", "contraceptive",
    "condom", "abortion", "menstruation", "menstrual", "period pain",
    "uti", "std", "sti", "hiv", "herpes", "gonorrhea", "syphilis",
    # Roman-Urdu / slang for the same
    "lulli", "lund", "chuchi", "boobs", "shagal", "kamzor mardana",
    "mardana", "nifas",
    # Off-topic
    "bitcoin", "ethereum", "stock", "trading", "loan",
    "homework", "assignment", "javascript", "python", "react",
    "recipe", "cooking", "biryani", "pizza",
    "football", "cricket", "movie", "song", "netflix",
}

_TOK_RE = re.compile(r"[a-z]+")


def looks_out_of_scope(text: str) -> tuple[bool, list[str]]:
    """Return (is_off_topic, matched_words)."""
    if not text:
        return False, []
    toks = set(_TOK_RE.findall(text.lower()))
    # Substring match so "erectile" also catches "erectile dysfunction".
    hits = [t for t in _OUT_OF_SCOPE_TOKENS
            if t in toks or any(t in w for w in toks)]
    return bool(hits), hits


def deflection_message(specialty: str) -> str:
    return (
        "That question is outside what this assistant covers. I am "
        "trained only on Radiology, Physiotherapy, and Cardiovascular "
        "FAQs that have been reviewed by clinicians. Please ask your "
        "family doctor or the relevant specialist for this concern. "
        f"If your question is about {specialty}, please rephrase it."
    )

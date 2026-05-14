"""Basic PHI (protected health information) scrubbing via regex.

This is intentionally simple. The pipeline runs a heavier NER-based pass
before clustering. The point of this scrub is to keep raw chat logs clean
in the database from the very first turn.
"""
import re

_PATTERNS = [
    # Pakistani CNIC pattern (5 + 7 + 1 digits with optional dashes).
    (re.compile(r"\b\d{5}[- ]?\d{7}[- ]?\d\b"), "[ID]"),
    # Long digit sequences likely to be phone numbers.
    (re.compile(r"\b\d{10,13}\b"), "[PHONE]"),
    # Emails.
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    # Dates like 01/02/2025 or 1-2-25.
    (re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"), "[DATE]"),
]


def scrub(text: str) -> str:
    for pat, repl in _PATTERNS:
        text = pat.sub(repl, text)
    return text

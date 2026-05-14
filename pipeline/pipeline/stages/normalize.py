"""Stage 3: clean text, scrub PHI, fix unicode and casing."""
import re

try:
    import ftfy
    _have_ftfy = True
except ImportError:
    _have_ftfy = False

_PHI = [
    (re.compile(r"\b\d{5}[- ]?\d{7}[- ]?\d\b"), "[ID]"),
    (re.compile(r"\b\d{10,13}\b"), "[PHONE]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"), "[DATE]"),
]


def _clean(text: str) -> str:
    if _have_ftfy:
        text = ftfy.fix_text(text)
    for pat, repl in _PHI:
        text = pat.sub(repl, text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.lower()


def run(turns: list[dict]) -> list[dict]:
    for t in turns:
        t["clean"] = _clean(t.get("user_text", ""))
    return turns

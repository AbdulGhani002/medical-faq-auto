"""Question type classifier.

Returns one of {yes_no, what, why, how, when, where, who, which,
choice, statement}. Pure heuristics on the first 1-3 tokens.
"""
from __future__ import annotations

import re

_AUX = {"is", "are", "was", "were", "do", "does", "did", "can",
        "could", "should", "shall", "will", "would", "may", "might",
        "must", "have", "has", "had", "am"}

_WH = {
    "what": "what", "whats": "what",
    "why": "why",
    "how": "how", "hows": "how",
    "when": "when",
    "where": "where",
    "who": "who", "whos": "who",
    "which": "which",
}

_TOKEN_RE = re.compile(r"[a-z0-9']+")


def classify(text: str) -> str:
    raw = (text or "").lower().strip()
    has_qmark = raw.endswith("?")
    t = raw.rstrip("?.!,")
    toks = _TOKEN_RE.findall(t)
    if not toks:
        return "statement"

    first = toks[0].replace("'", "")
    if first in _WH:
        return _WH[first]

    # 'A or B?' style takes priority over yes/no when both could apply.
    if " or " in t and has_qmark:
        return "choice"

    if first in _AUX:
        return "yes_no"

    # 'tell me ...' is procedurally a yes/no-ish but we treat it as wh-what.
    if first in {"tell", "show", "give", "explain"}:
        return "what"

    if has_qmark:
        return "yes_no"

    return "statement"


_OPENERS = {
    "yes_no": "",  # Use the FAQ verbatim.
    "what": "",
    "why": "",
    "how": "",
    "when": "",
    "where": "",
    "who": "",
    "which": "",
    "choice": "",
    "statement": "",
}

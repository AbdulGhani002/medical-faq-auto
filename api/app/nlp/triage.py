"""Urgency / triage detector.

We flag any message that contains red-flag medical phrases ("crushing
chest pain", "can't breathe", "passing out", ...) and return an
``urgency`` level + a list of matched cues.

Levels:
  0 - none
  1 - mild concern (we add a soft caution)
  2 - moderate (we add a clear "see a doctor" note)
  3 - severe (we lead with an emergency banner)
"""
from __future__ import annotations

import re

_SEVERE_PATTERNS = [
    r"\bcrushing chest pain\b",
    r"\bsevere chest pain\b",
    r"\bcant breathe\b",
    r"\bcan ?not breathe\b",
    r"\bstruggling to breathe\b",
    r"\bgasping\b",
    r"\bpassing out\b",
    r"\bpassed out\b",
    r"\bfainted\b",
    r"\bunconscious\b",
    r"\bnot breathing\b",
    r"\bblue lips\b",
    r"\bblue around the mouth\b",
    r"\bturning blue\b",
    r"\bstroke symptoms\b",
    r"\bface drooping\b",
    r"\bslurred speech\b",
    r"\bone side weak(ness)?\b",
    r"\barm went numb\b",
    r"\bcoughing up blood\b",
    r"\bvomiting blood\b",
    r"\bblood in (stool|urine|vomit)\b",
    r"\bsuicid(e|al)\b",
    r"\bheart attack\b",
    r"\bhad a stroke\b",
    r"\bseizure\b",
]

_MODERATE_PATTERNS = [
    r"\bchest pain\b",
    r"\bchest tightness\b",
    r"\bsevere headache\b",
    r"\bshortness of breath\b",
    r"\bvery breathless\b",
    r"\bfast heart\b",
    r"\bracing heart\b",
    r"\bbleeding heavily\b",
    r"\bblurred vision\b",
    r"\bnumbness\b",
    r"\bweakness on one side\b",
    r"\bsevere pain\b",
    r"\bcollapsed\b",
    r"\bvery dizzy\b",
    r"\bsudden weight loss\b",
    r"\bhigh fever\b",
    r"\b40 ?degrees\b",
]

_MILD_PATTERNS = [
    r"\bworried\b",
    r"\banxious\b",
    r"\bscared\b",
    r"\bfeel awful\b",
    r"\bsharp pain\b",
    r"\bsudden pain\b",
    r"\bgetting worse\b",
    r"\bhurts a lot\b",
    r"\breally hurts\b",
    r"\bcant sleep\b",
    r"\bnausea\b",
    r"\bvomiting\b",
]

_RE = {
    3: [re.compile(p, re.I) for p in _SEVERE_PATTERNS],
    2: [re.compile(p, re.I) for p in _MODERATE_PATTERNS],
    1: [re.compile(p, re.I) for p in _MILD_PATTERNS],
}


def assess(text: str) -> dict:
    """Return {level, cues}."""
    t = text or ""
    cues: list[str] = []
    level = 0
    for lvl in (3, 2, 1):
        for pat in _RE[lvl]:
            m = pat.search(t)
            if m:
                cues.append(m.group(0))
                if lvl > level:
                    level = lvl
        if level == lvl == 3:
            break
    return {"level": level, "cues": cues}


_BANNERS = {
    3: (
        "EMERGENCY: please call 1122 (or your local emergency number) "
        "now. The phrase you used can describe a life-threatening "
        "event. I will still try to find an FAQ but do not wait."
    ),
    2: (
        "This sounds like a symptom that should be reviewed by a "
        "clinician today. The FAQ below is general guidance, not a "
        "substitute for an in-person assessment."
    ),
    1: (
        "I am sorry you are not feeling great. The FAQ below is general "
        "guidance. If symptoms get worse, please contact your clinician."
    ),
}


def banner(level: int) -> str | None:
    return _BANNERS.get(level)

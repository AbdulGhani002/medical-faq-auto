"""Cross-specialty hint.

When the user is sitting in /chat/radiology and asks about chest pain
(a cardiovascular topic), the local retriever can only return
radiology FAQs about pain during scans. That is unhelpful.

This module looks at the user's message and the matched FAQ's
confidence. If the message strongly fits a different specialty AND
the local match is weak, we append a suggestion: "This sounds like
a cardiovascular question. Try the cardiology assistant for a better
answer." The local FAQ is still returned underneath.
"""
from __future__ import annotations

import re

_TOK_RE = re.compile(r"[a-z]+")

# Each specialty has a small bag of strongly-indicating keywords. We
# weight by simple counts: how many of the user's tokens hit each bag.
SPECIALTY_KEYWORDS: dict[str, set[str]] = {
    "radiology": {
        "mri", "ct", "x-ray", "xray", "scan", "ultrasound", "imaging",
        "contrast", "gadolinium", "iodine", "radiology", "radiologist",
        "mammogram", "biopsy", "dexa", "fluoroscopy", "pet", "tracer",
        "claustrophobic", "claustrophobia", "metallic", "implant",
        "tattoo", "pacemaker scan",
    },
    "physiotherapy": {
        "physio", "physiotherapy", "physiotherapist", "rehab",
        "exercise", "stretch", "stretching", "tens", "ultrasound therapy",
        "knee", "shoulder", "elbow", "ankle", "wrist", "hip",
        "back", "neck", "sciatica", "sprain", "strain",
        "rotator", "meniscus", "acl", "tendon", "ligament",
        "posture", "ergonomic", "gait", "balance",
    },
    "cardiovascular": {
        "heart", "cardiac", "cardio", "cardiology", "cardiologist",
        "chest", "angina", "stent", "bypass", "cabg",
        "bp", "blood pressure", "hypertension", "cholesterol",
        "statin", "aspirin", "ecg", "ekg", "holter", "echo",
        "echocardiogram", "angiogram", "stroke", "afib",
        "atrial fibrillation", "palpitation", "palpitations",
        "arrhythmia", "ldl", "hdl", "pacemaker", "valve",
        # Roman-Urdu cardiac
        "dil", "seenay", "dard",
    },
}


def best_specialty(text: str) -> tuple[str, int]:
    """Return (best_specialty, hit_count)."""
    toks = set(_TOK_RE.findall((text or "").lower()))
    blob = (text or "").lower()
    best = ""
    best_hits = 0
    for spec, kws in SPECIALTY_KEYWORDS.items():
        hits = 0
        for k in kws:
            if " " in k:
                if k in blob:
                    hits += 1
            elif k in toks:
                hits += 1
        if hits > best_hits:
            best = spec
            best_hits = hits
    return best, best_hits


# Pain words that escalate the cardio signal when chest / heart appears.
_PAIN_WORDS = {"pain", "ache", "hurt", "hurts", "hurting", "tight",
               "tightness", "pressure", "dard"}


def maybe_suggest_switch(text: str, current_specialty: str,
                          local_score: float) -> str | None:
    """Return a switch-hint string when warranted, else None."""
    best, hits = best_specialty(text)

    # Pain mentioned alongside "chest"/"heart"/"dil" counts as a strong
    # cardio signal even if those are the only two cardio keywords.
    toks = set(_TOK_RE.findall((text or "").lower()))
    if (toks & {"chest", "heart", "dil", "seenay"}) and (toks & _PAIN_WORDS):
        best = "cardiovascular"
        hits = max(hits, 2)

    if (best and best != current_specialty and hits >= 2
            and local_score < 0.70):
        nice = {
            "radiology": "the Radiology assistant",
            "physiotherapy": "the Physiotherapy assistant",
            "cardiovascular": "the Cardiology assistant",
        }.get(best, "another specialty")
        return (
            f"This message looks more like a {best} question. For a "
            f"better answer please ask {nice}. The closest FAQ in "
            f"{current_specialty} is shown below as general guidance."
        )
    return None

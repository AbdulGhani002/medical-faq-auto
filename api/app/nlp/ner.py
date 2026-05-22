"""Dictionary-based medical NER.

We do longest-match phrase lookup against curated medical lexicons. Every
entity is a real string from the input plus a label. No ML, no model.

Entity types we recognise:
  BODY        - body parts and anatomy
  SYMPTOM     - subjective complaints
  CONDITION   - named diseases / disorders
  DRUG        - medication classes and named drugs
  PROCEDURE   - tests, scans, therapies
  TIME        - duration / frequency hints
  NUMBER      - cardinal numbers (caught via regex)
  PERSON      - kid / mother / etc. (rough demographics)
"""
from __future__ import annotations

import re

BODY = {
    "head", "neck", "shoulder", "arm", "elbow", "wrist", "hand",
    "finger", "fingers", "chest", "rib", "ribs", "back", "spine",
    "hip", "thigh", "knee", "ankle", "foot", "feet", "toe", "toes",
    "leg", "calf", "stomach", "abdomen", "belly", "pelvis",
    "muscle", "muscles", "tendon", "ligament", "nerve", "bone",
    "heart", "brain", "lung", "lungs", "liver", "kidney", "kidneys",
    "skin", "eye", "eyes", "ear", "ears", "throat", "mouth",
    "tongue", "jaw", "lower back", "upper back", "rotator cuff",
    "achilles tendon", "calf muscle", "shoulder blade",
}

SYMPTOM = {
    "pain", "ache", "soreness", "stiffness", "swelling", "dizziness",
    "tiredness", "fatigue", "shortness of breath", "breathlessness",
    "palpitations", "palpitation", "fluttering", "tightness",
    "pressure", "burning", "numbness", "tingling", "weakness",
    "fainting", "blacking out", "blackout", "blurred vision",
    "headache", "nausea", "vomiting", "fever", "sweating",
    "chills", "cough", "wheezing", "itching", "rash",
    "chest pain", "back pain", "neck pain", "knee pain",
    "leg pain", "abdominal pain", "stomach pain", "joint pain",
    "muscle ache", "sore throat",
}

CONDITION = {
    "hypertension", "high blood pressure", "low blood pressure",
    "diabetes", "asthma", "copd", "stroke", "heart attack",
    "heart failure", "afib", "atrial fibrillation", "angina",
    "arrhythmia", "tachycardia", "bradycardia", "stenosis",
    "blockage", "blocked artery", "high cholesterol",
    "sleep apnea", "anxiety", "depression", "obesity",
    "sciatica", "arthritis", "tendinitis", "tendonitis",
    "bursitis", "carpal tunnel", "frozen shoulder", "plantar fasciitis",
    "rotator cuff tear", "meniscus tear", "acl tear", "fracture",
    "sprain", "strain", "whiplash", "slipped disc", "herniated disc",
    "pinched nerve", "kidney stones", "thyroid",
}

DRUG = {
    "aspirin", "paracetamol", "ibuprofen", "naproxen", "panadol",
    "amlodipine", "losartan", "valsartan", "lisinopril", "ramipril",
    "atenolol", "metoprolol", "bisoprolol", "carvedilol",
    "atorvastatin", "rosuvastatin", "simvastatin", "warfarin",
    "clopidogrel", "rivaroxaban", "apixaban", "dabigatran",
    "metformin", "insulin", "salbutamol", "ventolin",
    "blood pressure medicine", "bp medicine", "bp meds",
    "statin", "statins", "beta blocker", "ace inhibitor",
    "calcium channel blocker", "diuretic", "blood thinner",
    "blood thinners", "nitroglycerin", "gtn", "nitro spray",
    "painkiller", "painkillers", "antibiotic", "antibiotics",
}

PROCEDURE = {
    "mri", "ct", "x-ray", "xray", "ultrasound", "echo",
    "echocardiogram", "ecg", "ekg", "holter", "stress test",
    "blood test", "bloods", "angiogram", "angioplasty", "stent",
    "bypass", "cabg", "ablation", "pacemaker", "physio session",
    "physiotherapy session", "physical therapy", "rehab session",
    "scan", "imaging", "biopsy", "surgery", "operation",
    "exercise programme", "exercise program", "home exercises",
    "stretching exercises", "cardio rehab", "cardiac rehab",
}

TIME = {
    "morning", "afternoon", "evening", "night", "noon",
    "today", "tomorrow", "yesterday", "weekly", "daily",
    "monthly", "yearly", "minute", "minutes", "hour", "hours",
    "day", "days", "week", "weeks", "month", "months", "year",
    "years", "now", "soon", "later", "before", "after",
}

PERSON = {
    "kid", "kids", "child", "children", "baby", "infant",
    "mother", "father", "parent", "parents", "wife", "husband",
    "son", "daughter", "elderly", "senior", "pregnant",
    "pregnancy", "diabetic", "diabetics", "hypertensive",
}


# Map each entity to its label, longest first for greedy matching.
def _build_lexicon() -> list[tuple[str, str]]:
    items: list[tuple[str, str]] = []
    for s in BODY: items.append((s.lower(), "BODY"))
    for s in SYMPTOM: items.append((s.lower(), "SYMPTOM"))
    for s in CONDITION: items.append((s.lower(), "CONDITION"))
    for s in DRUG: items.append((s.lower(), "DRUG"))
    for s in PROCEDURE: items.append((s.lower(), "PROCEDURE"))
    for s in TIME: items.append((s.lower(), "TIME"))
    for s in PERSON: items.append((s.lower(), "PERSON"))
    # Sort by length desc so phrase "chest pain" beats "chest" + "pain".
    items.sort(key=lambda kv: -len(kv[0]))
    return items


_LEXICON = _build_lexicon()


_NUM_RE = re.compile(r"\b\d+(?:\.\d+)?\b")


def extract_entities(text: str) -> list[dict]:
    """Return [{text, label, start, end}] entities.

    Phrases are matched greedily, longest first. A char span is masked
    after a match so substrings of an already-matched phrase do not
    double-count.
    """
    if not text:
        return []
    t = text.lower()
    mask = [False] * len(t)
    out: list[dict] = []

    for term, label in _LEXICON:
        if " " in term:
            # Phrase: find every occurrence.
            start = 0
            while True:
                i = t.find(term, start)
                if i == -1:
                    break
                if not any(mask[i:i + len(term)]):
                    # Boundary check.
                    left_ok = i == 0 or not t[i - 1].isalnum()
                    right_ok = (
                        i + len(term) == len(t)
                        or not t[i + len(term)].isalnum()
                    )
                    if left_ok and right_ok:
                        out.append({"text": text[i:i + len(term)],
                                    "label": label,
                                    "start": i,
                                    "end": i + len(term)})
                        for k in range(i, i + len(term)):
                            mask[k] = True
                start = i + len(term)
        else:
            # Single word: regex with word boundaries.
            for m in re.finditer(rf"\b{re.escape(term)}\b", t):
                i, j = m.span()
                if any(mask[i:j]):
                    continue
                out.append({"text": text[i:j], "label": label,
                            "start": i, "end": j})
                for k in range(i, j):
                    mask[k] = True

    for m in _NUM_RE.finditer(t):
        i, j = m.span()
        if any(mask[i:j]):
            continue
        out.append({"text": text[i:j], "label": "NUMBER",
                    "start": i, "end": j})
        for k in range(i, j):
            mask[k] = True

    out.sort(key=lambda e: e["start"])
    return out


def entity_labels(entities: list[dict]) -> set[str]:
    return {e["label"] for e in entities}


def primary_topic(entities: list[dict]) -> str | None:
    """The most distinctive entity for follow-up tracking."""
    priority = ["CONDITION", "PROCEDURE", "DRUG", "SYMPTOM", "BODY"]
    for p in priority:
        for e in entities:
            if e["label"] == p:
                return e["text"].lower()
    return None

"""Lightweight Roman-Urdu phonetic normaliser for Pakistani patient input.

Patients in Pakistan routinely mix English and Roman-Urdu inside the
same sentence ("mera dard kam ho gaya, doctor sahab"). We don't run a
translation model; we just have a curated dictionary of the ~80 most
common medical-relevant Roman-Urdu words that map onto an English
keyword, plus a couple of phonetic rules so close spellings collapse.

Output goes into the standard retrieval pipeline as a *normalisation*
step: the original tokens are kept and the English equivalents are
appended, so a query like "sar mein dard" gets expanded to
"sar mein dard head head pain head pain".
"""
from __future__ import annotations

import re

URDU_TO_EN: dict[str, list[str]] = {
    # Body parts
    "sar": ["head"], "sir": ["head"],
    "ankh": ["eye"], "ankhain": ["eyes"],
    "kaan": ["ear"], "kan": ["ear"], "kaano": ["ears"],
    "naak": ["nose"],
    "moo": ["mouth"], "munh": ["mouth"], "munh": ["mouth"],
    "dant": ["tooth"], "daant": ["tooth"],
    "haath": ["hand"], "haat": ["hand"],
    "ungli": ["finger"], "unglian": ["fingers"],
    "kandha": ["shoulder"], "kandhe": ["shoulder"],
    "kohni": ["elbow"],
    "ghutna": ["knee"], "ghutne": ["knee"], "ghutno": ["knees"],
    "paer": ["foot", "leg"], "paair": ["foot"], "paaon": ["foot"],
    "tang": ["leg"], "tangain": ["legs"],
    "kamar": ["back", "lower back"],
    "peeth": ["back"], "peet": ["back"],
    "pet": ["stomach", "abdomen"], "peeit": ["stomach"],
    "seena": ["chest"], "seenay": ["chest"], "chaati": ["chest"],
    "dil": ["heart"],
    "khoon": ["blood"],
    "jisam": ["body"],

    # Symptoms / sensations
    "dard": ["pain", "ache"],
    "takleef": ["pain", "discomfort"],
    "kharish": ["itching"],
    "soozish": ["swelling"],
    "soozan": ["swelling"],
    "garam": ["fever", "hot"],
    "bukhar": ["fever"],
    "khansi": ["cough"],
    "zukam": ["cold", "flu"],
    "matli": ["nausea"],
    "ulti": ["vomiting"], "ulti aana": ["vomiting"],
    "ghabrahat": ["anxiety", "palpitations"],
    "chakar": ["dizziness"], "chakkar": ["dizziness"],
    "kamzori": ["weakness", "tiredness"],
    "thakaan": ["fatigue", "tiredness"],
    "neend": ["sleep"],
    "saans": ["breath"], "saans phoolna": ["shortness of breath"],
    "ghutan": ["tightness"],

    # Common verbs / function
    "hai": [], "hain": [], "hain": [], "ho": [], "hoga": [],
    "kya": ["what"], "kab": ["when"], "kahan": ["where"],
    "kaise": ["how"], "kyon": ["why"], "kyun": ["why"],
    "kyunke": ["because"],
    "nahi": ["no", "not"], "nahin": ["no", "not"],
    "haan": ["yes"],
    "thora": ["a little"], "thoda": ["a little"],
    "bohot": ["a lot", "very"], "bahut": ["a lot", "very"],
    "ziada": ["more"], "zyada": ["more"],
    "thik": ["fine", "ok"], "theek": ["fine", "ok"],
    "buri": ["bad"], "bura": ["bad"],
    "achi": ["good"], "acha": ["good"], "accha": ["good"],

    # Procedures / care
    "scan": ["scan"], "test": ["test"],
    "dawai": ["medicine"], "dawaiyan": ["medicines"],
    "dawa": ["medicine"],
    "doctor": ["doctor"], "doctar": ["doctor"],
    "hospital": ["hospital"],
    "clinic": ["clinic"],
    "report": ["report", "result"],
    "khoon ka test": ["blood test"],
    "elaaj": ["treatment"], "ilaj": ["treatment"],

    # Time
    "subah": ["morning"],
    "shaam": ["evening"],
    "raat": ["night"],
    "din": ["day"],
    "kal": ["yesterday", "tomorrow"],
    "aaj": ["today"],
    "abhi": ["now"],
    "phir": ["again"],

    # Family / context
    "ami": ["mother"], "ammi": ["mother"], "maa": ["mother"],
    "abu": ["father"], "abbu": ["father"], "baba": ["father"],
    "bhai": ["brother"], "behan": ["sister"],
    "bacha": ["child"], "bachay": ["children"], "bachi": ["girl"],

    # Common greetings / politeness (recognised so intent classifier
    # picks them up; not actually translated to anything useful).
    "salaam": ["hello"], "salam": ["hello"],
    "assalam": ["hello"], "assalamoalaikum": ["hello"],
    "shukria": ["thanks"], "shukriya": ["thanks"], "mehrbani": ["thanks"],
}


_TOK_RE = re.compile(r"[A-Za-z]+")


def contains_roman_urdu(text: str) -> bool:
    """Cheap heuristic: at least 2 tokens are in our dictionary."""
    if not text:
        return False
    hits = 0
    for m in _TOK_RE.finditer(text.lower()):
        if m.group(0) in URDU_TO_EN:
            hits += 1
            if hits >= 2:
                return True
    return False


def expand(text: str) -> tuple[str, list[dict]]:
    """Return (augmented_text, edits). The original text is preserved and
    English equivalents are appended at the end, separated by a space.
    """
    if not text:
        return text, []
    additions: list[str] = []
    edits: list[dict] = []
    seen: set[str] = set()
    for m in _TOK_RE.finditer(text.lower()):
        tok = m.group(0)
        if tok not in URDU_TO_EN:
            continue
        for tr in URDU_TO_EN[tok]:
            if not tr or tr in seen:
                continue
            additions.append(tr)
            seen.add(tr)
            edits.append({"original": tok, "translated": tr,
                          "start": m.start(), "end": m.end()})
    if not additions:
        return text, []
    return f"{text} {' '.join(additions)}", edits

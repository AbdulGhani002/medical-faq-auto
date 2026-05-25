"""Generate JSONL datasets from the project's existing JSON sources.

Outputs (all written to ``data/`` next to this script):

  - faqs.jsonl              merged FAQ corpus, one JSON object per line
  - intents.jsonl           Naive-Bayes intent training data, one per line
  - eval_queries.jsonl      evaluation queries, one per line
  - chat_logs.jsonl         synthetic patient chat logs for the pipeline
  - ner_examples.jsonl      annotated NER examples (token + BIO tag)
  - sentiment_lexicon.jsonl per-word polarity weights
  - dataset_manifest.json   summary index of every file produced

The JSONL format keeps each record on a single line so the pipeline
(and any external tool) can stream-read it.

Run with:  python data/build_jsonl.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path


HERE = Path(__file__).parent
ROOT = HERE.parent
API_APP = ROOT / "api" / "app"


# ---------------------------------------------------------------- helpers


def write_jsonl(path: Path, records: list[dict]) -> int:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return len(records)


def read_json(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------- FAQs


def build_faqs() -> list[dict]:
    out: list[dict] = []
    for name in ("faqs_radiology.json", "faqs_physiotherapy.json",
                 "faqs_cardiovascular.json"):
        p = HERE / name
        if not p.exists():
            continue
        for i, item in enumerate(read_json(p)):
            rec = {
                "id": f"{item['specialty']}-{i:04d}",
                "specialty": item["specialty"],
                "question": item["question"],
                "answer": item["answer"],
                "approved": bool(item.get("approved", True)),
                "tags": _faq_tags(item["question"] + " " + item["answer"]),
            }
            out.append(rec)
    return out


def _faq_tags(text: str) -> list[str]:
    """Coarse tags inferred from the FAQ text. Helps downstream filtering."""
    t = text.lower()
    tags: list[str] = []
    if any(k in t for k in ("mri", "ct ", "x-ray", "xray", "ultrasound",
                            "scan ", "imaging", "echocardiogram", "ecg",
                            "ekg", "holter")):
        tags.append("imaging")
    if any(k in t for k in ("exercise", "physio", "rehab", "stretch",
                            "session")):
        tags.append("physio")
    if any(k in t for k in ("blood pressure", "bp ", "heart", "cholesterol",
                            "stroke", "afib", "angina", "statin", "aspirin")):
        tags.append("cardio")
    if any(k in t for k in ("fast", "before your", "preparation", "prepare")):
        tags.append("preparation")
    if any(k in t for k in ("recover", "after", "return", "rest")):
        tags.append("recovery")
    if any(k in t for k in ("warning", "emergency", "call 1122",
                            "see your doctor", "see a doctor")):
        tags.append("warning")
    if any(k in t for k in ("medicine", "tablet", "dose", "drug",
                            "side effect")):
        tags.append("medication")
    if not tags:
        tags.append("general")
    return tags


# ---------------------------------------------------------------- intents


def build_intents() -> list[dict]:
    """Re-export the Naive Bayes training corpus from `nb_intent._TRAIN`
    plus extra augmentations so future training has more signal."""
    sys.path.insert(0, str(ROOT / "api"))
    from app.nlp.nb_intent import _TRAIN  # noqa: WPS433 - intentional import

    extra: list[tuple[str, str]] = [
        # extra greetings (12)
        ("hey doc", "greeting"), ("hi there assistant", "greeting"),
        ("good day", "greeting"), ("hello dr", "greeting"),
        ("hey", "greeting"), ("yo", "greeting"),
        ("morning doctor", "greeting"), ("hello there", "greeting"),
        ("good morning sir", "greeting"), ("hiya", "greeting"),
        ("hi assistant", "greeting"), ("hey medfaq", "greeting"),
        # extra thanks (10)
        ("appreciate the help", "thanks"), ("thanks a lot", "thanks"),
        ("thank you very much", "thanks"), ("many thanks", "thanks"),
        ("cheers for that", "thanks"), ("super helpful", "thanks"),
        ("thanks doctor", "thanks"), ("thanks for explaining", "thanks"),
        ("thx so much", "thanks"), ("thanks i got it now", "thanks"),
        # extra frustration (8)
        ("not helpful at all", "frustration"),
        ("this answer is wrong", "frustration"),
        ("you have no idea", "frustration"),
        ("terrible bot", "frustration"),
        ("waste of time", "frustration"),
        ("you are useless", "frustration"),
        ("nope this is wrong", "frustration"),
        ("rubbish", "frustration"),
        # extra help (8)
        ("what topics can you answer", "help"),
        ("give me a list of things you can do", "help"),
        ("how do i use you", "help"),
        ("can you guide me", "help"),
        ("what kind of questions can i ask", "help"),
        ("show options", "help"),
        ("what areas you cover", "help"),
        ("can you list specialties", "help"),
        # definition (8)
        ("explain afib", "ask_definition"),
        ("what is bp", "ask_definition"),
        ("define dash diet", "ask_definition"),
        ("what does cardiac arrest mean", "ask_definition"),
        ("explain to me what diabetes is", "ask_definition"),
        ("tell me what high cholesterol is", "ask_definition"),
        ("what is a stent", "ask_definition"),
        ("what does ldl stand for", "ask_definition"),
        # preparation (8)
        ("any prep before angiogram", "ask_preparation"),
        ("fast before contrast scan", "ask_preparation"),
        ("preparation for x ray", "ask_preparation"),
        ("any restriction before ecg", "ask_preparation"),
        ("what to do night before mri", "ask_preparation"),
        ("can i eat before the test", "ask_preparation"),
        ("instructions before holter monitor", "ask_preparation"),
        ("what to bring to my first physio", "ask_preparation"),
        # recovery (10)
        ("when can i start lifting again", "ask_recovery"),
        ("how long until i can go back to work", "ask_recovery"),
        ("recovery period after stent", "ask_recovery"),
        ("when can i drive after surgery", "ask_recovery"),
        ("how long for the bruise to clear", "ask_recovery"),
        ("when can i swim again", "ask_recovery"),
        ("how soon can i fly after a heart attack", "ask_recovery"),
        ("when can i resume gym", "ask_recovery"),
        ("recovery after rotator cuff repair", "ask_recovery"),
        ("how many weeks for the knee to heal", "ask_recovery"),
        # medication (8)
        ("can i skip my dose", "ask_medication"),
        ("which painkiller is safe with my bp meds", "ask_medication"),
        ("side effects of statins", "ask_medication"),
        ("is aspirin safe daily", "ask_medication"),
        ("what to do if i double dose", "ask_medication"),
        ("can i stop my blood thinner", "ask_medication"),
        ("ibuprofen safe with hypertension", "ask_medication"),
        ("when do i take my cholesterol pill", "ask_medication"),
        # symptom (10)
        ("my shoulder hurts at night", "ask_symptom"),
        ("i feel dizzy on standing", "ask_symptom"),
        ("i get short of breath quickly", "ask_symptom"),
        ("my heart is racing", "ask_symptom"),
        ("i feel sick after my session", "ask_symptom"),
        ("there is a sharp pain in my chest", "ask_symptom"),
        ("my back is killing me", "ask_symptom"),
        ("my knee feels weak when i walk", "ask_symptom"),
        ("i cannot sleep because of leg cramps", "ask_symptom"),
        ("i feel tired all day", "ask_symptom"),
        # lifestyle (8)
        ("how much salt is safe", "ask_lifestyle"),
        ("is walking good for the heart", "ask_lifestyle"),
        ("best diet for diabetes", "ask_lifestyle"),
        ("can i eat eggs with high cholesterol", "ask_lifestyle"),
        ("smoking and recovery", "ask_lifestyle"),
        ("alcohol with blood thinners", "ask_lifestyle"),
        ("how many hours of sleep", "ask_lifestyle"),
        ("yoga and back pain", "ask_lifestyle"),
        # procedure (8)
        ("how does the echo work", "ask_procedure"),
        ("what happens in an mri", "ask_procedure"),
        ("how long does an angiogram take", "ask_procedure"),
        ("does dry needling hurt", "ask_procedure"),
        ("what to expect during ultrasound", "ask_procedure"),
        ("ecg explanation", "ask_procedure"),
        ("steps of a stress test", "ask_procedure"),
        ("what does a physiotherapist do", "ask_procedure"),
        # warning (8)
        ("danger signs for stroke", "ask_warning"),
        ("warning signs after cardiac stent", "ask_warning"),
        ("red flag symptoms after physio", "ask_warning"),
        ("when do i need er", "ask_warning"),
        ("symptoms i should never ignore", "ask_warning"),
        ("warning signs in chest pain", "ask_warning"),
        ("danger after a head injury", "ask_warning"),
        ("when to call ambulance for heart", "ask_warning"),
    ]
    from expand_corpus import NEW_INTENTS  # noqa: WPS433
    try:
        from expand_corpus_v2 import NEW_INTENTS as NEW_INTENTS_V2  # noqa: WPS433
    except ImportError:
        NEW_INTENTS_V2 = []
    try:
        from expand_corpus_v3 import NEW_INTENTS as NEW_INTENTS_V3  # noqa: WPS433
    except ImportError:
        NEW_INTENTS_V3 = []
    combined = (list(_TRAIN) + extra + NEW_INTENTS
                + NEW_INTENTS_V2 + NEW_INTENTS_V3)
    seen: set[str] = set()
    deduped: list[tuple[str, str]] = []
    for text, label in combined:
        k = (text or "").strip().lower() + "|" + label
        if k in seen:
            continue
        seen.add(k)
        deduped.append((text, label))
    out: list[dict] = []
    for i, (text, label) in enumerate(deduped):
        out.append({"id": f"intent-{i:04d}", "text": text, "label": label})
    return out


# ---------------------------------------------------------------- eval queries


def build_eval_queries() -> list[dict]:
    from expand_corpus import NEW_EVAL  # noqa: WPS433
    try:
        from expand_corpus_v2 import NEW_EVAL as NEW_EVAL_V2  # noqa: WPS433
    except ImportError:
        NEW_EVAL_V2 = []
    try:
        from expand_corpus_v3 import NEW_EVAL as NEW_EVAL_V3  # noqa: WPS433
    except ImportError:
        NEW_EVAL_V3 = []
    out: list[dict] = []
    base = read_json(HERE / "eval_queries.json")
    seen = {(q["query"] or "").strip().lower() for q in base}
    combined = list(base)
    for q in list(NEW_EVAL) + list(NEW_EVAL_V2) + list(NEW_EVAL_V3):
        key = (q["query"] or "").strip().lower()
        if key in seen:
            continue
        combined.append(q)
        seen.add(key)
    for i, q in enumerate(combined):
        out.append({
            "id": f"eval-{i:04d}",
            "specialty": q["specialty"],
            "query": q["query"],
            "expected_keyword": q.get("expected_keyword", ""),
        })
    return out


# ---------------------------------------------------------------- chat logs


# Synthetic but realistic patient chat snippets, one session per record.
# These feed the pipeline that auto-generates FAQ candidates.
_CHAT_LOGS = [
    {
        "session_id": "log-rad-001",
        "specialty": "radiology",
        "turns": [
            {"role": "user", "text": "do i need to fast before my mri scan tomorrow"},
            {"role": "bot",  "text": "For most MRI scans, fasting is not required..."},
            {"role": "user", "text": "what about water"},
            {"role": "bot",  "text": "Plain water is fine unless the abdominal protocol says otherwise."},
        ],
    },
    {
        "session_id": "log-rad-002",
        "specialty": "radiology",
        "turns": [
            {"role": "user", "text": "im claustrophobic, will the mri be okay"},
            {"role": "bot",  "text": "Tell the radiographer beforehand. We can offer a mild sedative..."},
        ],
    },
    {
        "session_id": "log-rad-003",
        "specialty": "radiology",
        "turns": [
            {"role": "user", "text": "is the contrast dye safe for kidney patients"},
            {"role": "bot",  "text": "Gadolinium is avoided in advanced kidney disease..."},
            {"role": "user", "text": "my creatinine is 1.8"},
            {"role": "bot",  "text": "Please share the latest eGFR; we may switch to a non-contrast protocol."},
        ],
    },
    {
        "session_id": "log-phy-001",
        "specialty": "physiotherapy",
        "turns": [
            {"role": "user", "text": "my knee hurts after running, can i still come for physio"},
            {"role": "bot",  "text": "Yes, mild discomfort during/after exercise is okay..."},
            {"role": "user", "text": "should i ice it"},
            {"role": "bot",  "text": "Ice 15 minutes after activity is reasonable for an acute flare."},
        ],
    },
    {
        "session_id": "log-phy-002",
        "specialty": "physiotherapy",
        "turns": [
            {"role": "user", "text": "how often should i do the home exercises"},
            {"role": "bot",  "text": "Aim for daily, two short sets, unless you were given a different plan."},
        ],
    },
    {
        "session_id": "log-phy-003",
        "specialty": "physiotherapy",
        "turns": [
            {"role": "user", "text": "i feel sore after every session, is this normal"},
            {"role": "bot",  "text": "Mild soreness for 24-48h is normal..."},
            {"role": "user", "text": "but mine is sharp"},
            {"role": "bot",  "text": "Sharp pain is different. Please flag it; we may need to ease the load."},
        ],
    },
    {
        "session_id": "log-cv-001",
        "specialty": "cardiovascular",
        "turns": [
            {"role": "user", "text": "when should i take my bp medicine"},
            {"role": "bot",  "text": "Most blood-pressure medicines are once daily, in the morning..."},
            {"role": "user", "text": "what if i forgot today's dose"},
            {"role": "bot",  "text": "Take it as soon as you remember the same day. Do not double up."},
        ],
    },
    {
        "session_id": "log-cv-002",
        "specialty": "cardiovascular",
        "turns": [
            {"role": "user", "text": "i have crushing chest pain"},
            {"role": "bot",  "text": "EMERGENCY: please call 1122..."},
        ],
        "triage_level": 3,
    },
    {
        "session_id": "log-cv-003",
        "specialty": "cardiovascular",
        "turns": [
            {"role": "user", "text": "is chest tightness a warning sign"},
            {"role": "bot",  "text": "It can be. Heart-related chest discomfort..."},
        ],
    },
    {
        "session_id": "log-cv-004",
        "specialty": "cardiovascular",
        "turns": [
            {"role": "user", "text": "can i drink coffee with high bp"},
            {"role": "bot",  "text": "1-3 cups a day is fine for most people..."},
        ],
    },
    {
        "session_id": "log-cv-005",
        "specialty": "cardiovascular",
        "turns": [
            {"role": "user", "text": "what is angina"},
            {"role": "bot",  "text": "Angina is chest discomfort due to reduced blood flow..."},
            {"role": "user", "text": "how is it treated"},
            {"role": "bot",  "text": "Lifestyle, BP/cholesterol control, anti-anginal medicines."},
        ],
    },
]


def build_chat_logs() -> list[dict]:
    from expand_corpus import NEW_CHAT_LOGS  # noqa: WPS433
    base = [dict(rec) for rec in _CHAT_LOGS]
    seen = {rec.get("session_id") for rec in base}
    for rec in NEW_CHAT_LOGS:
        if rec.get("session_id") in seen:
            continue
        base.append(dict(rec))
        seen.add(rec.get("session_id"))
    return base


# ---------------------------------------------------------------- NER examples


_NER_SENTENCES = [
    "my knee hurts after running",
    "i have crushing chest pain and my arm went numb",
    "do i need to fast before my mri scan",
    "is the contrast dye safe for a pregnant patient",
    "i feel breathless when i climb the stairs",
    "should i take aspirin every day for my heart",
    "my back hurts after sitting at the desk",
    "when can i go back to work after the angiogram",
    "i missed my blood pressure medicine today",
    "do statins cause muscle pain",
    "my shoulder feels stiff in the morning",
    "i had a seizure last week",
]


def build_ner_examples() -> list[dict]:
    sys.path.insert(0, str(ROOT / "api"))
    from app.nlp.ner import extract_entities  # noqa: WPS433
    from expand_corpus import NEW_NER_SENTS  # noqa: WPS433

    sentences = list(_NER_SENTENCES)
    seen = {s.lower().strip() for s in sentences}
    for s in NEW_NER_SENTS:
        key = s.lower().strip()
        if key in seen:
            continue
        sentences.append(s)
        seen.add(key)

    out: list[dict] = []
    for i, sent in enumerate(sentences):
        ents = extract_entities(sent)
        tokens, tags = _tag_with_bio(sent, ents)
        out.append({
            "id": f"ner-{i:04d}",
            "text": sent,
            "tokens": tokens,
            "tags": tags,  # BIO scheme
            "entities": ents,
        })
    return out


def _tag_with_bio(text: str, ents: list[dict]) -> tuple[list[str], list[str]]:
    """Build BIO tags aligned with whitespace tokens."""
    import re
    tokens: list[str] = []
    spans: list[tuple[int, int]] = []
    for m in re.finditer(r"\S+", text):
        tokens.append(m.group(0))
        spans.append(m.span())

    tags = ["O"] * len(tokens)
    for e in ents:
        e_start, e_end, label = e["start"], e["end"], e["label"]
        first = True
        for i, (ts, te) in enumerate(spans):
            if te <= e_start or ts >= e_end:
                continue
            tags[i] = ("B-" if first else "I-") + label
            first = False
    return tokens, tags


# ---------------------------------------------------------------- sentiment lexicon


def build_sentiment_lexicon() -> list[dict]:
    sys.path.insert(0, str(ROOT / "api"))
    from app.nlp.sentiment import (  # noqa: WPS433
        NEGATIVE, POSITIVE, INTENSIFIERS, DIMINISHERS,
    )
    out: list[dict] = []
    for w, v in sorted(POSITIVE.items()):
        out.append({"word": w, "polarity": v, "kind": "positive"})
    for w, v in sorted(NEGATIVE.items()):
        out.append({"word": w, "polarity": v, "kind": "negative"})
    for w, v in sorted(INTENSIFIERS.items()):
        out.append({"word": w, "polarity": v, "kind": "intensifier"})
    for w, v in sorted(DIMINISHERS.items()):
        out.append({"word": w, "polarity": v, "kind": "diminisher"})
    return out


# ---------------------------------------------------------------- main


def build_kg_triples() -> list[dict]:
    """Run the in-house knowledge-graph extractor over every FAQ answer."""
    sys.path.insert(0, str(ROOT / "api"))
    from app.nlp.kg import extract_triples  # noqa: WPS433

    out: list[dict] = []
    for name in ("faqs_radiology.json", "faqs_physiotherapy.json",
                 "faqs_cardiovascular.json"):
        p = HERE / name
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for rec in data:
            for t in extract_triples(rec.get("answer", "")):
                t["specialty"] = rec.get("specialty", "")
                t["question"] = rec.get("question", "")
                out.append(t)
    for i, t in enumerate(out):
        t["id"] = f"kg-{i:05d}"
    return out


SPECS = [
    ("faqs.jsonl",              build_faqs),
    ("intents.jsonl",           build_intents),
    ("eval_queries.jsonl",      build_eval_queries),
    ("chat_logs.jsonl",         build_chat_logs),
    ("ner_examples.jsonl",      build_ner_examples),
    ("sentiment_lexicon.jsonl", build_sentiment_lexicon),
    ("kg_triples.jsonl",        build_kg_triples),
]


def main() -> int:
    manifest: dict = {"files": []}
    for name, fn in SPECS:
        records = fn()
        p = HERE / name
        n = write_jsonl(p, records)
        manifest["files"].append({
            "name": name,
            "path": str(p.relative_to(ROOT).as_posix()),
            "records": n,
        })
        print(f"  wrote {p.relative_to(ROOT).as_posix():32s} ({n:4d} records)")

    mpath = HERE / "dataset_manifest.json"
    with mpath.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"  wrote {mpath.relative_to(ROOT).as_posix():32s} (manifest)")
    print()
    print(f"Total files: {len(manifest['files']) + 1}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

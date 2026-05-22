"""Augment intent training data via:

  1. Synonym swaps (medical paraphrases)
  2. Casing / punctuation variants
  3. Light typo injection (transpose 2 adjacent chars)
  4. Prefix variants ("can you tell me", "i need to know", ...)
  5. Politeness wrappers ("please", "thanks if you can")

Produces ``data/intents_augmented.jsonl`` *in addition to* the curated
``intents.jsonl`` so the original stays human-readable and the model
trainer can read both.
"""
from __future__ import annotations

import json
import random
import re
from pathlib import Path

HERE = Path(__file__).parent
SRC = HERE / "intents.jsonl"
DST = HERE / "intents_augmented.jsonl"

# Curated medical synonym map; each entry is symmetric.
SYNONYMS = {
    "mri": ["scan", "imaging"],
    "ct": ["computed tomography", "ct scan"],
    "x-ray": ["xray", "radiograph"],
    "scan": ["test", "imaging"],
    "doctor": ["dr", "physician", "clinician"],
    "physiotherapist": ["physio", "pt", "therapist"],
    "cardiologist": ["heart doctor"],
    "medicine": ["meds", "tablet", "drug"],
    "meds": ["medicine", "tablets", "pills"],
    "bp": ["blood pressure", "hypertension"],
    "chest pain": ["chest discomfort", "tight chest"],
    "knee": ["knee joint"],
    "stretch": ["stretching", "loosen"],
    "exercise": ["workout", "activity"],
    "fast": ["skip food", "avoid eating"],
    "good": ["fine", "ok"],
    "bad": ["awful", "terrible"],
    "lot": ["plenty", "much"],
    "help": ["assist", "guide"],
    "hi": ["hey", "hello"],
    "hello": ["hi", "hey there"],
    "thanks": ["thank you", "thx"],
    "sometimes": ["occasionally", "now and then"],
}

PREFIXES = [
    "", "can you ", "could you ", "please tell me ", "i want to know ",
    "i need to know ", "do you know ", "kindly tell me ",
]

SUFFIXES = [
    "", " please", " kindly", " thanks", " ?", " :)", "...",
]


def _swap_chars(s: str) -> str:
    """Transpose two random adjacent alphabetic characters."""
    chars = list(s)
    pos = [i for i in range(len(chars) - 1)
           if chars[i].isalpha() and chars[i + 1].isalpha()]
    if not pos:
        return s
    i = random.choice(pos)
    chars[i], chars[i + 1] = chars[i + 1], chars[i]
    return "".join(chars)


def _synonym_swap(text: str) -> str:
    toks = re.findall(r"\w+|\W+", text)
    out: list[str] = []
    for t in toks:
        key = t.lower()
        if key in SYNONYMS and random.random() < 0.6:
            out.append(random.choice(SYNONYMS[key]))
        else:
            out.append(t)
    return "".join(out)


def _phrase_swap(text: str) -> str:
    t = text.lower()
    for phrase, alts in SYNONYMS.items():
        if " " in phrase and phrase in t and random.random() < 0.5:
            return t.replace(phrase, random.choice(alts), 1)
    return text


def _augment_one(text: str, label: str, rng: random.Random) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    # 1. Synonym swap
    out.append((_synonym_swap(text), label))
    # 2. Phrase-level swap
    out.append((_phrase_swap(text), label))
    # 3. Prefix variant
    out.append((rng.choice(PREFIXES) + text, label))
    # 4. Casing change (sentence case)
    out.append((text.capitalize(), label))
    # 5. Mild typo (only on long enough strings)
    if len(text) > 6:
        out.append((_swap_chars(text), label))
    # 6. Combined prefix + suffix
    out.append((rng.choice(PREFIXES) + text + rng.choice(SUFFIXES), label))
    return out


def main() -> None:
    if not SRC.is_file():
        raise SystemExit(f"missing {SRC}")
    rng = random.Random(42)
    # Load source.
    rows: list[tuple[str, str]] = []
    with SRC.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "text" in rec and "label" in rec:
                rows.append((rec["text"], rec["label"]))
    # Augment.
    extras: list[tuple[str, str]] = []
    for text, label in rows:
        extras.extend(_augment_one(text, label, rng))
    # Dedup the union.
    seen: set[tuple[str, str]] = set()
    out_rows: list[tuple[str, str]] = []
    for text, label in rows + extras:
        t2 = text.strip()
        if not t2:
            continue
        key = (t2.lower(), label)
        if key in seen:
            continue
        seen.add(key)
        out_rows.append((t2, label))

    with DST.open("w", encoding="utf-8") as f:
        for i, (text, label) in enumerate(out_rows):
            f.write(json.dumps(
                {"id": f"aug-{i:05d}", "text": text, "label": label},
                ensure_ascii=False) + "\n")
    print(f"  base    : {len(rows)}")
    print(f"  augmented (after dedup): {len(out_rows)}")
    print(f"  multiplier: {len(out_rows) / max(1, len(rows)):.2f}x")
    print(f"  wrote {DST.relative_to(HERE.parent).as_posix()}")


if __name__ == "__main__":
    main()

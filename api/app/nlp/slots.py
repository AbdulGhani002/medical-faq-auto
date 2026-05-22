"""Slot extraction for the dialog manager.

A slot is a labelled value the bot keeps in conversation state. We pull
slots from NER output and a couple of light regexes. Used to detect
missing information ("which body part?") and to disambiguate follow-ups.
"""
from __future__ import annotations

import re

from .ner import extract_entities


_FREQUENCY = re.compile(
    r"\b(\d+)\s*(?:times|x)\s*(?:a|per)\s*(day|week|month)\b",
    re.I,
)
_DURATION = re.compile(
    r"\b(\d+)\s*(minute|minutes|hour|hours|day|days|week|weeks|month|months|year|years)\b",
    re.I,
)
_AGE = re.compile(r"\b(\d{1,3})\s*(?:years? old|y/o)\b", re.I)


def extract_slots(text: str) -> dict:
    ents = extract_entities(text)
    slots: dict = {
        "body_part": None,
        "symptom": None,
        "condition": None,
        "drug": None,
        "procedure": None,
        "person": None,
        "duration": None,
        "frequency": None,
        "age": None,
        "entities": ents,
    }
    for e in ents:
        if e["label"] == "BODY" and not slots["body_part"]:
            slots["body_part"] = e["text"].lower()
        elif e["label"] == "SYMPTOM" and not slots["symptom"]:
            slots["symptom"] = e["text"].lower()
        elif e["label"] == "CONDITION" and not slots["condition"]:
            slots["condition"] = e["text"].lower()
        elif e["label"] == "DRUG" and not slots["drug"]:
            slots["drug"] = e["text"].lower()
        elif e["label"] == "PROCEDURE" and not slots["procedure"]:
            slots["procedure"] = e["text"].lower()
        elif e["label"] == "PERSON" and not slots["person"]:
            slots["person"] = e["text"].lower()

    m = _FREQUENCY.search(text or "")
    if m:
        slots["frequency"] = f"{m.group(1)}x per {m.group(2).lower()}"

    m = _DURATION.search(text or "")
    if m:
        slots["duration"] = f"{m.group(1)} {m.group(2).lower()}"

    m = _AGE.search(text or "")
    if m:
        slots["age"] = int(m.group(1))

    return slots


def merge(prev: dict | None, new: dict) -> dict:
    """Carry over previous slot values when the new message did not
    repopulate them. Helps multi-turn coreference."""
    out = dict(new)
    if not prev:
        return out
    for k, v in prev.items():
        if k == "entities":
            continue
        if not out.get(k) and v:
            out[k] = v
    return out

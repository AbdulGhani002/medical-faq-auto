"""Knowledge-graph triple extractor.

Given a POS-tagged sentence with noun-phrase chunks, extract simple
(subject, predicate, object) triples by walking the chunk sequence:

    NP_left  VP  NP_right

with simple heuristics for negation ("MRI does *not* damage cells") and
auxiliary chains ("a CT *can* show bone").

We also expose ``extract_for_corpus`` which streams every FAQ answer
through the sentence splitter + chunker + triple extractor to produce a
mini KG over the whole specialty corpus, written to
``data/kg_triples.jsonl``.

This is the same shallow-extraction approach used in classical IE
pipelines (Reverb, OLLIE) before transformer-based OpenIE took over.
No LLM. No transformer.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .chunker import noun_phrases, verb_phrases
from .hmm_pos import hmm_tag
from .negation import is_negated


_SENT_RE = re.compile(r"(?<=[.!?])\s+")


def _tokenise(text: str) -> list[str]:
    return [m.group(0) for m in re.finditer(r"[A-Za-z][A-Za-z0-9'-]*", text)]


def extract_triples(text: str) -> list[dict]:
    """Return a list of {subject, predicate, object, negated, sentence}.

    A triple fires when a noun-phrase precedes a verb-phrase that
    precedes another noun-phrase, all in the same sentence.
    """
    out: list[dict] = []
    for sent in _SENT_RE.split(text or ""):
        sent = sent.strip()
        if not sent or len(sent) < 6:
            continue
        toks = _tokenise(sent)
        if len(toks) < 3:
            continue
        tagged = hmm_tag(toks)
        nps = noun_phrases(tagged)
        vps = verb_phrases(tagged)
        if len(nps) < 2 or not vps:
            continue
        # Walk chunks left to right.
        for i, vp in enumerate(vps):
            # subject = nearest NP that ends before this VP starts
            subj = None
            for np_ in reversed(nps):
                if np_["end_tok"] <= vp["start_tok"]:
                    subj = np_
                    break
            if subj is None:
                continue
            # object = nearest NP that starts after this VP ends
            obj = None
            for np_ in nps:
                if np_["start_tok"] >= vp["end_tok"]:
                    obj = np_
                    break
            if obj is None:
                continue
            triple = {
                "subject": subj["text"],
                "predicate": vp["text"],
                "object": obj["text"],
                "negated": is_negated(sent),
                "sentence": sent,
            }
            out.append(triple)
    return out


# ---------- corpus-level dump ----------


def extract_for_corpus(limit: int | None = None) -> dict:
    """Walk all FAQs and write triples to ``data/kg_triples.jsonl``.

    Returns a summary dict with counts.
    """
    repo_root = Path(__file__).resolve().parents[3]
    out_path = repo_root / "data" / "kg_triples.jsonl"

    all_triples: list[dict] = []
    sources = ("faqs_radiology.json", "faqs_physiotherapy.json",
               "faqs_cardiovascular.json")
    for name in sources:
        p = repo_root / "data" / name
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
        for rec in data:
            for t in extract_triples(rec.get("answer", "")):
                t["specialty"] = rec.get("specialty", "")
                t["question"] = rec.get("question", "")
                all_triples.append(t)
                if limit and len(all_triples) >= limit:
                    break

    with out_path.open("w", encoding="utf-8") as f:
        for i, t in enumerate(all_triples):
            t["id"] = f"kg-{i:05d}"
            f.write(json.dumps(t, ensure_ascii=False) + "\n")
    return {
        "n_triples": len(all_triples),
        "output": str(out_path.relative_to(repo_root).as_posix()),
        "per_specialty": _per_spec_counts(all_triples),
    }


def _per_spec_counts(triples: list[dict]) -> dict[str, int]:
    out: dict[str, int] = {}
    for t in triples:
        s = t.get("specialty", "")
        out[s] = out.get(s, 0) + 1
    return out

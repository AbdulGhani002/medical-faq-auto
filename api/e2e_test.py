"""End-to-end smoke test for the NLP chatbot.

Hits the running API on localhost:8000 and exercises every NLP feature.
Writes pretty-printed results to e2e_results.json + a markdown summary.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

API = "http://127.0.0.1:8000"


def _post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        API + path,
        data=data,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(path: str) -> dict:
    with urllib.request.urlopen(API + path, timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


SCENARIOS = [
    # 1. Chitchat / canned reply.
    {
        "name": "greeting",
        "specialty": "cardiovascular",
        "session": "scen-greet",
        "turns": ["hi there"],
        "expect": {"intent": "greeting"},
    },
    # 2. Frustration.
    {
        "name": "frustration",
        "specialty": "cardiovascular",
        "session": "scen-frust",
        "turns": ["this is useless"],
        "expect": {"intent": "frustration"},
    },
    # 3. Definition.
    {
        "name": "definition",
        "specialty": "cardiovascular",
        "session": "scen-def",
        "turns": ["what is angina?"],
        "expect": {"intent": "question", "matched_contains": "angina"},
    },
    # 4. Preparation (radiology).
    {
        "name": "radiology_prep",
        "specialty": "radiology",
        "session": "scen-rad",
        "turns": ["Do I need to fast before my MRI?"],
        "expect": {"matched_contains": "MRI"},
    },
    # 5. Emergency triage.
    {
        "name": "emergency_triage",
        "specialty": "cardiovascular",
        "session": "scen-911",
        "turns": ["I have crushing chest pain and my arm is numb"],
        "expect": {"triage_level": 3},
    },
    # 6. Moderate urgency.
    {
        "name": "moderate_urgency",
        "specialty": "cardiovascular",
        "session": "scen-mod",
        "turns": ["I have sudden shortness of breath today"],
        "expect": {"triage_level_min": 1},
    },
    # 7. Distressed sentiment.
    {
        "name": "distressed",
        "specialty": "cardiovascular",
        "session": "scen-distress",
        "turns": ["I'm really worried, my heart races all the time"],
        "expect": {"sentiment_label": "negative"},
    },
    # 8. Spell correction.
    {
        "name": "spelling",
        "specialty": "physiotherapy",
        "session": "scen-spell",
        "turns": ["my knne hurts after runing"],
        "expect": {"spell_corrections_min": 1},
    },
    # 9. Negation handling (should still find chest pain FAQ).
    {
        "name": "negation",
        "specialty": "cardiovascular",
        "session": "scen-neg",
        "turns": ["I do not have any chest pain right now"],
        "expect": {"negation_count_min": 1},
    },
    # 10. Multi-turn pronoun resolution.
    {
        "name": "multi_turn_coref",
        "specialty": "cardiovascular",
        "session": "scen-coref",
        "turns": [
            "What is angina?",
            "How do I treat it?",
        ],
        "expect": {"coref_count_min": 1},
    },
    # 11. Follow-up "tell me more".
    {
        "name": "tell_me_more",
        "specialty": "physiotherapy",
        "session": "scen-more",
        "turns": [
            "How often should I do my home exercises?",
            "tell me more",
        ],
        "expect": {"matched_contains": "exercise"},
    },
    # 12. NER + slot filling.
    {
        "name": "slot_filling",
        "specialty": "cardiovascular",
        "session": "scen-slot",
        "turns": ["Can I take aspirin every day for my heart?"],
        "expect": {"slot_drug": True},
    },
    # 13. Question type "why".
    {
        "name": "why_question",
        "specialty": "cardiovascular",
        "session": "scen-why",
        "turns": ["Why do I get dizzy when I stand up?"],
        "expect": {"question_type": "why"},
    },
    # 14. Synonym expansion (BP -> blood pressure).
    {
        "name": "synonyms",
        "specialty": "cardiovascular",
        "session": "scen-syn",
        "turns": ["when should I take my BP medicine?"],
        "expect": {"matched_contains": "blood pressure"},
    },
    # 15. LSA topic vs literal lexical mismatch.
    {
        "name": "lsa_topic",
        "specialty": "cardiovascular",
        "session": "scen-lsa",
        "turns": ["how to eat for my heart"],
        "expect": {"matched_contains": ""},  # any match
    },
]


def evaluate(scn: dict, results: list[dict]) -> tuple[bool, str]:
    last = results[-1]
    checks = []
    exp = scn["expect"]
    if "intent" in exp:
        ok = last.get("intent") == exp["intent"]
        checks.append((f"intent={exp['intent']}", ok, last.get("intent")))
    if "matched_contains" in exp:
        mq = (last.get("matched_question") or "").lower()
        ok = exp["matched_contains"].lower() in mq if exp["matched_contains"] else bool(mq)
        checks.append((f"matched contains '{exp['matched_contains']}'", ok, mq))
    if "triage_level" in exp:
        ok = (last.get("dialog") or {}).get("triage_level") == exp["triage_level"]
        checks.append((f"triage={exp['triage_level']}", ok, (last.get("dialog") or {}).get("triage_level")))
    if "triage_level_min" in exp:
        v = (last.get("dialog") or {}).get("triage_level", 0)
        ok = v >= exp["triage_level_min"]
        checks.append((f"triage>={exp['triage_level_min']}", ok, v))
    if "sentiment_label" in exp:
        v = ((last.get("nlp") or {}).get("sentiment") or {}).get("label")
        ok = v == exp["sentiment_label"]
        checks.append((f"sentiment={exp['sentiment_label']}", ok, v))
    if "spell_corrections_min" in exp:
        v = len(last.get("spell_corrections") or [])
        ok = v >= exp["spell_corrections_min"]
        checks.append((f"spell>={exp['spell_corrections_min']}", ok, v))
    if "negation_count_min" in exp:
        v = len(((last.get("nlp") or {}).get("negations") or []))
        ok = v >= exp["negation_count_min"]
        checks.append((f"neg>={exp['negation_count_min']}", ok, v))
    if "coref_count_min" in exp:
        v = len((last.get("dialog") or {}).get("coref") or [])
        ok = v >= exp["coref_count_min"]
        checks.append((f"coref>={exp['coref_count_min']}", ok, v))
    if "slot_drug" in exp:
        v = (((last.get("nlp") or {}).get("slots") or {}).get("drug"))
        ok = bool(v) == exp["slot_drug"]
        checks.append((f"drug-slot={exp['slot_drug']}", ok, v))
    if "question_type" in exp:
        v = ((last.get("nlp") or {}).get("question_type"))
        ok = v == exp["question_type"]
        checks.append((f"qtype={exp['question_type']}", ok, v))

    all_ok = all(c[1] for c in checks)
    summary = "; ".join(
        f"{name}={'OK' if ok else f'FAIL({got})'}" for name, ok, got in checks
    )
    return all_ok, summary


def main() -> int:
    print("Probing API health...")
    h = _get("/health")
    print(f"  health: {h}")

    out: list[dict] = []
    fails = 0

    for scn in SCENARIOS:
        # Always reset per-scenario session.
        try:
            _post(f"/chat/reset/{scn['session']}", {})
        except urllib.error.HTTPError:
            pass

        per_turn: list[dict] = []
        for t in scn["turns"]:
            resp = _post("/chat", {
                "session_id": scn["session"],
                "specialty": scn["specialty"],
                "text": t,
            })
            per_turn.append(resp)

        ok, summary = evaluate(scn, per_turn)
        status = "PASS" if ok else "FAIL"
        if not ok:
            fails += 1
        print(f"  {status:4s} {scn['name']:20s} - {summary}")

        out.append({
            "name": scn["name"],
            "specialty": scn["specialty"],
            "turns": scn["turns"],
            "expect": scn["expect"],
            "summary": summary,
            "passed": ok,
            "last_response": per_turn[-1],
        })

    # NLP analyse-only endpoint sample.
    sample = _post("/nlp/analyze", {
        "text": "My knee hurts a lot after running, I'm really worried."})
    print(
        f"  /nlp/analyze sample: intent={sample['intent']['label']} "
        f"sentiment={sample['sentiment']['label']} "
        f"entities={[e['text']+'/'+e['label'] for e in sample['entities']]}"
    )

    repo = Path(__file__).parent.parent
    (repo / "e2e_results.json").write_text(
        json.dumps({"scenarios": out, "analyze_sample": sample}, indent=2),
        encoding="utf-8",
    )

    print()
    print(f"Total: {len(SCENARIOS)} | Pass: {len(SCENARIOS) - fails} | Fail: {fails}")
    return 0 if fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

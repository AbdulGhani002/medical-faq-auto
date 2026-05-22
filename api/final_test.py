"""Comprehensive end-to-end test for the whole stack.

Exercises everything added across both upgrade waves:

  - API /health, /chat, /chat/reset, /chat/state, /chat/history,
    /nlp/analyze, /nlp/health, /nlp/datasets, /nlp/datasets/{name}
  - /stats/overview, /stats/chat_distribution/{specialty}
  - /faq/{specialty}
  - All 15 chat scenarios (e2e_test.py contents)
  - Retrieval eval (eval.py contents) -- imports run_once()
  - MMR diversity check (alternatives must be distinct FAQ ids)
  - Roman-Urdu translation produces non-empty edits and a real match
  - Frontend routes (home, /playground, /admin, /chat/cardiovascular,
    /faq/radiology) return HTTP 200

Prints a final summary block. Returns non-zero if any check fails.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

API = "http://127.0.0.1:8000"
WEB = "http://127.0.0.1:3000"
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from e2e_test import SCENARIOS, evaluate  # noqa: E402
from eval import run_once as eval_run_once  # noqa: E402


PASS = "PASS"
FAIL = "FAIL"


def _get(path: str, base: str = API) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(base + path, timeout=20) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, str(e)


def _post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        API + path,
        data=data,
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


class Suite:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passes: list[str] = []

    def check(self, name: str, ok: bool, detail: str = "") -> None:
        if ok:
            self.passes.append(name)
            print(f"  {PASS} {name:46s} {detail}")
        else:
            self.failures.append(name)
            print(f"  {FAIL} {name:46s} {detail}")

    def summary(self) -> int:
        total = len(self.passes) + len(self.failures)
        print()
        print(f"  Total: {total} | Pass: {len(self.passes)} | "
              f"Fail: {len(self.failures)}")
        return 0 if not self.failures else 1


def test_api_health(s: Suite) -> None:
    code, body = _get("/health")
    s.check("GET /health -> 200", code == 200, body.strip())

    code, body = _get("/nlp/health")
    s.check("GET /nlp/health -> 200", code == 200, body.strip())
    s.check("NB intent loaded from JSONL",
            '"nb_intent_source":"jsonl"' in body, body.strip())

    # New advanced-NLP endpoints
    try:
        r = _post("/nlp/perplexity", {"text": "what is angina"})
        s.check("POST /nlp/perplexity returns numeric perplexity",
                isinstance(r.get("perplexity"), (int, float)))
    except Exception as e:
        s.check("POST /nlp/perplexity -> 200", False, str(e))
    try:
        r = _post("/nlp/autocomplete?k=3", {"text": "what is"})
        s.check("POST /nlp/autocomplete returns suggestions",
                len(r.get("suggestions", [])) > 0)
    except Exception as e:
        s.check("POST /nlp/autocomplete -> 200", False, str(e))
    try:
        r = _post("/nlp/chunks",
                  {"text": "my chest hurts after running"})
        s.check("POST /nlp/chunks returns NPs",
                len(r.get("noun_phrases", [])) > 0)
    except Exception as e:
        s.check("POST /nlp/chunks -> 200", False, str(e))
    try:
        r = _post("/nlp/triples",
                  {"text": "Aspirin prevents heart attacks for many people"})
        s.check("POST /nlp/triples returns list",
                isinstance(r.get("triples"), list))
    except Exception as e:
        s.check("POST /nlp/triples -> 200", False, str(e))
    code, body = _get("/nlp/triples_dump?limit=2&specialty=radiology")
    s.check("GET /nlp/triples_dump -> 200", code == 200)
    s.check("triples dump returns triples",
            '"subject"' in body)


def test_chat_scenarios(s: Suite) -> None:
    print()
    print("  --- chat scenarios ---")
    fails = 0
    for scn in SCENARIOS:
        try:
            _post(f"/chat/reset/{scn['session']}", {})
        except urllib.error.HTTPError:
            pass
        per_turn = []
        for t in scn["turns"]:
            resp = _post("/chat", {
                "session_id": scn["session"],
                "specialty": scn["specialty"],
                "text": t,
            })
            per_turn.append(resp)
        ok, summary = evaluate(scn, per_turn)
        s.check(f"scenario {scn['name']}", ok, summary)
        if not ok:
            fails += 1


def test_evaluation_harness(s: Suite) -> None:
    print()
    print("  --- retrieval evaluation ---")
    queries_path = ROOT / "data" / "eval_queries.jsonl"
    queries = []
    with queries_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                queries.append(json.loads(line))

    report = eval_run_once(queries)
    o = report["overall"]
    s.check("Precision@1 >= 0.85", o["precision_at_1"] >= 0.85,
            f"{o['precision_at_1']:.3f}")
    s.check("MRR >= 0.85", o["mrr"] >= 0.85, f"{o['mrr']:.3f}")
    s.check("Recall@5 >= 0.90", o["recall_at_5"] >= 0.90,
            f"{o['recall_at_5']:.3f}")
    s.check("Median latency < 100 ms",
            o["median_latency_s"] < 0.1,
            f"{o['median_latency_s']*1000:.1f} ms")


def test_mmr_diversity(s: Suite) -> None:
    print()
    print("  --- MMR diversity ---")
    resp = _post("/chat", {
        "session_id": "mmr-check",
        "specialty": "cardiovascular",
        "text": "is chest pain a heart attack",
    })
    alts = resp.get("alternatives") or []
    ids = [a["id"] for a in alts]
    s.check("alternatives are distinct FAQ ids",
            len(ids) == len(set(ids)) and len(ids) >= 1,
            f"{len(ids)} alts, unique={len(set(ids))}")


def test_roman_urdu(s: Suite) -> None:
    print()
    print("  --- Roman-Urdu ---")
    resp = _post("/chat", {
        "session_id": "ru-check",
        "specialty": "cardiovascular",
        "text": "sar mein dard ho raha hai aur seenay mein bhi",
    })
    edits = (resp.get("dialog") or {}).get("roman_urdu") or []
    matched = resp.get("matched_question") or ""
    s.check("Roman-Urdu edits produced", len(edits) >= 3,
            f"{len(edits)} edits")
    s.check("Roman-Urdu query matched a real FAQ",
            bool(matched), matched[:60])


def test_introspection_endpoints(s: Suite) -> None:
    print()
    print("  --- introspection endpoints ---")
    code, _ = _get("/nlp/datasets")
    s.check("GET /nlp/datasets -> 200", code == 200)
    code, _ = _get("/nlp/datasets/faqs.jsonl?n=2")
    s.check("GET /nlp/datasets/faqs.jsonl?n=2 -> 200", code == 200)
    code, _ = _get("/stats/overview")
    s.check("GET /stats/overview -> 200", code == 200)
    code, body = _get("/stats/chat_distribution/cardiovascular?limit=100")
    s.check("GET /stats/chat_distribution/cardiovascular -> 200",
            code == 200)
    if code == 200:
        d = json.loads(body)
        s.check("chat distribution returns intent counts",
                "intent" in d and isinstance(d["intent"], list),
                f"intent items={len(d.get('intent', []))}")


def test_session_history(s: Suite) -> None:
    print()
    print("  --- session lifecycle ---")
    sid = "lifecycle-check"
    try:
        _post(f"/chat/reset/{sid}", {})
    except urllib.error.HTTPError:
        pass
    _post("/chat", {"session_id": sid, "specialty": "radiology",
                    "text": "do i need to fast before my mri"})
    _post("/chat", {"session_id": sid, "specialty": "radiology",
                    "text": "what about water"})
    code, body = _get(f"/chat/history/{sid}")
    s.check("GET /chat/history/{sid} -> 200", code == 200)
    if code == 200:
        d = json.loads(body)
        turns = d.get("turns", [])
        s.check("history has at least 4 turns (2 user + 2 bot)",
                len(turns) >= 4, f"{len(turns)} turns")


def test_frontend_routes(s: Suite) -> None:
    print()
    print("  --- frontend routes (http://localhost:3000) ---")
    for path in ("/", "/playground", "/architecture", "/admin",
                 "/chat/cardiovascular", "/faq/radiology"):
        code, body = _get(path, base=WEB)
        s.check(f"GET {path} -> 200", code == 200, str(code))
    # Spot-check that the chat page no longer claims "Pure BM25" and the
    # architecture page mentions every retrieval channel.
    _, chat_html = _get("/chat/cardiovascular", base=WEB)
    s.check("chat page does NOT say 'Pure BM25'",
            "Pure BM25" not in chat_html)
    s.check("chat page mentions PPMI",
            "PPMI" in chat_html)
    _, arch_html = _get("/architecture", base=WEB)
    for needle in ("TF-IDF", "BM25", "LSA", "PPMI",
                   "Statistical NER", "LTR rerank", "MMR"):
        s.check(f"architecture page mentions '{needle}'",
                needle in arch_html)


def test_pipeline_output(s: Suite) -> None:
    print()
    print("  --- pipeline output ---")
    cand = ROOT / "data" / "faq_candidates.jsonl"
    s.check("data/faq_candidates.jsonl exists", cand.is_file())
    if cand.is_file():
        n = 0
        with cand.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    n += 1
        s.check("pipeline produced candidates (>= 1)", n >= 1,
                f"{n} candidates")


def test_unit_tests(s: Suite) -> None:
    import subprocess
    print()
    print("  --- pytest unit suite ---")
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/"],
        cwd=str(ROOT / "api"), capture_output=True, text=True,
    )
    tail = (r.stdout or "").strip().splitlines()[-1] if r.stdout else ""
    s.check("pytest tests/ all pass", r.returncode == 0, tail)


def test_ablation_artifacts(s: Suite) -> None:
    print()
    print("  --- ablation artifacts ---")
    for name in ("ABLATION_REPORT.md", "ablation_results.json"):
        s.check(f"{name} exists", (ROOT / name).is_file())


def test_intent_eval_artifacts(s: Suite) -> None:
    print()
    print("  --- intent eval artifacts ---")
    for name in ("INTENT_EVAL.md", "intent_eval.json"):
        s.check(f"{name} exists", (ROOT / name).is_file())


def test_statistical_ner(s: Suite) -> None:
    print()
    print("  --- statistical NER ---")
    from app.nlp.ner_stat import (
        train_default, evaluate, _load_gold_jsonl,
    )
    m = train_default()
    gold = _load_gold_jsonl()
    examples = [(toks, tags, " ".join(toks)) for toks, tags in gold]
    metrics = evaluate(m, examples)
    s.check("statistical NER F1 >= 0.80 on gold",
            metrics["f1"] >= 0.80, f"F1={metrics['f1']}")
    pred = m.predict_entities("my knee hurts after running")
    s.check("statistical NER finds at least one entity",
            len(pred) >= 1, f"{len(pred)} entities")


def main() -> int:
    print("=" * 60)
    print("Medical FAQ Chatbot - final test sweep")
    print("=" * 60)
    t0 = time.perf_counter()
    s = Suite()

    test_api_health(s)
    test_introspection_endpoints(s)
    test_chat_scenarios(s)
    test_mmr_diversity(s)
    test_roman_urdu(s)
    test_session_history(s)
    test_evaluation_harness(s)
    test_statistical_ner(s)
    test_ablation_artifacts(s)
    test_intent_eval_artifacts(s)
    test_unit_tests(s)
    test_frontend_routes(s)
    test_pipeline_output(s)

    dt = time.perf_counter() - t0
    print()
    print(f"Suite finished in {dt:.1f}s")
    return s.summary()


if __name__ == "__main__":
    sys.exit(main())

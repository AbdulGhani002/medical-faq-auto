"""Evaluation harness.

Runs every query in ``data/eval_queries.jsonl`` against the live API and
reports:

  - Precision@1
  - MRR (Mean Reciprocal Rank)
  - Recall@5
  - Median + p95 latency
  - Per-specialty breakdown

Writes ``eval_results.json`` and an updatable ``EVALUATION_REPORT.md``.

Usage:
    cd api && python eval.py
"""
from __future__ import annotations

import argparse
import json
import statistics
import time
import urllib.error
import urllib.request
from collections import defaultdict
from pathlib import Path


API = "http://127.0.0.1:8000"
HERE = Path(__file__).parent
ROOT = HERE.parent


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


def _load_eval() -> list[dict]:
    path = ROOT / "data" / "eval_queries.jsonl"
    out: list[dict] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def _is_hit(answer: str, expected_keyword: str) -> bool:
    if not expected_keyword:
        return True
    return expected_keyword.lower() in (answer or "").lower()


def _rank_of_hit(resp: dict, expected_keyword: str) -> int | None:
    if not expected_keyword:
        return 1
    # Hit if the keyword appears in the chosen FAQ's question OR answer.
    if _is_hit(resp.get("answer", ""), expected_keyword) or _is_hit(
        resp.get("matched_question", ""), expected_keyword
    ):
        return 1
    for i, a in enumerate(resp.get("alternatives") or [], start=2):
        if _is_hit(a.get("question", ""), expected_keyword):
            return i
    return None


def run_once(queries: list[dict]) -> dict:
    results = []
    latencies: list[float] = []
    per_specialty: dict[str, list[dict]] = defaultdict(list)
    hits1 = 0
    recall5 = 0
    rr_sum = 0.0

    for q in queries:
        sid = "eval-" + (q.get("id") or q["query"][:20])
        try:
            _post(f"/chat/reset/{sid}", {})
        except urllib.error.HTTPError:
            pass

        t0 = time.perf_counter()
        try:
            resp = _post("/chat", {
                "session_id": sid,
                "specialty": q["specialty"],
                "text": q["query"],
            })
        except urllib.error.HTTPError as e:
            print(f"  ! HTTP {e.code} on {q['query']!r}")
            continue
        dt = time.perf_counter() - t0
        latencies.append(dt)

        rank = _rank_of_hit(resp, q.get("expected_keyword", ""))
        is_h1 = rank == 1
        is_h5 = rank is not None and rank <= 5

        if is_h1:
            hits1 += 1
        if is_h5:
            recall5 += 1
        if rank is not None:
            rr_sum += 1.0 / rank

        row = {
            "id": q.get("id"),
            "specialty": q["specialty"],
            "query": q["query"],
            "expected": q.get("expected_keyword", ""),
            "matched_question": resp.get("matched_question"),
            "confidence": resp.get("confidence"),
            "rank": rank,
            "hit@1": is_h1,
            "hit@5": is_h5,
            "latency_s": round(dt, 3),
        }
        per_specialty[q["specialty"]].append(row)
        results.append(row)

    n = len(results) or 1
    overall = {
        "n": len(results),
        "precision_at_1": round(hits1 / n, 3),
        "recall_at_5": round(recall5 / n, 3),
        "mrr": round(rr_sum / n, 3),
        "median_latency_s": round(
            statistics.median(latencies) if latencies else 0.0, 3),
        "p95_latency_s": round(_p95(latencies), 3),
    }

    by_spec = {}
    for spec, rows in per_specialty.items():
        nn = len(rows) or 1
        by_spec[spec] = {
            "n": len(rows),
            "precision_at_1": round(sum(r["hit@1"] for r in rows) / nn, 3),
            "recall_at_5": round(sum(r["hit@5"] for r in rows) / nn, 3),
            "mrr": round(
                sum(1.0 / r["rank"] for r in rows if r["rank"]) / nn, 3),
        }

    return {"overall": overall, "per_specialty": by_spec, "rows": results}


def _p95(xs: list[float]) -> float:
    if not xs:
        return 0.0
    s = sorted(xs)
    idx = max(0, min(len(s) - 1, int(round(0.95 * (len(s) - 1)))))
    return s[idx]


def write_markdown(report: dict, path: Path) -> None:
    o = report["overall"]
    lines = ["# Retrieval evaluation report", ""]
    lines.append(
        "| Metric | Value |\n|---|---:|\n"
        f"| Precision@1 | **{o['precision_at_1']:.3f}** |\n"
        f"| MRR | **{o['mrr']:.3f}** |\n"
        f"| Recall@5 | **{o['recall_at_5']:.3f}** |\n"
        f"| Median latency | {o['median_latency_s']*1000:.1f} ms |\n"
        f"| p95 latency | {o['p95_latency_s']*1000:.1f} ms |\n"
        f"| Queries | {o['n']} |\n"
    )
    lines.append("")
    lines.append("## Per-specialty breakdown")
    lines.append("")
    lines.append("| Specialty | n | P@1 | Recall@5 | MRR |")
    lines.append("|---|---:|---:|---:|---:|")
    for spec, m in sorted(report["per_specialty"].items()):
        lines.append(
            f"| {spec} | {m['n']} | {m['precision_at_1']:.3f} | "
            f"{m['recall_at_5']:.3f} | {m['mrr']:.3f} |"
        )
    lines.append("")
    lines.append("## Failed queries (rank > 1)")
    fails = [r for r in report["rows"] if not r["hit@1"]]
    if not fails:
        lines.append("None — every query hit the top FAQ.")
    else:
        lines.append("")
        lines.append("| Query | Expected | Matched | Rank |")
        lines.append("|---|---|---|---:|")
        for r in fails[:30]:
            lines.append(
                f"| {r['query']} | `{r['expected']}` | "
                f"{(r.get('matched_question') or '—')[:60]} | "
                f"{r['rank'] if r['rank'] else '—'} |"
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    global API
    parser = argparse.ArgumentParser()
    parser.add_argument("--api", default=API)
    args = parser.parse_args()
    API = args.api

    queries = _load_eval()
    print(f"Loaded {len(queries)} eval queries")
    print("Running...")
    report = run_once(queries)

    o = report["overall"]
    print()
    print(f"  Precision@1 : {o['precision_at_1']:.3f}")
    print(f"  Recall@5    : {o['recall_at_5']:.3f}")
    print(f"  MRR         : {o['mrr']:.3f}")
    print(f"  Latency p50 : {o['median_latency_s']*1000:.1f} ms")
    print(f"  Latency p95 : {o['p95_latency_s']*1000:.1f} ms")
    print()
    for spec, m in sorted(report["per_specialty"].items()):
        print(
            f"  {spec:14s} n={m['n']:2d}  P@1={m['precision_at_1']:.3f}  "
            f"R@5={m['recall_at_5']:.3f}  MRR={m['mrr']:.3f}"
        )

    out_json = ROOT / "eval_results.json"
    out_md = ROOT / "EVALUATION_REPORT.md"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, out_md)
    print()
    print(f"Wrote {out_json.relative_to(ROOT).as_posix()}")
    print(f"Wrote {out_md.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Ablation study for the retrieval pipeline.

Runs the eval queries through the lexical retriever with each scoring
channel zeroed in turn. Tabulates the marginal contribution of each
NLP component, so a viva committee can see hard numbers for every
classical-NLP module that ships with this project.

Output: ABLATION_REPORT.md + ablation_results.json
Usage : python ablate.py
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

# Force the in-memory store so we don't depend on Mongo.
os.environ.setdefault("FAQ_FORCE_MEMORY", "1")

from app.db import get_db  # noqa: E402
from app.nlp import HybridIndex  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


CHANNELS = ["tfidf_word", "tfidf_char", "bm25", "lsa", "embed"]

# Baseline weights from indexer.py top_k().
BASELINE = {
    "tfidf_word": 0.20, "tfidf_char": 0.45,
    "bm25": 0.25, "lsa": 0.05, "embed": 0.05,
}


def _load_eval() -> list[dict]:
    out: list[dict] = []
    p = ROOT / "data" / "eval_queries.jsonl"
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


async def _load_faqs() -> dict[str, list[dict]]:
    db = get_db()
    by_spec: dict[str, list[dict]] = {}
    for spec in ("radiology", "physiotherapy", "cardiovascular"):
        cur = db.faqs.find({"specialty": spec, "approved": True})
        docs: list[dict] = []
        async for d in cur:
            docs.append(d)
        by_spec[spec] = docs
    return by_spec


def _is_hit(text: str, kw: str) -> bool:
    return bool(kw) and kw.lower() in (text or "").lower()


def _rank(idx: HybridIndex, faqs: list[dict], query: str, kw: str,
          weights: dict) -> int | None:
    """Return 1-based rank of the first hit using these weights."""
    scored = idx.top_k(query, k=10, weights=weights)
    for r, (i, _s, _per) in enumerate(scored, start=1):
        f = faqs[i]
        if _is_hit(f["answer"], kw) or _is_hit(f["question"], kw):
            return r
    return None


def _run_eval(idx_by_spec: dict[str, tuple[HybridIndex, list[dict]]],
              queries: list[dict], weights: dict) -> dict:
    n = len(queries)
    hits1 = 0
    hits5 = 0
    rr_sum = 0.0
    t0 = time.perf_counter()
    for q in queries:
        idx, faqs = idx_by_spec[q["specialty"]]
        rank = _rank(idx, faqs, q["query"], q.get("expected_keyword", ""),
                     weights)
        if rank == 1:
            hits1 += 1
        if rank is not None and rank <= 5:
            hits5 += 1
        if rank is not None:
            rr_sum += 1.0 / rank
    dt = time.perf_counter() - t0
    return {
        "p_at_1": round(hits1 / n, 3),
        "recall_at_5": round(hits5 / n, 3),
        "mrr": round(rr_sum / n, 3),
        "elapsed_s": round(dt, 2),
    }


def write_markdown(results: list[dict], path: Path) -> None:
    base = next(r for r in results if r["name"] == "baseline")
    lines = ["# Retrieval-channel ablation study", ""]
    lines.append(
        f"Baseline weights: `{json.dumps(BASELINE)}`. Each row zeroes one "
        f"channel and re-runs the {results[0]['n']} eval queries. **ΔP@1** "
        f"is the absolute drop relative to the baseline."
    )
    lines.append("")
    lines.append("| Variant | P@1 | ΔP@1 | MRR | ΔMRR | Recall@5 |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for r in results:
        d_p = r["p_at_1"] - base["p_at_1"]
        d_m = r["mrr"] - base["mrr"]
        marker = "" if r["name"] == "baseline" else " "
        lines.append(
            f"| {marker}{r['label']} | {r['p_at_1']:.3f} | "
            f"{d_p:+.3f} | {r['mrr']:.3f} | {d_m:+.3f} | "
            f"{r['recall_at_5']:.3f} |"
        )
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    drops = sorted(
        [r for r in results if r["name"].startswith("no_")],
        key=lambda r: r["p_at_1"]
    )
    worst_drop = base["p_at_1"] - drops[0]["p_at_1"] if drops else 0.0
    if worst_drop > 0.0:
        worst = drops[0]
        ch = worst["name"][3:]
        lines.append(
            f"- Removing **{ch}** causes the largest drop "
            f"(P@1 → {worst['p_at_1']:.3f}, a fall of "
            f"{worst_drop:.3f}), confirming that channel is the most "
            f"informative."
        )
    else:
        lines.append(
            "- No single channel removal reduces P@1 below the baseline, "
            "which means the ensemble is **robust to channel loss** "
            "(each query is correctly answered by at least one remaining "
            "channel)."
        )
    only = [r for r in results if r["name"].endswith("_only")]
    if only:
        only.sort(key=lambda r: -r["p_at_1"])
        b = only[0]
        ch = b["name"][:-5]
        lines.append(
            f"- The strongest **single channel in isolation** is "
            f"**{ch}** (P@1 = {b['p_at_1']:.3f})."
        )
        worst_only = only[-1]
        ch2 = worst_only["name"][:-5]
        lines.append(
            f"- The weakest single channel is **{ch2}** "
            f"(P@1 = {worst_only['p_at_1']:.3f}); on this corpus it is "
            f"useful only as part of the ensemble."
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    import asyncio

    print("Building indexes ...")
    faqs_by_spec = asyncio.run(_load_faqs())
    idx_by_spec: dict[str, tuple[HybridIndex, list[dict]]] = {}
    for spec, faqs in faqs_by_spec.items():
        idx_by_spec[spec] = (HybridIndex(faqs), faqs)
        print(f"  built {spec:14s} ({len(faqs)} FAQs)")

    queries = _load_eval()
    print(f"Loaded {len(queries)} eval queries")
    print()

    variants: list[tuple[str, str, dict]] = [
        ("baseline", "baseline (all channels)", BASELINE),
    ]
    for ch in CHANNELS:
        w = {k: (0.0 if k == ch else v) for k, v in BASELINE.items()}
        variants.append((f"no_{ch}", f"baseline − {ch}", w))
    for ch in CHANNELS:
        w = {k: (1.0 if k == ch else 0.0) for k in BASELINE}
        variants.append((f"{ch}_only", f"{ch} only", w))

    results: list[dict] = []
    for name, label, w in variants:
        m = _run_eval(idx_by_spec, queries, w)
        m["name"] = name
        m["label"] = label
        m["weights"] = w
        m["n"] = len(queries)
        print(
            f"  {name:18s} P@1={m['p_at_1']:.3f}  MRR={m['mrr']:.3f}  "
            f"R@5={m['recall_at_5']:.3f}"
        )
        results.append(m)

    out_json = ROOT / "ablation_results.json"
    out_md = ROOT / "ABLATION_REPORT.md"
    out_json.write_text(json.dumps(results, indent=2), encoding="utf-8")
    write_markdown(results, out_md)
    print()
    print(f"Wrote {out_json.relative_to(ROOT).as_posix()}")
    print(f"Wrote {out_md.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

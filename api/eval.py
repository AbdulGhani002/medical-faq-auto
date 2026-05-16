"""Offline evaluation harness for the retrieval pipeline.

Loads data/eval_queries.json and asks the API one question at a time,
scoring each based on whether the returned answer contains the expected
keyword. Reports per-specialty accuracy, hit rate, and average latency.

Usage:
    python api/eval.py
    python api/eval.py --base-url http://localhost:8000
    python api/eval.py --specialty radiology
"""
import argparse
import json
import sys
import time
from pathlib import Path
from urllib import error as urlerr
from urllib import request as urlreq


def _post_chat(base_url: str, specialty: str, query: str) -> dict:
    # Use a fresh session per query so the follow-up detector cannot pull
    # an unrelated prior turn into the augmented query.
    import uuid
    body = json.dumps({
        "session_id": f"eval-{uuid.uuid4().hex[:8]}",
        "specialty": specialty,
        "text": query,
    }).encode("utf-8")
    req = urlreq.Request(
        f"{base_url.rstrip('/')}/chat",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    with urlreq.urlopen(req, timeout=10) as r:
        return json.loads(r.read())


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base-url", default="http://localhost:8000")
    p.add_argument("--specialty", default=None,
                   help="Run only one specialty.")
    p.add_argument("--verbose", action="store_true")
    args = p.parse_args()

    repo_root = Path(__file__).parent.parent
    eval_path = repo_root / "data" / "eval_queries.json"
    queries = json.loads(eval_path.read_text(encoding="utf-8"))
    if args.specialty:
        queries = [q for q in queries if q["specialty"] == args.specialty]

    per_spec: dict[str, dict] = {}
    total_lat = 0.0
    hits = 0
    confident = 0
    n = 0

    for q in queries:
        spec = q["specialty"]
        keyword = q["expected_keyword"].lower()
        t0 = time.time()
        try:
            r = _post_chat(args.base_url, spec, q["query"])
        except urlerr.URLError as e:
            print(f"  request failed for '{q['query']}': {e}")
            continue
        dt = time.time() - t0
        total_lat += dt
        n += 1
        answer = (r.get("answer") or "").lower()
        ok = keyword in answer
        if ok:
            hits += 1
        if r.get("bucket") == "confident":
            confident += 1

        bucket = per_spec.setdefault(spec, {"n": 0, "hits": 0, "conf": 0, "lat": 0.0})
        bucket["n"] += 1
        bucket["hits"] += int(ok)
        bucket["conf"] += int(r.get("bucket") == "confident")
        bucket["lat"] += dt

        if args.verbose or not ok:
            tag = "OK " if ok else "MISS"
            print(f"  [{tag}] [{spec}] {q['query'][:60]!r:62s} "
                  f"-> {r.get('bucket','?')} {r.get('confidence',0):.2f}")

    if n == 0:
        print("no queries ran")
        return 1

    print()
    print(f"{'specialty':18s} {'n':>4s} {'hit_rate':>9s} {'confident':>11s} {'avg_latency':>13s}")
    print("-" * 60)
    for spec, b in sorted(per_spec.items()):
        print(f"{spec:18s} {b['n']:>4d} "
              f"{b['hits']/b['n']*100:>7.1f}%  "
              f"{b['conf']/b['n']*100:>9.1f}%  "
              f"{b['lat']/b['n']*1000:>10.1f}ms")
    print("-" * 60)
    print(f"{'overall':18s} {n:>4d} "
          f"{hits/n*100:>7.1f}%  "
          f"{confident/n*100:>9.1f}%  "
          f"{total_lat/n*1000:>10.1f}ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())

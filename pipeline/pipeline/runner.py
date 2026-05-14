"""CLI runner for the FAQ generation pipeline.

Usage:
    python -m pipeline.runner --once
    python -m pipeline.runner --once --specialty radiology
"""
import argparse
import sys

from pipeline.stages import (
    cluster,
    embed,
    ingest,
    normalize,
    polish,
    publish,
    segment,
    select,
)


def run_once(specialty: str | None = None) -> int:
    print("[1/8] Ingest")
    sessions = ingest.run(specialty=specialty)
    print(f"      pulled {len(sessions)} sessions")

    print("[2/8] Segment")
    turns = segment.run(sessions)
    print(f"      {len(turns)} question turns")

    print("[3/8] Normalize")
    turns = normalize.run(turns)

    print("[4/8] Embed")
    vectors = embed.run(turns)

    print("[5/8] Cluster")
    clusters = cluster.run(turns, vectors)
    print(f"      {len(clusters)} clusters")

    print("[6/8] Select best answer per cluster (extractive)")
    selected = select.run(clusters, turns)

    print("[7/8] Polish output (rule-based)")
    polished = polish.run(selected)

    print("[8/8] Publish to FAQ store")
    n = publish.run(polished)
    print(f"      published {n} FAQs")
    return n


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--once", action="store_true", help="Run pipeline once and exit.")
    p.add_argument("--specialty", help="Restrict to one specialty.")
    args = p.parse_args()

    if args.once:
        run_once(specialty=args.specialty)
        return

    print("Use --once to run a single pass.")
    print("Scheduler integration (Celery beat): TODO.")
    sys.exit(0)


if __name__ == "__main__":
    main()

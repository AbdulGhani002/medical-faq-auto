"""Single CLI entry point for the project.

    python -m app.cli chat            # interactive REPL
    python -m app.cli eval            # run retrieval eval (needs API up)
    python -m app.cli ablate          # offline ablation study
    python -m app.cli intent-eval     # NB intent 80/20 evaluation
    python -m app.cli pipeline        # run the chat-log -> FAQ pipeline
    python -m app.cli analyze "text"  # offline NLP analysis dump
    python -m app.cli ner-train       # train statistical NER + report F1
    python -m app.cli build-jsonl     # regenerate the JSONL bundle
    python -m app.cli test            # run pytest unit suite
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


# ----------------------------- subcommands ---------------------------------


def _api_url() -> str:
    return os.environ.get("MEDFAQ_API", "http://127.0.0.1:8000")


def cmd_chat(args) -> int:
    """Interactive REPL against the chat API."""
    import readline  # noqa: F401  (improves input UX on POSIX; harmless elsewhere)
    specialty = args.specialty
    sid = args.session
    print(f"[chat] specialty={specialty}  session={sid}")
    print("[chat] type :q to quit, :reset to clear, :state to inspect")
    while True:
        try:
            text = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not text:
            continue
        if text == ":q":
            return 0
        if text == ":reset":
            _post(f"/chat/reset/{sid}", {})
            print("[chat] state cleared")
            continue
        if text == ":state":
            data = _get(f"/chat/state/{sid}")
            print(json.dumps(data, indent=2))
            continue
        r = _post("/chat", {
            "session_id": sid, "specialty": specialty, "text": text,
        })
        d = r.get("dialog") or {}
        if d.get("banner"):
            print(f"!! {d['banner']}")
        print(f"bot> {r.get('answer','')}")
        if d.get("active_topic"):
            print(f"  [topic={d['active_topic']}  "
                  f"intent={r.get('nlp', {}).get('intent', {}).get('label')}  "
                  f"conf={r.get('confidence', 0):.0%}]")


def cmd_eval(args) -> int:
    return _run_script("eval.py")


def cmd_ablate(args) -> int:
    return _run_script("ablate.py")


def cmd_intent_eval(args) -> int:
    return _run_script("intent_eval.py")


def cmd_pipeline(args) -> int:
    """Run the chat-log -> FAQ candidate pipeline once."""
    return subprocess.call(
        [sys.executable, "-m", "pipeline.runner", "--once"],
        cwd=str(ROOT / "pipeline"),
    )


def cmd_analyze(args) -> int:
    from app.services.analyzer import analyse as _analyse
    out = _analyse(args.text)
    print(json.dumps(out, indent=2, default=str))
    return 0


def cmd_ner_train(args) -> int:
    """Train the structured-perceptron NER on the BIO JSONL + silver
    labels from the FAQ corpus, then report F1 on the gold set."""
    from app.nlp.ner_stat import (
        train_default, evaluate, _load_gold_jsonl,
    )
    print("[ner] training averaged structured perceptron…")
    model = train_default()
    gold = _load_gold_jsonl()
    examples = [(toks, tags, " ".join(toks)) for toks, tags in gold]
    metrics = evaluate(model, examples)
    print()
    print("  gold set metrics:")
    for k, v in metrics.items():
        print(f"    {k:10s} {v}")
    print()
    sample = "I have crushing chest pain and my left arm is numb"
    pred = model.predict_entities(sample)
    print(f"  sample: {sample!r}")
    for e in pred:
        print(f"    {e['text']:20s} -> {e['label']}")
    return 0


def cmd_build_jsonl(args) -> int:
    return subprocess.call(
        [sys.executable, str(ROOT / "data" / "build_jsonl.py")],
        cwd=str(ROOT),
    )


def cmd_test(args) -> int:
    return subprocess.call(
        [sys.executable, "-m", "pytest", "-q", "tests/"],
        cwd=str(ROOT / "api"),
    )


# ----------------------------- helpers -------------------------------------


def _post(path: str, body: dict) -> dict:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        _api_url() + path,
        data=data,
        headers={"content-type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e), "answer": "<API unreachable>"}


def _get(path: str) -> dict:
    try:
        with urllib.request.urlopen(_api_url() + path, timeout=20) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"error": str(e)}


def _run_script(name: str) -> int:
    return subprocess.call(
        [sys.executable, str(ROOT / "api" / name)],
        cwd=str(ROOT / "api"),
    )


# ----------------------------- argparse ------------------------------------


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="medfaq",
        description="Medical FAQ chatbot CLI — single entry to chat, "
                    "evaluate, train, and run the pipeline.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chat", help="Interactive REPL")
    c.add_argument("--specialty", default="cardiovascular",
                   choices=["radiology", "physiotherapy", "cardiovascular"])
    c.add_argument("--session", default="cli-session")
    c.set_defaults(func=cmd_chat)

    sub.add_parser("eval", help="Retrieval evaluation").set_defaults(
        func=cmd_eval)
    sub.add_parser("ablate", help="Ablation study").set_defaults(
        func=cmd_ablate)
    sub.add_parser("intent-eval",
                   help="NB intent 80/20 evaluation").set_defaults(
        func=cmd_intent_eval)
    sub.add_parser("pipeline",
                   help="Run chat-log -> FAQ pipeline").set_defaults(
        func=cmd_pipeline)

    a = sub.add_parser("analyze", help="One-shot NLP analysis on a string")
    a.add_argument("text")
    a.set_defaults(func=cmd_analyze)

    sub.add_parser("ner-train",
                   help="Train statistical NER and report F1").set_defaults(
        func=cmd_ner_train)

    sub.add_parser("build-jsonl",
                   help="Regenerate data/*.jsonl from sources").set_defaults(
        func=cmd_build_jsonl)

    sub.add_parser("test",
                   help="Run pytest unit suite").set_defaults(
        func=cmd_test)
    return p


def main(argv: list[str] | None = None) -> int:
    ns = _parser().parse_args(argv)
    return int(ns.func(ns) or 0)


if __name__ == "__main__":
    raise SystemExit(main())

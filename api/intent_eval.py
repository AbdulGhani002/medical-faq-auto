"""Rigorous evaluation of the Naive Bayes intent classifier.

Splits ``data/intents.jsonl`` 80/20 (stratified by label), trains on 80,
evaluates on 20. Reports:

  - macro-F1
  - per-class precision / recall / F1
  - confusion matrix (Markdown table)

Outputs ``INTENT_EVAL.md`` and ``intent_eval.json``.
"""
from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parents[1]


def _load_intents() -> list[dict]:
    p = ROOT / "data" / "intents.jsonl"
    out: list[dict] = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            out.append(json.loads(line))
    return out


def stratified_split(rows: list[dict], ratio: float = 0.2,
                     seed: int = 0) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    by_label: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_label[r["label"]].append(r)
    train: list[dict] = []
    test: list[dict] = []
    for label, group in by_label.items():
        group = list(group)
        rng.shuffle(group)
        n_test = max(1, int(round(len(group) * ratio)))
        test.extend(group[:n_test])
        train.extend(group[n_test:])
    rng.shuffle(train)
    rng.shuffle(test)
    return train, test


def fit_model(train: list[dict]) -> Pipeline:
    p = Pipeline([
        ("tfidf", TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True,
        )),
        ("nb", MultinomialNB(alpha=0.3)),
    ])
    p.fit([r["text"] for r in train], [r["label"] for r in train])
    return p


def per_class_metrics(y_true: list[str],
                      y_pred: list[str]) -> dict[str, dict]:
    labels = sorted(set(y_true) | set(y_pred))
    out: dict[str, dict] = {}
    for L in labels:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == L and p == L)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != L and p == L)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == L and p != L)
        prec = tp / (tp + fp) if (tp + fp) else 0.0
        rec = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) else 0.0
        support = sum(1 for t in y_true if t == L)
        out[L] = {
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3),
            "support": support,
        }
    return out


def confusion_matrix(y_true: list[str], y_pred: list[str]) -> dict:
    labels = sorted(set(y_true) | set(y_pred))
    mat: dict[str, dict[str, int]] = {
        t: {p: 0 for p in labels} for t in labels
    }
    for t, p in zip(y_true, y_pred):
        mat[t][p] += 1
    return {"labels": labels, "matrix": mat}


def macro_f1(per_class: dict[str, dict]) -> float:
    if not per_class:
        return 0.0
    return round(
        sum(v["f1"] for v in per_class.values()) / len(per_class), 3
    )


def write_markdown(report: dict, path: Path) -> None:
    lines = ["# Naive Bayes intent classifier evaluation", ""]
    lines.append(
        f"Stratified 80/20 split of `data/intents.jsonl`. Trained on "
        f"{report['train_size']} examples, evaluated on "
        f"{report['test_size']}. **Macro-F1 = "
        f"{report['macro_f1']:.3f}** across "
        f"{len(report['per_class'])} classes."
    )
    lines.append("")
    lines.append("## Per-class metrics")
    lines.append("")
    lines.append("| Class | Precision | Recall | F1 | Support |")
    lines.append("|---|---:|---:|---:|---:|")
    items = sorted(report["per_class"].items(),
                   key=lambda kv: -kv[1]["f1"])
    for label, m in items:
        lines.append(
            f"| {label} | {m['precision']:.3f} | {m['recall']:.3f} | "
            f"{m['f1']:.3f} | {m['support']} |"
        )
    lines.append("")
    lines.append("## Confusion matrix")
    lines.append("")
    cm = report["confusion"]
    labels = cm["labels"]
    header = "| true ↓ / pred → | " + " | ".join(labels) + " |"
    sep = "|---" * (len(labels) + 1) + "|"
    lines.append(header)
    lines.append(sep)
    for t in labels:
        row = [f"**{t}**"] + [str(cm["matrix"][t][p]) for p in labels]
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")
    if report.get("errors"):
        lines.append("## Misclassifications")
        lines.append("")
        lines.append("| text | true | predicted |")
        lines.append("|---|---|---|")
        for e in report["errors"][:25]:
            lines.append(
                f"| {e['text']} | {e['true']} | {e['pred']} |"
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    rows = _load_intents()
    print(f"Loaded {len(rows)} intent examples")

    train, test = stratified_split(rows, ratio=0.2, seed=0)
    print(f"Train: {len(train)}  Test: {len(test)}")

    model = fit_model(train)
    y_true = [r["label"] for r in test]
    y_pred = list(map(str, model.predict([r["text"] for r in test])))

    per = per_class_metrics(y_true, y_pred)
    cm = confusion_matrix(y_true, y_pred)
    mf1 = macro_f1(per)

    errors = []
    for r, p in zip(test, y_pred):
        if p != r["label"]:
            errors.append({
                "text": r["text"], "true": r["label"], "pred": p,
            })

    report = {
        "train_size": len(train),
        "test_size": len(test),
        "macro_f1": mf1,
        "per_class": per,
        "confusion": cm,
        "errors": errors,
    }

    print()
    print(f"  Macro-F1: {mf1:.3f}")
    print(f"  Errors  : {len(errors)} / {len(test)}")
    print()
    print(f"  Worst classes (F1):")
    for label, m in sorted(per.items(), key=lambda kv: kv[1]["f1"])[:3]:
        print(f"    {label:18s} P={m['precision']:.2f} R={m['recall']:.2f} "
              f"F1={m['f1']:.2f}  (support={m['support']})")

    out_json = ROOT / "intent_eval.json"
    out_md = ROOT / "INTENT_EVAL.md"
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    write_markdown(report, out_md)
    print()
    print(f"Wrote {out_json.relative_to(ROOT).as_posix()}")
    print(f"Wrote {out_md.relative_to(ROOT).as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

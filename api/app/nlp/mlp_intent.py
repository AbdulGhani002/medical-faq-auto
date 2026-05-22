"""Intent classifier built on a neural network — every line ours.

Pipeline:
    text -> TfidfVectorizer (myml)  ->  MLPClassifier (myml, with backprop)
                                        |
                                        +--> 64-unit hidden ReLU
                                        +--> 32-unit hidden ReLU
                                        +--> softmax over 12 intents

Trained at import time on the JSONL intent corpus (``data/intents.jsonl``).
Side-by-side with the Naive Bayes classifier so we can compare both.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from app.myml.mlp import MLPClassifier
from app.myml.tfidf import TfidfVectorizer


def _load_jsonl_training() -> list[tuple[str, str]]:
    """Look for ``data/intents.jsonl`` next to the repo root."""
    candidates = [
        Path(__file__).resolve().parents[3] / "data" / "intents.jsonl",
        Path(__file__).resolve().parents[4] / "data" / "intents.jsonl",
    ]
    for p in candidates:
        if p.is_file():
            rows: list[tuple[str, str]] = []
            with p.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    if "text" in rec and "label" in rec:
                        rows.append((rec["text"], rec["label"]))
            if rows:
                return rows
    return []


class _NeuralIntent:
    def __init__(self) -> None:
        self.vec = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2),
            min_df=1, sublinear_tf=True,
        )
        self.mlp = MLPClassifier(
            hidden_layer_sizes=(64, 32),
            max_iter=160, batch_size=32, lr=0.08,
            momentum=0.9, weight_decay=1e-4,
            random_state=0,
        )
        self.classes_ = None
        self.train_n = 0
        self.final_loss = None
        self.train_accuracy = None

    def fit(self, X: list[str], y: list[str]) -> "_NeuralIntent":
        Xv = self.vec.fit_transform(X)
        self.mlp.fit(Xv, y)
        self.classes_ = self.mlp.classes_
        self.train_n = len(X)
        self.final_loss = (
            self.mlp.loss_curve_[-1] if self.mlp.loss_curve_ else None
        )
        self.train_accuracy = self.mlp.score(Xv, y)
        return self

    def predict_proba(self, X: list[str]) -> np.ndarray:
        return self.mlp.predict_proba(self.vec.transform(X))


_MODEL: "_NeuralIntent | None" = None


def model() -> "_NeuralIntent":
    global _MODEL
    if _MODEL is None:
        m = _NeuralIntent()
        rows = _load_jsonl_training()
        if rows:
            X = [t for t, _ in rows]
            y = [l for _, l in rows]
            m.fit(X, y)
        _MODEL = m
    return _MODEL


def classify(text: str) -> dict:
    mdl = model()
    if mdl.classes_ is None or len(mdl.classes_) == 0:
        return {"label": "question", "confidence": 0.0, "top3": []}
    probs = mdl.predict_proba([text or ""])[0]
    classes = list(mdl.classes_)
    pairs = sorted(zip(classes, probs), key=lambda kv: -kv[1])
    label, conf = pairs[0]
    return {
        "label": str(label),
        "confidence": float(round(conf, 3)),
        "top3": [(str(c), float(round(p, 3))) for c, p in pairs[:3]],
        "model": "MLP (myml, backprop, 64-32-softmax)",
    }


def stats() -> dict:
    m = model()
    has_classes = m.classes_ is not None and len(m.classes_) > 0
    return {
        "trained": bool(has_classes),
        "n_train_examples": m.train_n,
        "n_classes": int(len(m.classes_)) if has_classes else 0,
        "final_training_loss": (
            round(float(m.final_loss), 4) if m.final_loss else None
        ),
        "train_accuracy": (
            round(float(m.train_accuracy), 4)
            if m.train_accuracy is not None else None
        ),
        "vocab_size": len(m.vec.vocabulary_),
        "architecture": [64, 32],
    }

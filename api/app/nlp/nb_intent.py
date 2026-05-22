"""Multinomial Naive Bayes intent classifier.

Trained at import time. The training corpus lives in
``data/intents.jsonl`` (one JSON record per line, ``{text, label, id}``).
If that file is missing we fall back to the in-file ``_TRAIN`` list so
the API still boots in any environment.

Categories:

  greeting         - "hi", "hello", "good morning", ...
  thanks           - "thanks", "much appreciated", ...
  frustration      - "useless", "this is bad", ...
  help             - "what can you do?", "menu", ...
  ask_definition   - "what is angina?"
  ask_preparation  - "do i need to fast before my mri?"
  ask_recovery     - "when can i drive after surgery?"
  ask_medication   - "should i take aspirin every day?"
  ask_symptom      - "is chest tightness a warning sign?"
  ask_lifestyle    - "can i exercise with hypertension?"
  ask_procedure    - "how long does a CT take?"
  ask_warning      - "what are the signs of a stroke?"

Pure Python + scikit-learn TF-IDF + MultinomialNB. No LLM.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.myml.tfidf import TfidfVectorizer
from app.myml.nb import MultinomialNB


_TRAIN: list[tuple[str, str]] = [
    # greeting
    ("hi", "greeting"),
    ("hello", "greeting"),
    ("hey there", "greeting"),
    ("hi assistant", "greeting"),
    ("good morning", "greeting"),
    ("good afternoon", "greeting"),
    ("good evening", "greeting"),
    ("salaam", "greeting"),
    ("salam", "greeting"),
    ("assalam alaikum", "greeting"),
    # thanks
    ("thanks", "thanks"),
    ("thank you", "thanks"),
    ("much appreciated", "thanks"),
    ("appreciate it", "thanks"),
    ("thx", "thanks"),
    ("ty", "thanks"),
    ("shukria", "thanks"),
    # frustration
    ("this is useless", "frustration"),
    ("you are stupid", "frustration"),
    ("garbage answer", "frustration"),
    ("wtf is this", "frustration"),
    ("rubbish bot", "frustration"),
    ("this sucks", "frustration"),
    ("you are not helpful", "frustration"),
    # help
    ("help", "help"),
    ("what can you do", "help"),
    ("how do i use this", "help"),
    ("menu", "help"),
    ("show me options", "help"),
    ("list topics", "help"),
    # ask_definition
    ("what is angina", "ask_definition"),
    ("define hypertension", "ask_definition"),
    ("what is sciatica", "ask_definition"),
    ("explain heart failure", "ask_definition"),
    ("what does mri mean", "ask_definition"),
    ("what is an echocardiogram", "ask_definition"),
    ("tell me about cholesterol", "ask_definition"),
    ("what is afib", "ask_definition"),
    ("define stroke", "ask_definition"),
    ("what does dash diet stand for", "ask_definition"),
    # ask_preparation
    ("do i need to fast before my mri", "ask_preparation"),
    ("how to prepare for a ct scan", "ask_preparation"),
    ("any prep before ultrasound", "ask_preparation"),
    ("should i stop eating before angiogram", "ask_preparation"),
    ("can i drink water before the scan", "ask_preparation"),
    ("what to wear for an mri", "ask_preparation"),
    ("preparation for blood test", "ask_preparation"),
    ("any preparation before physio", "ask_preparation"),
    # ask_recovery
    ("when can i drive after surgery", "ask_recovery"),
    ("how long is recovery after a stent", "ask_recovery"),
    ("when can i return to work", "ask_recovery"),
    ("after the procedure how long until i feel better", "ask_recovery"),
    ("recovery time after knee surgery", "ask_recovery"),
    ("when can i exercise after physio session", "ask_recovery"),
    ("how long till the bruise heals", "ask_recovery"),
    # ask_medication
    ("when should i take my bp medicine", "ask_medication"),
    ("should i take aspirin every day", "ask_medication"),
    ("what are the side effects of statins", "ask_medication"),
    ("how to take my blood thinner", "ask_medication"),
    ("missed a dose of my medicine", "ask_medication"),
    ("can i double up on my blood pressure pill", "ask_medication"),
    ("painkillers safe with my heart", "ask_medication"),
    # ask_symptom
    ("is chest tightness a warning sign", "ask_symptom"),
    ("are palpitations dangerous", "ask_symptom"),
    ("why do i feel dizzy when i stand up", "ask_symptom"),
    ("my knee feels stiff after running", "ask_symptom"),
    ("i feel sore after my physio session", "ask_symptom"),
    ("my heart races at night", "ask_symptom"),
    ("i feel breathless climbing stairs", "ask_symptom"),
    ("sharp pain in my chest", "ask_symptom"),
    ("my back hurts after sitting", "ask_symptom"),
    # ask_lifestyle
    ("can i exercise with high blood pressure", "ask_lifestyle"),
    ("is alcohol safe with my heart condition", "ask_lifestyle"),
    ("is coffee bad for my heart", "ask_lifestyle"),
    ("can i lift weights with bp", "ask_lifestyle"),
    ("what diet for heart disease", "ask_lifestyle"),
    ("how much salt is too much", "ask_lifestyle"),
    ("can i sleep on my back after surgery", "ask_lifestyle"),
    ("smoking and the heart", "ask_lifestyle"),
    # ask_procedure
    ("how long does a ct take", "ask_procedure"),
    ("how long is the mri appointment", "ask_procedure"),
    ("what happens during an ecg", "ask_procedure"),
    ("what is involved in an echo scan", "ask_procedure"),
    ("how does the holter monitor work", "ask_procedure"),
    ("will the angiogram hurt", "ask_procedure"),
    ("how long does a physio session take", "ask_procedure"),
    # ask_warning
    ("what are the signs of a stroke", "ask_warning"),
    ("warning signs of heart attack", "ask_warning"),
    ("when should i call an ambulance", "ask_warning"),
    ("red flags after heart surgery", "ask_warning"),
    ("when should i go to the er", "ask_warning"),
    ("danger signs in pregnancy", "ask_warning"),
    ("symptoms to watch for after a fall", "ask_warning"),
]


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


class _Pipeline:
    """Light TF-IDF -> Naive Bayes pipeline using our myml modules."""

    def __init__(self) -> None:
        self.vec = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2),
            min_df=1, sublinear_tf=True,
        )
        self.nb = MultinomialNB(alpha=0.3)
        self.classes_ = None

    def fit(self, X: list[str], y: list[str]) -> "_Pipeline":
        Xv = self.vec.fit_transform(X)
        self.nb.fit(Xv, y)
        self.classes_ = self.nb.classes_
        return self

    def predict_proba(self, X: list[str]):
        Xv = self.vec.transform(X)
        return self.nb.predict_proba(Xv)


def _build_model() -> "_Pipeline":
    pipe = _Pipeline()
    jsonl_rows = _load_jsonl_training()
    rows = jsonl_rows or _TRAIN
    X = [t for t, _ in rows]
    y = [l for _, l in rows]
    pipe.fit(X, y)
    return pipe


def training_source() -> str:
    return "jsonl" if _load_jsonl_training() else "hardcoded"


_MODEL: "_Pipeline | None" = None


def model() -> "_Pipeline":
    global _MODEL
    if _MODEL is None:
        _MODEL = _build_model()
    return _MODEL


def classify(text: str) -> dict:
    """Return {label, confidence, top3:[(label, score)]}."""
    mdl = model()
    probs = mdl.predict_proba([text or ""])[0]
    classes = list(mdl.classes_)
    pairs = sorted(zip(classes, probs), key=lambda kv: -kv[1])
    label, conf = pairs[0]
    return {
        "label": str(label),
        "confidence": float(round(conf, 3)),
        "top3": [(str(c), float(round(p, 3))) for c, p in pairs[:3]],
    }


def is_chitchat(label: str) -> bool:
    return label in {"greeting", "thanks", "frustration", "help"}

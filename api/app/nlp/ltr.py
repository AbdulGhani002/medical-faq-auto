"""Learning-to-rank reranker.

For each (query, FAQ-doc) pair we build a feature vector and train a
sklearn LogisticRegression to predict ``is this the right FAQ?``. At
inference time the top-K candidates from the lexical retriever are
re-ranked by the LR score, blended with the lexical score.

Features (all derived from the in-house NLP stack, no LLM):

  0  tfidf_word            word TF-IDF cosine
  1  tfidf_char            char TF-IDF cosine
  2  bm25                  normalised BM25
  3  lsa                   LSA topic cosine
  4  embed                 PPMI embedding cosine
  5  ner_overlap_count     # NER labels shared with the doc
  6  ner_overlap_jaccard   Jaccard over entity sets
  7  intent_alignment      1 if query intent ∈ {ask_*} else 0
  8  qtype_yes_no          1 if question is yes/no
  9  qtype_what            1 if question is "what"
 10  qtype_why_how         1 if "why" or "how"
 11  has_negation          1 if any negation cue
 12  query_len_tokens      raw query length
 13  query_doc_len_ratio   |q| / |doc| (length penalty)

Trained on (eval_queries.jsonl, faqs.jsonl). Positives are (query, FAQ
whose answer contains the expected_keyword). Negatives are (query, 4
random other FAQs from the same specialty).
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import numpy as np

from app.myml.logreg import LogisticRegression

from .ner import extract_entities
from .nb_intent import classify as classify_nb_intent
from .qtype import classify as classify_qtype
from .negation import is_negated

_HERE = Path(__file__).resolve()
_ROOT = _HERE.parents[3]


FEATURE_NAMES = [
    "tfidf_word", "tfidf_char", "bm25", "lsa", "embed",
    "ner_overlap_count", "ner_overlap_jaccard",
    "intent_alignment",
    "qtype_yes_no", "qtype_what", "qtype_why_how",
    "has_negation",
    "query_len_tokens", "query_doc_len_ratio",
]


def _tokens(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _ner_overlap(q_ents: list[dict], d_ents: list[dict]) -> tuple[int, float]:
    qset = {(e["text"].lower(), e["label"]) for e in q_ents}
    dset = {(e["text"].lower(), e["label"]) for e in d_ents}
    inter = qset & dset
    union = qset | dset
    jacc = (len(inter) / len(union)) if union else 0.0
    return len(inter), round(jacc, 4)


def featurise(query: str, doc_text: str, per: dict, q_ents=None,
              d_ents=None) -> list[float]:
    """Build one feature vector for (query, doc).

    Parameters
    ----------
    query     raw user text
    doc_text  FAQ "question + answer" string used in retrieval
    per       per-method score dict from HybridIndex.top_k (tfidf_word, ...)
    q_ents    optional precomputed query entities
    d_ents    optional precomputed doc entities
    """
    if q_ents is None:
        q_ents = extract_entities(query)
    if d_ents is None:
        d_ents = extract_entities(doc_text)
    ner_n, ner_j = _ner_overlap(q_ents, d_ents)

    intent = classify_nb_intent(query)["label"]
    qtype = classify_qtype(query)

    q_toks = _tokens(query)
    d_toks = _tokens(doc_text)
    return [
        float(per.get("tfidf_word", 0.0)),
        float(per.get("tfidf_char", 0.0)),
        float(per.get("bm25", 0.0)),
        float(per.get("lsa", 0.0)),
        float(per.get("embed", 0.0)),
        float(ner_n),
        float(ner_j),
        1.0 if intent.startswith("ask_") else 0.0,
        1.0 if qtype == "yes_no" else 0.0,
        1.0 if qtype == "what" else 0.0,
        1.0 if qtype in ("why", "how") else 0.0,
        1.0 if is_negated(query) else 0.0,
        float(len(q_toks)),
        round(len(q_toks) / max(1, len(d_toks)), 4),
    ]


class LTRReranker:
    def __init__(self) -> None:
        self.clf: LogisticRegression | None = None
        self.trained = False
        self.train_size = 0
        self.train_acc: float | None = None

    def train_from_eval_set(self, idx, faqs: list[dict],
                            queries: list[dict], k_neg: int = 4
                            ) -> dict:
        """Train on (query, expected-FAQ) positives + random negatives.

        Parameters
        ----------
        idx       a built HybridIndex (so we can get per-method scores)
        faqs      the FAQ corpus used by `idx`
        queries   list of {specialty, query, expected_keyword}
        k_neg     # negatives per positive
        """
        X: list[list[float]] = []
        y: list[int] = []
        rng = np.random.default_rng(0)
        # Cache doc texts for featurise.
        doc_texts = [f"{f['question']} {f['answer']}" for f in faqs]
        doc_ents = [extract_entities(t) for t in doc_texts]

        for q in queries:
            kw = (q.get("expected_keyword") or "").lower()
            if not kw:
                continue
            spec = q["specialty"]
            qx = q["query"]
            q_ents = extract_entities(qx)
            # Find the positive FAQ (first whose answer contains the keyword)
            cand_pos = []
            for i, f in enumerate(faqs):
                if f["specialty"] != spec:
                    continue
                if kw in (f["question"] + " " + f["answer"]).lower():
                    cand_pos.append(i)
            if not cand_pos:
                continue
            # Score all docs to get per-method values.
            scores = idx.score(qx)
            bm25 = scores["bm25"]
            bm25_max = float(bm25.max()) if bm25.size else 0.0
            bm25_norm = bm25 / (bm25_max + 1e-9) if bm25_max > 0 else bm25
            for pos in cand_pos[:1]:
                per_pos = {
                    "tfidf_word": float(scores["tfidf_word"][pos]),
                    "tfidf_char": float(scores["tfidf_char"][pos]),
                    "bm25": float(bm25_norm[pos]),
                    "lsa": float(scores["lsa"][pos]),
                    "embed": float(scores["embed"][pos]),
                }
                X.append(featurise(qx, doc_texts[pos], per_pos, q_ents,
                                   doc_ents[pos]))
                y.append(1)
                # Sample k_neg random negatives from same specialty.
                same_spec = [i for i, f in enumerate(faqs)
                             if f["specialty"] == spec and i != pos]
                if same_spec:
                    chosen = rng.choice(
                        same_spec, size=min(k_neg, len(same_spec)),
                        replace=False
                    )
                    for j in chosen.tolist():
                        per_neg = {
                            "tfidf_word": float(scores["tfidf_word"][j]),
                            "tfidf_char": float(scores["tfidf_char"][j]),
                            "bm25": float(bm25_norm[j]),
                            "lsa": float(scores["lsa"][j]),
                            "embed": float(scores["embed"][j]),
                        }
                        X.append(featurise(qx, doc_texts[j], per_neg,
                                           q_ents, doc_ents[j]))
                        y.append(0)
        if not X:
            return {"trained": False, "n": 0}
        Xn = np.asarray(X, dtype=np.float64)
        yn = np.asarray(y, dtype=int)
        self.clf = LogisticRegression(
            max_iter=400, C=2.0, class_weight="balanced",
        )
        self.clf.fit(Xn, yn)
        self.trained = True
        self.train_size = len(X)
        self.train_acc = float(self.clf.score(Xn, yn))
        return {
            "trained": True, "n": len(X), "train_acc": self.train_acc,
            "coef": dict(zip(FEATURE_NAMES, self.clf.coef_[0].round(4).tolist())),
        }

    def score_one(self, query: str, doc_text: str, per: dict) -> float:
        if not self.trained or self.clf is None:
            return per.get("bm25", 0.0)
        x = np.asarray([featurise(query, doc_text, per)], dtype=np.float64)
        return float(self.clf.predict_proba(x)[0, 1])

    def feature_importances(self) -> list[tuple[str, float]]:
        if not self.trained or self.clf is None:
            return []
        return sorted(
            zip(FEATURE_NAMES, self.clf.coef_[0].tolist()),
            key=lambda kv: -abs(kv[1])
        )

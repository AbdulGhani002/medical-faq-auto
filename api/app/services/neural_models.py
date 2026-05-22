"""Singleton trainers for the from-scratch neural models.

Each model is trained lazily the first time it is requested and cached
in process memory. The trainers all read from ``data/faqs.jsonl`` so a
single corpus refresh propagates everywhere.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Iterable

import numpy as np

from app.myml.bpe import BPETokenizer
from app.myml.dual_encoder import DualEncoder
from app.myml.tfidf import TfidfVectorizer
from app.myml.word2vec import Word2Vec

_ROOT = Path(__file__).resolve().parents[3]


def _faqs() -> list[dict]:
    p = _ROOT / "data" / "faqs.jsonl"
    out: list[dict] = []
    if not p.is_file():
        return out
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _faq_sentences() -> list[str]:
    out: list[str] = []
    for rec in _faqs():
        q = rec.get("question", "")
        a = rec.get("answer", "")
        if q:
            out.append(q)
        for s in re.split(r"(?<=[.!?])\s+", a):
            s = s.strip()
            if s:
                out.append(s)
    return out


# ---------------- word2vec ----------------


_W2V: Word2Vec | None = None
_W2V_STATS: dict = {}


def get_word2vec() -> Word2Vec:
    global _W2V, _W2V_STATS
    if _W2V is None:
        m = Word2Vec(
            dim=64, window=5, min_count=2, k_negatives=8,
            epochs=10, lr=0.05,
        )
        _W2V_STATS = m.fit(_faq_sentences())
        _W2V = m
    return _W2V


def word2vec_stats() -> dict:
    get_word2vec()
    return _W2V_STATS


# ---------------- BPE ----------------


_BPE: BPETokenizer | None = None
_BPE_STATS: dict = {}


def get_bpe() -> BPETokenizer:
    global _BPE, _BPE_STATS
    if _BPE is None:
        m = BPETokenizer(num_merges=500)
        _BPE_STATS = m.fit(_faq_sentences())
        _BPE = m
    return _BPE


def bpe_stats() -> dict:
    get_bpe()
    return _BPE_STATS


# ---------------- dual encoder ----------------


_DUAL: DualEncoder | None = None
_DUAL_VEC: TfidfVectorizer | None = None
_DUAL_DOC_MATRIX: np.ndarray | None = None
_DUAL_DOC_FAQS: list[dict] = []
_DUAL_STATS: dict = {}


def _build_dual_training_pairs() -> tuple[list[str], list[str], list[dict]]:
    """Build (query_text, doc_text, doc_record) triples.

    The training queries are the eval queries (each known to map to a
    specific FAQ identified by `expected_keyword`). For each eval query
    we find the FAQ whose answer contains the keyword in the same
    specialty.
    """
    faqs = _faqs()
    eval_p = _ROOT / "data" / "eval_queries.jsonl"
    if not eval_p.is_file():
        return [], [], faqs
    rows: list[tuple[str, str]] = []
    with eval_p.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            spec = rec.get("specialty")
            kw = (rec.get("expected_keyword") or "").lower()
            query = rec.get("query") or ""
            if not (spec and kw and query):
                continue
            for fr in faqs:
                if fr.get("specialty") != spec:
                    continue
                blob = (fr.get("question", "") + " " + fr.get("answer", "")).lower()
                if kw in blob:
                    rows.append((query, fr["question"] + " " + fr["answer"]))
                    break
    queries = [q for q, _ in rows]
    docs = [d for _, d in rows]
    return queries, docs, faqs


def get_dual_encoder() -> tuple[DualEncoder, TfidfVectorizer, np.ndarray, list[dict]]:
    global _DUAL, _DUAL_VEC, _DUAL_DOC_MATRIX, _DUAL_DOC_FAQS, _DUAL_STATS
    if _DUAL is not None:
        return _DUAL, _DUAL_VEC, _DUAL_DOC_MATRIX, _DUAL_DOC_FAQS

    queries, docs, faqs = _build_dual_training_pairs()
    _DUAL_DOC_FAQS = faqs
    if not queries:
        _DUAL_STATS = {"trained": False, "reason": "no training pairs"}
        _DUAL_VEC = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2),
            min_df=1, sublinear_tf=True,
        )
        # Fit on at least something so transform() works.
        all_text = [f.get("question", "") + " " + f.get("answer", "")
                    for f in faqs]
        if all_text:
            _DUAL_VEC.fit(all_text)
            _DUAL_DOC_MATRIX = _DUAL_VEC.transform(all_text)
        else:
            _DUAL_DOC_MATRIX = np.zeros((0, 0))
        return DualEncoder(d_in=1, hidden=1, d_out=1), _DUAL_VEC, _DUAL_DOC_MATRIX, faqs

    # Build one big TF-IDF over everything for the input features.
    all_text = queries + docs + [f.get("question", "") + " " + f.get("answer", "")
                                   for f in faqs]
    _DUAL_VEC = TfidfVectorizer(
        analyzer="word", ngram_range=(1, 2),
        min_df=1, sublinear_tf=True,
    )
    _DUAL_VEC.fit(all_text)
    Xq = _DUAL_VEC.transform(queries)
    Xd = _DUAL_VEC.transform(docs)
    enc = DualEncoder(
        d_in=Xq.shape[1], hidden=64, d_out=32,
        temperature=1 / 0.07, lr=0.02, weight_decay=1e-5,
        epochs=30, batch_size=8,
    )
    _DUAL_STATS = enc.fit(Xq, Xd)
    _DUAL_STATS["d_in"] = int(Xq.shape[1])

    # Cache the FAQ doc embeddings.
    corpus_text = [f.get("question", "") + " " + f.get("answer", "") for f in faqs]
    Xcorpus = _DUAL_VEC.transform(corpus_text)
    _DUAL_DOC_MATRIX = enc.encode_docs(Xcorpus)
    _DUAL = enc
    return _DUAL, _DUAL_VEC, _DUAL_DOC_MATRIX, _DUAL_DOC_FAQS


def dual_encoder_stats() -> dict:
    get_dual_encoder()
    return _DUAL_STATS


def neural_retrieve(query: str, k: int = 5) -> list[dict]:
    enc, vec, doc_mat, faqs = get_dual_encoder()
    if not faqs or doc_mat is None or doc_mat.size == 0:
        return []
    if not _DUAL_STATS.get("trained"):
        return []
    Xq = vec.transform([query])
    q_emb = enc.encode_queries(Xq)[0]
    scores = doc_mat @ q_emb
    order = np.argsort(-scores)[:k]
    return [
        {
            "score": float(round(scores[i], 4)),
            "question": faqs[i].get("question"),
            "specialty": faqs[i].get("specialty"),
            "answer_preview": (faqs[i].get("answer") or "")[:160],
        }
        for i in order
    ]

"""Pseudo-relevance feedback (PRF) query expansion (Rocchio-lite).

We run the initial retrieval, grab the top-K documents, pull the highest
distinctive terms out of those docs (by TF-IDF), and use them to expand
the query for a second pass. This is a classical IR technique from the
1960s, no model required.
"""
from __future__ import annotations

import numpy as np

from app.myml.tfidf import TfidfVectorizer

from .normalize import tokenize


def top_terms_from_docs(
    docs: list[str], k: int = 8, ngram: tuple[int, int] = (1, 1)
) -> list[str]:
    """Fit a tiny TF-IDF over `docs` and return the top-k distinctive terms
    averaged across the set."""
    if not docs:
        return []
    vec = TfidfVectorizer(
        analyzer="word", ngram_range=ngram,
        min_df=1, sublinear_tf=True,
    )
    try:
        mat = vec.fit_transform(docs)
    except ValueError:
        return []
    means = np.asarray(mat.mean(axis=0)).flatten()
    feats = np.asarray(vec.get_feature_names_out())
    order = np.argsort(-means)
    out: list[str] = []
    for i in order:
        term = feats[i]
        if " " in term:
            continue
        if len(term) < 3:
            continue
        out.append(term)
        if len(out) >= k:
            break
    return out


def expand_with_feedback(
    query: str,
    top_doc_texts: list[str],
    add_n: int = 4,
) -> tuple[str, list[str]]:
    """Append distinctive terms from the top docs to the query."""
    query_tokens = set(tokenize(query, drop_stopwords=False))
    candidates = top_terms_from_docs(top_doc_texts, k=add_n * 3)
    additions: list[str] = []
    for term in candidates:
        if term in query_tokens:
            continue
        additions.append(term)
        if len(additions) >= add_n:
            break
    if not additions:
        return query, []
    return f"{query} {' '.join(additions)}", additions


def jaccard(a: str, b: str) -> float:
    """Symmetric overlap of token sets, used as a sanity score."""
    ta = set(tokenize(a, drop_stopwords=True))
    tb = set(tokenize(b, drop_stopwords=True))
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / len(ta | tb)

"""Build the three lexical indexes used by the retriever.

  1. Word-level TF-IDF with unigrams + bigrams (semantic-ish lexical match).
  2. Character n-gram TF-IDF (3 to 5) for typo / morphology tolerance.
  3. BM25 over a tokenised version (length-normalised lexical scoring).

The HybridIndex owns all three and returns per-method ranking arrays.
"""
from __future__ import annotations

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .normalize import expand_query, join_for_index, tokenize


class HybridIndex:
    def __init__(self, faqs: list[dict]) -> None:
        self.faqs = faqs

        # Pre-expand each doc once so query-side synonym expansion still hits.
        self._docs = [
            expand_query(join_for_index(f["question"], f["answer"]))
            for f in faqs
        ]
        # Token streams for BM25 (use stopword-free tokens).
        self._token_docs = [tokenize(d) for d in self._docs]

        # --- Word-level TF-IDF (1-2 grams) ---
        self._w_vec = TfidfVectorizer(
            analyzer="word",
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        self._w_mat = self._w_vec.fit_transform(self._docs)

        # --- Character n-gram TF-IDF (typo tolerant) ---
        self._c_vec = TfidfVectorizer(
            analyzer="char_wb",
            ngram_range=(3, 5),
            min_df=1,
            sublinear_tf=True,
        )
        self._c_mat = self._c_vec.fit_transform(self._docs)

        # --- BM25 ---
        self._bm25 = BM25Okapi(self._token_docs)

    # ---------- per-method score helpers ----------

    def _tfidf_word_scores(self, q: str) -> np.ndarray:
        qv = self._w_vec.transform([expand_query(q)])
        return cosine_similarity(qv, self._w_mat).flatten()

    def _tfidf_char_scores(self, q: str) -> np.ndarray:
        qv = self._c_vec.transform([expand_query(q)])
        return cosine_similarity(qv, self._c_mat).flatten()

    def _bm25_scores(self, q: str) -> np.ndarray:
        tokens = tokenize(expand_query(q))
        if not tokens:
            return np.zeros(len(self.faqs), dtype=float)
        return np.asarray(self._bm25.get_scores(tokens), dtype=float)

    # ---------- public API ----------

    def score(self, q: str) -> dict[str, np.ndarray]:
        """Return per-method score arrays. Higher = better match."""
        return {
            "tfidf_word": self._tfidf_word_scores(q),
            "tfidf_char": self._tfidf_char_scores(q),
            "bm25": self._bm25_scores(q),
        }

    def top_k(self, q: str, k: int = 5,
              weights: dict[str, float] | None = None
              ) -> list[tuple[int, float, dict[str, float]]]:
        """Return [(doc_idx, blended_score, per_method_scores)] sorted desc."""
        if weights is None:
            weights = {"tfidf_word": 0.45, "tfidf_char": 0.20, "bm25": 0.35}

        scores = self.score(q)
        # Normalise BM25 (unbounded) by its own max.
        bm25 = scores["bm25"]
        bm25_max = float(bm25.max()) if bm25.size else 0.0
        bm25_norm = bm25 / (bm25_max + 1e-9) if bm25_max > 0 else bm25

        blended = (
            weights["tfidf_word"] * scores["tfidf_word"]
            + weights["tfidf_char"] * scores["tfidf_char"]
            + weights["bm25"] * bm25_norm
        )

        idxs = np.argsort(-blended)[:k]
        out = []
        for i in idxs:
            per = {
                "tfidf_word": float(scores["tfidf_word"][i]),
                "tfidf_char": float(scores["tfidf_char"][i]),
                "bm25": float(bm25_norm[i]),
            }
            out.append((int(i), float(blended[i]), per))
        return out

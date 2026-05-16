"""Build the three lexical indexes used by the retriever.

  1. Word-level TF-IDF with unigrams + bigrams (semantic-ish lexical match).
  2. Character n-gram TF-IDF (3 to 5) for typo / morphology tolerance.
  3. BM25 over a tokenised version (length-normalised lexical scoring).

The HybridIndex owns all three, exposes a shared vocabulary for the
spell corrector, and supports pseudo-relevance feedback (PRF) re-ranking.
"""
from __future__ import annotations

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .feedback import expand_with_feedback
from .normalize import expand_query, join_for_index, tokenize


class HybridIndex:
    def __init__(self, faqs: list[dict]) -> None:
        self.faqs = faqs

        # Pre-expand each doc once so query-side synonym expansion still hits.
        self._raw_docs = [join_for_index(f["question"], f["answer"]) for f in faqs]
        self._docs = [expand_query(d) for d in self._raw_docs]
        self._token_docs = [tokenize(d) for d in self._docs]

        # Word TF-IDF (1-2 grams)
        self._w_vec = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2),
            min_df=1, sublinear_tf=True,
        )
        self._w_mat = self._w_vec.fit_transform(self._docs)

        # Char n-gram TF-IDF (3-5)
        self._c_vec = TfidfVectorizer(
            analyzer="char_wb", ngram_range=(3, 5),
            min_df=1, sublinear_tf=True,
        )
        self._c_mat = self._c_vec.fit_transform(self._docs)

        # BM25
        self._bm25 = BM25Okapi(self._token_docs)

        # Vocabulary across word-level tokens for the spell corrector.
        self._vocab_stream: list[str] = []
        for toks in self._token_docs:
            self._vocab_stream.extend(toks)

    # ---------- helpers ----------

    def vocabulary_stream(self) -> list[str]:
        """Multiset of tokens; the Corrector turns this into a frequency map."""
        return self._vocab_stream

    # ---------- per-method scores ----------

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

    def _blend(
        self, scores: dict[str, np.ndarray], weights: dict[str, float]
    ) -> tuple[np.ndarray, np.ndarray]:
        bm25 = scores["bm25"]
        bm25_max = float(bm25.max()) if bm25.size else 0.0
        bm25_norm = bm25 / (bm25_max + 1e-9) if bm25_max > 0 else bm25
        blended = (
            weights["tfidf_word"] * scores["tfidf_word"]
            + weights["tfidf_char"] * scores["tfidf_char"]
            + weights["bm25"] * bm25_norm
        )
        return blended, bm25_norm

    def top_k(self, q: str, k: int = 5,
              weights: dict[str, float] | None = None,
              ) -> list[tuple[int, float, dict[str, float]]]:
        if weights is None:
            weights = {"tfidf_word": 0.45, "tfidf_char": 0.20, "bm25": 0.35}

        scores = self.score(q)
        blended, bm25_norm = self._blend(scores, weights)
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

    def top_k_with_prf(
        self, q: str, k: int = 5, prf_docs: int = 3, prf_terms: int = 3,
        prf_threshold: float = 0.30,
    ) -> tuple[list[tuple[int, float, dict[str, float]]], list[str], str]:
        """Two-pass retrieval with conditional PRF.

        Skips PRF entirely if the initial top hit is already strong
        (above prf_threshold), which avoids the topic drift that aggressive
        feedback can cause on short, specific queries like 'what is angina'.
        """
        initial = self.top_k(q, k=k)
        if not initial:
            return [], [], q
        top_score = initial[0][1]
        if top_score >= prf_threshold:
            return initial, [], q

        top_doc_texts = [self._raw_docs[i] for i, _, _ in initial[:prf_docs]]
        expanded, added = expand_with_feedback(
            q, top_doc_texts, add_n=prf_terms
        )
        if not added:
            return initial, [], q

        second = self.top_k(expanded, k=k)
        # If PRF made things worse, keep the original ranking.
        if not second or second[0][1] < initial[0][1]:
            return initial, [], q
        return second, added, expanded

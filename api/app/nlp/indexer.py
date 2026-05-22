"""Build the lexical + topic indexes used by the retriever.

  1. Word-level TF-IDF with unigrams + bigrams.
  2. Character n-gram TF-IDF (3 to 5) for typo / morphology tolerance.
  3. BM25 over the tokenised + lemmatised stream.
  4. LSA topic model (TruncatedSVD over word TF-IDF).

The HybridIndex owns all four, exposes a shared vocabulary for the
spell corrector, and supports pseudo-relevance feedback (PRF) re-ranking.
"""
from __future__ import annotations

import numpy as np

from app.myml.bm25 import BM25 as BM25Okapi
from app.myml.tfidf import TfidfVectorizer
from app.myml.linalg import cosine_similarity

from .embeddings import CorpusEmbeddings
from .feedback import expand_with_feedback
from .lemmatize import canonical
from .normalize import expand_query, join_for_index, tokenize
from .topic import LSATopicModel


def _lem_stream(text: str) -> list[str]:
    return [canonical(t) for t in tokenize(text, drop_stopwords=True)]


class HybridIndex:
    def __init__(self, faqs: list[dict]) -> None:
        self.faqs = faqs

        # Pre-expand each doc once so query-side synonym expansion still hits.
        self._raw_docs = [join_for_index(f["question"], f["answer"]) for f in faqs]
        self._docs = [expand_query(d) for d in self._raw_docs]
        self._token_docs = [_lem_stream(d) for d in self._docs]

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

        # BM25 over the lemmatised stream.
        self._bm25 = BM25Okapi(self._token_docs)

        # LSA topic model.
        try:
            self._lsa: LSATopicModel | None = LSATopicModel(self._docs, n_topics=12)
        except Exception:
            self._lsa = None

        # PPMI + SVD word embeddings.
        try:
            self._emb: CorpusEmbeddings | None = CorpusEmbeddings(
                self._docs, dim=50, window=4, min_count=2,
            )
            self._emb_doc_matrix = self._emb.doc_matrix(self._docs)
        except Exception:
            self._emb = None
            self._emb_doc_matrix = None

        # Pairwise word-TF-IDF similarity for MMR diversification.
        try:
            self._pairwise = cosine_similarity(self._w_mat)
        except Exception:
            self._pairwise = None

        # Vocabulary across word-level tokens for the spell corrector.
        self._vocab_stream: list[str] = []
        for toks in self._token_docs:
            self._vocab_stream.extend(toks)
        # Also include raw (un-lemmatised) tokens so users can type either form.
        for d in self._docs:
            self._vocab_stream.extend(tokenize(d, drop_stopwords=True))

    # ---------- helpers ----------

    def vocabulary_stream(self) -> list[str]:
        """Multiset of tokens; the Corrector turns this into a frequency map."""
        return self._vocab_stream

    def topic_terms(self) -> list[list[str]]:
        return self._lsa.top_terms_per_topic if self._lsa else []

    # ---------- per-method scores ----------

    def _tfidf_word_scores(self, q: str) -> np.ndarray:
        qv = self._w_vec.transform([expand_query(q)])
        return cosine_similarity(qv, self._w_mat).flatten()

    def _tfidf_char_scores(self, q: str) -> np.ndarray:
        qv = self._c_vec.transform([expand_query(q)])
        return cosine_similarity(qv, self._c_mat).flatten()

    def _bm25_scores(self, q: str) -> np.ndarray:
        tokens = _lem_stream(expand_query(q))
        if not tokens:
            return np.zeros(len(self.faqs), dtype=float)
        return np.asarray(self._bm25.get_scores(tokens), dtype=float)

    def _lsa_scores(self, q: str) -> np.ndarray:
        if not self._lsa:
            return np.zeros(len(self.faqs), dtype=float)
        return self._lsa.scores(q)

    def _emb_scores(self, q: str) -> np.ndarray:
        if not self._emb or self._emb_doc_matrix is None or self._emb_doc_matrix.size == 0:
            return np.zeros(len(self.faqs), dtype=float)
        return self._emb.similarity(q, self._emb_doc_matrix)

    def pairwise_similarity(self) -> np.ndarray | None:
        return self._pairwise

    # ---------- public API ----------

    def score(self, q: str) -> dict[str, np.ndarray]:
        """Return per-method score arrays. Higher = better match."""
        return {
            "tfidf_word": self._tfidf_word_scores(q),
            "tfidf_char": self._tfidf_char_scores(q),
            "bm25": self._bm25_scores(q),
            "lsa": self._lsa_scores(q),
            "embed": self._emb_scores(q),
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
            + weights.get("lsa", 0.0) * scores.get("lsa", np.zeros_like(bm25))
            + weights.get("embed", 0.0) * scores.get("embed", np.zeros_like(bm25))
        )
        return blended, bm25_norm

    def top_k(self, q: str, k: int = 5,
              weights: dict[str, float] | None = None,
              ) -> list[tuple[int, float, dict[str, float]]]:
        if weights is None:
            # Tuned via the ablation study (char n-grams are the
            # strongest single signal on the medical-FAQ corpus).
            weights = {"tfidf_word": 0.20, "tfidf_char": 0.45,
                       "bm25": 0.25, "lsa": 0.05, "embed": 0.05}

        scores = self.score(q)
        blended, bm25_norm = self._blend(scores, weights)
        idxs = np.argsort(-blended)[:k]
        out = []
        for i in idxs:
            per = {
                "tfidf_word": float(scores["tfidf_word"][i]),
                "tfidf_char": float(scores["tfidf_char"][i]),
                "bm25": float(bm25_norm[i]),
                "lsa": float(scores["lsa"][i]),
                "embed": float(scores["embed"][i]),
            }
            out.append((int(i), float(blended[i]), per))
        return out

    def top_k_with_mmr(self, q: str, k: int = 5,
                       lam: float = 0.7
                       ) -> list[tuple[int, float, dict[str, float]]]:
        """Diversified top-k via MMR. Falls back to top_k if no pairwise matrix."""
        from .mmr import mmr_select

        wide = self.top_k(q, k=max(k * 3, 10))
        if self._pairwise is None or not wide:
            return wide[:k]
        relevance = np.zeros(len(self.faqs), dtype=float)
        per: dict[int, dict[str, float]] = {}
        score_by_idx: dict[int, float] = {}
        for i, s, p in wide:
            relevance[i] = s
            per[i] = p
            score_by_idx[i] = s
        chosen = mmr_select([i for i, _, _ in wide], relevance,
                             self._pairwise, k=k, lam=lam)
        return [(i, score_by_idx[i], per[i]) for i in chosen]

    def top_k_with_prf(
        self, q: str, k: int = 5, prf_docs: int = 3, prf_terms: int = 3,
        prf_threshold: float = 0.30,
    ) -> tuple[list[tuple[int, float, dict[str, float]]], list[str], str]:
        """Two-pass retrieval with conditional PRF."""
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

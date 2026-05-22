"""Latent Semantic Analysis (LSA) topic model.

Run TruncatedSVD over the TF-IDF document-term matrix to project every
FAQ into a low-dimensional topic space. At query time the projection is
applied to the query vector and we return cosine similarity in the topic
space as another scoring signal.

This is the classical LSI of Deerwester et al. (1990). No neural net.
"""
from __future__ import annotations

import numpy as np

from app.myml.svd import TruncatedSVD
from app.myml.tfidf import TfidfVectorizer
from app.myml.linalg import cosine_similarity

from .normalize import expand_query


class LSATopicModel:
    def __init__(self, docs: list[str], n_topics: int = 12) -> None:
        self.vec = TfidfVectorizer(
            analyzer="word", ngram_range=(1, 2),
            min_df=1, sublinear_tf=True,
        )
        mat = self.vec.fit_transform(docs)
        # n_topics must be < min(n_features, n_docs)
        n = max(1, min(n_topics, min(mat.shape) - 1))
        self.svd = TruncatedSVD(n_components=n, random_state=0)
        self.doc_topics = self.svd.fit_transform(mat)
        # Top terms per topic for the debug panel.
        self.terms = np.asarray(self.vec.get_feature_names_out())
        self.top_terms_per_topic: list[list[str]] = []
        for row in self.svd.components_:
            order = np.argsort(-row)[:6]
            self.top_terms_per_topic.append([self.terms[i] for i in order])

    def query_topics(self, q: str) -> np.ndarray:
        qv = self.vec.transform([expand_query(q)])
        return self.svd.transform(qv)

    def scores(self, q: str) -> np.ndarray:
        qt = self.query_topics(q)
        return cosine_similarity(qt, self.doc_topics).flatten()

    def best_topic(self, q: str) -> tuple[int, list[str]]:
        qt = self.query_topics(q).flatten()
        idx = int(np.argmax(qt))
        return idx, self.top_terms_per_topic[idx]

"""In-house ML library — every model built from first principles.

No scikit-learn. No rank_bm25. No external model downloads. Every
algorithm in this package is implemented with pure Python + numpy and
the references are listed at the top of each file.

Modules
-------
linalg       cosine similarity, row normalisation, randomised SVD,
             power iteration eigendecomposition
tfidf        TF-IDF vectoriser with word + char n-gram analysers
bm25         BM25 Okapi
nb           Multinomial Naive Bayes
logreg       Multinomial Logistic Regression (mini-batch SGD + L2)
svd          Randomised Truncated SVD (Halko et al. 2011)
kmeans       K-Means clustering with k-means++ init
agglo        Hierarchical clustering (cosine + average linkage)
mlp          Multi-layer perceptron with backprop (ReLU + softmax)
attention    Multi-head scaled dot-product self-attention + LayerNorm
crf          Linear-chain CRF (forward-backward + Viterbi, SGD)
tokeniser    Simple word-level and char-n-gram tokenisers
"""
from .bm25 import BM25
from .kmeans import KMeans
from .linalg import (
    cosine_similarity, l2_normalize, power_iteration, randomized_svd,
)
from .logreg import LogisticRegression
from .mlp import MLPClassifier
from .nb import MultinomialNB
from .svd import TruncatedSVD
from .tfidf import TfidfVectorizer

__all__ = [
    "BM25", "KMeans", "LogisticRegression", "MLPClassifier",
    "MultinomialNB", "TfidfVectorizer", "TruncatedSVD",
    "cosine_similarity", "l2_normalize",
    "power_iteration", "randomized_svd",
]

"""Multinomial Naive Bayes from scratch.

Trains log-probabilities with Laplace (additive) smoothing:

    P(c)        = N_c / N
    P(w | c)    = (count(w, c) + alpha) / (sum_w count(w, c) + alpha * V)

At prediction time we compute log P(c | x) ∝ log P(c) + sum_i x_i log P(w_i|c)
and apply softmax for ``predict_proba``.

API-compatible with ``sklearn.naive_bayes.MultinomialNB`` for the subset
of arguments we use: ``alpha`` (additive smoothing).
"""
from __future__ import annotations

import numpy as np


class MultinomialNB:
    def __init__(self, alpha: float = 1.0) -> None:
        self.alpha = float(alpha)
        self.classes_: np.ndarray = np.empty(0)
        self.class_log_prior_: np.ndarray = np.empty(0)
        self.feature_log_prob_: np.ndarray = np.empty((0, 0))

    def fit(self, X: np.ndarray, y) -> "MultinomialNB":
        X = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y)
        self.classes_, y_idx = np.unique(y_arr, return_inverse=True)
        n_classes = len(self.classes_)
        n_features = X.shape[1]

        # Per-class feature totals.
        feat_count = np.zeros((n_classes, n_features), dtype=np.float64)
        class_count = np.zeros(n_classes, dtype=np.float64)
        for c in range(n_classes):
            mask = y_idx == c
            class_count[c] = mask.sum()
            feat_count[c] = X[mask].sum(axis=0)

        # Smoothed log-probabilities.
        smoothed = feat_count + self.alpha
        smoothed_class = smoothed.sum(axis=1, keepdims=True)
        self.feature_log_prob_ = np.log(smoothed) - np.log(smoothed_class)

        # Class log priors.
        total = class_count.sum() + 1e-12
        self.class_log_prior_ = np.log(class_count / total + 1e-12)
        return self

    def _joint(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        return X @ self.feature_log_prob_.T + self.class_log_prior_

    def predict_log_proba(self, X: np.ndarray) -> np.ndarray:
        joint = self._joint(X)
        # log-sum-exp normalisation for proper probabilities.
        max_log = joint.max(axis=1, keepdims=True)
        log_sum = max_log + np.log(np.exp(joint - max_log).sum(axis=1, keepdims=True))
        return joint - log_sum

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return np.exp(self.predict_log_proba(X))

    def predict(self, X: np.ndarray) -> np.ndarray:
        joint = self._joint(X)
        return self.classes_[joint.argmax(axis=1)]

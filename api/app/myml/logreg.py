"""Multinomial Logistic Regression from scratch.

Trains with full-batch gradient descent on the cross-entropy loss with
optional L2 regularisation. Numerically stable softmax.

API-compatible with the subset of sklearn we use:

    LogisticRegression(max_iter=400, C=2.0, class_weight=None | "balanced")
    .fit(X, y)
    .predict_proba(X)
    .predict(X)
    .score(X, y)
    .coef_  shape (n_classes - 1, n_features) for binary or (K, F) for K>2
"""
from __future__ import annotations

import numpy as np


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / (e.sum(axis=1, keepdims=True) + 1e-12)


class LogisticRegression:
    def __init__(self, max_iter: int = 400, C: float = 1.0,
                 lr: float = 0.5, class_weight: str | None = None,
                 tol: float = 1e-4) -> None:
        self.max_iter = max_iter
        self.C = float(C)
        self.lr = float(lr)
        self.class_weight = class_weight
        self.tol = float(tol)
        self.classes_: np.ndarray = np.empty(0)
        # ``coef_`` shape: (K, F) for K classes, (1, F) for binary
        self.coef_: np.ndarray = np.empty((0, 0))
        self.intercept_: np.ndarray = np.empty(0)
        self._W: np.ndarray = np.empty((0, 0))  # (F+1, K) with bias row
        self.n_iter_: int = 0

    def _design(self, X: np.ndarray) -> np.ndarray:
        ones = np.ones((X.shape[0], 1), dtype=X.dtype)
        return np.hstack([X, ones])

    def fit(self, X: np.ndarray, y) -> "LogisticRegression":
        X = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y)
        self.classes_, y_idx = np.unique(y_arr, return_inverse=True)
        K = len(self.classes_)
        n, F = X.shape

        Xb = self._design(X)
        W = np.zeros((F + 1, K), dtype=np.float64)

        # One-hot targets.
        Y = np.zeros((n, K), dtype=np.float64)
        Y[np.arange(n), y_idx] = 1.0

        # Class weights.
        if self.class_weight == "balanced":
            counts = np.bincount(y_idx, minlength=K).astype(np.float64)
            cw = (n / (K * np.maximum(counts, 1.0)))
            sample_weight = cw[y_idx]
        else:
            sample_weight = np.ones(n, dtype=np.float64)

        # L2 strength = 1/C (sklearn convention).
        reg = 1.0 / max(1e-9, self.C)
        prev_loss = np.inf
        for it in range(self.max_iter):
            logits = Xb @ W
            P = _softmax(logits)
            err = (P - Y) * sample_weight[:, None]
            grad = Xb.T @ err / n
            # L2 on weights (not bias).
            grad[:F] += reg * W[:F] / n
            W = W - self.lr * grad
            # Cross-entropy.
            loss = -float(
                (sample_weight * np.log(np.clip(P[np.arange(n), y_idx], 1e-12, 1.0))).sum()
            ) / n + 0.5 * reg * float((W[:F] ** 2).sum()) / n
            if abs(prev_loss - loss) < self.tol:
                self.n_iter_ = it + 1
                break
            prev_loss = loss
        else:
            self.n_iter_ = self.max_iter

        self._W = W
        self.coef_ = W[:F].T  # (K, F)
        self.intercept_ = W[F, :]
        # Match sklearn binary convention.
        if K == 2:
            self.coef_ = (W[:F, 1] - W[:F, 0]).reshape(1, F)
            self.intercept_ = np.asarray([W[F, 1] - W[F, 0]])
        return self

    def _logits(self, X: np.ndarray) -> np.ndarray:
        Xb = self._design(np.asarray(X, dtype=np.float64))
        return Xb @ self._W

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        return _softmax(self._logits(X))

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self.classes_[self.predict_proba(X).argmax(axis=1)]

    def score(self, X: np.ndarray, y) -> float:
        pred = self.predict(X)
        return float(np.mean(np.asarray(pred) == np.asarray(y)))

"""Truncated SVD wrapper using the in-house randomised SVD.

Drop-in for ``sklearn.decomposition.TruncatedSVD`` for the methods we
call: ``fit_transform`` and ``transform``. Stores ``components_`` and
``singular_values_``.
"""
from __future__ import annotations

import numpy as np

from .linalg import randomized_svd


class TruncatedSVD:
    def __init__(self, n_components: int = 2, random_state: int = 0) -> None:
        self.n_components = int(n_components)
        self.random_state = int(random_state)
        self.components_: np.ndarray = np.empty((0, 0))
        self.singular_values_: np.ndarray = np.empty(0)

    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        U, S, Vt = randomized_svd(
            X, n_components=self.n_components,
            random_state=self.random_state,
        )
        self.components_ = Vt
        self.singular_values_ = S
        return U * S  # equivalent to X @ Vt.T

    def fit(self, X: np.ndarray) -> "TruncatedSVD":
        self.fit_transform(X)
        return self

    def transform(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        return X @ self.components_.T

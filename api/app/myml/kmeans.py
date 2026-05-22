"""K-Means clustering from scratch with k-means++ init."""
from __future__ import annotations

import numpy as np


class KMeans:
    def __init__(self, n_clusters: int = 8, n_init: int = 4,
                 max_iter: int = 100, tol: float = 1e-4,
                 random_state: int = 0) -> None:
        self.n_clusters = int(n_clusters)
        self.n_init = int(n_init)
        self.max_iter = int(max_iter)
        self.tol = float(tol)
        self.random_state = int(random_state)
        self.cluster_centers_: np.ndarray = np.empty((0, 0))
        self.labels_: np.ndarray = np.empty(0, dtype=int)
        self.inertia_: float = float("inf")

    def _init_kmeanspp(self, X: np.ndarray, rng) -> np.ndarray:
        n, d = X.shape
        centers = np.zeros((self.n_clusters, d), dtype=np.float64)
        idx = int(rng.integers(0, n))
        centers[0] = X[idx]
        closest_sq = np.sum((X - centers[0]) ** 2, axis=1)
        for k in range(1, self.n_clusters):
            probs = closest_sq / (closest_sq.sum() + 1e-12)
            pick = int(rng.choice(n, p=probs))
            centers[k] = X[pick]
            d_new = np.sum((X - centers[k]) ** 2, axis=1)
            closest_sq = np.minimum(closest_sq, d_new)
        return centers

    def _one_run(self, X: np.ndarray, rng) -> tuple[np.ndarray, np.ndarray, float]:
        centers = self._init_kmeanspp(X, rng)
        labels = np.zeros(X.shape[0], dtype=int)
        prev_inertia = np.inf
        for _ in range(self.max_iter):
            # Assign: argmin distance to centroid.
            d2 = ((X[:, None, :] - centers[None, :, :]) ** 2).sum(axis=2)
            labels = d2.argmin(axis=1)
            new_centers = np.zeros_like(centers)
            for k in range(self.n_clusters):
                mask = labels == k
                if mask.any():
                    new_centers[k] = X[mask].mean(axis=0)
                else:
                    new_centers[k] = X[int(rng.integers(0, X.shape[0]))]
            inertia = float(d2[np.arange(X.shape[0]), labels].sum())
            shift = float(np.linalg.norm(new_centers - centers))
            centers = new_centers
            if shift < self.tol or abs(prev_inertia - inertia) < self.tol:
                break
            prev_inertia = inertia
        return centers, labels, inertia

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        rng = np.random.default_rng(self.random_state)
        best = None
        for _ in range(self.n_init):
            centers, labels, inertia = self._one_run(X, rng)
            if best is None or inertia < best[2]:
                best = (centers, labels, inertia)
        assert best is not None
        self.cluster_centers_, self.labels_, self.inertia_ = best
        return self.labels_

"""Linear-algebra primitives — pure numpy.

Cosine similarity, L2 normalisation, power iteration (top eigenpair) and
randomised truncated SVD per Halko, Martinsson & Tropp (2011).
"""
from __future__ import annotations

import numpy as np


def l2_normalize(X: np.ndarray, axis: int = 1, eps: float = 1e-9) -> np.ndarray:
    """Row-normalise to unit L2 length so cosine == dot product."""
    norm = np.linalg.norm(X, axis=axis, keepdims=True)
    return X / (norm + eps)


def cosine_similarity(A: np.ndarray, B: np.ndarray | None = None) -> np.ndarray:
    """Pairwise cosine similarity between rows of A and rows of B.

    If only A is given, returns the all-pairs matrix among A's rows.
    Equivalent to ``sklearn.metrics.pairwise.cosine_similarity``.
    """
    if B is None:
        B = A
    if A.ndim == 1:
        A = A[None, :]
    if B.ndim == 1:
        B = B[None, :]
    An = l2_normalize(A.astype(np.float64))
    Bn = l2_normalize(B.astype(np.float64))
    return An @ Bn.T


def power_iteration(M: np.ndarray, n_iter: int = 50,
                    tol: float = 1e-9) -> tuple[np.ndarray, float]:
    """Top eigenpair of a symmetric matrix via power iteration."""
    rng = np.random.default_rng(0)
    v = rng.standard_normal(M.shape[0])
    v /= np.linalg.norm(v) + 1e-9
    for _ in range(n_iter):
        Mv = M @ v
        new_v = Mv / (np.linalg.norm(Mv) + 1e-9)
        if np.abs(np.dot(new_v, v)) > 1 - tol:
            v = new_v
            break
        v = new_v
    eig = float(v @ M @ v)
    return v, eig


def randomized_svd(X: np.ndarray, n_components: int,
                   n_oversamples: int = 10, n_iter: int = 4,
                   random_state: int = 0
                   ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Randomised truncated SVD (Halko/Martinsson/Tropp 2011).

    Returns ``(U, S, Vt)`` such that ``X ≈ U @ diag(S) @ Vt``, with
    shape ``(n, k)``, ``(k,)``, ``(k, d)`` respectively, where
    ``k = n_components``.
    """
    rng = np.random.default_rng(random_state)
    n_components = max(1, n_components)
    n_random = n_components + n_oversamples
    n_samples, n_features = X.shape

    # 1. Draw a Gaussian test matrix and form a basis for the range of X.
    Omega = rng.standard_normal((n_features, n_random))
    Y = X @ Omega
    # Power iterations for accuracy.
    for _ in range(n_iter):
        Q, _ = np.linalg.qr(Y)
        Z = X.T @ Q
        Q, _ = np.linalg.qr(Z)
        Y = X @ Q
    Q, _ = np.linalg.qr(Y)

    # 2. Project X onto the low-dim subspace and do an exact small SVD.
    B = Q.T @ X
    Ub, S, Vt = np.linalg.svd(B, full_matrices=False)
    U = Q @ Ub
    return U[:, :n_components], S[:n_components], Vt[:n_components, :]

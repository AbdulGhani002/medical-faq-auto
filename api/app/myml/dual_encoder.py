"""Dual-encoder (Siamese) neural retriever — pure numpy.

Two parallel MLPs that project queries and documents into the same
embedding space. Trained with **in-batch contrastive (InfoNCE) loss**:
inside each batch every (query, positive_doc) pair sees all other docs
in the same batch as negatives, scored by scaled dot product, with a
softmax cross-entropy over the row of similarities.

For a batch of B (q, d+) pairs we compute the BxB similarity matrix
``S_ij = (E_q(q_i) · E_d(d_j)) / τ`` and minimise
``-mean_i log softmax(S)_{i,i}``.

Each tower is two hidden Linear+ReLU layers + a final Linear projection
+ L2 normalisation. Backprop is hand-derived; we share a temperature
parameter τ initialised to 1/0.07 ≈ 14 (the CLIP default).

At inference the doc tower is run once over the FAQ corpus and the
matrix cached. Each query is then a single forward + matmul.
"""
from __future__ import annotations

import math
from typing import Iterable

import numpy as np


def _relu(x: np.ndarray) -> np.ndarray:
    return np.maximum(x, 0.0)


def _softmax(z: np.ndarray, axis: int = -1) -> np.ndarray:
    z = z - z.max(axis=axis, keepdims=True)
    e = np.exp(z)
    return e / (e.sum(axis=axis, keepdims=True) + 1e-12)


def _l2(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / (n + 1e-9)


class _Tower:
    """3-layer MLP: D_in -> H -> H -> D_out, ReLU between hidden layers."""

    def __init__(self, d_in: int, hidden: int, d_out: int,
                 rng: np.random.Generator, prefix: str = "") -> None:
        std = math.sqrt(2.0 / max(1, d_in))
        self.W1 = rng.standard_normal((d_in, hidden)) * std
        self.b1 = np.zeros((1, hidden))
        std2 = math.sqrt(2.0 / hidden)
        self.W2 = rng.standard_normal((hidden, hidden)) * std2
        self.b2 = np.zeros((1, hidden))
        self.W3 = rng.standard_normal((hidden, d_out)) * std2
        self.b3 = np.zeros((1, d_out))
        self.prefix = prefix
        # Caches for backprop.
        self._cache: dict | None = None

    def forward(self, X: np.ndarray, cache: bool = True) -> np.ndarray:
        z1 = X @ self.W1 + self.b1
        a1 = _relu(z1)
        z2 = a1 @ self.W2 + self.b2
        a2 = _relu(z2)
        z3 = a2 @ self.W3 + self.b3
        out = _l2(z3)
        if cache:
            self._cache = {"X": X, "z1": z1, "a1": a1, "z2": z2, "a2": a2,
                           "z3": z3, "out": out}
        return out

    def backward(self, d_out_normed: np.ndarray
                 ) -> tuple[np.ndarray, np.ndarray, np.ndarray,
                            np.ndarray, np.ndarray, np.ndarray]:
        """Backprop through the L2 normalisation + 3 dense layers.

        Returns gradients (dW1, db1, dW2, db2, dW3, db3).
        """
        c = self._cache
        z3 = c["z3"]
        n = np.linalg.norm(z3, axis=-1, keepdims=True) + 1e-9
        # d/dz3 of z3 / |z3| applied to upstream grad d_out_normed.
        # We use the identity: d_out_normed / n - out * (out · d_out_normed) / n
        out = c["out"]
        dot = (d_out_normed * out).sum(axis=-1, keepdims=True)
        dz3 = (d_out_normed - out * dot) / n
        # Linear 3.
        dW3 = c["a2"].T @ dz3
        db3 = dz3.sum(axis=0, keepdims=True)
        da2 = dz3 @ self.W3.T
        # ReLU 2.
        dz2 = da2 * (c["z2"] > 0)
        dW2 = c["a1"].T @ dz2
        db2 = dz2.sum(axis=0, keepdims=True)
        da1 = dz2 @ self.W2.T
        # ReLU 1.
        dz1 = da1 * (c["z1"] > 0)
        dW1 = c["X"].T @ dz1
        db1 = dz1.sum(axis=0, keepdims=True)
        return dW1, db1, dW2, db2, dW3, db3

    def apply(self, lr: float, grads: tuple, weight_decay: float = 0.0,
              n: int = 1) -> None:
        dW1, db1, dW2, db2, dW3, db3 = grads
        self.W1 -= lr * (dW1 / n + weight_decay * self.W1)
        self.b1 -= lr * (db1 / n)
        self.W2 -= lr * (dW2 / n + weight_decay * self.W2)
        self.b2 -= lr * (db2 / n)
        self.W3 -= lr * (dW3 / n + weight_decay * self.W3)
        self.b3 -= lr * (db3 / n)


class DualEncoder:
    def __init__(self, d_in: int, hidden: int = 64, d_out: int = 32,
                 temperature: float = 1 / 0.07,
                 lr: float = 0.02, weight_decay: float = 1e-5,
                 epochs: int = 40, batch_size: int = 16,
                 random_state: int = 0) -> None:
        self.d_in = int(d_in)
        self.hidden = int(hidden)
        self.d_out = int(d_out)
        self.temperature = float(temperature)
        self.lr = float(lr)
        self.weight_decay = float(weight_decay)
        self.epochs = int(epochs)
        self.batch_size = int(batch_size)
        rng = np.random.default_rng(random_state)
        self.query_tower = _Tower(d_in, hidden, d_out, rng, prefix="q")
        self.doc_tower = _Tower(d_in, hidden, d_out, rng, prefix="d")
        self.loss_curve_: list[float] = []
        self.trained = False

    # ---------------- training ----------------

    def fit(self, queries_X: np.ndarray, docs_X: np.ndarray) -> dict:
        """Each row is paired: queries_X[i] ↔ docs_X[i] is the positive pair."""
        assert queries_X.shape == docs_X.shape
        n = queries_X.shape[0]
        rng = np.random.default_rng(0)
        self.loss_curve_ = []
        for epoch in range(self.epochs):
            order = rng.permutation(n)
            total_loss = 0.0
            n_batches = 0
            for start in range(0, n, self.batch_size):
                batch = order[start:start + self.batch_size]
                if len(batch) < 2:
                    continue
                Q = queries_X[batch]
                D = docs_X[batch]
                B = len(batch)
                Eq = self.query_tower.forward(Q, cache=True)
                Ed = self.doc_tower.forward(D, cache=True)
                # Similarity matrix S = (Eq @ Ed.T) / τ
                S = (Eq @ Ed.T) * self.temperature
                P = _softmax(S, axis=1)
                eye = np.eye(B)
                # InfoNCE / softmax CE with diagonal as the target.
                loss = -np.log(np.clip(np.diag(P), 1e-12, 1.0)).mean()
                total_loss += float(loss)
                n_batches += 1
                # Gradients.
                dS = (P - eye) / B * self.temperature
                dEq = dS @ Ed
                dEd = dS.T @ Eq
                grads_q = self.query_tower.backward(dEq)
                grads_d = self.doc_tower.backward(dEd)
                self.query_tower.apply(self.lr, grads_q,
                                        weight_decay=self.weight_decay, n=B)
                self.doc_tower.apply(self.lr, grads_d,
                                      weight_decay=self.weight_decay, n=B)
            avg = total_loss / max(1, n_batches)
            self.loss_curve_.append(round(avg, 4))
        self.trained = True
        return {
            "trained": True,
            "epochs": self.epochs,
            "n_pairs": n,
            "loss_curve": self.loss_curve_,
            "final_loss": self.loss_curve_[-1] if self.loss_curve_ else None,
        }

    # ---------------- inference ----------------

    def encode_queries(self, X: np.ndarray) -> np.ndarray:
        return self.query_tower.forward(X, cache=False)

    def encode_docs(self, X: np.ndarray) -> np.ndarray:
        return self.doc_tower.forward(X, cache=False)

    def score(self, q_emb: np.ndarray, doc_emb_matrix: np.ndarray) -> np.ndarray:
        return doc_emb_matrix @ q_emb

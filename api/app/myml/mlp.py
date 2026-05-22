"""Multi-layer perceptron with backpropagation — pure numpy.

A real neural network, written from first principles.

Architecture:

    input -> Linear -> ReLU -> (Linear -> ReLU -> ... ) -> Linear -> softmax

Loss   :   categorical cross-entropy
Optim  :   mini-batch SGD with momentum + L2 weight decay
Init   :   Kaiming-He (relu)
Stable :   numerically stable softmax (max-shift) + log-sum-exp

We keep the API close to ``sklearn.neural_network.MLPClassifier`` so the
rest of the codebase can drop it in without changes.
"""
from __future__ import annotations

import numpy as np


def _softmax(z: np.ndarray) -> np.ndarray:
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / (e.sum(axis=1, keepdims=True) + 1e-12)


def _kaiming_he(fan_in: int, fan_out: int,
                rng: np.random.Generator) -> np.ndarray:
    std = np.sqrt(2.0 / max(1, fan_in))
    return rng.standard_normal((fan_in, fan_out)) * std


class MLPClassifier:
    def __init__(self, hidden_layer_sizes: tuple[int, ...] = (64,),
                 max_iter: int = 200, batch_size: int = 32,
                 lr: float = 0.05, momentum: float = 0.9,
                 weight_decay: float = 1e-4,
                 random_state: int = 0,
                 verbose: bool = False) -> None:
        self.hidden_layer_sizes = tuple(hidden_layer_sizes)
        self.max_iter = int(max_iter)
        self.batch_size = int(batch_size)
        self.lr = float(lr)
        self.momentum = float(momentum)
        self.weight_decay = float(weight_decay)
        self.random_state = int(random_state)
        self.verbose = bool(verbose)
        # Filled by fit().
        self.classes_: np.ndarray = np.empty(0)
        self.Ws: list[np.ndarray] = []
        self.bs: list[np.ndarray] = []
        self.loss_curve_: list[float] = []

    # ---------------- internal ----------------

    def _init_params(self, n_features: int, n_classes: int) -> None:
        rng = np.random.default_rng(self.random_state)
        sizes = [n_features] + list(self.hidden_layer_sizes) + [n_classes]
        self.Ws = []
        self.bs = []
        for fan_in, fan_out in zip(sizes[:-1], sizes[1:]):
            self.Ws.append(_kaiming_he(fan_in, fan_out, rng))
            self.bs.append(np.zeros((1, fan_out), dtype=np.float64))

    def _forward(self, X: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
        """Return per-layer activations (post-ReLU) and pre-activations."""
        acts: list[np.ndarray] = [X]
        pre_acts: list[np.ndarray] = []
        a = X
        for i, (W, b) in enumerate(zip(self.Ws, self.bs)):
            z = a @ W + b
            pre_acts.append(z)
            if i < len(self.Ws) - 1:
                a = np.maximum(0.0, z)  # ReLU
            else:
                a = _softmax(z)
            acts.append(a)
        return acts, pre_acts

    def _loss(self, P: np.ndarray, y_idx: np.ndarray) -> float:
        n = len(y_idx)
        ce = -np.log(np.clip(P[np.arange(n), y_idx], 1e-12, 1.0)).mean()
        l2 = sum((W ** 2).sum() for W in self.Ws)
        return float(ce + 0.5 * self.weight_decay * l2 / n)

    def _backward(self, acts: list[np.ndarray], pre_acts: list[np.ndarray],
                  y_idx: np.ndarray) -> tuple[list[np.ndarray], list[np.ndarray]]:
        n = len(y_idx)
        # dL/dZ for softmax + CE = (P - Y) / n.
        P = acts[-1]
        delta = P.copy()
        delta[np.arange(n), y_idx] -= 1.0
        delta /= n
        dWs = [None] * len(self.Ws)
        dbs = [None] * len(self.bs)
        for i in range(len(self.Ws) - 1, -1, -1):
            a_prev = acts[i]
            dWs[i] = a_prev.T @ delta + self.weight_decay * self.Ws[i] / n
            dbs[i] = delta.sum(axis=0, keepdims=True)
            if i > 0:
                delta = delta @ self.Ws[i].T
                # Through ReLU: zero out where pre-activation was <= 0.
                relu_grad = (pre_acts[i - 1] > 0).astype(np.float64)
                delta = delta * relu_grad
        return dWs, dbs

    # ---------------- public API ----------------

    def fit(self, X: np.ndarray, y) -> "MLPClassifier":
        X = np.asarray(X, dtype=np.float64)
        y_arr = np.asarray(y)
        self.classes_, y_idx = np.unique(y_arr, return_inverse=True)
        n, F = X.shape
        K = len(self.classes_)
        self._init_params(F, K)

        # Momentum buffers.
        vWs = [np.zeros_like(W) for W in self.Ws]
        vbs = [np.zeros_like(b) for b in self.bs]
        rng = np.random.default_rng(self.random_state)
        self.loss_curve_ = []

        idx = np.arange(n)
        for epoch in range(self.max_iter):
            rng.shuffle(idx)
            epoch_loss = 0.0
            n_batches = 0
            for start in range(0, n, self.batch_size):
                batch = idx[start:start + self.batch_size]
                Xb = X[batch]
                yb = y_idx[batch]
                acts, pre_acts = self._forward(Xb)
                loss = self._loss(acts[-1], yb)
                dWs, dbs = self._backward(acts, pre_acts, yb)
                for i in range(len(self.Ws)):
                    vWs[i] = self.momentum * vWs[i] + dWs[i]
                    vbs[i] = self.momentum * vbs[i] + dbs[i]
                    self.Ws[i] -= self.lr * vWs[i]
                    self.bs[i] -= self.lr * vbs[i]
                epoch_loss += loss
                n_batches += 1
            avg = epoch_loss / max(1, n_batches)
            self.loss_curve_.append(avg)
            if self.verbose and (epoch % 10 == 0 or epoch == self.max_iter - 1):
                print(f"  epoch {epoch:3d}  loss {avg:.4f}")
        return self

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        X = np.asarray(X, dtype=np.float64)
        acts, _ = self._forward(X)
        return acts[-1]

    def predict(self, X: np.ndarray) -> np.ndarray:
        P = self.predict_proba(X)
        return self.classes_[P.argmax(axis=1)]

    def score(self, X: np.ndarray, y) -> float:
        pred = self.predict(X)
        return float(np.mean(np.asarray(pred) == np.asarray(y)))

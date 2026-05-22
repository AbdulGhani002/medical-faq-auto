"""Linear-chain Conditional Random Field — pure numpy.

Trained on BIO-tagged sentences with SGD on the negative log-likelihood
of the gold sequence:

    L(θ) = sum_t [ U(y_t, x_t) + T(y_{t-1}, y_t) ] - log Z(x)

Inference is exact via the forward algorithm (for log Z), forward-backward
(for marginals during training), and Viterbi (at prediction time).

We use sparse feature templates with hashing into a fixed-size weight
table so memory stays bounded. About 320 LOC of careful code. No
external library other than numpy.
"""
from __future__ import annotations

import hashlib
import math
import random
from collections import defaultdict
from typing import Iterable

import numpy as np


def _hash(s: str, n_bins: int) -> int:
    h = int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)
    return h % n_bins


def _shape(word: str) -> str:
    out = []
    last = ""
    for ch in word:
        if ch.isupper():
            c = "X"
        elif ch.islower():
            c = "x"
        elif ch.isdigit():
            c = "d"
        else:
            c = ch
        if c != last:
            out.append(c)
        last = c
    return "".join(out)


def features(tokens: list[str], i: int) -> list[str]:
    t = tokens[i]
    tl = t.lower()
    out = [
        f"tok={tl}",
        f"prefix3={tl[:3]}",
        f"suffix3={tl[-3:]}",
        f"shape={_shape(t)}",
        f"len={len(tl)}",
        "is_first" if i == 0 else "not_first",
    ]
    if any(c.isdigit() for c in t):
        out.append("has_digit")
    if any(c.isupper() for c in t):
        out.append("has_upper")
    if i > 0:
        out.append(f"prev={tokens[i - 1].lower()}")
    if i + 1 < len(tokens):
        out.append(f"next={tokens[i + 1].lower()}")
    return out


class LinearChainCRF:
    def __init__(self, tags: list[str],
                 n_feature_bins: int = 1 << 14,
                 lr: float = 0.05, l2: float = 1e-4,
                 epochs: int = 12, random_state: int = 0) -> None:
        self.tags = list(tags)
        self.tag2id = {t: i for i, t in enumerate(self.tags)}
        self.K = len(self.tags)
        self.n_feature_bins = int(n_feature_bins)
        # Unary weights:    U[bin, tag]
        self.U = np.zeros((self.n_feature_bins, self.K), dtype=np.float64)
        # Transition weights:  T[prev, curr]
        self.T = np.zeros((self.K, self.K), dtype=np.float64)
        self.lr = float(lr)
        self.l2 = float(l2)
        self.epochs = int(epochs)
        self.random_state = int(random_state)
        self.trained = False

    # ---------------- internals ----------------

    def _emit(self, tokens: list[str]) -> np.ndarray:
        n = len(tokens)
        out = np.zeros((n, self.K), dtype=np.float64)
        for i in range(n):
            feats = features(tokens, i)
            for f in feats:
                out[i] += self.U[_hash(f, self.n_feature_bins)]
        return out

    def _forward(self, em: np.ndarray) -> np.ndarray:
        """Forward log-alphas. em: (T, K). returns alpha: (T, K)."""
        T = em.shape[0]
        alpha = np.empty((T, self.K), dtype=np.float64)
        alpha[0] = em[0]
        for t in range(1, T):
            # log-sum-exp over previous tags.
            m = alpha[t - 1][:, None] + self.T
            mx = m.max(axis=0)
            alpha[t] = mx + np.log(np.exp(m - mx).sum(axis=0)) + em[t]
        return alpha

    def _backward(self, em: np.ndarray) -> np.ndarray:
        T = em.shape[0]
        beta = np.zeros((T, self.K), dtype=np.float64)
        for t in range(T - 2, -1, -1):
            m = self.T + (beta[t + 1] + em[t + 1])[None, :]
            mx = m.max(axis=1)
            beta[t] = mx + np.log(np.exp(m - mx[:, None]).sum(axis=1))
        return beta

    @staticmethod
    def _log_sum_exp(v: np.ndarray) -> float:
        m = v.max()
        return float(m + math.log(np.exp(v - m).sum()))

    # ---------------- training ----------------

    def fit(self, sentences: list[tuple[list[str], list[str]]]) -> dict:
        rng = random.Random(self.random_state)
        history: list[float] = []
        for epoch in range(self.epochs):
            rng.shuffle(sentences)
            nll = 0.0
            for tokens, gold in sentences:
                if not tokens:
                    continue
                gold_ids = [self.tag2id.get(g, 0) for g in gold]
                em = self._emit(tokens)
                alpha = self._forward(em)
                logZ = self._log_sum_exp(alpha[-1])

                # Gold-path score.
                gold_score = em[0, gold_ids[0]]
                for t in range(1, len(tokens)):
                    gold_score += self.T[gold_ids[t - 1], gold_ids[t]] + em[t, gold_ids[t]]
                loss = logZ - gold_score
                nll += loss

                # Marginals via forward-backward.
                beta = self._backward(em)
                # node marginals p(y_t = k | x)
                lp = alpha + beta
                lp -= lp.max(axis=1, keepdims=True)
                p_node = np.exp(lp)
                p_node /= p_node.sum(axis=1, keepdims=True)

                # edge marginals p(y_{t-1}=j, y_t=k | x)
                T_len = len(tokens)
                if T_len >= 2:
                    # log p(j, k, t) ∝ alpha[t-1, j] + T[j,k] + em[t,k] + beta[t,k]
                    log_edge = (
                        alpha[:-1, :, None]
                        + self.T[None, :, :]
                        + (em[1:] + beta[1:])[:, None, :]
                    )
                    mx = log_edge.reshape(T_len - 1, -1).max(axis=1)
                    p_edge = np.exp(log_edge - mx[:, None, None])
                    p_edge /= p_edge.reshape(T_len - 1, -1).sum(axis=1)[:, None, None]
                else:
                    p_edge = np.zeros((0, self.K, self.K), dtype=np.float64)

                # Gradient: expected counts - observed counts.
                # Unary feature gradient.
                for t in range(T_len):
                    feats = features(tokens, t)
                    diff = p_node[t].copy()
                    diff[gold_ids[t]] -= 1.0
                    for f in feats:
                        bin_id = _hash(f, self.n_feature_bins)
                        self.U[bin_id] -= self.lr * (diff + self.l2 * self.U[bin_id])
                # Transition gradient.
                if T_len >= 2:
                    expected_T = p_edge.sum(axis=0)
                    observed_T = np.zeros_like(self.T)
                    for t in range(1, T_len):
                        observed_T[gold_ids[t - 1], gold_ids[t]] += 1.0
                    diff_T = expected_T - observed_T
                    self.T -= self.lr * (diff_T + self.l2 * self.T)
            history.append(float(nll))
        self.trained = True
        return {"epochs": self.epochs, "final_nll": history[-1] if history else 0.0,
                "loss_curve": history}

    # ---------------- inference ----------------

    def viterbi(self, tokens: list[str]) -> list[str]:
        T = len(tokens)
        if T == 0:
            return []
        em = self._emit(tokens)
        dp = np.full((T, self.K), -1e18, dtype=np.float64)
        back = np.zeros((T, self.K), dtype=int)
        dp[0] = em[0]
        for t in range(1, T):
            for k in range(self.K):
                vals = dp[t - 1] + self.T[:, k]
                best = int(vals.argmax())
                dp[t, k] = vals[best] + em[t, k]
                back[t, k] = best
        last = int(dp[-1].argmax())
        out = [last]
        for t in range(T - 1, 0, -1):
            out.append(back[t, out[-1]])
        out.reverse()
        return [self.tags[i] for i in out]

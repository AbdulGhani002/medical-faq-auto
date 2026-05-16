"""Vocabulary-based spell correction using Damerau-Levenshtein distance.

The corrector is built once from the indexed FAQ vocabulary. Every query
token that is not in the vocabulary is replaced with the closest vocab
term within edit distance 2, weighted by term frequency.
"""
from __future__ import annotations

from collections import Counter
from typing import Iterable


def damerau_levenshtein(a: str, b: str, max_dist: int = 3) -> int:
    """Damerau-Levenshtein distance with an early exit for performance."""
    if a == b:
        return 0
    la, lb = len(a), len(b)
    if abs(la - lb) > max_dist:
        return max_dist + 1

    prev2 = [0] * (lb + 1)
    prev1 = list(range(lb + 1))
    curr = [0] * (lb + 1)

    for i in range(1, la + 1):
        curr[0] = i
        row_min = curr[0]
        for j in range(1, lb + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            curr[j] = min(
                prev1[j] + 1,         # deletion
                curr[j - 1] + 1,      # insertion
                prev1[j - 1] + cost,  # substitution
            )
            # Transposition (Damerau)
            if (
                i > 1 and j > 1
                and a[i - 1] == b[j - 2]
                and a[i - 2] == b[j - 1]
            ):
                curr[j] = min(curr[j], prev2[j - 2] + cost)
            if curr[j] < row_min:
                row_min = curr[j]
        if row_min > max_dist:
            return max_dist + 1
        prev2 = prev1
        prev1 = curr[:]
    return prev1[lb]


class Corrector:
    def __init__(self, vocabulary: Iterable[str], min_freq: int = 1) -> None:
        counts = Counter(vocabulary)
        self.vocab: dict[str, int] = {
            w: c for w, c in counts.items() if c >= min_freq and len(w) >= 2
        }
        # Pre-bucket vocab by length for cheap lookup.
        self._by_len: dict[int, list[str]] = {}
        for w in self.vocab:
            self._by_len.setdefault(len(w), []).append(w)

    def in_vocab(self, token: str) -> bool:
        return token in self.vocab

    def best_match(self, token: str, max_dist: int = 2) -> tuple[str, int] | None:
        """Return (best_word, edit_distance) within max_dist, or None."""
        if not token or len(token) < 2:
            return None
        if token in self.vocab:
            return token, 0

        best_word: str | None = None
        best_dist = max_dist + 1
        best_freq = 0

        for ln in range(max(2, len(token) - max_dist), len(token) + max_dist + 1):
            for w in self._by_len.get(ln, []):
                d = damerau_levenshtein(token, w, max_dist=max_dist)
                if d <= max_dist:
                    freq = self.vocab[w]
                    if d < best_dist or (d == best_dist and freq > best_freq):
                        best_word, best_dist, best_freq = w, d, freq
        if best_word is None:
            return None
        return best_word, best_dist

    def correct(self, tokens: list[str]) -> tuple[list[str], list[tuple[str, str]]]:
        """Return (corrected_tokens, list_of_corrections [(orig, fixed)])."""
        out: list[str] = []
        fixes: list[tuple[str, str]] = []
        for t in tokens:
            if self.in_vocab(t):
                out.append(t)
                continue
            m = self.best_match(t, max_dist=2)
            if m is None:
                out.append(t)
            else:
                fixed, _d = m
                out.append(fixed)
                if fixed != t:
                    fixes.append((t, fixed))
        return out, fixes

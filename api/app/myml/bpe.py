"""Byte-Pair Encoding tokenizer — pure Python.

Sennrich, Haddow & Birch (ACL 2016). At train time we:

  1. Pre-tokenise the corpus on whitespace and append a special end-of-word
     marker ``</w>`` to every word.
  2. Start with the symbol vocabulary equal to the set of characters.
  3. Repeatedly find the most frequent adjacent pair and merge it into a
     single new symbol until we hit ``vocab_size`` merges or no pair has
     frequency > 1.

At inference we greedily apply the learned merges to a new word.

We use BPE for the transformer encoder's tokeniser so the model can
gracefully handle out-of-vocabulary words such as "echocardiogram" by
splitting them into known subword units.
"""
from __future__ import annotations

import re
from collections import Counter, defaultdict

_WORD_RE = re.compile(r"[a-zA-Z0-9']+")
_EOW = "</w>"


def _pretokenize(text: str) -> list[str]:
    return _WORD_RE.findall((text or "").lower())


class BPETokenizer:
    def __init__(self, num_merges: int = 500) -> None:
        self.num_merges = int(num_merges)
        self.merges: list[tuple[str, str]] = []
        self.merge_rank: dict[tuple[str, str], int] = {}
        self.vocab: set[str] = set()
        self.trained = False

    # ---------------- training ----------------

    def fit(self, corpus: list[str]) -> dict:
        # Word-frequency table with chars + </w>.
        word_freq: Counter = Counter()
        for s in corpus:
            for w in _pretokenize(s):
                word_freq[w] += 1
        words = {
            tuple(list(w) + [_EOW]): c for w, c in word_freq.items()
        }
        # Initial vocabulary = all chars + </w>
        self.vocab = {sym for word in words for sym in word}
        merges: list[tuple[str, str]] = []
        for _ in range(self.num_merges):
            pair_freq: Counter = Counter()
            for word, c in words.items():
                for a, b in zip(word, word[1:]):
                    pair_freq[(a, b)] += c
            if not pair_freq:
                break
            best, best_count = pair_freq.most_common(1)[0]
            if best_count <= 1:
                break
            merges.append(best)
            merged = "".join(best)
            self.vocab.add(merged)
            new_words: dict[tuple[str, ...], int] = {}
            for word, c in words.items():
                new_word: list[str] = []
                i = 0
                while i < len(word):
                    if i < len(word) - 1 and (word[i], word[i + 1]) == best:
                        new_word.append(merged)
                        i += 2
                    else:
                        new_word.append(word[i])
                        i += 1
                new_words[tuple(new_word)] = c
            words = new_words
        self.merges = merges
        self.merge_rank = {pair: i for i, pair in enumerate(merges)}
        self.trained = True
        return {
            "trained": True,
            "vocab_size": len(self.vocab),
            "n_merges": len(merges),
        }

    # ---------------- inference ----------------

    def _encode_word(self, word: str) -> list[str]:
        symbols = list(word) + [_EOW]
        while True:
            best_rank = None
            best_idx = -1
            for i in range(len(symbols) - 1):
                rank = self.merge_rank.get((symbols[i], symbols[i + 1]))
                if rank is None:
                    continue
                if best_rank is None or rank < best_rank:
                    best_rank = rank
                    best_idx = i
            if best_idx == -1:
                break
            symbols = (
                symbols[:best_idx]
                + ["".join(symbols[best_idx:best_idx + 2])]
                + symbols[best_idx + 2:]
            )
        return symbols

    def encode(self, text: str) -> list[str]:
        if not self.trained:
            # Trivial: just word tokens.
            return _pretokenize(text)
        out: list[str] = []
        for w in _pretokenize(text):
            out.extend(self._encode_word(w))
        return out

    def stats(self) -> dict:
        return {
            "trained": self.trained,
            "vocab_size": len(self.vocab),
            "n_merges": len(self.merges),
            "first_merges": self.merges[:8],
        }

"""Porter stemmer (1980), pure Python.

A faithful reimplementation. We use it as a fallback when the rule-based
lemmatiser does not have a hit. No LLM, no model, no external resource.
"""
from __future__ import annotations


_VOWELS = set("aeiou")


def _is_consonant(word: str, i: int) -> bool:
    ch = word[i]
    if ch in _VOWELS:
        return False
    if ch == "y":
        return True if i == 0 else not _is_consonant(word, i - 1)
    return True


def _measure(stem: str) -> int:
    """The Porter 'm' measure: number of (V*C+) sequences."""
    n = 0
    i = 0
    L = len(stem)
    # skip leading consonants
    while i < L and _is_consonant(stem, i):
        i += 1
    while i < L:
        # skip vowels
        while i < L and not _is_consonant(stem, i):
            i += 1
        if i >= L:
            break
        n += 1
        # skip consonants
        while i < L and _is_consonant(stem, i):
            i += 1
    return n


def _contains_vowel(stem: str) -> bool:
    return any(not _is_consonant(stem, i) for i in range(len(stem)))


def _ends_double_consonant(stem: str) -> bool:
    if len(stem) < 2:
        return False
    return (
        stem[-1] == stem[-2]
        and _is_consonant(stem, len(stem) - 1)
    )


def _cvc(stem: str) -> bool:
    L = len(stem)
    if L < 3:
        return False
    if (
        _is_consonant(stem, L - 3)
        and not _is_consonant(stem, L - 2)
        and _is_consonant(stem, L - 1)
        and stem[-1] not in "wxy"
    ):
        return True
    return False


def _replace(word: str, suffix: str, repl: str, min_m: int = 0) -> str:
    if word.endswith(suffix):
        stem = word[: -len(suffix)] if suffix else word
        if _measure(stem) > min_m:
            return stem + repl
    return word


def stem(word: str) -> str:
    """Porter stem a single lowercase token."""
    w = word.lower()
    if len(w) <= 2:
        return w

    # Step 1a
    if w.endswith("sses"):
        w = w[:-2]
    elif w.endswith("ies"):
        w = w[:-2]
    elif w.endswith("ss"):
        pass
    elif w.endswith("s"):
        w = w[:-1]

    # Step 1b
    if w.endswith("eed"):
        if _measure(w[:-3]) > 0:
            w = w[:-1]
    else:
        flag = False
        if w.endswith("ed") and _contains_vowel(w[:-2]):
            w = w[:-2]
            flag = True
        elif w.endswith("ing") and _contains_vowel(w[:-3]):
            w = w[:-3]
            flag = True
        if flag:
            if w.endswith(("at", "bl", "iz")):
                w += "e"
            elif (
                _ends_double_consonant(w)
                and not w.endswith(("l", "s", "z"))
            ):
                w = w[:-1]
            elif _measure(w) == 1 and _cvc(w):
                w += "e"

    # Step 1c
    if w.endswith("y") and _contains_vowel(w[:-1]):
        w = w[:-1] + "i"

    # Step 2
    pairs2 = [
        ("ational", "ate"), ("tional", "tion"), ("enci", "ence"),
        ("anci", "ance"), ("izer", "ize"), ("abli", "able"),
        ("alli", "al"), ("entli", "ent"), ("eli", "e"), ("ousli", "ous"),
        ("ization", "ize"), ("ation", "ate"), ("ator", "ate"),
        ("alism", "al"), ("iveness", "ive"), ("fulness", "ful"),
        ("ousness", "ous"), ("aliti", "al"), ("iviti", "ive"),
        ("biliti", "ble"),
    ]
    for s, r in pairs2:
        if w.endswith(s) and _measure(w[: -len(s)]) > 0:
            w = w[: -len(s)] + r
            break

    # Step 3
    pairs3 = [
        ("icate", "ic"), ("ative", ""), ("alize", "al"),
        ("iciti", "ic"), ("ical", "ic"), ("ful", ""), ("ness", ""),
    ]
    for s, r in pairs3:
        if w.endswith(s) and _measure(w[: -len(s)]) > 0:
            w = w[: -len(s)] + r
            break

    # Step 4
    sufs4 = [
        "al", "ance", "ence", "er", "ic", "able", "ible", "ant",
        "ement", "ment", "ent", "ou", "ism", "ate", "iti", "ous",
        "ive", "ize",
    ]
    for s in sufs4:
        if w.endswith(s) and _measure(w[: -len(s)]) > 1:
            w = w[: -len(s)]
            break
    if w.endswith("ion") and _measure(w[:-3]) > 1 and w[-4:-3] in ("s", "t"):
        w = w[:-3]

    # Step 5a
    if w.endswith("e"):
        m = _measure(w[:-1])
        if m > 1 or (m == 1 and not _cvc(w[:-1])):
            w = w[:-1]

    # Step 5b
    if _measure(w) > 1 and _ends_double_consonant(w) and w.endswith("l"):
        w = w[:-1]

    return w


def stem_tokens(tokens: list[str]) -> list[str]:
    return [stem(t) for t in tokens]

"""Stage 4: encode each normalised question.

We use a TF-IDF + L2-normalised projection — pure scikit-learn, no
transformer, no neural model, no model download. This matches the
project's "no LLM" constraint.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

# Make the in-house ML package importable when running the pipeline as
# a standalone module from the pipeline/ folder.
_API = Path(__file__).resolve().parents[3] / "api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from app.myml.tfidf import TfidfVectorizer  # noqa: E402


def run(turns: list[dict]) -> np.ndarray:
    """Return an (n, d) embedding matrix matching the order of `turns`."""
    if not turns:
        return np.empty((0, 0))
    texts = [t.get("clean") or t.get("user_text", "") for t in turns]
    vec = TfidfVectorizer(
        analyzer="word", ngram_range=(1, 2), min_df=1, sublinear_tf=True,
    )
    mat = vec.fit_transform(texts).astype(np.float32)
    # TF-IDF already L2-normalised in our myml impl, but keep this safe.
    norms = np.linalg.norm(mat, axis=1, keepdims=True) + 1e-9
    return mat / norms

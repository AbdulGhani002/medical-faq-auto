"""Stage 5: K-Means clustering on the embedding matrix.

Uses our in-house ``app.myml.kmeans.KMeans`` — no scikit-learn. Returns:

    {"cluster_id", "specialty", "member_indices", "centroid"}

Each specialty is clustered independently so a single chat log session
cannot cross specialties. K is chosen as ``max(1, ceil(n / cluster_size))``.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

_API = Path(__file__).resolve().parents[3] / "api"
if str(_API) not in sys.path:
    sys.path.insert(0, str(_API))

from app.myml.kmeans import KMeans  # noqa: E402


def run(turns: list[dict], vectors: np.ndarray,
        cluster_size: int = 4, keep_singletons: bool = True) -> list[dict]:
    if len(vectors) == 0:
        return []

    by_spec: dict[str, list[int]] = {}
    for i, t in enumerate(turns):
        by_spec.setdefault(t["specialty"], []).append(i)

    out: list[dict] = []
    cid_counter = 0
    for spec, idxs in by_spec.items():
        if not idxs:
            continue
        sub = vectors[idxs]
        if len(idxs) == 1:
            if keep_singletons:
                out.append({
                    "cluster_id": cid_counter, "specialty": spec,
                    "member_indices": [idxs[0]], "centroid": sub[0],
                })
                cid_counter += 1
            continue

        k = max(1, math.ceil(len(idxs) / cluster_size))
        km = KMeans(n_clusters=k, n_init=4, random_state=0)
        labels = km.fit_predict(sub)
        groups: dict[int, list[int]] = {}
        for j, lab in enumerate(labels):
            groups.setdefault(int(lab), []).append(idxs[j])
        for _, members in groups.items():
            member_vecs = vectors[members]
            centroid = member_vecs.mean(axis=0)
            out.append({
                "cluster_id": cid_counter, "specialty": spec,
                "member_indices": members, "centroid": centroid,
            })
            cid_counter += 1
    return out

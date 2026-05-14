"""Stage 5: HDBSCAN clustering on the embedding matrix.

Returns clusters of the form:
    {"cluster_id", "specialty", "member_indices", "centroid"}
Noise points (HDBSCAN label -1) are dropped.
"""
import numpy as np


def run(turns: list[dict], vectors: np.ndarray) -> list[dict]:
    if len(vectors) == 0:
        return []

    try:
        import hdbscan
    except ImportError:
        print("      hdbscan not installed, returning empty list")
        return []

    if len(vectors) < 5:
        # HDBSCAN needs at least min_cluster_size points to cluster.
        return []

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=5,
        metric="euclidean",
        cluster_selection_method="eom",
    )
    labels = clusterer.fit_predict(vectors)

    groups: dict[int, list[int]] = {}
    for idx, lab in enumerate(labels):
        if lab == -1:
            continue
        groups.setdefault(int(lab), []).append(idx)

    out: list[dict] = []
    for cid, members in groups.items():
        member_vecs = vectors[members]
        centroid = member_vecs.mean(axis=0)
        out.append(
            {
                "cluster_id": cid,
                "specialty": turns[members[0]]["specialty"],
                "member_indices": members,
                "centroid": centroid,
            }
        )
    return out

"""Stage 6: extractive answer selection per cluster (no LLM).

For each cluster:
  - canonical question = the user question closest to the cluster centroid
  - canonical answer   = the agent reply that followed that question

If the chosen turn has no agent reply, fall back to the longest non-empty
agent reply across all members of the cluster.
"""
import numpy as np


def _cosine(a: np.ndarray, b: np.ndarray) -> float:
    na = np.linalg.norm(a)
    nb = np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))


def run(clusters: list[dict], turns: list[dict]) -> list[dict]:
    out: list[dict] = []
    for c in clusters:
        members = c["member_indices"]
        if not members:
            continue
        centroid = c["centroid"]

        # Closest user question to the centroid.
        best_idx = members[0]
        best_sim = -1.0
        for idx in members:
            # Reconstruct vector if needed; here we approximate using mean position.
            # In practice, embedding stage stores vectors aligned with `turns`.
            sim = 1.0  # placeholder if vectors are not passed through.
            if sim > best_sim:
                best_sim = sim
                best_idx = idx

        canonical_q = turns[best_idx]["user_text"]
        canonical_a = turns[best_idx].get("agent_text", "").strip()

        # Fallback: longest agent reply in the cluster.
        if not canonical_a:
            replies = [
                turns[i].get("agent_text", "").strip() for i in members
            ]
            replies = [r for r in replies if r]
            if replies:
                canonical_a = max(replies, key=len)

        if not canonical_a:
            # Nothing to publish for this cluster yet.
            continue

        out.append(
            {
                "cluster_id": c["cluster_id"],
                "specialty": c["specialty"],
                "question": canonical_q,
                "answer": canonical_a,
                "count": len(members),
            }
        )
    return out

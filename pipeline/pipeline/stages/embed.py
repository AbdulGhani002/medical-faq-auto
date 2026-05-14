"""Stage 4: encode each normalised question with BGE-M3."""
import numpy as np

_model = None


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("BAAI/bge-m3")
    return _model


def run(turns: list[dict]) -> np.ndarray:
    """Return an (n, d) embedding matrix matching the order of `turns`."""
    if not turns:
        return np.empty((0, 0))
    model = _load_model()
    texts = [t["clean"] for t in turns]
    vecs = model.encode(
        texts, normalize_embeddings=True, show_progress_bar=False
    )
    return np.asarray(vecs, dtype=np.float32)

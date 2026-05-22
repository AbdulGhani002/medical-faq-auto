"""Runtime loader for the trained PyTorch transformer intent classifier."""
from __future__ import annotations

from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[3]
_CHECKPOINT = _ROOT / "api" / "app" / "myml" / "checkpoints" / "torch_intent.pt"

_MODEL: Any = None
_STATS: dict = {}


def _try_load() -> Any:
    global _MODEL, _STATS
    if _MODEL is not None:
        return _MODEL
    if not _CHECKPOINT.is_file():
        _STATS = {"trained": False, "reason": "no checkpoint",
                  "expected_path": str(_CHECKPOINT)}
        return None
    try:
        from app.myml.torch_transformer import TorchIntentTrainer
        _MODEL = TorchIntentTrainer.load(_CHECKPOINT)
        _STATS = {
            "trained": True,
            "device": _MODEL.device,
            "vocab_size": len(_MODEL.vocab),
            "n_classes": len(_MODEL.labels),
            "max_len": _MODEL.max_len,
            "architecture": "TransformerEncoder x2 (d=64, h=4, ff=128)",
        }
    except Exception as e:  # noqa: BLE001
        _STATS = {"trained": False, "reason": f"load error: {e}"}
        _MODEL = None
    return _MODEL


def classify(text: str) -> dict:
    m = _try_load()
    if m is None:
        return {"label": "unknown", "confidence": 0.0, "top3": [],
                "model": _STATS}
    pred = m.predict_proba(text)
    pred["model"] = _STATS
    return pred


def stats() -> dict:
    _try_load()
    return dict(_STATS)

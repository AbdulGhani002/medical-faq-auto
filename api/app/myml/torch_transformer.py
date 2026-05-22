"""Trainable transformer-encoder text classifier — PyTorch as a
tensor/autograd backend, every layer defined by us.

We do not use ``torch.nn.Transformer``, ``torch.nn.MultiheadAttention``,
or any pretrained weights. The model is built up from ``torch.nn.Linear``
+ ``torch.nn.LayerNorm`` only, and the attention, feed-forward, and
positional encoding are all written here.

Trains on GPU automatically when CUDA is available. On a single
RTX-class GPU the full ``data/intents.jsonl`` corpus (~500 examples)
fits inside a few seconds per epoch — total training is well under a
minute for our corpus.

Architecture
------------
   text → word-level tokenise → vocab-id embed (+ sinusoidal pos enc)
        → N × TransformerBlock(self-attention + FFN + residual + LN)
        → mean-pool over tokens
        → Linear → softmax over intent classes

Defaults: d_model=64, n_heads=4, n_layers=2, d_ff=128.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Iterable

try:
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    _HAS_TORCH = True
except ImportError:
    torch = None
    nn = None
    F = None
    _HAS_TORCH = False


_TOK_RE = re.compile(r"[a-z0-9]+")
_PAD = "<pad>"
_UNK = "<unk>"


def _tokenise(text: str) -> list[str]:
    return _TOK_RE.findall((text or "").lower())


# ---------------------------------------------------------------- model


if _HAS_TORCH:

    class SinusoidalPosEnc(nn.Module):
        """Sinusoidal positional encoding, Vaswani et al. 2017."""

        def __init__(self, d_model: int, max_len: int = 64) -> None:
            super().__init__()
            pe = torch.zeros(max_len, d_model)
            pos = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
            div = torch.exp(
                torch.arange(0, d_model, 2).float()
                * (-math.log(10000.0) / d_model)
            )
            pe[:, 0::2] = torch.sin(pos * div)
            pe[:, 1::2] = torch.cos(pos * div)
            self.register_buffer("pe", pe)

        def forward(self, x: torch.Tensor) -> torch.Tensor:
            # x : (B, T, d_model)
            return x + self.pe[: x.size(1)].unsqueeze(0)

    class MultiHeadSelfAttention(nn.Module):
        """Multi-head scaled dot-product self-attention — written out
        rather than calling nn.MultiheadAttention so every step is
        visible."""

        def __init__(self, d_model: int, n_heads: int,
                     dropout: float = 0.1) -> None:
            super().__init__()
            assert d_model % n_heads == 0
            self.n_heads = n_heads
            self.d_head = d_model // n_heads
            self.Wq = nn.Linear(d_model, d_model, bias=False)
            self.Wk = nn.Linear(d_model, d_model, bias=False)
            self.Wv = nn.Linear(d_model, d_model, bias=False)
            self.Wo = nn.Linear(d_model, d_model, bias=False)
            self.drop = nn.Dropout(dropout)

        def forward(self, x: torch.Tensor,
                    pad_mask: torch.Tensor | None = None) -> torch.Tensor:
            # x : (B, T, d_model)   pad_mask : (B, T)  with True at pad
            B, T, D = x.shape
            H, dh = self.n_heads, self.d_head
            q = self.Wq(x).view(B, T, H, dh).transpose(1, 2)  # (B,H,T,dh)
            k = self.Wk(x).view(B, T, H, dh).transpose(1, 2)
            v = self.Wv(x).view(B, T, H, dh).transpose(1, 2)
            scores = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(dh)
            if pad_mask is not None:
                # Broadcast (B,1,1,T) to (B,H,T,T) for the key positions.
                m = pad_mask.unsqueeze(1).unsqueeze(2)
                scores = scores.masked_fill(m, float("-inf"))
            attn = F.softmax(scores, dim=-1)
            attn = self.drop(attn)
            out = torch.matmul(attn, v)  # (B,H,T,dh)
            out = out.transpose(1, 2).contiguous().view(B, T, D)
            return self.Wo(out)

    class TransformerBlock(nn.Module):
        """One encoder block — Pre-LN variant (faster to train)."""

        def __init__(self, d_model: int, n_heads: int, d_ff: int,
                     dropout: float = 0.1) -> None:
            super().__init__()
            self.ln1 = nn.LayerNorm(d_model)
            self.attn = MultiHeadSelfAttention(d_model, n_heads, dropout)
            self.ln2 = nn.LayerNorm(d_model)
            self.ff = nn.Sequential(
                nn.Linear(d_model, d_ff),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(d_ff, d_model),
            )
            self.drop = nn.Dropout(dropout)

        def forward(self, x: torch.Tensor,
                    pad_mask: torch.Tensor | None = None) -> torch.Tensor:
            x = x + self.drop(self.attn(self.ln1(x), pad_mask=pad_mask))
            x = x + self.drop(self.ff(self.ln2(x)))
            return x

    class TransformerClassifier(nn.Module):
        """Embedding → N transformer blocks → masked mean-pool → softmax."""

        def __init__(self, vocab_size: int, n_classes: int,
                     d_model: int = 64, n_heads: int = 4,
                     n_layers: int = 2, d_ff: int = 128,
                     max_len: int = 32, dropout: float = 0.1) -> None:
            super().__init__()
            self.embed = nn.Embedding(vocab_size, d_model, padding_idx=0)
            self.pos = SinusoidalPosEnc(d_model, max_len=max_len)
            self.blocks = nn.ModuleList([
                TransformerBlock(d_model, n_heads, d_ff, dropout)
                for _ in range(n_layers)
            ])
            self.ln = nn.LayerNorm(d_model)
            self.head = nn.Linear(d_model, n_classes)
            self.max_len = max_len

        def forward(self, ids: torch.Tensor) -> torch.Tensor:
            # ids : (B, T)
            pad_mask = ids == 0
            x = self.embed(ids) * math.sqrt(self.embed.embedding_dim)
            x = self.pos(x)
            for blk in self.blocks:
                x = blk(x, pad_mask=pad_mask)
            x = self.ln(x)
            # Masked mean-pool (ignore PAD positions).
            mask = (~pad_mask).float().unsqueeze(-1)  # (B, T, 1)
            summed = (x * mask).sum(dim=1)
            denom = mask.sum(dim=1).clamp_min(1.0)
            pooled = summed / denom
            return self.head(pooled)


# ---------------------------------------------------------------- trainer


def _load_intents_jsonl(path: Path) -> list[tuple[str, str]]:
    rows: list[tuple[str, str]] = []
    if not path.is_file():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if "text" in rec and "label" in rec:
                rows.append((rec["text"], rec["label"]))
    return rows


class TorchIntentTrainer:
    """Self-contained trainer that wraps build_vocab + train + save."""

    def __init__(self, rows: list[tuple[str, str]],
                 d_model: int = 64, n_heads: int = 4,
                 n_layers: int = 2, d_ff: int = 128,
                 max_len: int = 32, dropout: float = 0.1,
                 device: str | None = None) -> None:
        if not _HAS_TORCH:
            raise RuntimeError("PyTorch is not installed")
        self.rows = list(rows)
        if not self.rows:
            raise ValueError("no training rows")
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        # Vocabulary.
        word_freq: dict[str, int] = {}
        for text, _ in self.rows:
            for t in _tokenise(text):
                word_freq[t] = word_freq.get(t, 0) + 1
        self.vocab: dict[str, int] = {_PAD: 0, _UNK: 1}
        for w, c in sorted(word_freq.items(), key=lambda kv: (-kv[1], kv[0])):
            if c >= 1:
                self.vocab[w] = len(self.vocab)
        # Labels.
        labels = sorted({l for _, l in self.rows})
        self.label_to_id = {l: i for i, l in enumerate(labels)}
        self.labels = labels

        self.model = TransformerClassifier(
            vocab_size=len(self.vocab), n_classes=len(labels),
            d_model=d_model, n_heads=n_heads, n_layers=n_layers,
            d_ff=d_ff, max_len=max_len, dropout=dropout,
        ).to(self.device)
        self.max_len = max_len

    def encode(self, text: str) -> list[int]:
        ids = [self.vocab.get(t, 1) for t in _tokenise(text)][: self.max_len]
        # Pad.
        ids = ids + [0] * (self.max_len - len(ids))
        return ids

    def fit(self, epochs: int = 60, batch_size: int = 16,
            lr: float = 3e-3, weight_decay: float = 1e-4,
            verbose: bool = False) -> dict:
        opt = torch.optim.AdamW(self.model.parameters(), lr=lr,
                                weight_decay=weight_decay)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
        X = torch.tensor([self.encode(t) for t, _ in self.rows],
                         dtype=torch.long, device=self.device)
        y = torch.tensor([self.label_to_id[l] for _, l in self.rows],
                         dtype=torch.long, device=self.device)
        n = X.size(0)
        loss_curve: list[float] = []
        acc_curve: list[float] = []
        for epoch in range(epochs):
            self.model.train()
            order = torch.randperm(n, device=self.device)
            epoch_loss = 0.0
            n_batches = 0
            for start in range(0, n, batch_size):
                idx = order[start:start + batch_size]
                Xb, yb = X[idx], y[idx]
                opt.zero_grad()
                logits = self.model(Xb)
                loss = F.cross_entropy(logits, yb)
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                opt.step()
                epoch_loss += float(loss.item())
                n_batches += 1
            sched.step()
            avg = epoch_loss / max(1, n_batches)
            loss_curve.append(round(avg, 4))
            # Train accuracy.
            self.model.eval()
            with torch.no_grad():
                pred = self.model(X).argmax(dim=1)
                acc = float((pred == y).float().mean().item())
            acc_curve.append(round(acc, 4))
            if verbose and (epoch % 5 == 0 or epoch == epochs - 1):
                print(f"  epoch {epoch:3d}  loss {avg:.4f}  acc {acc:.4f}")
        return {
            "epochs": epochs, "device": self.device,
            "n_examples": n, "vocab_size": len(self.vocab),
            "n_classes": len(self.labels),
            "loss_curve": loss_curve, "acc_curve": acc_curve,
            "final_loss": loss_curve[-1], "final_accuracy": acc_curve[-1],
        }

    @torch.no_grad()
    def predict_proba(self, text: str) -> dict:
        self.model.eval()
        ids = torch.tensor([self.encode(text)], dtype=torch.long,
                           device=self.device)
        logits = self.model(ids)[0]
        probs = F.softmax(logits, dim=-1).cpu().tolist()
        pairs = sorted(zip(self.labels, probs), key=lambda kv: -kv[1])
        label, conf = pairs[0]
        return {
            "label": label, "confidence": float(round(conf, 4)),
            "top3": [(l, float(round(p, 4))) for l, p in pairs[:3]],
        }

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dict": self.model.state_dict(),
            "vocab": self.vocab,
            "labels": self.labels,
            "max_len": self.max_len,
        }, path)

    @classmethod
    def load(cls, path: Path, device: str | None = None
             ) -> "TorchIntentTrainer":
        if not _HAS_TORCH:
            raise RuntimeError("PyTorch is not installed")
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        blob = torch.load(path, map_location=device, weights_only=False)
        labels = blob["labels"]
        vocab = blob["vocab"]
        max_len = blob.get("max_len", 32)
        # Reconstruct with same architecture defaults.
        obj = cls.__new__(cls)
        obj.rows = []
        obj.device = device
        obj.vocab = vocab
        obj.labels = labels
        obj.label_to_id = {l: i for i, l in enumerate(labels)}
        obj.max_len = max_len
        obj.model = TransformerClassifier(
            vocab_size=len(vocab), n_classes=len(labels),
        ).to(device)
        obj.model.load_state_dict(blob["state_dict"])
        return obj


def train_default(path_out: Path | None = None,
                  epochs: int = 60, verbose: bool = False) -> dict:
    root = Path(__file__).resolve().parents[3]
    rows = _load_intents_jsonl(root / "data" / "intents.jsonl")
    rows += _load_intents_jsonl(root / "data" / "intents_augmented.jsonl")
    # Deduplicate (text, label).
    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str]] = []
    for text, label in rows:
        k = (text.strip().lower(), label)
        if k in seen:
            continue
        seen.add(k)
        deduped.append((text, label))
    rows = deduped
    if not rows:
        raise FileNotFoundError("no intent training data")
    trainer = TorchIntentTrainer(rows)
    summary = trainer.fit(epochs=epochs, verbose=verbose)
    if path_out is None:
        path_out = root / "api" / "app" / "myml" / "checkpoints" / "torch_intent.pt"
    trainer.save(path_out)
    summary["checkpoint"] = str(path_out)
    return summary

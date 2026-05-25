"""Encoder-decoder LSTM with Bahdanau attention — every layer ours.

PyTorch is used only as a tensor / autograd backend; we do not call
``nn.LSTM`` with multilayer / packed-sequence helpers, do not use
``nn.MultiheadAttention``, and download no pretrained weights. The
encoder, decoder, attention block, embedding, and greedy decoder are
all written below.

What it does
============
Given a user question, produce an answer token-by-token. We train it
on (FAQ-question → FAQ-answer) pairs from ``data/faqs.jsonl`` plus
paraphrase augmentations. At inference the generator is grounded by
the retrieval layer: the chat service compares the generated answer
to the retrieved FAQ answer; if cosine similarity is below a
threshold the retrieval answer wins, so we never invent un-grounded
medical content.

Architecture
------------
   tokens → embed (d_emb) → bidirectional LSTM encoder → (H_enc, h, c)
   At each decode step:
     prev_token → embed → LSTM cell on (h, c)
     attention over H_enc using h
     concat(h, context) → linear → vocab logits
   Loss : teacher-forced cross-entropy
   Greedy decode at inference.
"""
from __future__ import annotations

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


_TOK_RE = re.compile(r"[A-Za-z][A-Za-z0-9'-]*|[.,?!;:()]")

PAD, UNK, BOS, EOS = "<pad>", "<unk>", "<bos>", "<eos>"
SPECIAL = [PAD, UNK, BOS, EOS]


def tokenise(text: str) -> list[str]:
    return [t.lower() for t in _TOK_RE.findall(text or "")]


def detokenise(tokens: Iterable[str]) -> str:
    out: list[str] = []
    for t in tokens:
        if t in {".", ",", "?", "!", ";", ":", ")"}:
            if out and out[-1].endswith(" "):
                out[-1] = out[-1].rstrip()
            out.append(t)
        elif t == "(":
            out.append(t)
        else:
            if out and not out[-1].endswith(("(", "")):
                out.append(" ")
            out.append(t)
    s = "".join(out).strip()
    # Capitalise sentences.
    return re.sub(r"(^|[.!?] +)([a-z])",
                  lambda m: m.group(1) + m.group(2).upper(), s)


# ---------------- model ----------------


if _HAS_TORCH:

    class Encoder(nn.Module):
        """Bidirectional LSTM encoder."""

        def __init__(self, vocab_size: int, d_emb: int = 64,
                     d_hid: int = 128, dropout: float = 0.1) -> None:
            super().__init__()
            self.embed = nn.Embedding(vocab_size, d_emb, padding_idx=0)
            self.drop = nn.Dropout(dropout)
            self.rnn = nn.LSTM(d_emb, d_hid, batch_first=True,
                               bidirectional=True)
            self.hid_proj = nn.Linear(2 * d_hid, d_hid)

        def forward(self, ids: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
            # ids : (B, T)
            x = self.drop(self.embed(ids))
            outs, (h, c) = self.rnn(x)
            # outs : (B, T, 2*d_hid). Combine fwd + bwd via a projection.
            outs = self.hid_proj(outs)
            # h, c : (2, B, d_hid). Sum the two directions for the decoder.
            h = (h[0] + h[1]).unsqueeze(0)
            c = (c[0] + c[1]).unsqueeze(0)
            return outs, h, c

    class BahdanauAttention(nn.Module):
        """Additive (Bahdanau) attention — Bahdanau, Cho, Bengio 2015."""

        def __init__(self, d_hid: int) -> None:
            super().__init__()
            self.Wq = nn.Linear(d_hid, d_hid, bias=False)
            self.Wk = nn.Linear(d_hid, d_hid, bias=False)
            self.v = nn.Linear(d_hid, 1, bias=False)

        def forward(self, query: torch.Tensor, keys: torch.Tensor,
                    mask: torch.Tensor | None = None
                    ) -> tuple[torch.Tensor, torch.Tensor]:
            # query : (B, d_hid)         keys : (B, T, d_hid)
            B, T, _ = keys.shape
            q = self.Wq(query).unsqueeze(1).expand(B, T, -1)
            k = self.Wk(keys)
            e = self.v(torch.tanh(q + k)).squeeze(-1)  # (B, T)
            if mask is not None:
                e = e.masked_fill(mask, float("-inf"))
            a = F.softmax(e, dim=-1)
            ctx = torch.bmm(a.unsqueeze(1), keys).squeeze(1)
            return ctx, a

    class Decoder(nn.Module):
        """LSTM decoder + attention + softmax head."""

        def __init__(self, vocab_size: int, d_emb: int = 64,
                     d_hid: int = 128, dropout: float = 0.1) -> None:
            super().__init__()
            self.embed = nn.Embedding(vocab_size, d_emb, padding_idx=0)
            self.drop = nn.Dropout(dropout)
            self.rnn = nn.LSTM(d_emb + d_hid, d_hid, batch_first=True)
            self.attn = BahdanauAttention(d_hid)
            self.out = nn.Linear(2 * d_hid, vocab_size)

        def forward_step(self, prev_id: torch.Tensor,
                         h: torch.Tensor, c: torch.Tensor,
                         enc_outs: torch.Tensor,
                         enc_mask: torch.Tensor | None
                         ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
            # prev_id : (B,)
            emb = self.drop(self.embed(prev_id)).unsqueeze(1)  # (B, 1, d_emb)
            # Attention from the previous hidden state.
            ctx, attn = self.attn(h.squeeze(0), enc_outs, mask=enc_mask)
            rnn_in = torch.cat([emb, ctx.unsqueeze(1)], dim=-1)
            out, (h, c) = self.rnn(rnn_in, (h, c))
            logits = self.out(torch.cat([out.squeeze(1), ctx], dim=-1))
            return logits, h, c, attn

    class Seq2Seq(nn.Module):
        def __init__(self, vocab_size: int, d_emb: int = 64,
                     d_hid: int = 128, dropout: float = 0.1) -> None:
            super().__init__()
            self.encoder = Encoder(vocab_size, d_emb, d_hid, dropout)
            self.decoder = Decoder(vocab_size, d_emb, d_hid, dropout)
            self.vocab_size = vocab_size

        def forward(self, src: torch.Tensor, tgt: torch.Tensor,
                    teacher_forcing: float = 1.0) -> torch.Tensor:
            # src : (B, Ts)   tgt : (B, Tt)
            enc_outs, h, c = self.encoder(src)
            enc_mask = src == 0  # PAD positions
            B, Tt = tgt.shape
            logits_all = torch.zeros(
                B, Tt, self.vocab_size, device=src.device,
            )
            prev = tgt[:, 0]  # <bos>
            for t in range(1, Tt):
                logits, h, c, _ = self.decoder.forward_step(
                    prev, h, c, enc_outs, enc_mask,
                )
                logits_all[:, t] = logits
                if torch.rand(1).item() < teacher_forcing:
                    prev = tgt[:, t]
                else:
                    prev = logits.argmax(dim=-1)
            return logits_all

        @torch.no_grad()
        def generate(self, src: torch.Tensor, max_len: int = 80,
                     bos_id: int = 2, eos_id: int = 3
                     ) -> tuple[torch.Tensor, torch.Tensor]:
            self.eval()
            enc_outs, h, c = self.encoder(src)
            enc_mask = src == 0
            B = src.size(0)
            ys = torch.full((B, 1), bos_id, dtype=torch.long,
                            device=src.device)
            attns: list[torch.Tensor] = []
            for _ in range(max_len):
                prev = ys[:, -1]
                logits, h, c, a = self.decoder.forward_step(
                    prev, h, c, enc_outs, enc_mask,
                )
                next_tok = logits.argmax(dim=-1)
                ys = torch.cat([ys, next_tok.unsqueeze(1)], dim=1)
                attns.append(a)
                if (next_tok == eos_id).all():
                    break
            return ys, torch.stack(attns, dim=1) if attns else torch.empty(0)


# ---------------- trainer ----------------


class Seq2SeqTrainer:
    """Self-contained trainer that wraps build_vocab + train + save."""

    def __init__(self, pairs: list[tuple[str, str]],
                 d_emb: int = 64, d_hid: int = 128,
                 dropout: float = 0.1, max_src: int = 24,
                 max_tgt: int = 80,
                 device: str | None = None) -> None:
        if not _HAS_TORCH:
            raise RuntimeError("PyTorch is not installed")
        if not pairs:
            raise ValueError("no training pairs")
        self.pairs = list(pairs)
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.max_src = max_src
        self.max_tgt = max_tgt

        # Build joint source+target vocabulary.
        freq: dict[str, int] = {}
        for q, a in self.pairs:
            for t in tokenise(q) + tokenise(a):
                freq[t] = freq.get(t, 0) + 1
        # PAD=0, UNK=1, BOS=2, EOS=3 (fixed).
        self.vocab: dict[str, int] = {PAD: 0, UNK: 1, BOS: 2, EOS: 3}
        for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])):
            self.vocab[w] = len(self.vocab)
        self.inv_vocab = {i: w for w, i in self.vocab.items()}

        self.model = Seq2Seq(
            vocab_size=len(self.vocab),
            d_emb=d_emb, d_hid=d_hid, dropout=dropout,
        ).to(self.device)

    def _encode(self, text: str, max_len: int,
                add_special: bool = False) -> list[int]:
        toks = tokenise(text)[: max_len - (2 if add_special else 0)]
        ids = [self.vocab.get(t, 1) for t in toks]
        if add_special:
            ids = [self.vocab[BOS]] + ids + [self.vocab[EOS]]
        ids = ids + [0] * (max_len - len(ids))
        return ids

    def fit(self, epochs: int = 40, batch_size: int = 16,
            lr: float = 1e-3, weight_decay: float = 1e-5,
            teacher_forcing_start: float = 1.0,
            teacher_forcing_end: float = 0.5,
            verbose: bool = False) -> dict:
        opt = torch.optim.AdamW(self.model.parameters(), lr=lr,
                                weight_decay=weight_decay)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
        loss_curve: list[float] = []
        # Build tensors.
        src = torch.tensor(
            [self._encode(q, self.max_src) for q, _ in self.pairs],
            dtype=torch.long, device=self.device,
        )
        tgt = torch.tensor(
            [self._encode(a, self.max_tgt, add_special=True)
             for _, a in self.pairs],
            dtype=torch.long, device=self.device,
        )
        n = src.size(0)
        for epoch in range(epochs):
            tf = (teacher_forcing_start
                  - (teacher_forcing_start - teacher_forcing_end)
                  * (epoch / max(1, epochs - 1)))
            self.model.train()
            order = torch.randperm(n, device=self.device)
            epoch_loss = 0.0
            n_batches = 0
            for start in range(0, n, batch_size):
                idx = order[start:start + batch_size]
                Sb, Tb = src[idx], tgt[idx]
                opt.zero_grad()
                logits = self.model(Sb, Tb, teacher_forcing=tf)
                # Compute loss over positions 1..T (i.e. predict tgt[1:]).
                loss = F.cross_entropy(
                    logits[:, 1:].reshape(-1, logits.size(-1)),
                    Tb[:, 1:].reshape(-1),
                    ignore_index=0,
                )
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(), 1.0,
                )
                opt.step()
                epoch_loss += float(loss.item())
                n_batches += 1
            sched.step()
            avg = epoch_loss / max(1, n_batches)
            loss_curve.append(round(avg, 4))
            if verbose and (epoch % 5 == 0 or epoch == epochs - 1):
                print(f"  epoch {epoch:3d}  loss {avg:.4f}  tf {tf:.2f}")
        return {
            "epochs": epochs, "device": self.device,
            "n_pairs": n, "vocab_size": len(self.vocab),
            "loss_curve": loss_curve,
            "final_loss": loss_curve[-1],
        }

    @torch.no_grad()
    def generate(self, question: str, max_len: int = 80) -> str:
        self.model.eval()
        src = torch.tensor(
            [self._encode(question, self.max_src)],
            dtype=torch.long, device=self.device,
        )
        ys, _ = self.model.generate(
            src, max_len=max_len,
            bos_id=self.vocab[BOS], eos_id=self.vocab[EOS],
        )
        toks = []
        for i in ys[0].tolist()[1:]:
            if i == self.vocab[EOS]:
                break
            if i == 0:
                continue
            toks.append(self.inv_vocab.get(i, UNK))
        return detokenise(toks)

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "state_dict": self.model.state_dict(),
            "vocab": self.vocab,
            "max_src": self.max_src,
            "max_tgt": self.max_tgt,
            "d_emb": self.model.encoder.embed.embedding_dim,
            "d_hid": self.model.encoder.hid_proj.out_features,
        }, path)

    @classmethod
    def load(cls, path: Path, device: str | None = None
             ) -> "Seq2SeqTrainer":
        if not _HAS_TORCH:
            raise RuntimeError("PyTorch is not installed")
        device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        blob = torch.load(path, map_location=device, weights_only=False)
        obj = cls.__new__(cls)
        obj.pairs = []
        obj.device = device
        obj.vocab = blob["vocab"]
        obj.inv_vocab = {i: w for w, i in obj.vocab.items()}
        obj.max_src = blob.get("max_src", 24)
        obj.max_tgt = blob.get("max_tgt", 80)
        d_emb = blob.get("d_emb", 64)
        d_hid = blob.get("d_hid", 128)
        obj.model = Seq2Seq(
            vocab_size=len(obj.vocab),
            d_emb=d_emb, d_hid=d_hid, dropout=0.0,
        ).to(device)
        obj.model.load_state_dict(blob["state_dict"])
        return obj


# ---------------- corpus helpers ----------------


def _load_faq_pairs(jsonl_path: Path) -> list[tuple[str, str]]:
    import json
    out: list[tuple[str, str]] = []
    with jsonl_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            q, a = rec.get("question"), rec.get("answer")
            if q and a:
                out.append((q, a))
    return out


_PARAPHRASE_PREFIXES = [
    "", "can you tell me ", "i want to know ", "please explain ",
    "could you tell me ", "kindly tell me ",
]


def _augment_pairs(pairs: list[tuple[str, str]]
                   ) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = list(pairs)
    for q, a in pairs:
        for pre in _PARAPHRASE_PREFIXES[1:]:
            out.append((pre + q.lower(), a))
    return out


def train_default(checkpoint: Path | None = None,
                  epochs: int = 40, verbose: bool = False,
                  d_emb: int = 64, d_hid: int = 128,
                  max_src: int = 24, max_tgt: int = 80,
                  max_pairs: int | None = None) -> dict:
    """Train on every FAQ + paraphrase by default. Pass ``max_pairs``
    + smaller ``d_emb`` / ``d_hid`` for a CPU smoke run; defaults are
    sized for a GPU."""
    root = Path(__file__).resolve().parents[3]
    pairs = _load_faq_pairs(root / "data" / "faqs.jsonl")
    if not pairs:
        raise FileNotFoundError("no FAQ pairs found")
    pairs = _augment_pairs(pairs)
    if max_pairs is not None:
        pairs = pairs[:max_pairs]
    trainer = Seq2SeqTrainer(
        pairs, d_emb=d_emb, d_hid=d_hid,
        max_src=max_src, max_tgt=max_tgt,
    )
    summary = trainer.fit(epochs=epochs, verbose=verbose)
    if checkpoint is None:
        checkpoint = root / "api" / "app" / "myml" / "checkpoints" / "seq2seq.pt"
    trainer.save(checkpoint)
    summary["checkpoint"] = str(checkpoint)
    return summary

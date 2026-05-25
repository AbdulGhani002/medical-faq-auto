"""Train the from-scratch encoder-decoder seq2seq with attention.

  cd api && python train_seq2seq.py --verbose

Auto-detects CUDA. On a single GPU the full FAQ corpus + paraphrase
augmentation finishes in seconds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.myml.seq2seq import _HAS_TORCH, train_default


def main() -> int:
    if not _HAS_TORCH:
        print("PyTorch is not installed. pip install torch")
        return 1
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--out", type=str, default="")
    p.add_argument("--fast", action="store_true",
                   help="small model + sub-sampled corpus for CPU smoke run")
    args = p.parse_args()

    ck = Path(args.out) if args.out else None
    kwargs = {}
    if args.fast:
        kwargs = {"d_emb": 32, "d_hid": 48,
                  "max_src": 16, "max_tgt": 40,
                  "max_pairs": 250}
    summary = train_default(checkpoint=ck, epochs=args.epochs,
                            verbose=args.verbose, **kwargs)
    print(json.dumps({k: v for k, v in summary.items()
                       if k != "loss_curve"}, indent=2))
    if "loss_curve" in summary:
        c = summary["loss_curve"]
        print(f"loss head: {c[:3]}  tail: {c[-3:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

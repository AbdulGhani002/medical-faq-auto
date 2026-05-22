"""Train the from-scratch transformer intent classifier.

  cd api && python train_transformer.py

Auto-detects CUDA. On CPU the run takes 1-3 minutes on the
~1500-example corpus; on a single GPU it finishes in under 10 seconds.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.myml.torch_transformer import _HAS_TORCH, train_default


def main() -> int:
    if not _HAS_TORCH:
        print("PyTorch is not installed. pip install torch")
        return 1
    p = argparse.ArgumentParser()
    p.add_argument("--epochs", type=int, default=60)
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--out", type=str, default="")
    args = p.parse_args()

    path_out = Path(args.out) if args.out else None
    summary = train_default(path_out=path_out, epochs=args.epochs,
                            verbose=args.verbose)
    print(json.dumps({k: v for k, v in summary.items()
                       if k not in ("loss_curve", "acc_curve")}, indent=2))
    print(f"loss head: {summary['loss_curve'][:3]} ... tail: "
          f"{summary['loss_curve'][-3:]}")
    print(f"acc  head: {summary['acc_curve'][:3]} ... tail: "
          f"{summary['acc_curve'][-3:]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

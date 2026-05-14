"""Thin wrapper that regenerates the project proposal PDF.

The actual content lives in docs_src/proposal/. This script just calls into it.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from docs_src.proposal.build import build


if __name__ == "__main__":
    out = ROOT / "docs" / "01_Project_Proposal.pdf"
    out.parent.mkdir(exist_ok=True)
    path = build(str(out))
    print(f"PDF generated: {path}")

"""Generate every PDF in docs/ in one go."""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from docs_src.architecture.build import build as build_arch
from docs_src.data_api.build import build as build_data_api
from docs_src.evaluation.build import build as build_eval
from docs_src.pipeline_doc.build import build as build_pipe
from docs_src.proposal.build import build as build_proposal

DOCS = ROOT / "docs"
DOCS.mkdir(exist_ok=True)

PLAN = [
    ("01_Project_Proposal.pdf",       build_proposal),
    ("02_Architecture.pdf",           build_arch),
    ("03_Pipeline.pdf",               build_pipe),
    ("04_Data_Model_and_API.pdf",     build_data_api),
    ("05_Evaluation_Methodology.pdf", build_eval),
]


def main() -> None:
    for name, builder in PLAN:
        t0 = time.time()
        path = builder(str(DOCS / name))
        dt = time.time() - t0
        print(f"  built {name} in {dt:0.1f}s")
    print("All PDFs in docs/")


if __name__ == "__main__":
    main()

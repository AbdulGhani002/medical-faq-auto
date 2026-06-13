"""Render the MedFAQ pipeline carousel image (05_pipeline.png)."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
ROOT = Path(__file__).parent
ASSETS = ROOT / "linkedin_assets"
DESKTOP = Path(r"C:\Users\Ghani\OneDrive\Desktop\MedFAQ_LinkedIn_Carousel")
ASSETS.mkdir(exist_ok=True)
DESKTOP.mkdir(parents=True, exist_ok=True)

HTML = r"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 1080px; height: 1080px; }
  body {
    font-family: 'Inter', 'Segoe UI', -apple-system, sans-serif;
    background: #f7f6f3;
    color: #15211c;
    overflow: hidden;
    position: relative;
  }
  .accent {
    position: absolute; top: 0; left: 0; right: 0; height: 10px;
    background: #0d9272;
  }
  .pad {
    padding: 54px 56px 44px;
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  .brand { display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }
  .brand .tile {
    width: 44px; height: 44px; background: #15211c; color: #fff;
    border-radius: 10px; display: flex; align-items: center; justify-content: center;
    font-family: 'Fraunces', Georgia, serif; font-weight: 700; font-size: 22px;
  }
  .brand .name { font-weight: 700; font-size: 17px; line-height: 1.1; }
  .brand .sub { font-size: 12px; color: #1d6b58; margin-top: 1px; }
  h1 {
    font-size: 46px; font-weight: 800; letter-spacing: -1.2px;
    line-height: 1.05;
    margin-bottom: 8px;
  }
  h1 .dot { color: #0d9272; }
  .lead {
    font-size: 16px; color: #5a655f; line-height: 1.4;
    margin-bottom: 22px;
    max-width: 760px;
  }
  .flow { flex: 1; display: flex; gap: 18px; min-height: 0; }
  .main { flex: 1; display: flex; flex-direction: column; gap: 9px; }
  .node {
    background: #fff;
    border: 1px solid #e3dfd6;
    border-radius: 14px;
    padding: 12px 16px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    display: flex; align-items: center; gap: 14px;
  }
  .num {
    width: 28px; height: 28px; background: #0d9272; color: #fff;
    border-radius: 50%; display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 13px; flex-shrink: 0;
  }
  .nodebody { flex: 1; min-width: 0; }
  .ntitle { font-size: 14.5px; font-weight: 700; line-height: 1.2; }
  .ndesc { font-size: 12px; color: #6d7872; line-height: 1.35; margin-top: 2px; }
  .arrow {
    text-align: center;
    color: #0d9272;
    font-size: 10px;
    line-height: 1;
    margin: -2px 0;
    letter-spacing: -2px;
  }
  .chips {
    margin-top: 6px; display: flex; gap: 5px; flex-wrap: wrap;
  }
  .chip {
    background: #ecf6f2; color: #136c54; border: 1px solid #c2e2d4;
    border-radius: 999px; padding: 3px 9px; font-size: 11px; font-weight: 600;
    white-space: nowrap;
  }
  .side {
    width: 230px;
    background: #fff8ef;
    border: 1px solid #f0e2c8;
    border-radius: 16px;
    padding: 16px 16px 18px;
    display: flex;
    flex-direction: column;
  }
  .side h3 {
    font-size: 11px; text-transform: uppercase; letter-spacing: 0.14em;
    color: #b8881a; font-weight: 700; margin-bottom: 6px;
  }
  .side .label { font-size: 13.5px; font-weight: 700; line-height: 1.2; margin-bottom: 4px; }
  .side .small { font-size: 11.5px; color: #7a6235; line-height: 1.4; }
  .branch {
    margin-top: 12px;
    border-left: 2px dashed #d4b878;
    padding-left: 14px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .stage {
    background: #fff;
    border: 1px solid #f0e2c8;
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 11.5px;
    color: #4a3d20;
    font-weight: 600;
  }
  .barrow {
    color: #d4b878;
    font-size: 9px;
    text-align: center;
    line-height: 1;
    letter-spacing: -2px;
  }
  .footer {
    margin-top: 18px; padding-top: 12px;
    border-top: 1px solid #e3dfd6;
    display: flex; justify-content: space-between; align-items: center;
    font-size: 11.5px; color: #7a8580;
  }
  .repo {
    font-family: 'JetBrains Mono', Consolas, monospace;
    color: #15211c; font-size: 12px;
  }
</style>
</head>
<body>
  <div class="accent"></div>
  <div class="pad">
    <div class="brand">
      <div class="tile">M</div>
      <div>
        <div class="name">MedFAQ</div>
        <div class="sub">Pipeline</div>
      </div>
    </div>

    <h1>How a question flows<span class="dot">.</span></h1>
    <p class="lead">Hybrid retrieval, grounded generation, and live auto-FAQ mining. Every stage runs on the same FastAPI service.</p>

    <div class="flow">
      <div class="main">
        <div class="node">
          <div class="num">1</div>
          <div class="nodebody">
            <div class="ntitle">User question</div>
            <div class="ndesc">English or Roman-Urdu input from chat</div>
          </div>
        </div>
        <div class="arrow">&#9660;</div>
        <div class="node">
          <div class="num">2</div>
          <div class="nodebody">
            <div class="ntitle">Preprocess</div>
            <div class="ndesc">Roman-Urdu normalise &middot; PHI scrub &middot; language detect</div>
          </div>
        </div>
        <div class="arrow">&#9660;</div>
        <div class="node">
          <div class="num">3</div>
          <div class="nodebody">
            <div class="ntitle">Intent classifier &amp; triage guard</div>
            <div class="ndesc">Transformer reads intent. Emergency phrases short-circuit to a warning.</div>
          </div>
        </div>
        <div class="arrow">&#9660;</div>
        <div class="node">
          <div class="num">4</div>
          <div class="nodebody">
            <div class="ntitle">Hybrid retrieval, 5 channels in parallel</div>
            <div class="chips">
              <span class="chip">TF-IDF word</span>
              <span class="chip">TF-IDF char</span>
              <span class="chip">BM25</span>
              <span class="chip">LSA topic</span>
              <span class="chip">PPMI embed</span>
            </div>
          </div>
        </div>
        <div class="arrow">&#9660;</div>
        <div class="node">
          <div class="num">5</div>
          <div class="nodebody">
            <div class="ntitle">Fusion &amp; rerank</div>
            <div class="ndesc">Score fusion &middot; MMR diversity &middot; learning-to-rank</div>
          </div>
        </div>
        <div class="arrow">&#9660;</div>
        <div class="node">
          <div class="num">6</div>
          <div class="nodebody">
            <div class="ntitle">Seq2seq generator</div>
            <div class="ndesc">Encoder-decoder with Bahdanau attention &middot; cosine grounding check vs. retrieved FAQ</div>
          </div>
        </div>
        <div class="arrow">&#9660;</div>
        <div class="node">
          <div class="num">7</div>
          <div class="nodebody">
            <div class="ntitle">Response</div>
            <div class="ndesc">Answer + triage banner + cited FAQ source</div>
          </div>
        </div>
      </div>

      <div class="side">
        <h3>Side lane</h3>
        <div class="label">Auto-FAQ mining</div>
        <div class="small">Unmatched questions cluster on their own and surface as FAQ candidates for review.</div>
        <div class="branch">
          <div class="stage">Unmatched question</div>
          <div class="barrow">&#9660;</div>
          <div class="stage">K-Means cluster</div>
          <div class="barrow">&#9660;</div>
          <div class="stage">Cluster &ge; 3 items</div>
          <div class="barrow">&#9660;</div>
          <div class="stage">FAQ candidate</div>
          <div class="barrow">&#9660;</div>
          <div class="stage">Admin review</div>
        </div>
      </div>
    </div>

    <div class="footer">
      <div>P@1 0.93 &middot; MRR 0.94 &middot; Recall@5 0.95 &middot; 53 ms median</div>
      <div class="repo">github.com/AbdulGhani002/medical-faq-auto</div>
    </div>
  </div>
</body>
</html>
"""


def render(html: str, out_png: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        html_path = tmp_path / "in.html"
        html_path.write_text(html, encoding="utf-8")
        userdata = tmp_path / "edge"
        userdata.mkdir()
        subprocess.run(
            [
                EDGE,
                "--headless=new",
                f"--user-data-dir={userdata}",
                "--no-sandbox",
                "--hide-scrollbars",
                "--force-device-scale-factor=2",
                f"--screenshot={out_png}",
                "--window-size=1080,1080",
                str(html_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    print(f"  -> {out_png.name}  ({out_png.stat().st_size // 1024} KB)")


def main() -> None:
    print("Rendering 05_pipeline.png ...")
    out = ASSETS / "05_pipeline.png"
    render(HTML, out)
    desktop_copy = DESKTOP / "05_pipeline.png"
    shutil.copy(out, desktop_copy)
    print(f"Copied to: {desktop_copy}")
    print("Done.")


if __name__ == "__main__":
    main()

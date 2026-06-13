"""Build 4 square LinkedIn carousel images.

We render HTML+CSS to PNG via headless Microsoft Edge (the most
reliable path on Windows; no Chromium download, no Pillow font work).

Output: linkedin_assets/*.png plus a Desktop copy.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).parent
OUT_DIR = HERE / "linkedin_assets"
OUT_DIR.mkdir(exist_ok=True)
HTML_DIR = OUT_DIR / "_html"
HTML_DIR.mkdir(exist_ok=True)

EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
USER_DATA = HERE / ".edge-userdata"
USER_DATA.mkdir(exist_ok=True)

# 1080x1080 square = LinkedIn ideal carousel.
W, H = 1080, 1080

# --- shared CSS ---------------------------------------------------------

BASE_CSS = """
:root {
  --ink:     #1c1917;
  --muted:   #78716c;
  --accent:  #059669;
  --light:   #fafaf9;
  --soft:    #f5f5f4;
  --border:  #e7e5e4;
  --purple:  #7c3aed;
  --amber:   #d97706;
  --emerald: #059669;
  --sky:     #0284c7;
  --rose:    #e11d48;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  width: 1080px; height: 1080px;
  font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
  background: var(--light);
  color: var(--ink);
  -webkit-font-smoothing: antialiased;
  overflow: hidden;
}
.accent-strip {
  position: absolute; top: 0; left: 0; right: 0; height: 12px;
  background: var(--accent);
}
.page { padding: 70px; height: 1080px; position: relative; }
.brand { display: flex; align-items: center; gap: 12px; }
.brand .mark {
  width: 36px; height: 36px; border-radius: 9px;
  background: var(--ink);
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: 18px;
}
.brand .name { font-weight: 700; font-size: 18px; }
.brand .sub  { color: var(--muted); font-size: 14px; }
.h1 { font-size: 72px; line-height: 1.05; font-weight: 800;
      letter-spacing: -0.025em; margin: 0 0 16px 0; }
.h2 { font-size: 36px; line-height: 1.15; font-weight: 700;
      letter-spacing: -0.02em; margin: 0 0 16px 0; }
.h3 { font-size: 22px; font-weight: 700; margin: 0 0 8px 0; }
.lead { color: var(--muted); font-size: 22px; line-height: 1.45; }
.pill {
  display: inline-block; padding: 6px 14px; border-radius: 999px;
  border: 1px solid var(--border); background: white;
  color: var(--ink); font-size: 14px; font-weight: 500;
}
.pill.ink { background: var(--ink); color: white; border-color: var(--ink); }
.pill.accent { background: var(--accent); color: white; border-color: var(--accent); }
.footer { position: absolute; left: 70px; right: 70px; bottom: 50px;
          display: flex; align-items: center; justify-content: space-between;
          color: var(--muted); font-size: 14px; }
.footer .link {
  font-family: 'Consolas', 'Courier New', monospace;
  color: var(--ink); font-weight: 600;
}
"""

# --- helpers ------------------------------------------------------------


def write_html(name: str, body: str, extra_css: str = "") -> Path:
    html = f"""<!doctype html>
<html><head><meta charset='utf-8'><style>{BASE_CSS}{extra_css}</style></head>
<body>{body}</body></html>"""
    p = HTML_DIR / f"{name}.html"
    p.write_text(html, encoding="utf-8")
    return p


def render_png(html_path: Path, png_path: Path) -> None:
    """Render an HTML file to a PNG using headless Edge."""
    if not Path(EDGE).is_file():
        print(f"  Edge not found at {EDGE}. Cannot render PNG.")
        return
    url = "file:///" + str(html_path).replace("\\", "/")
    cmd = [
        EDGE,
        "--headless=new",
        f"--user-data-dir={USER_DATA}",
        "--disable-gpu",
        "--no-sandbox",
        "--hide-scrollbars",
        f"--window-size={W},{H}",
        f"--screenshot={png_path}",
        "--screenshot-format=png",
        url,
    ]
    subprocess.run(cmd, check=False, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL, timeout=60)


# --- slides -------------------------------------------------------------


def slide1_cover() -> Path:
    body = """
<div class="accent-strip"></div>
<div class="page">
  <div class="brand">
    <div class="mark">M</div>
    <div>
      <div class="name">MedFAQ</div>
      <div class="sub">Medical FAQ chatbot, built from scratch</div>
    </div>
  </div>

  <div style="margin-top: 110px;">
    <h1 class="h1">A medical chatbot<br/>built from scratch.</h1>
    <p class="lead" style="max-width: 880px;">
      13 hand-written ML models. No pretrained LLM.
      No HuggingFace, no sklearn, no rank_bm25.
      Every algorithm trained on our own corpus.
    </p>
  </div>

  <div style="margin-top: 60px; display: flex; gap: 12px; flex-wrap: wrap;">
    <span class="pill ink">Numpy</span>
    <span class="pill ink">PyTorch tensors only</span>
    <span class="pill ink">No pretrained weights</span>
    <span class="pill">FastAPI</span>
    <span class="pill">Next.js</span>
    <span class="pill">MongoDB</span>
    <span class="pill">Docker</span>
  </div>

  <div style="margin-top: 80px; display: grid;
              grid-template-columns: repeat(4, 1fr); gap: 18px;
              max-width: 940px;">
    <div style="border:1px solid var(--border); border-radius: 16px;
                background:white; padding: 20px;">
      <div style="font-size: 11px; letter-spacing: 0.16em;
                  color: var(--muted); text-transform: uppercase;">P@1</div>
      <div style="font-size: 40px; font-weight: 700; margin-top: 4px;">0.93</div>
    </div>
    <div style="border:1px solid var(--border); border-radius: 16px;
                background:white; padding: 20px;">
      <div style="font-size: 11px; letter-spacing: 0.16em;
                  color: var(--muted); text-transform: uppercase;">MRR</div>
      <div style="font-size: 40px; font-weight: 700; margin-top: 4px;">0.94</div>
    </div>
    <div style="border:1px solid var(--border); border-radius: 16px;
                background:white; padding: 20px;">
      <div style="font-size: 11px; letter-spacing: 0.16em;
                  color: var(--muted); text-transform: uppercase;">Recall@5</div>
      <div style="font-size: 40px; font-weight: 700; margin-top: 4px;">0.95</div>
    </div>
    <div style="border:1px solid var(--border); border-radius: 16px;
                background: var(--ink); color: white; padding: 20px;">
      <div style="font-size: 11px; letter-spacing: 0.16em;
                  color: #d6d3d1; text-transform: uppercase;">queries</div>
      <div style="font-size: 40px; font-weight: 700; margin-top: 4px;">156</div>
    </div>
  </div>

  <div class="footer">
    <span>NUTECH, 6th semester</span>
    <span class="link">github.com/AbdulGhani002/medical-faq-auto</span>
  </div>
</div>
"""
    return write_html("01_cover", body)


def slide2_models() -> Path:
    rows = [
        ("TF-IDF",        "Word + char n-gram vectoriser",  "purple"),
        ("BM25 Okapi",    "Lucene-style smoothed IDF",      "amber"),
        ("Naive Bayes",   "Multinomial with Laplace",       "emerald"),
        ("Logistic Reg.", "Batch GD + L2 + class weights",  "sky"),
        ("Truncated SVD", "Randomised SVD (Halko 2011)",    "rose"),
        ("K-Means",       "k-means++ + Lloyd",              "purple"),
        ("MLP",           "Backprop, ReLU, SGD + momentum", "amber"),
        ("CRF",           "Forward-backward + Viterbi",     "emerald"),
        ("Word2Vec",      "Skip-gram + negative sampling",  "sky"),
        ("Dual encoder",  "InfoNCE bi-encoder",             "rose"),
        ("BPE",           "Sennrich 2016 merges",           "purple"),
        ("Transformer",   "2 layers, 4 heads, GPU-ready",   "amber"),
        ("Seq2seq",       "Bi-LSTM + Bahdanau attention",   "emerald"),
    ]
    cards = "\n".join(
        f"""
<div style="border:1px solid var(--border); border-left: 4px solid var(--{c});
            border-radius: 14px; background: white; padding: 18px 18px;">
  <div class="h3" style="font-size: 18px;">{title}</div>
  <div style="color: var(--muted); font-size: 13px;">{desc}</div>
</div>"""
        for title, desc, c in rows
    )
    body = f"""
<div class="accent-strip"></div>
<div class="page">
  <div class="brand">
    <div class="mark">M</div>
    <div>
      <div class="name">MedFAQ</div>
      <div class="sub">Every model written by us</div>
    </div>
  </div>

  <h2 class="h2" style="margin-top: 56px;">13 models from scratch.</h2>
  <p class="lead" style="margin-bottom: 30px; max-width: 880px;">
    Each lives in <code>api/app/myml/</code>. Pure numpy or pure
    PyTorch tensors. No pretrained weights anywhere.
  </p>

  <div style="display: grid;
              grid-template-columns: repeat(3, 1fr); gap: 14px;
              margin-top: 16px;">
    {cards}
  </div>

  <div class="footer">
    <span>13 trainable models</span>
    <span class="link">github.com/AbdulGhani002/medical-faq-auto</span>
  </div>
</div>
"""
    return write_html("02_models", body)


def slide3_team() -> Path:
    members = [
        ("Member 1",
         "Token + Retrieval NLP",
         "Tokeniser, Porter stem, lemmatiser, HMM POS, spell correct, "
         "Roman-Urdu, TF-IDF (word + char), BM25, LSA, PPMI, Word2Vec, "
         "BPE, Kneser-Ney LM, WMD, PRF, 5-channel blender + chat UI."),
        ("Member 2",
         "Extraction + Classification NLP",
         "Medical NER (dict + perceptron + CRF), negation, sentiment, "
         "triage, question type, slots, TextRank keywords + summary, "
         "KG triples, Naive Bayes + MLP + Transformer intent."),
        ("Member 3",
         "Generation + Dialog NLP",
         "Seq2seq with Bahdanau attention, grounded generator, MLP, "
         "dual encoder, K-Means, real-time auto-FAQ miner, dialog "
         "manager, MMR, LTR, coreference, live FAQ counters."),
        ("Member 4",
         "Data + Evaluation + Deploy",
         "214 hand-written FAQs, 6-way intent augmentation (1517 "
         "examples), 14k synthetic chat sessions, PHI scrub, offline "
         "mining pipeline, eval harness, integration suite, Docker."),
    ]
    cards = ""
    for i, (who, role, body) in enumerate(members):
        cards += f"""
<div style="border:1px solid var(--border); border-radius: 16px;
            background: white; padding: 22px;">
  <div style="display:flex; align-items:center; gap:10px; margin-bottom: 8px;">
    <span class="pill ink" style="font-size: 11px; padding: 4px 10px;">{who}</span>
    <span style="font-weight: 700; font-size: 15px;">{role}</span>
  </div>
  <div style="color: var(--muted); font-size: 13px; line-height: 1.45;">{body}</div>
</div>
"""
    body = f"""
<div class="accent-strip"></div>
<div class="page">
  <div class="brand">
    <div class="mark">M</div>
    <div>
      <div class="name">MedFAQ</div>
      <div class="sub">Team of 4. Every role owns NLP.</div>
    </div>
  </div>

  <h2 class="h2" style="margin-top: 56px;">4 NLP-heavy roles.</h2>
  <p class="lead" style="margin-bottom: 28px; max-width: 880px;">
    Every member built one of the trainable models and owns a real
    slice of the classical NLP stack.
  </p>

  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
    {cards}
  </div>

  <div class="footer">
    <span>Roles in TEAM_ROLES.md</span>
    <span class="link">github.com/AbdulGhani002/medical-faq-auto</span>
  </div>
</div>
"""
    return write_html("03_team", body)


def slide4_run() -> Path:
    body = """
<div class="accent-strip"></div>
<div class="page">
  <div class="brand">
    <div class="mark">M</div>
    <div>
      <div class="name">MedFAQ</div>
      <div class="sub">How to run it</div>
    </div>
  </div>

  <h2 class="h2" style="margin-top: 56px;">One command.</h2>
  <p class="lead" style="max-width: 880px; margin-bottom: 30px;">
    Docker compose brings up the web app, the API, MongoDB and the
    pipeline services. Auto-seeded on first boot.
  </p>

  <div style="background: var(--ink); color: #d1fae5; border-radius: 16px;
              padding: 28px 32px; font-family: 'Consolas', 'Courier New', monospace;
              font-size: 22px; line-height: 1.5; margin-bottom: 30px;">
    <span style="color: #a8a29e;"># Clone</span><br/>
    git clone https://github.com/AbdulGhani002/medical-faq-auto<br/>
    cd medical-faq-auto<br/>
    <br/>
    <span style="color: #a8a29e;"># Bring it all up</span><br/>
    docker compose up --build
  </div>

  <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
    <div style="border:1px solid var(--border); border-radius: 14px;
                background: white; padding: 18px;">
      <div style="font-size: 11px; letter-spacing: 0.16em;
                  color: var(--muted); text-transform: uppercase;">Web app</div>
      <div style="font-size: 18px; font-weight: 700; margin-top: 4px;
                  font-family: monospace;">localhost:3000</div>
      <div style="color: var(--muted); font-size: 13px; margin-top: 4px;">
        Chat, playground, architecture, admin
      </div>
    </div>
    <div style="border:1px solid var(--border); border-radius: 14px;
                background: white; padding: 18px;">
      <div style="font-size: 11px; letter-spacing: 0.16em;
                  color: var(--muted); text-transform: uppercase;">FastAPI</div>
      <div style="font-size: 18px; font-weight: 700; margin-top: 4px;
                  font-family: monospace;">localhost:8000/docs</div>
      <div style="color: var(--muted); font-size: 13px; margin-top: 4px;">
        Swagger UI for every endpoint
      </div>
    </div>
  </div>

  <div style="margin-top: 30px;
              border:1px solid var(--border); border-radius: 16px;
              background: white; padding: 22px;">
    <div style="font-weight:700; font-size:18px; margin-bottom: 12px;">
      Want to train the transformer on your GPU?
    </div>
    <div style="font-family: monospace; font-size: 16px;
                color: var(--ink); background: var(--soft);
                padding: 12px 14px; border-radius: 10px;">
      pip install torch --index-url<br/>
      &nbsp;&nbsp;https://download.pytorch.org/whl/cu121<br/>
      cd api && python train_transformer.py --verbose
    </div>
  </div>

  <div class="footer">
    <span>Repo includes 26-page PDF + 11-slide deck</span>
    <span class="link">github.com/AbdulGhani002/medical-faq-auto</span>
  </div>
</div>
"""
    return write_html("04_run", body)


# --- main --------------------------------------------------------------


def main() -> None:
    slides = [
        ("01_cover.png",  slide1_cover()),
        ("02_models.png", slide2_models()),
        ("03_team.png",   slide3_team()),
        ("04_run.png",    slide4_run()),
    ]
    for png_name, html_path in slides:
        png_path = OUT_DIR / png_name
        print(f"  rendering {png_name} ...")
        render_png(html_path, png_path)

    # Copy to Desktop.
    desktop = Path(os.environ.get("USERPROFILE", "")) / "OneDrive" / "Desktop"
    if not desktop.is_dir():
        desktop = Path(os.environ.get("USERPROFILE", "")) / "Desktop"
    out_desktop = desktop / "MedFAQ_LinkedIn_Carousel"
    out_desktop.mkdir(exist_ok=True, parents=True)
    for png_name, _ in slides:
        src = OUT_DIR / png_name
        if src.is_file():
            shutil.copy(src, out_desktop / png_name)

    # Cleanup.
    shutil.rmtree(USER_DATA, ignore_errors=True)

    sys.stdout.reconfigure(encoding="utf-8")
    print(f"\nlinkedin_assets/ -> 4 PNGs in {OUT_DIR}")
    print(f"Desktop copy     -> {out_desktop}")


if __name__ == "__main__":
    main()

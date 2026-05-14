"""Per-stage mini-diagrams: input -> process -> output for each of the 8 stages."""
from reportlab.graphics.shapes import Drawing, Rect, String

from docs_src.common import (
    ACCENT, DARK, GREEN, LIGHT, ORANGE, PRIMARY, SOFT,
    arrow, box,
)


def _stage_box(d, title, inp, proc, out, fill):
    """Render one input-process-output triplet centred horizontally."""
    W = 480
    H = 130
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, title,
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    box(d, 20, 35, 130, 40, LIGHT, ACCENT, "INPUT\n" + inp, fc=DARK, fs=8)
    box(d, 175, 35, 130, 40, fill, DARK, "PROCESS\n" + proc, fs=8)
    box(d, 330, 35, 130, 40, ORANGE, DARK, "OUTPUT\n" + out, fs=8)
    arrow(d, 150, 55, 175, 55, color=PRIMARY)
    arrow(d, 305, 55, 330, 55, color=PRIMARY)


def stage_ingest():
    d = Drawing(480, 130)
    _stage_box(d, "Stage 1 — Ingest".replace("—", "-"),
               "MongoDB chat_turns", "group by session_id",
               "list of sessions", ACCENT)
    return d


def stage_segment():
    d = Drawing(480, 130)
    _stage_box(d, "Stage 2 - Segment",
               "session turns", "detect question turns,\npair with bot reply",
               "list of question turns", ACCENT)
    return d


def stage_normalize():
    d = Drawing(480, 130)
    _stage_box(d, "Stage 3 - Normalize",
               "raw question text", "ftfy + PHI scrub +\nlowercase",
               "clean text", ACCENT)
    return d


def stage_embed():
    d = Drawing(480, 130)
    _stage_box(d, "Stage 4 - Embed",
               "clean text", "BGE-M3 encode,\nnormalize vectors",
               "(n, d) matrix", ACCENT)
    return d


def stage_cluster():
    d = Drawing(480, 130)
    _stage_box(d, "Stage 5 - Cluster",
               "embedding matrix", "HDBSCAN +\nBERTopic labels",
               "list of clusters", GREEN)
    return d


def stage_select():
    d = Drawing(480, 130)
    _stage_box(d, "Stage 6 - Select",
               "cluster + turns", "rank agent replies\nby sim + length",
               "canonical Q + A", GREEN)
    return d


def stage_polish():
    d = Drawing(480, 130)
    _stage_box(d, "Stage 7 - Polish",
               "canonical Q + A", "rule-based clean\nwhitespace, trim",
               "polished FAQ", GREEN)
    return d


def stage_publish():
    d = Drawing(480, 130)
    _stage_box(d, "Stage 8 - Publish",
               "polished FAQs", "upsert to Mongo\napproved=false",
               "FAQ candidates", ORANGE)
    return d


def cluster_visualisation_mock() -> Drawing:
    """Mock 2D scatter of clusters in embedding space."""
    import random
    W, H = 480, 230
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "Embedding space (2D UMAP) - mock",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    rng = random.Random(7)
    centres = [(120, 100), (260, 140), (380, 80), (200, 60), (340, 170)]
    colours = [PRIMARY, GREEN, ACCENT, ORANGE, GRAY := LIGHT]
    from reportlab.graphics.shapes import Circle
    for (cx, cy), col in zip(centres, colours):
        for _ in range(28):
            x = cx + rng.gauss(0, 14)
            y = cy + rng.gauss(0, 10)
            d.add(Circle(x, y, 2.4, fillColor=col, strokeColor=col))
    return d

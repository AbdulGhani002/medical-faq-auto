"""Schema and API hierarchy diagrams."""
from reportlab.graphics.shapes import Drawing, Line, Rect, String

from docs_src.common import (
    ACCENT, DARK, GRAY, LIGHT, ORANGE, PRIMARY, SOFT,
    arrow, box,
)


def collection_diagram() -> Drawing:
    """ER-style view of the three Mongo collections + one Qdrant collection."""
    W, H = 480, 280
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "Storage Schema",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))

    # chat_turns box
    box(d, 25, H - 100, 160, 50, ORANGE, DARK,
        "mongo.chat_turns\n(every user / bot turn)", fs=9)
    d.add(String(35, H - 115, "_id, session_id, specialty,",
                 fontName="Courier", fontSize=8, fillColor=DARK))
    d.add(String(35, H - 127, "role, text, timestamp",
                 fontName="Courier", fontSize=8, fillColor=DARK))

    # faqs box
    box(d, 205, H - 100, 165, 50, ORANGE, DARK,
        "mongo.faqs\n(cluster -> canonical Q+A)", fs=9)
    d.add(String(215, H - 115, "_id, specialty, cluster_id,",
                 fontName="Courier", fontSize=8, fillColor=DARK))
    d.add(String(215, H - 127, "question, answer, count,",
                 fontName="Courier", fontSize=8, fillColor=DARK))
    d.add(String(215, H - 139, "approved, rejected, updated_at",
                 fontName="Courier", fontSize=8, fillColor=DARK))

    # qdrant box
    box(d, 25, H - 200, 160, 50, ORANGE, DARK,
        "qdrant.faqs_<specialty>\n(vector index)", fs=9)
    d.add(String(35, H - 215, "id, vector (1024d),",
                 fontName="Courier", fontSize=8, fillColor=DARK))
    d.add(String(35, H - 227, "payload {faq_id, question,",
                 fontName="Courier", fontSize=8, fillColor=DARK))
    d.add(String(35, H - 239, "answer, specialty}",
                 fontName="Courier", fontSize=8, fillColor=DARK))

    # clusters box (logical, not a literal mongo collection in stubs)
    box(d, 205, H - 200, 165, 50, LIGHT, ACCENT,
        "mongo.clusters\n(emerging-issue tracking)", fc=DARK, fs=9)
    d.add(String(215, H - 215, "cluster_id, specialty,",
                 fontName="Courier", fontSize=8, fillColor=DARK))
    d.add(String(215, H - 227, "first_seen, last_seen,",
                 fontName="Courier", fontSize=8, fillColor=DARK))
    d.add(String(215, H - 239, "size_history[]",
                 fontName="Courier", fontSize=8, fillColor=DARK))

    arrow(d, 185, H - 75, 205, H - 75)
    arrow(d, 105, H - 100, 105, H - 150)
    arrow(d, 287, H - 100, 287, H - 150)
    return d


def api_hierarchy() -> Drawing:
    """Tree of API endpoints under the FastAPI root."""
    W, H = 480, 230
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "API Endpoint Hierarchy",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))

    box(d, 180, H - 65, 120, 28, PRIMARY, DARK, "FastAPI /", fs=9)
    groups = [
        ("/health", 30, "GET"),
        ("/chat", 170, "POST"),
        ("/faq", 300, "GET"),
        ("/admin", 410, "various"),
    ]
    for path, x, method in groups:
        box(d, x, H - 125, 70, 28, ACCENT, PRIMARY, path, fs=9)
        d.add(String(x + 35, H - 142, method,
                     fontName="Courier", fontSize=8,
                     fillColor=GRAY, textAnchor="middle"))
        arrow(d, 240, H - 65, x + 35, H - 100)

    admin_endpoints = [
        ("/candidates/{s}", 230),
        ("/approve/{id}", 320),
        ("/edit/{id}", 400),
        ("/reject/{id}", 35),
    ]
    for name, x in admin_endpoints:
        box(d, x, H - 195, 110, 26, LIGHT, ACCENT, name, fc=DARK, fs=8)
    arrow(d, 445, H - 125, 285, H - 170)
    arrow(d, 445, H - 125, 375, H - 170)
    arrow(d, 445, H - 125, 455, H - 170)
    arrow(d, 445, H - 125, 90, H - 170)
    return d

"""Three diagrams used by the proposal: webapp flow, architecture, pipeline."""
from reportlab.graphics.shapes import Drawing, Rect, String

from docs_src.common import (
    ACCENT, DARK, GRAY, GREEN, LIGHT, ORANGE, PRIMARY, SOFT,
    arrow, box, label,
)


def webapp_flow_diagram() -> Drawing:
    W, H = 480, 180
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "Web Application Flow",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))

    box(d, 20, H - 80, 100, 40, LIGHT, ACCENT, "User visits\nwebsite", fc=DARK, fs=9)
    box(d, 145, H - 80, 110, 40, ACCENT, PRIMARY,
        "Selects specialty\n(Radio / Physio / Cardio)", fs=8)
    box(d, 280, H - 80, 90, 40, ACCENT, PRIMARY, "Chats with\nbot", fs=9)
    box(d, 390, H - 80, 75, 40, GREEN, DARK, "Chat\nlogged", fs=9)
    arrow(d, 120, H - 60, 145, H - 60)
    arrow(d, 255, H - 60, 280, H - 60)
    arrow(d, 370, H - 60, 390, H - 60)

    box(d, 20, H - 150, 130, 40, ORANGE, DARK,
        "Pipeline runs\n(scheduled / streaming)", fs=8)
    box(d, 180, H - 150, 130, 40, ORANGE, DARK, "FAQ clusters\nupdated", fs=9)
    box(d, 335, H - 150, 130, 40, GREEN, DARK, "Public FAQ page\nrefreshed", fs=9)
    arrow(d, 425, H - 80, 425, H - 110)
    arrow(d, 335, H - 130, 310, H - 130)
    arrow(d, 180, H - 130, 150, H - 130)
    return d


def architecture_diagram() -> Drawing:
    W, H = 480, 340
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "System Architecture",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))

    box(d, 20, H - 70, 140, 35, LIGHT, ACCENT, "Patients / Users", fc=DARK)
    box(d, 180, H - 70, 130, 35, LIGHT, ACCENT, "Clinicians (Review)", fc=DARK)
    box(d, 330, H - 70, 130, 35, LIGHT, ACCENT, "Admin Dashboard", fc=DARK)

    box(d, 60, H - 130, 360, 35, ACCENT, PRIMARY,
        "Web Frontend (Next.js)  Chatbot Widgets + FAQ Page + Admin Panel")
    arrow(d, 90, H - 70, 120, H - 95)
    arrow(d, 245, H - 70, 240, H - 95)
    arrow(d, 395, H - 70, 360, H - 95)

    box(d, 80, H - 185, 150, 35, PRIMARY, DARK, "Chatbot API\n(FastAPI)", fs=9)
    box(d, 250, H - 185, 150, 35, PRIMARY, DARK, "FAQ Service API\n(FastAPI)", fs=9)
    arrow(d, 200, H - 130, 155, H - 150)
    arrow(d, 290, H - 130, 325, H - 150)

    box(d, 25, H - 245, 110, 35, GREEN, DARK, "Retrieval\nService", fs=8)
    box(d, 150, H - 245, 110, 35, GREEN, DARK, "Chat Logger\n+ Tracker", fs=8)
    box(d, 275, H - 245, 110, 35, GREEN, DARK, "FAQ Generator\n(Pipeline)", fs=8)
    box(d, 400, H - 245, 65, 35, GREEN, DARK, "Alerts\n(Issues)", fs=8)
    arrow(d, 155, H - 185, 80, H - 210)
    arrow(d, 155, H - 185, 205, H - 210)
    arrow(d, 325, H - 185, 330, H - 210)
    arrow(d, 325, H - 185, 425, H - 210)

    box(d, 20, H - 310, 130, 40, ORANGE, DARK, "MongoDB\nChat Sessions", fs=8)
    box(d, 165, H - 310, 130, 40, ORANGE, DARK, "Vector DB (Qdrant)\nEmbeddings", fs=8)
    box(d, 310, H - 310, 155, 40, ORANGE, DARK,
        "FAQ Store + Analytics\n(Mongo / Postgres)", fs=8)
    arrow(d, 80, H - 245, 85, H - 270)
    arrow(d, 205, H - 245, 230, H - 270)
    arrow(d, 330, H - 245, 385, H - 270)
    arrow(d, 432, H - 245, 405, H - 270)

    for txt, y in [("USERS", 50), ("FRONT", 115), ("API", 170),
                   ("SERVICE", 225), ("DATA", 290)]:
        label(d, 5, H - y, txt)
    return d


def pipeline_diagram() -> Drawing:
    W, H = 480, 260
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "FAQ Generation Pipeline",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))

    stages = [
        ("1. Ingest", "Chat logs from\nweb chatbot", ACCENT),
        ("2. Segment", "Split turns,\ntag questions", ACCENT),
        ("3. Normalize", "Clean PHI,\nintent extract", ACCENT),
        ("4. Embed", "BGE-M3\nsentence vectors", ACCENT),
        ("5. Cluster", "HDBSCAN +\nBERTopic", GREEN),
        ("6. Select", "Extractive best\nagent answer", GREEN),
        ("7. Polish", "Rule-based\nclean-up", GREEN),
        ("8. Publish", "Rank + push\nto FAQ page", ORANGE),
    ]
    bw, bh, gap_x, start_x = 105, 55, 13, 12
    row1_y, row2_y = H - 100, H - 200

    positions = [(start_x + i * (bw + gap_x), row1_y) for i in range(4)]
    positions += [(start_x + (3 - i) * (bw + gap_x), row2_y) for i in range(4)]

    for i, (title, sub, color) in enumerate(stages):
        x, y = positions[i]
        box(d, x, y, bw, bh, color, DARK, title, fs=10)
        for j, line in enumerate(sub.split("\n")):
            d.add(String(x + bw / 2, y - 12 - j * 10, line,
                         fontName="Helvetica", fontSize=8,
                         fillColor=DARK, textAnchor="middle"))
    for i in range(3):
        y = row1_y + bh / 2
        arrow(d, positions[i][0] + bw + 1, y, positions[i + 1][0] - 2, y, color=PRIMARY)
    x_down = positions[3][0] + bw / 2
    arrow(d, x_down, row1_y - 25, x_down, row2_y + bh + 5, color=PRIMARY)
    for i in range(4, 7):
        y = row2_y + bh / 2
        arrow(d, positions[i][0] - 1, y, positions[i + 1][0] + bw + 2, y, color=PRIMARY)
    d.add(String(W / 2, 10, "Continuous loop: new chats feed back to step 1",
                 fontName="Helvetica-Oblique", fontSize=8,
                 fillColor=GRAY, textAnchor="middle"))
    return d

"""Architecture-specific diagrams: component tree, sequence flows, deployment."""
from reportlab.graphics.shapes import Drawing, Line, Rect, String

from docs_src.common import (
    ACCENT, DARK, GRAY, GREEN, LIGHT, ORANGE, PRIMARY, SOFT,
    arrow, box,
)


def frontend_component_tree() -> Drawing:
    W, H = 480, 230
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "Frontend Component Tree",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    box(d, 180, H - 70, 120, 32, PRIMARY, DARK, "RootLayout", fs=9)
    pages = [
        ("/", "Home"), ("/chat/[s]", "ChatPage"),
        ("/faq/[s]", "FAQPage"), ("/admin", "AdminPage"),
    ]
    for i, (route, name) in enumerate(pages):
        x = 20 + i * 115
        box(d, x, H - 130, 100, 30, ACCENT, PRIMARY, name, fs=9)
        d.add(String(x + 50, H - 145, route,
                     fontName="Courier", fontSize=8,
                     fillColor=GRAY, textAnchor="middle"))
        arrow(d, 240, H - 70, x + 50, H - 100)
    comps = [
        ("SpecialtyCard", 30), ("ChatWidget", 160),
        ("FAQList", 290), ("AdminPanel", 410),
    ]
    for name, x in comps:
        box(d, x, H - 195, 100, 28, LIGHT, ACCENT, name, fc=DARK, fs=9)
    arrow(d, 70, H - 130, 80, H - 167)
    arrow(d, 185, H - 130, 210, H - 167)
    arrow(d, 300, H - 130, 340, H - 167)
    arrow(d, 415, H - 130, 460, H - 167)
    return d


def backend_module_tree() -> Drawing:
    W, H = 480, 230
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "Backend Module Tree",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    box(d, 180, H - 70, 120, 32, PRIMARY, DARK, "FastAPI app", fs=9)
    routers = [("/chat", 30), ("/faq", 180), ("/admin", 330)]
    for path, x in routers:
        box(d, x, H - 130, 120, 30, ACCENT, PRIMARY, f"router {path}", fs=9)
        arrow(d, 240, H - 70, x + 60, H - 100)
    services = [
        ("retrieval", 20), ("phi_scrub", 140),
        ("chat_logger", 250), ("db (motor)", 370),
    ]
    for name, x in services:
        box(d, x, H - 195, 100, 28, LIGHT, ACCENT, name, fc=DARK, fs=9)
    arrow(d, 90, H - 130, 70, H - 167)
    arrow(d, 240, H - 130, 190, H - 167)
    arrow(d, 240, H - 130, 300, H - 167)
    arrow(d, 390, H - 130, 420, H - 167)
    return d


def sequence_chat() -> Drawing:
    W, H = 480, 280
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "Sequence: Chat Request",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    actors = [
        ("User", 50), ("Browser", 140), ("FastAPI", 240),
        ("Mongo", 340), ("Qdrant", 430),
    ]
    for name, x in actors:
        box(d, x - 35, H - 60, 70, 24, PRIMARY, DARK, name, fs=9)
        d.add(Line(x, H - 60, x, 30, strokeColor=GRAY, strokeWidth=0.8))
    msgs = [
        (50, 140, H - 90, "types question"),
        (140, 240, H - 115, "POST /chat"),
        (240, 340, H - 140, "log turn"),
        (240, 430, H - 165, "search vector"),
        (430, 240, H - 190, "top hits"),
        (240, 340, H - 215, "log bot reply"),
        (240, 140, H - 240, "answer + confidence"),
        (140, 50, H - 263, "render"),
    ]
    for sx, ex, y, txt in msgs:
        arrow(d, sx, y, ex, y, color=PRIMARY, width=1)
        d.add(String((sx + ex) / 2, y + 4, txt,
                     fontName="Helvetica", fontSize=8,
                     fillColor=DARK, textAnchor="middle"))
    return d


def sequence_pipeline() -> Drawing:
    W, H = 480, 280
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "Sequence: Pipeline Run",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    actors = [
        ("Cron", 50), ("Pipeline", 160), ("Mongo", 270),
        ("BGE-M3", 360), ("Qdrant", 440),
    ]
    for name, x in actors:
        box(d, x - 35, H - 60, 70, 24, PRIMARY, DARK, name, fs=9)
        d.add(Line(x, H - 60, x, 30, strokeColor=GRAY, strokeWidth=0.8))
    msgs = [
        (50, 160, H - 90, "trigger hourly"),
        (160, 270, H - 115, "fetch chats"),
        (160, 360, H - 140, "encode"),
        (360, 160, H - 165, "vectors"),
        (160, 440, H - 190, "upsert + cluster"),
        (160, 270, H - 215, "publish FAQs"),
        (160, 50, H - 250, "done"),
    ]
    for sx, ex, y, txt in msgs:
        arrow(d, sx, y, ex, y, color=PRIMARY, width=1)
        d.add(String((sx + ex) / 2, y + 4, txt,
                     fontName="Helvetica", fontSize=8,
                     fillColor=DARK, textAnchor="middle"))
    return d


def deployment_diagram() -> Drawing:
    W, H = 480, 240
    d = Drawing(W, H)
    d.add(Rect(0, H - 22, W, 22, fillColor=SOFT, strokeColor=ACCENT))
    d.add(String(W / 2, H - 16, "Deployment Topology (single VM)",
                 fontName="Helvetica-Bold", fontSize=11,
                 fillColor=PRIMARY, textAnchor="middle"))
    d.add(Rect(15, 20, W - 30, H - 60, fillColor=SOFT,
               strokeColor=ACCENT, strokeWidth=1))
    d.add(String(25, H - 50, "VPS (4 vCPU, 8GB)",
                 fontName="Helvetica-Bold", fontSize=9, fillColor=PRIMARY))
    box(d, 30, H - 110, 120, 35, PRIMARY, DARK, "NGINX\n:80 / :443", fs=9)
    box(d, 170, H - 110, 120, 35, ACCENT, PRIMARY, "Next.js\n:3000", fs=9)
    box(d, 310, H - 110, 120, 35, ACCENT, PRIMARY, "FastAPI\n:8000", fs=9)
    box(d, 30, H - 170, 120, 35, GREEN, DARK, "Celery worker\n+ beat", fs=9)
    box(d, 170, H - 170, 120, 35, ORANGE, DARK, "Mongo\n:27017", fs=9)
    box(d, 310, H - 170, 120, 35, ORANGE, DARK, "Qdrant\n:6333", fs=9)
    box(d, 170, H - 220, 120, 35, ORANGE, DARK, "Redis\n:6379", fs=9)
    for x1, x2 in [(150, 170), (290, 310)]:
        arrow(d, x1, H - 92, x2, H - 92)
    for sx, sy, ex, ey in [
        (90, H - 145, 230, H - 152), (370, H - 145, 230, H - 152),
        (230, H - 152, 230, H - 185),
    ]:
        arrow(d, sx, sy, ex, ey)
    return d

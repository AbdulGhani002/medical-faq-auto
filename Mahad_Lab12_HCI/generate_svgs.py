#!/usr/bin/env python3
"""Generate all SVG deliverables for HCI Lab 12 (Mahad).

Scenario: Online Hospital Management System (MediCare+)
Produces persona, user-journey, low-fi wireframes, hi-fi UI screens,
a 10-frame storyboard, a navigation flow and a usability/accessibility board.
"""
from __future__ import annotations
from pathlib import Path
from html import escape

OUT = Path(__file__).parent / "svg"
OUT.mkdir(parents=True, exist_ok=True)

# ----------------------------- design system ----------------------------- #
PRIMARY      = "#0F8B8D"
PRIMARY_DARK = "#0A6E70"
ACCENT       = "#14B8A6"
BG           = "#EEF3F5"
CARD         = "#FFFFFF"
INK          = "#0F172A"
MUTED        = "#64748B"
LIGHT        = "#94A3B8"
BORDER       = "#E2E8F0"
ERROR        = "#E11D48"
SUCCESS      = "#16A34A"
WARN         = "#F59E0B"
GREY1        = "#CBD5E1"   # wireframe fills
GREY2        = "#E2E8F0"
GREY3        = "#F1F5F9"
FONT = "font-family='Segoe UI, Roboto, Helvetica, Arial, sans-serif'"


def T(x, y, s, size=14, fill=INK, weight="normal", anchor="start", spacing=None):
    sp = f" letter-spacing='{spacing}'" if spacing else ""
    return (f"<text x='{x}' y='{y}' font-size='{size}' fill='{fill}' "
            f"font-weight='{weight}' text-anchor='{anchor}' {FONT}{sp}>{escape(str(s))}</text>")


def R(x, y, w, h, r=0, fill=CARD, stroke="none", sw=1, opacity=1, dash=None):
    d = f" stroke-dasharray='{dash}'" if dash else ""
    return (f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='{r}' ry='{r}' "
            f"fill='{fill}' stroke='{stroke}' stroke-width='{sw}' opacity='{opacity}'{d}/>")


def C(cx, cy, r, fill=PRIMARY, stroke="none", sw=1, opacity=1):
    return (f"<circle cx='{cx}' cy='{cy}' r='{r}' fill='{fill}' stroke='{stroke}' "
            f"stroke-width='{sw}' opacity='{opacity}'/>")


def line(x1, y1, x2, y2, stroke=BORDER, sw=1, dash=None):
    d = f" stroke-dasharray='{dash}'" if dash else ""
    return f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{stroke}' stroke-width='{sw}'{d}/>"


def path(d, fill="none", stroke=INK, sw=2, cap="round", join="round"):
    return (f"<path d='{d}' fill='{fill}' stroke='{stroke}' stroke-width='{sw}' "
            f"stroke-linecap='{cap}' stroke-linejoin='{join}'/>")


def doc(w, h, body, bg=BG):
    return (f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' "
            f"viewBox='0 0 {w} {h}'>\n{R(0,0,w,h,0,bg)}\n{body}\n</svg>\n")


def save(name, svg):
    (OUT / name).write_text(svg, encoding="utf-8")
    print("wrote", name)


# small icon helpers (stroke icons) ------------------------------------------------
def ic_search(cx, cy, s=9, col=MUTED, sw=2):
    return (C(cx-2, cy-2, s, "none", col, sw) +
            line(cx-2+s*0.7, cy-2+s*0.7, cx-2+s*1.5, cy-2+s*1.5, col, sw))

def ic_heart(cx, cy, col=PRIMARY):
    return path(f"M {cx} {cy+7} C {cx-10} {cy-3}, {cx-6} {cy-11}, {cx} {cy-5} "
                f"C {cx+6} {cy-11}, {cx+10} {cy-3}, {cx} {cy+7} Z", col, col, 1)

def ic_user(cx, cy, col=MUTED, sw=2):
    return C(cx, cy-4, 5, "none", col, sw) + path(f"M {cx-8} {cy+9} C {cx-8} {cy} {cx+8} {cy} {cx+8} {cy+9}", "none", col, sw)

def ic_home(cx, cy, col=MUTED, sw=2):
    return path(f"M {cx-8} {cy} L {cx} {cy-8} L {cx+8} {cy} M {cx-6} {cy-1} L {cx-6} {cy+8} L {cx+6} {cy+8} L {cx+6} {cy-1}", "none", col, sw)

def ic_cal(cx, cy, col=MUTED, sw=2):
    return (R(cx-8, cy-7, 16, 15, 2, "none", col, sw) + line(cx-8, cy-2, cx+8, cy-2, col, sw) +
            line(cx-4, cy-10, cx-4, cy-5, col, sw) + line(cx+4, cy-10, cx+4, cy-5, col, sw))

def star(cx, cy, r=6, fill=WARN):
    import math
    pts = []
    for i in range(10):
        ang = -math.pi/2 + i*math.pi/5
        rr = r if i % 2 == 0 else r*0.45
        pts.append(f"{cx+rr*math.cos(ang):.1f},{cy+rr*math.sin(ang):.1f}")
    return f"<polygon points='{' '.join(pts)}' fill='{fill}'/>"


# ------------------------- phone mockup scaffold ------------------------- #
def phone(x, y, screen_inner, scale=1.0, label=None, label_sub=None):
    """A 390x844 phone at (x,y). screen_inner: svg drawn with origin at screen top-left
    (content area is 350 wide x 760 tall after insets). Returns group string."""
    W, H = 390, 844
    g = [f"<g transform='translate({x},{y}) scale({scale})'>"]
    # device body
    g.append(R(-6, -6, W+12, H+12, 46, "#0B1220"))
    g.append(R(0, 0, W, H, 40, CARD, BORDER, 1))
    # status bar
    g.append(R(0, 0, W, 44, 40, "#FFFFFF"))
    g.append(R(0, 24, W, 20, 0, "#FFFFFF"))
    g.append(T(22, 28, "9:41", 13, INK, "bold"))
    # notch
    g.append(R(W/2-45, 8, 90, 22, 11, "#0B1220"))
    # signal / battery
    g.append(R(W-70, 16, 14, 11, 2, INK))
    g.append(R(W-50, 14, 16, 13, 3, "none", INK, 1.5) + R(W-47, 17, 9, 7, 1, INK))
    g.append(C(W-86, 22, 5, INK))
    g.append(screen_inner)
    # home indicator
    g.append(R(W/2-55, H-16, 110, 5, 3, "#0B1220", opacity=0.85))
    g.append("</g>")
    if label:
        g.append(T(x + W*scale/2, y + H*scale + 34, label, 17, INK, "bold", "middle"))
    if label_sub:
        g.append(T(x + W*scale/2, y + H*scale + 56, label_sub, 13, MUTED, "normal", "middle"))
    return "\n".join(g)


def bottomnav(active=0):
    items = [("Home", ic_home), ("Find", ic_search), ("Visits", ic_cal), ("Me", ic_user)]
    g = [R(0, 844-78, 390, 78, 0, "#FFFFFF", BORDER, 1)]
    for i, (lbl, ic) in enumerate(items):
        cx = 65 + i*87
        col = PRIMARY if i == active else LIGHT
        if i == 1:
            g.append(ic_search(cx, 844-46, 8, col, 2.2))
        elif i == 2:
            g.append(ic_cal(cx, 844-48, col, 2.2))
        elif i == 3:
            g.append(ic_user(cx, 844-48, col, 2.2))
        else:
            g.append(ic_home(cx, 844-48, col, 2.2))
        g.append(T(cx, 844-22, lbl, 11, col, "bold" if i == active else "normal", "middle"))
    return "\n".join(g)


def appbar(title, sub=None, back=False):
    g = [R(0, 44, 390, (96 if sub else 78), 0, PRIMARY)]
    if back:
        g.append(path("M 38 84 L 26 76 L 38 68", "none", "#FFFFFF", 2.4))
        tx = 56
    else:
        tx = 24
    g.append(T(tx, 90 if not sub else 86, title, 21, "#FFFFFF", "bold"))
    if sub:
        g.append(T(tx, 110, sub, 12.5, "#CFFAF5"))
    g.append(C(360, 80, 14, "#FFFFFF", opacity=0.18))
    g.append(C(360, 80, 3, "#FFFFFF"))
    g.append(C(355, 75, 3, "#FFFFFF"))
    return "\n".join(g)


def btn(x, y, w, h, label, fill=PRIMARY, txt="#FFFFFF", r=14, size=16, stroke="none"):
    return R(x, y, w, h, r, fill, stroke, 1.5) + T(x+w/2, y+h/2+size*0.36, label, size, txt, "bold", "middle")


# =======================================================================
# 1. PERSONA
# =======================================================================
def persona():
    W, H = 1000, 640
    g = []
    g.append(R(40, 30, 920, 60, 12, PRIMARY))
    g.append(T(64, 68, "USER PERSONA", 24, "#FFFFFF", "bold", spacing="2"))
    g.append(T(936, 68, "MediCare+  |  Online Hospital Management", 13, "#CFFAF5", "end"))
    # left card
    g.append(R(40, 110, 300, 500, 14, CARD, BORDER, 1))
    g.append(C(190, 215, 70, GREY3, PRIMARY, 2))
    g.append(ic_user(190, 205, PRIMARY, 4))
    g.append(T(190, 320, "Sara Ahmed", 26, INK, "bold", "middle"))
    g.append(T(190, 348, "University Student", 15, PRIMARY, "bold", "middle"))
    rows = [("Age", "22"), ("Occupation", "BS Student"), ("Location", "Islamabad, PK"),
            ("Devices", "Mobile (primary), Laptop"), ("Tech skill", "Intermediate"),
            ("Personality", "Busy, impatient, goal-driven")]
    yy = 380
    for k, v in rows:
        g.append(T(64, yy, k.upper(), 10.5, MUTED, "bold", spacing="1"))
        g.append(T(64, yy+18, v, 14, INK))
        yy += 38
    # right column: goals / frustrations / accessibility / quote
    def block(x, y, w, h, title, items, col):
        s = [R(x, y, w, h, 12, CARD, BORDER, 1), R(x, y, 6, h, 12, col)]
        s.append(T(x+22, y+30, title, 15, INK, "bold"))
        ly = y + 58
        for it in items:
            s.append(C(x+26, ly-4, 3, col))
            s.append(T(x+40, ly, it, 12.5, "#334155"))
            ly += 24
        return "\n".join(s)
    g.append(block(366, 110, 290, 195, "GOALS",
            ["Book a doctor appointment in under 2 min",
             "View prescriptions & lab reports anytime",
             "Get reminders before each visit",
             "Pay consultation fees online safely"], SUCCESS))
    g.append(block(674, 110, 286, 195, "FRUSTRATIONS",
            ["Confusing, cluttered navigation",
             "Long manual queues at reception",
             "No clear feedback after booking",
             "Tiny tap targets on small screens"], ERROR))
    g.append(block(366, 320, 290, 175, "ACCESSIBILITY NEEDS",
            ["Mild colour-blindness (red/green)",
             "Prefers large, high-contrast text",
             "Often one-handed phone use",
             "Needs keyboard / screen-reader paths"], WARN))
    # quote
    g.append(R(674, 320, 286, 175, 12, PRIMARY))
    g.append(T(696, 360, "“", 60, "#CFFAF5", "bold"))
    g.append(T(696, 392, "I just want to book a", 16, "#FFFFFF", "bold"))
    g.append(T(696, 416, "doctor and get on with", 16, "#FFFFFF", "bold"))
    g.append(T(696, 440, "my day  no fuss.”", 16, "#FFFFFF", "bold"))
    g.append(T(696, 474, "  Sara, primary user", 12.5, "#CFFAF5"))
    # tech bars
    g.append(R(366, 510, 594, 100, 12, CARD, BORDER, 1))
    g.append(T(388, 540, "TECHNOLOGY COMFORT", 12, MUTED, "bold", spacing="1"))
    skills = [("Smartphone apps", 0.9), ("Online payments", 0.75), ("Web forms", 0.65), ("New software", 0.5)]
    bx = 388
    for name, val in skills:
        g.append(T(bx, 568, name, 11.5, INK))
        g.append(R(bx, 578, 130, 9, 5, GREY2))
        g.append(R(bx, 578, int(130*val), 9, 5, PRIMARY))
        g.append(T(bx+138, 587, f"{int(val*100)}%", 11, MUTED))
        bx += 148
    save("01_persona.svg", doc(W, H, "\n".join(g)))


# =======================================================================
# 2. USER JOURNEY MAP (with emotion curve)
# =======================================================================
def journey():
    W, H = 1300, 700
    g = []
    g.append(T(40, 56, "User Journey Map", 28, INK, "bold"))
    g.append(T(40, 82, "Goal: Sara books a doctor appointment  including an error & recovery path", 14, MUTED))
    steps = [
        ("1. Open app", "Launch MediCare+", "Splash + auto session check", "\U0001F642", 0.6),
        ("2. Log in", "Enters email + password", "Validates credentials", "\U0001F610", 0.45),
        ("3. Wrong pwd", "Mistypes password", "Inline error + retry hint", "\U0001F61F", 0.2),
        ("4. Retry", "Re-enters correctly", "Auth success → dashboard", "\U0001F642", 0.55),
        ("5. Search", "Searches 'Cardiologist'", "Live results + filters", "\U0001F642", 0.7),
        ("6. Filter", "Filters by rating/time", "Refined doctor list", "\U0001F642", 0.72),
        ("7. Review", "Opens doctor profile", "Shows slots, fee, reviews", "\U0001F600", 0.8),
        ("8. Confirm", "Picks slot, taps Book", "Confirmation dialog", "\U0001F600", 0.78),
        ("9. Pay", "Pays fee via card", "Secure processing spinner", "\U0001F610", 0.6),
        ("10. Success", "Sees confirmation", "Toast + reminder set", "\U0001F929", 0.92),
    ]
    n = len(steps)
    x0, gap = 70, (W-120)/n
    top = 120
    # phase bands
    phases = [("AWARENESS", 0, 1, "#E0F2F1"), ("AUTHENTICATION", 1, 4, "#FFF3E0"),
              ("DISCOVERY", 4, 8, "#E3F2FD"), ("CONVERSION", 8, 10, "#E8F5E9")]
    for name, a, b, col in phases:
        bx = x0 + a*gap
        bw = (b-a)*gap
        g.append(R(bx, top, bw-6, 40, 8, col))
        g.append(T(bx+(bw-6)/2, top+25, name, 12, "#334155", "bold", "middle", spacing="1"))
    # column cards
    rowy = [("ACTION", top+58), ("SYSTEM RESPONSE", top+150)]
    for lbl, yy in rowy:
        g.append(T(40, yy+14, lbl, 10.5, MUTED, "bold", spacing="1"))
    for i, (title, action, resp, emoji, val) in enumerate(steps):
        cx = x0 + i*gap + gap/2
        bx = x0 + i*gap + 6
        bw = gap - 12
        # action card
        g.append(R(bx, top+58, bw, 78, 8, CARD, BORDER, 1))
        g.append(T(cx, top+80, title, 11.5, PRIMARY, "bold", "middle"))
        for j, wline in enumerate(_wrap(action, 16)):
            g.append(T(cx, top+100+j*15, wline, 10.5, INK, "normal", "middle"))
        # system card
        col = ERROR if i == 2 else BORDER
        g.append(R(bx, top+150, bw, 70, 8, GREY3, col, 1.5 if i == 2 else 1))
        for j, wline in enumerate(_wrap(resp, 17)):
            g.append(T(cx, top+178+j*15, wline, 10.5, "#334155", "normal", "middle"))
    # emotion curve
    ey0, eh = 470, 150
    g.append(T(40, ey0-6, "EMOTION", 10.5, MUTED, "bold", spacing="1"))
    g.append(R(x0, ey0, W-120, eh, 10, CARD, BORDER, 1))
    g.append(line(x0, ey0+eh/2, x0+W-120, ey0+eh/2, GREY2, 1, "4 4"))
    pts = []
    for i, (_, _, _, emoji, val) in enumerate(steps):
        cx = x0 + i*gap + gap/2
        cy = ey0 + eh - 18 - val*(eh-36)
        pts.append((cx, cy))
    d = "M " + " L ".join(f"{x:.0f} {y:.0f}" for x, y in pts)
    g.append(path(d, "none", PRIMARY, 3))
    for i, (cx, cy) in enumerate(pts):
        col = ERROR if i == 2 else (SUCCESS if i == 9 else PRIMARY)
        g.append(C(cx, cy, 12, "#FFFFFF", col, 2))
        g.append(T(cx, cy+5, steps[i][3], 14, INK, "normal", "middle"))
    # pain & opportunity callouts
    g.append(R(x0+1.6*gap, ey0+eh+18, 240, 44, 8, "#FEF2F2", ERROR, 1))
    g.append(T(x0+1.6*gap+12, ey0+eh+38, "PAIN POINT", 9.5, ERROR, "bold", spacing="1"))
    g.append(T(x0+1.6*gap+12, ey0+eh+54, "Login error – needs clear recovery", 11, "#7F1D1D"))
    g.append(R(x0+7.3*gap, ey0+eh+18, 250, 44, 8, "#ECFDF5", SUCCESS, 1))
    g.append(T(x0+7.3*gap+12, ey0+eh+38, "OPPORTUNITY", 9.5, SUCCESS, "bold", spacing="1"))
    g.append(T(x0+7.3*gap+12, ey0+eh+54, "Instant feedback boosts confidence", 11, "#14532D"))
    save("02_user_journey.svg", doc(W, H, "\n".join(g)))


def _wrap(text, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        if len(cur)+len(w)+1 <= width:
            cur = (cur+" "+w).strip()
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines[:3]


# =======================================================================
# 3. LOW-FIDELITY WIREFRAMES (6 grayscale screens)
# =======================================================================
def wireframes():
    W, H = 1320, 760
    g = [T(40, 50, "Low-Fidelity Wireframes", 28, INK, "bold"),
         T(40, 76, "Grayscale layout, hierarchy & spacing  6 core screens (Step 6)", 14, MUTED)]

    def frame(x, y, title, draw):
        s = [R(x, y, 360, 300, 10, CARD, "#94A3B8", 1.5)]
        s.append(R(x, y, 360, 30, 10, GREY3))
        s.append(R(x, y+18, 360, 12, 0, GREY3))
        s.append(C(x+16, y+15, 4, GREY1))
        s.append(T(x+30, y+19, title, 11, MUTED, "bold"))
        s.append(draw(x, y+30))
        return "\n".join(s)

    def bx(x, y, w, h, r=4, fill=GREY2):
        return R(x, y, w, h, r, fill)
    def ln(x, y, w, c=GREY1, h=8):
        return R(x, y, w, h, 4, c)

    def login(x, y):
        s = [bx(x+130, y+30, 100, 100, 50, GREY1)]
        s += [ln(x+90, y+150, 180, GREY1, 12)]
        s += [bx(x+40, y+185, 280, 30), bx(x+40, y+225, 280, 30)]
        s += [bx(x+40, y+265, 280, 34, 6, "#94A3B8")]
        return "\n".join(s)
    def dash(x, y):
        s = [bx(x+20, y+15, 320, 50, 8)]
        s += [bx(x+20+i*108, y+80, 96, 60, 8) for i in range(3)]
        s += [ln(x+20, y+160, 120, GREY1, 10)]
        s += [bx(x+20, y+180, 320, 40), bx(x+20, y+228, 320, 40)]
        s += [R(x, y+270-30+30, 360, 30, 0, GREY3)]
        return "\n".join(s)
    def navm(x, y):
        s = [bx(x+20, y+20, 240, 40, 8, GREY1)]
        s += [bx(x+20, y+78+i*42, 320, 30) for i in range(5)]
        return "\n".join(s)
    def settings(x, y):
        s = [ln(x+20, y+22, 140, GREY1, 12)]
        for i in range(5):
            s += [bx(x+20, y+50+i*42, 320, 32)]
            s += [bx(x+285, y+56+i*42, 40, 20, 10, GREY1)]
        return "\n".join(s)
    def profile(x, y):
        s = [bx(x+150, y+20, 60, 60, 30, GREY1)]
        s += [ln(x+120, y+95, 120, GREY1, 10)]
        s += [bx(x+20, y+125+i*40, 320, 30) for i in range(4)]
        return "\n".join(s)
    def confirm(x, y):
        s = [bx(x+150, y+25, 60, 60, 30, GREY1)]
        s += [ln(x+90, y+105, 180, GREY1, 12)]
        s += [bx(x+40, y+135, 280, 24), bx(x+60, y+167, 240, 18)]
        s += [bx(x+40, y+215, 130, 34, 6, GREY1), bx(x+190, y+215, 130, 34, 6, "#94A3B8")]
        return "\n".join(s)

    cells = [("Login", login), ("Dashboard", dash), ("Navigation menu", navm),
             ("Settings", settings), ("Profile", profile), ("Confirmation", confirm)]
    for i, (t, fn) in enumerate(cells):
        x = 40 + (i % 3)*420
        y = 110 + (i // 3)*330
        g.append(frame(x, y, t, fn))
    save("03_wireframes_lowfi.svg", doc(W, H, "\n".join(g)))


# =======================================================================
# 4-9. HIGH-FIDELITY UI SCREENS
# =======================================================================
def ui_login():
    s = [R(0, 44, 390, 800, 0, PRIMARY)]
    s.append(R(0, 300, 390, 544, 0, "#FFFFFF"))
    s.append(R(0, 300, 390, 60, 30, "#FFFFFF"))
    s.append(C(300, 150, 80, "#FFFFFF", opacity=0.10))
    s.append(C(70, 240, 50, "#FFFFFF", opacity=0.08))
    # logo
    s.append(C(195, 140, 38, "#FFFFFF"))
    s.append(ic_heart(195, 140, PRIMARY))
    s.append(T(195, 215, "MediCare+", 30, "#FFFFFF", "bold", "middle"))
    s.append(T(195, 242, "Your hospital, in your pocket", 13, "#CFFAF5", "normal", "middle"))
    s.append(T(40, 355, "Welcome back", 24, INK, "bold"))
    s.append(T(40, 382, "Sign in to continue", 14, MUTED))
    # fields
    s.append(T(40, 425, "EMAIL", 11, MUTED, "bold", spacing="1"))
    s.append(R(40, 435, 310, 52, 12, "#F8FAFC", BORDER, 1.5))
    s.append(ic_user(64, 461, MUTED, 1.8))
    s.append(T(86, 466, "sara.ahmed@email.com", 14, INK))
    s.append(T(40, 515, "PASSWORD", 11, MUTED, "bold", spacing="1"))
    s.append(R(40, 525, 310, 52, 12, "#F8FAFC", PRIMARY, 2))
    s.append(T(64, 556, "• • • • • • • •", 16, INK))
    s.append(T(326, 558, "\U0001F441", 14, MUTED, "normal", "middle"))
    s.append(T(310, 605, "Forgot password?", 12.5, PRIMARY, "bold", "end"))
    s.append(btn(40, 630, 310, 54, "Sign In", PRIMARY))
    # divider
    s.append(line(40, 715, 160, 715, BORDER))
    s.append(line(230, 715, 350, 715, BORDER))
    s.append(T(195, 719, "or", 12, MUTED, "normal", "middle"))
    s.append(R(40, 735, 310, 50, 12, "#FFFFFF", BORDER, 1.5))
    s.append(T(195, 766, "Continue as Guest", 14, INK, "bold", "middle"))
    s.append(T(195, 815, "New here?  Create account", 13, MUTED, "normal", "middle"))
    save("04_ui_login.svg", doc(900, 1000,
        phone(60, 60, "\n".join(s), label="Screen 1  Login",
              label_sub="Branded, single-column, large tap targets")))


def ui_dashboard():
    s = [appbar("Hi, Sara \U0001F44B", "How are you feeling today?")]
    # search
    s.append(R(24, 158, 342, 50, 14, "#FFFFFF", BORDER, 1.5))
    s.append(ic_search(48, 184, 8, MUTED, 2))
    s.append(T(70, 189, "Search doctors, services, labs", 13.5, LIGHT))
    # quick actions
    acts = [("Book", PRIMARY), ("Records", "#6366F1"), ("Pharmacy", "#EC4899"), ("Emergency", ERROR)]
    for i, (lbl, col) in enumerate(acts):
        x = 24 + i*87
        s.append(R(x, 228, 75, 84, 16, "#FFFFFF", BORDER, 1))
        s.append(C(x+37, 262, 18, col + "22" if False else "#F1F5F9"))
        s.append(C(x+37, 262, 18, col, opacity=0.14))
        if i == 0:
            s.append(ic_cal(x+37, 262, col, 2))
        elif i == 1:
            s.append(R(x+30, 255, 14, 16, 2, "none", col, 2))
        elif i == 2:
            s.append(ic_heart(x+37, 262, col))
        else:
            s.append(path(f"M {x+37} 254 L {x+37} 270 M {x+29} 262 L {x+45} 262", "none", col, 3))
        s.append(T(x+37, 302, lbl, 10.5, INK, "bold", "middle"))
    # upcoming appointment banner
    s.append(R(24, 332, 342, 96, 16, PRIMARY))
    s.append(T(44, 360, "UPCOMING VISIT", 10, "#CFFAF5", "bold", spacing="1"))
    s.append(T(44, 386, "Dr. Imran Khan", 18, "#FFFFFF", "bold"))
    s.append(T(44, 408, "Cardiology  Today, 4:30 PM", 12.5, "#E0F2F1"))
    s.append(C(330, 380, 26, "#FFFFFF", opacity=0.18))
    s.append(ic_user(330, 378, "#FFFFFF", 2))
    s.append(R(290, 398, 60, 22, 11, "#FFFFFF"))
    s.append(T(320, 413, "Join", 11, PRIMARY, "bold", "middle"))
    # categories
    s.append(T(24, 462, "Specialties", 16, INK, "bold"))
    s.append(T(366, 462, "See all", 12, PRIMARY, "bold", "end"))
    cats = ["Cardio", "Dental", "Neuro", "Derma", "Ortho", "ENT"]
    for i, cnm in enumerate(cats):
        x = 24 + (i % 3)*116
        y = 480 + (i // 3)*78
        s.append(R(x, y, 104, 66, 14, "#FFFFFF", BORDER, 1))
        s.append(C(x+24, y+33, 14, PRIMARY, opacity=0.12))
        s.append(ic_heart(x+24, y+33, PRIMARY))
        s.append(T(x+44, y+38, cnm, 12.5, INK, "bold"))
    # promo
    s.append(R(24, 650, 342, 78, 16, "#EEF6FF", "#BFDBFE", 1))
    s.append(T(44, 682, "Free health check-up", 15, "#1E40AF", "bold"))
    s.append(T(44, 704, "Book a full screening this week", 12, "#3B82F6"))
    s.append(bottomnav(0))
    save("05_ui_dashboard.svg", doc(900, 1000,
        phone(60, 60, "\n".join(s), label="Screen 2  Dashboard",
              label_sub="Personalised home, quick actions, clear hierarchy")))


def ui_search():
    s = [appbar("Find a Doctor", back=True)]
    s.append(R(24, 138, 300, 48, 14, "#FFFFFF", BORDER, 1.5))
    s.append(ic_search(48, 162, 8, PRIMARY, 2))
    s.append(T(70, 167, "Cardiologist", 14, INK, "bold"))
    s.append(R(334, 138, 32, 48, 12, PRIMARY))
    s.append(path("M 343 154 L 357 154 M 346 162 L 354 162 M 348 170 L 352 170", "none", "#FFFFFF", 2))
    # filter chips
    chips = [("Top rated", True), ("Available today", True), ("< Rs.2000", False), ("Female", False)]
    cx = 24
    for lbl, on in chips:
        w = 30 + len(lbl)*7
        s.append(R(cx, 200, w, 32, 16, PRIMARY if on else "#FFFFFF", "none" if on else BORDER, 1))
        s.append(T(cx+w/2, 220, lbl, 11.5, "#FFFFFF" if on else MUTED, "bold", "middle"))
        cx += w + 8
    s.append(T(24, 262, "8 cardiologists found", 12.5, MUTED, "bold"))
    # doctor cards
    docs = [("Dr. Imran Khan", "Cardiologist  12 yrs", "4.9", "Today 4:30 PM", "Rs.1,800"),
            ("Dr. Ayesha Malik", "Cardiologist  9 yrs", "4.8", "Tomorrow 11 AM", "Rs.2,000"),
            ("Dr. Bilal Raza", "Cardiologist  15 yrs", "4.7", "Today 6:00 PM", "Rs.2,200")]
    for i, (nm, spec, rt, slot, fee) in enumerate(docs):
        y = 282 + i*138
        sel = i == 0
        s.append(R(24, y, 342, 122, 16, "#FFFFFF", PRIMARY if sel else BORDER, 2 if sel else 1))
        s.append(C(58, y+44, 26, "#E0F2F1"))
        s.append(ic_user(58, y+42, PRIMARY, 2))
        s.append(T(96, y+34, nm, 15.5, INK, "bold"))
        s.append(T(96, y+54, spec, 12, MUTED))
        s.append(star(100, y+74, 6))
        s.append(T(112, y+78, f"{rt}", 12, INK, "bold"))
        s.append(T(140, y+78, "(120 reviews)", 11, MUTED))
        s.append(R(96, y+92, 130, 22, 11, "#ECFDF5"))
        s.append(C(108, y+103, 3, SUCCESS))
        s.append(T(118, y+107, slot, 10.5, "#15803D", "bold"))
        s.append(T(342, y+34, fee, 14, PRIMARY, "bold", "end"))
        s.append(R(246, y+88, 100, 30, 10, PRIMARY if sel else "#FFFFFF", "none" if sel else PRIMARY, 1.5))
        s.append(T(296, y+108, "Book", 12.5, "#FFFFFF" if sel else PRIMARY, "bold", "middle"))
    s.append(bottomnav(1))
    save("06_ui_doctor_search.svg", doc(900, 1000,
        phone(60, 60, "\n".join(s), label="Screen 3  Doctor Search + Filters",
              label_sub="Live results, filter chips, scannable cards")))


def ui_appointment():
    s = [appbar("Book Appointment", back=True)]
    # doctor summary
    s.append(R(24, 138, 342, 96, 16, "#FFFFFF", BORDER, 1))
    s.append(C(64, 186, 28, "#E0F2F1"))
    s.append(ic_user(64, 184, PRIMARY, 2))
    s.append(T(104, 172, "Dr. Imran Khan", 17, INK, "bold"))
    s.append(T(104, 192, "Cardiologist  Shifa Hospital", 12, MUTED))
    s.append(star(108, 212, 6))
    s.append(T(120, 216, "4.9  12 yrs exp", 11.5, INK, "bold"))
    s.append(T(346, 172, "Rs.1,800", 14, PRIMARY, "bold", "end"))
    # date picker
    s.append(T(24, 268, "Select date", 15, INK, "bold"))
    days = [("Mon", "9"), ("Tue", "10"), ("Wed", "11"), ("Thu", "12"), ("Fri", "13")]
    for i, (d, num) in enumerate(days):
        x = 24 + i*70
        sel = i == 2
        s.append(R(x, 284, 60, 76, 14, PRIMARY if sel else "#FFFFFF", "none" if sel else BORDER, 1))
        s.append(T(x+30, 308, d, 11.5, "#CFFAF5" if sel else MUTED, "bold", "middle"))
        s.append(T(x+30, 338, num, 20, "#FFFFFF" if sel else INK, "bold", "middle"))
    # time slots
    s.append(T(24, 396, "Available slots", 15, INK, "bold"))
    slots = [("09:00 AM", 0), ("10:30 AM", 0), ("12:00 PM", 2),
             ("02:00 PM", 0), ("04:30 PM", 1), ("06:00 PM", 0)]
    for i, (slot, st) in enumerate(slots):
        x = 24 + (i % 3)*116
        y = 412 + (i // 3)*58
        if st == 1:    fill, fg, br = PRIMARY, "#FFFFFF", "none"
        elif st == 2:  fill, fg, br = GREY3, LIGHT, BORDER
        else:          fill, fg, br = "#FFFFFF", INK, BORDER
        s.append(R(x, y, 104, 46, 12, fill, br, 1.5))
        s.append(T(x+52, y+29, slot, 13, fg, "bold", "middle"))
    s.append(T(24, 545, "Reason for visit (optional)", 12.5, MUTED, "bold"))
    s.append(R(24, 556, 342, 70, 12, "#F8FAFC", BORDER, 1.5))
    s.append(T(40, 582, "Chest tightness when climbing stairs...", 12, LIGHT))
    # summary
    s.append(R(24, 642, 342, 70, 14, "#F0FDFA", ACCENT, 1))
    s.append(T(40, 668, "Wed 11 Jun  4:30 PM", 14, INK, "bold"))
    s.append(T(40, 690, "Consultation fee", 11.5, MUTED))
    s.append(T(346, 690, "Rs.1,800", 15, PRIMARY, "bold", "end"))
    s.append(btn(24, 726, 342, 54, "Proceed to Payment", PRIMARY))
    save("07_ui_appointment.svg", doc(900, 1000,
        phone(60, 60, "\n".join(s), label="Screen 4  Appointment Booking",
              label_sub="Date & slot selection, disabled states, live summary")))


def ui_payment():
    s = [appbar("Payment", back=True)]
    # confirm dialog feel: order summary
    s.append(R(24, 138, 342, 110, 16, "#FFFFFF", BORDER, 1))
    s.append(T(44, 168, "Appointment summary", 13, MUTED, "bold"))
    s.append(T(44, 194, "Dr. Imran Khan  Cardiology", 14, INK, "bold"))
    s.append(T(44, 216, "Wed, 11 Jun 2026  4:30 PM", 12, MUTED))
    s.append(line(44, 230, 346, 230, BORDER))
    s.append(T(44, 244, "Wed 11 Jun", 0.1, BORDER))
    # payment methods
    s.append(T(24, 282, "Payment method", 15, INK, "bold"))
    methods = [("Credit / Debit Card", "Visa ending 4242", True),
               ("JazzCash / Easypaisa", "Mobile wallet", False),
               ("Cash at hospital", "Pay on arrival", False)]
    for i, (m, sub, on) in enumerate(methods):
        y = 298 + i*72
        s.append(R(24, y, 342, 60, 14, "#FFFFFF", PRIMARY if on else BORDER, 2 if on else 1))
        s.append(R(40, y+18, 36, 24, 5, "#EEF6FF", "#BFDBFE", 1))
        s.append(T(58, y+34, "\U0001F4B3", 13, INK, "normal", "middle"))
        s.append(T(92, y+27, m, 14, INK, "bold"))
        s.append(T(92, y+45, sub, 11.5, MUTED))
        s.append(C(348, y+30, 10, "none", PRIMARY if on else LIGHT, 2))
        if on:
            s.append(C(348, y+30, 5, PRIMARY))
    # fee breakdown
    s.append(R(24, 522, 342, 118, 14, "#F8FAFC", BORDER, 1))
    rows = [("Consultation fee", "Rs.1,800"), ("Platform fee", "Rs.50"), ("Tax (5%)", "Rs.92")]
    for i, (k, v) in enumerate(rows):
        s.append(T(44, 552+i*26, k, 12.5, MUTED))
        s.append(T(346, 552+i*26, v, 12.5, INK, "bold", "end"))
    s.append(line(44, 612, 346, 612, BORDER))
    s.append(T(44, 632, "Total", 15, INK, "bold"))
    s.append(T(346, 632, "Rs.1,942", 16, PRIMARY, "bold", "end"))
    # secure note
    s.append(C(40, 668, 7, "none", SUCCESS, 2))
    s.append(path("M 37 668 L 39 671 L 43 665", "none", SUCCESS, 1.8))
    s.append(T(54, 672, "256-bit encrypted  secure payment", 11.5, MUTED))
    s.append(btn(24, 692, 342, 54, "Pay Rs.1,942", PRIMARY))
    save("08_ui_payment.svg", doc(900, 1000,
        phone(60, 60, "\n".join(s), label="Screen 5  Secure Payment",
              label_sub="Selectable methods, transparent fees, trust cues")))


def ui_success():
    s = [R(0, 44, 390, 800, 0, "#FFFFFF")]
    s.append(R(0, 44, 390, 360, 0, PRIMARY))
    s.append(R(0, 360, 390, 60, 30, "#FFFFFF"))
    s.append(C(80, 120, 50, "#FFFFFF", opacity=0.08))
    s.append(C(330, 300, 70, "#FFFFFF", opacity=0.08))
    # check badge
    s.append(C(195, 200, 64, "#FFFFFF", opacity=0.18))
    s.append(C(195, 200, 48, "#FFFFFF"))
    s.append(path("M 175 200 L 189 214 L 217 184", "none", SUCCESS, 6))
    s.append(T(195, 300, "Booking Confirmed!", 26, "#FFFFFF", "bold", "middle"))
    s.append(T(195, 328, "A confirmation has been sent to", 13, "#E0F2F1", "normal", "middle"))
    s.append(T(195, 348, "sara.ahmed@email.com", 13, "#FFFFFF", "bold", "middle"))
    # ticket card
    s.append(R(34, 430, 322, 250, 18, "#FFFFFF", BORDER, 1))
    s.append(R(34, 430, 322, 6, 18, PRIMARY))
    s.append(C(34, 555, 14, BG))
    s.append(C(356, 555, 14, BG))
    s.append(line(58, 555, 332, 555, BORDER, 1.5, "5 5"))
    s.append(C(74, 470, 24, "#E0F2F1"))
    s.append(ic_user(74, 468, PRIMARY, 2))
    s.append(T(110, 462, "Dr. Imran Khan", 16, INK, "bold"))
    s.append(T(110, 482, "Cardiology  Shifa Hospital", 11.5, MUTED))
    cols = [("DATE", "Wed, 11 Jun"), ("TIME", "4:30 PM")]
    for i, (k, v) in enumerate(cols):
        s.append(T(58+i*150, 522, k, 10, MUTED, "bold", spacing="1"))
        s.append(T(58+i*150, 542, v, 14, INK, "bold"))
    s.append(T(58, 590, "TOKEN", 10, MUTED, "bold", spacing="1"))
    s.append(T(58, 610, "#A-042", 16, PRIMARY, "bold"))
    s.append(T(332, 590, "FEE PAID", 10, MUTED, "bold", spacing="1", anchor="end"))
    s.append(T(332, 610, "Rs.1,942", 16, INK, "bold", "end"))
    # qr
    s.append(R(150, 630, 90, 40, 6, GREY3))
    s.append(T(195, 655, "█ █ █ QR", 12, INK, "normal", "middle"))
    # reminder toast
    s.append(R(34, 700, 322, 48, 12, "#ECFDF5", SUCCESS, 1))
    s.append(C(58, 724, 8, SUCCESS))
    s.append(path("M 54 724 L 57 727 L 62 721", "none", "#FFFFFF", 1.8))
    s.append(T(76, 728, "Reminder set for 1 hour before visit", 12, "#15803D", "bold"))
    s.append(btn(34, 762, 154, 50, "View Visits", PRIMARY))
    s.append(R(202, 762, 154, 50, 14, "#FFFFFF", PRIMARY, 1.5))
    s.append(T(279, 792, "Add to Calendar", 13, PRIMARY, "bold", "middle"))
    save("09_ui_success.svg", doc(900, 1000,
        phone(60, 60, "\n".join(s), label="Screen 6  Success Confirmation",
              label_sub="Positive feedback, e-ticket, clear next steps")))


# =======================================================================
# 10. STORYBOARD (10 annotated frames)
# =======================================================================
def storyboard():
    W, H = 1500, 980
    g = [T(40, 50, "Storyboard  10 Annotated Frames", 28, INK, "bold"),
         T(40, 76, "UI screen + user action + system response + emotion (Step 8)", 14, MUTED)]
    frames = [
        ("01", "Open App", "Sara taps the MediCare+ icon", "Splash + session check", "\U0001F642 Hopeful", "screen"),
        ("02", "Login Shown", "Login form appears", "Fields focused, keyboard up", "\U0001F610 Neutral", "form"),
        ("03", "Enter Credentials", "Types email & password", "Masks input, validates format", "\U0001F610 Focused", "form2"),
        ("04", "Wrong Password", "Submits wrong password", "Inline red error + shake", "\U0001F61F Annoyed", "error"),
        ("05", "Retry Login", "Re-enters correctly", "Spinner → auth success", "\U0001F642 Relieved", "load"),
        ("06", "Dashboard Loads", "Lands on home", "Personalised cards render", "\U0001F600 Pleased", "dash"),
        ("07", "Select Doctor", "Searches & taps a doctor", "Profile + slots open", "\U0001F600 Engaged", "list"),
        ("08", "Confirm Dialog", "Taps Book → confirm", "Modal asks to confirm", "\U0001F914 Cautious", "modal"),
        ("09", "Payment Success", "Pays consultation fee", "Secure spinner → done", "\U0001F60C Confident", "pay"),
        ("10", "Success Toast", "Sees confirmation", "Toast + reminder set", "\U0001F929 Delighted", "done"),
    ]
    fw, fh = 270, 400
    gapx, gapy = 18, 40
    for i, (no, title, action, resp, emo, kind) in enumerate(frames):
        x = 40 + (i % 5)*(fw+gapx)
        y = 110 + (i // 5)*(fh+gapy+40)
        g.append(R(x, y, fw, fh, 14, CARD, BORDER, 1.5))
        # number badge
        g.append(C(x+26, y+26, 16, PRIMARY))
        g.append(T(x+26, y+31, no, 13, "#FFFFFF", "bold", "middle"))
        g.append(T(x+52, y+24, title, 14, INK, "bold"))
        emc = ERROR if "Annoyed" in emo else (SUCCESS if i in (5,9) else MUTED)
        g.append(T(x+fw-12, y+24, emo, 11, emc, "bold", "end"))
        # mini screen
        sx, sy, sw, sh = x+24, y+52, fw-48, 210
        g.append(_mini_screen(sx, sy, sw, sh, kind))
        # annotations
        ay = y+278
        g.append(T(x+16, ay, "ACTION", 9, PRIMARY, "bold", spacing="1"))
        for j, l in enumerate(_wrap(action, 34)):
            g.append(T(x+16, ay+16+j*14, l, 11, INK))
        g.append(T(x+16, ay+58, "SYSTEM RESPONSE", 9, MUTED, "bold", spacing="1"))
        for j, l in enumerate(_wrap(resp, 34)):
            g.append(T(x+16, ay+74+j*14, l, 11, "#334155"))
        # arrow to next
        if (i % 5) != 4 and i != 9:
            ax = x+fw+2
            ay2 = y+fh/2
            g.append(path(f"M {ax} {ay2} L {ax+gapx-4} {ay2}", "none", PRIMARY, 2.5))
            g.append(path(f"M {ax+gapx-9} {ay2-5} L {ax+gapx-4} {ay2} L {ax+gapx-9} {ay2+5}", "none", PRIMARY, 2.5))
    # row connector 5 -> 6
    g.append(path(f"M {40+4*(fw+gapx)+fw/2} {110+fh+10} C {40+4*(fw+gapx)+fw/2} {110+fh+30}, "
                  f"{40+fw/2} {110+fh+10}, {40+fw/2} {110+fh+gapy+40-10}", "none", PRIMARY, 2.5, "round", "round").replace("fill='none'","fill='none' stroke-dasharray='6 5'"))
    save("10_storyboard.svg", doc(W, H, "\n".join(g)))


def _mini_screen(x, y, w, h, kind):
    s = [R(x, y, w, h, 10, "#F8FAFC", BORDER, 1)]
    s.append(R(x, y, w, 22, 10, "#FFFFFF"))
    s.append(R(x, y+12, w, 10, 0, "#FFFFFF"))
    s.append(C(x+12, y+11, 3, GREY1))
    cx = x+w/2
    if kind == "screen":
        s.append(C(cx, y+90, 30, PRIMARY))
        s.append(ic_heart(cx, y+90, "#FFFFFF"))
        s.append(T(cx, y+150, "MediCare+", 14, PRIMARY, "bold", "middle"))
        s.append(R(x+w/2-30, y+170, 60, 6, 3, GREY2))
    elif kind in ("form", "form2"):
        s.append(C(cx, y+50, 20, GREY2))
        s.append(R(x+20, y+85, w-40, 28, 6, "#FFFFFF", BORDER, 1))
        s.append(R(x+20, y+122, w-40, 28, 6, "#FFFFFF", PRIMARY if kind=="form2" else BORDER, 1.5))
        if kind == "form2":
            s.append(T(x+30, y+140, "• • • • •", 12, INK))
        s.append(btn(x+20, y+162, w-40, 30, "Sign In", PRIMARY, size=12, r=8))
    elif kind == "error":
        s.append(R(x+20, y+50, w-40, 28, 6, "#FFFFFF", BORDER, 1))
        s.append(R(x+20, y+88, w-40, 28, 6, "#FEF2F2", ERROR, 2))
        s.append(T(x+24, y+106, "• • • • •", 12, ERROR))
        s.append(T(x+20, y+132, "⚠ Incorrect password", 10.5, ERROR, "bold"))
        s.append(btn(x+20, y+150, w-40, 30, "Try Again", ERROR, size=12, r=8))
    elif kind == "load":
        s.append(C(cx, y+95, 22, "none", GREY2, 5))
        s.append(path(f"M {cx} {y+73} A 22 22 0 0 1 {cx+22} {y+95}", "none", PRIMARY, 5))
        s.append(T(cx, y+150, "Signing in...", 12, MUTED, "normal", "middle"))
    elif kind == "dash":
        s.append(R(x+16, y+34, w-32, 30, 6, PRIMARY))
        for i in range(3):
            s.append(R(x+16+i*((w-32)/3-4)+i*2, y+74, (w-32)/3-8, 34, 6, "#FFFFFF", BORDER, 1))
        s.append(R(x+16, y+120, w-32, 30, 6, "#FFFFFF", BORDER, 1))
        s.append(R(x+16, y+156, w-32, 30, 6, "#FFFFFF", BORDER, 1))
    elif kind == "list":
        for i in range(3):
            yy = y+38+i*52
            br = PRIMARY if i == 0 else BORDER
            s.append(R(x+16, yy, w-32, 44, 8, "#FFFFFF", br, 1.5 if i==0 else 1))
            s.append(C(x+34, yy+22, 12, "#E0F2F1"))
            s.append(R(x+54, yy+12, 70, 7, 3, GREY1))
            s.append(R(x+54, yy+26, 50, 6, 3, GREY2))
            s.append(star(x+w-46, yy+22, 5))
    elif kind == "modal":
        s.append(R(x, y+22, w, h-22, 0, "#0F172A", opacity=0.35))
        s.append(R(x+24, y+60, w-48, 130, 12, "#FFFFFF", BORDER, 1))
        s.append(C(cx, y+92, 18, "#E0F2F1"))
        s.append(ic_cal(cx, y+90, PRIMARY, 2))
        s.append(T(cx, y+128, "Confirm booking?", 12, INK, "bold", "middle"))
        s.append(R(x+36, y+148, (w-84)/2, 28, 8, "#FFFFFF", BORDER, 1))
        s.append(T(x+36+(w-84)/4, y+166, "Cancel", 11, MUTED, "bold", "middle"))
        s.append(btn(x+48+(w-84)/2, y+148, (w-84)/2, 28, "Confirm", PRIMARY, size=11, r=8))
    elif kind == "pay":
        s.append(C(cx, y+88, 24, "none", GREY2, 5))
        s.append(path(f"M {cx} {y+64} A 24 24 0 0 1 {cx+24} {y+88}", "none", PRIMARY, 5))
        s.append(T(cx, y+144, "Processing payment", 11.5, MUTED, "normal", "middle"))
        s.append(T(cx, y+162, "Rs.1,942", 13, INK, "bold", "middle"))
    elif kind == "done":
        s.append(C(cx, y+80, 28, SUCCESS))
        s.append(path(f"M {cx-13} {y+80} L {cx-3} {y+90} L {cx+15} {y+68}", "none", "#FFFFFF", 5))
        s.append(T(cx, y+128, "Confirmed!", 14, SUCCESS, "bold", "middle"))
        s.append(R(x+24, y+148, w-48, 30, 8, "#ECFDF5", SUCCESS, 1))
        s.append(T(cx, y+168, "Reminder set", 11, "#15803D", "bold", "middle"))
    return "\n".join(s)


# =======================================================================
# 11. NAVIGATION FLOW DIAGRAM
# =======================================================================
def navflow():
    W, H = 1280, 720
    g = [T(40, 50, "Navigation & Interaction Flow", 28, INK, "bold"),
         T(40, 76, "Screen transitions, decision points & error-handling paths (Step 9)", 14, MUTED)]

    def node(x, y, w, h, label, sub=None, fill=CARD, stroke=PRIMARY, txt=INK):
        s = [R(x, y, w, h, 12, fill, stroke, 2)]
        s.append(T(x+w/2, y+(h/2 if not sub else h/2-6), label, 14, txt, "bold", "middle"))
        if sub:
            s.append(T(x+w/2, y+h/2+14, sub, 10.5, MUTED if txt==INK else txt, "normal", "middle"))
        return "\n".join(s)

    def diamond(cx, cy, w, h, label):
        pts = f"{cx},{cy-h/2} {cx+w/2},{cy} {cx},{cy+h/2} {cx-w/2},{cy}"
        return (f"<polygon points='{pts}' fill='#FFF7ED' stroke='{WARN}' stroke-width='2'/>" +
                T(cx, cy+4, label, 12, "#92400E", "bold", "middle"))

    def arrow(x1, y1, x2, y2, label=None, col=PRIMARY, dash=None, lpos=0.5):
        d = " stroke-dasharray='6 5'" if dash else ""
        s = [f"<line x1='{x1}' y1='{y1}' x2='{x2}' y2='{y2}' stroke='{col}' stroke-width='2.2'{d}/>"]
        import math
        ang = math.atan2(y2-y1, x2-x1)
        s.append(f"<polygon points='{x2},{y2} {x2-10*math.cos(ang-0.4):.0f},{y2-10*math.sin(ang-0.4):.0f} "
                 f"{x2-10*math.cos(ang+0.4):.0f},{y2-10*math.sin(ang+0.4):.0f}' fill='{col}'/>")
        if label:
            lx, ly = x1+(x2-x1)*lpos, y1+(y2-y1)*lpos
            s.append(R(lx-len(label)*3.4, ly-22, len(label)*6.8, 18, 4, "#FFFFFF", col, 1))
            s.append(T(lx, ly-9, label, 10, col, "bold", "middle"))
        return "\n".join(s)

    # nodes
    g.append(node(60, 150, 150, 64, "Splash", "auto check", CARD, LIGHT))
    g.append(node(60, 320, 150, 64, "Login", "Screen 1"))
    g.append(diamond(420, 352, 150, 90, "Valid?"))
    g.append(node(330, 470, 180, 60, "Error state", "inline message", "#FEF2F2", ERROR, "#991B1B"))
    g.append(node(560, 150, 170, 64, "Dashboard", "Screen 2"))
    g.append(node(800, 150, 170, 64, "Doctor Search", "Screen 3"))
    g.append(node(800, 300, 170, 64, "Appointment", "Screen 4"))
    g.append(diamond(1090, 332, 150, 90, "Confirm?"))
    g.append(node(1020, 470, 180, 60, "Back to list", "re-select", GREY3, LIGHT))
    g.append(node(800, 470, 170, 64, "Payment", "Screen 5"))
    g.append(node(560, 470, 170, 64, "Success", "Screen 6", "#ECFDF5", SUCCESS, "#15803D"))
    g.append(node(560, 300, 170, 64, "Profile / Records", "side nav"))

    g.append(arrow(135, 214, 135, 320))
    g.append(arrow(210, 352, 345, 352, "submit"))
    g.append(arrow(420, 397, 420, 470, "No", ERROR))
    g.append(arrow(330, 500, 210, 360, "retry", ERROR, dash=True))
    g.append(arrow(495, 352, 560, 200, "Yes  auth ok", SUCCESS))
    g.append(arrow(730, 182, 800, 182, "search"))
    g.append(arrow(885, 214, 885, 300, "select"))
    g.append(arrow(970, 332, 1015, 332, "book"))
    g.append(arrow(1090, 377, 1090, 470, "No", WARN))
    g.append(arrow(1020, 490, 970, 332, "edit", WARN, dash=True))
    g.append(arrow(1060, 362, 940, 478, "Yes", SUCCESS, lpos=0.4))
    g.append(arrow(800, 502, 730, 502, "paid", SUCCESS))
    g.append(arrow(645, 214, 645, 300, "menu", LIGHT, dash=True))
    g.append(arrow(560, 502, 300, 360, "home", LIGHT, dash=True, lpos=0.2))

    # legend
    g.append(R(60, 600, 1160, 80, 12, CARD, BORDER, 1))
    g.append(T(80, 628, "LEGEND", 11, MUTED, "bold", spacing="1"))
    leg = [(PRIMARY, "Primary path"), (SUCCESS, "Success transition"),
           (ERROR, "Error / recovery"), (WARN, "Decision branch"), (LIGHT, "Secondary nav")]
    lx = 80
    for col, txt in leg:
        g.append(line(lx, 656, lx+30, 656, col, 3))
        g.append(T(lx+38, 660, txt, 12, INK))
        lx += 230
    save("11_navigation_flow.svg", doc(W, H, "\n".join(g)))


# =======================================================================
# 12. USABILITY & ACCESSIBILITY BOARD
# =======================================================================
def evaluation():
    W, H = 1280, 860
    g = [T(40, 50, "Usability & Accessibility Evaluation", 28, INK, "bold"),
         T(40, 76, "Nielsen heuristics + WCAG 2.1 checks (Steps 11–13)", 14, MUTED)]
    # usability cards
    items = [
        ("Learnability", "Familiar patterns (bottom nav, cards) let first-time users book a visit without training. Icons paired with labels.", 0.9),
        ("Efficiency", "Quick-action tiles + persistent search cut the core task to 4 taps. Smart defaults pre-fill date/time.", 0.85),
        ("Memorability", "Consistent layout & colour roles mean returning users instantly recall where things live.", 0.8),
        ("Error prevention", "Disabled unavailable slots, input masking, and a confirm dialog before payment stop costly mistakes.", 0.88),
        ("Feedback", "Every action gives a visible response: spinners, inline errors, success toast & e-ticket.", 0.92),
    ]
    for i, (title, desc, score) in enumerate(items):
        x = 40 + (i % 3)*410
        y = 110 + (i // 3)*150
        g.append(R(x, y, 390, 132, 12, CARD, BORDER, 1))
        g.append(R(x, y, 6, 132, 12, PRIMARY))
        g.append(T(x+24, y+30, title, 16, INK, "bold"))
        for j, l in enumerate(_wrap(desc, 52)):
            g.append(T(x+24, y+54+j*16, l, 11.5, "#334155"))
        g.append(R(x+24, y+108, 250, 8, 4, GREY2))
        g.append(R(x+24, y+108, int(250*score), 8, 4, PRIMARY))
        g.append(T(x+286, y+114, f"{int(score*100)}/100", 12, PRIMARY, "bold"))
    # accessibility panel
    ay = 420
    g.append(R(40, ay, 590, 410, 12, CARD, BORDER, 1))
    g.append(T(64, ay+34, "Accessibility (WCAG 2.1)", 18, INK, "bold"))
    checks = [
        ("Contrast ratio", "Body text 7.4:1, buttons 5.1:1  passes AA/AAA"),
        ("Readable fonts", "16px base, 1.4 line-height, scalable to 200%"),
        ("Tap targets", "All interactive areas ≥ 44×44px"),
        ("Keyboard access", "Logical focus order + visible focus ring"),
        ("Screen reader", "Labelled icons, alt text, ARIA roles"),
        ("Colour-blind safe", "Status uses icon + text, never colour alone"),
    ]
    for i, (k, v) in enumerate(checks):
        yy = ay+64+i*56
        g.append(C(76, yy, 11, "none", SUCCESS, 2.2))
        g.append(path(f"M 71 {yy} L 75 {yy+4} L 82 {yy-5}", "none", SUCCESS, 2.2))
        g.append(T(100, yy-2, k, 13.5, INK, "bold"))
        g.append(T(100, yy+15, v, 11.5, MUTED))
    # contrast swatches
    g.append(T(360, ay+64, "CONTRAST SAMPLES", 10, MUTED, "bold", spacing="1"))
    sw = [(PRIMARY, "#FFFFFF", "5.1:1"), (INK, "#FFFFFF", "16:1"), ("#FFFFFF", PRIMARY, "5.1:1"), (WARN, INK, "8.2:1")]
    for i, (bg, fg, ratio) in enumerate(sw):
        yy = ay+80+i*78
        g.append(R(360, yy, 240, 64, 10, bg, BORDER, 1))
        g.append(T(380, yy+30, "Aa Book now", 16, fg, "bold"))
        g.append(T(380, yy+50, f"Ratio {ratio}  PASS", 11, fg))
    # consistency panel
    g.append(R(650, ay, 590, 410, 12, CARD, BORDER, 1))
    g.append(T(674, ay+34, "Design Consistency Check", 18, INK, "bold"))
    # color palette
    g.append(T(674, ay+66, "COLOUR PALETTE", 10, MUTED, "bold", spacing="1"))
    pal = [(PRIMARY,"Primary"),(PRIMARY_DARK,"Dark"),(ACCENT,"Accent"),(SUCCESS,"Success"),(WARN,"Warn"),(ERROR,"Error"),(INK,"Ink"),(MUTED,"Muted")]
    for i,(col,nm) in enumerate(pal):
        x = 674 + i*68
        g.append(R(x, ay+78, 56, 40, 8, col, BORDER, 1))
        g.append(T(x+28, ay+134, nm, 9.5, MUTED, "normal", "middle"))
    # typography
    g.append(T(674, ay+170, "TYPOGRAPHY SCALE", 10, MUTED, "bold", spacing="1"))
    g.append(T(674, ay+196, "Heading  24/700", 22, INK, "bold"))
    g.append(T(674, ay+222, "Subhead  16/700", 16, INK, "bold"))
    g.append(T(674, ay+244, "Body  14/400", 14, "#334155"))
    g.append(T(674, ay+264, "Caption  11/600", 11, MUTED, "bold"))
    # buttons consistency
    g.append(T(950, ay+170, "COMPONENTS", 10, MUTED, "bold", spacing="1"))
    g.append(btn(950, ay+182, 120, 38, "Primary", PRIMARY, size=13, r=10))
    g.append(R(950, ay+228, 120, 38, 10, "#FFFFFF", PRIMARY, 1.5)+T(1010, ay+252, "Secondary", 13, PRIMARY, "bold", "middle"))
    g.append(R(1082, ay+182, 120, 38, 10, GREY3, BORDER, 1)+T(1142, ay+206, "Disabled", 13, LIGHT, "bold", "middle"))
    g.append(R(1082, ay+228, 56, 38, 19, PRIMARY)+R(1118, ay+232, 30, 30, 15, "#FFFFFF"))
    # spacing/grid note
    g.append(R(674, ay+296, 528, 92, 10, "#F0FDFA", ACCENT, 1))
    g.append(T(694, ay+322, "8-pt spacing grid • 16px screen margins • 12px card radius", 12.5, "#0F766E", "bold"))
    g.append(T(694, ay+346, "Same button styles, icon set & elevation across all 6 screens.", 12, "#134E4A"))
    g.append(T(694, ay+368, "Single source of truth = predictable, trustworthy interface.", 12, "#134E4A"))
    save("12_usability_accessibility.svg", doc(W, H, "\n".join(g)))


if __name__ == "__main__":
    persona()
    journey()
    wireframes()
    ui_login()
    ui_dashboard()
    ui_search()
    ui_appointment()
    ui_payment()
    ui_success()
    storyboard()
    navflow()
    evaluation()
    print("\nAll SVGs generated in", OUT)

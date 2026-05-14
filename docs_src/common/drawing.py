"""Reusable drawing primitives: rounded boxes, arrows, side labels."""
import math

from reportlab.graphics.shapes import Line, Polygon, Rect, String
from reportlab.lib import colors

from .theme import DARK, GRAY


def box(d, x, y, w, h, fill, stroke, text, fs=9, fc=colors.white, bold=True):
    """Rounded rectangle with centered (possibly multi-line) text."""
    d.add(Rect(x, y, w, h, rx=4, ry=4,
               fillColor=fill, strokeColor=stroke, strokeWidth=1))
    font = "Helvetica-Bold" if bold else "Helvetica"
    lines = text.split("\n")
    line_h = fs + 2
    start_y = y + h / 2 + (len(lines) - 1) * line_h / 2 - fs / 3
    for i, line in enumerate(lines):
        d.add(String(
            x + w / 2, start_y - i * line_h, line,
            fontName=font, fontSize=fs, fillColor=fc, textAnchor="middle",
        ))


def arrow(d, x1, y1, x2, y2, color=GRAY, width=1.2):
    """Line segment with a triangular arrowhead at (x2, y2)."""
    d.add(Line(x1, y1, x2, y2, strokeColor=color, strokeWidth=width))
    angle = math.atan2(y2 - y1, x2 - x1)
    size = 5
    ax1 = x2 - size * math.cos(angle - math.pi / 6)
    ay1 = y2 - size * math.sin(angle - math.pi / 6)
    ax2 = x2 - size * math.cos(angle + math.pi / 6)
    ay2 = y2 - size * math.sin(angle + math.pi / 6)
    d.add(Polygon([x2, y2, ax1, ay1, ax2, ay2],
                  fillColor=color, strokeColor=color))


def label(d, x, y, text, fs=7, color=None, bold=True, anchor="start"):
    """Small text label, used for layer markers on the left of diagrams."""
    font = "Helvetica-Bold" if bold else "Helvetica"
    d.add(String(
        x, y, text, fontName=font, fontSize=fs,
        fillColor=color or GRAY, textAnchor=anchor,
    ))

"""Grayscale colour palette and shared paragraph styles."""
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

# Grayscale theme (black and white print friendly).
PRIMARY = colors.HexColor("#000000")
ACCENT = colors.HexColor("#7A7A7A")
LIGHT = colors.HexColor("#D9D9D9")
SOFT = colors.HexColor("#F2F2F2")
DARK = colors.HexColor("#000000")
GREEN = colors.HexColor("#3F3F3F")
ORANGE = colors.HexColor("#1A1A1A")
GRAY = colors.HexColor("#595959")


def build_styles():
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocTitle", fontName="Helvetica-Bold", fontSize=22,
        textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=8, leading=26,
    ))
    styles.add(ParagraphStyle(
        name="Subtitle", fontName="Helvetica", fontSize=12,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=14, leading=15,
    ))
    styles.add(ParagraphStyle(
        name="SectionHeader", fontName="Helvetica-Bold", fontSize=13,
        textColor=colors.white, backColor=PRIMARY,
        borderPadding=(5, 6, 5, 6), leftIndent=0,
        spaceBefore=10, spaceAfter=6, leading=16,
    ))
    styles.add(ParagraphStyle(
        name="SubHeader", fontName="Helvetica-Bold", fontSize=11,
        textColor=PRIMARY, spaceBefore=6, spaceAfter=3, leading=13,
    ))
    styles.add(ParagraphStyle(
        name="BodyText2", fontName="Helvetica", fontSize=10,
        textColor=DARK, alignment=TA_JUSTIFY, spaceAfter=5, leading=13,
    ))
    styles.add(ParagraphStyle(
        name="BulletText", fontName="Helvetica", fontSize=10,
        textColor=DARK, leftIndent=12, bulletIndent=2,
        spaceAfter=2, leading=13,
    ))
    styles.add(ParagraphStyle(
        name="Caption", fontName="Helvetica-Oblique", fontSize=9,
        textColor=GRAY, alignment=TA_CENTER, spaceAfter=8,
    ))
    styles.add(ParagraphStyle(
        name="CodeBlock", fontName="Courier", fontSize=9,
        textColor=DARK, leftIndent=14, spaceAfter=4, leading=12,
    ))
    return styles

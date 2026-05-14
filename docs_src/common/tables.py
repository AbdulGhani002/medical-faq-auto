"""Reusable Table styling helpers."""
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from .theme import LIGHT, PRIMARY, SOFT


def std_table_style() -> TableStyle:
    """Default table style: dark header, alternating row backgrounds."""
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, LIGHT),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])


def simple_table(data, col_widths, bold_first_col=True,
                 extra_styles=None) -> Table:
    """Convenience helper that returns a styled Table in one call."""
    t = Table(data, colWidths=col_widths)
    t.setStyle(std_table_style())
    if bold_first_col and len(data) > 1:
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
        ]))
    if extra_styles:
        t.setStyle(TableStyle(extra_styles))
    return t

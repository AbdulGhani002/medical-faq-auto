"""Orchestrate the architecture document PDF build."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate

from docs_src.common import build_styles

from .content import (
    backend_section, deployment_section, frontend_section,
    overview_section, sequence_section, title, trade_offs,
)


def build(out_path: str) -> str:
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
        title="Medical FAQ - Architecture Document",
    )
    styles = build_styles()
    story = []
    title(story, styles)
    overview_section(story, styles)
    frontend_section(story, styles)
    backend_section(story, styles)
    sequence_section(story, styles)
    deployment_section(story, styles)
    trade_offs(story, styles)
    doc.build(story)
    return out_path

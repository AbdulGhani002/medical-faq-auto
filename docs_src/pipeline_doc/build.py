"""Orchestrate the pipeline document PDF build."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate

from docs_src.common import build_styles

from .content import (
    cluster_view, overview, performance_section, quality_section,
    scheduling_section, stages_part_one, stages_part_two, title,
)


def build(out_path: str) -> str:
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
        title="Medical FAQ - Pipeline Document",
    )
    styles = build_styles()
    story = []
    title(story, styles)
    overview(story, styles)
    stages_part_one(story, styles)
    stages_part_two(story, styles)
    cluster_view(story, styles)
    scheduling_section(story, styles)
    performance_section(story, styles)
    quality_section(story, styles)
    doc.build(story)
    return out_path

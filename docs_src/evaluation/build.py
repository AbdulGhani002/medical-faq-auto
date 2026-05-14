"""Orchestrate the evaluation methodology PDF build."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate

from docs_src.common import build_styles

from .content import (
    answer_quality, chart_summary, cluster_eval, emerging_eval, goals,
    latency_eval, reporting, title,
)


def build(out_path: str) -> str:
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
        title="Medical FAQ - Evaluation Methodology",
    )
    styles = build_styles()
    story = []
    title(story, styles)
    goals(story, styles)
    chart_summary(story, styles)
    cluster_eval(story, styles)
    answer_quality(story, styles)
    latency_eval(story, styles)
    emerging_eval(story, styles)
    reporting(story, styles)
    doc.build(story)
    return out_path

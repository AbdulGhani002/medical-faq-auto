"""Orchestrate the data model + API reference PDF build."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate

from docs_src.common import build_styles

from .content_api import (
    api_overview, endpoint_admin, endpoint_chat, endpoint_faq,
    sample_requests,
)
from .content_data import (
    collections, indexes, overview, qdrant_section, title,
)


def build(out_path: str) -> str:
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
        title="Medical FAQ - Data Model and API Reference",
    )
    styles = build_styles()
    story = []
    title(story, styles)
    overview(story, styles)
    collections(story, styles)
    qdrant_section(story, styles)
    indexes(story, styles)
    api_overview(story, styles)
    endpoint_chat(story, styles)
    endpoint_faq(story, styles)
    endpoint_admin(story, styles)
    sample_requests(story, styles)
    doc.build(story)
    return out_path

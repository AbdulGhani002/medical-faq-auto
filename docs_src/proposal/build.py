"""Orchestrate the proposal PDF build."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate

from docs_src.common import build_styles

from .content_design import (
    architecture_section, datasets_section, pipeline_section, web_app_section,
)
from .content_impl import nlp_section, task_split_section, tools_section
from .content_outcomes import (
    closing_section, evaluation_section, results_section,
    timeline_section, value_section,
)
from .content_overview import (
    problem_and_objectives, tasks_and_requirements, title_block,
)


def build(out_path: str) -> str:
    doc = SimpleDocTemplate(
        out_path, pagesize=A4,
        leftMargin=1.6 * cm, rightMargin=1.6 * cm,
        topMargin=1.4 * cm, bottomMargin=1.4 * cm,
        title="Auto-Generated Medical FAQ Proposal",
        author="Group, Healthcare NLP Semester Project",
    )
    styles = build_styles()
    story = []

    title_block(story, styles)
    problem_and_objectives(story, styles)
    tasks_and_requirements(story, styles)
    datasets_section(story, styles)
    web_app_section(story, styles)
    architecture_section(story, styles)
    pipeline_section(story, styles)
    nlp_section(story, styles)
    tools_section(story, styles)
    task_split_section(story, styles)
    results_section(story, styles)
    value_section(story, styles)
    evaluation_section(story, styles)
    timeline_section(story, styles)
    closing_section(story, styles)

    doc.build(story)
    return out_path

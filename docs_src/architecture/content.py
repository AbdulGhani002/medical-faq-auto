"""Architecture document content sections."""
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from docs_src.common import simple_table
from docs_src.proposal.diagrams import architecture_diagram

from .diagrams import (
    backend_module_tree, deployment_diagram, frontend_component_tree,
    sequence_chat, sequence_pipeline,
)


def title(story, styles):
    story.append(Paragraph("System Architecture", styles["DocTitle"]))
    story.append(Paragraph(
        "Detailed architecture document for the Medical FAQ project.",
        styles["Subtitle"],
    ))


def overview_section(story, styles):
    story.append(Paragraph("1. Overview", styles["SectionHeader"]))
    story.append(Paragraph(
        "The system is split into five layers: users, frontend, API, services, "
        "and data. Every layer is independently deployable through "
        "docker-compose. The whole stack is designed to run on a single 4 vCPU "
        "8 GB VM so a small clinic or a university lab can host it without "
        "cloud spend.",
        styles["BodyText2"],
    ))
    story.append(architecture_diagram())
    story.append(Paragraph("Fig 1. Five-layer system view.", styles["Caption"]))


def frontend_section(story, styles):
    story.append(Paragraph("2. Frontend Layer", styles["SectionHeader"]))
    story.append(Paragraph(
        "Next.js 15 (React 19) handles all browser-facing pages. Routes are "
        "file-based under <font face='Courier'>src/app/</font>. Three pages are "
        "public (landing, chat, FAQ) and one is admin-only. Components are kept "
        "small and single-purpose so each member can iterate without stepping "
        "on others' work.",
        styles["BodyText2"],
    ))
    story.append(frontend_component_tree())
    story.append(Paragraph(
        "Fig 2. Frontend component tree (routes connect to components).",
        styles["Caption"],
    ))
    rows = [["Path", "Component", "Responsibility"]] + [
        ["/", "Home", "Lists the three specialties as cards."],
        ["/chat/[s]", "ChatPage + ChatWidget",
         "Streams chat turns to the API, displays answers."],
        ["/faq/[s]", "FAQPage + FAQList",
         "Lists approved auto-built FAQs for the specialty."],
        ["/admin", "AdminPage",
         "Approve / edit / reject candidates, view trending issues."],
    ]
    story.append(simple_table(rows, [3 * cm, 4 * cm, 9.5 * cm]))


def backend_section(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("3. Backend Layer", styles["SectionHeader"]))
    story.append(Paragraph(
        "FastAPI exposes three routers: <font face='Courier'>/chat</font>, "
        "<font face='Courier'>/faq</font>, and <font face='Courier'>/admin"
        "</font>. Routers are thin and delegate to a service layer "
        "(retrieval, PHI scrub, chat logger). The service layer is the only "
        "place that talks to MongoDB or Qdrant, so swapping a store later "
        "stays local.",
        styles["BodyText2"],
    ))
    story.append(backend_module_tree())
    story.append(Paragraph(
        "Fig 3. Backend module tree (FastAPI -> routers -> services).",
        styles["Caption"],
    ))
    rows = [["Endpoint", "Method", "Purpose"]] + [
        ["/health", "GET", "Liveness probe used by docker / NGINX."],
        ["/chat", "POST", "Take a user message, log it, return retrieval answer."],
        ["/faq/{specialty}", "GET", "List approved FAQs for the specialty."],
        ["/admin/candidates/{specialty}", "GET",
         "List candidate FAQs awaiting clinician review."],
        ["/admin/approve/{faq_id}", "POST", "Mark a candidate as approved."],
        ["/admin/edit/{faq_id}", "POST", "Edit a candidate's question or answer."],
        ["/admin/reject/{faq_id}", "POST", "Mark a candidate as rejected."],
    ]
    story.append(simple_table(rows, [5.5 * cm, 2 * cm, 9 * cm]))


def sequence_section(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("4. Sequence Flows", styles["SectionHeader"]))
    story.append(Paragraph(
        "Two key flows: a user chat request, and a scheduled pipeline run. "
        "Diagrams below trace each call across components.",
        styles["BodyText2"],
    ))
    story.append(sequence_chat())
    story.append(Paragraph(
        "Fig 4. Chat request flow: user types question to bot reply.",
        styles["Caption"],
    ))
    story.append(sequence_pipeline())
    story.append(Paragraph(
        "Fig 5. Pipeline flow: cron triggers fetch, encode, cluster, publish.",
        styles["Caption"],
    ))


def deployment_section(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("5. Deployment", styles["SectionHeader"]))
    story.append(Paragraph(
        "Single VM. One docker-compose file brings up Mongo, Qdrant, and "
        "Redis. The Next.js and FastAPI processes run via systemd or under "
        "Docker, depending on the operator's preference. NGINX terminates TLS "
        "and routes <font face='Courier'>/api/*</font> to FastAPI and the rest "
        "to Next.js. Celery worker plus Celery beat handle the scheduled "
        "pipeline runs.",
        styles["BodyText2"],
    ))
    story.append(deployment_diagram())
    story.append(Paragraph(
        "Fig 6. Single-VM deployment topology with ports labelled.",
        styles["Caption"],
    ))
    rows = [["Component", "Port", "Restart Policy"]] + [
        ["NGINX", "80, 443", "always (systemd)"],
        ["Next.js", "3000", "always (systemd or docker)"],
        ["FastAPI (uvicorn)", "8000", "always (systemd or docker)"],
        ["Celery worker", "(internal)", "always (docker)"],
        ["MongoDB", "27017", "unless-stopped (docker)"],
        ["Qdrant", "6333, 6334", "unless-stopped (docker)"],
        ["Redis", "6379", "unless-stopped (docker)"],
    ]
    story.append(simple_table(rows, [5 * cm, 3.5 * cm, 8 * cm]))


def trade_offs(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("6. Trade-offs and Decisions", styles["SectionHeader"]))
    for b in [
        "No LLM. Trade: simpler, traceable answers and zero hallucination risk. Cost: chatbot cannot synthesise novel answers; it can only return what is already in the index.",
        "Single VM. Trade: easy to operate by a 5-person student team. Cost: vertical scaling only.",
        "Mongo + Qdrant split. Trade: write-heavy chat logs go to Mongo, latency-sensitive search goes to Qdrant. Cost: two stores to operate.",
        "Celery scheduling instead of an event stream. Trade: simpler to reason about for a 16-week project. Cost: not real-time.",
        "Approval workflow before publishing. Trade: clinician safety. Cost: slower to surface FAQs publicly.",
    ]:
        story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{b}", styles["BulletText"]))

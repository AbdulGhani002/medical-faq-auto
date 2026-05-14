"""API reference section."""
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from docs_src.common import simple_table

from .diagrams import api_hierarchy


def api_overview(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("5. API Overview", styles["SectionHeader"]))
    story.append(Paragraph(
        "FastAPI exposes one health check plus three routers: "
        "<font face='Courier'>/chat</font>, <font face='Courier'>/faq</font>, "
        "and <font face='Courier'>/admin</font>. All responses are JSON. "
        "The Next.js frontend is the primary consumer; Swagger UI is on "
        "<font face='Courier'>/docs</font> for manual testing.",
        styles["BodyText2"],
    ))
    story.append(api_hierarchy())
    story.append(Paragraph(
        "Fig 2. API endpoint hierarchy.", styles["Caption"]
    ))


def endpoint_chat(story, styles):
    story.append(Paragraph("6. POST /chat", styles["SectionHeader"]))
    story.append(Paragraph(
        "Take a user message, log it, return the closest stored answer.",
        styles["BodyText2"],
    ))
    story.append(Paragraph("Request body", styles["SubHeader"]))
    rows = [["Field", "Type", "Required", "Notes"]] + [
        ["session_id", "string", "yes", "Client-side UUID."],
        ["specialty", "string", "yes", "One of the three specialties."],
        ["text", "string", "yes", "User message. PHI scrubbed at write time."],
    ]
    story.append(simple_table(rows, [3.5 * cm, 2.5 * cm, 2.5 * cm, 8 * cm]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("Response (200 OK)", styles["SubHeader"]))
    rows = [["Field", "Type", "Notes"]] + [
        ["answer", "string", "Selected answer from the FAQ index, or a polite fallback."],
        ["matched_faq_id", "string|null", "FAQ id when confidence is above threshold."],
        ["confidence", "float", "Cosine similarity of the top retrieval hit."],
    ]
    story.append(simple_table(rows, [3.5 * cm, 2.5 * cm, 10.5 * cm]))


def endpoint_faq(story, styles):
    story.append(Paragraph("7. GET /faq/{specialty}", styles["SectionHeader"]))
    story.append(Paragraph(
        "Return approved FAQs for the specialty, ranked by cluster size. "
        "Pagination is via the <font face='Courier'>limit</font> query param "
        "(default 50).",
        styles["BodyText2"],
    ))
    rows = [["Field", "Type", "Notes"]] + [
        ["id", "string", "Mongo _id as a hex string."],
        ["specialty", "string", "Echoed back."],
        ["question", "string", "Canonical question."],
        ["answer", "string", "Polished extractive answer."],
        ["count", "int", "Cluster size."],
        ["updated_at", "datetime (ISO)", "Last pipeline run."],
    ]
    story.append(simple_table(rows, [3.5 * cm, 3 * cm, 10 * cm]))


def endpoint_admin(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("8. Admin endpoints", styles["SectionHeader"]))
    rows = [["Endpoint", "Method", "Body", "Purpose"]] + [
        ["/admin/candidates/{specialty}", "GET", "-",
         "List candidate FAQs awaiting review."],
        ["/admin/approve/{faq_id}", "POST", "-",
         "Mark FAQ as approved (visible on public FAQ page)."],
        ["/admin/edit/{faq_id}", "POST", "{question?, answer?}",
         "Edit one or both of the FAQ fields."],
        ["/admin/reject/{faq_id}", "POST", "-",
         "Mark FAQ as rejected. Never auto-republished."],
    ]
    story.append(simple_table(rows, [5 * cm, 1.5 * cm, 3.5 * cm, 6.5 * cm]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("Error model", styles["SubHeader"]))
    rows = [["Code", "When", "Body"]] + [
        ["400", "Bad input (missing fields, bad id format)",
         "{detail: 'Invalid FAQ id'}"],
        ["404", "FAQ not found", "{detail: 'FAQ not found'}"],
        ["422", "Pydantic validation failure",
         "FastAPI default validation envelope"],
        ["500", "Service error (Mongo down)",
         "{detail: 'Internal Server Error'}"],
    ]
    story.append(simple_table(rows, [1.5 * cm, 7 * cm, 8 * cm]))


def sample_requests(story, styles):
    story.append(Paragraph("9. Sample Requests", styles["SectionHeader"]))
    story.append(Paragraph("POST /chat", styles["SubHeader"]))
    story.append(Paragraph(
        "<font face='Courier'>curl -X POST http://localhost:8000/chat "
        "-H 'Content-Type: application/json' -d '{\"session_id\":\"abc\","
        "\"specialty\":\"radiology\",\"text\":\"do i need to fast before mri?\"}'"
        "</font>",
        styles["BodyText2"],
    ))
    story.append(Paragraph("GET /faq/radiology", styles["SubHeader"]))
    story.append(Paragraph(
        "<font face='Courier'>curl http://localhost:8000/faq/radiology</font>",
        styles["BodyText2"],
    ))
    story.append(Paragraph("POST /admin/approve/{id}", styles["SubHeader"]))
    story.append(Paragraph(
        "<font face='Courier'>curl -X POST "
        "http://localhost:8000/admin/approve/65b1c2d3e4f5a6b7c8d9e0f1</font>",
        styles["BodyText2"],
    ))

"""Proposal sections 1-5: title block, summary, problem, objectives, requirements."""
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer, Table, TableStyle

from docs_src.common import LIGHT, PRIMARY, SOFT, simple_table


def title_block(story, styles):
    story.append(Paragraph(
        "Auto-Generated FAQ from Medical Chatbot Logs", styles["DocTitle"]
    ))
    story.append(Paragraph(
        "Specialties: Radiology, Physiotherapy, Cardiovascular",
        styles["Subtitle"],
    ))

    members_text = (
        "1. Abdul Ghani (F23607005) &nbsp;&nbsp;&nbsp; "
        "2. Anas Bhatti (F23607044) &nbsp;&nbsp;&nbsp; "
        "3. Muhammad Salman (F23607037)<br/>"
        "4. [Member 4 - name and roll number TBD] &nbsp;&nbsp;&nbsp; "
        "5. [Member 5 - name and roll number TBD]"
    )
    team = Table(
        [[Paragraph("<b>Group Members</b>", styles["BodyText2"]),
          Paragraph(members_text, styles["BodyText2"])]],
        colWidths=[3.5 * cm, 13 * cm],
    )
    team.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, 0), PRIMARY),
        ("BACKGROUND", (1, 0), (1, 0), SOFT),
        ("TEXTCOLOR", (0, 0), (0, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (0, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("BOX", (0, 0), (-1, -1), 0.4, LIGHT),
    ]))
    story.append(team)
    story.append(Spacer(1, 8))

    summary = [
        ["Project Type", "Semester Project, Healthcare NLP"],
        ["Team Size", "5 members"],
        ["Stack", "Next.js, FastAPI, BGE-M3, HDBSCAN, Qdrant, MongoDB"],
        ["Deliverable", "Web app with 3 chatbots + auto-FAQ page + admin dashboard"],
        ["Weightage", "Proposal and approval contribute 20% of course marks"],
    ]
    t = Table(summary, colWidths=[3.5 * cm, 13 * cm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), SOFT),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("GRID", (0, 0), (-1, -1), 0.4, LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(t)
    story.append(Spacer(1, 10))


def problem_and_objectives(story, styles):
    story.append(Paragraph("1. Problem Statement and Motivation",
                           styles["SectionHeader"]))
    story.append(Paragraph(
        "Hospitals, diagnostic centers, and rehab clinics receive the same patient "
        "questions every single day. Front-desk staff and junior doctors keep "
        "explaining scan preparation, exercise routines, recovery timelines, and "
        "medication usage again and again. The conversations are stored somewhere "
        "but almost never mined, so help sections on clinic websites stay outdated, "
        "response times stay slow, and new symptom trends are spotted late.",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "There is no straightforward system that turns this raw chat history into a "
        "clean, ranked, continuously updated knowledge base. We want to build one "
        "that works directly off a clinic's own web chatbot logs, covers three "
        "medical specialties (Radiology, Physiotherapy, Cardiovascular), and handles "
        "the Urdu and English code-switched text that local patients actually write.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("2. Project Objectives", styles["SectionHeader"]))
    for o in [
        "Build a web application that hosts three specialty chatbots and logs every conversation.",
        "Run an NLP pipeline that clusters semantically similar patient questions.",
        "Auto-generate a ranked FAQ page per specialty from those clusters.",
        "Detect emerging issues that grow fast over a short time window and alert admins.",
        "Provide an admin dashboard so clinicians can review, edit, or reject FAQs.",
        "Evaluate with quantitative clustering metrics and qualitative clinician ratings.",
    ]:
        story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{o}", styles["BulletText"]))


def tasks_and_requirements(story, styles):
    story.append(Paragraph("3. Project Tasks and Scope", styles["SectionHeader"]))
    story.append(Paragraph(
        "Eight tracks. Each has an input, output, and owner (Section 12). Tracks "
        "run partly in parallel to fit a 16-week semester.",
        styles["BodyText2"],
    ))
    tasks = [["Task", "Description"]] + [
        ["T1. Web frontend",
         "Next.js site, three specialty chat widgets, FAQ page, admin dashboard."],
        ["T2. Backend and APIs",
         "FastAPI services, MongoDB schema, chat logger, optional connectors."],
        ["T3. Conversation processing",
         "Turn segmentation, question identification, PHI scrubbing, normalisation."],
        ["T4. Embedding and clustering",
         "BGE-M3 embeddings, HDBSCAN + BERTopic, cross-channel deduplication."],
        ["T5. Answer selection and polish",
         "Extractive best-answer pick per cluster, rule-based output polish."],
        ["T6. Emerging issue detection",
         "Temporal embedding analysis, anomaly detection, in-dashboard alerts."],
        ["T7. Admin dashboard",
         "FAQ approval / edit / reject workflow, analytics, manual override, export."],
        ["T8. Evaluation and reporting",
         "Clustering metrics, clinician ratings, latency tests, final report."],
    ]
    story.append(simple_table(tasks, [3.7 * cm, 12.8 * cm]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("4. Functional Requirements", styles["SectionHeader"]))
    fr = [["ID", "Functional Requirement"]] + [
        ["FR1", "User can select one of three specialties on the landing page."],
        ["FR2", "User can chat with a specialty-specific bot in real time."],
        ["FR3", "Every chat turn is stored in MongoDB with session id and timestamp."],
        ["FR4", "Background pipeline clusters past conversations on a schedule."],
        ["FR5", "Each specialty has a public FAQ page with ranked Q and A entries."],
        ["FR6", "Admins can log in and approve, edit, reject, or pin candidate FAQs."],
        ["FR7", "System detects fast-growing clusters in a 24-hour window."],
        ["FR8", "Admins can write a manual FAQ that overrides auto-generated entries."],
        ["FR9", "Admins can export all clusters and FAQs as CSV."],
    ]
    story.append(simple_table(fr, [1.5 * cm, 15 * cm]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("5. Non-Functional Requirements", styles["SectionHeader"]))
    nfr = [["ID", "Non-Functional Requirement"]] + [
        ["NFR1", "Chatbot reply latency under 5 seconds for typical input."],
        ["NFR2", "Pipeline runs end to end on 10k conversations in under 30 minutes."],
        ["NFR3", "PHI scrubbing applied before any conversation is stored."],
        ["NFR4", "Entire stack runs from one docker-compose file."],
        ["NFR5", "Frontend renders correctly on mobile screens."],
        ["NFR6", "Multilingual embeddings (BGE-M3) for Urdu and English code-switched text."],
        ["NFR7", "Code is version-controlled in Git with unit tests for core helpers."],
        ["NFR8", "If pipeline is down, chatbot keeps working and FAQ page shows the last snapshot."],
    ]
    story.append(simple_table(nfr, [1.5 * cm, 15 * cm]))

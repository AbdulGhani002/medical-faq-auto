"""Data model section."""
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, Spacer

from docs_src.common import simple_table

from .diagrams import collection_diagram


def title(story, styles):
    story.append(Paragraph(
        "Data Model and API Reference", styles["DocTitle"]
    ))
    story.append(Paragraph(
        "Storage schema, indexes, and HTTP API for the Medical FAQ project.",
        styles["Subtitle"],
    ))


def overview(story, styles):
    story.append(Paragraph("1. Storage Overview", styles["SectionHeader"]))
    story.append(Paragraph(
        "Two stores are used. MongoDB holds chat sessions, the FAQ store, and "
        "the cluster history. Qdrant holds dense embeddings used by the "
        "retrieval service. The split keeps write-heavy chat logs on a "
        "general-purpose database and latency-sensitive search on a vector DB.",
        styles["BodyText2"],
    ))
    story.append(collection_diagram())
    story.append(Paragraph(
        "Fig 1. MongoDB collections (top) and Qdrant collection (bottom-left).",
        styles["Caption"],
    ))


def collections(story, styles):
    story.append(Paragraph("2. MongoDB Collections", styles["SectionHeader"]))

    story.append(Paragraph("2.1 chat_turns", styles["SubHeader"]))
    story.append(Paragraph(
        "Append-only log of every turn in every session, user and bot. "
        "Written by the FastAPI <font face='Courier'>/chat</font> endpoint "
        "and consumed by the pipeline ingest stage.",
        styles["BodyText2"],
    ))
    rows = [["Field", "Type", "Notes"]] + [
        ["_id", "ObjectId", "Mongo auto-id."],
        ["session_id", "string", "Client-side UUID, groups one user conversation."],
        ["specialty", "string", "One of: radiology, physiotherapy, cardiovascular."],
        ["role", "string", "user or bot."],
        ["text", "string", "Already PHI-scrubbed at write time."],
        ["timestamp", "datetime", "UTC. Indexed for ingest queries."],
    ]
    story.append(simple_table(rows, [3 * cm, 2.5 * cm, 11 * cm]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.2 faqs", styles["SubHeader"]))
    story.append(Paragraph(
        "One document per cluster. Pipeline upserts on (specialty, cluster_id). "
        "Admin dashboard flips <font face='Courier'>approved</font> to true. "
        "Public FAQ endpoint reads only approved entries.",
        styles["BodyText2"],
    ))
    rows = [["Field", "Type", "Notes"]] + [
        ["_id", "ObjectId", "Mongo auto-id."],
        ["specialty", "string", "Specialty tag."],
        ["cluster_id", "int", "Stable id from HDBSCAN result."],
        ["question", "string", "Canonical question (closest to cluster centroid)."],
        ["answer", "string", "Extractively selected agent reply, polished."],
        ["count", "int", "Cluster size at publish time."],
        ["approved", "bool", "Clinician approval flag. Defaults false."],
        ["rejected", "bool", "Set true if a clinician rejected this candidate."],
        ["updated_at", "datetime", "Last pipeline run that touched this row."],
    ]
    story.append(simple_table(rows, [3 * cm, 2.5 * cm, 11 * cm]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("2.3 clusters", styles["SubHeader"]))
    story.append(Paragraph(
        "Tracks size over time per cluster so the emerging-issue detector can "
        "spot fast growth. Written at the end of the cluster stage.",
        styles["BodyText2"],
    ))
    rows = [["Field", "Type", "Notes"]] + [
        ["cluster_id", "int", "Stable id."],
        ["specialty", "string", "Specialty tag."],
        ["first_seen", "datetime", "First time this cluster appeared."],
        ["last_seen", "datetime", "Most recent pipeline run that produced it."],
        ["size_history", "list", "Daily sizes for the trailing 14 days."],
    ]
    story.append(simple_table(rows, [3 * cm, 2.5 * cm, 11 * cm]))


def qdrant_section(story, styles):
    story.append(Paragraph("3. Qdrant Collection", styles["SectionHeader"]))
    story.append(Paragraph(
        "One collection per specialty: <font face='Courier'>faqs_radiology"
        "</font>, <font face='Courier'>faqs_physiotherapy</font>, "
        "<font face='Courier'>faqs_cardiovascular</font>. Vector dimension is "
        "1024 (BGE-M3). Distance is cosine, with vectors normalised at write "
        "time so dot-product is enough at query time.",
        styles["BodyText2"],
    ))
    rows = [["Setting", "Value"]] + [
        ["Vector dimension", "1024"],
        ["Distance", "Cosine"],
        ["Quantization", "Off for the prototype, scalar later if needed."],
        ["Payload schema", "faq_id, specialty, question, answer"],
        ["Write path", "Pipeline publish stage. Upserts one point per FAQ."],
        ["Read path", "FastAPI retrieval service on /chat."],
    ]
    story.append(simple_table(rows, [4.5 * cm, 12 * cm]))


def indexes(story, styles):
    story.append(Paragraph("4. Indexes", styles["SectionHeader"]))
    rows = [["Collection", "Index", "Reason"]] + [
        ["chat_turns", "(specialty, timestamp)",
         "Pipeline ingest pulls new turns by time, filtered by specialty."],
        ["chat_turns", "session_id",
         "Group turns into sessions inside the ingest stage."],
        ["faqs", "(specialty, approved)",
         "Public FAQ endpoint reads only approved rows per specialty."],
        ["faqs", "(specialty, cluster_id)",
         "Pipeline upsert key. Unique."],
        ["clusters", "(specialty, last_seen)",
         "Emerging-issue detector scans recent clusters."],
    ]
    story.append(simple_table(rows, [3 * cm, 5 * cm, 8.5 * cm]))

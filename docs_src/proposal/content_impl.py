"""Proposal sections 10-12: NLP techniques, libraries, task split."""
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer, TableStyle

from docs_src.common import simple_table


def nlp_section(story, styles):
    story.append(Paragraph("10. NLP Techniques Used", styles["SectionHeader"]))
    for b in [
        "Conversation segmentation with turn-level question identification using a small fine-tuned classifier.",
        "Intent extraction and question normalisation (paraphrase resolution) using rule-based plus embedding similarity.",
        "Semantic retrieval for the chatbot: dense nearest-neighbour search over the FAQ index (no LLM in the loop).",
        "Semantic clustering with multilingual sentence embeddings (BGE-M3, E5-multilingual).",
        "Density-based clustering with HDBSCAN; topic labels via BERTopic.",
        "Extractive answer selection per cluster: rank existing agent replies by centroid similarity, length, and recency.",
        "Rule-based output polishing: whitespace, punctuation, length trimming, greeting and closing templates.",
        "Temporal embedding analysis for emerging-issue detection (rising clusters over a sliding window).",
        "Cross-channel deduplication (same issue logged across web chat and WhatsApp).",
        "PHI scrubbing with regex plus a small NER model before any storage of training-eligible text.",
    ]:
        story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{b}", styles["BulletText"]))


def tools_section(story, styles):
    story.append(Paragraph("11. Libraries, Tools, and IDE", styles["SectionHeader"]))
    rows = [["Category", "Choice"]] + [
        ["IDE", "VS Code (primary), Jupyter for ML experiments, DataGrip for Mongo browsing"],
        ["Languages", "Python 3.11 for backend and ML, TypeScript for frontend"],
        ["Frontend", "Next.js 15, React 19, Tailwind CSS, shadcn/ui, Zustand"],
        ["Backend", "FastAPI, Uvicorn, Pydantic v2"],
        ["Background jobs", "Celery + Redis broker, Celery beat for scheduling"],
        ["Databases", "MongoDB (chat sessions, FAQ store), Postgres (analytics, optional)"],
        ["Vector DB", "Qdrant in Docker, Weaviate as a fallback"],
        ["Embeddings", "sentence-transformers, BAAI/bge-m3, intfloat/e5-multilingual"],
        ["Clustering", "scikit-learn (KMeans baseline), HDBSCAN, BERTopic, UMAP"],
        ["Retrieval / IR", "FAISS or Qdrant for dense kNN, rank_bm25 as a sparse baseline"],
        ["Extractive selection", "Custom Python scorer (centroid similarity + length + recency), MMR for diversity"],
        ["Text polish", "Pure Python rule-based cleaners (regex, NLTK sentence splitter, custom templates)"],
        ["NLP utilities", "spaCy (English), Indic-NLP, ftfy, langdetect, regex"],
        ["Evaluation", "Hugging Face evaluate, custom Python scripts, scikit-learn metrics"],
        ["Versioning", "Git + GitHub, conventional commits, pull requests"],
        ["Containers", "Docker, Docker Compose"],
        ["Hosting", "VPS (Hetzner or DigitalOcean), NGINX reverse proxy, systemd"],
        ["Project management", "GitHub Projects (Kanban), Notion for notes, Discord for daily sync"],
    ]
    t = simple_table(rows, [4 * cm, 12.5 * cm], extra_styles=[
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ])
    story.append(t)
    story.append(PageBreak())


def task_split_section(story, styles):
    story.append(Paragraph("12. Task Split (5 Members)", styles["SectionHeader"]))
    story.append(Paragraph(
        "Eight project tracks bundled into five ownership areas, one per member. "
        "Members meet at the boundaries (API contracts, data schemas, evaluation "
        "hooks). Each row maps one member to one focused area.",
        styles["BodyText2"],
    ))
    rows = [
        ["#", "Member", "Focus Area", "Concrete Responsibilities"],
        ["1", "Abdul Ghani\n(F23607005)", "Frontend and UI",
         "Next.js site, three specialty chat widgets, FAQ page layout, admin UI."],
        ["2", "Anas Bhatti\n(F23607044)", "Conversation Processing",
         "Turn segmentation, question identification, intent normalisation, PHI scrubbing."],
        ["3", "Muhammad Salman\n(F23607037)", "Embedding and Clustering",
         "Embedding pipeline (BGE-M3), HDBSCAN with BERTopic, cross-channel deduplication."],
        ["4", "[Member 4]\n([Roll No 4])", "Backend, APIs, Data",
         "FastAPI services, MongoDB schema, chat logger, optional ingest connectors."],
        ["5", "[Member 5]\n([Roll No 5])", "Selection, Issues, Eval",
         "Extractive selection, rule-based polish, emerging-issue detection, evaluation, report."],
    ]
    t = simple_table(rows, [0.7 * cm, 3 * cm, 3.5 * cm, 9.3 * cm], extra_styles=[
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 1), (2, -1), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (1, 0), (1, -1), "CENTER"),
    ])
    story.append(t)
    story.append(Spacer(1, 8))

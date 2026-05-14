"""Proposal sections 6-9: datasets, web overview, architecture, pipeline."""
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from docs_src.common import simple_table

from .diagrams import architecture_diagram, pipeline_diagram, webapp_flow_diagram


def datasets_section(story, styles):
    story.append(Paragraph("6. Datasets", styles["SectionHeader"]))
    story.append(Paragraph(
        "We mix public medical Q and A datasets, general dialogue corpora for "
        "turn-segmentation training, template-built synthetic conversations "
        "(no LLM, just parameterised patterns), and a small set of anonymised "
        "logs from one or two partner clinics if consent is arranged.",
        styles["BodyText2"],
    ))
    ds = [["Dataset", "Size", "Use in Project"]] + [
        ["MedDialog (English)", "approx. 250k dialogues",
         "Training and evaluation of question clustering."],
        ["HealthCareMagic-100k", "100k Q/A pairs",
         "Bootstrap answer pool for retrieval index and clustering evaluation."],
        ["iCliniq-10k", "10k Q/A pairs",
         "Held-out evaluation set, especially cardiovascular."],
        ["MTSamples", "approx. 5k clinical notes",
         "Medical vocabulary and abbreviation reference for normalisation."],
        ["Customer Support on Twitter", "approx. 2.8M tweets",
         "General support dialogue structure for the segmenter."],
        ["Ubuntu Dialogue Corpus", "approx. 1M dialogues",
         "Conversation turn segmentation training."],
        ["Template-built specialty Q/A", "approx. 3k per specialty",
         "Cold-start corpus built from parameterised templates (no LLM)."],
        ["Partner clinic anonymised logs", "approx. 1k each (target)",
         "Pilot validation and Urdu / English code-switched samples."],
    ]
    story.append(simple_table(ds, [5.3 * cm, 3.5 * cm, 7.7 * cm]))
    story.append(Spacer(1, 8))


def web_app_section(story, styles):
    story.append(Paragraph("7. Web Application Overview", styles["SectionHeader"]))
    story.append(Paragraph(
        "The product is a single web application with three working surfaces. "
        "(1) A public landing page lets a patient pick a specialty and chat with "
        "the matching bot. The bot is fully retrieval-based: it embeds the user's "
        "question and returns the closest stored answer from a curated FAQ index. "
        "No generative model is used. The index is bootstrapped from public "
        "medical Q and A datasets and enriched over time by our clustering "
        "pipeline. Every turn is stored in MongoDB along with session metadata. "
        "(2) A public FAQ page for each specialty lists the auto-built questions "
        "and answers, refreshed as new clusters form. (3) An admin dashboard lets "
        "clinicians approve, edit, or reject candidate FAQs before they go public.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 4))
    story.append(webapp_flow_diagram())
    story.append(Paragraph(
        "Fig 1. End-to-end user flow from chat to published FAQ.",
        styles["Caption"],
    ))
    story.append(PageBreak())


def architecture_section(story, styles):
    story.append(Paragraph("8. System Architecture", styles["SectionHeader"]))
    story.append(Paragraph(
        "The system has five layers. Users hit a Next.js frontend that serves "
        "both the chatbot widgets and the public FAQ page. A FastAPI gateway "
        "routes traffic to two core services: the retrieval service (semantic "
        "search over the FAQ index, no LLM) and the FAQ service (clustering "
        "pipeline). MongoDB stores chat sessions, Qdrant holds embeddings, and "
        "a separate FAQ store keeps the curated knowledge base plus analytics. "
        "Each layer is independently deployable from one docker-compose file.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 4))
    story.append(architecture_diagram())
    story.append(Paragraph(
        "Fig 2. Five-layer architecture of the chatbot plus FAQ generator.",
        styles["Caption"],
    ))


def pipeline_section(story, styles):
    story.append(Paragraph("9. Tentative Pipeline", styles["SectionHeader"]))
    story.append(Paragraph(
        "Logged chats flow through eight stages. Stages 1 to 4 prepare and embed "
        "the data, stages 5 to 7 cluster and synthesise, and stage 8 publishes. "
        "The pipeline runs on a schedule (default hourly via Celery beat) and can "
        "be triggered on demand from the admin dashboard.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 4))
    story.append(pipeline_diagram())
    story.append(Paragraph(
        "Fig 3. Eight-stage FAQ generation pipeline.", styles["Caption"]
    ))

    story.append(Paragraph("Step-by-step details", styles["SubHeader"]))
    for title, desc in [
        ("Step 1: Ingest",
         "Pull new chat sessions from MongoDB. Each session has a turn list "
         "and a specialty tag. Optionally also load partner-clinic export files."),
        ("Step 2: Segment",
         "Split each session into single turns and classify each user turn as "
         "question, follow-up, or non-question."),
        ("Step 3: Normalise",
         "Strip names, phone numbers, IDs, and dates (PHI). Lower-case, fix "
         "typos with ftfy, language-tag using langdetect."),
        ("Step 4: Embed",
         "Encode each candidate question with BGE-M3 (multilingual). Store the "
         "embedding plus metadata in Qdrant."),
        ("Step 5: Cluster",
         "Run HDBSCAN on the embeddings to get density-based clusters. BERTopic "
         "gives topic labels for each cluster."),
        ("Step 6: Select",
         "For each cluster, pick the highest-scoring existing agent reply by "
         "centroid similarity, length, and recency. Fully extractive, no LLM."),
        ("Step 7: Polish",
         "Apply rule-based clean-up: normalise whitespace, fix punctuation, "
         "trim to a maximum sentence count."),
        ("Step 8: Publish",
         "Rank clusters by frequency, recency, and severity. Push the top N "
         "to the public FAQ page. Mark sudden-growth clusters as emerging issues."),
    ]:
        story.append(Paragraph(f"<b>{title}.</b> {desc}", styles["BulletText"]))
    story.append(PageBreak())

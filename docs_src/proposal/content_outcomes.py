"""Proposal sections 13-18: results, value, evaluation, timeline, academic value, refs."""
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from docs_src.common import simple_table


def results_section(story, styles):
    story.append(Paragraph("13. Expected Results", styles["SectionHeader"]))
    for r in [
        "Live demo URL hosting three specialty chatbots and three FAQ pages.",
        "At least 5,000 synthetic conversations and 1,000 or more real conversations processed end to end.",
        "FAQ page with at least 30 high-quality ranked Q and A entries per specialty.",
        "Clustering quality: silhouette score above 0.45, manual cluster purity above 80% on a 100-cluster sample.",
        "Answer quality: 70% of generated answers rated useful as-is by a clinician on a 50-FAQ sample.",
        "Pipeline runtime: full run on 10k chats under 30 minutes on a 4-core 8GB VM.",
        "Emerging-issue detection that surfaces at least three trending clusters in a two-week pilot.",
        "Final project report (12 to 20 pages), recorded demo video, and open-source repository.",
    ]:
        story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{r}", styles["BulletText"]))


def value_section(story, styles):
    story.append(Paragraph("14. Value Addition by Our Work", styles["SectionHeader"]))
    for v in [
        "LLM-free design. The whole system uses classical NLP plus sentence embeddings only. Every answer the user sees is a real, human-written agent reply. This avoids hallucination risk in a medical setting and keeps every output traceable.",
        "Cross-specialty pipeline. Our pipeline handles three specialties from one codebase, so it generalises.",
        "Code-switched language support. Patients in Pakistan often mix Urdu and English. BGE-M3 supports this at the embedding layer.",
        "Continuous and incremental. The FAQ regenerates as new chats arrive, instead of being a one-shot batch job.",
        "Clinician-in-the-loop. A review-and-approve workflow rather than a black-box auto-publish, since medical content needs a human check.",
        "Emerging-issue detection. Beyond static FAQs, our system flags rising clusters as early-warning signals.",
        "Local hosting friendly. The full stack runs on a single 4-core 8GB VM, so small clinics and university labs can self-host without cloud costs.",
        "Open dataset potential. With partner consent, we can release a clustered anonymised medical FAQ dataset for follow-up research.",
    ]:
        story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{v}", styles["BulletText"]))


def evaluation_section(story, styles):
    story.append(Paragraph("15. Evaluation Plan", styles["SectionHeader"]))
    story.append(Paragraph(
        "Evaluation uses both intrinsic (cluster quality) and extrinsic (FAQ "
        "usefulness) metrics, plus a small user study if a partner clinic agrees.",
        styles["BodyText2"],
    ))
    for e in [
        "Clustering: silhouette coefficient, Davies-Bouldin index, manual cluster purity on a 100-cluster sample.",
        "Question normalisation: pairwise accuracy on 500 hand-labelled paraphrase pairs.",
        "Answer quality: three graders rate 50 FAQ entries on correctness, tone, completeness (5-point scale).",
        "Cross-specialty consistency: pipeline run separately on each specialty must give comparable cluster quality.",
        "Latency: chatbot response time and pipeline run time measured under 4-core VM load.",
        "Emerging-issue detection: simulate a spike, measure time-to-alert and false-positive rate.",
        "User study (optional): ten patients try the bot and rate the experience.",
    ]:
        story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{e}", styles["BulletText"]))
    story.append(PageBreak())


def timeline_section(story, styles):
    story.append(Paragraph(
        "16. Project Timeline (16-week semester)", styles["SectionHeader"]
    ))
    rows = [["Weeks", "Phase", "Key Deliverables"]] + [
        ["1-2", "Proposal and approval",
         "Approved proposal, GitHub repo, project skeleton, dataset download."],
        ["3-4", "Frontend skeleton",
         "Landing page, three chatbot widgets (placeholder replies), empty FAQ page."],
        ["4-6", "Backend and logging",
         "FastAPI service, MongoDB schema, chat logger, retrieval returning real answers."],
        ["6-8", "Data preprocessing",
         "Dataset loaders, PHI scrub, conversation segmentation, normalisation."],
        ["8-10", "Embedding and clustering",
         "Pipeline running on 5k chats, first cluster output, BERTopic labels."],
        ["10-12", "Selection and polish",
         "Auto-built FAQs (extractive plus rule-based polish) on the public FAQ page."],
        ["12-13", "Emerging-issue detection",
         "Trending-cluster alerts and admin notifications in the dashboard."],
        ["13-14", "Pilot data collection",
         "Optional pilot with a partner clinic, real conversation ingest."],
        ["14-15", "Evaluation",
         "Compute metrics, clinician rating session, latency tests."],
        ["15-16", "Report and demo",
         "Final report, recorded demo video, presentation, GitHub release."],
    ]
    t = simple_table(rows, [1.6 * cm, 4 * cm, 10.9 * cm], extra_styles=[
        ("FONTNAME", (1, 1), (1, -1), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (1, -1), "CENTER"),
    ])
    story.append(t)
    story.append(Spacer(1, 8))


def closing_section(story, styles):
    story.append(Paragraph("17. Academic Value", styles["SectionHeader"]))
    story.append(Paragraph(
        "The project covers the classical NLP stack: text preprocessing, "
        "sentence embeddings, dense retrieval, unsupervised clustering, extractive "
        "selection, rule-based polishing, and temporal anomaly detection. By "
        "avoiding LLMs entirely, the work stays inside well-understood NLP "
        "territory and every output is traceable to a real human-written answer. "
        "The final deliverable is a working web system that can be demonstrated "
        "live and evaluated end to end.",
        styles["BodyText2"],
    ))

    story.append(Paragraph("18. References (Tentative)", styles["SectionHeader"]))
    refs = [
        "Chen Z. et al., MedDialog: Large-scale Medical Dialogue Datasets, EMNLP 2020.",
        "Reimers N., Gurevych I., Sentence-BERT, EMNLP 2019.",
        "Xiao S. et al., BGE M3-Embedding, 2024.",
        "McInnes L., Healy J., HDBSCAN, JOSS 2017.",
        "Grootendorst M., BERTopic, 2022.",
        "Erkan G., Radev D., LexRank, JAIR 2004.",
        "Robertson S., Zaragoza H., BM25 and Beyond, FnTIR 2009.",
        "Li J. et al., A Survey on Medical Question Answering Systems, ACM CS 2023.",
    ]
    for i, r in enumerate(refs, 1):
        story.append(Paragraph(f"[{i}] {r}", styles["BulletText"]))

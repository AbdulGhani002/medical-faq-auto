"""Pipeline document content sections."""
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from docs_src.common import simple_table
from docs_src.proposal.diagrams import pipeline_diagram

from .perf_charts import (
    cluster_count_over_time_line, latency_per_request_bar,
    runtime_breakdown_pie, silhouette_targets_bar, stage_throughput_bar,
)
from .stage_diagrams import (
    cluster_visualisation_mock,
    stage_cluster, stage_embed, stage_ingest, stage_normalize,
    stage_polish, stage_publish, stage_segment, stage_select,
)


def title(story, styles):
    story.append(Paragraph(
        "FAQ Generation Pipeline", styles["DocTitle"]
    ))
    story.append(Paragraph(
        "Stage-by-stage design document for the medical FAQ pipeline.",
        styles["Subtitle"],
    ))


def overview(story, styles):
    story.append(Paragraph("1. Overview", styles["SectionHeader"]))
    story.append(Paragraph(
        "Eight stages, all extractive and rule-based. No LLM is invoked at "
        "any point. The pipeline pulls chat sessions from MongoDB, prepares "
        "and embeds the questions, clusters them, picks a canonical answer "
        "from real agent replies, polishes the wording, and writes the FAQ "
        "back to MongoDB for clinician review.",
        styles["BodyText2"],
    ))
    story.append(pipeline_diagram())
    story.append(Paragraph("Fig 1. End-to-end pipeline.", styles["Caption"]))


def stages_part_one(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("2. Stages 1 to 4 - Preparation",
                           styles["SectionHeader"]))
    for fn, header, body in [
        (stage_ingest, "Stage 1: Ingest",
         "Pulls every session from MongoDB written since the last run. Groups "
         "turns by session_id. Optionally loads partner-clinic export files."),
        (stage_segment, "Stage 2: Segment",
         "Detects user questions (punctuation, question starter words, "
         "including Urdu-roman starters). Pairs each question with the bot "
         "reply that followed it; that pairing becomes the candidate answer."),
        (stage_normalize, "Stage 3: Normalize",
         "Strips PHI (IDs, phone numbers, emails, dates). Fixes encoding "
         "issues with ftfy. Lower-cases and squashes whitespace."),
        (stage_embed, "Stage 4: Embed",
         "Encodes each clean question with BGE-M3, normalised vectors. "
         "Result is an (n, d) NumPy matrix aligned with the turn list."),
    ]:
        story.append(Paragraph(header, styles["SubHeader"]))
        story.append(Paragraph(body, styles["BodyText2"]))
        story.append(fn())
        story.append(Spacer(1, 4))


def stages_part_two(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("3. Stages 5 to 8 - Selection and Publish",
                           styles["SectionHeader"]))
    for fn, header, body in [
        (stage_cluster, "Stage 5: Cluster",
         "HDBSCAN with min_cluster_size=5 on euclidean-normalised vectors. "
         "Noise points (label -1) are dropped. BERTopic provides a topic "
         "label per cluster for the admin dashboard."),
        (stage_select, "Stage 6: Select",
         "Extractive. For each cluster, rank candidate agent replies by "
         "centroid similarity, length, and recency. Pick the top one as the "
         "canonical answer. Fall back to the longest non-empty reply if the "
         "top scoring reply is empty."),
        (stage_polish, "Stage 7: Polish",
         "Rule-based clean-up only. Normalise whitespace, fix punctuation, "
         "trim to a configured maximum sentence count, optional greeting and "
         "closing prefix."),
        (stage_publish, "Stage 8: Publish",
         "Upserts each FAQ to mongo.faqs keyed on (specialty, cluster_id) "
         "with approved=false. Admin dashboard reviews and approves."),
    ]:
        story.append(Paragraph(header, styles["SubHeader"]))
        story.append(Paragraph(body, styles["BodyText2"]))
        story.append(fn())
        story.append(Spacer(1, 4))


def cluster_view(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("4. Cluster Visualisation", styles["SectionHeader"]))
    story.append(Paragraph(
        "After Stage 4 the embeddings sit in a 1024-dimensional space. For "
        "the admin dashboard and reports, we project them to two dimensions "
        "with UMAP. Each cluster shows up as a coloured blob. Noise points "
        "are dropped before the projection.",
        styles["BodyText2"],
    ))
    story.append(cluster_visualisation_mock())
    story.append(Paragraph(
        "Fig 10. 2D UMAP projection of the embedding space (mock data).",
        styles["Caption"],
    ))


def scheduling_section(story, styles):
    story.append(Paragraph("5. Scheduling and Re-runs", styles["SectionHeader"]))
    story.append(Paragraph(
        "Celery beat triggers the runner every hour by default. The runner "
        "can also be invoked manually from the admin dashboard or the CLI:",
        styles["BodyText2"],
    ))
    story.append(Paragraph(
        "&nbsp;&nbsp;<font face='Courier'>python -m pipeline.runner --once</font><br/>"
        "&nbsp;&nbsp;<font face='Courier'>python -m pipeline.runner --once --specialty radiology</font>",
        styles["BodyText2"],
    ))
    rows = [["Schedule", "Trigger", "Scope"]] + [
        ["Hourly", "Celery beat", "All specialties, incremental."],
        ["On demand", "Admin button", "One specialty, full re-cluster."],
        ["Nightly (option)", "cron job", "Full re-cluster, drop noise."],
    ]
    story.append(simple_table(rows, [3.5 * cm, 4 * cm, 9 * cm]))


def performance_section(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("6. Performance Targets", styles["SectionHeader"]))
    story.append(Paragraph(
        "Targets below are what we plan to hit on a 4 vCPU 8GB VM with 10,000 "
        "logged chats. Embedding dominates wall-clock time because it is the "
        "only stage that runs a neural model.",
        styles["BodyText2"],
    ))
    story.append(runtime_breakdown_pie())
    story.append(Paragraph(
        "Fig 11. Time spent per stage on a 10k-chat run (target).",
        styles["Caption"],
    ))
    story.append(stage_throughput_bar())
    story.append(Paragraph(
        "Fig 12. Per-stage throughput target (items/sec).",
        styles["Caption"],
    ))
    story.append(latency_per_request_bar())
    story.append(Paragraph(
        "Fig 13. API latency target (p95, ms).", styles["Caption"]
    ))


def quality_section(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("7. Quality Targets", styles["SectionHeader"]))
    story.append(Paragraph(
        "Quality is measured at two places: cluster quality (intrinsic) and "
        "answer usefulness (extrinsic). Targets below are what we plan to "
        "report in the final paper.",
        styles["BodyText2"],
    ))
    story.append(silhouette_targets_bar())
    story.append(Paragraph(
        "Fig 14. Silhouette coefficient target per specialty.",
        styles["Caption"],
    ))
    story.append(cluster_count_over_time_line())
    story.append(Paragraph(
        "Fig 15. Cluster count growth as chats are ingested (target curve).",
        styles["Caption"],
    ))

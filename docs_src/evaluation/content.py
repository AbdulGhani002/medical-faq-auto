"""Evaluation methodology document content."""
from reportlab.lib.units import cm
from reportlab.platypus import PageBreak, Paragraph, Spacer

from docs_src.common import simple_table

from .charts import (
    clinician_ratings_pie, cluster_size_distribution_bar,
    latency_vs_load_line, metric_targets_bar, silhouette_progression_line,
)


def title(story, styles):
    story.append(Paragraph(
        "Evaluation Methodology", styles["DocTitle"]
    ))
    story.append(Paragraph(
        "How we will measure clustering, retrieval, answer quality, and latency.",
        styles["Subtitle"],
    ))


def goals(story, styles):
    story.append(Paragraph("1. Evaluation Goals", styles["SectionHeader"]))
    story.append(Paragraph(
        "Three questions decide whether the project is a success. (a) Do the "
        "clusters group semantically similar questions together? (b) Does the "
        "retrieval-based chatbot return useful answers? (c) Does the pipeline "
        "finish on time on a modest VM? Each question maps to a measurable "
        "metric so the final report can give numbers, not opinions.",
        styles["BodyText2"],
    ))
    rows = [["Goal", "Metric", "Target"]] + [
        ["Cluster quality", "Silhouette coefficient", "above 0.45"],
        ["Cluster purity", "Manual labeling, 100 clusters", "above 80%"],
        ["Paraphrase detection", "Pairwise accuracy, 500 pairs", "above 75%"],
        ["Retrieval relevance", "MRR@5 on labelled hold-out", "above 0.60"],
        ["Answer usefulness", "Clinician 5-point rating", "70% rated useful"],
        ["Pipeline runtime", "Wall clock on 10k chats", "under 30 minutes"],
        ["Chat latency (p95)", "Concurrent load test", "under 400 ms"],
    ]
    story.append(simple_table(rows, [4.5 * cm, 5 * cm, 7 * cm]))


def chart_summary(story, styles):
    story.append(metric_targets_bar())
    story.append(Paragraph(
        "Fig 1. Key evaluation targets, normalised to a 0 to 1 scale.",
        styles["Caption"],
    ))


def cluster_eval(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("2. Cluster Quality", styles["SectionHeader"]))
    story.append(Paragraph(
        "Intrinsic metrics on the embedding-space clusters tell us if the "
        "pipeline is grouping like with like, even before any human reads the "
        "FAQs. We report silhouette (higher better), Davies-Bouldin (lower "
        "better), and human-labelled purity on a sample of 100 clusters.",
        styles["BodyText2"],
    ))
    story.append(silhouette_progression_line())
    story.append(Paragraph(
        "Fig 2. Silhouette score expected to climb as the corpus grows.",
        styles["Caption"],
    ))
    story.append(cluster_size_distribution_bar())
    story.append(Paragraph(
        "Fig 3. Expected cluster-size distribution across all three specialties.",
        styles["Caption"],
    ))


def answer_quality(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("3. Answer Quality (Extrinsic)",
                           styles["SectionHeader"]))
    story.append(Paragraph(
        "A real clinician (and ideally three) rate 50 auto-built FAQs on "
        "factual correctness, tone, and completeness. We use a 5-point scale "
        "and report inter-rater agreement (Cohen's kappa). The headline "
        "number is the share of FAQs rated 4 or 5 on correctness.",
        styles["BodyText2"],
    ))
    story.append(clinician_ratings_pie())
    story.append(Paragraph(
        "Fig 4. Target distribution of clinician ratings on 50 FAQs.",
        styles["Caption"],
    ))
    rows = [["Rating", "Meaning", "Action"]] + [
        ["5", "Correct, complete, friendly tone", "Approve as-is."],
        ["4", "Correct but minor edit needed", "Approve after edit."],
        ["3", "Mostly correct, needs rework", "Send back to pipeline."],
        ["2", "Partly wrong or unsafe", "Reject."],
        ["1", "Wrong or harmful", "Reject, mark cluster for review."],
    ]
    story.append(simple_table(rows, [1.5 * cm, 7 * cm, 8 * cm]))


def latency_eval(story, styles):
    story.append(PageBreak())
    story.append(Paragraph("4. Latency and Throughput",
                           styles["SectionHeader"]))
    story.append(Paragraph(
        "We load-test the chat endpoint with a small Python script that opens "
        "N concurrent sessions and times each round-trip. The retrieval "
        "service is the only hot path. Mongo writes are async and not on the "
        "critical path.",
        styles["BodyText2"],
    ))
    story.append(latency_vs_load_line())
    story.append(Paragraph(
        "Fig 5. Chat latency vs concurrent requests (target).",
        styles["Caption"],
    ))
    rows = [["Load", "p50 target", "p95 target"]] + [
        ["10 concurrent", "60 ms", "120 ms"],
        ["100 concurrent", "90 ms", "200 ms"],
        ["500 concurrent", "180 ms", "400 ms"],
        ["1000 concurrent", "350 ms", "700 ms"],
    ]
    story.append(simple_table(rows, [3.5 * cm, 4 * cm, 4 * cm]))


def emerging_eval(story, styles):
    story.append(Paragraph("5. Emerging-Issue Detection",
                           styles["SectionHeader"]))
    story.append(Paragraph(
        "To test the anomaly detector we simulate a synthetic spike: 80 fresh "
        "questions arrive in 12 hours for one cluster that had a baseline of "
        "5 questions/day. We measure how many hours it takes for the alert "
        "to fire and whether we get false alerts on unrelated clusters.",
        styles["BodyText2"],
    ))
    rows = [["Metric", "Target"]] + [
        ["Time to alert (true spike)", "under 6 hours"],
        ["False positives per week per specialty", "fewer than 1"],
        ["Recall on injected spikes", "above 90%"],
    ]
    story.append(simple_table(rows, [7 * cm, 8 * cm]))


def reporting(story, styles):
    story.append(Paragraph("6. Reporting and Reproducibility",
                           styles["SectionHeader"]))
    for b in [
        "All metrics are computed by a single CLI: python -m evaluation.run.",
        "Each run writes a timestamped JSON to docs/evaluation_runs/ so results are diff-able.",
        "Charts in this document are regenerated from the same JSON.",
        "Final project report includes the latest JSON tables alongside these charts.",
        "Manual cluster purity labels are kept in data/eval_labels/ for re-use.",
    ]:
        story.append(Paragraph(f"&#8226;&nbsp;&nbsp;{b}", styles["BulletText"]))

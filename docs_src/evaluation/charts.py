"""Evaluation charts (mock targets, replaced with real numbers later)."""
from docs_src.common import bar_chart, horizontal_bar_chart, line_chart, pie_chart


def metric_targets_bar():
    return bar_chart(
        values=[0.48, 0.82, 0.74, 0.70, 0.75],
        categories=["Silhouette", "Purity", "Paraphr Acc",
                    "Answer 'Useful'", "Time-to-alert"],
        title="Key evaluation targets (normalised 0-1)",
        y_label="score",
        value_min=0, value_max=1.0,
    )


def clinician_ratings_pie():
    return pie_chart(
        values=[35, 11, 4],
        labels=["Useful as-is (target 70%)",
                "Useful with edits (target 22%)",
                "Reject (target 8%)"],
        title="Clinician answer-quality rating split (target on 50 FAQs)",
    )


def cluster_size_distribution_bar():
    return horizontal_bar_chart(
        values=[5, 12, 18, 22, 14, 9, 6, 4],
        categories=["5-10", "11-20", "21-30", "31-50",
                    "51-80", "81-120", "121-200", "200+"],
        title="Expected cluster-size distribution (cluster count per bucket)",
        value_max=30,
    )


def silhouette_progression_line():
    return line_chart(
        series=[
            [0.32, 0.38, 0.42, 0.45, 0.47, 0.48],  # Radiology
            [0.30, 0.36, 0.40, 0.44, 0.48, 0.52],  # Physiotherapy
            [0.28, 0.34, 0.39, 0.42, 0.45, 0.46],  # Cardiovascular
        ],
        categories=["1k", "2k", "4k", "6k", "8k", "10k"],
        names=["Radiology", "Physiotherapy", "Cardiovascular"],
        title="Silhouette score vs corpus size (target progression)",
        y_max=0.7,
    )


def latency_vs_load_line():
    return line_chart(
        series=[
            [80, 95, 110, 130, 160, 210, 290, 410],
            [70, 75, 80, 90, 105, 120, 145, 180],
        ],
        categories=["10", "20", "50", "100", "200", "500", "1000", "2000"],
        names=["/chat (cold model)", "/chat (warm)"],
        title="Chat latency vs concurrent requests (ms, target)",
        y_max=500,
    )

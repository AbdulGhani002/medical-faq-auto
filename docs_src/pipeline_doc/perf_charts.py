"""Performance charts for the pipeline document (mock data based on targets)."""
from docs_src.common import bar_chart, horizontal_bar_chart, line_chart, pie_chart


def runtime_breakdown_pie():
    """Time spent per stage in a typical 10k-chat run (target distribution)."""
    return pie_chart(
        values=[40, 65, 30, 380, 180, 60, 25, 20],
        labels=[
            "Ingest", "Segment", "Normalize", "Embed",
            "Cluster", "Select", "Polish", "Publish",
        ],
        title="Pipeline runtime breakdown (seconds, on 10k chats)",
    )


def stage_throughput_bar():
    """Approximate throughput per stage in items/second."""
    return bar_chart(
        values=[5000, 2200, 4500, 35, 800, 1500, 9000, 1200],
        categories=[
            "Ingest", "Segment", "Normaliz", "Embed",
            "Cluster", "Select", "Polish", "Publish",
        ],
        title="Stage throughput target (items per second)",
        y_label="items/sec",
        value_min=0,
    )


def latency_per_request_bar():
    """Per-endpoint latency targets in milliseconds."""
    return horizontal_bar_chart(
        values=[120, 320, 80, 45],
        categories=["/chat (warm)", "/chat (cold)", "/faq", "/admin"],
        title="API latency target (ms, p95)",
        value_max=400,
    )


def cluster_count_over_time_line():
    """How many clusters grow as more chats are ingested."""
    return line_chart(
        series=[
            [12, 30, 48, 65, 80, 95, 110, 120],   # Radiology
            [8, 22, 36, 50, 62, 74, 85, 92],      # Physiotherapy
            [10, 25, 42, 58, 72, 86, 99, 108],    # Cardiovascular
        ],
        categories=["1k", "2k", "3k", "4k", "5k", "6k", "8k", "10k"],
        names=["Radiology", "Physiotherapy", "Cardiovascular"],
        title="Clusters formed vs chats ingested (mock target curve)",
    )


def silhouette_targets_bar():
    """Target silhouette score per specialty."""
    return bar_chart(
        values=[0.48, 0.52, 0.46],
        categories=["Radiology", "Physiotherapy", "Cardiovascular"],
        title="Silhouette coefficient target (per specialty)",
        y_label="silhouette",
        value_min=0,
        value_max=1.0,
    )

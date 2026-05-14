"""Shared utilities for all PDF documents (colours, styles, drawings, charts)."""
from .theme import (
    PRIMARY, ACCENT, LIGHT, SOFT, DARK, GREEN, ORANGE, GRAY,
    build_styles,
)
from .drawing import box, arrow, label
from .tables import std_table_style, simple_table
from .charts import bar_chart, horizontal_bar_chart, line_chart, pie_chart

__all__ = [
    "PRIMARY", "ACCENT", "LIGHT", "SOFT", "DARK", "GREEN", "ORANGE", "GRAY",
    "build_styles",
    "box", "arrow", "label",
    "std_table_style", "simple_table",
    "bar_chart", "horizontal_bar_chart", "line_chart", "pie_chart",
]

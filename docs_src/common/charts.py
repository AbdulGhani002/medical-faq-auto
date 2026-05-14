"""Chart factory functions built on reportlab.graphics.charts.

All charts are grayscale to match the document theme.
"""
from reportlab.graphics.charts.barcharts import (
    HorizontalBarChart, VerticalBarChart,
)
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.lib import colors as rl_colors

from .theme import ACCENT, GRAY, GREEN, LIGHT, ORANGE, PRIMARY, SOFT


GRAY_PALETTE = [PRIMARY, GREEN, ACCENT, ORANGE, LIGHT, GRAY, SOFT]


def _title(d, w, text):
    d.add(String(
        w / 2, d.height - 14, text,
        fontName="Helvetica-Bold", fontSize=11,
        fillColor=PRIMARY, textAnchor="middle",
    ))


def bar_chart(values, categories, title="", w=460, h=200,
              y_label="", value_min=0, value_max=None) -> Drawing:
    """Vertical bar chart (single series)."""
    d = Drawing(w, h)
    if title:
        _title(d, w, title)
    bc = VerticalBarChart()
    bc.x = 50
    bc.y = 30
    bc.height = h - 70
    bc.width = w - 80
    bc.data = [values]
    bc.categoryAxis.categoryNames = categories
    bc.categoryAxis.labels.fontSize = 8
    bc.categoryAxis.labels.angle = 0
    bc.valueAxis.valueMin = value_min
    if value_max is not None:
        bc.valueAxis.valueMax = value_max
    bc.valueAxis.labels.fontSize = 8
    bc.bars[0].fillColor = PRIMARY
    bc.bars[0].strokeColor = PRIMARY
    if y_label:
        d.add(String(8, h / 2, y_label,
                     fontName="Helvetica", fontSize=8,
                     fillColor=GRAY, textAnchor="middle"))
    d.add(bc)
    return d


def horizontal_bar_chart(values, categories, title="", w=460, h=240,
                         value_max=None) -> Drawing:
    """Horizontal bar chart, single series."""
    d = Drawing(w, h)
    if title:
        _title(d, w, title)
    bc = HorizontalBarChart()
    bc.x = 120
    bc.y = 30
    bc.height = h - 60
    bc.width = w - 150
    bc.data = [values]
    bc.categoryAxis.categoryNames = categories
    bc.categoryAxis.labels.fontSize = 8
    bc.valueAxis.valueMin = 0
    if value_max is not None:
        bc.valueAxis.valueMax = value_max
    bc.valueAxis.labels.fontSize = 8
    bc.bars[0].fillColor = PRIMARY
    bc.bars[0].strokeColor = PRIMARY
    d.add(bc)
    return d


def line_chart(series, categories, names=None, title="", w=460, h=220,
               y_max=None) -> Drawing:
    """One or more line series with shared x axis."""
    d = Drawing(w, h)
    if title:
        _title(d, w, title)
    lc = HorizontalLineChart()
    lc.x = 50
    lc.y = 30
    lc.height = h - 70
    lc.width = w - 80
    lc.data = series
    lc.categoryAxis.categoryNames = categories
    lc.categoryAxis.labels.fontSize = 8
    lc.valueAxis.valueMin = 0
    if y_max is not None:
        lc.valueAxis.valueMax = y_max
    lc.valueAxis.labels.fontSize = 8
    for i in range(len(series)):
        lc.lines[i].strokeColor = GRAY_PALETTE[i % len(GRAY_PALETTE)]
        lc.lines[i].strokeWidth = 1.6
    d.add(lc)
    if names:
        leg = Legend()
        leg.x = w - 100
        leg.y = h - 30
        leg.fontSize = 8
        leg.colorNamePairs = [
            (GRAY_PALETTE[i % len(GRAY_PALETTE)], n)
            for i, n in enumerate(names)
        ]
        d.add(leg)
    return d


def pie_chart(values, labels, title="", w=400, h=220) -> Drawing:
    """Grayscale pie chart with side legend."""
    d = Drawing(w, h)
    if title:
        _title(d, w, title)
    p = Pie()
    p.x = 40
    p.y = 30
    p.width = h - 60
    p.height = h - 60
    p.data = values
    p.labels = [""] * len(values)
    p.slices.strokeColor = rl_colors.white
    p.slices.strokeWidth = 1
    for i in range(len(values)):
        p.slices[i].fillColor = GRAY_PALETTE[i % len(GRAY_PALETTE)]
    d.add(p)

    leg = Legend()
    leg.x = h + 20
    leg.y = h - 40
    leg.fontSize = 8
    leg.alignment = "right"
    leg.colorNamePairs = [
        (GRAY_PALETTE[i % len(GRAY_PALETTE)], f"{labels[i]} ({values[i]})")
        for i in range(len(values))
    ]
    d.add(leg)
    return d

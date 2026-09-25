"""Chart generation and conversion utilities.

Supports:
1. High-resolution (300 DPI) Matplotlib chart rendering with corporate palettes.
2. Conversion to docx-mcp compatible chart parameters for native Office DrawingML charts.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend
import matplotlib.pyplot as plt
import numpy as np
from .ir_schema import ChartBlock, ChartType


CORPORATE_PALETTE = [
    "#1F4E79",  # Deep Navy
    "#2E75B6",  # Medium Blue
    "#5B9BD5",  # Light Blue
    "#41719C",  # Slate Blue
    "#1B365D",  # Dark Royal
    "#70AD47",  # Accent Green
    "#FFC000",  # Accent Gold
    "#ED7D31",  # Accent Orange
]


def render_chart_image(
    chart: ChartBlock,
    output_path: str | Path,
    dpi: int = 300,
) -> Path:
    """Renders a ChartBlock into a crisp 300 DPI PNG image using Matplotlib.

    Applies clean typography, corporate color palettes, and tight bounding boxes.
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(chart.width_inches, chart.height_inches), dpi=dpi)

    # Style configuration
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.grid(axis="y", linestyle="--", alpha=0.4, color="#CCCCCC")
    ax.set_axisbelow(True)

    categories = chart.categories
    series_list = chart.series

    if chart.chart_type == ChartType.BAR:
        x = np.arange(len(categories)) if categories else np.arange(len(series_list[0].values))
        num_series = max(1, len(series_list))
        total_width = 0.75
        bar_width = total_width / num_series

        for i, s in enumerate(series_list):
            offset = (i - (num_series - 1) / 2) * bar_width
            color = CORPORATE_PALETTE[i % len(CORPORATE_PALETTE)]
            vals = s.values
            if len(vals) < len(x):
                vals = vals + [0.0] * (len(x) - len(vals))
            rects = ax.bar(x + offset, vals[:len(x)], bar_width, label=s.name, color=color, edgecolor="none", zorder=3)

        if categories:
            ax.set_xticks(x)
            ax.set_xticklabels(categories, fontsize=9, rotation=0 if len(categories) <= 5 else 25)
        if len(series_list) > 1:
            ax.legend(frameon=False, fontsize=9)

    elif chart.chart_type == ChartType.LINE or chart.chart_type == ChartType.AREA:
        for i, s in enumerate(series_list):
            color = CORPORATE_PALETTE[i % len(CORPORATE_PALETTE)]
            x_vals = range(len(s.values))
            ax.plot(x_vals, s.values, marker="o", markersize=4, linewidth=2.2, label=s.name, color=color, zorder=3)
            if chart.chart_type == ChartType.AREA:
                ax.fill_between(x_vals, s.values, alpha=0.2, color=color)

        if categories:
            ax.set_xticks(range(len(categories)))
            ax.set_xticklabels(categories, fontsize=9)
        if len(series_list) > 1:
            ax.legend(frameon=False, fontsize=9)

    elif chart.chart_type == ChartType.PIE:
        if series_list and series_list[0].values:
            vals = series_list[0].values
            labels = categories if len(categories) == len(vals) else [f"Item {i+1}" for i in range(len(vals))]
            colors = CORPORATE_PALETTE[:len(vals)]
            ax.pie(vals, labels=labels, autopct="%1.1f%%", startangle=90, colors=colors, textprops={"fontsize": 9})
            ax.axis("equal")

    if chart.title:
        ax.set_title(chart.title, fontsize=12, fontweight="bold", pad=12, color="#222222")

    fig.tight_layout()
    fig.savefig(str(out_path), dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def to_docx_mcp_chart_args(chart: ChartBlock, para_id: str = "p1") -> Dict[str, Any]:
    """Converts a ChartBlock to argument dict for docx-mcp chart tools.

    Compatible with:
    - docx-mcp: insert_bar_chart
    - docx-mcp: insert_line_chart
    - docx-mcp: insert_pie_chart
    """
    series_data = [{"name": s.name, "values": s.values} for s in chart.series]
    base_args = {
        "para_id": para_id,
        "title": chart.title,
        "series": series_data,
        "width_cm": round(chart.width_inches * 2.54, 1),
        "height_cm": round(chart.height_inches * 2.54, 1),
    }
    if chart.chart_type != ChartType.PIE:
        base_args["categories"] = chart.categories
    return base_args

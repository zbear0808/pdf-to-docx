"""Chart rendering via Matplotlib with corporate palettes."""

from __future__ import annotations
import logging
from pathlib import Path
from .ir_schema import ChartBlock, ChartType

logger = logging.getLogger(__name__)

CORPORATE_PALETTE = [
    "#1F4E79", "#2E75B6", "#5B9BD5", "#41719C",
    "#1B365D", "#70AD47", "#FFC000", "#ED7D31",
]


def render_chart_image(
    chart: ChartBlock,
    output_path: str | Path,
    dpi: int = 300,
) -> Path:
    """Renders a ChartBlock into a 300 DPI PNG image."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np
    except ImportError:
        logger.warning("matplotlib or numpy not available; cannot render synthetic chart")
        return out_path

    fig, ax = plt.subplots(figsize=(chart.width_inches, chart.height_inches), dpi=dpi)
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
            ax.bar(x + offset, vals[:len(x)], bar_width, label=s.name, color=color, edgecolor="none", zorder=3)
        if categories:
            ax.set_xticks(x)
            ax.set_xticklabels(categories, fontsize=9, rotation=0 if len(categories) <= 5 else 25)
        if len(series_list) > 1:
            ax.legend(frameon=False, fontsize=9)

    elif chart.chart_type == ChartType.LINE:
        for i, s in enumerate(series_list):
            color = CORPORATE_PALETTE[i % len(CORPORATE_PALETTE)]
            ax.plot(range(len(s.values)), s.values, marker="o", markersize=4, linewidth=2.2, label=s.name, color=color, zorder=3)
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

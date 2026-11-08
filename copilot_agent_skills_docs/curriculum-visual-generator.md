# Skill: curriculum-visual-generator

## Description

_Source: `C:\Users\zubair\Documents\GitHub\pdf-to-docx\.agents\skills\curriculum-visual-generator\SKILL.md`

```markdown
---
name: curriculum-visual-generator
description: Generates high-resolution mathematical diagrams, geometry figures, statistical charts, coordinate grids, and computer science visuals using Python (Matplotlib, NumPy, Pillow) and crops assets for the Worksheet AST.
---

# Curriculum Visual Generator Skill

This skill provides comprehensive instructions, standardized visual styling, and reusable Python templates for generating high-resolution, print-ready diagrams and figures for assessments, worksheets, and lesson plans.

All generated assets are saved directly to `_temp/assets/` and auto-cropped to guarantee accurate 2D bin-packing footprint calculations.

---

## 1. Visual Styling & Rendering Standards

Every generated figure must follow these strict publication standards:

| Parameter | Standard Value | Rationale |
| :--- | :--- | :--- |
| **Resolution / DPI** | `300` | Eliminates pixelation on both high-res screens and print |
| **Primary Theme Color** | `#1F4E79` (Deep Navy) | Professional, high-contrast, matches school and district palette |
| **Highlight Color** | `#C00000` (Crimson) | For lines of reflection, transversal cut lines, key angles |
| **Secondary Color** | `#D66011` (Amber/Orange) | For transformed images ($A'B'C'$), candidate choices |
| **Shape Fill Color** | `#EBF3FA` (Very soft blue) | Subtly shades polygons without obscuring grid lines |
| **Grid / Axes Color** | `#7F7F7F` or `#D9D9D9` | Low contrast so student drawings and problem shapes stand out |
| **Font Family** | `DejaVu Sans` / `Arial` | Clean, sans-serif, widely compatible |
| **Font Size** | `9 - 11 pt` | Scaled to match standard document body text |

---

## 2. Standard Workspace Script Structure

Store all diagram generation scripts in `_temp/build/generate_figures.py` and output all images to `_temp/assets/`:

```python
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

# 1. Output directory
ASSET_DIR = Path("_temp/assets")
ASSET_DIR.mkdir(parents=True, exist_ok=True)

# 2. Global styling
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 9.5
plt.rcParams['axes.edgecolor'] = '#595959'
plt.rcParams['axes.linewidth'] = 0.8

# 3. Always auto-crop after saving
from worksheet_packer.image_utils import auto_crop_image

def save_and_crop(fig, filename: str):
    path = ASSET_DIR / filename
    fig.savefig(path, dpi=300, bbox_inches='tight', transparent=False, facecolor='white')
    plt.close(fig)
    # Auto-trim border whitespace
    clean_path, w, h, ar = auto_crop_image(path)
    print(f"Generated: {clean_path.name} ({w}x{h} px, AR: {ar:.3f})")
    return clean_path
```

---

## 3. Reusable Educational Visual Templates

### A. Coordinate Grid with Polygon Transformation
Used for Geometry grid problems where students translate, reflect, or rotate shapes:

```python
from matplotlib.patches import Polygon

def make_coordinate_grid_problem():
    fig, ax = plt.subplots(figsize=(4.5, 4.5), dpi=300)
    
    # Grid configuration (-6 to 6)
    ax.set_xlim(-6.5, 6.5)
    ax.set_ylim(-6.5, 6.5)
    ax.set_xticks(range(-6, 7))
    ax.set_yticks(range(-6, 7))
    ax.grid(True, which='both', color='#D9D9D9', linestyle='-', linewidth=0.7)
    
    # Axes lines
    ax.axhline(0, color='#595959', linewidth=1.2)
    ax.axvline(0, color='#595959', linewidth=1.2)
    ax.set_aspect('equal')
    
    # Original Polygon ABCD
    pts = np.array([[-4, 2], [-2, 5], [-1, 3], [-3, 1]])
    poly = Polygon(pts, closed=True, facecolor='#EBF3FA', edgecolor='#1F4E79', linewidth=2.0)
    ax.add_patch(poly)
    
    # Label vertices
    labels = ['A', 'B', 'C', 'D']
    for (x, y), l in zip(pts, labels):
        ax.plot(x, y, 'o', color='#1F4E79', markersize=4.5)
        ax.text(x - 0.45, y + 0.25, l, fontweight='bold', fontsize=10, color='#1F4E79')
        
    # Translated point A'
    ax.plot(2, -1, 's', color='#C00000', markersize=5)
    ax.text(2.2, -1.2, "$A'$", fontweight='bold', fontsize=10, color='#C00000')
    
    return save_and_crop(fig, "fig_p4_quadrilateral_grid.png")
```

---

### B. Parallel Lines Cut by Transversal with Angle Arcs
Used for Geometry angle relationship and proof items:

```python
from matplotlib.patches import Arc

def make_parallel_transversal():
    fig, ax = plt.subplots(figsize=(4.5, 3.2), dpi=300)
    
    # Parallel lines x and y
    ax.plot([-3, 5], [2, 2], color='#1F4E79', linewidth=1.8)
    ax.plot([-3, 5], [-1, -1], color='#1F4E79', linewidth=1.8)
    ax.text(5.2, 1.9, "$\ell_1$", fontsize=10, color='#1F4E79', fontweight='bold')
    ax.text(5.2, -1.1, "$\ell_2$", fontsize=10, color='#1F4E79', fontweight='bold')
    
    # Transversal t
    ax.plot([-1.5, 3.5], [-2.5, 3.5], color='#C00000', linewidth=1.8)
    ax.text(3.6, 3.4, "$t$", fontsize=10, color='#C00000', fontweight='bold')
    
    # Intersection centers: (2.25, 2.0) and (-0.25, -1.0)
    # Add angle labels
    ax.text(1.7, 2.2, "$a^\\circ$", fontsize=9, fontweight='bold')
    ax.text(2.6, 2.2, "$b^\\circ$", fontsize=9, fontweight='bold')
    ax.text(1.7, 1.6, "$c^\\circ$", fontsize=9, fontweight='bold')
    ax.text(2.6, 1.6, "$d^\\circ$", fontsize=9, fontweight='bold')
    
    ax.text(-0.8, -0.8, "$e^\\circ$", fontsize=9, fontweight='bold')
    ax.text(0.1, -0.8, "$f^\\circ$", fontsize=9, fontweight='bold')
    ax.text(-0.8, -1.4, "$g^\\circ$", fontsize=9, fontweight='bold')
    ax.text(0.1, -1.4, "$h^\\circ$", fontsize=9, fontweight='bold')
    
    ax.set_xlim(-3, 6)
    ax.set_ylim(-3, 4)
    ax.axis('off')
    
    return save_and_crop(fig, "fig_p8_parallel_transversal.png")
```

---

### C. AP Statistics: Comparative Boxplots
Used for AP Statistics data display and comparison questions:

```python
def make_comparative_boxplots():
    fig, ax = plt.subplots(figsize=(5.0, 2.2), dpi=300)
    
    # Synthetic clean data for two treatments
    np.random.seed(42)
    group_a = np.random.normal(loc=72, scale=8, size=40)
    group_b = np.random.normal(loc=84, scale=6, size=40)
    
    bp = ax.boxplot([group_a, group_b], vert=False, patch_artist=True,
                    labels=['Control Group', 'Treatment Group'],
                    widths=0.45)
    
    # Styling colors
    colors = ['#EBF3FA', '#FFF2CC']
    border_colors = ['#1F4E79', '#D66011']
    for patch, c, bc in zip(bp['boxes'], colors, border_colors):
        patch.set_facecolor(c)
        patch.set_edgecolor(bc)
        patch.set_linewidth(1.5)
        
    for median in bp['medians']:
        median.set_color('#C00000')
        median.set_linewidth(1.8)
        
    ax.set_xlabel("Exam Score (Points)", fontsize=9.5)
    ax.grid(axis='x', color='#E0E0E0', linestyle='--', linewidth=0.7)
    
    return save_and_crop(fig, "fig_p2_comparative_boxplots.png")
```

---

### D. Geometry Inscribed Polygons & Symmetries
Used for rotational and line symmetry problems:

```python
from matplotlib.patches import Circle, RegularPolygon

def make_regular_hexagon():
    fig, ax = plt.subplots(figsize=(3.5, 3.5), dpi=300)
    
    # Bounding circle
    circle = Circle((0, 0), radius=1.0, facecolor='none', edgecolor='#7F7F7F', linestyle='--', linewidth=1.0)
    ax.add_patch(circle)
    
    # Inscribed regular hexagon
    hex_patch = RegularPolygon((0, 0), numVertices=6, radius=1.0, orientation=0,
                               facecolor='#EBF3FA', edgecolor='#1F4E79', linewidth=2.0)
    ax.add_patch(hex_patch)
    
    # Center H
    ax.plot(0, 0, 'o', color='#C00000', markersize=5)
    ax.text(0.08, -0.05, "$H$", fontsize=10, fontweight='bold', color='#C00000')
    
    # Vertex labels A-F
    labels = ['A', 'B', 'C', 'D', 'E', 'F']
    angles = np.linspace(np.pi/6, 2*np.pi + np.pi/6, 7)[:-1]
    for ang, l in zip(angles, labels):
        x = 1.18 * np.cos(ang)
        y = 1.18 * np.sin(ang)
        ax.text(x - 0.06, y - 0.06, l, fontsize=10, fontweight='bold', color='#1F4E79')
        # Center radii
        ax.plot([0, np.cos(ang)], [0, np.sin(ang)], color='#7F7F7F', linestyle=':', linewidth=0.9)
        
    ax.set_xlim(-1.4, 1.4)
    ax.set_ylim(-1.4, 1.4)
    ax.set_aspect('equal')
    ax.axis('off')
    
    return save_and_crop(fig, "fig_p5_hexagon_symmetry.png")
```

---

## 4. Cropping & Asset Metadata Integration

When figures are generated or harvested:
1. Every file must be auto-cropped with `auto_crop_image(path)`.
2. Record its width, height, and aspect ratio ($H / W$).
3. In `worksheet_spec.json`, configure the problem's `image` object:
   - For square/portrait figures ($0.6 \le AR \le 1.4$): `category = "detailed_diagram"`, `min_width_in = 1.6`, `preferred_width_in = 2.4`, `layout_hint = "side_by_side"`.
   - For wide figures ($AR < 0.6$): `category = "wide_grid"`, `min_width_in = 2.8`, `preferred_width_in = 3.4`, `layout_hint = "stacked"`.


```

## Notes
Instruction/agent skill; Python utilities for image sizing/cropping and chart rendering.

## Relevant Python Code


### src\worksheet_packer\image_utils.py

```python
"""Image pre-processing and whitespace trimming utilities for worksheet diagrams.

Extracts bounding boxes of actual visual drawings, trims empty white/transparent margins,
computes true aspect ratios, and validates minimum scale thresholds for legibility.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageChops, ImageFilter, ImageOps


@dataclass
class ScaleBoundsResult:
    """Scale bounds and classification for an image asset."""
    source_width_in: float
    source_height_in: float
    min_width_in: float
    preferred_width_in: float
    max_width_in: float
    category: str        # "formula_icon", "compact_shape", "detailed_diagram", "wide_grid"
    has_fine_text: bool
    elasticity: float


def auto_crop_image(
    image_path: str | Path,
    output_path: Optional[str | Path] = None,
    tolerance: int = 15,
    padding_px: int = 4,
) -> Tuple[Path, int, int, float]:
    """Trims solid white and transparent borders from an extracted diagram.

    Args:
        image_path: Path to original raster image.
        output_path: Optional path to save cropped result. If omitted, appends '_cropped'.
        tolerance: Color variance from pure white (0-255) to consider as background margin.
        padding_px: Safe perimeter padding in pixels to prevent clipping edge strokes.

    Returns:
        Tuple of (saved_cropped_path, width_px, height_px, aspect_ratio).
    """
    src = Path(image_path)
    if not src.exists():
        raise FileNotFoundError(f"Image not found for cropping: {src}")

    with Image.open(src) as img:
        # Convert to RGBA for consistent border detection
        rgba = img.convert("RGBA")
        width, height = rgba.size

        # Split channels
        r, g, b, a = rgba.split()

        # Step 1: Detect non-transparent pixels
        # Pixels with alpha > 15 are potential content
        alpha_mask = a.point(lambda p: 255 if p > 15 else 0)

        # Step 2: Detect non-white pixels
        # An RGB pixel is "white background" if R > 255 - tol and G > 255 - tol and B > 255 - tol
        threshold = max(0, 255 - tolerance)
        r_dark = r.point(lambda p: 255 if p < threshold else 0)
        g_dark = g.point(lambda p: 255 if p < threshold else 0)
        b_dark = b.point(lambda p: 255 if p < threshold else 0)

        # Combined color mask: any channel significantly below 255
        color_mask = ImageChops.lighter(r_dark, ImageChops.lighter(g_dark, b_dark))

        # Content is where it's not transparent AND not white
        content_mask = ImageChops.darker(alpha_mask, color_mask)

        bbox = content_mask.getbbox()

        if bbox is None:
            # Image is entirely blank or white; keep original
            crop_box = (0, 0, width, height)
        else:
            x0, y0, x1, y1 = bbox
            # Apply safety padding
            x0 = max(0, x0 - padding_px)
            y0 = max(0, y0 - padding_px)
            x1 = min(width, x1 + padding_px)
            y1 = min(height, y1 + padding_px)
            crop_box = (x0, y0, x1, y1)

        cropped_img = img.crop(crop_box)
        crop_w, crop_h = cropped_img.size
        aspect_ratio = float(crop_h) / float(crop_w) if crop_w > 0 else 1.0

        if output_path is None:
            out_p = src.parent / f"{src.stem}_cropped{src.suffix}"
        else:
            out_p = Path(output_path)

        out_p.parent.mkdir(parents=True, exist_ok=True)
        # Preserve format or default to PNG
        fmt = img.format if img.format else "PNG"
        cropped_img.save(str(out_p), format=fmt)

        return out_p, crop_w, crop_h, aspect_ratio


def inspect_diagram_dimensions(image_path: str | Path) -> Tuple[int, int, float]:
    """Inspects native dimensions and aspect ratio (H / W) of an image without modifying it."""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")
    with Image.open(p) as img:
        w, h = img.size
        ar = float(h) / float(w) if w > 0 else 1.0
        return w, h, ar


def estimate_image_scale_bounds(
    image_path: str | Path,
    native_width_px: int,
    native_height_px: int,
    aspect_ratio: float,
    bbox: Optional[List[int]] = None,
    page_width_in: float = 8.5,
    col_width_in: float = 3.5,
) -> ScaleBoundsResult:
    """Estimates content-aware scale bounds [min_w, pref_w, max_w] and classification for an image.

    Prevents formula icons (e.g. radical signs) from exploding into huge diagrams, while
    enforcing a strict legibility floor for detailed geometry figures with fine angle text.

    Args:
        image_path: File path of the image.
        native_width_px: Native cropped width in pixels.
        native_height_px: Native cropped height in pixels.
        aspect_ratio: True height-to-width ratio (H / W).
        bbox: Optional normalized bounding box [ymin, xmin, ymax, xmax] (0-1000 scale).
        page_width_in: Page width in inches (default 8.5).
        col_width_in: Target column width in inches (default 3.5).

    Returns:
        ScaleBoundsResult with source dimensions, bounds, category, fine_text flag, and elasticity.
    """
    # 1. Physical source width anchor
    if bbox and len(bbox) == 4 and (bbox[3] > bbox[1]):
        w_ratio = (bbox[3] - bbox[1]) / 1000.0
        h_ratio = (bbox[2] - bbox[0]) / 1000.0
        source_w = round(w_ratio * page_width_in, 2)
        source_h = round(h_ratio * 11.0, 2)
    else:
        # Fallback to ~180 DPI estimation
        source_w = round(native_width_px / 180.0, 2)
        source_h = round(native_height_px / 180.0, 2)

    # 2. Check for fine line / text density
    has_fine_text = True
    p = Path(image_path)
    if p.exists():
        try:
            with Image.open(p) as img:
                small = img.convert("L").resize((120, 120))
                edges = small.filter(ImageFilter.FIND_EDGES)
                px_data = edges.get_flattened_data() if hasattr(edges, "get_flattened_data") else edges.getdata()
                edge_pixels = sum(1 for px in px_data if px > 64)
                has_fine_text = (edge_pixels / 14400.0) > 0.05
        except Exception:
            has_fine_text = True

    # 3. Content classification & scale bounds derivation
    # Category A: Formula / Math Symbol Icon (e.g. radical expression, fraction, small symbol)
    if source_w <= 1.10 or (native_width_px < 220 and native_height_px < 150):
        category = "formula_icon"
        # Never let a formula icon balloon to fill the column!
        min_w = max(0.40, round(source_w * 0.85, 2))
        pref_w = min(1.25, max(0.65, round(source_w * 1.05, 2)))
        max_w = min(1.40, max(0.95, round(source_w * 1.30, 2)))
        elasticity = 0.5  # Modest compression

    # Category B: Wide Grid, Coordinate Plane, or Data Table
    elif aspect_ratio < 0.52 or source_w >= 3.20:
        category = "wide_grid"
        min_w = min(col_width_in * 0.70, max(2.20, round(col_width_in * 0.65, 2)))
        pref_w = min(col_width_in * 0.95, max(2.80, round(source_w, 2)))
        max_w = col_width_in
        elasticity = 0.8

    # Category C: Compact Shape / Diagram (simple geometric figure, single polygon)
    elif source_w <= 2.20 and not (aspect_ratio > 1.6 or aspect_ratio < 0.6):
        category = "compact_shape"
        min_w = 1.10
        pref_w = min(col_width_in * 0.85, max(1.50, round(source_w, 2)))
        max_w = min(col_width_in * 0.95, max(2.40, round(source_w * 1.25, 2)))
        elasticity = 1.0

    # Category D: Detailed Geometry Diagram (angles, line labels, complex markings)
    else:
        category = "detailed_diagram"
        # High legibility floor: below ~1.45 in, angle markings like 30° become illegible
        min_w = 1.45
        pref_w = min(col_width_in * 0.90, max(1.90, round(source_w, 2)))
        max_w = min(col_width_in, max(3.00, round(source_w * 1.20, 2)))
        elasticity = 1.0

    # Safety clamps
    min_w = min(min_w, col_width_in)
    pref_w = max(min_w, min(pref_w, col_width_in))
    max_w = max(pref_w, min(max_w, col_width_in))

    return ScaleBoundsResult(
        source_width_in=source_w,
        source_height_in=source_h,
        min_width_in=min_w,
        preferred_width_in=pref_w,
        max_width_in=max_w,
        category=category,
        has_fine_text=has_fine_text,
        elasticity=elasticity,
    )


def audit_image_boundaries(
    image_path: str | Path,
    bg_threshold: int = 240,
    edge_density_tolerance: float = 0.015,
) -> Dict[str, Any]:
    """Audits image edge perimeters for non-background pixels indicative of cutoffs.

    Scans the outer 2 rows and columns of an image asset to detect whether visual content
    (e.g., axes, formulas, exponent text, or diagram strokes) was truncated by a tight crop.

    Args:
        image_path: Path to the image file to audit.
        bg_threshold: RGB channel value above which a pixel is considered white background (0-255).
        edge_density_tolerance: Max allowed proportion of content pixels along any edge before flagging.

    Returns:
        Dict with status ("PASS" | "FAIL"), filename, cutoffs list, and per-edge density metrics.
    """
    img_p = Path(image_path)
    if not img_p.exists():
        raise FileNotFoundError(f"Image not found: {img_p}")

    with Image.open(img_p) as raw_img:
        img = raw_img.convert("RGBA")
        w, h = img.size
        if w == 0 or h == 0:
            return {
                "status": "FAIL",
                "name": img_p.name,
                "error": "Empty image",
                "cutoffs": [],
                "densities": {"top": 0.0, "bottom": 0.0, "left": 0.0, "right": 0.0},
            }

        pixels = img.load()

        def is_content(x: int, y: int) -> bool:
            r, g, b, a = pixels[x, y]
            if a < 30:  # transparent
                return False
            return r < bg_threshold or g < bg_threshold or b < bg_threshold

        def scan_edge(coords: List[Tuple[int, int]]) -> float:
            content_count = sum(1 for (x, y) in coords if is_content(x, y))
            return content_count / max(1, len(coords))

        top_density = scan_edge([(x, y) for y in range(min(2, h)) for x in range(w)])
        bottom_density = scan_edge([(x, y) for y in range(max(0, h - 2), h) for x in range(w)])
        left_density = scan_edge([(x, y) for x in range(min(2, w)) for y in range(h)])
        right_density = scan_edge([(x, y) for x in range(max(0, w - 2), w) for y in range(h)])

        cutoffs: List[Tuple[str, float]] = []
        if top_density > edge_density_tolerance:
            cutoffs.append(("TOP", top_density))
        if bottom_density > edge_density_tolerance:
            cutoffs.append(("BOTTOM", bottom_density))
        if left_density > edge_density_tolerance:
            cutoffs.append(("LEFT", left_density))
        if right_density > edge_density_tolerance:
            cutoffs.append(("RIGHT", right_density))

        return {
            "status": "FAIL" if cutoffs else "PASS",
            "name": img_p.name,
            "cutoffs": cutoffs,
            "densities": {
                "top": top_density,
                "bottom": bottom_density,
                "left": left_density,
                "right": right_density,
            },
        }


class ImageBoundaryAuditor:
    """Audits image edge perimeters for non-background pixels indicative of cutoffs."""

    def __init__(self, bg_threshold: int = 240, edge_density_tolerance: float = 0.015):
        self.bg_threshold = bg_threshold
        self.edge_density_tolerance = edge_density_tolerance

    def audit_image_file(self, image_path: str | Path) -> Dict[str, Any]:
        return audit_image_boundaries(
            image_path=image_path,
            bg_threshold=self.bg_threshold,
            edge_density_tolerance=self.edge_density_tolerance,
        )




```

### src\pdf_to_docx\chart_generator.py

```python
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

```

### .agents\skills\pdf-to-docx\scripts\crop_asset.py

_File not found in repo._

### .agents\skills\pdf-to-docx\scripts\render_pages.py

_File not found in repo._

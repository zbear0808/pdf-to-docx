"""Image pre-processing and whitespace trimming utilities for worksheet diagrams.

Extracts bounding boxes of actual visual drawings, trims empty white/transparent margins,
computes true aspect ratios, and validates minimum scale thresholds for legibility.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
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



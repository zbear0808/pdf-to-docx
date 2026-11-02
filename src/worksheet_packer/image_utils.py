"""Image pre-processing and whitespace trimming utilities for worksheet diagrams.

Extracts bounding boxes of actual visual drawings, trims empty white/transparent margins,
computes true aspect ratios, and validates minimum scale thresholds for legibility.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image, ImageChops, ImageOps


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


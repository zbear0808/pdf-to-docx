"""Multi-Modal Asset Harvester & Visual Refiner.

Provides unified detection and extraction across:
  - Discrete embedded raster images (PDF XObjects)
  - Native vector / SVG graphics (PDF drawing path clusters)
  - Scanned / flattened page regions (whitespace valley snapping)
  - Peripheral text absorption (axis labels, tick text, and legends)
"""

from __future__ import annotations
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pymupdf as fitz

logger = logging.getLogger(__name__)


@dataclass
class VisualCandidate:
    """A detected visual candidate region on a PDF page."""
    type: str  # "native_image" | "vector_cluster" | "scan_region"
    rect: fitz.Rect
    xref: Optional[int] = None
    ext: str = "png"
    width_px: Optional[int] = None
    height_px: Optional[int] = None
    path_count: int = 0


def harvest_page_visual_candidates(
    doc: fitz.Document,
    page: fitz.Page,
    min_vector_paths: int = 3,
    min_vector_area: float = 1500.0,
) -> List[VisualCandidate]:
    """Discovers all deterministic visual candidate anchors on a page.

    Identifies:
      1. Embedded raster image XObjects with their exact placement rects.
      2. Vector drawing path clusters (native SVG/chart diagrams).
    """
    w = page.rect.width
    h = page.rect.height
    candidates: List[VisualCandidate] = []

    # ── 1. Embedded Raster Images ──
    seen_xrefs = set()
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        if xref in seen_xrefs:
            continue
        seen_xrefs.add(xref)

        try:
            base_img = doc.extract_image(xref)
            placements = page.get_image_rects(xref)
            for r in placements:
                # Ignore tiny 1x1 icons or full-page background textures if page has digital text
                if r.width < 5 or r.height < 5:
                    continue
                if r.width >= w * 0.98 and r.height >= h * 0.98 and len(page.get_text()) > 200:
                    continue

                candidates.append(
                    VisualCandidate(
                        type="native_image",
                        rect=r,
                        xref=xref,
                        ext=base_img.get("ext", "png"),
                        width_px=base_img.get("width"),
                        height_px=base_img.get("height"),
                    )
                )
        except Exception as e:
            logger.debug(f"Failed to inspect image xref {xref}: {e}")

    # ── 2. Vector Drawing Clusters ──
    drawings = page.get_drawings()
    # Filter out page borders or tiny decorative rules
    valid_drawings = [
        d for d in drawings
        if d["rect"].width > 6 and d["rect"].height > 6
        and not (d["rect"].width >= w * 0.96 and d["rect"].height >= h * 0.96)
    ]

    if valid_drawings:
        clusters: List[Dict[str, Any]] = []
        for d in valid_drawings:
            d_rect = fitz.Rect(d["rect"])
            merged = False
            for c in clusters:
                # Expand cluster by 15 pt to merge nearby strokes
                c_rect = c["rect"]
                expanded_c = fitz.Rect(c_rect.x0 - 15, c_rect.y0 - 15, c_rect.x1 + 15, c_rect.y1 + 15)
                if expanded_c.intersects(d_rect):
                    c["rect"] |= d_rect
                    c["count"] += 1
                    merged = True
                    break
            if not merged:
                clusters.append({"rect": d_rect, "count": 1})

        for c in clusters:
            r = c["rect"]
            area = r.width * r.height
            if c["count"] >= min_vector_paths or area >= min_vector_area:
                # Check if this vector cluster is already covered by a native image
                covered = False
                for cand in candidates:
                    overlap = (cand.rect & r).get_area()
                    if overlap / max(1.0, area) > 0.7:
                        covered = True
                        break
                if not covered:
                    candidates.append(
                        VisualCandidate(
                            type="vector_cluster",
                            rect=r,
                            xref=None,
                            ext="png",
                            path_count=c["count"],
                        )
                    )

    return candidates


def snap_rect_to_whitespace(
    page: fitz.Page,
    rect: fitz.Rect,
    max_expansion_pt: float = 40.0,
    scan_dpi: int = 150,
) -> fitz.Rect:
    """Snaps a bounding box outward if its edges slice through active visual content.

    Ensures that crops never slice through letters, lines, or diagram components
    by expanding towards the nearest clean horizontal/vertical whitespace valley.
    """
    zoom = scan_dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)

    px0 = max(0, int(rect.x0 * zoom))
    py0 = max(0, int(rect.y0 * zoom))
    px1 = min(pix.width, int(rect.x1 * zoom))
    py1 = min(pix.height, int(rect.y1 * zoom))

    def row_is_clean(y: int, x_start: int, x_end: int) -> bool:
        if y < 0 or y >= pix.height:
            return True
        non_white = 0
        total = max(1, x_end - x_start)
        for x in range(x_start, x_end):
            r, g, b = pix.pixel(x, y)
            if r < 240 or g < 240 or b < 240:
                non_white += 1
                if non_white / total > 0.015:
                    return False
        return True

    max_search_px = int(max_expansion_pt * zoom)

    # 1. Top Edge: If slicing content, scan upwards for whitespace
    new_py0 = py0
    if not row_is_clean(py0, px0, px1):
        for y in range(py0 - 1, max(0, py0 - max_search_px), -1):
            if row_is_clean(y, px0, px1):
                new_py0 = y
                break

    # 2. Bottom Edge: If slicing content, scan downwards for whitespace
    new_py1 = py1
    if not row_is_clean(py1, px0, px1):
        for y in range(py1 + 1, min(pix.height, py1 + max_search_px)):
            if row_is_clean(y, px0, px1):
                new_py1 = y
                break

    snapped = fitz.Rect(
        rect.x0,
        new_py0 / zoom,
        rect.x1,
        new_py1 / zoom,
    )
    return snapped & page.rect


def absorb_peripheral_text(
    page: fitz.Page,
    rect: fitz.Rect,
    max_distance_pt: float = 20.0,
) -> fitz.Rect:
    """Expands a graphic rectangle to absorb adjacent axis labels, tick labels, or legends."""
    expanded = fitz.Rect(rect)
    blocks = page.get_text("blocks")
    for b in blocks:
        b_rect = fitz.Rect(b[:4])
        # If the text block is within max_distance_pt below or above the graphic
        # and has significant horizontal alignment
        if b_rect.intersects(fitz.Rect(rect.x0, rect.y1, rect.x1, rect.y1 + max_distance_pt)):
            expanded |= b_rect
        elif b_rect.intersects(fitz.Rect(rect.x0, rect.y0 - max_distance_pt, rect.x1, rect.y0)):
            # Only absorb small single-line titles or labels (height <= 25 pt)
            if b_rect.height <= 25:
                expanded |= b_rect
    return expanded & page.rect


def resolve_visual_asset(
    doc: fitz.Document,
    page: fitz.Page,
    requested_bbox: List[int] | Tuple[int, int, int, int],
    output_path: str | Path,
    candidates: Optional[List[VisualCandidate]] = None,
    dpi: int = 300,
) -> Dict[str, Any]:
    """Resolves an asset request to the highest-fidelity representation possible.

    If the requested bounding box overlaps an embedded native image:
      -> Extracts original native image bytes directly (zero loss, zero cropping).
    If it overlaps a native vector drawing cluster:
      -> Renders vector paths at high-resolution 300 DPI.
    Otherwise:
      -> Performs a whitespace-snapped crop on the rendered page canvas.

    Returns:
        dict with keys:
          - 'source': 'native_image' | 'vector_cluster' | 'snapped_crop'
          - 'rect': fitz.Rect in PDF points
          - 'width_inches': float
          - 'height_inches': float
          - 'image_path': str
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    w = page.rect.width
    h = page.rect.height
    ymin, xmin, ymax, xmax = requested_bbox

    req_rect = fitz.Rect(
        (xmin / 1000.0) * w,
        (ymin / 1000.0) * h,
        (xmax / 1000.0) * w,
        (ymax / 1000.0) * h,
    )

    if candidates is None:
        candidates = harvest_page_visual_candidates(doc, page)

    # ── Match against candidate anchors ──
    best_candidate: Optional[VisualCandidate] = None
    best_overlap = 0.0

    for cand in candidates:
        intersect = req_rect & cand.rect
        if not intersect.is_empty:
            cand_area = cand.rect.get_area()
            req_area = req_rect.get_area()
            overlap_ratio = intersect.get_area() / max(1.0, min(req_area, cand_area))
            if overlap_ratio > 0.35 and overlap_ratio > best_overlap:
                best_overlap = overlap_ratio
                best_candidate = cand

    # Case A: Matched Native Embedded Image
    if best_candidate and best_candidate.type == "native_image" and best_candidate.xref is not None:
        base_img = doc.extract_image(best_candidate.xref)
        image_bytes = base_img["image"]
        # Ensure correct extension
        ext = base_img.get("ext", "png")
        if output_path.suffix.lower() != f".{ext}":
            output_path = output_path.with_suffix(f".{ext}")

        output_path.write_bytes(image_bytes)
        c_rect = best_candidate.rect
        logger.info(
            f"Extracted native image xref={best_candidate.xref} "
            f"({base_img.get('width')}x{base_img.get('height')} {ext}) to {output_path}"
        )
        return {
            "source": "native_image",
            "rect": c_rect,
            "width_inches": round(min(6.5, max(0.5, c_rect.width / 72.0)), 2),
            "height_inches": round(c_rect.height / 72.0, 2),
            "image_path": str(output_path),
        }

    # Case B: Matched Native Vector Cluster
    if best_candidate and best_candidate.type == "vector_cluster":
        c_rect = absorb_peripheral_text(page, best_candidate.rect)
        c_rect = snap_rect_to_whitespace(page, c_rect)
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=c_rect, alpha=False)
        pix.save(str(output_path))
        logger.info(
            f"Rendered vector cluster ({best_candidate.path_count} paths) to {output_path}"
        )
        return {
            "source": "vector_cluster",
            "rect": c_rect,
            "width_inches": round(min(6.5, max(0.5, c_rect.width / 72.0)), 2),
            "height_inches": round(c_rect.height / 72.0, 2),
            "image_path": str(output_path),
        }

    # Case C: Scanned Page or Unanchored Region (Whitespace Snapped Crop)
    c_rect = absorb_peripheral_text(page, req_rect)
    c_rect = snap_rect_to_whitespace(page, c_rect)
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=c_rect, alpha=False)
    pix.save(str(output_path))
    logger.info(f"Rendered whitespace-snapped crop to {output_path}")
    return {
        "source": "snapped_crop",
        "rect": c_rect,
        "width_inches": round(min(6.5, max(0.5, c_rect.width / 72.0)), 2),
        "height_inches": round(c_rect.height / 72.0, 2),
        "image_path": str(output_path),
    }


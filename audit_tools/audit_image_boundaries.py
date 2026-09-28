#!/usr/bin/env python3
"""Audit image borders and boundaries to detect truncated graphics or severed labels.

Analyzes edge pixel profiles (top, bottom, left, right borders) of image assets
or crops to determine if graphics, axes, or labels were sliced off prematurely.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf as fitz


class ImageBoundaryAuditor:
    """Audits image edge perimeters for non-background pixels indicative of cutoffs."""

    def __init__(self, bg_threshold: int = 240, edge_density_tolerance: float = 0.015):
        """
        Args:
            bg_threshold: RGB channel value above which pixel is considered white/background (0-255).
            edge_density_tolerance: Max percentage of non-white pixels allowed on an edge before flagging.
        """
        self.bg_threshold = bg_threshold
        self.edge_density_tolerance = edge_density_tolerance

    def audit_image_file(self, image_path: str | Path) -> Dict[str, Any]:
        """Audits an image file on disk (PNG, JPEG, etc.)."""
        img_p = Path(image_path)
        if not img_p.exists():
            raise FileNotFoundError(f"Image not found: {img_p}")

        pix = fitz.Pixmap(str(img_p))
        return self._audit_pixmap(pix, name=img_p.name)

    def _audit_pixmap(self, pix: fitz.Pixmap, name: str = "image") -> Dict[str, Any]:
        w, h = pix.width, pix.height
        if w == 0 or h == 0:
            return {"name": name, "error": "Empty pixmap"}

        # Helper to test if a pixel is non-background
        def is_content(x: int, y: int) -> bool:
            try:
                # If pixmap has alpha, check opacity
                if pix.alpha:
                    # pixel returns (r, g, b, a) or (gray, a)
                    p = pix.pixel(x, y)
                    a = p[-1]
                    if a < 30:  # transparent
                        return False
                    rgb = p[:-1]
                else:
                    rgb = pix.pixel(x, y)

                # Check lightness
                if len(rgb) == 1:
                    return rgb[0] < self.bg_threshold
                return any(c < self.bg_threshold for c in rgb[:3])
            except Exception:
                return False

        # Scan 4 outer borders (sampling 3 perimeter rows/columns to catch near-border cutoffs)
        def scan_edge(pixels_list: List[Tuple[int, int]]) -> Tuple[int, float]:
            content_count = sum(1 for (x, y) in pixels_list if is_content(x, y))
            density = content_count / max(1, len(pixels_list))
            return content_count, density

        # Top border (first 2 rows)
        top_pixels = [(x, y) for y in range(min(2, h)) for x in range(w)]
        top_count, top_density = scan_edge(top_pixels)

        # Bottom border (last 2 rows)
        bottom_pixels = [(x, y) for y in range(max(0, h - 2), h) for x in range(w)]
        bottom_count, bottom_density = scan_edge(bottom_pixels)

        # Left border (first 2 columns)
        left_pixels = [(x, y) for x in range(min(2, w)) for y in range(h)]
        left_count, left_density = scan_edge(left_pixels)

        # Right border (last 2 columns)
        right_pixels = [(x, y) for x in range(max(0, w - 2), w) for y in range(h)]
        right_count, right_density = scan_edge(right_pixels)

        cutoffs = []
        if top_density > self.edge_density_tolerance:
            cutoffs.append(("TOP", top_density))
        if bottom_density > self.edge_density_tolerance:
            cutoffs.append(("BOTTOM", bottom_density))
        if left_density > self.edge_density_tolerance:
            cutoffs.append(("LEFT", left_density))
        if right_density > self.edge_density_tolerance:
            cutoffs.append(("RIGHT", right_density))

        status = "FAIL" if cutoffs else "PASS"

        return {
            "name": name,
            "dimensions_px": f"{w}x{h}",
            "status": status,
            "cutoffs": cutoffs,
            "edges": {
                "top": {"density": round(top_density, 4), "non_white": top_count},
                "bottom": {"density": round(bottom_density, 4), "non_white": bottom_count},
                "left": {"density": round(left_density, 4), "non_white": left_count},
                "right": {"density": round(right_density, 4), "non_white": right_count},
            },
        }

    def audit_pdf_bbox(
        self,
        pdf_path: str | Path,
        page_number: int,
        bbox: List[int] | Tuple[int, int, int, int],
        dpi: int = 150,
    ) -> Dict[str, Any]:
        """Audits a candidate normalized bbox [ymin, xmin, ymax, xmax] on a PDF page."""
        doc = fitz.open(str(pdf_path))
        page = doc[page_number - 1]
        w, h = page.rect.width, page.rect.height
        ymin, xmin, ymax, xmax = bbox

        clip_rect = fitz.Rect(
            (xmin / 1000.0) * w,
            (ymin / 1000.0) * h,
            (xmax / 1000.0) * w,
            (ymax / 1000.0) * h,
        ) & page.rect

        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
        result = self._audit_pixmap(pix, name=f"Page {page_number} bbox {bbox}")
        result["rect_pt"] = [round(clip_rect.x0, 1), round(clip_rect.y0, 1), round(clip_rect.x1, 1), round(clip_rect.y1, 1)]
        doc.close()
        return result


def main():
    parser = argparse.ArgumentParser(description="Audit image boundaries and test for cutoffs.")
    parser.add_argument("target", type=str, help="Path to image file OR directory of images to audit")
    parser.add_argument("--pdf", type=str, default=None, help="Optional: PDF path to audit a bbox on")
    parser.add_argument("--page", type=int, default=1, help="Page number if testing PDF bbox (1-indexed)")
    parser.add_argument("--bbox", type=int, nargs=4, default=None, metavar=("YMIN", "XMIN", "YMAX", "XMAX"),
                        help="Optional: Normalized [ymin xmin ymax xmax] 0-1000")
    args = parser.parse_args()

    auditor = ImageBoundaryAuditor()

    print("=" * 70)
    print(" IMAGE BOUNDARY & CUTOFF AUDIT")
    print("=" * 70)

    if args.pdf and args.bbox:
        # PDF bbox mode
        print(f"Auditing BBox {args.bbox} on {Path(args.pdf).name} (Page {args.page})...")
        res = auditor.audit_pdf_bbox(args.pdf, args.page, args.bbox)
        badge = "[PASSED]" if res["status"] == "PASS" else "[CUTOFF DETECTED]"
        print(f"Status: {badge} | Size: {res['dimensions_px']} | Rect: {res['rect_pt']}")
        if res["cutoffs"]:
            for edge, dens in res["cutoffs"]:
                print(f"  ! CUTOFF at {edge} edge: {dens*100:.1f}% non-background pixels!")
        else:
            print("  + All 4 borders terminate in clean whitespace. No graphic cutoff.")
        print("=" * 70)
        return

    target_path = Path(args.target)
    if target_path.is_file():
        image_files = [target_path]
    elif target_path.is_dir():
        image_files = sorted(
            [f for f in target_path.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg", ".bmp", ".webp")]
        )
    else:
        print(f"Error: Target path not found: {target_path}")
        sys.exit(1)

    print(f"Target: {target_path} ({len(image_files)} image(s))")
    print("-" * 70)

    passed = 0
    failed = 0

    for img_file in image_files:
        res = auditor.audit_image_file(img_file)
        if res["status"] == "PASS":
            passed += 1
            print(f"  + [PASS] {res['name']:<35} ({res['dimensions_px']}) - Clean borders")
        else:
            failed += 1
            cutoff_strs = [f"{edge} ({dens*100:.1f}%)" for edge, dens in res["cutoffs"]]
            print(f"  ! [FAIL] {res['name']:<35} ({res['dimensions_px']}) - CUTOFF DETECTED at {', '.join(cutoff_strs)}")

    print("-" * 70)
    print(f"SUMMARY: {passed} Clean Borders | {failed} Cutoff Warnings across {len(image_files)} images.")
    print("=" * 70)


if __name__ == "__main__":
    main()

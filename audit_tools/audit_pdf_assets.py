#!/usr/bin/env python3
"""Audit visual assets, vector drawings, and layout geometry in a source PDF.

Discovers native embedded images, vector path clusters, and text blocks
across all pages or a targeted page, reporting exact bounding boxes
and dimensions.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymupdf as fitz


class PDFAssetAuditor:
    """Discovers and inspects visual candidates (images, drawings) in a PDF."""

    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        self.doc = fitz.open(str(self.pdf_path))

    def close(self):
        if self.doc:
            self.doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def audit_page(self, page_number: int, save_crops_dir: Optional[Path] = None) -> Dict[str, Any]:
        """Audits visual candidates on a single page (1-indexed)."""
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page {page_number} out of range (1..{len(self.doc)})")

        page = self.doc[page_number - 1]
        rect = page.rect
        w, h = rect.width, rect.height

        # 1. Native embedded images
        native_images = []
        seen_xrefs = set()
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen_xrefs:
                continue
            seen_xrefs.add(xref)
            base_img = self.doc.extract_image(xref)
            placements = page.get_image_rects(xref)
            for r in placements:
                is_full_bg = r.width >= w * 0.95 and r.height >= h * 0.95
                norm_box = [
                    round((r.y0 / h) * 1000, 1),
                    round((r.x0 / w) * 1000, 1),
                    round((r.y1 / h) * 1000, 1),
                    round((r.x1 / w) * 1000, 1),
                ]
                ar = round(r.width / r.height, 3) if r.height > 0 else 0.0
                native_images.append({
                    "xref": xref,
                    "rect": [round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)],
                    "norm_bbox": norm_box,
                    "width_pt": round(r.width, 1),
                    "height_pt": round(r.height, 1),
                    "width_px": base_img["width"],
                    "height_px": base_img["height"],
                    "ext": base_img["ext"],
                    "aspect_ratio": ar,
                    "is_full_page_bg": is_full_bg,
                })

        # 2. Vector drawings and clusters
        drawings = page.get_drawings()
        valid_drawings = [
            d for d in drawings
            if d["rect"].width > 5 and d["rect"].height > 5
            and not (d["rect"].width >= w * 0.95 and d["rect"].height >= h * 0.95)
        ]

        clusters = []
        for d in valid_drawings:
            d_rect = fitz.Rect(d["rect"])
            merged = False
            for c in clusters:
                expanded = fitz.Rect(c["rect"].x0 - 15, c["rect"].y0 - 15, c["rect"].x1 + 15, c["rect"].y1 + 15)
                if expanded.intersects(d_rect):
                    c["rect"] |= d_rect
                    c["count"] += 1
                    merged = True
                    break
            if not merged:
                clusters.append({"rect": d_rect, "count": 1})

        vector_clusters = []
        for c_idx, c in enumerate(clusters):
            r = c["rect"]
            if c["count"] >= 3 or (r.width * r.height > 1500):
                norm_box = [
                    round((r.y0 / h) * 1000, 1),
                    round((r.x0 / w) * 1000, 1),
                    round((r.y1 / h) * 1000, 1),
                    round((r.x1 / w) * 1000, 1),
                ]
                ar = round(r.width / r.height, 3) if r.height > 0 else 0.0
                vector_clusters.append({
                    "cluster_id": c_idx + 1,
                    "path_count": c["count"],
                    "rect": [round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)],
                    "norm_bbox": norm_box,
                    "width_pt": round(r.width, 1),
                    "height_pt": round(r.height, 1),
                    "aspect_ratio": ar,
                })

        # 3. Text blocks
        text_blocks = page.get_text("blocks")
        text_blocks_summary = []
        for b in text_blocks:
            tb_rect = fitz.Rect(b[:4])
            text = b[4].strip().replace("\n", " ")
            if text:
                text_blocks_summary.append({
                    "rect": [round(tb_rect.x0, 1), round(tb_rect.y0, 1), round(tb_rect.x1, 1), round(tb_rect.y1, 1)],
                    "text_preview": text[:40],
                    "line_count": text.count(" ") + 1,
                })

        # Save optional preview crops
        if save_crops_dir:
            save_crops_dir.mkdir(parents=True, exist_ok=True)
            for idx, img in enumerate(native_images):
                if not img["is_full_page_bg"]:
                    crop_rect = fitz.Rect(img["rect"])
                    pix = page.get_pixmap(clip=crop_rect, dpi=200)
                    pix.save(str(save_crops_dir / f"p{page_number}_native_{idx+1}_xref{img['xref']}.png"))
            for idx, vc in enumerate(vector_clusters):
                crop_rect = fitz.Rect(vc["rect"])
                pix = page.get_pixmap(clip=crop_rect, dpi=200)
                pix.save(str(save_crops_dir / f"p{page_number}_vector_cluster_{vc['cluster_id']}.png"))

        return {
            "page_number": page_number,
            "width_pt": round(w, 1),
            "height_pt": round(h, 1),
            "orientation": "landscape" if w > h else "portrait",
            "native_images": native_images,
            "vector_clusters": vector_clusters,
            "total_raw_drawings": len(drawings),
            "text_blocks_count": len(text_blocks_summary),
        }

    def print_report(self, target_page: Optional[int] = None, save_crops: Optional[Path] = None):
        """Prints a CLI report for all pages or target_page."""
        meta = self.doc.metadata or {}
        print("=" * 75)
        print(f" PDF ASSET & GEOMETRY AUDIT: {self.pdf_path.name}")
        print("=" * 75)
        print(f"Title: {meta.get('title') or self.pdf_path.stem} | Total Pages: {len(self.doc)}")
        print("-" * 75)

        pages_to_audit = [target_page] if target_page else list(range(1, len(self.doc) + 1))

        total_native = 0
        total_vectors = 0

        for p_num in pages_to_audit:
            res = self.audit_page(p_num, save_crops_dir=save_crops)
            non_bg_imgs = [img for img in res["native_images"] if not img["is_full_page_bg"]]
            v_clusts = res["vector_clusters"]
            total_native += len(non_bg_imgs)
            total_vectors += len(v_clusts)

            print(f"\n--- PAGE {p_num} ({res['width_pt']} x {res['height_pt']} pt, {res['orientation']}) ---")
            print(f"  Text Blocks: {res['text_blocks_count']} | Raw Drawings: {res['total_raw_drawings']}")
            print(f"  Visual Assets: {len(non_bg_imgs)} Native Images, {len(v_clusts)} Vector Drawing Clusters")

            if non_bg_imgs:
                print("  [Native Images]:")
                for img in non_bg_imgs:
                    print(f"    - xref={img['xref']} ({img['ext'].upper()} {img['width_px']}x{img['height_px']}px) | "
                          f"Rect: {img['rect']} (AR: {img['aspect_ratio']}) | "
                          f"Norm: {img['norm_bbox']}")

            if v_clusts:
                print("  [Vector Drawing Clusters]:")
                for vc in v_clusts:
                    print(f"    - Cluster #{vc['cluster_id']} ({vc['path_count']} paths) | "
                          f"Rect: {vc['rect']} (AR: {vc['aspect_ratio']}) | "
                          f"Norm: {vc['norm_bbox']}")

            if not non_bg_imgs and not v_clusts:
                print("  (Pure textual/tabular page - no standalone visual graphics)")

        print("\n" + "=" * 75)
        print(f" SUMMARY: Discovered {total_native} native images and {total_vectors} vector graphic clusters across {len(pages_to_audit)} pages.")
        if save_crops:
            print(f" Crops saved to: {save_crops.resolve()}")
        print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Audit visual assets and geometry of a PDF.")
    parser.add_argument("pdf_path", type=str, help="Path to input PDF file")
    parser.add_argument("--page", "-p", type=int, default=None, help="Target specific page (1-indexed)")
    parser.add_argument("--save-crops", "-s", type=str, default=None, help="Directory to save asset crop PNGs")
    args = parser.parse_args()

    crops_dir = Path(args.save_crops) if args.save_crops else None
    with PDFAssetAuditor(args.pdf_path) as auditor:
        auditor.print_report(target_page=args.page, save_crops=crops_dir)


if __name__ == "__main__":
    main()

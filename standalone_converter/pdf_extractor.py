"""PDF Extraction utilities powered by PyMuPDF.

Handles rendering pages to high-resolution images for vision analysis,
and cropping bounding-box regions for asset extraction.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pymupdf as fitz


class PDFExtractor:
    """Extracts pages, text, and visual assets from PDF documents."""

    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        self.doc = fitz.open(str(self.pdf_path))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.doc:
            self.doc.close()

    @property
    def page_count(self) -> int:
        return len(self.doc)

    def get_document_info(self) -> Dict[str, Any]:
        """Returns document metadata and page geometry overview."""
        meta = self.doc.metadata or {}
        pages_summary = []
        for i, page in enumerate(self.doc):
            rect = page.rect
            pages_summary.append({
                "page_number": i + 1,
                "width_pt": rect.width,
                "height_pt": rect.height,
                "orientation": "landscape" if rect.width > rect.height else "portrait",
            })
        return {
            "title": meta.get("title") or self.pdf_path.stem,
            "author": meta.get("author"),
            "page_count": len(self.doc),
            "pages": pages_summary,
        }

    def render_page_to_png(
        self,
        page_number: int,
        output_path: str | Path,
        dpi: int = 200,
    ) -> Path:
        """Renders a PDF page (1-indexed) as a high-resolution PNG image."""
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page {page_number} out of range (1..{len(self.doc)})")

        page = self.doc[page_number - 1]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(output_path))
        return output_path

    def render_all_pages(
        self,
        output_dir: str | Path,
        dpi: int = 200,
    ) -> List[Path]:
        """Renders all pages of the PDF to PNG images in output_dir."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(1, len(self.doc) + 1):
            target = out_dir / f"page_{i}.png"
            paths.append(self.render_page_to_png(i, target, dpi=dpi))
        return paths

    def resolve_asset(
        self,
        page_number: int,
        bbox: List[int] | Tuple[int, int, int, int],
        output_path: str | Path,
        dpi: int = 300,
    ) -> Dict[str, Any]:
        """Resolves a visual asset to native image, vector cluster, or snapped crop."""
        from .asset_harvester import resolve_visual_asset
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page {page_number} out of range (1..{len(self.doc)})")
        page = self.doc[page_number - 1]
        return resolve_visual_asset(self.doc, page, bbox, output_path, dpi=dpi)

    def extract_region(
        self,
        page_number: int,
        bbox: List[int] | Tuple[int, int, int, int],
        output_path: str | Path,
        dpi: int = 300,
    ) -> Path:
        """Extracts a bounding box region using multi-modal asset resolution."""
        res = self.resolve_asset(page_number, bbox, output_path, dpi=dpi)
        return Path(res["image_path"])

    def get_page_typography(self, page_number: int) -> Dict[str, Any]:
        """Extracts exact page geometry, margins, and text spans from PDF content stream."""
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page {page_number} out of range (1..{len(self.doc)})")
        page = self.doc[page_number - 1]
        rect = page.rect
        text_page = page.get_text("dict")

        spans = []
        min_x, min_y = rect.width, rect.height
        max_x, max_y = 0.0, 0.0

        for block in text_page.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        b = span["bbox"]
                        min_x = min(min_x, b[0])
                        min_y = min(min_y, b[1])
                        max_x = max(max_x, b[2])
                        max_y = max(max_y, b[3])
                        spans.append({
                            "text": text,
                            "font": span["font"],
                            "size": round(span["size"], 1),
                            "flags": span["flags"],
                            "color": f"#{span['color']:06x}" if span["color"] > 0 else None,
                            "bbox": b,
                        })

        margin_left = max(24.0, min_x) if min_x < rect.width else 36.0
        margin_top = max(18.0, min_y) if min_y < rect.height else 36.0
        margin_right = max(24.0, rect.width - max_x) if max_x > 0 else 36.0
        margin_bottom = max(18.0, rect.height - max_y) if max_y > 0 else 36.0

        return {
            "page_number": page_number,
            "width_pt": rect.width,
            "height_pt": rect.height,
            "margin_left_pt": round(margin_left, 1),
            "margin_top_pt": round(margin_top, 1),
            "margin_right_pt": round(margin_right, 1),
            "margin_bottom_pt": round(margin_bottom, 1),
            "spans": spans,
        }


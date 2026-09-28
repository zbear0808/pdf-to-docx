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


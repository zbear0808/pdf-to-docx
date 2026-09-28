"""PDF Extraction utilities powered by PyMuPDF (fitz).

Handles rendering pages to high-resolution images for vision analysis,
extracting embedded images, vector drawings, and cropping bounding-box regions.
"""

from __future__ import annotations
import os
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
                "image_count": len(page.get_images()),
                "drawings_count": len(page.get_drawings()),
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
        output_path: Optional[str | Path] = None,
        dpi: int = 200,
    ) -> Path:
        """Renders a PDF page (1-indexed) as a high-resolution PNG image.

        Args:
            page_number: 1-indexed page number.
            output_path: Destination path for the PNG image.
            dpi: Rendering DPI (default 200 for Gemini multimodal analysis).
        """
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page number {page_number} out of range (1..{len(self.doc)})")

        page = self.doc[page_number - 1]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        if output_path is None:
            output_path = self.pdf_path.parent / f"{self.pdf_path.stem}_p{page_number}_{dpi}dpi.png"
        else:
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

    def extract_region(
        self,
        page_number: int,
        bbox: List[int] | Tuple[int, int, int, int],  # [ymin, xmin, ymax, xmax] 0-1000
        output_path: Optional[str | Path] = None,
        dpi: int = 300,
        format: str = "png",
    ) -> Path:
        """Crops a normalized bounding box region from a page.

        Args:
            page_number: 1-indexed page number.
            bbox: [ymin, xmin, ymax, xmax] on a 0-1000 normalized scale.
            output_path: Path to save cropped asset.
            dpi: Rendering DPI for cropped raster image.
            format: 'png' or 'svg'.
        """
        page = self.doc[page_number - 1]
        rect = page.rect
        ymin, xmin, ymax, xmax = bbox

        # Convert normalized 0-1000 coords to PDF points
        x0 = (xmin / 1000.0) * rect.width
        y0 = (ymin / 1000.0) * rect.height
        x1 = (xmax / 1000.0) * rect.width
        y1 = (ymax / 1000.0) * rect.height

        clip_rect = fitz.Rect(x0, y0, x1, y1)

        if output_path is None:
            output_path = self.pdf_path.parent / f"crop_p{page_number}_{xmin}_{ymin}.{format}"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "svg":
            # Extract page SVG and clip
            svg_text = page.get_svg_image()
            # If full svg is extracted, save it (caller can handle clipping or PyMuPDF drawing paths)
            output_path.write_text(svg_text, encoding="utf-8")
        else:
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
            pix.save(str(output_path))

        return output_path

    def extract_text_spans(self, page_number: int) -> List[Dict[str, Any]]:
        """Extracts text spans with font size, bold/italic flags, and coordinates."""
        page = self.doc[page_number - 1]
        blocks = page.get_text("dict")["blocks"]
        spans_out = []
        rect = page.rect

        for b in blocks:
            if b.get("type") == 0:  # text block
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        s_bbox = span.get("bbox", [0, 0, 0, 0])
                        # Normalize to 0-1000
                        norm_bbox = [
                            int((s_bbox[1] / rect.height) * 1000),
                            int((s_bbox[0] / rect.width) * 1000),
                            int((s_bbox[3] / rect.height) * 1000),
                            int((s_bbox[2] / rect.width) * 1000),
                        ]
                        flags = span.get("flags", 0)
                        spans_out.append({
                            "text": text,
                            "size": span.get("size", 10),
                            "font": span.get("font", ""),
                            "bold": bool(flags & 2 or "bold" in span.get("font", "").lower()),
                            "italic": bool(flags & 1 or "italic" in span.get("font", "").lower()),
                            "color": f"#{span.get('color', 0):06x}",
                            "bbox": norm_bbox,
                        })
        return spans_out

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

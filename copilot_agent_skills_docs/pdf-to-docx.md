# Skill: pdf-to-docx

## Description

_Source: `C:\Users\zubair\Documents\GitHub\pdf-to-docx\.agents\skills\pdf-to-docx\SKILL.md`

```markdown
---
name: pdf-to-docx
description: >-
  Converts PDF documents into high-fidelity, editable Word (.docx) documents using a multimodal
  Block-Based Intermediate Representation (IR), PyMuPDF asset harvesting, deterministic compilation,
  and docx-mcp integration. Runs as a sequential, single-agent workflow (no subagents). Use when asked
  to convert, extract, or transcribe a PDF to Word (.docx).
---

# PDF to Editable DOCX Conversion Skill

This skill executes a robust, battle-tested pipeline to transform complex PDF documents into fully editable Microsoft Word (`.docx`) files.

## Core Principle: Sequential Single-Agent Execution (No Subagents)

> [!IMPORTANT]
> **Do not start subagents or use agent-delegation tools** (e.g., `invoke_subagent`, `task`). Microsoft Copilot and similar environments may not support them.
>
> Process pages **one at a time in the current session**, writing each page’s outputs to disk (`_temp/specs/`, `_temp/assets/`, `_temp/renders/`) before moving to the next page. This keeps progress durable and avoids relying on parallel delegation. For long documents, resume from the next unprocessed page by checking existing `page_*_spec.json` / `page_*.md` files.

---

## 3 Conversion Pathways

| Pathway | Document Characteristics | Primary Tooling | Execution Pattern |
| :--- | :--- | :--- | :--- |
| **Pathway 1: Block-Based IR (Default)** | Corporate reports, multi-column articles, financial statements, mixed text + tables + charts + images | `pdf_to_docx` CLI AST Compiler | Extract `page_{k}_spec.json` per page sequentially; compile all specs |
| **Pathway 2: Fast-Track Markdown** | Text-heavy papers, simple documentation, standard tables, sequential reading order | Gemini GFM extraction + `docx-mcp: create_from_markdown` | Extract `page_{k}.md` per page sequentially; merge and compile |
| **Pathway 3: CodeAgent Sandbox** | Highly custom ad-hoc layouts, complex math formulas, dynamic data transformations | Direct executable Python scripts with `python-docx` | Run dedicated scripts in the current session |
| **Pathway 4: Worksheet Packer** | Worksheets, quizzes, problem sets with diagrams and answer workspaces where whitespace packing is critical | `worksheet-packer` CLI | Extracts problems, auto-crops diagrams, 2D packs into 1- or 2-column invisible tables (`w:cantSplit`). See [worksheet-packer skill](../worksheet-packer/SKILL.md). |

---

## Directory Layout & Workspace Hygiene

All document conversion workflows must isolate outputs and temporary files into standard subfolders:
```text
<document_workspace>/
├── output/                 # Final deliverables (.docx, .pdf)
└── _temp/                  # ALL temporary & intermediate working files
    ├── assets/             # Harvested/cropped images, diagrams, logos
    ├── renders/            # High-resolution rendered page PNGs (orig_p*.png, docx_p*.png)
    ├── specs/              # Extracted AST JSONs (page_*_spec.json, document_spec.json)
    └── build/              # Scratch scripts and temporary build logs
```
This guarantees that all transient files are automatically matched by gitignore rules (`**/_temp/`).

---

## Step-by-Step Execution Workflow

```
[ Single Agent / Current Session ]
       │
       ├─► 1. Inspect PDF structure (page count N, dimensions)
       ├─► 2. Render all pages to PNGs (_temp/renders/orig_p{k}.png)
       │
       ├─► 3. For each page k = 1..N (sequential)
       │         └──► Parse page k → _temp/specs/page_{k}_spec.json (or page_{k}.md) and crop assets to _temp/assets/
       │              Resume by skipping pages whose output file already exists
       │
       ├─► 4. Compile assembled specs: uv run python -m pdf_to_docx compile-pages _temp/specs/ -o output/final.docx
       │
       └─► 5. Optional QA: refine specific pages/sections in-place (no subagents)
```

---

### Phase 1: Orchestrator Intake & Page Rendering
1. Inspect the PDF structure, total page count, orientation, and vector drawings:
   ```bash
   uv run python scripts/pdf_to_docx/inspect_pdf.py path/to/document.pdf
   ```
2. Create standardized subfolders:
   ```bash
   mkdir -p output _temp/renders _temp/assets _temp/specs _temp/build
   ```
3. Render all pages to high-resolution PNG images (`200 DPI`) into `_temp/renders`:
   ```bash
   uv run python -m pdf_to_docx render-pages path/to/document.pdf -o _temp/renders
   ```

---

### Phase 2: Per-Page Extraction (Sequential)

Process each page in the current session. For every page `k` (1-indexed), run:

```bash
uv run python -m pdf_to_docx parse-page path/to/document.pdf --page {k} --image _temp/renders/orig_p{k}.png -o _temp/specs/page_{k}_spec.json --assets-dir _temp/assets
```

- After each page, inspect `_temp/specs/page_{k}_spec.json` to ensure table headers, cell values, and any charts/images are accurately captured.
- Keep a brief running note (page number, block/table/chart counts, issues) instead of dumping large JSON into chat.
- **Resume-friendly:** if `_temp/specs/page_{k}_spec.json` already exists and is valid, skip and continue.

#### Fast-Track Markdown Alternative (Pathway 2)
For text/narrative-heavy documents:
```bash
uv run python -m pdf_to_docx to-markdown-page path/to/document.pdf --page {k} --image _temp/renders/orig_p{k}.png -o _temp/specs/page_{k}.md
```

---

### Phase 3: Assembly & Compilation

Once all required page outputs exist in `_temp/specs/` (`page_*_spec.json` for Pathway 1 or `page_*.md` for Pathway 2):

#### For Pathway 1 (Block-Based IR):
Compile the assembled `page_*_spec.json` files into `.docx` in `output/`:
```bash
uv run python -m pdf_to_docx compile-pages _temp/specs/ -o output/document.docx --title "Document Title" --save-ast
```
Or use the convenience script:
```bash
uv run python scripts/pdf_to_docx/compile_pages.py _temp/specs/ -o output/document.docx --save-ast
```

The compiler deterministically enforces OpenXML structural rules:
- `w:tblHeader`: Repeats header rows across page breaks.
- `w:cantSplit`: Prevents table rows from breaking mid-cell across pages.
- Precise twip margins and cell padding.

#### For Pathway 2 (Fast-Track Markdown):
Merge page markdown files and create the document:
```bash
uv run python -m pdf_to_docx merge-markdown _temp/specs/ -o _temp/specs/document.md
```
Then use `docx-mcp`:
```text
docx-mcp: create_from_markdown(markdown_path="_temp/specs/document.md", output_path="output/document.docx")
```

---

### Phase 4: Page-Level Visual QA & Surgical Refinement

If visual validation or surgical edits are required:
1. Render output pages headlessly to compare against original rendered PNGs:
   ```bash
   uv run python scripts/pdf_to_docx/diff_layout.py _temp/renders/orig_p1.png output/document.docx
   ```
2. If a specific page (e.g. Page 2) exhibits layout issues (column clipping, chart upgrade needed), fix it **in the current session**:
   - Use the `docx-layout-refinement` skill instructions.
   - Perform surgical edits with `docx-mcp` tools (`set_column_widths`, `insert_bar_chart`, `set_cell_shading`).
   - Keep changes targeted to the affected page/element and re-check the rendered output.

---

## Detailed References

- [Intermediate Representation (IR) Schema Specification](./references/ir_schema_spec.md)
- [Conversion Workflow Playbook & Decision Matrix](./references/workflow_playbook.md)
- [docx-mcp Tooling Guide & Chart Specs](./references/docx_mcp_integration.md)

```

## Notes
Sequential single-agent workflow (no subagents). For Copilot compatibility.

## Relevant Python Code


### src\pdf_to_docx\__init__.py

```python
"""PDF to DOCX Conversion Package."""

from .ir_schema import (
    Alignment,
    BoundingBox,
    ChartBlock,
    ChartSeries,
    ChartType,
    DocumentBlock,
    DocumentSpec,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageBreakBlock,
    PageSpec,
    ParagraphBlock,
    TableBlock,
    TableCell,
    TextRun,
)
from .pdf_extractor import PDFExtractor
from .layout_parser import LayoutParser
from .docx_compiler import DocxCompiler
from .chart_generator import render_chart_image, to_docx_mcp_chart_args
from .visual_diff import VisualDiffInspector, render_docx_to_png
from .cli import app, main

__all__ = [
    "Alignment",
    "BoundingBox",
    "ChartBlock",
    "ChartSeries",
    "ChartType",
    "DocumentBlock",
    "DocumentSpec",
    "HeadingBlock",
    "ImageBlock",
    "ListType",
    "PageBreakBlock",
    "PageSpec",
    "ParagraphBlock",
    "TableBlock",
    "TableCell",
    "TextRun",
    "PDFExtractor",
    "LayoutParser",
    "DocxCompiler",
    "render_chart_image",
    "to_docx_mcp_chart_args",
    "VisualDiffInspector",
    "render_docx_to_png",
    "app",
    "main",
]

```

### src\pdf_to_docx\ir_schema.py

```python
"""Unified Intermediate Representation (IR) Schema for Document Conversion.

Defines the strongly-typed Abstract Syntax Tree (AST) representing a document.
Extracted once from the input PDF by multimodal page subagents, this canonical
format is deterministically compiled into either:
  1. Professional Word documents (.docx) via DocxCompiler
  2. Publication-grade LaTeX documents (.tex / .pdf) via LatexCompiler
"""

from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class DocumentClass(str, Enum):
    ARTICLE = "article"
    REPORT = "report"
    EXAM = "exam"
    SCRARTCL = "scrartcl"


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class ListType(str, Enum):
    BULLET = "bullet"
    NUMBERED = "numbered"
    DESCRIPTION = "description"
    NONE = "none"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"


class TextRun(BaseModel):
    """A styled fragment of text within a paragraph, table cell, or callout box."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    color_hex: Optional[str] = None  # e.g., "#1F4E79"
    font_size_pt: Optional[float] = None
    font_name: Optional[str] = None
    superscript: bool = False
    subscript: bool = False
    code: bool = False
    is_math: bool = False  # True for raw mathematical formulas (e.g. \frac{a}{b}, x_i)


class BoundingBox(BaseModel):
    """Normalized bounding box coordinates on a 0-1000 scale [ymin, xmin, ymax, xmax]."""
    ymin: int = Field(..., ge=0, le=1000)
    xmin: int = Field(..., ge=0, le=1000)
    ymax: int = Field(..., ge=0, le=1000)
    xmax: int = Field(..., ge=0, le=1000)

    @property
    def height_ratio(self) -> float:
        return (self.ymax - self.ymin) / 1000.0

    @property
    def width_ratio(self) -> float:
        return (self.xmax - self.xmin) / 1000.0


class HeadingBlock(BaseModel):
    """Section heading with hierarchical level."""
    type: str = "heading"
    level: int = Field(1, ge=1, le=4)
    text: str
    runs: Optional[List[TextRun]] = None
    alignment: Alignment = Alignment.LEFT
    numbered: bool = True
    bbox: Optional[BoundingBox] = None


class ParagraphBlock(BaseModel):
    """Narrative text block with optional runs, list formatting, and callout styling."""
    type: str = "paragraph"
    runs: List[TextRun] = Field(default_factory=list)
    alignment: Alignment = Alignment.LEFT
    list_type: ListType = ListType.NONE
    list_level: int = 0
    is_callout: bool = False
    callout_color_hex: Optional[str] = None
    line_spacing: Optional[float] = None
    space_before_pt: Optional[float] = None
    space_after_pt: Optional[float] = None
    bbox: Optional[BoundingBox] = None


class EquationBlock(BaseModel):
    """Dedicated mathematical display equation block."""
    type: str = "equation"
    latex_code: str  # Raw LaTeX math without outer delimiters, e.g. "z = \frac{x - \mu}{\sigma}"
    numbered: bool = False
    label: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class TableCell(BaseModel):
    """A single cell inside a table."""
    text: str = ""
    runs: Optional[List[TextRun]] = None
    bg_color_hex: Optional[str] = None
    bold: bool = False
    italic: bool = False
    alignment: Alignment = Alignment.LEFT
    col_span: int = 1
    row_span: int = 1


class TableBlock(BaseModel):
    """Structured table block."""
    type: str = "table"
    caption: Optional[str] = None
    headers: List[str] = Field(default_factory=list)
    header_cells: Optional[List[TableCell]] = None
    rows: List[List[str]] = Field(default_factory=list)
    row_cells: Optional[List[List[TableCell]]] = None
    col_alignments: Optional[List[Alignment]] = None
    col_widths_pct: Optional[List[float]] = None  # e.g. [30.0, 35.0, 35.0]
    cant_split: bool = True  # Prevent row break across page boundaries (Word)
    repeat_header: bool = True  # Repeat header row if table crosses page
    style_name: Optional[str] = "Table Grid"
    booktabs: bool = True  # Professional table styling (LaTeX)
    full_width: bool = False
    bbox: Optional[BoundingBox] = None


class ChartSeries(BaseModel):
    name: str
    values: List[float]


class ChartBlock(BaseModel):
    """Chart or data visualization."""
    type: str = "chart"
    title: str
    chart_type: ChartType = ChartType.BAR
    categories: List[str] = Field(default_factory=list)
    series: List[ChartSeries] = Field(default_factory=list)
    reproduce_programmatically: bool = True
    generated_image_path: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    width_inches: float = 5.5
    height_inches: float = 3.5
    caption: Optional[str] = None


class ImageBlock(BaseModel):
    """Raster image or vector drawing extracted from PDF."""
    type: str = "image"
    image_path: str = ""
    caption: Optional[str] = None
    label: Optional[str] = None
    alt_text: Optional[str] = None
    width_inches: float = 5.5
    height_inches: Optional[float] = None
    width_ratio: float = 0.8
    alignment: Alignment = Alignment.CENTER
    bbox: Optional[BoundingBox] = None
    is_vector: bool = False


class BoxBlock(BaseModel):
    """Framed callout or response box (tcolorbox in LaTeX / shaded frame in Word)."""
    type: str = "box"
    title: Optional[str] = None
    content: List[ParagraphBlock] = Field(default_factory=list)
    color_hex: str = "#1F4E79"
    height_pt: Optional[float] = None
    empty_for_response: bool = False
    bbox: Optional[BoundingBox] = None


class QuestionChoice(BaseModel):
    """Multiple choice option."""
    label: str  # "(A)", "(B)", "(C)", etc.
    text: str
    runs: Optional[List[TextRun]] = None


class QuestionBlock(BaseModel):
    """Specialized block for exam / quiz problems."""
    type: str = "question"
    number: Optional[int] = None
    part: Optional[str] = None  # "a", "b", "c", etc.
    points: Optional[int] = None
    prompt: List[ParagraphBlock] = Field(default_factory=list)
    choices: Optional[List[QuestionChoice]] = None
    response_box_height_pt: Optional[float] = None
    solution: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class CodeBlock(BaseModel):
    """Verbatim or syntax-highlighted code block."""
    type: str = "code"
    language: Optional[str] = None
    code: str
    caption: Optional[str] = None


class PageBreakBlock(BaseModel):
    """Explicit page break."""
    type: str = "page_break"


DocumentBlock = Union[
    HeadingBlock,
    ParagraphBlock,
    EquationBlock,
    TableBlock,
    ChartBlock,
    ImageBlock,
    BoxBlock,
    QuestionBlock,
    CodeBlock,
    PageBreakBlock,
]


class PageSpec(BaseModel):
    """Specification for a single document page."""
    page_number: int
    width_pt: float = 612.0  # Standard letter (8.5 x 11 in points)
    height_pt: float = 792.0
    orientation: str = "portrait"  # portrait | landscape
    margin_top_pt: Optional[float] = None
    margin_bottom_pt: Optional[float] = None
    margin_left_pt: Optional[float] = None
    margin_right_pt: Optional[float] = None
    blocks: List[DocumentBlock] = Field(default_factory=list)


class DocumentSpec(BaseModel):
    """Root canonical representation of the entire document."""
    title: str = "Converted Document"
    author: Optional[str] = None
    company: Optional[str] = None
    date: Optional[str] = None
    document_class: DocumentClass = DocumentClass.ARTICLE
    font_size: str = "11pt"
    paper_size: str = "letterpaper"
    margins_in: float = 1.0
    theme_hex: str = "#1F4E79"
    default_font: str = "Calibri"
    default_font_size_pt: float = 11.0
    custom_preamble: Optional[str] = None
    pages: List[PageSpec] = Field(default_factory=list)


```

### src\pdf_to_docx\pdf_extractor.py

```python
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

```

### src\pdf_to_docx\layout_parser.py

```python
"""Unified Multimodal Layout Parser using Gemini 2.5 Flash.

Interprets rendered PDF page images, performs spatial layout decomposition,
and produces strongly-typed PageSpec / DocumentSpec AST instances.
Supports both Markdown fast-track (for DOCX) and LaTeX fragment fast-track (for LaTeX).
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from .ir_schema import (
    Alignment,
    BoundingBox,
    BoxBlock,
    ChartBlock,
    ChartSeries,
    ChartType,
    CodeBlock,
    DocumentBlock,
    DocumentSpec,
    EquationBlock,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageSpec,
    ParagraphBlock,
    QuestionBlock,
    QuestionChoice,
    TableBlock,
    TableCell,
    TextRun,
)


LAYOUT_EXTRACTION_PROMPT = """Analyze this document page image and output a precise structured JSON matching the PageSpec schema.

Guidelines:
1. Deconstruct the layout into logical blocks in reading order: headings, paragraphs, equations, tables, charts, images, boxes, or questions.
2. For HEADINGS: Identify hierarchical level (1-4), text, alignment, and bounding box [ymin, xmin, ymax, xmax] (0-1000 scale).
3. For PARAGRAPHS: Preserve typography (bold, italic, colors), detect if it's a bullet list or numbered list, and identify callouts/highlights.
4. For MATHEMATICAL FORMULAS & SYMBOLS:
   - Inline math: Set TextRun.is_math = true or enclose in $...$ (e.g. $z = \\frac{x - \\mu}{\\sigma}$, $\\bar{x}$, $\\sigma^2$, $\\hat{p}$).
   - Display equations: Use EquationBlock with latex_code.
   - Preserve all Greek letters, fractions, superscripts, subscripts, summations, integrals.
5. For EXAM & QUIZ QUESTIONS:
   - If this is an exam, test, or problem set, use QuestionBlock with number, points, prompt, multiple choice options, and response_box_height_pt.
6. For TABLES: Extract full tabular structure with headers and rows. Preserve exact mathematical symbols, numbers, and units.
7. For CHARTS: Identify chart type (bar, line, pie), extract the title, category labels, and series data values so it can be re-rendered programmatically. Also provide bbox.
8. For FIGURES / IMAGES / LOGOS / SIGNATURES: Provide bounding box [ymin, xmin, ymax, xmax] (0-1000 scale) so they can be cropped from the PDF.
9. For CALLOUT / FRAMED BOXES: Use BoxBlock with title and content.
10. Set page orientation to 'portrait' or 'landscape'.
"""


FAST_TRACK_LATEX_PROMPT = """Convert this document page image directly into a clean, modular LaTeX body fragment suitable for \\input{...}.

Formatting Rules:
1. Do NOT include \\documentclass, \\begin{document}, or preamble. Output ONLY the body content for this page.
2. Mathematics: Use proper LaTeX math environments ($...$ for inline, \\[...\\] or \\begin{equation} for display math, \\frac, \\sqrt, Greek letters, etc.).
3. Headings: Use \\section*, \\subsection*, \\subsubsection*.
4. Tables: Use clean booktabs formatting (\\begin{table}[htbp] \\centering \\begin{tabular}{...} \\toprule ... \\midrule ... \\bottomrule \\end{tabular} \\end{table}).
5. Exam / Quiz Questions: Format with \\paragraph{Question X} or \\question, multiple choices with enumerate or choices environment, and empty response boxes using \\begin{tcolorbox}[height=...cm] or \\makeemptybox{...}.
6. Figures / Diagrams: If there is a visual image or diagram, mark it as \\begin{figure}[htbp] \\centering \\includegraphics[width=0.8\\linewidth]{assets/p{PAGE}_asset.png} \\caption{...} \\end{figure}.
7. Do NOT include Markdown backticks (```latex) or conversational commentary.
"""


class LayoutParser:
    """Invokes Gemini Flash multimodal vision model to parse page layouts."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-flash-lite-latest"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            import logging
            logging.getLogger("google_genai.models").addFilter(
                lambda record: "automatic function calling (AFC)" not in record.getMessage()
            )
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            else:
                self._client = genai.Client()
        return self._client

    def parse_page_image(self, image_path: str | Path, page_number: int = 1) -> PageSpec:
        """Parses a rendered page image using Gemini Flash into a unified PageSpec AST."""
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")

        img_bytes = img_path.read_bytes()

        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                LAYOUT_EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PageSpec,
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        try:
            parsed_json = json.loads(response.text)
            spec = PageSpec.model_validate(parsed_json)
            spec.page_number = page_number
            return spec
        except (json.JSONDecodeError, ValidationError) as e:
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()
            parsed_json = json.loads(raw_text)
            spec = PageSpec.model_validate(parsed_json)
            spec.page_number = page_number
            return spec

    def parse_markdown_fast_path(self, image_path: str | Path) -> str:
        """Fast-track parsing: Converts a page image directly into GitHub-Flavored Markdown (for Word)."""
        img_path = Path(image_path)
        img_bytes = img_path.read_bytes()

        from google.genai import types

        prompt = (
            "Convert this document page into clean GitHub-Flavored Markdown (GFM). "
            "Preserve all headings (#, ##), bold, italics, bullet lists, numbered lists, "
            "and standard markdown tables (| Header | ... |). Do not include conversational text or enclosing ```markdown blocks."
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        return response.text.strip()

    def parse_latex_fast_path(self, image_path: str | Path, page_number: int = 1) -> str:
        """Fast-track parsing: Converts a page image directly into a LaTeX fragment (.tex)."""
        img_path = Path(image_path)
        img_bytes = img_path.read_bytes()

        from google.genai import types

        prompt = FAST_TRACK_LATEX_PROMPT.replace("{PAGE}", str(page_number))

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        text = response.text.strip()
        if text.startswith("```latex"):
            text = text.split("```latex", 1)[1].split("```", 1)[0].strip()
        elif text.startswith("```tex"):
            text = text.split("```tex", 1)[1].split("```", 1)[0].strip()
        elif text.startswith("```"):
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        return text


```

### src\pdf_to_docx\docx_compiler.py

```python
"""Deterministic DOCX Compiler.

Transforms a DocumentSpec AST into a production-grade Word document (.docx).
Enforces OpenXML rules for repeating table headers (w:tblHeader), atomic table rows
(w:cantSplit), twip-precise column layouts, and robust typography.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, List, Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from .ir_schema import (
    Alignment,
    BoxBlock,
    ChartBlock,
    CodeBlock,
    DocumentBlock,
    DocumentSpec,
    EquationBlock,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageBreakBlock,
    PageSpec,
    ParagraphBlock,
    QuestionBlock,
    TableBlock,
    TableCell,
    TextRun,
)
from .chart_generator import render_chart_image


def hex_to_rgb(hex_str: str) -> RGBColor:
    """Converts hex color string (#RRGGBB) to docx RGBColor."""
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    r = int(hex_clean[0:2], 16)
    g = int(hex_clean[2:4], 16)
    b = int(hex_clean[4:6], 16)
    return RGBColor(r, g, b)


def set_cell_background(cell, hex_color: str):
    """Sets background shading of a table cell via OpenXML."""
    hex_clean = hex_color.lstrip("#")
    tcPr = cell._tc.get_or_add_tcPr()
    # Remove existing shading if present
    shd = tcPr.find(qn("w:shd"))
    if shd is not None:
        tcPr.remove(shd)
    shd_element = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_clean}" w:val="clear"/>')
    tcPr.append(shd_element)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    """Sets cell padding in twips (1/20th of a point)."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def make_row_cant_split(row):
    """Prevents a table row from breaking mid-cell across a page boundary (w:cantSplit)."""
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:cantSplit")) is None:
        trPr.append(OxmlElement("w:cantSplit"))


def make_row_header(row):
    """Repeats this table row at the top of each page if the table splits (w:tblHeader)."""
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:tblHeader")) is None:
        trPr.append(OxmlElement("w:tblHeader"))


class DocxCompiler:
    """Compiles a canonical DocumentSpec AST into a formatted Word (.docx) file."""

    def __init__(self, spec: DocumentSpec):
        self.spec = spec
        self.doc = Document()
        self._configure_styles()

    def _configure_styles(self):
        """Sets up default typographic styles with corporate theme colors."""
        normal_style = self.doc.styles["Normal"]
        font = normal_style.font
        font.name = self.spec.default_font
        font.size = Pt(self.spec.default_font_size_pt)
        font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        normal_style.paragraph_format.line_spacing = 1.05
        normal_style.paragraph_format.space_after = Pt(2)

    def _apply_page_geometry(self, section, page: PageSpec):
        """Applies exact PDF page dimensions and margins to Word section."""
        if page.width_pt and page.height_pt:
            section.page_width = Pt(page.width_pt)
            section.page_height = Pt(page.height_pt)

        if page.orientation == "landscape":
            from docx.enum.section import WD_ORIENTATION
            section.orientation = WD_ORIENTATION.LANDSCAPE
            if page.width_pt and page.height_pt and page.width_pt < page.height_pt:
                section.page_width = Pt(page.height_pt)
                section.page_height = Pt(page.width_pt)

        top_m = page.margin_top_pt if page.margin_top_pt is not None else (self.spec.margins_in * 72 if self.spec.margins_in else 36.0)
        btm_m = page.margin_bottom_pt if page.margin_bottom_pt is not None else (self.spec.margins_in * 72 if self.spec.margins_in else 36.0)
        left_m = page.margin_left_pt if page.margin_left_pt is not None else (self.spec.margins_in * 72 if self.spec.margins_in else 40.0)
        right_m = page.margin_right_pt if page.margin_right_pt is not None else (self.spec.margins_in * 72 if self.spec.margins_in else 40.0)

        section.top_margin = Pt(max(18.0, float(top_m)))
        section.bottom_margin = Pt(max(18.0, float(btm_m)))
        section.left_margin = Pt(max(24.0, float(left_m)))
        section.right_margin = Pt(max(24.0, float(right_m)))

    def compile(self, output_docx_path: str | Path, assets_dir: Optional[str | Path] = None) -> Path:
        """Executes full compilation and writes output file."""
        out_path = Path(output_docx_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        assets_path = Path(assets_dir) if assets_dir else out_path.parent / "assets"
        assets_path.mkdir(parents=True, exist_ok=True)

        if self.spec.pages:
            self._apply_page_geometry(self.doc.sections[0], self.spec.pages[0])

        for page_idx, page in enumerate(self.spec.pages):
            if page_idx > 0:
                prev_page = self.spec.pages[page_idx - 1]
                need_new_section = (
                    page.orientation != prev_page.orientation
                    or abs((page.width_pt or 612) - (prev_page.width_pt or 612)) > 10
                    or abs((page.height_pt or 792) - (prev_page.height_pt or 792)) > 10
                )
                if need_new_section:
                    sec = self.doc.add_section()
                    self._apply_page_geometry(sec, page)
                else:
                    self.doc.add_page_break()

            for block in page.blocks:
                self._render_block(block, assets_path)

        self.doc.save(str(out_path))
        return out_path

    def _render_block(self, block: DocumentBlock, assets_path: Path):
        b_type = getattr(block, "type", "")

        if b_type == "heading":
            self._render_heading(block)  # type: ignore
        elif b_type == "paragraph":
            self._render_paragraph(block)  # type: ignore
        elif b_type == "table":
            self._render_table(block)  # type: ignore
        elif b_type == "chart":
            self._render_chart(block, assets_path)  # type: ignore
        elif b_type == "image":
            self._render_image(block)  # type: ignore
        elif b_type == "equation":
            self._render_equation(block)  # type: ignore
        elif b_type == "box":
            self._render_box(block)  # type: ignore
        elif b_type == "question":
            self._render_question(block)  # type: ignore
        elif b_type == "code":
            self._render_code(block)  # type: ignore
        elif b_type == "page_break":
            self.doc.add_page_break()

    def _render_heading(self, h: HeadingBlock):
        p = self.doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(max(4, 14 - (h.level * 2)))
        p.paragraph_format.space_after = Pt(3)

        if h.alignment == Alignment.CENTER:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif h.alignment == Alignment.RIGHT:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT

        if h.runs:
            for run in h.runs:
                self._apply_run(p.add_run(run.text), run, is_heading=True, level=h.level)
        else:
            run = p.add_run(h.text)
            run.bold = True
            run.font.size = Pt(max(12, 18 - (h.level * 2)))
            run.font.color.rgb = hex_to_rgb(self.spec.theme_hex)

    def _render_paragraph(self, p_block: ParagraphBlock):
        p = self.doc.add_paragraph()

        # Handle list styles
        if p_block.list_type == ListType.BULLET:
            p.style = "List Bullet"
        elif p_block.list_type == ListType.NUMBERED:
            p.style = "List Number"

        # Handle callout styling
        if p_block.is_callout:
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.right_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(4)
            p.paragraph_format.space_after = Pt(4)
        elif p_block.space_before_pt is not None:
            p.paragraph_format.space_before = Pt(p_block.space_before_pt)

        if p_block.space_after_pt is not None:
            p.paragraph_format.space_after = Pt(p_block.space_after_pt)
        else:
            p.paragraph_format.space_after = Pt(2)

        if p_block.line_spacing is not None:
            p.paragraph_format.line_spacing = p_block.line_spacing

        # Handle alignment
        if p_block.alignment == Alignment.CENTER:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif p_block.alignment == Alignment.RIGHT:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif p_block.alignment == Alignment.JUSTIFY:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

        for r_spec in p_block.runs:
            self._apply_run(p.add_run(r_spec.text), r_spec)

    def _render_equation(self, eq: EquationBlock):
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        code = eq.latex_code.strip()
        for delim in ("$$", "\\[", "\\]"):
            code = code.replace(delim, "").strip()
        run = p.add_run(code)
        run.italic = True
        run.font.name = "Cambria Math"

    def _render_box(self, box: BoxBlock):
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_margins(cell, top=100, bottom=100, left=140, right=140)
        border_color = box.color_hex.lstrip("#") if box.color_hex else "444444"
        borders = parse_xml(
            f'<w:tcBorders {nsdecls("w")}>\n'
            f'  <w:top w:val="single" w:sz="8" w:space="0" w:color="{border_color}"/>\n'
            f'  <w:left w:val="single" w:sz="8" w:space="0" w:color="{border_color}"/>\n'
            f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="{border_color}"/>\n'
            f'  <w:right w:val="single" w:sz="8" w:space="0" w:color="{border_color}"/>\n'
            f'</w:tcBorders>'
        )
        cell._tc.get_or_add_tcPr().append(borders)
        if box.title:
            p0 = cell.paragraphs[0]
            p0.paragraph_format.space_after = Pt(2)
            r = p0.add_run(box.title)
            r.bold = True
        first_p = not bool(box.title)
        for p_spec in box.content:
            p = cell.paragraphs[0] if first_p else cell.add_paragraph()
            first_p = False
            p.paragraph_format.space_after = Pt(2)
            for r_spec in p_spec.runs:
                self._apply_run(p.add_run(r_spec.text), r_spec)
        if box.empty_for_response:
            table.rows[0].height = Pt(box.height_pt or 100.0)

    def _render_question(self, q: QuestionBlock):
        q_prefix = ""
        if q.number is not None:
            q_prefix = f"{q.number}. "
        if q.part:
            q_prefix += f"({q.part}) "
        for i, p_spec in enumerate(q.prompt):
            p = self.doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            if i == 0 and q_prefix:
                r_pre = p.add_run(q_prefix)
                r_pre.bold = True
            for r_spec in p_spec.runs:
                self._apply_run(p.add_run(r_spec.text), r_spec)
        if q.choices:
            for c in q.choices:
                p_ch = self.doc.add_paragraph()
                p_ch.paragraph_format.left_indent = Inches(0.25)
                p_ch.paragraph_format.space_after = Pt(2)
                r_lbl = p_ch.add_run(f"{c.label} ")
                r_lbl.bold = True
                if c.runs:
                    for r_spec in c.runs:
                        self._apply_run(p_ch.add_run(r_spec.text), r_spec)
                else:
                    p_ch.add_run(c.text)
        if q.response_box_height_pt and q.response_box_height_pt > 0:
            self._render_box(BoxBlock(height_pt=q.response_box_height_pt, empty_for_response=True))

    def _render_code(self, code_block: CodeBlock):
        table = self.doc.add_table(rows=1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        cell = table.cell(0, 0)
        set_cell_background(cell, "#F4F5F7")
        set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        run = p.add_run(code_block.code)
        run.font.name = "Consolas"
        run.font.size = Pt(9.5)

    def _apply_run(self, docx_run, r_spec: TextRun, is_heading: bool = False, level: int = 1):
        docx_run.bold = r_spec.bold
        docx_run.italic = r_spec.italic
        docx_run.underline = r_spec.underline
        docx_run.font.strike = r_spec.strike

        if r_spec.font_size_pt:
            docx_run.font.size = Pt(r_spec.font_size_pt)
        elif is_heading:
            docx_run.font.size = Pt(max(12, 22 - (level * 2)))

        if r_spec.color_hex:
            docx_run.font.color.rgb = hex_to_rgb(r_spec.color_hex)
        elif is_heading:
            docx_run.font.color.rgb = hex_to_rgb(self.spec.theme_hex)

        if r_spec.font_name:
            docx_run.font.name = r_spec.font_name

    def _render_table(self, tbl: TableBlock):
        all_rows = []
        if tbl.headers:
            all_rows.append(tbl.headers)
        all_rows.extend(tbl.rows)

        if not all_rows:
            return

        num_rows = len(all_rows)
        num_cols = max(len(r) for r in all_rows)

        table = self.doc.add_table(rows=num_rows, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        if tbl.style_name:
            try:
                table.style = tbl.style_name
            except Exception:
                table.style = "Table Grid"

        # Apply header formatting & OOXML rules
        for row_idx, row_data in enumerate(all_rows):
            doc_row = table.rows[row_idx]

            # Enforce atomic rows (never split across pages)
            if tbl.cant_split:
                make_row_cant_split(doc_row)

            # Enforce header row repetition
            is_header = row_idx == 0 and bool(tbl.headers)
            if is_header and tbl.repeat_header:
                make_row_header(doc_row)

            for col_idx in range(num_cols):
                cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
                cell = doc_row.cells[col_idx]
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_margins(cell, top=120, bottom=120, left=140, right=140)

                # Clear default paragraph
                p = cell.paragraphs[0]
                p.text = ""
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0

                run = p.add_run(cell_text)

                if is_header:
                    run.bold = True
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    run.font.size = Pt(10)
                    set_cell_background(cell, self.spec.theme_hex)
                else:
                    run.font.size = Pt(9.5)
                    # Alternate row shading for readability
                    if row_idx % 2 == 1:
                        set_cell_background(cell, "#F7F9FB")

        # Explicit column widths if available
        if tbl.col_widths_pct and len(tbl.col_widths_pct) == num_cols:
            total_width = Inches(6.5)  # Standard printable width on 8.5" page with 1" margins
            for col_idx, pct in enumerate(tbl.col_widths_pct):
                col_w = total_width * (pct / 100.0)
                for row in table.rows:
                    row.cells[col_idx].width = col_w

    def _render_chart(self, chart: ChartBlock, assets_path: Path):
        chart_img_path = chart.generated_image_path
        if not chart_img_path or not Path(chart_img_path).exists():
            chart_filename = f"chart_{id(chart)}.png"
            chart_img_path = str(assets_path / chart_filename)
            render_chart_image(chart, chart_img_path)

        if not Path(chart_img_path).exists():
            return

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(6)
        self.doc.add_picture(str(chart_img_path), width=Inches(min(6.0, chart.width_inches)))

    def _render_image(self, img: ImageBlock):
        if not img.image_path or not Path(img.image_path).exists():
            return

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)

        w = Inches(img.width_inches) if img.width_inches else Inches(5.5)
        h = Inches(img.height_inches) if img.height_inches else None
        if h:
            self.doc.add_picture(img.image_path, width=w, height=h)
        else:
            self.doc.add_picture(img.image_path, width=w)

        if img.caption:
            cap_p = self.doc.add_paragraph()
            cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap_p.paragraph_format.space_before = Pt(2)
            cap_p.paragraph_format.space_after = Pt(6)
            run = cap_p.add_run(img.caption)
            run.italic = True
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

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

### src\pdf_to_docx\visual_diff.py

```python
"""Visual Diff and Self-Correction Engine.

Renders compiled DOCX documents headlessly and utilizes Gemini Flash vision
to inspect visual fidelity against original PDF page images.
"""

from __future__ import annotations
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import pymupdf as fitz
from pydantic import BaseModel, Field


class Discrepancy(BaseModel):
    category: str = Field(..., description="typography, table, chart, layout, image, margins")
    description: str
    severity: str = Field("medium", description="low, medium, high, critical")
    suggested_fix: str


class VisualCritique(BaseModel):
    fidelity_score: int = Field(..., ge=0, le=100, description="Overall layout fidelity score from 0 to 100")
    page_number: int
    matches_well: List[str] = Field(default_factory=list)
    discrepancies: List[Discrepancy] = Field(default_factory=list)
    actionable_adjustments: Dict[str, Any] = Field(default_factory=dict)


def render_docx_to_png(
    docx_path: str | Path,
    output_png_path: str | Path,
    page_number: int = 1,
    dpi: int = 200,
) -> Optional[Path]:
    """Attempts to render a DOCX page to PNG via available headless tools.

    Tries:
    1. LibreOffice ('soffice' or 'libreoffice' on PATH)
    2. Windows MS Word COM automation (if on Windows with Office installed)
    """
    docx_file = Path(docx_path).resolve()
    out_png = Path(output_png_path).resolve()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = out_png.parent / ".temp_render"
    temp_dir.mkdir(parents=True, exist_ok=True)
    pdf_out = temp_dir / f"{docx_file.stem}.pdf"

    converted = False

    # 1. Try LibreOffice CLI
    soffice_cmd = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice_cmd:
        # Check standard Windows paths
        win_candidates = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        ]
        for c in win_candidates:
            if c.exists():
                soffice_cmd = str(c)
                break

    if soffice_cmd:
        try:
            subprocess.run(
                [soffice_cmd, "--headless", "--convert-to", "pdf", str(docx_file), "--outdir", str(temp_dir)],
                check=True,
                capture_output=True,
                timeout=60,
            )
            if pdf_out.exists():
                converted = True
        except Exception:
            pass

    # 2. Try Windows Word COM if LibreOffice unavailable
    if not converted and os.name == "nt":
        try:
            import win32com.client  # type: ignore
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(str(docx_file))
            # 17 = wdFormatPDF
            doc.SaveAs(str(pdf_out), FileFormat=17)
            doc.Close()
            word.Quit()
            if pdf_out.exists():
                converted = True
        except Exception:
            pass

    if not converted or not pdf_out.exists():
        return None

    # Render PDF page to PNG using PyMuPDF
    doc = fitz.open(str(pdf_out))
    if page_number > len(doc):
        page_number = 1
    page = doc[page_number - 1]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(out_png))
    doc.close()

    # Clean up temp PDF
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    return out_png


DIFF_PROMPT = """You are a document layout QA expert. Compare these two images side-by-side:
Image 1: ORIGINAL PDF PAGE (Reference standard)
Image 2: GENERATED WORD (.DOCX) PAGE (Compiled output)

Perform a meticulous layout discrepancy analysis:
1. Typography & Hierarchy: Are heading sizes, weights, and colors faithfully reproduced?
2. Tables: Are table columns properly proportioned, borders crisp, cell padding balanced, headers distinct?
3. Charts & Figures: Are chart dimensions, titles, and legends placed accurately?
4. Page Flow: Did any content overflow or wrap awkwardly?
5. Assign a fidelity score from 0-100 and provide clear, actionable suggestions to adjust the styling AST or docx-mcp properties.
"""


class VisualDiffInspector:
    """Uses Gemini multimodal capabilities to critique and guide self-correction."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            import logging
            logging.getLogger("google_genai.models").addFilter(
                lambda record: "automatic function calling (AFC)" not in record.getMessage()
            )
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            else:
                self._client = genai.Client()
        return self._client

    def inspect_and_critique(
        self,
        original_image_path: str | Path,
        rendered_image_path: str | Path,
        page_number: int = 1,
    ) -> VisualCritique:
        """Sends original vs rendered DOCX page to Gemini Flash for critique."""
        from google.genai import types

        orig_bytes = Path(original_image_path).read_bytes()
        rend_bytes = Path(rendered_image_path).read_bytes()

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=orig_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=rend_bytes, mime_type="image/png"),
                DIFF_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VisualCritique,
                temperature=0.2,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        try:
            data = json.loads(response.text)
            critique = VisualCritique.model_validate(data)
            critique.page_number = page_number
            return critique
        except Exception:
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()
            data = json.loads(raw_text)
            critique = VisualCritique.model_validate(data)
            critique.page_number = page_number
            return critique

```

### src\pdf_to_docx\cli.py

```python
"""Command-line interface for PDF to DOCX conversion."""

from __future__ import annotations
import json
from pathlib import Path
import re
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table

from .ir_schema import DocumentSpec, PageSpec
from .pdf_extractor import PDFExtractor
from .layout_parser import LayoutParser
from .docx_compiler import DocxCompiler
from .visual_diff import VisualDiffInspector, render_docx_to_png

app = typer.Typer(help="Autonomous, high-fidelity PDF to editable Word (.docx) converter.")
console = Console()


@app.command()
def info(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
):
    """Inspects PDF structure, dimensions, and visual elements."""
    with PDFExtractor(pdf_path) as extractor:
        doc_info = extractor.get_document_info()

    console.print(f"[bold cyan]Document:[/] {doc_info['title']} ({doc_info['page_count']} pages)")
    table = Table(title="Pages Overview")
    table.add_column("Page #", justify="center")
    table.add_column("Dimensions (pt)")
    table.add_column("Orientation")
    table.add_column("Images", justify="right")
    table.add_column("Drawings", justify="right")

    for p in doc_info["pages"]:
        table.add_row(
            str(p["page_number"]),
            f"{p['width_pt']:.1f} x {p['height_pt']:.1f}",
            p["orientation"],
            str(p["image_count"]),
            str(p["drawings_count"]),
        )
    console.print(table)


@app.command()
def render_pages(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory for rendered PNGs"),
    dpi: int = typer.Option(200, "--dpi", help="Rendering resolution"),
):
    """Renders all PDF pages to high-resolution PNG images."""
    target_dir = output_dir or (Path("./rendered_pages") / pdf_path.stem)
    with PDFExtractor(pdf_path) as extractor:
        paths = extractor.render_all_pages(target_dir, dpi=dpi)
    console.print(f"[green]Successfully rendered {len(paths)} pages to {target_dir}[/]")


@app.command()
def crop(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(1, "--page", "-p", help="Page number (1-indexed)"),
    bbox: str = typer.Option(..., "--bbox", help="Normalized bbox as 'ymin,xmin,ymax,xmax' (0-1000)"),
    output_path: Path = typer.Option(Path("cropped_asset.png"), "--output", "-o"),
    dpi: int = typer.Option(300, "--dpi"),
):
    """Crops a specific bounding box region from a PDF page."""
    coords = [int(x.strip()) for x in bbox.split(",")]
    if len(coords) != 4:
        raise typer.BadParameter("BBox must have 4 comma-separated integers: ymin,xmin,ymax,xmax")

    with PDFExtractor(pdf_path) as extractor:
        out = extractor.extract_region(page, coords, output_path=output_path, dpi=dpi)
    console.print(f"[green]Cropped region saved to {out}[/]")


@app.command()
def parse_page(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(..., "--page", "-p", help="Page number (1-indexed)"),
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="Path to pre-rendered page PNG"),
    output_spec: Path = typer.Option(..., "--output", "-o", help="Output PageSpec JSON path"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Directory for cropped assets"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution if rendering"),
):
    """Parses a single PDF page into a PageSpec JSON and crops assets (designed for page subagents)."""
    resolved_assets = assets_dir or (output_spec.parent / "assets")
    resolved_assets.mkdir(parents=True, exist_ok=True)
    output_spec.parent.mkdir(parents=True, exist_ok=True)

    with PDFExtractor(pdf_path) as extractor:
        if image and image.exists():
            page_png = image
        else:
            temp_dir = output_spec.parent / ".temp_renders"
            temp_dir.mkdir(parents=True, exist_ok=True)
            page_png = extractor.render_page_to_png(page, temp_dir / f"orig_p{page}.png", dpi=dpi)

        console.print(f"[cyan]Parsing layout structure for page {page}...[/]")
        parser = LayoutParser()
        page_spec = parser.parse_page_image(page_png, page_number=page)

        # Backfill exact typography and margins from PDF content stream
        try:
            typo = extractor.get_page_typography(page)
            page_spec.width_pt = typo.get("width_pt", page_spec.width_pt)
            page_spec.height_pt = typo.get("height_pt", page_spec.height_pt)
            page_spec.margin_top_pt = typo.get("margin_top_pt")
            page_spec.margin_bottom_pt = typo.get("margin_bottom_pt")
            page_spec.margin_left_pt = typo.get("margin_left_pt")
            page_spec.margin_right_pt = typo.get("margin_right_pt")

            pdf_spans = typo.get("spans", [])
            for block in page_spec.blocks:
                runs = getattr(block, "runs", None) or []
                for run in runs:
                    if getattr(run, "font_size_pt", None) is None or not getattr(run, "font_name", None):
                        r_txt = getattr(run, "text", "").strip()
                        for s in pdf_spans:
                            if s["text"] in r_txt or r_txt in s["text"]:
                                if getattr(run, "font_size_pt", None) is None:
                                    run.font_size_pt = s["size"]
                                if not getattr(run, "font_name", None):
                                    run.font_name = s["font"]
                                break
        except Exception as typo_err:
            console.print(f"[dim yellow]Typography backfilling skipped: {typo_err}[/]")

        # Crop any image/figure blocks flagged with bbox
        for b_idx, block in enumerate(page_spec.blocks):
            if getattr(block, "type", "") == "image" and block.bbox:  # type: ignore
                crop_dest = resolved_assets / f"p{page}_img{b_idx}.png"
                extractor.extract_region(
                    page,
                    [block.bbox.ymin, block.bbox.xmin, block.bbox.ymax, block.bbox.xmax],  # type: ignore
                    output_path=crop_dest,
                    dpi=300,
                )
                block.image_path = str(crop_dest)  # type: ignore

    output_spec.write_text(page_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]Page {page} AST saved to:[/] {output_spec}")


@app.command()
def compile_pages(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*_spec.json files"),
    output_docx: Path = typer.Option(Path("output.docx"), "--output", "-o", help="Output DOCX path"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex", help="Corporate theme color hex"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save the merged DocumentSpec AST JSON alongside the exported file"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path to save the DocumentSpec AST JSON"),
):
    """Compiles multiple PageSpec JSON files from a workspace directory into a single Word (.docx) file."""
    if pages_dir.is_dir():
        spec_files = sorted(
            [f for f in pages_dir.glob("page_*_spec.json") if not f.name.endswith("_merged_ast.json")],
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
        if not spec_files:
            spec_files = sorted(
                [f for f in pages_dir.glob("*.json") if not f.name.endswith("_merged_ast.json") and not f.name.endswith("_ast.json")],
                key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
            )
    elif pages_dir.is_file():
        spec_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not spec_files:
        raise typer.BadParameter(f"No PageSpec JSON files found in {pages_dir}")

    console.print(f"[cyan]Found {len(spec_files)} page spec(s) to compile in order:[/]")
    for sf in spec_files:
        console.print(f"  - {sf.name}")

    pages = []
    for f in spec_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        pages.append(PageSpec.model_validate(data))

    doc_spec = DocumentSpec(title=title, theme_hex=theme_hex, pages=pages)

    if save_ast or ast_path is not None:
        target_ast = ast_path or (output_docx.parent / f"{output_docx.stem}_ast.json")
        target_ast.parent.mkdir(parents=True, exist_ok=True)
        target_ast.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[dim]DocumentSpec AST saved to: {target_ast}[/]")

    # Resolve assets directory if not provided
    resolved_assets = assets_dir
    if resolved_assets is None and pages_dir.is_dir() and (pages_dir / "assets").exists():
        resolved_assets = pages_dir / "assets"

    compiler = DocxCompiler(doc_spec)
    out = compiler.compile(output_docx, assets_dir=resolved_assets)
    console.print(f"[bold green]Successfully compiled {len(pages)} pages to:[/] {out}")


@app.command()
def merge_specs(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*_spec.json files"),
    output_spec: Path = typer.Option(Path("merged_spec.json"), "--output", "-o", help="Output merged DocumentSpec JSON path"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex", help="Corporate theme color hex"),
):
    """Merges individual PageSpec JSON files into a single DocumentSpec AST JSON."""
    if pages_dir.is_dir():
        spec_files = sorted(
            [f for f in pages_dir.glob("page_*_spec.json") if not f.name.endswith("_merged_ast.json")],
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
        if not spec_files:
            spec_files = sorted(
                [f for f in pages_dir.glob("*.json") if not f.name.endswith("_merged_ast.json") and not f.name.endswith("_ast.json")],
                key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
            )
    elif pages_dir.is_file():
        spec_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not spec_files:
        raise typer.BadParameter(f"No PageSpec JSON files found in {pages_dir}")

    pages = [PageSpec.model_validate(json.loads(f.read_text(encoding="utf-8"))) for f in spec_files]
    doc_spec = DocumentSpec(title=title, theme_hex=theme_hex, pages=pages)
    output_spec.parent.mkdir(parents=True, exist_ok=True)
    output_spec.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]Successfully merged {len(pages)} pages into:[/] {output_spec}")


@app.command()
def to_markdown_page(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(..., "--page", "-p", help="Page number (1-indexed)"),
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="Path to pre-rendered page PNG"),
    output_md: Path = typer.Option(..., "--output", "-o", help="Output Markdown path"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution if rendering"),
):
    """Fast-track: Converts a single page to clean GFM Markdown (designed for page subagents)."""
    output_md.parent.mkdir(parents=True, exist_ok=True)
    with PDFExtractor(pdf_path) as extractor:
        if image and image.exists():
            page_png = image
        else:
            temp_dir = output_md.parent / ".temp_renders"
            temp_dir.mkdir(parents=True, exist_ok=True)
            page_png = extractor.render_page_to_png(page, temp_dir / f"p{page}.png", dpi=dpi)

        console.print(f"Parsing page {page} into Markdown...")
        parser = LayoutParser()
        md = parser.parse_markdown_fast_path(page_png)
        output_md.write_text(f"<!-- Page {page} -->\n{md}\n", encoding="utf-8")
    console.print(f"[bold green]Page {page} Markdown saved to:[/] {output_md}")


@app.command()
def merge_markdown(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*.md files"),
    output_md: Path = typer.Option(Path("document.md"), "--output", "-o", help="Output merged Markdown path"),
):
    """Merges individual page Markdown files into a single unified Markdown document."""
    if pages_dir.is_dir():
        md_files = sorted(
            pages_dir.glob("page_*.md"),
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
    elif pages_dir.is_file():
        md_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not md_files:
        raise typer.BadParameter(f"No Markdown files found in {pages_dir}")

    full_md = [f.read_text(encoding="utf-8").strip() for f in md_files]
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n\n---\n\n".join(full_md), encoding="utf-8")
    console.print(f"[bold green]Merged {len(md_files)} pages into:[/] {output_md}")


@app.command()
def compile(
    spec_path: Path = typer.Argument(..., help="Path to AST DocumentSpec JSON file"),
    output_docx: Path = typer.Option(Path("output.docx"), "--output", "-o"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save the DocumentSpec AST JSON alongside the exported file"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path to save the DocumentSpec AST JSON"),
):
    """Compiles a canonical DocumentSpec AST JSON into a formatted Word (.docx) file."""
    raw_data = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = DocumentSpec.model_validate(raw_data)

    if save_ast or ast_path is not None:
        target_ast = ast_path or (output_docx.parent / f"{output_docx.stem}_ast.json")
        target_ast.parent.mkdir(parents=True, exist_ok=True)
        target_ast.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[dim]DocumentSpec AST saved to: {target_ast}[/]")

    compiler = DocxCompiler(spec)
    out = compiler.compile(output_docx, assets_dir=assets_dir)
    console.print(f"[bold green]Successfully compiled document to:[/] {out}")


@app.command()
def to_markdown(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_md: Path = typer.Option(Path("document.md"), "--output", "-o"),
    page: Optional[int] = typer.Option(None, "--page", "-p", help="Specific page (default: all)"),
):
    """Fast-track: Converts PDF pages to clean Markdown for direct docx-mcp generation."""
    temp_dir = output_md.parent / f".temp_pages_{pdf_path.stem}"
    with PDFExtractor(pdf_path) as extractor:
        pages = [page] if page else list(range(1, extractor.page_count + 1))
        parser = LayoutParser()
        full_md = []

        for p_num in pages:
            img = extractor.render_page_to_png(p_num, temp_dir / f"p{p_num}.png")
            console.print(f"Parsing page {p_num} into Markdown...")
            md = parser.parse_markdown_fast_path(img)
            full_md.append(f"<!-- Page {p_num} -->\n{md}")

    output_md.write_text("\n\n---\n\n".join(full_md), encoding="utf-8")
    console.print(f"[bold green]Markdown exported to:[/] {output_md}")


@app.command()
def convert(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_docx: Path = typer.Option(Path("output.docx"), "--output", "-o"),
    workspace_dir: Optional[Path] = typer.Option(None, "--workspace-dir", "-w", help="Independent temp workspace directory for this conversion"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory for cropped images and charts"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution"),
    diff: bool = typer.Option(False, "--diff", help="Perform visual diff critique"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save the DocumentSpec AST JSON alongside the exported file"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path to save the DocumentSpec AST JSON"),
):
    """Executes full autonomous conversion pipeline from PDF to DOCX."""
    console.print(f"[bold cyan]Starting conversion:[/] {pdf_path}")
    target_stem = output_docx.stem if output_docx.name != "output.docx" else pdf_path.stem
    if workspace_dir is not None:
        temp_dir = Path(workspace_dir)
    elif output_docx.parent.name == target_stem or output_docx.parent.name == pdf_path.stem:
        temp_dir = output_docx.parent / "workspace"
    else:
        temp_dir = output_docx.parent / f".workspace_{target_stem}"

    if assets_dir is not None:
        assets_path = Path(assets_dir)
    elif output_docx.parent.name == target_stem or output_docx.parent.name == pdf_path.stem:
        assets_path = output_docx.parent / "assets"
    else:
        assets_path = temp_dir / "assets"

    temp_dir.mkdir(parents=True, exist_ok=True)
    assets_path.mkdir(parents=True, exist_ok=True)

    with PDFExtractor(pdf_path) as extractor:
        doc_info = extractor.get_document_info()
        doc_spec = DocumentSpec(title=doc_info["title"])
        parser = LayoutParser()

        for p_info in doc_info["pages"]:
            p_num = p_info["page_number"]
            console.print(f"[cyan]Rendering page {p_num}/{doc_info['page_count']}...[/]")
            page_png = extractor.render_page_to_png(p_num, temp_dir / f"orig_p{p_num}.png", dpi=dpi)

            console.print(f"[cyan]Parsing layout structure for page {p_num}...[/]")
            page_spec = parser.parse_page_image(page_png, page_number=p_num)

            # Crop any image/figure blocks flagged with bbox
            for b_idx, block in enumerate(page_spec.blocks):
                if getattr(block, "type", "") == "image" and block.bbox:  # type: ignore
                    crop_dest = assets_path / f"p{p_num}_img{b_idx}.png"
                    extractor.extract_region(
                        p_num,
                        [block.bbox.ymin, block.bbox.xmin, block.bbox.ymax, block.bbox.xmax],  # type: ignore
                        output_path=crop_dest,
                        dpi=300,
                    )
                    block.image_path = str(crop_dest)  # type: ignore

            doc_spec.pages.append(page_spec)

    # Save AST JSON if requested
    if save_ast or ast_path is not None:
        target_ast = ast_path or (output_docx.parent / f"{output_docx.stem}_ast.json")
        target_ast.parent.mkdir(parents=True, exist_ok=True)
        target_ast.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[dim]Intermediate Representation AST saved to: {target_ast}[/]")

    # Compile to DOCX
    console.print("[cyan]Compiling AST into Word document (.docx)...[/]")
    compiler = DocxCompiler(doc_spec)
    compiler.compile(output_docx, assets_dir=assets_path)
    console.print(f"[bold green]Successfully created Word document:[/] {output_docx}")

    # Optional Visual Diff
    if diff:
        console.print("[cyan]Rendering DOCX headlessly for visual validation...[/]")
        rendered_docx_png = temp_dir / "rendered_docx_p1.png"
        res = render_docx_to_png(output_docx, rendered_docx_png, page_number=1)
        if res and res.exists():
            orig_p1 = temp_dir / "orig_p1.png"
            inspector = VisualDiffInspector()
            critique = inspector.inspect_and_critique(orig_p1, rendered_docx_png, page_number=1)
            console.print(f"[bold yellow]Layout Fidelity Score:[/] {critique.fidelity_score}/100")
            for d in critique.discrepancies:
                console.print(f"  - [{d.severity.upper()}] ({d.category}): {d.description} -> [italic]{d.suggested_fix}[/]")
        else:
            console.print("[dim yellow]Headless DOCX renderer (LibreOffice) not detected; skipped visual diff.[/]")


def main():
    app()


if __name__ == "__main__":
    main()

```

### .agents\skills\pdf-to-docx\scripts\inspect_pdf.py

_File not found in repo._

### .agents\skills\pdf-to-docx\scripts\render_pages.py

_File not found in repo._

### .agents\skills\pdf-to-docx\scripts\crop_asset.py

_File not found in repo._

### .agents\skills\pdf-to-docx\scripts\compile_pages.py

_File not found in repo._

### .agents\skills\pdf-to-docx\scripts\convert.py

_File not found in repo._

### .agents\skills\pdf-to-docx\scripts\diff_layout.py

_File not found in repo._

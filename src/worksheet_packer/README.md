# Worksheet Packer

A space-efficient worksheet parsing, layout packing, and dual DOCX/LaTeX rendering engine.

## Overview

Traditional worksheet PDFs and document conversions often waste massive horizontal whitespace—for example, placing a 2-inch geometric diagram on its own vertical block leaving 4.5 inches of empty horizontal space next to it. 

**Worksheet Packer** solves this with a two-stage layout architecture:
1. **Perception & AST Extraction**: Parses PDF pages, detects problems, harvests diagrams, trims empty margin pixels via auto-cropping, and produces a strongly-typed `WorksheetSpec` AST.
2. **2D Bin-Packing Layout Engine**: Analyzes each problem's footprint, aspect ratios, and section ordering constraints to choose between **Side-by-Side** (text 65% / diagram 35%) and **Stacked** layouts, minimizing page count.
3. **Deterministic Dual Compilation**:
   - **DOCX**: Invisible borderless tables with OpenXML `w:cantSplit` guarantees that diagrams, text, and student workspaces stay locked together across pages.
   - **LaTeX**: Clean `minipage` environments with `multicol` and `tcolorbox`.

---

## Directory Structure

```
src/worksheet_packer/
├── __init__.py           # Public exports
├── __main__.py           # python -m worksheet_packer entrypoint
├── cli.py                # Typer CLI (info, parse, pack, render, convert, render-docx-pages)
├── worksheet_ast.py      # Pydantic AST: WorksheetSpec, Problem, ProblemImage, etc.
├── image_utils.py        # PIL-based auto-crop & whitespace perimeter trimming
├── layout_engine.py      # 2D bin packing & footprint calculation
├── docx_renderer.py      # Deterministic Word compiler using invisible tables
├── latex_renderer.py     # Deterministic LaTeX & PDF compiler using minipage/multicols
├── docx_extractor.py     # Headless DOCX->PDF/PNG rendering & zip media extraction
└── worksheet_parser.py   # PDF & DOCX extractor + Gemini multimodal vision parser
```

---

## Core Capabilities

### 1. Side-by-Side vs. Stacked Heuristics
- **Side-by-Side (Layout A)**: For diagrams with aspect ratio $0.55 \le H/W \le 1.50$ and question prompts under 450 characters. Places prompt text on the left (65%) and diagram on the right (35%), with the student answer area spanning full width below.
- **Stacked (Layout B)**: For wide diagrams ($H/W < 0.50$) or lengthy prompts. Centers the diagram under the text.
- **Minimum Scale Floor**: Enforces minimum diagram rendering width (1.5 in) so axis markings and labels remain legible.

### 2. Flexible vs. Strict Problem Ordering
- `SectionOrdering.STRICT`: Preserves the author's exact problem sequence (e.g. for numbered multi-part exam problems).
- `SectionOrdering.FLEXIBLE`: Allows the 2D bin packer to reorder problems (First-Fit Decreasing) within the section to maximize packing density.

### 3. Student Workspaces (Clean Empty Whitespace)
Prefers clean empty whitespace for student work over artificial underline blanks:
- `blank` (Default): Clean whitespace gap budgeted via `approx_height_in` (e.g. `0.75`), `approx_area_sq_in` (e.g. `3.0`), or `lines` (`WorkspaceConfig(type="blank", approx_height_in=1.0)`).
- `box`: Framed response box (`WorkspaceConfig(type="box", height_pt=80)`).
- `grid`: Coordinate / graph grid area (`WorkspaceConfig(type="grid")`).
- `none`: Compact layout for multiple-choice or short-answer questions.
- `lines`: Legacy ruled lines (automatically converted to clean whitespace).
- `fill_remaining`: Automatically expands the final problem's work area to fill trailing page whitespace.

### 4. Re-packing Existing Word Documents (.docx)
Existing Word documents can be ingested directly:
- **Headless Page Rendering**: Converts DOCX -> PDF -> PNG pages via LibreOffice or Windows Word COM.
- **Embedded Media Extraction**: Extracts native PNGs/JPEGs directly from `word/media/` inside the DOCX ZIP archive.
- **Visual Vision Parsing**: Passes rendered pages to Gemini to understand problems and diagram placements, then 2D packs into a fresh, compact document.

---

## CLI Usage

```bash
# 1. Inspect a PDF, Word DOCX, or AST file
worksheet-packer info input.pdf
worksheet-packer info input.docx

# 2. Render all pages of an existing Word doc to PNGs (for visual inspection/critique)
worksheet-packer render-docx-pages input.docx -o ./rendered_pages

# 3. Parse PDF or Word document into WorksheetSpec JSON with harvested diagrams
worksheet-packer parse input.pdf --output spec.json --columns 2
worksheet-packer parse input.docx --output spec.json --columns 2

# 4. Pack spec into a positioned 2D RenderPlan
worksheet-packer pack spec.json --output plan.json --ordering flexible

# 5. Render to Word (.docx) or LaTeX (.tex / .pdf)
worksheet-packer render plan.json --output worksheet.docx --format docx
worksheet-packer render plan.json --output worksheet.tex --format latex

# 6. Full autonomous end-to-end conversion (PDF or DOCX input)
worksheet-packer convert input.pdf --columns 2 --format both
worksheet-packer convert sprawling_worksheet.docx --columns 2 --format docx
```


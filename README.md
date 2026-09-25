# PDF to DOCX: Autonomous, High-Fidelity Document Converter

> An enterprise-grade, multimodal pipeline for converting complex PDF documents into fully editable Microsoft Word (`.docx`) files using spatial AI layout analysis, deterministic block compilation, vector/raster asset harvesting, and visual diff self-correction.

---

## Architecture Overview

Traditional approaches fail at PDF-to-DOCX conversion:
- **Pure OCR** destroys tables, multi-column reading order, font scale hierarchies, and vector assets.
- **Naive Granular Tool-Calling** (e.g. LLM calling `add_table`, `add_row`, `set_formatting` hundreds of times) quickly exhausts context tokens, incurs extreme latency, and loses global spatial alignment.

This project implements the **Block-Based Intermediate Representation (IR) Compiler Architecture**:

```
[ Input PDF ]
      │
      ├─► PyMuPDF: Render Page N as High-Res PNG (200-300 DPI)
      │
      ├─► Gemini Flash (Multimodal): Spatial Layout Extraction
      │     └─► Canonical AST (DocumentSpec: Headings, Paragraphs, Tables, Charts, Images)
      │
      ├─► Asset Harvesting & Rendering:
      │     ├─► Vector drawings, logos & signatures ──► PyMuPDF BBox Cropper
      │     ├─► Charts ──► Matplotlib (300 DPI) OR native DrawingML via docx-mcp
      │     └─► Tables ──► Native python-docx builder (with w:cantSplit & w:tblHeader)
      │
      ├─► Deterministic DOCX Compiler: Assembles publication-ready .docx
      │
[ Visual Self-Correction Loop (QA) ]
      │
      ├─► Headless Renderer (LibreOffice / soffice): DOCX -> PDF -> PNG
      └─► Gemini Flash Vision Inspector: Side-by-side critique of Original vs Rendered
            └─► Automated adjustment of layout parameters if fidelity < 85%
```

---

## 3 Conversion Pathways

1. **Pathway 1: Block-Based IR (Default & Most Robust)**
   - Used for complex corporate reports, financial statements, and multi-column documents.
   - Extracts page elements into an Intermediate Representation (`DocumentSpec` AST).
   - Python engine deterministically compiles OpenXML Word structures with zero hallucination.

2. **Pathway 2: Fast-Track Markdown (`docx-mcp`)**
   - Ideal for narrative documents, research papers, and technical specifications.
   - Gemini extracts page content into clean GitHub-Flavored Markdown (GFM).
   - Ingested via `docx-mcp: create_from_markdown` for instant single-pass DOCX creation.

3. **Pathway 3: CodeAgent Sandboxing & Surgical Refinement**
   - For bespoke layouts, custom math formulas, or dynamic data tables.
   - Programmatic script execution alongside `docx-mcp` tools (`open_document`, `modify_cell`, `insert_bar_chart`, `set_formatting`).

---

## Antigravity Agent Skills & Slash Commands

This repository includes two first-class Antigravity skills in `.agents/skills/`:

| Skill / Slash Command | Purpose |
| :--- | :--- |
| **`/pdf-to-docx`** | Full end-to-end conversion orchestrator. Handles page inspection, multimodal layout extraction, asset cropping, compilation, and visual QA. |
| **`/docx-layout-refinement`** | Surgical post-conversion editing. Adjusts table column twips, borders, padding, margins, and upgrades charts to native Office DrawingML. |

---

## CLI Usage

The project includes a complete CLI powered by `uv` and `typer`:

```bash
# 1. Inspect PDF structure and page dimensions
uv run python -m pdf_to_docx info document.pdf

# 2. Render all pages to high-res PNG for visual inspection
uv run python -m pdf_to_docx render-pages document.pdf -o ./rendered_pages

# 3. Crop a specific region (logo, signature, diagram) using normalized BBox (ymin,xmin,ymax,xmax)
uv run python -m pdf_to_docx crop document.pdf --page 1 --bbox 120,50,300,450 -o ./assets/logo.png

# 4. Compile an AST JSON spec directly into Word
uv run python -m pdf_to_docx compile spec.json -o output.docx

# 5. Fast-track export to Markdown
uv run python -m pdf_to_docx to-markdown document.pdf -o document.md

# 6. Autonomous End-to-End Conversion (with optional visual diff QA)
uv run python -m pdf_to_docx convert document.pdf -o output.docx --diff
```

---

## Project Structure

```text
pdf-to-docx/
├── .agents/skills/
│   ├── pdf-to-docx/              # Main conversion orchestrator skill
│   │   ├── SKILL.md              # Slash command instructions (/pdf-to-docx)
│   │   ├── scripts/              # Helper CLI scripts (convert, inspect, crop, diff)
│   │   └── references/           # AST JSON spec, playbook, docx-mcp guide
│   └── docx-layout-refinement/   # Surgical styling & native charts skill
│       ├── SKILL.md              # Slash command instructions (/docx-layout-refinement)
│       └── references/           # Native chart specs, table styling guide
├── src/pdf_to_docx/
│   ├── ir_schema.py              # Pydantic Intermediate Representation (AST)
│   ├── pdf_extractor.py          # PyMuPDF page rendering, drawings, crops
│   ├── layout_parser.py          # Gemini 2.5 Flash spatial layout extraction
│   ├── chart_generator.py        # 300 DPI Matplotlib & docx-mcp chart schemas
│   ├── docx_compiler.py          # Deterministic OpenXML compiler (cantSplit, tblHeader)
│   ├── visual_diff.py            # Headless DOCX rendering & vision QA inspector
│   └── cli.py                    # Unified CLI command interface
├── tests/
│   ├── create_sample_pdf.py      # Synthetic PDF generator
│   └── test_pipeline.py          # Full compilation & AST test
└── pyproject.toml                # Managed via uv
```

---

## OpenXML Rules Enforced

- **`w:cantSplit`**: Enforced on all table rows to prevent rows from breaking mid-cell across page breaks.
- **`w:tblHeader`**: Injected on row 0 to repeat headers across subsequent pages.
- **Twip-accurate column allocations**: Predictable column widths avoiding platform-dependent auto-fit reflows.
- **High-DPI rasterization**: 300 DPI for vector diagrams, signatures, and charts.

# PDF to DOCX: Autonomous, High-Fidelity Document Converter

> An enterprise-grade, multimodal pipeline for converting complex PDF documents into fully editable Microsoft Word (`.docx`) files using spatial AI layout analysis, independent page-parallel subagents, deterministic block compilation, vector/raster asset harvesting, and visual diff self-correction.

---

## Architecture Overview

Traditional approaches fail at PDF-to-DOCX conversion:
- **Pure OCR** destroys tables, multi-column reading order, font scale hierarchies, and vector assets.
- **Monolithic Context Exhaustion**: Processing multi-page documents sequentially inside a single LLM context causes rapid context window explosion, attention dilution, lost table columns, and token limit crashes.
- **Naive Granular Tool-Calling** (e.g. LLM calling `add_table`, `add_row`, `set_formatting` hundreds of times) quickly exhausts context tokens, incurs extreme latency, and loses global spatial alignment.

This project implements the **Page-Parallel Subagent Compiler Architecture**:

```
[ Input PDF ]
      │
      ├─► Orchestrator: PyMuPDF inspects structure & renders pages (200-300 DPI)
      │
      ├─► Parallel Subagent Delegation (invoke_subagent):
      │     ├─► [Subagent Page 1] ──► Isolated extraction ──► page_1_spec.json & cropped assets
      │     ├─► [Subagent Page 2] ──► Isolated extraction ──► page_2_spec.json & cropped assets
      │     └─► [Subagent Page N] ──► Isolated extraction ──► page_N_spec.json & cropped assets
      │
      ├─► Reactive Wakeup: Orchestrator receives concise completion summaries (context stays clean!)
      │
      ├─► Deterministic DOCX Compiler:
      │     └─► uv run python -m pdf_to_docx compile-pages .conversion_workspace/ -o output.docx
      │           ├─► Tables: Native python-docx builder (with w:cantSplit & w:tblHeader)
      │           ├─► Charts: Matplotlib (300 DPI) OR native DrawingML via docx-mcp
      │           └─► Vector/Raster Assets: PyMuPDF bounding-box crops
      │
[ Visual Self-Correction QA Loop ]
      │
      ├─► Headless Renderer (LibreOffice / soffice): DOCX -> PDF -> PNG
      └─► Targeted Refinement Subagent: Isolated surgical edits for any page with score < 85%
```

---

## 3 Conversion Pathways

1. **Pathway 1: Block-Based IR (Default & Most Robust)**
   - Used for complex corporate reports, financial statements, and multi-column documents.
   - Independent subagents extract page elements into isolated `PageSpec` AST JSON files.
   - Deterministic compiler merges and compiles OpenXML Word structures with zero hallucination.

2. **Pathway 2: Fast-Track Markdown (`docx-mcp`)**
   - Ideal for narrative documents, research papers, and technical specifications.
   - Independent subagents extract each page into clean GitHub-Flavored Markdown (`page_{k}.md`).
   - Merged and ingested via `docx-mcp: create_from_markdown` for instant Word document creation.

3. **Pathway 3: CodeAgent Sandboxing & Surgical Refinement**
   - For bespoke layouts, custom math formulas, or dynamic data tables.
   - Programmatic script execution alongside `docx-mcp` tools (`open_document`, `modify_cell`, `insert_bar_chart`, `set_formatting`).

---

## Antigravity Agent Skills & Slash Commands

This repository includes two first-class Antigravity skills in `.agents/skills/`:

| Skill / Slash Command | Purpose | Subagent Strategy |
| :--- | :--- | :--- |
| **`/pdf-to-docx`** | Full end-to-end conversion orchestrator. Handles page inspection, multimodal layout extraction, asset cropping, compilation, and visual QA. | Spawns independent subagents per page via `invoke_subagent` to isolate context and prevent token bloat. |
| **`/docx-layout-refinement`** | Surgical post-conversion editing. Adjusts table column twips, borders, padding, margins, and upgrades charts to native Office DrawingML. | Dispatches targeted page-level refinement subagents for surgical fixes without polluting parent context. |

---

## CLI Usage

The project includes a complete CLI powered by `uv` and `typer`:

```bash
# 1. Inspect PDF structure and page dimensions
uv run python -m pdf_to_docx info document.pdf

# 2. Render all pages to high-res PNG for visual inspection
uv run python -m pdf_to_docx render-pages document.pdf -o ./rendered_pages

# 3. Parse a single page into PageSpec JSON and auto-crop assets (used by page subagents)
uv run python -m pdf_to_docx parse-page document.pdf --page 1 --image ./rendered_pages/orig_p1.png -o .conversion_workspace/page_1_spec.json --assets-dir ./assets

# 4. Compile all isolated page specs in a workspace into a unified Word document
uv run python -m pdf_to_docx compile-pages .conversion_workspace/ -o output.docx --title "Document Title"

# 5. Merge multiple page specs into a single canonical DocumentSpec JSON
uv run python -m pdf_to_docx merge-specs .conversion_workspace/ -o merged_spec.json

# 6. Fast-track single-page Markdown extraction (used by fast-track subagents)
uv run python -m pdf_to_docx to-markdown-page document.pdf --page 1 -o .conversion_workspace/page_1.md

# 7. Merge page Markdown files into a single unified document
uv run python -m pdf_to_docx merge-markdown .conversion_workspace/ -o document.md

# 8. Crop a specific region (logo, signature, diagram) using normalized BBox (ymin,xmin,ymax,xmax)
uv run python -m pdf_to_docx crop document.pdf --page 1 --bbox 120,50,300,450 -o ./assets/logo.png

# 9. Compile an existing monolithic AST JSON spec directly into Word
uv run python -m pdf_to_docx compile spec.json -o output.docx

# 10. Autonomous End-to-End Conversion (with optional visual diff QA)
uv run python -m pdf_to_docx convert document.pdf -o output.docx --diff
```

---

## Project Structure

```text
pdf-to-docx/
├── .agents/skills/
│   ├── pdf-to-docx/              # Main conversion orchestrator skill
│   │   ├── SKILL.md              # Instructions for page-parallel subagent conversion
│   │   ├── scripts/              # Helper CLI scripts (compile_pages, convert, inspect, crop, diff)
│   │   └── references/           # AST JSON spec, workflow playbook, docx-mcp guide
│   └── docx-layout-refinement/   # Surgical styling & native charts skill
│       ├── SKILL.md              # Instructions for page-level surgical refinement
│       └── references/           # Native chart specs, table styling guide
├── src/pdf_to_docx/
│   ├── ir_schema.py              # Pydantic Intermediate Representation (PageSpec, DocumentSpec)
│   ├── pdf_extractor.py          # PyMuPDF page rendering, drawings, crops
│   ├── layout_parser.py          # Gemini 2.5 Flash spatial layout extraction
│   ├── chart_generator.py        # 300 DPI Matplotlib & docx-mcp chart schemas
│   ├── docx_compiler.py          # Deterministic OpenXML compiler (cantSplit, tblHeader)
│   ├── visual_diff.py            # Headless DOCX rendering & vision QA inspector
│   └── cli.py                    # Unified CLI command interface (compile-pages, parse-page, etc.)
├── tests/
│   ├── create_sample_pdf.py      # Synthetic PDF generator
│   ├── test_pipeline.py          # Monolithic compilation test
│   └── test_subagent_pipeline.py # Page-parallel subagent merge & compile test
└── pyproject.toml                # Managed via uv
```

---

## OpenXML Rules Enforced

- **`w:cantSplit`**: Enforced on all table rows to prevent rows from breaking mid-cell across page breaks.
- **`w:tblHeader`**: Injected on row 0 to repeat headers across subsequent pages.
- **Twip-accurate column allocations**: Predictable column widths avoiding platform-dependent auto-fit reflows.
- **High-DPI rasterization**: 300 DPI for vector diagrams, signatures, and charts.

# PDF to DOCX & LaTeX: Autonomous, High-Fidelity Document Converter

> An enterprise-grade, multimodal pipeline for converting complex PDF documents into fully editable Microsoft Word (`.docx`) files or publication-ready, compilable LaTeX (`.tex`) documents and PDFs. Powered by spatial AI layout analysis, independent page-parallel subagents, deterministic compilation, vector/raster asset harvesting, and visual diff self-correction.

---

## Architecture Overview

Traditional approaches fail at PDF conversion:
- **Pure OCR** destroys tables, multi-column reading order, font scale hierarchies, mathematical formulas, and vector assets.
- **Monolithic Context Exhaustion**: Processing multi-page documents sequentially inside a single LLM context causes rapid context window explosion, attention dilution, lost table columns, and token limit crashes.
- **Naive Granular Tool-Calling**: Repeated small edits incur extreme latency, exhaust token budgets, and destroy global spatial alignment.

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
      ├─► Deterministic Compilers:
      │     ├─► DOCX: python -m pdf_to_docx compile-pages .conversion_workspace/ -o output.docx
      │     └─► LaTeX: python scripts/pdf_to_latex/compile_pages.py .conversion_workspace/ -o doc.tex --pdf
      │
[ Visual Self-Correction QA Loop ]
      │
      ├─► Headless Renderer (LibreOffice / pdflatex / tectonic): Compiles to PDF -> PNG
      └─► Visual Diff Inspector: Side-by-side comparison & layout score verification
```

---

## 3 Conversion Pathways

1. **Pathway 1: Block-Based IR (Default & Most Robust)**
   - Used for complex corporate reports, financial statements, scientific papers, and quizzes/exams.
   - Independent subagents extract page elements into isolated `PageSpec` AST JSON files.
   - Deterministic compiler merges and compiles Word OpenXML structures or LaTeX documents with zero hallucination.

2. **Pathway 2: Fast-Track Markdown / LaTeX Fragments**
   - Ideal for narrative documents, research papers, and technical specifications.
   - Independent subagents extract each page into clean GitHub-Flavored Markdown (`page_{k}.md`) or LaTeX fragments (`page_{k}.tex`).
   - Merged and ingested via `docx-mcp: create_from_markdown` or `pdf_to_latex merge-latex` for instant compilation.

3. **Pathway 3: CodeAgent Sandboxing & Surgical Refinement**
   - For bespoke layouts, custom math formulas, TikZ diagrams, or dynamic data tables.
   - Programmatic script execution alongside `docx-mcp` tools or raw LaTeX packages (`tcolorbox`, `exam`, `booktabs`).

---

## Antigravity Agent Skills & Slash Commands

This repository includes three first-class Antigravity skills in `.agents/skills/`:

| Skill / Slash Command | Target Format | Purpose | Subagent Strategy |
| :--- | :--- | :--- | :--- |
| **`/pdf-to-docx`** | `.docx` | Full Word conversion orchestrator. Handles page inspection, multimodal layout extraction, asset cropping, compilation, and visual QA. | Spawns independent subagents per page via `invoke_subagent` to isolate context and prevent token bloat. |
| **`/pdf-to-latex`** | `.tex` / `.pdf` | Full LaTeX conversion orchestrator. Specializes in advanced mathematics (`amsmath`), professional tables (`booktabs`), and exam/quiz worksheets (`exam` class). | Spawns independent page subagents to extract math AST specs and crop figures for `\includegraphics`. |
| **`/docx-layout-refinement`** | `.docx` | Surgical post-conversion editing. Adjusts table column twips, borders, padding, margins, and upgrades charts to native Office DrawingML. | Dispatches targeted page-level refinement subagents for surgical fixes without polluting parent context. |

---

## LaTeX Distribution & Library Installation Guide

To compile generated `.tex` files into PDF locally, you need a LaTeX distribution or engine installed on your system.

### 1. Windows Installation

#### Option A: MiKTeX (Recommended for Windows)
MiKTeX is the easiest Windows distribution because it automatically downloads missing LaTeX packages on-the-fly when compiling.
```powershell
# Install via Windows Package Manager (winget)
winget install MiKTeX.MiKTeX

# Or install via Chocolatey
choco install miktex
```
*After installation, restart your terminal or IDE.*

#### Option B: Tectonic (Modern, Self-Contained Single-Binary Engine)
Tectonic is a fast, modernized XeTeX engine that automatically downloads required CTAN packages into a local cache without needing a 4GB TeX distribution.
```powershell
winget install tectonic
# Or via Cargo (Rust)
cargo install tectonic
```

#### Option C: TeX Live (Comprehensive Distribution)
Download the full installer from [tug.org/texlive/windows.html](https://www.tug.org/texlive/windows.html) or install via Chocolatey:
```powershell
choco install texlive
```

---

### 2. macOS Installation

#### Option A: MacTeX (Full Distribution)
```bash
brew install --cask mactex
```

#### Option B: BasicTeX (Lightweight ~100MB Distribution)
```bash
brew install --cask basictex
sudo tlmgr update --self
sudo tlmgr install amsmath booktabs tabularx tcolorbox xcolor microtype exam geometry hyperref enumitem ulem caption
```

#### Option C: Tectonic
```bash
brew install tectonic
```

---

### 3. Linux (Ubuntu / Debian / WSL) Installation

```bash
sudo apt-get update
sudo apt-get install -y texlive-latex-base texlive-latex-extra texlive-fonts-recommended texlive-science latexmk
```

Or install Tectonic:
```bash
curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh
```

---

### 4. Zero-Install / Cloud Option: Overleaf

If you do not have LaTeX installed locally, the generated output from `pdf-to-latex` is 100% self-contained:
1. Run the conversion to generate `document.tex` and the `assets/` folder.
2. Zip `document.tex` and the `assets/` folder.
3. Upload the zip directly to [Overleaf](https://www.overleaf.com) and click **Recompile**.

---

### 5. Required LaTeX CTAN Packages

The compiler generates standard, publication-grade LaTeX utilizing these standard CTAN libraries:

| Package | Purpose in Compiler |
| :--- | :--- |
| `geometry` | Margins and paper dimensions (`margin=1.0in`, `letterpaper` or `a4paper`). |
| `amsmath`, `amssymb`, `amsfonts`, `mathtools`, `bm` | AMS mathematical typography, display equations, fractions, bold symbols. |
| `booktabs`, `tabularx`, `multirow`, `array`, `colortbl` | Professional tables with `\toprule`, `\midrule`, auto-wrapped `X` columns, and cell shading. |
| `graphicx` | Inclusion of high-resolution cropped PDF graphics and charts (`\includegraphics`). |
| `xcolor`, `tcolorbox` | Framed callouts, theorem boxes, and student fill-in response frames. |
| `exam` | Native exam/quiz worksheet environment (`\question`, `\part`, `choices`, `\makeemptybox`). |
| `enumitem`, `ulem` | Customizable list layouts and typographical decorations (strikethrough). |
| `microtype`, `caption` | Micro-typographical font justification and figure/table captions. |
| `hyperref` | Clickable internal links, citations, and URLs. |

---

## CLI Usage

### LaTeX Workflow (`scripts/pdf_to_latex/` & `pdf-to-latex` CLI)

```bash
# 1. Inspect PDF structure and check for installed LaTeX compiler
uv run python scripts/pdf_to_latex/inspect_pdf.py path/to/document.pdf

# 2. Render all pages to high-res PNG
uv run python -m pdf_to_latex render-pages document.pdf -o ./rendered_pages

# 3. Parse single page into PageSpec JSON with LaTeX math & crop assets (used by subagents)
uv run python -m pdf_to_latex parse-page document.pdf --page 1 --image ./rendered_pages/page_1.png -o .conversion_workspace/page_1_spec.json --assets-dir ./assets

# 4. Compile all isolated page specs into a complete LaTeX document (.tex) and PDF
uv run python scripts/pdf_to_latex/compile_pages.py .conversion_workspace/ -o document.tex --title "Document Title" --doc-class article --pdf

# 4b. Compile with Exam / Quiz class (for worksheets, problem sets, and tests)
uv run python scripts/pdf_to_latex/compile_pages.py .conversion_workspace/ -o quiz.tex --title "AP Statistics Quiz" --doc-class exam --pdf

# 5. Fast-track single-page direct LaTeX fragment extraction
uv run python -m pdf_to_latex to-latex-page document.pdf --page 1 -o .conversion_workspace/page_1.tex

# 6. Merge modular LaTeX fragments into a master document
uv run python -m pdf_to_latex merge-latex .conversion_workspace/ -o document.tex --pdf

# 7. Compile an existing .tex file directly into PDF
uv run python scripts/pdf_to_latex/compile_latex.py document.tex -o output.pdf

# 8. Visual Diff: Compare compiled LaTeX PDF against original rendered PNG
uv run python scripts/pdf_to_latex/diff_layout.py rendered_pages/page_1.png output.pdf --page 1 -o visual_diff_p1.png

# 9. Autonomous End-to-End Conversion Pipeline
uv run python scripts/pdf_to_latex/convert.py document.pdf -o document.tex --doc-class article --pdf
```

### DOCX Workflow (`pdf-to-docx` CLI)

```bash
# 1. Inspect PDF structure and page dimensions
uv run python -m pdf_to_docx info document.pdf

# 2. Render all pages to high-res PNG
uv run python -m pdf_to_docx render-pages document.pdf -o ./rendered_pages

# 3. Parse a single page into PageSpec JSON and auto-crop assets
uv run python -m pdf_to_docx parse-page document.pdf --page 1 --image ./rendered_pages/orig_p1.png -o .conversion_workspace/page_1_spec.json --assets-dir ./assets

# 4. Compile all isolated page specs in a workspace into a unified Word document
uv run python -m pdf_to_docx compile-pages .conversion_workspace/ -o output.docx --title "Document Title"

# 5. Fast-track single-page Markdown extraction
uv run python -m pdf_to_docx to-markdown-page document.pdf --page 1 -o .conversion_workspace/page_1.md

# 6. Merge page Markdown files into a single unified document
uv run python -m pdf_to_docx merge-markdown .conversion_workspace/ -o document.md

# 7. Autonomous End-to-End Word Conversion
uv run python -m pdf_to_docx convert document.pdf -o output.docx --diff
```

---

## Project Structure

```text
pdf-to-docx/
├── .agents/skills/
│   ├── pdf-to-docx/              # Word (.docx) conversion orchestrator skill
│   │   ├── SKILL.md              # Instructions for page-parallel DOCX conversion
│   │   ├── scripts/              # Helper DOCX scripts (compile_pages, convert, diff)
│   │   └── references/           # AST JSON spec, workflow playbook, docx-mcp guide
│   ├── pdf-to-latex/             # LaTeX (.tex / .pdf) conversion orchestrator skill
│   │   ├── SKILL.md              # Instructions for page-parallel LaTeX conversion
│   │   ├── scripts/              # Helper LaTeX scripts mirrored for skill execution
│   │   └── references/           # LaTeX architecture, workflow playbook, math & tables spec
│   └── docx-layout-refinement/   # Surgical styling & native charts skill
│       ├── SKILL.md              # Instructions for page-level surgical refinement
│       └── references/           # Native chart specs, table styling guide
├── scripts/
│   └── pdf_to_latex/             # Top-level organized LaTeX conversion scripts
│       ├── inspect_pdf.py        # Inspect PDF & render pages
│       ├── crop_asset.py         # High-DPI asset cropping for \includegraphics
│       ├── compile_pages.py      # Compile page specs into master LaTeX doc & PDF
│       ├── compile_latex.py      # Compile .tex to .pdf using local LaTeX engines
│       ├── convert.py            # End-to-end autonomous pipeline
│       └── diff_layout.py        # Headless visual diff comparison
├── src/
│   ├── pdf_to_docx/              # DOCX conversion package
│   │   ├── ir_schema.py          # DOCX Intermediate Representation
│   │   ├── docx_compiler.py      # Deterministic OpenXML compiler (cantSplit, tblHeader)
│   │   ├── layout_parser.py      # Gemini Flash spatial layout extraction
│   │   ├── chart_generator.py    # Matplotlib & DrawingML charts
│   │   └── cli.py                # DOCX CLI commands
│   └── pdf_to_latex/             # LaTeX conversion package
│       ├── ir_schema.py          # LaTeX-enhanced IR (math, exam questions, booktabs)
│       ├── latex_compiler.py     # Deterministic LaTeX compiler & engine detection
│       ├── layout_parser.py      # Gemini Flash LaTeX vision extractor
│       ├── chart_generator.py    # 300 DPI figure graphics
│       ├── pdf_extractor.py      # PyMuPDF rendering & coordinate cropping
│       └── cli.py                # LaTeX CLI commands (compile-pages, merge-latex, etc.)
├── tests/
│   ├── test_subagent_pipeline.py # DOCX subagent merge & compile test
│   ├── test_latex_pipeline.py    # LaTeX subagent merge & compile test
│   └── stats merged quiz unit 1.pdf # Sample AP Statistics quiz with math & diagrams
└── pyproject.toml                # Managed via uv with CLI entrypoints
```

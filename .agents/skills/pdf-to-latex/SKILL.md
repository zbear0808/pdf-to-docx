---
name: pdf-to-latex
description: >-
  Converts PDF documents into high-fidelity, compilable LaTeX (.tex) documents and PDFs using a multimodal
  LaTeX Intermediate Representation (IR), PyMuPDF asset harvesting, and deterministic compilation. Runs as a
  sequential, single-agent workflow (no subagents). Specializes in advanced mathematics, technical tables, and exam/quiz worksheets.
---

# PDF to High-Fidelity LaTeX Conversion Skill

This skill executes an autonomous, page-parallel pipeline to transform complex PDF documents into publication-ready, compilable LaTeX (`.tex`) documents and PDFs.

## Core Principle: Sequential Single-Agent Execution (No Subagents)

> [!IMPORTANT]
> **Do not start subagents or use agent-delegation tools** (e.g., `invoke_subagent`, `task`). Microsoft Copilot and similar environments may not support them.
>
> Process pages **one at a time in the current session**, writing each page’s outputs to disk (`_temp/specs/`, `_temp/assets/`, `_temp/renders/`) before moving to the next page. Keep progress durable and resume by skipping pages whose `page_*_spec.json` / `page_*.tex` output already exists.

---

## 3 Conversion Pathways

| Pathway | Document Characteristics | Primary Tooling | Execution Pattern |
| :--- | :--- | :--- | :--- |
| **Pathway 1: LaTeX AST IR (Default)** | Mathematical papers, multi-column reports, exams/quizzes, structured tables + charts + images | `pdf_to_latex` CLI AST Compiler | Extract `page_{k}_spec.json` per page sequentially; compile all specs |
| **Pathway 2: Direct LaTeX Fragments** | Standard narrative papers, lecture notes, straightforward equations | Gemini Vision fast-path + `pdf_to_latex merge-latex` | Extract `page_{k}.tex` per page sequentially; merge |
| **Pathway 3: CodeAgent Sandbox** | Complex TikZ diagrams, dynamic geometry, specialized custom exam environments | Python / TeX script sandbox | Run dedicated scripts in the current session |

---

## Directory Layout & Workspace Hygiene

All LaTeX conversion workflows must isolate outputs and temporary files into standard subfolders:
```text
<document_workspace>/
├── output/                 # Final deliverables (.tex, .pdf)
└── _temp/                  # ALL temporary & intermediate working files
    ├── assets/             # Harvested/cropped figures, diagrams, formulas
    ├── renders/            # High-resolution rendered page PNGs (page_{k}.png)
    ├── specs/              # Extracted AST JSONs (page_*_spec.json, document_spec.json)
    └── build/              # LaTeX compile artifacts (.aux, .log, .fls, .fdb_latexmk)
```
This guarantees that all transient files are automatically matched by gitignore rules (`**/_temp/`).

---

## Step-by-Step Execution Workflow

```
[ Single Agent / Current Session ]
       │
       ├─► 1. Inspect PDF structure (page count N, dimensions, local LaTeX compiler)
       ├─► 2. Render all pages to PNGs (_temp/renders/page_{k}.png)
       │
       ├─► 3. For each page k = 1..N (sequential)
       │         └──► Parse page k → _temp/specs/page_{k}_spec.json (or page_{k}.tex) and crop assets to _temp/assets/
       │              Resume by skipping pages whose output file already exists
       │
       ├─► 4. Compile assembled specs: uv run python scripts/pdf_to_latex/compile_pages.py _temp/specs/ -o output/document.tex --pdf
       │
       └─► 5. Optional QA: compare compiled PDF with original renderings (diff_layout.py)
```

---

### Phase 1: Orchestrator Intake & Page Rendering

1. Inspect PDF structure, total page count, orientation, and detected LaTeX compilers:
   ```bash
   uv run python scripts/pdf_to_latex/inspect_pdf.py path/to/document.pdf
   ```
2. Create standardized subfolders:
   ```bash
   mkdir -p output _temp/renders _temp/assets _temp/specs _temp/build
   ```
3. Render all pages to high-resolution PNG images (`200 DPI`) into `_temp/renders`:
   ```bash
   uv run python -m pdf_to_latex render-pages path/to/document.pdf -o _temp/renders
   ```

---

### Phase 2: Per-Page Extraction (Sequential)

Process each page in the current session. For every page `k` (1-indexed), run:

```bash
uv run python -m pdf_to_latex parse-page path/to/document.pdf --page {k} --image _temp/renders/page_{k}.png -o _temp/specs/page_{k}_spec.json --assets-dir _temp/assets
```

- After each page, inspect `_temp/specs/page_{k}_spec.json` to ensure mathematical formulas (`$...$`, display equations), table headers, and question blocks are accurately captured.
- Keep a brief running note (page number, block/equation/table counts, issues) instead of dumping large JSON into chat.
- **Resume-friendly:** if `_temp/specs/page_{k}_spec.json` already exists and is valid, skip and continue.

#### Fast-Track Direct LaTeX Fragment Alternative (Pathway 2)
```bash
uv run python -m pdf_to_latex to-latex-page path/to/document.pdf --page {k} --image _temp/renders/page_{k}.png -o _temp/specs/page_{k}.tex
```

---

### Phase 3: Assembly & Compilation

Once all required page outputs exist in `_temp/specs/` (`page_*_spec.json` for Pathway 1 or `page_*.tex` for Pathway 2):

#### For Pathway 1 (Block-Based IR):
Compile the assembled `page_*_spec.json` files directly into `.tex` and `.pdf` inside `output/`:

```bash
uv run python scripts/pdf_to_latex/compile_pages.py _temp/specs/ -o output/document.tex --title "Document Title" --doc-class article --pdf --save-ast
```

Available document classes:
- `--doc-class article` (Default: technical reports, research papers)
- `--doc-class exam` (Quizzes, tests, problem sets with `\question`, choices, and response boxes)
- `--doc-class report` (Long-form documents with chapters)
- `--doc-class scrartcl` (Modern KOMA-Script article)

#### For Pathway 2 (Direct LaTeX Fragments):
Assemble modular page fragments into a master document:
```bash
uv run python -m pdf_to_latex merge-latex .conversion_workspace/ -o document.tex --title "Document Title" --pdf
```

---

### Phase 4: Local Compilation or Remote Export

1. If a local LaTeX engine (`latexmk`, `tectonic`, `xelatex`, `pdflatex`, `lualatex`) is installed:
   ```bash
   uv run python scripts/pdf_to_latex/compile_latex.py document.tex -o output.pdf
   ```
2. If compiling remotely (e.g. Overleaf):
   - The generated `document.tex` and `assets/` directory are completely self-contained and ready to zip and upload.

---

### Phase 5: Visual QA & Comparison

To verify visual fidelity against the original PDF:
```bash
uv run python scripts/pdf_to_latex/diff_layout.py rendered_pages/page_1.png output.pdf --page 1 -o visual_diff_p1.png
```

---

## Detailed References

- [LaTeX Architecture & Preamble Specification](./references/latex_architecture_spec.md)
- [LaTeX Workflow Playbook & Decision Matrix](./references/workflow_playbook.md)
- [Math, Tables & Exam Formatting Guide](./references/math_and_tables_spec.md)

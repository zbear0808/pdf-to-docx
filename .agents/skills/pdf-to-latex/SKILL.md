---
name: pdf-to-latex
description: >-
  Converts PDF documents into high-fidelity, compilable LaTeX (.tex) documents and PDFs using a multimodal
  LaTeX Intermediate Representation (IR), independent page-parallel subagents, PyMuPDF asset harvesting,
  and deterministic compilation. Specializes in advanced mathematics, technical tables, and exam/quiz worksheets.
---

# PDF to High-Fidelity LaTeX Conversion Skill

This skill executes an autonomous, page-parallel pipeline to transform complex PDF documents into publication-ready, compilable LaTeX (`.tex`) documents and PDFs.

## Core Principle: Page-Parallel Subagent Architecture

> [!IMPORTANT]
> **Context Window Protection via Independent Subagents**
> Processing multiple PDF pages sequentially inside a single conversation context rapidly exhausts tokens with high-resolution page rasters, bounding-box math, and verbose markup.
> 
> **Rule**: The orchestrator agent **MUST spawn independent subagents for each page** using `invoke_subagent`. Each subagent operates within its own isolated conversation context, processes exactly one page, crops visual assets, and reports back a concise summary.

---

## 3 Conversion Pathways

| Pathway | Document Characteristics | Primary Tooling | Execution Pattern |
| :--- | :--- | :--- | :--- |
| **Pathway 1: LaTeX AST IR (Default)** | Mathematical papers, multi-column reports, exams/quizzes, structured tables + charts + images | `pdf_to_latex` CLI AST Compiler | Page subagents extract `page_{k}_spec.json`; orchestrator compiles |
| **Pathway 2: Direct LaTeX Fragments** | Standard narrative papers, lecture notes, straightforward equations | Gemini Vision fast-path + `pdf_to_latex merge-latex` | Page subagents extract `page_{k}.tex`; orchestrator merges |
| **Pathway 3: CodeAgent Sandbox** | Complex TikZ diagrams, dynamic geometry, specialized custom exam environments | Python / TeX script sandbox | Dedicated subagent script execution sandbox |

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
[ Orchestrator Agent ]
       │
       ├─► 1. Inspect PDF structure (page count N, dimensions, local LaTeX compiler)
       ├─► 2. Render all pages to PNGs (_temp/renders/page_{k}.png)
       │
       ├─► 3. Dispatch N Parallel Subagents (invoke_subagent)
       │         │
       │         ├──► [Subagent Page 1] ──► Extracts _temp/specs/page_1_spec.json & crops assets to _temp/assets/
       │         ├──► [Subagent Page 2] ──► Extracts _temp/specs/page_2_spec.json & crops assets to _temp/assets/
       │         └──► [Subagent Page N] ──► Extracts _temp/specs/page_N_spec.json & crops assets to _temp/assets/
       │
       ├─► 4. Reactive Wakeup: Receive concise completion messages (context stays clean!)
       ├─► 5. Compile assembled specs: uv run python scripts/pdf_to_latex/compile_pages.py _temp/specs/ -o output/document.tex --pdf
       │
       └─► 6. Optional QA: Compare compiled PDF with original renderings using diff_layout.py
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

### Phase 2: Page-Parallel Subagent Delegation

The orchestrator calls `invoke_subagent` to spawn an independent subagent for each page concurrently.

#### Subagent Dispatch Example:
```json
{
  "Subagents": [
    {
      "TypeName": "self",
      "Role": "Page 1 LaTeX Extractor",
      "Model": "flash",
      "Prompt": "You are the dedicated LaTeX extractor for Page 1 of 'path/to/document.pdf'.\nRendered image: '_temp/renders/page_1.png'.\n\nYour task:\n1. Parse Page 1 into the canonical PageSpec AST JSON schema.\n   Run: uv run python -m pdf_to_latex parse-page path/to/document.pdf --page 1 --image _temp/renders/page_1.png -o _temp/specs/page_1_spec.json --assets-dir _temp/assets\n2. Inspect _temp/specs/page_1_spec.json to ensure mathematical formulas ($...$, display equations), table headers, and question blocks are accurately captured.\n3. Reply with a 2-line completion summary: total blocks, equations, tables, and confirmation of file creation.\nDo NOT dump large JSON in your final reply to keep parent context compact."
    },
    {
      "TypeName": "self",
      "Role": "Page 2 LaTeX Extractor",
      "Model": "flash",
      "Prompt": "You are the dedicated LaTeX extractor for Page 2 of 'path/to/document.pdf'.\nRendered image: '_temp/renders/page_2.png'.\n\nYour task:\n1. Parse Page 2 into the canonical PageSpec AST JSON schema.\n   Run: uv run python -m pdf_to_latex parse-page path/to/document.pdf --page 2 --image _temp/renders/page_2.png -o _temp/specs/page_2_spec.json --assets-dir _temp/assets\n2. Inspect _temp/specs/page_2_spec.json to ensure mathematical formulas ($...$, display equations), table headers, and question blocks are accurately captured.\n3. Reply with a 2-line completion summary: total blocks, equations, tables, and confirmation of file creation.\nDo NOT dump large JSON in your final reply to keep parent context compact."
    }
  ]
}
```

> [!TIP]
> **Reactive Wakeup**: Do NOT poll or loop checking on subagents. Stop calling tools and allow the system to notify you when the subagents complete.

#### Fast-Track Direct LaTeX Fragment Subagent Alternative:
For narrative papers using Pathway 2:
```bash
uv run python -m pdf_to_latex to-latex-page path/to/document.pdf --page {k} --image _temp/renders/page_{k}.png -o _temp/specs/page_{k}.tex
```

---

### Phase 3: Assembly & Compilation

Once all page subagents report completion:

#### For Pathway 1 (Block-Based IR):
The orchestrator compiles the assembled `page_*_spec.json` files directly into `.tex` and `.pdf` inside `output/`:

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

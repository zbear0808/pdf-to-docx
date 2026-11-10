---
name: pdf-to-latex
description: >-
  Converts PDF documents into high-fidelity, compilable LaTeX (.tex) documents and PDFs using a multimodal
  LaTeX Intermediate Representation (IR), PyMuPDF asset harvesting, and deterministic compilation. Uses one
  subagent per page when the environment supports subagents, otherwise processes pages one at a time in the
  current session. Specializes in advanced mathematics, technical tables, and exam/quiz worksheets from
  arbitrary PDFs. Not for documents built by lesson-builder (lessons, keys, practice, assessments in
  `units/`); edit their YAML or `figures/<stem>.py` and rebuild instead.
---

# PDF to High-Fidelity LaTeX Conversion Skill

This skill executes an autonomous, page-by-page pipeline to transform complex PDF documents into publication-ready, compilable LaTeX (`.tex`) documents and PDFs.

> [!IMPORTANT]
> **Scope.** Not for documents built by lesson-builder (lessons, keys, practice, assessments in `units/`): edit the YAML or `figures/<stem>.py` and rebuild instead (see `lesson-builder`). To read a source PDF for a lesson/assessment, use `uv run lesson-builder ingest`, not this converter.

## Core Principle: Page Subagents When Available, Otherwise Sequential

Use one subagent per page (or per section) when the environment supports subagents: the orchestrator renders pages, launches page subagents with the page image path (`_temp/renders/page_{k}.png`) and the output spec path (`_temp/specs/page_{k}_spec.json` or `page_{k}.tex`), and merges. If subagents are not available (e.g., Microsoft Copilot), process pages one at a time in this session with the same files.

Either way, write each page's outputs to disk (`_temp/specs/`, `_temp/assets/`) before the next step. Resume by skipping pages whose `page_*_spec.json` / `page_*.tex` output already exists. Prompt templates are in [workflow_playbook.md](./references/workflow_playbook.md).

---

## 3 Conversion Pathways

| Pathway | Document Characteristics | Primary Tooling | Execution Pattern |
| :--- | :--- | :--- | :--- |
| **Pathway 1: LaTeX AST IR (Default)** | Mathematical papers, multi-column reports, exams/quizzes, structured tables + charts + images | `pdf_to_latex` CLI AST Compiler | Extract `page_{k}_spec.json` per page (page subagents or sequential); compile all specs |
| **Pathway 2: Direct LaTeX Fragments** | Standard narrative papers, lecture notes, straightforward equations | Gemini Vision fast-path + `pdf_to_latex merge-latex` | Extract `page_{k}.tex` per page (page subagents or sequential); merge |
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
[ Orchestrator (this session) ]
       │
       ├─► 1. Inspect PDF structure (page count N, dimensions, local LaTeX compiler)
       ├─► 2. Render all pages to PNGs (_temp/renders/page_{k}.png)
       │
       ├─► 3. For each page k = 1..N (one page subagent each, or sequentially here if subagents are unavailable)
       │         └──► Parse page k → _temp/specs/page_{k}_spec.json (or page_{k}.tex) and crop assets to _temp/assets/
       │              Resume by skipping pages whose output file already exists
       │
       ├─► 4. Assemble: uv run python scripts/pdf_to_latex/compile_pages.py _temp/specs/ -o output/document.tex --assets-dir _temp/assets
       ├─► 5. Compile: latexmk -pdf -output-directory=_temp/build output/document.tex, then copy the PDF to output/
       │
       └─► 6. Optional QA: compare compiled PDF with source renders (scripts/pdf_to_latex/diff_layout.py)
```

---

### Phase 1: Orchestrator Intake & Page Rendering

1. Inspect PDF structure, total page count, orientation, and detected LaTeX compilers:
   ```bash
   uv run python scripts/pdf_to_latex/inspect_pdf.py path/to/document.pdf
   ```
2. Create standardized subfolders:
   ```powershell
   New-Item -ItemType Directory -Force output, _temp/renders, _temp/assets, _temp/specs, _temp/build | Out-Null
   ```
3. Render all pages to high-resolution PNG images (`200 DPI`) into `_temp/renders` (named `page_1.png`, `page_2.png`, ...; without `-o` they go to `./rendered_pages/<stem>/`):
   ```bash
   uv run python -m pdf_to_latex render-pages path/to/document.pdf -o _temp/renders
   ```

---

### Phase 2: Per-Page Extraction

For every page `k` (1-indexed), a page subagent (or this session, if subagents are unavailable) runs:

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
Assemble the `page_*_spec.json` files into `.tex` inside `output/`. Pass `--assets-dir _temp/assets` (the compiler otherwise uses `<pages_dir>/assets/` or `output/assets/`) and `--ast-path` so the merged AST stays in `_temp/` (`--save-ast` alone writes `output/document_ast.json`):

```bash
uv run python scripts/pdf_to_latex/compile_pages.py _temp/specs/ -o output/document.tex --title "Document Title" --doc-class article --assets-dir _temp/assets --ast-path _temp/specs/document_ast.json
```

Available document classes:
- `--doc-class article` (Default: technical reports, research papers)
- `--doc-class exam` (Quizzes, tests, problem sets with `\question`, choices, and response boxes)
- `--doc-class report` (Long-form documents with chapters)
- `--doc-class scrartcl` (Modern KOMA-Script article)

#### For Pathway 2 (Direct LaTeX Fragments):
Assemble modular page fragments into a master document:
```bash
uv run python -m pdf_to_latex merge-latex _temp/specs/ -o output/document.tex --title "Document Title"
```

---

### Phase 4: Local Compilation or Remote Export

1. If a local LaTeX engine is installed, compile with build files routed to `_temp/build` (AGENTS.md §3.5), then copy the PDF into `output/`. Run from the workspace root so `\includegraphics` paths like `_temp/assets/...` resolve:
   ```powershell
   latexmk -pdf -interaction=nonstopmode -output-directory=_temp/build output/document.tex
   # or: pdflatex -interaction=nonstopmode -output-directory=_temp/build output/document.tex   (run twice for cross-references)
   Copy-Item _temp/build/document.pdf output/
   ```
   Do not use the `--pdf` flag of `compile_pages.py` / `merge-latex`, `compile_latex.py`, or `pdf_to_latex compile-pdf` for deliverables: they run the engine in the `.tex` folder with no output directory, so `.aux/.log/.fls` land in `output/`, and the cwd-relative image paths that `parse-page` stores (`_temp/assets/p{k}_img{n}.png`) no longer resolve. Avoid them.
2. If compiling remotely (e.g. Overleaf):
   - Zip `output/document.tex` together with the `_temp/assets/` images, keeping the relative paths the `.tex` references.

---

### Phase 5: Visual QA & Comparison

To verify visual fidelity against the original PDF:
```bash
uv run python scripts/pdf_to_latex/diff_layout.py _temp/renders/page_1.png output/document.pdf --page 1 -o _temp/renders/diff_p1.png
```

---

## Detailed References

- [LaTeX Architecture & Preamble Specification](./references/latex_architecture_spec.md)
- [LaTeX Workflow Playbook & Decision Matrix](./references/workflow_playbook.md)
- [Math, Tables & Exam Formatting Guide](./references/math_and_tables_spec.md)

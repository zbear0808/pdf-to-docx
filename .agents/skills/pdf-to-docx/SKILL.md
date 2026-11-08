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

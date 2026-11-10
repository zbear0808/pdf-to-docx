---
name: pdf-to-docx
description: >-
  Converts PDF documents into high-fidelity, editable Word (.docx) documents using a multimodal
  Block-Based Intermediate Representation (IR), PyMuPDF asset harvesting, deterministic compilation,
  and docx-mcp integration. Uses one subagent per page when the environment supports subagents, otherwise
  processes pages one at a time in the current session. Use when asked to convert, extract, or transcribe an
  arbitrary PDF to Word (.docx). Not for documents built by lesson-builder (lessons, keys, practice,
  assessments in `units/`); edit their YAML or `figures/<stem>.py` and rebuild instead.
---

# PDF to Editable DOCX Conversion Skill

This skill executes a robust, battle-tested pipeline to transform complex PDF documents into fully editable Microsoft Word (`.docx`) files.

> [!IMPORTANT]
> **Scope.** Not for documents built by lesson-builder (lessons, keys, practice, assessments in `units/`): edit the YAML or `figures/<stem>.py` and rebuild instead (see `lesson-builder`). To read source documents for a lesson/assessment, use `uv run lesson-builder ingest`, not this converter.

## Core Principle: Page Subagents When Available, Otherwise Sequential

Use one subagent per page (or per section) when the environment supports subagents: the orchestrator renders pages, launches page subagents with the page image path (`_temp/renders/page_{k}.png`) and the output spec path (`_temp/specs/page_{k}_spec.json` or `page_{k}.md`), and merges. If subagents are not available (e.g., Microsoft Copilot), process pages one at a time in this session with the same files.

Either way, each page's outputs are written to disk (`_temp/specs/`, `_temp/assets/`) before the next step, so progress is durable. For long documents, resume from the next unprocessed page by checking existing `page_*_spec.json` / `page_*.md` files. Prompt templates for page subagents are in [workflow_playbook.md](./references/workflow_playbook.md).

---

## 3 Conversion Pathways

| Pathway | Document Characteristics | Primary Tooling | Execution Pattern |
| :--- | :--- | :--- | :--- |
| **Pathway 1: Block-Based IR (Default)** | Corporate reports, multi-column articles, financial statements, mixed text + tables + charts + images | `pdf_to_docx` CLI AST Compiler | Extract `page_{k}_spec.json` per page (page subagents or sequential); compile all specs |
| **Pathway 2: Fast-Track Markdown** | Text-heavy papers, simple documentation, standard tables, sequential reading order | Gemini GFM extraction + `docx-mcp: create_from_markdown` | Extract `page_{k}.md` per page (page subagents or sequential); merge and compile |
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
    ├── renders/            # Rendered page PNGs: render-pages writes page_{k}.png (keep source renders here; put DOCX QA renders in renders/docx/)
    ├── specs/              # Extracted AST JSONs (page_*_spec.json, document_spec.json)
    └── build/              # Scratch scripts and temporary build logs
```
This guarantees that all transient files are automatically matched by gitignore rules (`**/_temp/`).

---

## Step-by-Step Execution Workflow

```
[ Orchestrator (this session) ]
       │
       ├─► 1. Inspect PDF structure (page count N, dimensions)
       ├─► 2. Render all pages to PNGs (_temp/renders/page_{k}.png)
       │
       ├─► 3. For each page k = 1..N (one page subagent each, or sequentially here if subagents are unavailable)
       │         └──► Parse page k → _temp/specs/page_{k}_spec.json (or page_{k}.md) and crop assets to _temp/assets/
       │              Resume by skipping pages whose output file already exists
       │
       ├─► 4. Compile assembled specs: uv run python -m pdf_to_docx compile-pages _temp/specs/ -o output/final.docx --assets-dir _temp/assets
       │
       └─► 5. Optional QA: refine specific pages/sections in place (docx-layout-refinement)
```

---

### Phase 1: Orchestrator Intake & Page Rendering
1. Inspect the PDF structure, total page count, orientation, and vector drawings:
   ```bash
   uv run python scripts/pdf_to_docx/inspect_pdf.py path/to/document.pdf
   ```
2. Create standardized subfolders:
   ```powershell
   New-Item -ItemType Directory -Force output, _temp/renders, _temp/assets, _temp/specs, _temp/build | Out-Null
   ```
3. Render all pages to high-resolution PNG images (`200 DPI`) into `_temp/renders` (files are named `page_1.png`, `page_2.png`, ...; without `-o` they go to `./rendered_pages/<stem>/`):
   ```bash
   uv run python -m pdf_to_docx render-pages path/to/document.pdf -o _temp/renders
   ```

---

### Phase 2: Per-Page Extraction

For every page `k` (1-indexed), a page subagent (or this session, if subagents are unavailable) runs:

```bash
uv run python -m pdf_to_docx parse-page path/to/document.pdf --page {k} --image _temp/renders/page_{k}.png -o _temp/specs/page_{k}_spec.json --assets-dir _temp/assets
```

- After each page, inspect `_temp/specs/page_{k}_spec.json` to ensure table headers, cell values, and any charts/images are accurately captured.
- Keep a brief running note (page number, block/table/chart counts, issues) instead of dumping large JSON into chat.
- **Resume-friendly:** if `_temp/specs/page_{k}_spec.json` already exists and is valid, skip and continue.

#### Fast-Track Markdown Alternative (Pathway 2)
For text/narrative-heavy documents:
```bash
uv run python -m pdf_to_docx to-markdown-page path/to/document.pdf --page {k} --image _temp/renders/page_{k}.png -o _temp/specs/page_{k}.md
```

---

### Phase 3: Assembly & Compilation

Once all required page outputs exist in `_temp/specs/` (`page_*_spec.json` for Pathway 1 or `page_*.md` for Pathway 2):

#### For Pathway 1 (Block-Based IR):
Compile the assembled `page_*_spec.json` files into `.docx` in `output/`. Pass `--assets-dir _temp/assets` (the compiler only auto-finds assets in `<pages_dir>/assets/`), and `--ast-path` so the merged AST stays in `_temp/` (`--save-ast` alone writes `output/<stem>_ast.json`):
```bash
uv run python -m pdf_to_docx compile-pages _temp/specs/ -o output/document.docx --title "Document Title" --assets-dir _temp/assets --ast-path _temp/specs/document_ast.json
```
Or use the convenience script (same flags):
```bash
uv run python scripts/pdf_to_docx/compile_pages.py _temp/specs/ -o output/document.docx --assets-dir _temp/assets --ast-path _temp/specs/document_ast.json
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
docx-mcp: create_from_markdown(md_path="_temp/specs/document.md", output_path="output/document.docx")
```
(Parameter names follow [docx_mcp_integration.md](./references/docx_mcp_integration.md); `markdown` takes inline text instead of a file path. If the server rejects `md_path`, check its tool schema.)

---

### Phase 4: Page-Level Visual QA & Surgical Refinement

If visual validation or surgical edits are required:
1. Render an output page headlessly and compare it against the source render (`--page` selects the DOCX page; match it to the source image):
   ```bash
   uv run python scripts/pdf_to_docx/diff_layout.py _temp/renders/page_1.png output/document.docx --page 1
   ```
   The script saves its DOCX render to `output/.temp_render/rendered_p{k}.png` (next to the DOCX). Delete `output/.temp_render/` before delivering.
2. If a specific page (e.g. Page 2) exhibits layout issues (column clipping, chart upgrade needed), fix it with the `docx-layout-refinement` skill (sequential edits to the one DOCX; a read-only audit of the page may run as a subagent):
   - Use the `docx-layout-refinement` skill instructions.
   - Perform surgical edits with `docx-mcp` tools (`set_column_widths`, `insert_bar_chart`, `set_cell_shading`).
   - Keep changes targeted to the affected page/element and re-check the rendered output.

---

## Detailed References

- [Intermediate Representation (IR) Schema Specification](./references/ir_schema_spec.md)
- [Conversion Workflow Playbook & Decision Matrix](./references/workflow_playbook.md)
- [docx-mcp Tooling Guide & Chart Specs](./references/docx_mcp_integration.md)

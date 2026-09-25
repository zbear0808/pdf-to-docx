---
name: pdf-to-docx
description: >-
  Converts PDF documents into high-fidelity, editable Word (.docx) documents using a multimodal
  Block-Based Intermediate Representation (IR), independent page-parallel subagents, PyMuPDF asset harvesting,
  deterministic compilation, and docx-mcp integration. Use when asked to convert, extract, or transcribe a PDF to Word (.docx).
---

# PDF to Editable DOCX Conversion Skill

This skill executes a robust, battle-tested pipeline to transform complex PDF documents into fully editable Microsoft Word (`.docx`) files.

## Core Principle: Page-Parallel Subagent Architecture

> [!IMPORTANT]
> **Context Window Protection via Independent Subagents**
> Processing multiple PDF pages sequentially inside a single conversation context rapidly bloats token counts with high-DPI raster images, bounding-box math, and extensive AST schemas. By Page 3 or 4, large context degradation leads to hallucinations, missed table columns, and token limit exhaustion.
> 
> **Rule**: To keep context clean, scalable, and focused, the orchestrator agent **MUST spawn independent subagents for each page** using `invoke_subagent`. Each subagent operates within its own isolated conversation context, processes exactly one page, and reports back a concise summary.

---

## 3 Conversion Pathways

| Pathway | Document Characteristics | Primary Tooling | Execution Pattern |
| :--- | :--- | :--- | :--- |
| **Pathway 1: Block-Based IR (Default)** | Corporate reports, multi-column articles, financial statements, mixed text + tables + charts + images | `pdf_to_docx` CLI AST Compiler | Page subagents extract `page_{k}_spec.json`; orchestrator compiles |
| **Pathway 2: Fast-Track Markdown** | Text-heavy papers, simple documentation, standard tables, sequential reading order | Gemini GFM extraction + `docx-mcp: create_from_markdown` | Page subagents extract `page_{k}.md`; orchestrator merges and compiles |
| **Pathway 3: CodeAgent Sandbox** | Highly custom ad-hoc layouts, complex math formulas, dynamic data transformations | Direct executable Python scripts with `python-docx` | Dedicated subagent script execution sandbox |

---

## Step-by-Step Execution Workflow

```
[ Orchestrator Agent ]
       │
       ├─► 1. Inspect PDF structure (page count N, dimensions)
       ├─► 2. Render all pages to PNGs (rendered_pages/orig_p{k}.png)
       │
       ├─► 3. Dispatch N Parallel Subagents (invoke_subagent)
       │         │
       │         ├──► [Subagent Page 1] ──► Extracts page_1_spec.json & crops assets
       │         ├──► [Subagent Page 2] ──► Extracts page_2_spec.json & crops assets
       │         └──► [Subagent Page N] ──► Extracts page_N_spec.json & crops assets
       │
       ├─► 4. Reactive Wakeup: Receive concise completion messages (context stays clean!)
       ├─► 5. Compile assembled specs: uv run python -m pdf_to_docx compile-pages
       │
       └─► 6. Optional QA: Dispatch targeted single-page refinement subagents if needed
```

---

### Phase 1: Orchestrator Intake & Page Rendering
1. Inspect the PDF structure, total page count, orientation, and vector drawings:
   ```bash
   uv run python .agents/skills/pdf-to-docx/scripts/inspect_pdf.py path/to/document.pdf
   ```
2. Render all pages to high-resolution PNG images (`200 DPI`) into a shared directory:
   ```bash
   uv run python -m pdf_to_docx render-pages path/to/document.pdf -o ./rendered_pages
   ```
3. Prepare workspace and assets directories:
   ```bash
   mkdir -p .conversion_workspace assets
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
      "Role": "Page 1 Extractor",
      "Model": "flash",
      "Prompt": "You are the dedicated extractor for Page 1 of 'path/to/document.pdf'.\nRendered image: './rendered_pages/orig_p1.png'.\n\nYour task:\n1. Parse Page 1 into the canonical PageSpec AST JSON schema.\n   Run: uv run python -m pdf_to_docx parse-page path/to/document.pdf --page 1 --image ./rendered_pages/orig_p1.png -o .conversion_workspace/page_1_spec.json --assets-dir ./assets\n2. Inspect .conversion_workspace/page_1_spec.json to ensure table headers, cell values, and any charts/images are accurately captured.\n3. Reply with a 2-line completion summary: total blocks, tables, charts, and confirmation of file creation.\nDo NOT dump large JSON in your final reply to keep parent context compact."
    },
    {
      "TypeName": "self",
      "Role": "Page 2 Extractor",
      "Model": "flash",
      "Prompt": "You are the dedicated extractor for Page 2 of 'path/to/document.pdf'.\nRendered image: './rendered_pages/orig_p2.png'.\n\nYour task:\n1. Parse Page 2 into the canonical PageSpec AST JSON schema.\n   Run: uv run python -m pdf_to_docx parse-page path/to/document.pdf --page 2 --image ./rendered_pages/orig_p2.png -o .conversion_workspace/page_2_spec.json --assets-dir ./assets\n2. Inspect .conversion_workspace/page_2_spec.json to ensure table headers, cell values, and any charts/images are accurately captured.\n3. Reply with a 2-line completion summary: total blocks, tables, charts, and confirmation of file creation.\nDo NOT dump large JSON in your final reply to keep parent context compact."
    }
  ]
}
```

> [!TIP]
> **Reactive Wakeup**: Do NOT poll or loop checking on subagents. Stop calling tools and allow the system to notify you when the subagents complete.

#### Fast-Track Markdown Subagent Alternative:
For text/narrative-heavy documents using Pathway 2:
Subagent prompt command:
```bash
uv run python -m pdf_to_docx to-markdown-page path/to/document.pdf --page {k} --image ./rendered_pages/orig_p{k}.png -o .conversion_workspace/page_{k}.md
```

---

### Phase 3: Assembly & Compilation

Once all page subagents report completion:

#### For Pathway 1 (Block-Based IR):
The orchestrator compiles the assembled `page_*_spec.json` files directly into `.docx`:
```bash
uv run python -m pdf_to_docx compile-pages .conversion_workspace/ -o output.docx --title "Document Title"
```
Or use the convenience script:
```bash
uv run python .agents/skills/pdf-to-docx/scripts/compile_pages.py .conversion_workspace/ -o output.docx
```

The compiler deterministically enforces OpenXML structural rules:
- `w:tblHeader`: Repeats header rows across page breaks.
- `w:cantSplit`: Prevents table rows from breaking mid-cell across pages.
- Precise twip margins and cell padding.

#### For Pathway 2 (Fast-Track Markdown):
Merge page markdown files and create the document:
```bash
uv run python -m pdf_to_docx merge-markdown .conversion_workspace/ -o .conversion_workspace/document.md
```
Then use `docx-mcp`:
```text
docx-mcp: create_from_markdown(markdown_path=".conversion_workspace/document.md", output_path="output.docx")
```

---

### Phase 4: Page-Level Visual QA & Surgical Refinement

If visual validation or surgical edits are required:
1. Render output pages headlessly to compare against original rendered PNGs:
   ```bash
   uv run python .agents/skills/pdf-to-docx/scripts/diff_layout.py rendered_pages/orig_p1.png output.docx
   ```
2. If a specific page (e.g. Page 2) exhibits layout issues (column clipping, chart upgrade needed):
   **Dispatch a single-page refinement subagent** (`Role: "Page 2 Refiner"`):
   - The refinement subagent uses the `docx-layout-refinement` skill.
   - It performs surgical edits with `docx-mcp` tools (`set_column_widths`, `insert_bar_chart`, `set_cell_shading`).
   - The orchestrator context remains completely clean of low-level cell/row manipulation tokens.

---

## Detailed References

- [Intermediate Representation (IR) Schema Specification](./references/ir_schema_spec.md)
- [Conversion Workflow Playbook & Decision Matrix](./references/workflow_playbook.md)
- [docx-mcp Tooling Guide & Chart Specs](./references/docx_mcp_integration.md)

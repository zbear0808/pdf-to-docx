---
name: pdf-to-docx
description: >-
  Converts PDF documents into high-fidelity, editable Word (.docx) documents using a multimodal
  Block-Based Intermediate Representation (IR), PyMuPDF asset harvesting, deterministic compilation,
  and docx-mcp integration. Use when asked to convert, extract, or transcribe a PDF to Word (.docx).
---

# PDF to Editable DOCX Conversion Skill

This skill executes a robust, battle-tested pipeline to transform complex PDF documents into fully editable Microsoft Word (`.docx`) files.

Instead of blind, token-expensive granular tool-calling (e.g. calling `add_paragraph` or `add_row` hundreds of times), this skill uses the **Block-Based Intermediate Representation (IR) Compiler Pattern**, combining multimodal spatial intelligence (Gemini Flash), deterministic layout compilers (`python-docx`), and Word OpenXML mastery (`docx-mcp`).

---

## 3 Conversion Pathways

Choose the optimal strategy based on the document type:

| Pathway | Document Characteristics | Primary Tooling |
| :--- | :--- | :--- |
| **Pathway 1: Block-Based IR (Default)** | Corporate reports, multi-column articles, financial statements, mixed text + tables + charts + images | `pdf_to_docx.cli` / AST Compiler |
| **Pathway 2: Fast-Track Markdown** | Text-heavy papers, simple documentation, standard tables, sequential reading order | Gemini GFM extraction + `docx-mcp: create_from_markdown` |
| **Pathway 3: CodeAgent Sandbox** | Highly custom ad-hoc layouts, complex math formulas, dynamic data transformations | Direct executable Python scripts with `python-docx` |

---

## Step-by-Step Execution Workflow

### Phase 1: Intake & Inspection
1. Inspect the PDF structure, total pages, page dimensions, and vector drawings:
   ```bash
   uv run python .agents/skills/pdf-to-docx/scripts/inspect_pdf.py path/to/document.pdf
   ```
2. Render pages to high-resolution PNG images (`200 DPI`) for multimodal inspection:
   ```bash
   uv run python -m pdf_to_docx render-pages path/to/document.pdf -o ./rendered_pages
   ```

### Phase 2: Layout Extraction (AST Generation)
Extract each page into the canonical `DocumentSpec` JSON schema:
- **Headings**: Level (1-4), text, alignment, font sizes.
- **Narratives & Paragraphs**: Runs with bold, italic, font colors, bullet lists, and callout blocks.
- **Tables**: Explicit column headers, rows, alignment, cell shading, and relative widths.
- **Charts**: Identify chart type (bar, line, pie), categories, and series data values for program-based rendering.
- **Figures / Logos / Signatures**: Bounding boxes `[ymin, xmin, ymax, xmax]` (0-1000 scale) for asset cropping.

Refer to the complete schema in [IR Schema Specification](./references/ir_schema_spec.md).

### Phase 3: Asset Cropping & Chart Generation
1. Extract non-text graphics (logos, signatures, diagrams) directly from the PDF:
   ```bash
   uv run python .agents/skills/pdf-to-docx/scripts/crop_asset.py path/to/document.pdf --page 1 --bbox 120,50,300,450 -o ./assets/figure_1.png
   ```
2. For charts:
   - **Rendered High-DPI Charts**: Render via `matplotlib` at 300 DPI with corporate palettes into the document.
   - **Native Office Charts**: Use `docx-mcp: insert_bar_chart`, `insert_line_chart`, or `insert_pie_chart` to insert dynamic Office DrawingML charts (see [docx-mcp Integration Guide](./references/docx_mcp_integration.md)).

### Phase 4: Deterministic DOCX Compilation
Compile the AST into `.docx`:
```bash
uv run python -m pdf_to_docx compile path/to/spec.json -o output.docx
```
Or run the full autonomous pipeline in one command:
```bash
uv run python -m pdf_to_docx convert path/to/document.pdf -o output.docx
```

The compiler automatically applies critical OpenXML rules:
- `w:tblHeader`: Repeats table header rows across page breaks.
- `w:cantSplit`: Prevents table rows from breaking mid-cell across pages.
- Precise twip margins and cell padding.

### Phase 5: Visual Diff & Self-Correction (QA Loop)
1. Render the generated DOCX headlessly to PNG:
   ```bash
   uv run python .agents/skills/pdf-to-docx/scripts/diff_layout.py path/to/original_page.png path/to/output.docx
   ```
2. Gemini Flash compares original vs output side-by-side, scoring layout fidelity (0-100) and flagging any discrepancies (e.g. table column overflow, font size mismatch).
3. If adjustments are needed, fine-tune the AST or make surgical edits using `docx-mcp`.

---

## Detailed References

- [Intermediate Representation (IR) Schema Specification](./references/ir_schema_spec.md)
- [Conversion Workflow Playbook & Decision Matrix](./references/workflow_playbook.md)
- [docx-mcp Tooling Guide & Chart Specs](./references/docx_mcp_integration.md)

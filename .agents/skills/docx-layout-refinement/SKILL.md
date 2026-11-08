---
name: docx-layout-refinement
description: >-
  Audits, polishes, and surgically edits existing Word (.docx) documents using targeted docx-mcp tools
  and native DrawingML charts. Runs as a sequential, single-agent workflow (no subagents).
---

# Word (.docx) Layout Refinement Skill

This skill performs targeted, surgical layout refinement on Word documents using `docx-mcp` tools, native Office DrawingML injection, and direct python-docx scripts.

## Execution Model: Sequential, No Subagents

> [!IMPORTANT]
> **Do not start subagents or use agent-delegation tools** (e.g., `invoke_subagent`, `task`). Microsoft Copilot and similar environments may not support them.
>
> When auditing or refining documents with multiple pages or complex tables/charts, process **one page or one logical section at a time in the current session**. Keep notes per section (target issues, actions taken, files saved) so context stays manageable without delegation.

---

## Directory Layout & Workspace Hygiene

All refinement and visual QA tasks must store modified deliverables in `output/` and temporary page renderings or diff images in `_temp/renders/`:
- `output/`: Refined `.docx` and converted `.pdf` deliverables.
- `_temp/renders/`: Headless page renderings (`docx_p*.png`, `diff_p*.png`).
- `_temp/build/`: Scratch scripts and audit logs.

---

## When to Use This Skill

- Refining a compiled `.docx` based on visual diff critique.
- Upgrading raster chart images to native, editable Office DrawingML charts (`insert_bar_chart`, `insert_line_chart`, `insert_pie_chart`).
- Adjusting table columns, cell padding, or border styles.
- Correcting page margins, section breaks, or orientation.
- Re-packing or compacting worksheets, exams, or problem sets that waste horizontal space next to diagrams. Use the [worksheet-packer skill](../worksheet-packer/SKILL.md) (`uv run worksheet-packer convert doc.docx --columns 2`).

---

## Refinement Checklist (Per Page/Section)

For each page or section that needs refinement, do the following in order:
1. Identify target issues (e.g., squeezed columns, misaligned table, chart should be native DrawingML).
2. `open_document('output.docx')` (or the target file).
3. Apply surgical fixes with `docx-mcp` tools (`set_column_widths`, `insert_bar_chart`/`insert_line_chart`/`insert_pie_chart`, `set_cell_shading`, etc.).
4. `save_document(...)` and `close_document()`.
5. Record a short completion note (page/section, changes made). Then proceed to the next page/section.

---

## Surgical Refinement Procedures

### 1. Document Lifecycle Management
Always follow this pattern when using `docx-mcp`:
```text
1. open_document(path="path/to/doc.docx")
2. [Perform surgical edits: formatting, tables, charts]
3. save_document(output_path="path/to/doc.docx")
4. close_document()
```

### 2. Upgrading Charts to Native Office DrawingML
Standard `python-docx` embeds charts as raster images. When true dynamic, editable Word charts are required, use `docx-mcp`:
1. Find the target paragraph ID (`get_paragraph` or `get_document_info`).
2. Call the appropriate chart tool:
   - Bar chart: `insert_bar_chart(para_id, title, categories, series, width_cm, height_cm)`
   - Line chart: `insert_line_chart(para_id, title, categories, series, width_cm, height_cm)`
   - Pie chart: `insert_pie_chart(para_id, title, categories, series, width_cm, height_cm)`
3. Save the document.

Refer to [Native Charts Guide](./references/native_charts_guide.md) for detailed schema parameters.

### 3. Polishing Tables
To achieve publication-grade tables:
1. **Header Row**: Call `set_header_row(table_index=0, row_index=0)` to repeat headers on subsequent pages.
2. **Column Proportions**: Call `set_column_widths(table_index=0, widths_cm=[...])` to fix squeezed or wrapping columns.
3. **Cell Shading**: Call `set_cell_shading(table_index=0, row=0, col=0, color="1F4E79")`.
4. **Borders**: Call `set_table_borders(table_index=0, style="single", size=4, color="CCCCCC")`.

Refer to [Table Styling Guide](./references/table_styling_guide.md).

### 4. Page Geometry & Section Formatting
- Margins: `set_page_margins(top_cm=2.54, bottom_cm=2.54, left_cm=2.54, right_cm=2.54)`
- Orientation: `set_page_orientation(orientation="landscape")` for wide tabular reports.
- Section Breaks: `add_section_break(break_type="next_page")` before wide tables.

---

## Verification & QA
After applying refinements:
1. Re-render the DOCX page using `diff_layout.py` or `docx-mcp: convert_to_pdf`.
2. Inspect side-by-side against target design or original PDF.
3. Confirm formatting fidelity before delivering to user.

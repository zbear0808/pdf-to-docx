---
name: docx-layout-refinement
description: >-
  Audits, polishes, and surgically edits existing Word (.docx) documents. Use when adjusting table formatting,
  injecting native Office DrawingML charts, modifying margins, fixing line spacing, or applying visual feedback.
---

# Word (.docx) Layout Refinement Skill

This skill performs targeted, surgical layout refinement on Word documents using `docx-mcp` tools and direct python-docx scripts.

Use this skill when:
- Refining a compiled `.docx` based on visual diff critique.
- Upgrading raster chart images to native, editable Office DrawingML charts (`insert_bar_chart`, `insert_line_chart`, `insert_pie_chart`).
- Adjusting table columns, cell padding, or border styles.
- Correcting page margins, section breaks, or orientation.

---

## Refinement Procedures

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

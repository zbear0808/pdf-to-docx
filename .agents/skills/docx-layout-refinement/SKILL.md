---
name: docx-layout-refinement
description: >-
  Audits, polishes, and surgically edits existing Word (.docx) documents using targeted docx-mcp tools,
  native DrawingML charts, and independent page-level refinement subagents to prevent context bloat.
---

# Word (.docx) Layout Refinement Skill

This skill performs targeted, surgical layout refinement on Word documents using `docx-mcp` tools, native Office DrawingML injection, and direct python-docx scripts.

## Context Conservation: Independent Page Refinement Subagents

> [!IMPORTANT]
> **Subagent Delegation for Multi-Page Auditing & Refinement**
> Calling multiple granular `docx-mcp` tools (`get_paragraph`, `modify_cell`, `set_column_widths`, `insert_bar_chart`) across multiple pages quickly fills the parent conversation context with paragraph IDs, XML fragments, and cell coordinates.
>
> **Pattern**: When auditing or refining documents with multiple pages or multiple complex tables/charts, the orchestrator agent **SHOULD dispatch independent subagents per page or section** using `invoke_subagent`. Each subagent performs surgical edits on its assigned page and returns only a concise confirmation.

---

## When to Use This Skill

- Refining a compiled `.docx` based on visual diff critique.
- Upgrading raster chart images to native, editable Office DrawingML charts (`insert_bar_chart`, `insert_line_chart`, `insert_pie_chart`).
- Adjusting table columns, cell padding, or border styles.
- Correcting page margins, section breaks, or orientation.

---

## Refinement Subagent Dispatch Pattern

When multiple pages require refinement, dispatch page-specific subagents concurrently:

```json
{
  "Subagents": [
    {
      "TypeName": "self",
      "Role": "Page 2 Refiner",
      "Model": "flash",
      "Prompt": "You are the Page 2 Refinement subagent for 'output.docx'.\nTarget issues:\n- Table 0: Squeezed columns (widen column 0 to 4.5cm).\n- Chart: Upgrade to native Office DrawingML bar chart.\n\nActions:\n1. open_document('output.docx')\n2. Call set_column_widths(table_index=0, widths_cm=[4.5, 3.0, 3.0, 3.5])\n3. Call insert_bar_chart(...) at the target paragraph\n4. save_document('output.docx') and close_document()\n5. Reply with a 2-line completion summary."
    }
  ]
}
```

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

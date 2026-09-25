# docx-mcp Tooling Guide & Integration Patterns

The `docx-mcp` server provides comprehensive tools for inspecting, generating, and surgically editing Microsoft Word (.docx) files.

---

## Key Tools & Usage

### 1. `create_from_markdown` (Fast-Track Generator)
Creates a complete Word document from markdown in one call.
- **Parameters**: `output_path`, `markdown` (or `md_path`), optional `template_path`.
- **Supports**: GFM tables, headings (# to ######), blockquotes, lists, images, footnotes, and bold/italic runs.
- **When to use**: Text-heavy reports, documentation, summaries.

### 2. `open_document`, `save_document`, `close_document`
Lifecycle management for in-memory document handles.
- **Parameters**: `path: str`, optional `document_handle: str` (e.g. UUID).
- **Note**: Always use `save_document` when edits are complete, followed by `close_document` to free the handle.

### 3. Native DrawingML Charts (No Excel Required)
`docx-mcp` can inject native Office charts:

#### `insert_bar_chart`
```json
{
  "para_id": "p2",
  "title": "Quarterly Revenue ($M)",
  "categories": ["Q1", "Q2", "Q3", "Q4"],
  "series": [
    {"name": "2025", "values": [1.0, 1.2, 1.4, 1.6]},
    {"name": "2026", "values": [1.2, 1.5, 1.8, 2.1]}
  ],
  "width_cm": 15.0,
  "height_cm": 8.5
}
```

#### `insert_line_chart`
```json
{
  "para_id": "p3",
  "title": "Margin Trend (%)",
  "categories": ["Jan", "Feb", "Mar", "Apr"],
  "series": [
    {"name": "Gross Margin", "values": [42.0, 43.5, 44.0, 45.2]}
  ],
  "width_cm": 15.0,
  "height_cm": 8.0
}
```

#### `insert_pie_chart`
```json
{
  "para_id": "p4",
  "title": "Market Share",
  "categories": ["Product A", "Product B", "Product C"],
  "series": [
    {"name": "Share", "values": [55.0, 30.0, 15.0]}
  ],
  "width_cm": 12.0,
  "height_cm": 8.0
}
```

### 4. Table Formatting Tools
- `set_column_widths`: `widths_cm: [5.0, 4.0, 3.5]`
- `set_cell_shading`: `color: "1F4E79"`
- `set_header_row`: marks row 0 as header.
- `set_table_borders`: customize style, color, size.
- `modify_cell`: surgical edit of text or alignment within a cell.

### 5. Document & Page Layout
- `set_page_margins`: `top_cm`, `bottom_cm`, `left_cm`, `right_cm`.
- `set_page_orientation`: `"portrait"` or `"landscape"`.
- `add_page_break`: insert manual break.
- `convert_to_pdf`: render open document to PDF via headless LibreOffice.

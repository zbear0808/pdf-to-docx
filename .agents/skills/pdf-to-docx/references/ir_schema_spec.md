# Intermediate Representation (IR) Schema Specification

The PDF to DOCX converter relies on a canonical Abstract Syntax Tree (AST) called `DocumentSpec`. This decouples multimodal perception from document layout compilation.

---

## Schema Architecture

```text
DocumentSpec
├── metadata (title, author, company, theme_hex, default_font, default_font_size_pt)
└── pages: List[PageSpec]
    ├── page_number: int
    ├── width_pt: float, height_pt: float, orientation: "portrait" | "landscape"
    └── blocks: List[DocumentBlock]
        ├── HeadingBlock (level: 1..6, text, alignment, bbox)
        ├── ParagraphBlock (runs: List[TextRun], list_type, is_callout, bbox)
        ├── TableBlock (headers, rows, col_widths_pct, cant_split, repeat_header)
        ├── ChartBlock (chart_type, title, categories, series, bbox)
        ├── ImageBlock (image_path, caption, bbox, width_inches, is_vector)
        └── PageBreakBlock
```

---

## JSON Block Examples

### 1. Heading Block
```json
{
  "type": "heading",
  "level": 1,
  "text": "Executive Summary",
  "alignment": "left",
  "bbox": {"ymin": 50, "xmin": 70, "ymax": 90, "xmax": 500}
}
```

### 2. Paragraph Block with Rich Runs
```json
{
  "type": "paragraph",
  "alignment": "left",
  "list_type": "none",
  "is_callout": false,
  "runs": [
    {"text": "Total revenue grew by "},
    {"text": "24.5% year-over-year", "bold": true, "color_hex": "#1F4E79"},
    {"text": ", surpassing industry benchmarks."}
  ]
}
```

### 3. Native Table Block
```json
{
  "type": "table",
  "headers": ["Department", "Budget", "Actual", "Variance"],
  "rows": [
    ["Engineering", "$1.2M", "$1.15M", "+$50K"],
    ["Marketing", "$800K", "$850K", "-$50K"]
  ],
  "col_widths_pct": [35.0, 22.0, 22.0, 21.0],
  "cant_split": true,
  "repeat_header": true,
  "style_name": "Table Grid"
}
```

### 4. Chart Block (Programmatic or docx-mcp)
```json
{
  "type": "chart",
  "title": "Quarterly Margin Progression (%)",
  "chart_type": "bar",
  "categories": ["Q1", "Q2", "Q3", "Q4"],
  "series": [
    {"name": "Gross Margin", "values": [42.1, 44.5, 45.0, 46.2]},
    {"name": "Operating Margin", "values": [18.2, 20.1, 21.5, 23.0]}
  ],
  "width_inches": 6.0,
  "height_inches": 3.2
}
```

### 5. Cropped Image / Figure Block
```json
{
  "type": "image",
  "image_path": "assets/p1_figure_1.png",
  "caption": "Figure 1: Architectural System Topology",
  "width_inches": 5.5,
  "bbox": {"ymin": 350, "xmin": 80, "ymax": 620, "xmax": 920}
}
```

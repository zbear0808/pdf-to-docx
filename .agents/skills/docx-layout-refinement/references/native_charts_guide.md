# Native Office Charts Reference Guide

This reference documents the parameter structures and formatting options for inserting native DrawingML charts into Word documents using `docx-mcp`.

---

## 1. Bar Chart (`insert_bar_chart`)

Inserts a native clustered or grouped bar chart.

### Parameters
- `para_id` (str, required): The ID of the paragraph before/after which to insert the chart.
- `title` (str, required): Title displayed above chart.
- `categories` (List[str], required): Labels for the category (X) axis.
- `series` (List[Dict], required): List of series objects `[{"name": str, "values": [float, ...]}]`.
- `width_cm` (float, optional, default: 14): Width in centimeters.
- `height_cm` (float, optional, default: 9): Height in centimeters.

### Example Call
```json
{
  "para_id": "p5",
  "title": "Division Performance (USD Millions)",
  "categories": ["Cloud", "Security", "Hardware", "Consulting"],
  "series": [
    {"name": "2025 Target", "values": [320.0, 180.0, 140.0, 95.0]},
    {"name": "2025 Actual", "values": [345.0, 192.0, 130.0, 110.0]}
  ],
  "width_cm": 15.0,
  "height_cm": 8.5
}
```

---

## 2. Line Chart (`insert_line_chart`)

Inserts a continuous line chart with data markers.

### Parameters
- `para_id` (str, required): Paragraph ID.
- `title` (str, required): Chart title.
- `categories` (List[str], required): Time periods or category axis points.
- `series` (List[Dict], required): Series data `[{"name": str, "values": [float, ...]}]`.
- `width_cm` (float, optional, default: 14).
- `height_cm` (float, optional, default: 9).

---

## 3. Pie Chart (`insert_pie_chart`)

Inserts a proportional pie chart.

### Parameters
- `para_id` (str, required): Paragraph ID.
- `title` (str, required): Chart title.
- `categories` (List[str], required): Slice category names.
- `series` (List[Dict], required): `[{"name": "Share", "values": [float, ...]}]`.
- `width_cm` (float, optional, default: 12).
- `height_cm` (float, optional, default: 8).

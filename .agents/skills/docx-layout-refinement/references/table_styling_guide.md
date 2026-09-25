# Word Table Styling & Layout Reference Guide

Achieving publication-quality tables requires controlling cell padding, column widths, border geometry, and pagination behavior.

---

## 1. Column Width Calculations
Standard page width for US Letter with 1-inch margins:
- Total page width: `8.5 inches = 21.59 cm`
- Margin left + right: `2.0 inches = 5.08 cm`
- Available table width: `6.5 inches = 16.51 cm`

When specifying `set_column_widths`, ensure the sum of `widths_cm` matches `~16.5 cm` for full-width portrait tables.

### Width Allocation Formula
```python
col_widths_cm = [16.51 * (pct / 100.0) for pct in col_percentages]
```

---

## 2. Table Borders & Shading via docx-mcp

### Clean Corporate Border Recipe
```python
# Subtle light grey borders
set_table_borders(
    table_index=0,
    style="single",
    size=4,          # 1/8 pt = 0.5 pt
    color="D3D3D3"   # Light grey
)
```

### Cell Background Shading
```python
# Dark corporate theme for header
set_cell_shading(table_index=0, row=0, col=0, color="1F4E79")

# Zebra alternating row shading
for r in range(1, row_count, 2):
    for c in range(col_count):
        set_cell_shading(table_index=0, row=r, col=c, color="F8FAFC")
```

---

## 3. Pagination Controls
1. **Never split a row mid-cell**: In OpenXML, set `w:cantSplit` on each row.
2. **Always repeat header**: Set `w:tblHeader` on row index 0 so that if a table overflows across page 1 and page 2, the headers are immediately visible to the reader.

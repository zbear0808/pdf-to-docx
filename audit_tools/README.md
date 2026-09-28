# PDF-to-DOCX Audit Tools Suite

A dedicated collection of CLI scripts designed to inspect, audit, and verify the quality and layout fidelity of generated Word (`.docx`) documents against their source PDFs and intermediate representations.

---

## Tool Overview

| Script | Purpose | Key Checks & Diagnostics |
| :--- | :--- | :--- |
| [`audit_docx.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_docx.py) | **DOCX Internal Structure & Styling** | Scans all paragraphs, tables, and runs for unwanted blue theme colors (`#1F4E79`), table header repetition (`w:tblHeader`), cell text duplication artifacts (e.g. `"Party WParty W"`), DrawingML image sizes, aspect ratios, and accessibility alt text. |
| [`audit_pdf_assets.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_pdf_assets.py) | **Source PDF Asset & Geometry Discovery** | Analyzes PDF pages for native embedded raster images (`xref`, dimensions, format), vector drawing path clusters, text blocks, and computes exact normalized `[0, 1000]` bounding boxes. |
| [`compare_pdf_to_docx.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/compare_pdf_to_docx.py) | **End-to-End Comparative Fidelity** | Compares source PDF directly against target DOCX: verifies visual asset count parity, aspect ratio preservation ($< 2\%$ delta), table counts, word count volume, and issues an overall Fidelity Score (0–100). |
| [`audit_image_boundaries.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_image_boundaries.py) | **Edge Perimeter & Cutoff Auditor** | Scans image borders (top, bottom, left, right perimeter pixels) for non-background density to detect severed axes, truncated labels, or incomplete figure crops. Also tests PDF bounding boxes directly. |
| [`audit_ast.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_ast.py) | **Intermediate Representation (AST) Validator** | Validates the AST JSON against the Pydantic `DocumentSpec` schema, checks bounding box boundaries ($0 \le y_{min} < y_{max} \le 1000$), audits table structures, and checks that referenced image paths exist. |
| [`run_all_audits.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/run_all_audits.py) | **Master Audit Runner** | Executes the entire audit suite in one command, producing a unified multi-stage scorecard. |

---

## Quick Start & CLI Usage

### 1. One-Click Master Audit
Run the entire suite against a source PDF and target DOCX:
```bash
python audit_tools/run_all_audits.py "tests/stats merged quiz unit 1.pdf" "tests/stats_merged_quiz_unified.docx"
```
Optional flags:
```bash
python audit_tools/run_all_audits.py "tests/stats merged quiz unit 1.pdf" "tests/stats_merged_quiz_unified.docx" \
  --ast "tests/stats_merged_quiz_multimodal_ast.json" \
  --assets "tests/.workspace_stats merged quiz unit 1/assets"
```

---

### 2. Auditing a DOCX Document Directly
Inspect typography, tables, and images of any generated Word document:
```bash
python audit_tools/audit_docx.py "tests/stats_merged_quiz_unified.docx"
```
**Output Highlights:**
- **Typography:** Flags any run styled with theme colors when neutral black was requested.
- **Tables:** Flags missing repeating headers or cell string duplication.
- **Images:** Displays rendered width/height in inches, aspect ratio, and alt text.

---

### 3. Discovering Assets & Vector Drawings in a PDF
Inspect what visual assets exist in the original PDF:
```bash
python audit_tools/audit_pdf_assets.py "tests/stats merged quiz unit 1.pdf"
```
Audit a specific page and optionally save cropped image previews:
```bash
python audit_tools/audit_pdf_assets.py "tests/stats merged quiz unit 1.pdf" --page 6 --save-crops "scratch/crops"
```

---

### 4. Side-by-Side PDF vs DOCX Comparison
Verify fidelity, image parity, and aspect ratio preservation:
```bash
python audit_tools/compare_pdf_to_docx.py "tests/stats merged quiz unit 1.pdf" "tests/stats_merged_quiz_unified.docx"
```
**Report Sample:**
```
===========================================================================
 PDF vs DOCX FIDELITY COMPARISON
===========================================================================
Source PDF : stats merged quiz unit 1.pdf
Target DOCX: stats_merged_quiz_unified.docx
Fidelity Score: 100/100 -> [PASSED - HIGH FIDELITY]
---------------------------------------------------------------------------

[1] STRUCTURAL METRICS
  Metric                    PDF (Source)       DOCX (Compiled)    Parity Status
  ------------------------- ------------------ ------------------ ---------------
  Pages / Sections          7                  92 paras / 1 sects OK
  Word Count (est.)         1147               1297               113.1%
  Visual Graphics/Images    7                  7                  MATCH
  Tables                    N/A (visual)       3                  3 detected

[2] IMAGE ASSET & ASPECT RATIO AUDIT (7 images)
  Image #1  | PDF AR: 2.701 -> DOCX AR: 2.702 ( 0.04% diff) [+ LOCKED]
  Image #2  | PDF AR: 2.701 -> DOCX AR: 2.702 ( 0.04% diff) [+ LOCKED]
  Image #3  | PDF AR: 1.791 -> DOCX AR: 1.791 ( 0.00% diff) [+ LOCKED]
  Image #4  | PDF AR: 3.886 -> DOCX AR: 3.888 ( 0.05% diff) [+ LOCKED]
  Image #5  | PDF AR: 3.553 -> DOCX AR: 3.554 ( 0.03% diff) [+ LOCKED]
  Image #6  | PDF AR: 2.078 -> DOCX AR: 2.078 ( 0.00% diff) [+ LOCKED]
  Image #7  | PDF AR: 2.017 -> DOCX AR: 2.017 ( 0.00% diff) [+ LOCKED]

[3] DISCREPANCIES & AUDIT FLAGS
  + None! High fidelity achieved across all measured dimensions.
===========================================================================
```

---

### 5. Detecting Graphic Cutoffs & Truncated Labels
Scan all images in an assets directory to ensure no borders slice through visual content:
```bash
python audit_tools/audit_image_boundaries.py "tests/.workspace_stats merged quiz unit 1/assets"
```
Test a specific PDF bounding box `[ymin, xmin, ymax, xmax]` on a page to verify if it slices content before cropping:
```bash
python audit_tools/audit_image_boundaries.py dummy --pdf "tests/stats merged quiz unit 1.pdf" --page 6 --bbox 286 236 432 794
```

---

### 6. Auditing Intermediate AST JSON
Validate intermediate AST JSON files produced during conversion:
```bash
python audit_tools/audit_ast.py "tests/stats_merged_quiz_multimodal_ast.json"
```

"""Creates a realistic sample PDF with text, table, and shapes to test extraction."""

import pymupdf as fitz
from pathlib import Path

def create_sample_pdf(pdf_path: Path):
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter

    # Title
    page.insert_text(fitz.Point(54, 72), "Quarterly Financial Analysis", fontsize=20, fontname="helv", color=(0.12, 0.31, 0.47))

    # Subtitle / Paragraph
    page.insert_text(fitz.Point(54, 110), "Prepared for Executive Leadership - Fiscal Year 2026", fontsize=11, fontname="helv", color=(0.3, 0.3, 0.3))

    # Narrative Paragraph
    body_text = (
        "Operating revenue increased significantly during the second quarter due to strong demand across cloud "
        "services and managed infrastructure. Gross margins expanded by 340 basis points year-over-year."
    )
    rect = fitz.Rect(54, 135, 558, 190)
    page.insert_textbox(rect, body_text, fontsize=10, fontname="helv", color=(0.1, 0.1, 0.1))

    # Draw a table
    headers = ["Segment", "Q1 Revenue", "Q2 Revenue", "Growth"]
    rows = [
        ["Enterprise Cloud", "$450M", "$560M", "+24.4%"],
        ["Platform Services", "$210M", "$245M", "+16.7%"],
        ["Advisory & Consulting", "$95M", "$110M", "+15.8%"],
    ]

    x_start = 54
    y_start = 220
    col_widths = [160, 110, 110, 120]
    row_height = 24

    # Header row background
    header_rect = fitz.Rect(x_start, y_start, x_start + sum(col_widths), y_start + row_height)
    page.draw_rect(header_rect, color=(0.12, 0.31, 0.47), fill=(0.12, 0.31, 0.47))

    # Header text
    cur_x = x_start
    for col_idx, h in enumerate(headers):
        page.insert_text(fitz.Point(cur_x + 8, y_start + 16), h, fontsize=10, fontname="helv", color=(1, 1, 1))
        cur_x += col_widths[col_idx]

    # Rows
    for r_idx, row in enumerate(rows):
        cur_y = y_start + (r_idx + 1) * row_height
        cur_x = x_start
        bg_color = (0.95, 0.96, 0.98) if r_idx % 2 == 1 else (1, 1, 1)
        r_rect = fitz.Rect(x_start, cur_y, x_start + sum(col_widths), cur_y + row_height)
        page.draw_rect(r_rect, color=(0.8, 0.8, 0.8), fill=bg_color)

        for col_idx, val in enumerate(row):
            page.insert_text(fitz.Point(cur_x + 8, cur_y + 16), val, fontsize=9.5, fontname="helv", color=(0.15, 0.15, 0.15))
            cur_x += col_widths[col_idx]

    # Draw a vector graphic / logo box
    logo_rect = fitz.Rect(54, 340, 200, 420)
    page.draw_rect(logo_rect, color=(0.12, 0.31, 0.47), fill=(0.9, 0.93, 0.97), width=2)
    page.draw_circle(fitz.Point(127, 380), 25, color=(0.12, 0.31, 0.47), fill=(0.2, 0.45, 0.7))
    page.insert_text(fitz.Point(100, 410), "Vector Diagram", fontsize=8, fontname="helv", color=(0.12, 0.31, 0.47))

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(pdf_path))
    doc.close()
    print(f"Sample PDF created at: {pdf_path}")

if __name__ == "__main__":
    create_sample_pdf(Path("tests/sample.pdf"))

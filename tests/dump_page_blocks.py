"""Dump text blocks with positions and styling for pages 2 through 7."""

import json
from pathlib import Path
import pymupdf

pdf_path = Path("tests/stats merged quiz unit 1.pdf")
doc = pymupdf.open(str(pdf_path))

for p_num in range(1, len(doc)):
    page = doc[p_num]
    print(f"===================== PAGE {p_num + 1} =====================")
    blocks = page.get_text("blocks")
    for b in blocks:
        # b is (x0, y0, x1, y1, text, block_no, block_type)
        if b[6] == 0:  # text
            print(f"[{b[1]:.1f}, {b[0]:.1f}, {b[3]:.1f}, {b[2]:.1f}]")
            print(repr(b[4]))

"""Merge PDFs into one duplex-ready packet. Each --group starts on a front page (odd page number);
files inside a group follow each other directly. Adds a bookmark per file.

  make_packet.py --out "Unit 2 Student Packet.pdf" \
      --group "L1 Handout.pdf" "L1 Practice.pdf" --group "L2 Handout.pdf" "L2 Practice.pdf"
"""
import argparse
from pathlib import Path

import pymupdf

ap = argparse.ArgumentParser()
ap.add_argument("--out", type=Path, required=True)
ap.add_argument("--group", nargs="+", action="append", required=True)
a = ap.parse_args()

merged, toc, starts = pymupdf.open(), [], []
for g, files in enumerate(a.group):
    if g and merged.page_count % 2:
        last = merged[-1].rect
        merged.new_page(width=last.width, height=last.height)
    starts.append(merged.page_count + 1)
    for f in files:
        with pymupdf.open(f) as d:
            toc.append([1, Path(f).stem, merged.page_count + 1])
            merged.insert_pdf(d)
merged.set_toc(toc)
merged.save(a.out)
print(f"{a.out.name}: {merged.page_count} pages; groups start on pages {starts}")

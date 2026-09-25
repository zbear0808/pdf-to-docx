"""Extract all embedded images and analyze text spans per page."""

import json
from pathlib import Path
import pymupdf

pdf_path = Path("tests/stats merged quiz unit 1.pdf")
doc = pymupdf.open(str(pdf_path))
out_dir = Path("extracted_assets")
out_dir.mkdir(exist_ok=True)

extracted = []

for p_idx, page in enumerate(doc):
    imgs = page.get_images()
    page_imgs = []
    for img_idx, img in enumerate(imgs):
        xref = img[0]
        base_img = doc.extract_image(xref)
        img_bytes = base_img["image"]
        img_ext = base_img["ext"]
        img_name = f"page_{p_idx+1}_img_{img_idx+1}_xref{xref}.{img_ext}"
        img_file = out_dir / img_name
        img_file.write_bytes(img_bytes)
        
        rects = [list(r) for r in page.get_image_rects(xref)]
        page_imgs.append({
            "xref": xref,
            "filename": str(img_file),
            "width": base_img["width"],
            "height": base_img["height"],
            "rects": rects,
        })
    extracted.append({
        "page": p_idx + 1,
        "images": page_imgs,
    })

print(f"Extracted {sum(len(p['images']) for p in extracted)} images successfully.")
for p in extracted:
    print(f"Page {p['page']}: {len(p['images'])} images")
    for img in p['images']:
        print(f"  {img['filename']}: {img['width']}x{img['height']}, rects={img['rects']}")

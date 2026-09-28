import pymupdf as fitz
from pathlib import Path
import json

doc = fitz.open("tests/stats merged quiz unit 1.pdf")

def inspect_page_assets(page_num):
    page = doc[page_num - 1]
    rect = page.rect
    print(f"\n{'='*25} PAGE {page_num} ({rect.width} x {rect.height}) {'='*25}")
    
    # 1. Native embedded images
    imgs = page.get_images(full=True)
    print(f"[1] Embedded Images: {len(imgs)}")
    for i, img in enumerate(imgs):
        xref = img[0]
        base_img = doc.extract_image(xref)
        placements = page.get_image_rects(xref)
        print(f"    Image {i}: xref={xref}, size={base_img['width']}x{base_img['height']} ({base_img['ext']}), placements={placements}")
        
    # 2. Text blocks around the page
    blocks = page.get_text("blocks")
    print(f"[2] Text Blocks: {len(blocks)}")
    
    # 3. Vector drawings
    drawings = page.get_drawings()
    print(f"[3] Vector Drawings: {len(drawings)}")
    valid_drawings = [d for d in drawings if d["rect"].width > 5 and d["rect"].height > 5]
    print(f"    Valid non-trivial drawings (>5x5): {len(valid_drawings)}")
    if valid_drawings:
        combined = fitz.Rect(valid_drawings[0]["rect"])
        for d in valid_drawings[1:]:
            combined |= fitz.Rect(d["rect"])
        print(f"    Combined drawing rect: {combined}")

print("Testing Page 1:")
inspect_page_assets(1)
print("\nTesting Page 6:")
inspect_page_assets(6)
print("\nTesting Page 7:")
inspect_page_assets(7)

import pymupdf as fitz
from pathlib import Path
import json

doc = fitz.open("tests/stats merged quiz unit 1.pdf")
with open("tests/stats_merged_quiz_multimodal_ast.json", "r", encoding="utf-8") as f:
    ast = json.load(f)

print("=== TESTING RECONCILIATION ON ALL PAGES ===")

for pno, page in enumerate(doc):
    p_num = pno + 1
    page_rect = page.rect
    w, h = page_rect.width, page_rect.height
    
    # Get native images
    native_imgs = []
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        for r in page.get_image_rects(xref):
            # normalized 0-1000
            native_imgs.append({
                "xref": xref,
                "rect": r,
                "norm_box": [r.y0 / h * 1000, r.x0 / w * 1000, r.y1 / h * 1000, r.x1 / w * 1000]
            })
            
    # Check Gemini's blocks
    page_ast = ast["pages"][pno] if pno < len(ast["pages"]) else {}
    for b_idx, block in enumerate(page_ast.get("blocks", [])):
        b_type = block.get("type")
        if b_type in ("image", "chart") and block.get("bbox"):
            bbox = block["bbox"]
            llm_y0 = bbox["ymin"] / 1000.0 * h
            llm_x0 = bbox["xmin"] / 1000.0 * w
            llm_y1 = bbox["ymax"] / 1000.0 * h
            llm_x1 = bbox["xmax"] / 1000.0 * w
            llm_rect = fitz.Rect(llm_x0, llm_y0, llm_x1, llm_y1)
            
            # Find best overlapping native image
            matched_native = None
            best_iou = 0.0
            for n_img in native_imgs:
                n_rect = n_img["rect"]
                intersect = llm_rect & n_rect
                if not intersect.is_empty:
                    union = llm_rect | n_rect
                    iou = intersect.get_area() / union.get_area()
                    overlap_ratio = intersect.get_area() / min(llm_rect.get_area(), n_rect.get_area())
                    if overlap_ratio > 0.4:
                        matched_native = n_img
                        best_iou = iou
                        break
                        
            print(f"Page {p_num} Block {b_idx} ({b_type.upper()}):")
            print(f"  LLM BBox: [ymin={bbox['ymin']}, xmin={bbox['xmin']}, ymax={bbox['ymax']}, xmax={bbox['xmax']}] -> rect={llm_rect}")
            if matched_native:
                nr = matched_native['rect']
                print(f"  --> MATCHED NATIVE IMAGE xref={matched_native['xref']}! Ground truth rect={nr}")
                print(f"      Snapped BBox: [ymin={nr.y0/h*1000:.1f}, xmin={nr.x0/w*1000:.1f}, ymax={nr.y1/h*1000:.1f}, xmax={nr.x1/w*1000:.1f}]")
            else:
                print(f"  --> No native image match. Using vector/whitespace-snapped crop.")


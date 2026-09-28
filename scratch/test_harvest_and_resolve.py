import pymupdf as fitz
from pathlib import Path
import json

doc = fitz.open("tests/stats merged quiz unit 1.pdf")

def harvest_page_assets(page: fitz.Page):
    """Discovers all native visual candidates on a page (images and vector clusters)."""
    h = page.rect.height
    w = page.rect.width
    candidates = []
    
    # 1. Native embedded images
    seen_xrefs = set()
    for img_info in page.get_images(full=True):
        xref = img_info[0]
        if xref in seen_xrefs:
            continue
        seen_xrefs.add(xref)
        base_img = doc.extract_image(xref)
        placements = page.get_image_rects(xref)
        for r in placements:
            # Skip full-page background images if there's digital text
            if r.width >= w * 0.95 and r.height >= h * 0.95 and len(page.get_text()) > 200:
                continue
            candidates.append({
                "type": "native_image",
                "xref": xref,
                "rect": r,
                "ext": base_img["ext"],
                "width_px": base_img["width"],
                "height_px": base_img["height"],
            })
            
    # 2. Vector drawing clusters
    drawings = page.get_drawings()
    # Filter out page borders or tiny decorative rules
    valid_drawings = [
        d for d in drawings 
        if d["rect"].width > 8 and d["rect"].height > 8
        and not (d["rect"].width >= w * 0.95 and d["rect"].height >= h * 0.95)
    ]
    if valid_drawings:
        # Cluster overlapping or nearby paths (< 15 pt distance)
        clusters = []
        for d in valid_drawings:
            d_rect = fitz.Rect(d["rect"])
            merged = False
            for c in clusters:
                # If close or overlapping
                expanded_c = fitz.Rect(c["rect"].x0 - 15, c["rect"].y0 - 15, c["rect"].x1 + 15, c["rect"].y1 + 15)
                if expanded_c.intersects(d_rect):
                    c["rect"] |= d_rect
                    c["count"] += 1
                    merged = True
                    break
            if not merged:
                clusters.append({"rect": d_rect, "count": 1})
                
        # Filter clusters to those with meaningful complexity (>= 3 paths or area > 1000)
        for c in clusters:
            r = c["rect"]
            if c["count"] >= 3 or (r.width * r.height > 2000):
                # Don't add if already covered by a native image
                covered = False
                for cand in candidates:
                    if (cand["rect"] & r).get_area() / r.get_area() > 0.7:
                        covered = True
                        break
                if not covered:
                    candidates.append({
                        "type": "vector_cluster",
                        "xref": None,
                        "rect": r,
                        "ext": "png",
                        "path_count": c["count"]
                    })
                    
    return candidates

def resolve_visual_asset(page: fitz.Page, requested_bbox: list, candidates: list, output_path: Path, dpi: int = 300):
    """Resolves an asset request: snaps to native image or renders vector cluster / crop."""
    w, h = page.rect.width, page.rect.height
    ymin, xmin, ymax, xmax = requested_bbox
    req_rect = fitz.Rect(
        (xmin / 1000.0) * w,
        (ymin / 1000.0) * h,
        (xmax / 1000.0) * w,
        (ymax / 1000.0) * h,
    )
    
    # 1. Match against candidates
    best_candidate = None
    best_overlap = 0.0
    for cand in candidates:
        c_rect = cand["rect"]
        intersect = req_rect & c_rect
        if not intersect.is_empty:
            overlap = intersect.get_area() / min(req_rect.get_area(), c_rect.get_area())
            if overlap > 0.4 and overlap > best_overlap:
                best_overlap = overlap
                best_candidate = cand
                
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if best_candidate and best_candidate["type"] == "native_image":
        # Extract native image directly!
        xref = best_candidate["xref"]
        base_img = doc.extract_image(xref)
        image_bytes = base_img["image"]
        output_path.write_bytes(image_bytes)
        c_rect = best_candidate["rect"]
        return {
            "source": "native_image",
            "rect": c_rect,
            "width_inches": round(c_rect.width / 72.0, 2),
            "height_inches": round(c_rect.height / 72.0, 2),
            "file": str(output_path)
        }
    elif best_candidate and best_candidate["type"] == "vector_cluster":
        # Render vector cluster
        c_rect = best_candidate["rect"]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=c_rect, alpha=False)
        pix.save(str(output_path))
        return {
            "source": "vector_cluster",
            "rect": c_rect,
            "width_inches": round(c_rect.width / 72.0, 2),
            "height_inches": round(c_rect.height / 72.0, 2),
            "file": str(output_path)
        }
    else:
        # Fallback to high-res region crop
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, clip=req_rect, alpha=False)
        pix.save(str(output_path))
        return {
            "source": "pixmap_crop",
            "rect": req_rect,
            "width_inches": round(req_rect.width / 72.0, 2),
            "height_inches": round(req_rect.height / 72.0, 2),
            "file": str(output_path)
        }

print("Testing Page 6 Resolution:")
page6 = doc[5]
cands6 = harvest_page_assets(page6)
print(f"Candidates on Page 6: {len(cands6)}")
for c in cands6:
    print(f"  {c['type']} rect={c['rect']}")
out_file6 = Path("scratch/test_p6_resolved.png")
res6 = resolve_visual_asset(page6, [286, 236, 432, 794], cands6, out_file6)
print(f"Resolved Page 6: {res6}")

print("\nTesting Page 7 Resolution:")
page7 = doc[6]
cands7 = harvest_page_assets(page7)
print(f"Candidates on Page 7: {len(cands7)}")
for c in cands7:
    print(f"  {c['type']} rect={c['rect']}")
out_file7 = Path("scratch/test_p7_resolved.png")
res7 = resolve_visual_asset(page7, [160, 196, 432, 801], cands7, out_file7)
print(f"Resolved Page 7: {res7}")

print("\nTesting Page 1 Resolution:")
page1 = doc[0]
cands1 = harvest_page_assets(page1)
print(f"Candidates on Page 1: {len(cands1)}")
for c in cands1:
    print(f"  {c['type']} rect={c['rect']}")
out_file1 = Path("scratch/test_p1_top_resolved.png")
res1 = resolve_visual_asset(page1, [412, 126, 605, 878], cands1, out_file1)
print(f"Resolved Page 1 Top: {res1}")

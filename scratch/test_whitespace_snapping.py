import pymupdf as fitz

def snap_to_whitespace(page: fitz.Page, rect: fitz.Rect, pad: float = 4.0, max_search: float = 40.0) -> fitz.Rect:
    """Expands a bounding box outward if its edges cut through non-background pixels."""
    # Render page at 150 DPI for fast pixel scanning
    dpi = 150
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    
    # Coordinates in pixmap pixels
    px0 = max(0, int(rect.x0 * zoom))
    py0 = max(0, int(rect.y0 * zoom))
    px1 = min(pix.width, int(rect.x1 * zoom))
    py1 = min(pix.height, int(rect.y1 * zoom))
    
    def row_is_whitespace(y: int, x_start: int, x_end: int) -> bool:
        if y < 0 or y >= pix.height:
            return True
        non_white = 0
        total = max(1, x_end - x_start)
        for x in range(x_start, x_end):
            r, g, b = pix.pixel(x, y)
            if r < 240 or g < 240 or b < 240:
                non_white += 1
                if non_white / total > 0.01:
                    return False
        return True

    def col_is_whitespace(x: int, y_start: int, y_end: int) -> bool:
        if x < 0 or x >= pix.width:
            return True
        non_white = 0
        total = max(1, y_end - y_start)
        for y in range(y_start, y_end):
            r, g, b = pix.pixel(x, y)
            if r < 240 or g < 240 or b < 240:
                non_white += 1
                if non_white / total > 0.01:
                    return False
        return True

    # Check top edge (py0)
    max_search_px = int(max_search * zoom)
    new_py0 = py0
    if not row_is_whitespace(py0, px0, px1):
        # Slicing content at top! Scan upwards
        for y in range(py0 - 1, max(0, py0 - max_search_px), -1):
            if row_is_whitespace(y, px0, px1):
                new_py0 = y
                break

    # Check bottom edge (py1)
    new_py1 = py1
    if not row_is_whitespace(py1, px0, px1):
        # Slicing content at bottom! Scan downwards
        for y in range(py1 + 1, min(pix.height, py1 + max_search_px)):
            if row_is_whitespace(y, px0, px1):
                new_py1 = y
                break

    # Convert back to points
    snapped_rect = fitz.Rect(
        rect.x0,
        new_py0 / zoom - pad,
        rect.x1,
        new_py1 / zoom + pad
    )
    # Clip to page boundary
    return snapped_rect & page.rect

doc = fitz.open("tests/stats merged quiz unit 1.pdf")
page6 = doc[5] # page 6

# Suppose Gemini truncated ymax at 342.1 pt (432 normalized)
truncated_rect = fitz.Rect(144.4, 226.5, 485.9, 342.1)
print(f"Truncated rect: {truncated_rect}")
snapped = snap_to_whitespace(page6, truncated_rect, max_search=70.0)
print(f"Whitespace snapped rect: {snapped}")
print(f"Ground truth native image rect was: Rect(152.09, 236.00, 484.33, 395.92)")


# Cleanup Plan 03: `audit_tools/` Deprecation & Heuristic Migration

This document details the status of the [`audit_tools/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools) package, evaluates its individual audit modules, and provides an actionable plan to harvest its valuable image boundary cutoff detection logic into [`src/worksheet_packer/image_utils.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/worksheet_packer/image_utils.py) before retiring the rest of the package.

---

## 1. Background & Current Status

Early in the project, [`audit_tools/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools) was created as a diagnostic suite to evaluate conversion quality across five dimensions:
1. Source PDF visual asset geometry ([`audit_pdf_assets.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_pdf_assets.py))
2. Compiled DOCX internal OpenXML structure and typography ([`audit_docx.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_docx.py))
3. End-to-end PDF vs DOCX comparative fidelity ([`compare_pdf_to_docx.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/compare_pdf_to_docx.py))
4. Cropped diagram edge cutoff detection ([`audit_image_boundaries.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_image_boundaries.py))
5. Intermediate AST JSON structure validation ([`audit_ast.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_ast.py))

### Why `audit_tools` Became Orphaned

1. **Unreferenced by Skills:** The agent skills evolved to use visual self-correction loops ([`visual-layout-checker`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/visual-layout-checker/SKILL.md) and [`docx-layout-refinement`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/docx-layout-refinement/SKILL.md)) relying on [`src/pdf_to_docx/visual_diff.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_docx/visual_diff.py) and `docx-mcp` tools, rather than running CLI audit suites.
2. **Coupling to Deprecated Schema:** [`audit_tools/audit_ast.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_ast.py#L23) explicitly imports the outdated schema:
   ```python
   from standalone_converter.ir_schema import DocumentSpec
   ```
3. **No CI or Test Integration:** None of the automated pytest suites in [`tests/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests) or CLI entrypoints in `pyproject.toml` ever call `audit_tools`.

---

## 2. Module-by-Module Evaluation

| File | Size | Functionality | Verdict & Rationale |
| :--- | :---: | :--- | :--- |
| **`audit_image_boundaries.py`** | 8.1 KB | Scans perimeter pixels of cropped images to detect clipped chart axes, math labels, or diagram edges | **VALUABLE HEURISTIC — Migrate to `src/worksheet_packer/image_utils.py`** |
| `audit_docx.py` | 15.0 KB | Deep OpenXML inspection of tables, fonts, headings, and DrawingML nodes | **Redundant** with `docx-mcp` tools (`get_document_info`, `get_styles`) and `worksheet-packer info` |
| `audit_pdf_assets.py` | 9.2 KB | Inspects PyMuPDF image and drawing bounding boxes | **Redundant** with `pdf-to-docx info` and `PDFExtractor` |
| `compare_pdf_to_docx.py` | 11.4 KB | Text block and table alignment comparison between PDF and DOCX | **Superseded** by multimodal page diffing in `visual_diff.py` |
| `audit_ast.py` | 7.1 KB | AST JSON validation | **Broken** (imports deprecated `standalone_converter.ir_schema`) |
| `run_all_audits.py` | 4.0 KB | CLI orchestrator running the above 5 audits | **Orphaned** runner script |
| `__init__.py` | 0.2 KB | Package init | Deprecated |

---

## 3. High-Value Heuristic: `ImageBoundaryAuditor`

### What It Does
When subagents crop diagrams or charts from a source PDF, tight bounding boxes can accidentally sever axis labels, negative signs, exponent numbers, or border lines.

`ImageBoundaryAuditor` analyzes the outer perimeter:
- Top border (first 2 rows)
- Bottom border (last 2 rows)
- Left border (first 2 columns)
- Right border (last 2 columns)

It computes the density of non-white/non-transparent pixels:
$$\text{density} = \frac{\text{non-background pixels}}{\text{total perimeter pixels}}$$
If $\text{density} > \text{edge\_density\_tolerance}$ (default $1.5\%$), the edge is flagged as a likely **cutoff warning**:
```text
! CUTOFF: figure_p2.png at LEFT (3.8%), BOTTOM (2.1%)
```

### Why It Belongs in `worksheet_packer.image_utils`
In [`src/worksheet_packer/image_utils.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/worksheet_packer/image_utils.py), we already have:
- `auto_crop_image()`: Trims whitespace from diagrams.
- `estimate_image_scale_bounds()`: Classifies diagrams and calculates min/max bounds.

Adding `audit_image_boundaries()` directly into `image_utils.py` creates a complete, production-grade image preparation suite that can auto-crop, detect cutoffs, and calculate scale bounds in one pass.

---

## 4. Step-by-Step Migration & Porting Plan

### Step 1: Port `ImageBoundaryAuditor` into `src/worksheet_packer/image_utils.py`

Add the following clean, self-contained implementation to [`src/worksheet_packer/image_utils.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/worksheet_packer/image_utils.py):

```python
from typing import Dict, Any, List, Tuple
from PIL import Image

def audit_image_boundaries(
    image_path: str | Path,
    bg_threshold: int = 240,
    edge_density_tolerance: float = 0.015,
) -> Dict[str, Any]:
    """Audits image edge perimeters for non-background pixels indicative of cutoffs.
    
    Returns:
        Dict with status ("PASS" | "FAIL"), cutoffs list, and edge densities.
    """
    img = Image.open(image_path).convert("RGBA")
    w, h = img.size
    if w == 0 or h == 0:
        return {"status": "FAIL", "error": "Empty image", "cutoffs": []}

    pixels = img.load()

    def is_content(x: int, y: int) -> bool:
        r, g, b, a = pixels[x, y]
        if a < 30:  # transparent
            return False
        return r < bg_threshold or g < bg_threshold or b < bg_threshold

    def scan_edge(coords: List[Tuple[int, int]]) -> float:
        content_count = sum(1 for (x, y) in coords if is_content(x, y))
        return content_count / max(1, len(coords))

    top_density = scan_edge([(x, y) for y in range(min(2, h)) for x in range(w)])
    bottom_density = scan_edge([(x, y) for y in range(max(0, h - 2), h) for x in range(w)])
    left_density = scan_edge([(x, y) for x in range(min(2, w)) for y in range(h)])
    right_density = scan_edge([(x, y) for x in range(max(0, w - 2), w) for y in range(h)])

    cutoffs = []
    if top_density > edge_density_tolerance:
        cutoffs.append(("TOP", top_density))
    if bottom_density > edge_density_tolerance:
        cutoffs.append(("BOTTOM", bottom_density))
    if left_density > edge_density_tolerance:
        cutoffs.append(("LEFT", left_density))
    if right_density > edge_density_tolerance:
        cutoffs.append(("RIGHT", right_density))

    return {
        "status": "FAIL" if cutoffs else "PASS",
        "name": Path(image_path).name,
        "cutoffs": cutoffs,
        "densities": {
            "top": top_density,
            "bottom": bottom_density,
            "left": left_density,
            "right": right_density,
        },
    }
```

### Step 2: Add Unit Test in `tests/test_worksheet_packer.py`
Add a unit test verifying `audit_image_boundaries` flags cropped images with content touching the borders.

### Step 3: Remove the `audit_tools/` Directory
Once the cutoff heuristic is ported and tested:
```powershell
Remove-Item -Recurse -Force audit_tools
```

---

## 5. Verification Checklist

- [x] `audit_image_boundaries()` is available in `worksheet_packer.image_utils`.
- [x] Unit test in `tests/test_worksheet_packer.py` passes.
- [x] `audit_tools/` folder is deleted.
- [x] No remaining references to `audit_tools` exist in the codebase.

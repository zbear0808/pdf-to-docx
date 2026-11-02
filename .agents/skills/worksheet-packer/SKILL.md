---
name: worksheet-packer
description: >-
  Parses, reorganizes, and packs worksheet and exam documents (PDF or Word .docx) into space-efficient,
  beautifully formatted Word (.docx) and LaTeX (.tex / .pdf) files using 2D bin packing,
  whitespace auto-cropping, and side-by-side minipage/table layouts. Use when converting, compacting, or
  re-formatting worksheets, problem sets, quizzes, or exams with excessive whitespace.
---

# Worksheet Packer Skill

This skill provides autonomous and surgical workflows for parsing, restructuring, and re-packing problem sets, worksheets, quizzes, and exams into dense, space-efficient Microsoft Word (`.docx`) and LaTeX (`.tex` / `.pdf`) documents.

---

## The Whitespace Problem & Solution

Standard worksheets often waste massive horizontal whitespace—for example, placing a 2-inch geometric diagram on its own vertical row with 4.5 inches of blank space next to it. 

**Worksheet Packer** eliminates this by:
1. **Perception**: Extracting problem prompts, multiple-choice choices, student answer areas, and attached diagrams from PDF or existing Word (`.docx`) documents.
2. **Auto-Cropping**: Trimming white and transparent borders from diagram images so footprint calculations reflect the true visual drawing rather than margin padding.
3. **Empty Space Workspaces**:
   - **No Blank Underlines**: Never generate blank underlines (`_______` or `\hrule`) for student work areas. Blank underlines constrain handwriting, look dated, and waste vertical space.
   - **Clean Whitespace Budgeting**: Use `WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=...)` or `approx_workspace_in=...` on `Problem`.
   - **2D Area Budgeting**: Use `approx_area_sq_in` so student work space automatically adapts its height when toggling between 1-column and 2-column layouts.
4. **2D Bin-Packing & Column Balancing Layout Engine**:
   - **Balanced Multi-Column Splits**: Automatically splits problems evenly across columns on each page (e.g. 3 questions in Column 0 and 3 questions in Column 1, instead of greedy 5-and-1 or 4-and-2 imbalances).
   - **Even Vertical Spacing Distribution**: Calculates vertical slack in each column and distributes it into inter-problem spacing (`spacing_after_in` up to 0.45 in / ~32 pt) so questions comfortably fill the page without awkward voids.
   - **Side-by-Side vs Stacked**: Heuristically routing square-ish or portrait diagrams ($0.55 \le AR \le 1.50$) into **Side-by-Side** (65% text / 35% diagram) containers, and wide diagrams into **Stacked** containers.
5. **Deterministic Structural Rendering**:
   - **DOCX**: Invisible borderless tables with OpenXML `w:cantSplit` on every row guarantee that diagrams, text, and workspaces stay strictly locked together without mid-problem page breaks or jumping floating anchors. Explicit `WD_BREAK.COLUMN` breaks guarantee balanced column transitions.
   - **LaTeX**: `minipage` environments with `multicol` and `tcolorbox`, inserting explicit `\columnbreak` to preserve balanced multi-column splits.

---

## When to Use This Skill

- When a user asks to convert an exam, quiz, or worksheet PDF into Word or LaTeX with optimal use of whitespace.
- When an existing Word document (`.docx`) has excessive whitespace, sprawling pages, or disorganized floating images that need to be re-packed into a compact 1- or 2-column format.
- When grouping problems where order does not matter (`SectionOrdering.FLEXIBLE`) to pack problems into the minimum possible page count.
- When preserving exact problem sequence (`SectionOrdering.STRICT`) while still compacting diagrams side-by-side with question text.

---

## Directory Layout & Workspace Hygiene

All worksheet packing workflows must store deliverables in `output/` and all intermediate diagrams, page renderings, and specs in `_temp/`:
```text
<document_workspace>/
├── output/                 # Final packed deliverables (.docx, .pdf, .tex)
└── _temp/                  # ALL temporary & intermediate working files
    ├── assets/             # Extracted & auto-cropped diagrams/figures
    ├── renders/            # Page preview images (orig_p*.png, docx_p*.png)
    ├── specs/              # Intermediate specs & plans (spec.json, plan.json)
    └── build/              # LaTeX compile logs (.aux, .log, .fls), temp runner scripts
```

---

## Workflow 1: End-to-End PDF Worksheet Conversion

Run the autonomous CLI pipeline:

```bash
# Convert PDF to space-optimized 2-column Word document in output/
uv run worksheet-packer convert "path/to/worksheet.pdf" --columns 2 --format docx -o output/optimized_worksheet.docx

# Convert PDF to LaTeX and compile PDF in output/
uv run worksheet-packer convert "path/to/worksheet.pdf" --columns 2 --format pdf -o output/optimized_worksheet.pdf

# Save intermediate AST (spec.json) and layout plan (plan.json) into _temp/specs/
uv run worksheet-packer convert "path/to/worksheet.pdf" --columns 2 --save-ast -o output/optimized_worksheet.docx --workspace-dir _temp/
```

---

## Workflow 2: Re-Packing an Existing Word Document (.docx)

When an existing `.docx` worksheet needs to be compacted or reformatted:

### Phase A: Direct Autonomous Ingestion
`worksheet-packer` natively ingests `.docx` files:
1. Headlessly renders `.docx` pages to high-resolution PNGs via LibreOffice or Windows Word COM.
2. Extracts original native uncompressed assets from `word/media/` inside the `.docx` archive into `_temp/assets/`.
3. Uses Gemini multimodal vision to understand question boundaries, choices, and diagrams.
4. Packs and outputs a new compacted `.docx` (or `.tex`) into `output/`:

```bash
uv run worksheet-packer convert "path/to/messy_worksheet.docx" --columns 2 --format docx -o output/optimized_worksheet.docx
```

### Phase B: Visual-Inspection First Workflow
If the agent needs to inspect or critique the existing Word document before deciding on layout changes:
1. Prepare directories:
   ```bash
   mkdir -p output _temp/renders _temp/assets _temp/specs _temp/build
   ```
2. Render all pages of the Word doc to PNGs in `_temp/renders`:
   ```bash
   uv run worksheet-packer render-docx-pages "path/to/messy_worksheet.docx" -o _temp/renders
   ```
3. Inspect the rendered page images with multimodal vision to check question density.
4. Parse and generate the editable `WorksheetSpec` JSON:
   ```bash
   uv run worksheet-packer parse "path/to/messy_worksheet.docx" -o _temp/specs/spec.json --columns 2 --workspace-dir _temp/assets
   ```
5. Customize section ordering or hints in `_temp/specs/spec.json`:
   - Set `"ordering": "flexible"` on sections where problem order can be rearranged to fill columns.
   - Set `"ordering": "strict"` on sections where sequence must be preserved.
6. Pack and compile:
   ```bash
   uv run worksheet-packer pack _temp/specs/spec.json -o _temp/specs/plan.json
   uv run worksheet-packer render _temp/specs/plan.json -o output/optimized_worksheet.docx --format docx
   ```

---

## CLI Command Reference

| Command | Purpose | Key Flags |
| :--- | :--- | :--- |
| `info` | Inspect PDF, DOCX, or AST JSON | `<file_path>` |
| `parse` | Parse PDF or DOCX into `WorksheetSpec` JSON | `-o spec.json`, `-c 2`, `--ordering strict\|flexible` |
| `pack` | Run 2D bin packer on AST to create `RenderPlan` | `-o plan.json`, `-c 1\|2`, `--ordering strict\|flexible` |
| `render` | Compile `RenderPlan` or AST into DOCX/LaTeX | `-o output.docx`, `-f docx\|latex\|pdf` |
| `render-docx-pages` | Render all pages of a DOCX to PNG images | `<doc.docx> -o ./pages --dpi 200` |
| `convert` | Full autonomous pipeline (PDF/DOCX -> DOCX/LaTeX) | `--columns 2`, `--format docx\|latex\|both`, `--save-ast` |

---

## Python API Usage

```python
from worksheet_packer import (
    WorksheetSpec,
    WorksheetSection,
    Problem,
    ProblemImage,
    WorkspaceConfig,
    WorkspaceType,
    SectionOrdering,
    LayoutEngine,
    DocxWorksheetRenderer,
    LatexWorksheetRenderer,
    auto_crop_image,
)

# 1. Clean diagram whitespace
clean_path, w, h, ar = auto_crop_image("raw_diagram.png")

# 2. Build WorksheetSpec
spec = WorksheetSpec(
    title="AP Calculus Quiz",
    default_columns=2,
    sections=[
        WorksheetSection(
            id="s1",
            title="Part I: Related Rates",
            ordering=SectionOrdering.STRICT,  # or FLEXIBLE
            problems=[
                Problem(
                    id="q1",
                    number=1,
                    prompt_text="Find the rate of change of angle θ.",
                    image=ProblemImage(media_path=str(clean_path), native_width_px=w, native_height_px=h, aspect_ratio=ar),
                    workspace=WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=1.0),
                )
            ]
        )
    ]
)

# 3. 2D Bin-Packing Layout
engine = LayoutEngine(spec)
plan = engine.pack()

# 4. Render to DOCX (invisible tables w:cantSplit) or LaTeX (minipage)
DocxWorksheetRenderer(plan).render("quiz.docx")
LatexWorksheetRenderer(plan).render("quiz.tex", compile_pdf=True)
```


---
name: worksheet-packer
description: >-
  Parses, reorganizes, and packs worksheet and exam documents (PDF or Word .docx) into space-efficient,
  beautifully formatted Word (.docx) and LaTeX (.tex / .pdf) files using 2D bin packing,
  whitespace auto-cropping, and side-by-side minipage/table layouts. Use when converting, compacting, or
  re-formatting one-off worksheets, problem sets, quizzes, or exams with excessive whitespace. Not for
  documents built by lesson-builder (lessons, keys, practice, assessments in `units/`); edit their YAML
  or `figures/<stem>.py` and rebuild instead.
---

# Worksheet Packer Skill

This skill provides autonomous and surgical workflows for parsing, restructuring, and re-packing problem sets, worksheets, quizzes, and exams into dense, space-efficient Microsoft Word (`.docx`) and LaTeX (`.tex` / `.pdf`) documents.

> [!IMPORTANT]
> **Scope.** Use this skill only for documents that were *not* built by lesson-builder (a one-off PDF or someone else's `.docx`). Not for documents built by lesson-builder (lessons, keys, practice, assessments in `units/`): edit the YAML or `figures/<stem>.py` and rebuild instead (see `lesson-builder`). Never re-pack a lesson-builder DOCX; the next build overwrites it. To read source documents for a lesson/assessment, use `uv run lesson-builder ingest`, not `worksheet-packer parse`.

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
    ├── renders/            # Page preview images (page_{k}.png; one subfolder per document, e.g. renders/orig/, renders/packed/, since every renderer uses the same names)
    ├── specs/              # Intermediate specs & plans (spec.json, plan.json)
    └── build/              # LaTeX compile logs (.aux, .log, .fls), temp runner scripts
```

---

## Workflow 1: End-to-End PDF Worksheet Conversion

Run the autonomous CLI pipeline. `convert` has **no** `--workspace-dir` option (only `parse` does) and it writes its side files next to the **source**, not into `_temp/`:

- `<stem>_spec.json` and `<stem>_plan.json` next to the source (on by default; `--no-save-ast` turns them off).
- Harvested media and page renders in `.ws_<stem>/` next to the source.
- With `--format latex|pdf|both`, the `.tex` goes to `-o` only if `-o` ends in `.tex`; otherwise it is `<source_dir>/<stem>.tex`. `--format pdf` compiles in the `.tex` folder, so the PDF and `.aux/.log` land there too. `-o output/x.pdf` is ignored (nothing is written to `output/`).
- With `--format docx`, `-o` must end in `.docx`, or the file goes next to the source.

So copy the source into the workspace `input/` folder first, and expect the side files there:

```powershell
New-Item -ItemType Directory -Force input, output, _temp/specs, _temp/build | Out-Null
Copy-Item "path/to/worksheet.pdf" input/

# PDF -> 2-column Word document in output/ (spec/plan JSON + .ws_worksheet/ land in input/)
uv run worksheet-packer convert input/worksheet.pdf --columns 2 --format docx -o output/optimized_worksheet.docx

# PDF -> LaTeX in output/ (do not use --format pdf; compile separately so logs go to _temp/build)
uv run worksheet-packer convert input/worksheet.pdf --columns 2 --format latex -o output/optimized_worksheet.tex
pdflatex -interaction=nonstopmode -output-directory=_temp/build output/optimized_worksheet.tex   # run from the folder you ran convert in, so image paths resolve
Copy-Item _temp/build/optimized_worksheet.pdf output/
```

When you need the spec and plan in `_temp/specs/` and media in `_temp/assets/`, use the step-by-step `parse` / `pack` / `render` commands in Workflow 2 Phase B instead; they take explicit paths.

---

## Workflow 2: Re-Packing an Existing Word Document (.docx)

When an existing `.docx` worksheet needs to be compacted or reformatted:

### Phase A: Direct Autonomous Ingestion
`worksheet-packer` natively ingests `.docx` files:
1. Headlessly renders `.docx` pages to high-resolution PNGs via LibreOffice or Windows Word COM.
2. Extracts original native uncompressed assets from `word/media/` inside the `.docx` archive into `.ws_<stem>/media/` next to the source (`convert` has no flag to move this; use Phase B for `_temp/assets/`).
3. Uses Gemini multimodal vision to understand question boundaries, choices, and diagrams.
4. Packs and outputs a new compacted `.docx` (or `.tex`) into `output/`. Copy the source into `input/` first, since the spec/plan JSON and `.ws_<stem>/` are written next to it:

```powershell
Copy-Item "path/to/messy_worksheet.docx" input/
uv run worksheet-packer convert input/messy_worksheet.docx --columns 2 --format docx -o output/optimized_worksheet.docx
```

### Phase B: Visual-Inspection First Workflow
If the agent needs to inspect or critique the existing Word document before deciding on layout changes:
1. Prepare directories:
   ```powershell
   New-Item -ItemType Directory -Force output, _temp/renders, _temp/assets, _temp/specs, _temp/build | Out-Null
   ```
2. Render all pages of the Word doc to PNGs (`page_{k}.png`) in `_temp/renders/orig`:
   ```powershell
   uv run worksheet-packer render-docx-pages "path/to/messy_worksheet.docx" -o _temp/renders/orig
   ```
3. Inspect the rendered page images with multimodal vision to check question density.
4. Parse and generate the editable `WorksheetSpec` JSON (`--workspace-dir` puts media in `_temp/assets/media/` and parser renders in `_temp/assets/rendered_pages/`):
   ```powershell
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
   For LaTeX, render `-f latex -o output/optimized_worksheet.tex` and compile with `pdflatex -output-directory=_temp/build` as in Workflow 1. `-f pdf` compiles in the `.tex` folder, which leaves `.aux/.log` in `output/`.

---

## CLI Command Reference

| Command | Purpose | Key Flags |
| :--- | :--- | :--- |
| `info` | Inspect PDF, DOCX, or AST JSON | `<file_path>` |
| `parse` | Parse PDF or DOCX into `WorksheetSpec` JSON | `-o spec.json` (default `<stem>_spec.json` next to source), `-w/--workspace-dir` (default `.ws_<stem>/` next to source), `-c 2`, `--ordering strict\|flexible` |
| `pack` | Run 2D bin packer on AST to create `RenderPlan` | `-o plan.json` (default `<spec stem>_plan.json` next to spec), `-c 1\|2`, `--ordering strict\|flexible` |
| `render` | Compile `RenderPlan` or AST into DOCX/LaTeX | `-o output.docx` (required), `-f docx\|latex\|pdf` (pdf writes `<o>.tex` + `<o>.pdf` and logs in the same folder) |
| `render-docx-pages` | Render all pages of a DOCX to `page_{k}.png` | `<doc.docx> -o _temp/renders/orig --dpi 200` |
| `convert` | Full autonomous pipeline (PDF/DOCX -> DOCX/LaTeX) | `-c/--columns 2`, `-f/--format docx\|latex\|pdf\|both`, `--ordering`, `--save-ast/--no-save-ast` (default on; JSON next to source), `-o` (`.docx` or `.tex` only). No `--workspace-dir`. |

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


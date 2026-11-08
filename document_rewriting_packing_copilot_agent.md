# Document Rewriting, Worksheet Packing & Assessment Pipeline — Copilot Agent Reference

This document consolidates the **document rewriting/packing logic, schemas, heuristics, rendering rules, and skill workflows** from the `pdf-to-docx` project. It is formatted as a single Markdown reference you can copy into **Microsoft Copilot Agents** (or another agent builder) as instructions/knowledge for an agent that can extract, rewrite, compact, and render educational documents (PDF/DOCX/LaTeX worksheets, quizzes, exams, retakes).

---

## 1. What This System Does

- **Extracts** problems, prompts, choices, diagrams, and workspace needs from worksheets/quizzes/exams (PDF or Word `.docx`) using multimodal vision + PDF/DOCX tooling.
- **Rewrites/polishes** educational text to be **direct, authentic, and human-sounding** (no AI tropes, no em dashes, no fluff) while preserving problem integrity and requirements.
- **Packs layouts** using a **2D bin-packing/column-balancing engine** to minimize whitespace: side-by-side diagram+text when appropriate, stacked when needed, balanced multi-column splits, elastic image squeeze/slack expansion, and clean student workspaces.
- **Renders deterministically** to:
  - **DOCX** (Word) using invisible structural tables with OpenXML `w:cantSplit` so problems/diagrams/workspaces don’t split across pages.
  - **LaTeX/PDF** using `minipage`/`multicol`/`tcolorbox` with explicit column breaks and whitespace work areas.
- **Audits** requirements (counts, points, A–D choices, coverage, page budget) and **visually checks** rendered output (legibility, distortion, column balance, no orphan spills).

---

## 2. Workspace Hygiene (Required)

Always separate final deliverables from intermediates:

```text
<document_workspace>/
├── input/                  # (Optional) source PDFs/DOCX
├── output/                 # Final deliverables ONLY (.docx, .pdf, .tex, answer keys)
└── _temp/                  # ALL transient/intermediate files
    ├── assets/             # Cropped diagrams/figures/media
    ├── renders/            # Page preview PNGs (orig_p*.png, docx_p*.png)
    ├── specs/              # Drafts, WorksheetSpec JSON, RenderPlan JSON, analyses
    └── build/              # Scripts, LaTeX logs (.aux/.log/.fls), scratch files
```

Rules:
- Never dump temp renders/crops/specs into the main folder.
- When compiling LaTeX, prefer `-output-directory=_temp/build` if applicable.
- Gitignore-friendly patterns: `**/_temp/`, `**/temp_*`, `**/_temp_*`, `**/rendered_pages/`, LaTeX aux/log files.

---

## 3. Core Data Model: Worksheet AST (`worksheet_packer.worksheet_ast`)

The packing pipeline centers on a **problem-oriented AST**.

### 3.1 Key Enums
- `SectionOrdering`: `strict` (preserve order) | `flexible` (reorder for density).
- `LayoutHint`: `auto` | `side_by_side` | `stacked` | `full_width`.
- `LayoutDecision` (engine output): `side_by_side` | `stacked` | `text_only` | `image_only`.
- `WorkspaceType`: `blank` (default, clean whitespace) | `box` | `grid` | `lines` (legacy; avoid) | `none`.

### 3.2 `WorkspaceConfig` (student answer/work area)
- **Default to clean whitespace** (`type="blank"`). **Never use blank underlines** for student work.
- Fields:
  - `type`, `lines` (approx 0.3 in/line via `effective_height_in`), `height_pt`
  - `approx_height_in` (explicit vertical inches)
  - `approx_area_sq_in` (scales height by column width: `area / col_width`)
  - `fill_remaining` (expand to fill trailing column whitespace)
- Height resolution priority (conceptually): `type==none -> 0`; `approx_height_in`; `approx_area_sq_in/col_width`; `height_pt`; `grid -> 2.0in`; `box -> max(1.0, lines*24pt)`; else `lines*22pt`.

### 3.3 `ProblemImage`
- `media_path`, `native_width_px/height_px`, `aspect_ratio` (H/W), `auto_cropped`, `caption/alt_text`, `bbox` (normalized 0–1000 `[ymin,xmin,ymax,xmax]`).
- Scale/classification metadata: `source_width_in/height_in`, `min_width_in`, `max_width_in`, `preferred_width_in`, `has_fine_text`, `category` (`formula_icon|compact_shape|detailed_diagram|wide_grid`), `elasticity` (0 rigid–1 compressible).

### 3.4 `Problem`
- Identity/content: `id`, `number`, `part` (`a,b,i,...`), `points`, `prompt_text`, `prompt_runs` (`TextRun`), `choices` (`QuestionChoice`), `image`.
- Workspace: `workspace` (`WorkspaceConfig`), shortcuts `approx_workspace_in`, `approx_workspace_area_sq_in` (synced into workspace on validation).
- Layout: `layout_hint`, `min_rendered_width_in`.
- Helpers: `effective_min_image_width_in`, `full_label` (e.g., `1.`, `2.(a) [3 pts]`).

### 3.5 `WorksheetSection` / `WorksheetSpec`
- `WorksheetSection`: `id`, `title`, `instructions`, `ordering` (strict/flexible), `column_mode` (`single/double/1/2`), `page_break_before`, `problems`.
- `WorksheetSpec`: title/subtitle/headers, page size (8.5×11), margins, `default_columns` (1–2), `column_gap_in`, theme/font defaults, `max_font_size_pt`, `auto_scale_font`, `sections`.
- Computed: `printable_width_in`, `printable_height_in`.

### 3.6 `RenderPlan` (packing output)
- `PlacedProblem` (page/col, x/y/width/height, layout decision, rendered text/image/workspace dimensions, `spacing_after_in`, `font_size_pt`), `PlacedSectionHeader`, `PlacedPage`, `RenderPlan(worksheet, pages, total_pages, stats)`.

---

## 4. 2D Layout & Packing Engine (`worksheet_packer.layout_engine.LayoutEngine`)

### 4.1 Objectives
- Minimize wasted whitespace while preserving legibility and (optionally) problem order.
- Keep diagrams, text, choices, and workspaces **bound together** as atomic units.
- Produce balanced columns/pages when feasible.

### 4.2 Text/Workspace Estimation
- Estimates text height from prompt/choices using font size, chars-per-line heuristic, and line height (~1.3× font).
- Cleans common LaTeX/markup artifacts for better estimation.
- Workspace height comes from `Problem`/`WorkspaceConfig` (explicit inches/area preferred).

### 4.3 Layout Decision (per problem)
- **No image** → `TEXT_ONLY`.
- **With image**: auto heuristic considers `layout_hint`, image `category`, aspect ratio (H/W), prompt length, and legibility floor:
  - `wide_grid`, very wide AR (`< ~0.52`), or `formula_icon` → tend to `STACKED` (prevents formula icons from ballooning).
  - Square-ish/portrait (`~0.55–1.55`) with moderate prompt and sufficient column share → `SIDE_BY_SIDE` (text ~65% / image ~35% share, respecting min widths).
  - Side-by-side uses bounded image width (pref/min/max, column share); stacked bounds image width/height (max stacked height cap) to avoid oversized diagrams.

### 4.4 Packing Behavior
- Respects `SectionOrdering.STRICT` (no reordering) vs `FLEXIBLE` (may sort by footprint height / FFD-like strategy for density).
- Supports 1–2 columns (section override or worksheet default); handles section headers spanning columns and page/section breaks.
- **Column balancing**: finds valid splits/partitions to balance heights and item counts across columns on a page (scoring includes height difference + count difference; special handling for odd counts).
- **Elastic squeeze**: if items overflow available column/page space, compresses diagram widths toward `min_width_in` proportionally (weighted by `elasticity`) to absorb overflow when possible.
- **Slack absorption/expansion**: when trailing whitespace remains, can expand images up to `max_width_in` (bounded) and/or distribute spacing; supports `fill_remaining` workspace.
- **Adaptive font scaling (optional)**: if `auto_scale_font`, may increase per-page font size (up to `max_font_size_pt`) to better fill pages, recalculating footprints/placement.

### 4.5 Output Stats
`RenderPlan.stats` includes totals/pages and counts for `side_by_side`, `stacked`, `text_only`, density ratio, etc.

---

## 5. Deterministic Rendering Rules

### 5.1 DOCX Renderer (`worksheet_packer.docx_renderer.DocxWorksheetRenderer`)
- Sets page geometry, margins, default font/spacing, and section columns when multi-column.
- Renders header block (title/subtitle, name/date/period).
- **Atomic problem containers**: uses **invisible borderless tables** with **`w:cantSplit` on every row** so diagram+text+workspace stay together (no mid-problem page breaks).
- Layouts:
  - **Side-by-side**: row with (text+choices, image) and optional merged workspace row below.
  - **Stacked**: text row, centered image row, workspace row.
  - **Text-only**: text+choices and workspace rows.
- Multi-column flow: inserts explicit column breaks (`WD_BREAK.COLUMN`) as needed to honor balanced placements.
- **No blank underlines** for student work. Workspaces render as clean vertical whitespace, framed `BOX`, or `[ Graph / Grid Area ]` placeholders for `GRID`.
- Cleans common LaTeX math in prompt/choices for Word-friendly Unicode where practical; preserves theme styling and readable typography.

### 5.2 LaTeX Renderer (`worksheet_packer.latex_renderer.LatexWorksheetRenderer`)
- Generates preamble (geometry, amsmath, graphicx, `multicol`, `tcolorbox`, theme colors) and header.
- Uses `minipage` for side-by-side text/image; `multicols*` for multi-column pages and `\columnbreak` for balanced splits.
- Renders choices as `enumerate` `(A)…`, workspaces as `\vspace*` (blank/lines-as-space), `worksheetbox` for box/grid.
- Can compile to PDF via available LaTeX engines (e.g., `latexmk`, `tectonic`, `xelatex`, `pdflatex`, `lualatex`) when requested.

### 5.3 General PDF→DOCX/LaTeX IR Renderers (project-wide)
- `pdf_to_docx.ir_schema` / `docx_compiler`: general document AST (headings, paragraphs, equations, tables, charts, images, boxes, questions). Enforces OpenXML table rules like `w:tblHeader` (repeat headers) and `w:cantSplit`.
- `pdf_to_latex`: parallel LaTeX IR/compilation pathway for publication-grade math/tables/exams.

---

## 6. Parsing & Diagram Harvesting

### 6.1 Worksheet Parser (`worksheet_packer.worksheet_parser`)
- Inputs: PDF or DOCX.
- DOCX ingestion: can headlessly convert DOCX→PDF for page rendering and extract native media from `word/media/`.
- Renders pages to PNG, sends to multimodal vision (Gemini model configurable; API key from env/`.env`) with a **worksheet extraction prompt** to produce structured `RawPageExtraction` / `RawProblemExtraction`:
  - problem number/part/points, prompt text (LaTeX math preserved), choices
  - `has_diagram`, normalized `diagram_bbox` (0–1000), caption, category, min/max width hints, layout hint
  - workspace type/lines/height/approx area; **default workspace = blank/clean whitespace (no underlines)**
- Crops diagram regions, **auto-crops whitespace**, inspects dimensions/aspect ratio, estimates **scale bounds/classification/elasticity**, and builds `ProblemImage` + `WorksheetSpec`.

### 6.2 Image Utilities (`worksheet_packer.image_utils`)
- `auto_crop_image`: trims white/transparent borders with tolerance/padding; returns cropped path, size, aspect ratio (H/W).
- `inspect_diagram_dimensions`: native size and AR.
- `estimate_image_scale_bounds`: derives `source_*`, `min/preferred/max_width_in`, `category` (`formula_icon|compact_shape|detailed_diagram|wide_grid`), `has_fine_text` (edge-density heuristic), `elasticity`. Prevents formula icons from ballooning; enforces legibility floors for detailed diagrams.

---

## 7. CLI / API Usage (Worksheet Packer)

Typical commands (run from repo; uses `uv` in this project):

```bash
# Inspect PDF/DOCX/JSON
uv run worksheet-packer info <file>

# Parse PDF/DOCX -> WorksheetSpec JSON (harvest/crop diagrams)
uv run worksheet-packer parse <doc.pdf|doc.docx> -o _temp/specs/spec.json --columns 2 --ordering strict --workspace-dir _temp/

# Pack spec -> RenderPlan
uv run worksheet-packer pack _temp/specs/spec.json -o _temp/specs/plan.json

# Render plan/spec -> DOCX or LaTeX/PDF
uv run worksheet-packer render _temp/specs/plan.json -o output/worksheet.docx --format docx
uv run worksheet-packer render _temp/specs/plan.json -o output/worksheet.tex --format pdf

# Render DOCX pages to PNGs for visual QA
uv run worksheet-packer render-docx-pages output/worksheet.docx -o _temp/renders/docx_pages --dpi 200

# End-to-end convert (PDF/DOCX -> packed output)
uv run worksheet-packer convert <doc.pdf|doc.docx> --columns 2 --format docx --ordering strict -o output/packed.docx --save-ast
```

Python API sketch:
```python
from worksheet_packer import WorksheetSpec, WorksheetSection, Problem, ProblemImage, WorkspaceConfig, WorkspaceType
from worksheet_packer import SectionOrdering, LayoutEngine, DocxWorksheetRenderer, LatexWorksheetRenderer, auto_crop_image

clean_path, w, h, ar = auto_crop_image("raw.png")
spec = WorksheetSpec(title="Quiz", default_columns=2, sections=[WorksheetSection(
    id="s1", ordering=SectionOrdering.STRICT, problems=[Problem(
        id="q1", number=1, prompt_text="...", image=ProblemImage(media_path=str(clean_path), native_width_px=w, native_height_px=h, aspect_ratio=ar),
        workspace=WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=1.0)
    )]
)])
plan = LayoutEngine(spec).pack()
DocxWorksheetRenderer(plan).render("output/quiz.docx")
LatexWorksheetRenderer(plan).render("output/quiz.tex", compile_pdf=True)
```

---

## 8. Document Rewriting & Quality Pipelines (Skill Workflows)

Use these as agent instructions/modules. Delegate phases to subagents where possible; pass **file paths** (not huge blobs) to reduce context bloat.

### 8.1 `course-content-extractor` (source ingestion)
- Locate and extract stems, choices, rubrics, code/math notation, diagrams from local course sources (past quizzes/exams, FRQs, unit materials). Preserve notation/syntax.
- Copy/crop diagrams into local `_temp/assets/` (workspace must be self-contained).
- Write provenance-rich extraction (source path/title, question IDs, correct answers/distractor rationale, rubric E/P/I, asset paths) to e.g. `_temp/specs/extracted_course_content.md` or `source_analysis.md`.
- **Exam integrity (retakes/reviews): never copy actual exam questions verbatim.** Mirror standards/cognitive demand/archetype; vary numbers, orientations, contexts, variable names; keep verified solutions.

### 8.2 `authentic-writer` (human, direct phrasing)
- **Banned AI tropes/vocab (examples):** delve, tapestry, vibrant, testament, multifaceted, crucial, pivotal, furthermore/moreover (prefer “also”), “it’s important to note”, “in conclusion…” preambles/conclusions, corporate/flowery inflation, artificial “rule of three”, negative parallelisms, elegant variation.
- **Test/worksheet phrasing:** direct stems (“Find the value of $x$…” not story preambles); concise instructions; authentic grounded scenarios.
- **Formatting/tone:** sentence-case headings; no conversational preambles to the reader; no preachy conclusions; minimal bold/bullets misuse.
- **Punctuation:** **strictly ban em dashes (`—`, `--`)**; use commas, parentheses, or split sentences.
- Align notation to the specific course (Geometry/AP Stats CED/AP CS A).

### 8.3 `critical-checker` (de-fluff, preserve integrity)
- Remove verbosity, redundancy, conversational filler, and dramatic phrasing (especially stems/directions).
- Replace **all em dashes** with clean punctuation.
- **Do not change** problem numbering, A–D options, math values/formulas, code logic, or core structure/rigor. Apply edits directly.

### 8.4 `requirement-checker` (constraints & rubric integrity)
Verify and surgically fix:
- Question/section counts and continuous numbering.
- Point totals (header = sum; FRQ subparts = problem total).
- MCQs have exactly (A)–(D), no duplicates/empties, one unambiguous correct answer.
- Topic/standard coverage and appropriate scope/difficulty.
- Page budget/workspace fits target (no overflow; `WorksheetConfig` heights reasonable).
- Answer key completeness; FRQ rubrics have objective criteria.
- Any added text must follow `authentic-writer` rules.

### 8.5 `visual-layout-checker` (post-render QA)
Render pages to PNG (`_temp/renders/`) and audit:
1. Diagram legibility (labels, angles, grids, code) and **no distortion** (AR preserved).
2. Multi-column symmetry and smooth slack distribution (no lopsided 5-and-1).
3. Side-by-side vs stacked harmony; **no text/diagram collisions**.
4. **Zero blank underlines**; adequate clean whitespace for handwriting (scale by task complexity).
5. Page budget: exact target pages, no orphan spills.

Remediation levers in `worksheet_spec.json`: adjust `min/preferred/max_width_in`, `layout_hint`, `ordering`, `default_font_size_pt` (small steps), `workspace.approx_height_in`, or regenerate higher-DPI/correct-AR assets; then repack+rerender.

### 8.6 `curriculum-visual-generator` (figures/diagrams)
- Generate 300 DPI, print-ready figures (Matplotlib/NumPy/PIL); save to `_temp/assets/`, then **auto-crop**.
- Standard styling (high contrast; theme/navy, highlight/crimson, secondary/amber, soft fills, legible sans fonts).
- Templates: coordinate grids + transformations, parallel lines/transversals with angle labels, comparative boxplots, inscribed polygons/symmetry, etc.
- Set AST image metadata/category and `layout_hint` based on AR/content (detailed/square → side-by-side; wide grid → stacked).

### 8.7 `lesson-assessment-designer` (pedagogy; used by assessment builder)
- Ground in UbD (Stage 1–3), Smith & Stein cognitive demand, Taylor & Nolen (selected/constructed/performance/diagnostic), MLL scaffolds (WIDA, translanguaging, 3-Reads, sentence frames), and course context (e.g., Geometry MLL supports; AP Stats CED argumentation; AP CS tracing/syntax).
- MCQ distractors must be **diagnostic** (common errors/misconceptions), not throwaways; provide rationales/remediation. Authentic tasks need clear directions + analytic rubrics.

### 8.8 `assessment-builder` (end-to-end autonomous pipeline)
1. **Ingest sources** → `_temp/specs/source_analysis.md` (respect exam integrity; no verbatim from active exams).
2. **Draft Markdown** with metadata/sections/problems/points, A–D choices, image placeholders (`- **Image**: _temp/assets/...`), workspace inches, layout hints → `draft_v1_initial.md`.
3. **Pedagogical revision** (cognitive demand, diagnostic distractors, MLL scaffolds, rubrics) → `draft_v2_pedagogy.md`.
4. **Authentic phrasing + de-fluff** (no AI tropes, no em dashes, direct stems) → `draft_v3_authentic.md` / final.
5. **Translate Markdown → `WorksheetSpec` JSON** (`_temp/specs/worksheet_spec.json`): map sections/problems/choices; **`workspace.type="blank"` with `approx_height_in`**; set image `category/min/max/preferred_width_in/has_fine_text/layout_hint`.
6. **Generate/crop visuals** to `_temp/assets/`; ensure spec paths match.
7. **Pack + render** to `output/` via `worksheet-packer` (plan JSON optional in `_temp/specs/`).
8. **Visual audit**; iterate spec/pack/render until PASS.

### 8.9 `curriculum-document-pipeline` (compact variant)
0) Extract course/quiz content → `_temp/specs/extracted_content.md` + assets.  
1) Authentic draft (`draft_v1.md`). 2) Critical de-fluff (`draft_v2.md`). 3) Requirement check (`draft_v3.md`). 4) Final authenticity pass (`final_content.md`). 5) Pack/render to `output/` (DOCX/PDF). Enforce workspace hygiene throughout.

### 8.10 Related conversion/refinement skills (broader repo)
- **`pdf-to-docx`**: page-parallel subagent extraction to `PageSpec` AST or Markdown fast-track; deterministic compile with OpenXML table rules; optional visual QA/refinement.
- **`pdf-to-latex`**: page-parallel extraction to LaTeX IR/fragments; compile with `article|exam|report|scrartcl`; asset harvesting.
- **`docx-layout-refinement`**: surgical DOCX edits (table widths/padding/borders, margins/sections, native DrawingML charts) — prefer page/section subagents to limit context.
- **`worksheet-packer` skill**: operational guidance for packing workflows (ingest PDF/DOCX, parse/pack/render, strict vs flexible ordering).

---

## 9. Implementation Invariants (Do Not Violate)

- **No blank underlines** for student response/work areas; use **clean whitespace** (`blank`), `box`, or `grid` only when appropriate.
- **Atomic layout containers**: problems/diagrams/workspaces must not split awkwardly (DOCX `w:cantSplit`; balanced placement; bounded footprints).
- **Preserve problem integrity** during rewriting: numbering, choices, point values, math/code/data, and required structure remain correct unless explicitly fixing a verified requirement gap.
- **Exam integrity**: no verbatim copying from actual exams into retakes/reviews/practice; vary parameters and contexts substantively.
- **No em dashes** in polished educational text; no AI-trope preambles/conclusions.
- **Workspace hygiene**: outputs in `output/`, intermediates in `_temp/` subfolders.
- **Legibility over density**: enforce image min widths/scale bounds; never distort aspect ratios; avoid oversized formula icons.

---

## 10. Suggested Copilot Agent Configuration

**Agent role/persona:** “Educational Document Rewriter & Worksheet Packer. Produces clear, compact, classroom-ready assessments/worksheets (DOCX/LaTeX/PDF) with balanced layouts, legible diagrams, and clean student workspaces.”

**Core capabilities to expose:**
1. Ingest PDF/DOCX and extract a `WorksheetSpec`-like structure (or guide the user through `worksheet-packer` CLI/API).
2. Rewrite/polish stems and instructions (authentic, direct, no em dashes, no fluff) and verify requirements.
3. Configure workspaces as **blank whitespace** with appropriate `approx_height_in`/`approx_area_sq_in`.
4. Set layout hints/categories/scale bounds for diagrams; recommend side-by-side vs stacked.
5. Pack with `strict` or `flexible` ordering and 1–2 columns; render to DOCX/LaTeX; run visual audit checklist.
6. Follow exam-integrity rules for retakes/variants.

**Default behaviors:** use `_temp/` and `output/`; prefer `blank` workspaces; ban em dashes and AI tropes; ask only when requirements are ambiguous (page count, column count, ordering, source-of-truth for points/standards).

---

## 11. Source Files in This Repo (for deeper reference)

- Worksheet packing core: `src/worksheet_packer/{worksheet_ast,layout_engine,worksheet_parser,image_utils,docx_renderer,latex_renderer,docx_extractor,cli}.py`
- General IR/compilers: `src/pdf_to_docx/{ir_schema,docx_compiler,layout_parser}.py`, `src/pdf_to_latex/{latex_compiler}.py`
- Skills: `.agents/skills/{worksheet-packer,pdf-to-docx,pdf-to-latex,docx-layout-refinement,assessment-builder,curriculum-document-pipeline,course-content-extractor,authentic-writer,critical-checker,requirement-checker,visual-layout-checker,curriculum-visual-generator,lesson-assessment-designer,classroom-context,mll-literacy-scaffolding}/SKILL.md`
- Project entrypoints: `pyproject.toml` (`worksheet-packer`, `pdf-to-docx`, `pdf-to-latex`)

*End of reference.*
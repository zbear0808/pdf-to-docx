# Copilot Agent: Skills, Scripts, and I/O Specification

This document defines the **skills** a Microsoft Copilot–style document agent should have for rewriting, packing, and rendering educational documents (PDF/DOCX worksheets, quizzes, exams, retakes), and the **scripts/tools each skill uses** with their **inputs and outputs**.

Grounded in this repository (`pdf-to-docx`): `.agents/skills/*/SKILL.md`, helper scripts in `.agents/skills/*/scripts/` and `scripts/pdf_to_latex/`, and CLI entrypoints from `pyproject.toml` (`worksheet-packer`, `pdf-to-docx`, `pdf-to-latex`).

---

## Global Conventions (apply to all skills)

| Item | Convention |
|---|---|
| **Workspace layout** | `input/` (optional sources), `output/` (final deliverables only), `_temp/assets/`, `_temp/renders/`, `_temp/specs/`, `_temp/build/` |
| **Student work areas** | Default to **clean whitespace** (`workspace.type="blank"`). **Never use blank underlines**. |
| **Phrasing** | Direct, authentic, human-sounding; **no em dashes**; no AI tropes/preambles/conclusions. |
| **Exam integrity** | Never copy actual exam questions verbatim into retakes/reviews/practice; mirror standards/cognitive demand and vary parameters/contexts. |
| **Problem integrity** | Rewriting must not change numbering, A–D options, math/code/data, or point structure unless fixing a verified requirement gap. |
| **Legibility** | Preserve aspect ratios; enforce diagram min widths; avoid oversized formula icons. |

---

## Skill 1 — `assessment-builder` (Orchestrator)

**Purpose:** Autonomous, multi-phase pipeline for standards-aligned assessments/quizzes/worksheets. Coordinates ingestion → drafting → pedagogy → authentic/de-fluff → AST translation → visual generation → 2D packing/render → visual audit. Delegates phases to subagents to limit context bloat.

**Source:** `.agents/skills/assessment-builder/SKILL.md` (instruction-only; no dedicated script files in skill folder).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| `worksheet-packer pack` | Yes (CLI: `src/worksheet_packer/cli.py`) | Convert `WorksheetSpec` AST to `RenderPlan` (2D bin-packing). | `spec_path` (`WorksheetSpec` JSON), `--output/-o` plan path, optional `--columns`, `--ordering`. | `RenderPlan` JSON (`_temp/specs/render_plan.json`): `worksheet`, `pages[]` with `PlacedProblem`/`PlacedSectionHeader`, `total_pages`, `stats`. |
| `worksheet-packer render` | Yes (CLI) | Render `RenderPlan` or `WorksheetSpec` to DOCX/LaTeX/PDF. | `plan_or_spec` JSON path, `--output/-o` (`.docx`/`.tex`), `--format/-f` (`docx`/`latex`/`pdf`). | `output/Assessment.docx` and/or `output/Assessment.tex` (+ compiled `.pdf` if `format=pdf`). |
| `worksheet-packer render-docx-pages` | Yes (CLI) | Headless DOCX page previews for visual audit. | `docx_path`, `--output-dir/-o`, `--dpi` (default 200). | PNGs like `_temp/renders/docx_pages/page_1.png`, … |
| **`translate_markdown_to_worksheet_spec.py`** (recommended agent script) | *Not present; agent should create per workspace* | Deterministic translation of polished Markdown draft to `WorksheetSpec` JSON (mapping rules from skill). | `_temp/specs/draft_v3_authentic.md` (or final draft), optional metadata overrides (title, margins, columns, theme). | `_temp/specs/worksheet_spec.json` (`WorksheetSpec`: sections/problems/choices/images/workspaces with `type="blank"` + `approx_height_in`, layout hints/categories). |
| **`generate_figures.py`** (workspace script) | *Created per task in `_temp/build/` per workflow* | Generate/crop assessment diagrams at 300 DPI. | Figure specs/placeholders from draft/spec; output dir `_temp/assets/`. | Cropped PNGs in `_temp/assets/*.png`; (optionally) updated `image.media_path` metadata. |

**Key I/O artifacts (pipeline):** `source_analysis.md` → `draft_v1_initial.md` → `draft_v2_pedagogy.md` → `draft_v3_authentic.md` → `worksheet_spec.json` + `_temp/assets/*` → `render_plan.json` → `output/*.docx|tex|pdf` → `_temp/renders/*`.

---

## Skill 2 — `curriculum-document-pipeline` (Orchestrator)

**Purpose:** Sequential pipeline: extract course/quiz content → authentic draft → critical de-fluff → requirement check → final authenticity → pack/render with `worksheet-packer`.

**Source:** `.agents/skills/curriculum-document-pipeline/SKILL.md` (instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| `worksheet-packer` (pack/render/convert as needed) | Yes (CLI) | Layout packing and final rendering. | Spec/plan JSON or source doc; format/columns/ordering flags. | `output/*.docx|tex|pdf`, optional spec/plan JSON. |
| **`md_to_ast_or_pack_script.py`** (recommended) | *Not present; agent should create* | Convert finalized Markdown (`final_content.md`) into `WorksheetSpec`/renderable structure for packing. | `_temp/specs/final_content.md`. | `_temp/specs/worksheet_spec.json` (or direct render inputs). |

**Key I/O artifacts:** `extracted_content.md` → `draft_v1.md` → `draft_v2.md` → `draft_v3.md` → `final_content.md` → packed `output/` deliverables.

---

## Skill 3 — `course-content-extractor`

**Purpose:** Locate/extract problem stems, choices, rubrics, code/math notation, diagrams, and standards from local course sources; preserve provenance; copy/crop assets into `_temp/assets/`. Enforce exam-integrity (no verbatim from actual exams for retakes/reviews).

**Source:** `.agents/skills/course-content-extractor/SKILL.md` (instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| `pdf-to-docx render-pages` / extraction helpers | Yes (`pdf_to_docx` CLI; repo modules) | Render/inspect source PDFs for extraction context. | Source PDF path, `-o` render dir. | Page PNGs in `_temp/renders/` (or specified dir). |
| `pdf-to-docx`/`pdf-to-latex` `crop` helpers (see Skills 10/11) | Yes | Crop diagram regions from source PDFs. | PDF, page, normalized bbox `ymin,xmin,ymax,xmax` (0–1000), output path, DPI. | Cropped image in `_temp/assets/` (PNG/SVG depending on tool). |
| **`extract_course_content.py`** (recommended agent script) | *Not present; agent should create when needed* | Compile provenance-rich extraction package. | Source file paths, target unit/standard/deliverable metadata. | `_temp/specs/extracted_course_content.md` or `source_analysis.md` with stems/choices/keys/rubrics/asset paths and provenance header. |

---

## Skill 4 — `authentic-writer`

**Purpose:** Rewrite/generate educational text with authentic, human phrasing; remove AI tropes, banned vocabulary, em dashes, formulaic transitions, fluff/preambles/conclusions; keep stems direct and course-aligned.

**Source:** `.agents/skills/authentic-writer/SKILL.md` (instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| **`authenticity_lint.py`** (recommended agent script) | *Not present; agent should create* | Flag banned words/phrases, em dashes, preambles/conclusions, title-case headings issues for review (human/agent fixes). | Markdown/text file path (e.g., `_temp/specs/draft_v1.md`). | Lint report (stdout or `_temp/specs/authenticity_report.md`) listing violations + locations; optionally auto-fixed text if implemented conservatively. |

*Primary operation is LLM/agent text editing; scripts are optional guardrails.*

---

## Skill 5 — `critical-checker`

**Purpose:** De-fluff and tighten drafts: remove verbosity/redundancy/conversational filler; replace em dashes; **preserve** numbering, options, math/code/data, and structure.

**Source:** `.agents/skills/critical-checker/SKILL.md` (instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| **`defluff_check.py`** (recommended agent script) | *Not present; agent should create* | Detect em dashes and optionally highlight long/redundant patterns for review (must not alter problem integrity). | Draft Markdown path. | Report or in-place cleaned copy (only safe punctuation/whitespace fixes) + change summary. |

---

## Skill 6 — `requirement-checker`

**Purpose:** Verify and surgically fix constraints: question/section counts, continuous numbering, point totals (incl. FRQ subparts), MCQ A–D completeness and single correct answer, standard coverage/scope, page/workspace budget, answer key/rubric completeness.

**Source:** `.agents/skills/requirement-checker/SKILL.md` (instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| **`check_assessment_requirements.py`** (recommended agent script) | *Not present; agent should create* | Parse draft/spec and validate structural/point/choice constraints; emit actionable gaps. | `_temp/specs/draft_v*.md` or `worksheet_spec.json`, optional requirement manifest (expected counts, total points, topics). | Validation report (`_temp/specs/requirement_report.md` or JSON) with pass/fail checks and discrepancies; optionally corrected draft/spec. |
| `worksheet-packer info` | Yes (CLI) | Quick sanity check of `WorksheetSpec`/`RenderPlan` problem/section counts. | JSON file path. | Console summary (sections, problems, pages, layout stats). |

---

## Skill 7 — `visual-layout-checker`

**Purpose:** Post-render visual QA on DOCX/PDF page images: diagram legibility/AR, column symmetry/slack, side-by-side vs stacked harmony, **no blank underlines**, adequate clean whitespace, exact page budget/no orphan spills.

**Source:** `.agents/skills/visual-layout-checker/SKILL.md` (instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| `worksheet-packer render-docx-pages` | Yes (CLI) | Render DOCX pages to PNG for inspection. | `docx_path`, `-o _temp/renders/docx_pages`, `--dpi 200`. | `page_1.png`, `page_2.png`, … |
| **`render_pdf_pages.py`** (recommended agent script) | *Not present as standalone file; skill shows inline PyMuPDF snippet* | Render PDF pages to PNG for inspection. | `output/Assessment.pdf`, output dir, DPI. | `_temp/renders/pdf_pages/page_*.png`. |
| `.agents/skills/pdf-to-docx/scripts/diff_layout.py` | Yes | Visual compare original page PNG vs rendered DOCX page (DOCX→PNG via LibreOffice/Word COM) and critique. | `original_png`, `docx_path`, `--page`. | Console fidelity score, matches/discrepancies; uses temp render under docx dir. |
| `scripts/pdf_to_latex/diff_layout.py` (mirrored in skill) | Yes | Side-by-side visual compare original PNG vs compiled PDF page. | `original_png`, `compiled_pdf`, `--page`, `-o` output image, `--dpi`. | `visual_diff.png` (side-by-side) and temp compiled page render (cleaned). |

---

## Skill 8 — `curriculum-visual-generator`

**Purpose:** Generate 300 DPI, print-ready diagrams (geometry, stats charts, coordinate grids, CS visuals) using Matplotlib/NumPy/Pillow; auto-crop; save to `_temp/assets/`; provide metadata/category/layout guidance for AST.

**Source:** `.agents/skills/curriculum-visual-generator/SKILL.md` (instruction-only; templates provided).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| **`_temp/build/generate_figures.py`** (workspace script per task) | *Created per assessment/task* | Generate all required figures and auto-crop. | Figure definitions (coordinates/data/labels), `ASSET_DIR=_temp/assets`. | Cropped PNGs in `_temp/assets/` (300 DPI, white bg); console prints `(w,h,AR)`. |
| `worksheet_packer.image_utils.auto_crop_image` (library) | Yes (`src/worksheet_packer/image_utils.py`) | Trim white/transparent borders; compute AR. | `image_path`, optional `output_path`, `tolerance`, `padding_px`. | `(saved_cropped_path, width_px, height_px, aspect_ratio)`; cropped file on disk. |
| `worksheet_packer.image_utils.estimate_image_scale_bounds` | Yes | Classify image and compute scale bounds/elasticity for layout. | Image path/size/AR, optional `bbox` (0–1000), `page_width_in`, `col_width_in`. | `ScaleBoundsResult` (`source/min/preferred/max_width_in`, `category`, `has_fine_text`, `elasticity`). |

---

## Skill 9 — `worksheet-packer` (Core Packing & Rendering)

**Purpose:** Parse PDF/DOCX worksheets into `WorksheetSpec`, 2D bin-pack into `RenderPlan`, and render space-efficient DOCX/LaTeX/PDF with side-by-side diagrams, balanced columns, and atomic non-splitting containers.

**Source:** `.agents/skills/worksheet-packer/SKILL.md`. **Primary implementation:** `src/worksheet_packer/*` (CLI `worksheet-packer`).

| Script / Tool (CLI/module entrypoint) | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| `uv run worksheet-packer info <file>` | Yes | Inspect PDF, DOCX, `WorksheetSpec` JSON, or `RenderPlan` JSON. | `file_path` (`.pdf`/`.docx`/`.json`). | Console summary (pages/dims for PDF; paragraphs/tables/media for DOCX; sections/problems/columns for spec; pages/stats/layout counts for plan). |
| `uv run worksheet-packer parse <doc> -o ...` | Yes | Multimodal parse + diagram crop/harvest → `WorksheetSpec`. | `doc_path` (PDF/DOCX), `--output/-o`, `--workspace-dir/-w` (cache/media), `--ordering strict|flexible`, `--columns 1|2`. Requires vision API config (e.g., `GEMINI_API_KEY`) per parser implementation. | `WorksheetSpec` JSON (default `<stem>_spec.json`); harvested/cropped assets under workspace/media dirs. |
| `uv run worksheet-packer pack <spec.json> -o ...` | Yes | 2D layout packing. | `spec_path`, `--output/-o`, optional `--columns`, `--ordering` overrides. | `RenderPlan` JSON (default `<stem>_plan.json`); console stats (pages, side-by-side/stacked/text-only). |
| `uv run worksheet-packer render <plan_or_spec.json> -o ...` | Yes | Deterministic render. | `plan_or_spec` JSON, `--output/-o`, `--format/-f docx|latex|pdf`. | DOCX at output path; or `.tex` (+ `.pdf` if compiled) at output/derived path. |
| `uv run worksheet-packer render-docx-pages <docx> -o <dir>` | Yes | DOCX → page PNGs (LibreOffice/Word COM). | `docx_path`, `--output-dir/-o`, `--dpi`. | PNG pages in output dir. |
| `uv run worksheet-packer convert <doc> [options]` | Yes | End-to-end parse → pack → render. | `doc_path` (PDF/DOCX), `-o`, `--format docx|latex|both|pdf`, `--columns`, `--ordering`, `--save-ast/--no-save-ast`. | Packed DOCX/TeX/PDF in `output`/default path; optionally `<stem>_spec.json`, `<stem>_plan.json`. |

**Core module I/O (programmatic):**

| Module/Class | Input | Output |
|---|---|---|
| `WorksheetParser.parse_worksheet(...)` | PDF/DOCX path, `workspace_dir`, `ordering`, `default_columns`; uses rendered page PNGs + vision extraction (`RawPageExtraction` schema). | `WorksheetSpec` (sections/problems/images/workspaces). |
| `LayoutEngine(spec).pack()` | `WorksheetSpec`. | `RenderPlan` (placed items per page/col, layout decisions, stats). |
| `DocxWorksheetRenderer(plan).render(path)` | `RenderPlan`, output `.docx` path. | Saved `.docx` (invisible `w:cantSplit` containers, balanced columns/breaks). |
| `LatexWorksheetRenderer(plan).render(path, compile_pdf=...)` | `RenderPlan`, `.tex` path, `compile_pdf` flag. | Saved `.tex`; optionally compiled `.pdf`. |

---

## Skill 10 — `pdf-to-docx` (General PDF → Word Conversion)

**Purpose:** High-fidelity PDF→DOCX via page-parallel subagents, `PageSpec`/`DocumentSpec` AST or Markdown fast-track, PyMuPDF asset harvesting, deterministic OpenXML compilation, optional visual diff QA.

**Source:** `.agents/skills/pdf-to-docx/SKILL.md`. **Helper scripts:** `.agents/skills/pdf-to-docx/scripts/`. **CLI:** `pdf-to-docx` / `python -m pdf_to_docx`.

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| `.agents/skills/pdf-to-docx/scripts/inspect_pdf.py` | Yes | Inspect PDF structure and render all pages. | `pdf_path`, `--dpi` (default 200), `--output-dir/-o` (default `./rendered_pages`). | Console page table (dims/orientation/images/drawings); rendered PNGs in output dir. |
| `.agents/skills/pdf-to-docx/scripts/crop_asset.py` | Yes | Crop figure/diagram region from PDF. | `pdf_path`, `--page/-p` (1-indexed), `--bbox/-b` as `ymin,xmin,ymax,xmax` (0–1000), `--output/-o`, `--dpi`, `--format` (`png`/`svg`). | Cropped asset file at output path. |
| `.agents/skills/pdf-to-docx/scripts/compile_pages.py` | Yes | Compile per-page `page_*_spec.json` into DOCX. | `pages_dir` (default `.conversion_workspace`), `-o output.docx`, `--title`, `--theme-hex`, `--assets-dir`, `--save-ast`, `--ast-path`. | `output/*.docx`; optionally merged `DocumentSpec` AST JSON. |
| `.agents/skills/pdf-to-docx/scripts/convert.py` | Yes | End-to-end PDF→DOCX conversion (CLI wrapper). | `pdf_path`, `-o`, `--workspace-dir`, `--assets-dir`, `--dpi`, `--diff`, `--save-ast`, `--ast-path`. | DOCX (+ optional AST, optional diff workflow artifacts). |
| `.agents/skills/pdf-to-docx/scripts/diff_layout.py` | Yes | Visual QA: compare original page PNG to rendered DOCX page. | `original_png`, `docx_path`, `--page`. | Fidelity/critique output; temp rendered DOCX page PNG (requires LibreOffice/`soffice`). |
| `python -m pdf_to_docx parse-page ...` | Yes (CLI module) | Parse one page to `PageSpec` JSON + crop assets (subagent task). | PDF, `--page`, `--image`, `-o spec.json`, `--assets-dir`. | `_temp/specs/page_{k}_spec.json`, cropped assets in `_temp/assets/`. |
| `python -m pdf_to_docx compile-pages ...` | Yes | Merge/compile page specs. | Pages/specs dir, `-o`, `--title`, `--save-ast`. | DOCX + optional AST. |
| `python -m pdf_to_docx to-markdown-page` / `merge-markdown` | Yes (per skill/CLI) | Markdown fast-track pathway. | Page image/PDF page refs; markdown output paths. | `page_{k}.md`, merged `document.md` (then `docx-mcp: create_from_markdown`). |

**Per-page subagent expected I/O (AST pathway):** Input = PDF path + page number + rendered PNG; Output = `page_{k}_spec.json` + assets; subagent returns concise summary (blocks/tables/charts/assets).

---

## Skill 11 — `pdf-to-latex` (General PDF → LaTeX/PDF Conversion)

**Purpose:** High-fidelity PDF→LaTeX via page-parallel subagents, LaTeX-oriented `PageSpec`/`DocumentSpec` extraction or direct `.tex` fragments, asset harvesting, deterministic compilation (`article|report|exam|scrartcl`), optional PDF compile and visual diff.

**Source:** `.agents/skills/pdf-to-latex/SKILL.md`. **Helper scripts:** `.agents/skills/pdf-to-latex/scripts/` (mirrors `scripts/pdf_to_latex/` patterns). **CLI:** `pdf-to-latex` / `python -m pdf_to_latex`.

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| `scripts/pdf_to_latex/inspect_pdf.py` (and skill mirror) | Yes | Inspect PDF, render pages, detect LaTeX compiler. | `pdf_path`, `--dpi`, `--output-dir/-o`. | Console page table + render count; PNG pages in output dir; reports detected LaTeX engine or install/Overleaf note. |
| `scripts/pdf_to_latex/crop_asset.py` (skill mirror) | Yes | Crop high-res asset for LaTeX `\includegraphics`. | `pdf_path`, `--page`, `--bbox` `ymin,xmin,ymax,xmax` (0–1000), `--output/-o`, `--dpi` (default 300). | Cropped image (e.g., `assets/cropped_asset.png`). |
| `scripts/pdf_to_latex/compile_pages.py` (skill mirror) | Yes | Compile `page_*_spec.json` → `.tex` (and optional PDF). | `pages_dir`, `-o document.tex`, `--title`, `--author`, `--doc-class article|report|exam|scrartcl`, `--theme-hex`, `--assets-dir`, `--pdf`, `--save-ast`, `--ast-path`. | `.tex` in `output/` (recommended); optional compiled `.pdf`; optional merged AST JSON. |
| `scripts/pdf_to_latex/compile_latex.py` (skill mirror) | Yes | Compile existing `.tex` to PDF. | `tex_path`, `--output/-o` PDF. | Compiled PDF (or error with engine/install guidance); uses `latexmk/tectonic/xelatex/pdflatex/lualatex` detection. |
| `scripts/pdf_to_latex/convert.py` (skill mirror) | Yes | End-to-end PDF→LaTeX (optional PDF). | `pdf_path`, `-o`, `--workspace-dir`, `--assets-dir`, `--doc-class`, `--title`, `--dpi`, `--pdf`, `--save-ast`, `--ast-path`. | `.tex` (+ optional `.pdf`, optional AST) in specified paths/workspace. |
| `scripts/pdf_to_latex/diff_layout.py` (skill mirror) | Yes | Visual QA vs original render. | `original_png`, `compiled_pdf`, `--page`, `--output/-o`, `--dpi`. | Side-by-side comparison PNG; temp compiled-page render removed. |
| `python -m pdf_to_latex render-pages` / `parse-page` / `to-latex-page` / `merge-latex` | Yes (per skill/CLI) | Page rendering, AST extraction, LaTeX fragment fast-track, merge. | PDF/pages/images + output/workspace/asset dirs; page numbers. | Page PNGs, `page_{k}_spec.json` or `page_{k}.tex`, merged `.tex`, assets. |

---

## Skill 12 — `docx-layout-refinement`

**Purpose:** Surgical post-conversion DOCX editing: table widths/padding/borders/shading/header rows, margins/orientation/section breaks, native DrawingML chart upgrades (`docx-mcp`), targeted page/section refinement subagents.

**Source:** `.agents/skills/docx-layout-refinement/SKILL.md` (instruction + `docx-mcp` tool usage; no local `.py` scripts in folder). References: `references/native_charts_guide.md`, `references/table_styling_guide.md`.

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| `docx-mcp` tools (`open_document`, `set_column_widths`, `set_cell_shading`, `set_table_borders`, `set_header_row`, `insert_*_chart`, `set_page_margins`, `set_page_orientation`, `save_document`, etc.) | External MCP (used by skill) | Deterministic/surgical DOCX edits and native charts. | DOCX path, table/paragraph indices, widths/colors/chart data, output path. | Updated DOCX saved to `output/` (or specified path). |
| `.agents/skills/pdf-to-docx/scripts/diff_layout.py` or DOCX render/QA flow | Yes | Verify refinement visually. | Original page PNG + refined DOCX, page. | Visual critique/fidelity feedback. |

---

## Skill 13 — `lesson-assessment-designer`

**Purpose:** Standards-aligned, equity-centered lesson plans, worksheets, and balanced assessments (diagnostic MCQs with pedagogical distractors, authentic performance tasks/rubrics) grounded in UbD, Smith & Stein, Taylor & Nolen, MLL scaffolds, and course context.

**Source:** `.agents/skills/lesson-assessment-designer/SKILL.md` (instruction-only; references external course readings/templates).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| *No dedicated scripts in skill folder* | N/A | Produces plans/blueprints/rubrics/keys as documents used by downstream drafting/AST/packing skills. | Learning targets, standards, course context, source analyses. | Lesson plan drafts, assessment blueprints, item rationales, rubrics (typically Markdown/JSON/DOCX specs consumed by `assessment-builder`/`worksheet-packer`). |

---

## Skill 14 — `classroom-context`

**Purpose:** Provides Franklin HS room/course context (e.g., Geometry Period 4 MLL needs; AP Stats/AP CS priorities) to ground materials and reflections.

**Source:** `.agents/skills/classroom-context/SKILL.md` (knowledge/instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| *None* | N/A | Contextual grounding for other skills. | Task/course identifier. | Constraints/tone/scaffold guidance applied in drafts and pedagogy. |

---

## Skill 15 — `mll-literacy-scaffolding`

**Purpose:** Evidence-based MLL supports: translanguaging, 3-Reads, WIDA word/sentence/discourse moves, polysemous-word unpacking, multimodal representations, sentence frames, accountable talk; maintain cognitive demand.

**Source:** `.agents/skills/mll-literacy-scaffolding/SKILL.md` (instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| *None* | N/A | Scaffolding design guidance. | Draft items/lesson tasks, learner context. | Revised stems/instructions/frames/organizers integrated into drafts/specs. |

---

## Skill 16 — `personal-writer` (Optional Voice Skill)

**Purpose:** Rewrite/generate materials in the user’s authentic personal voice using local writing samples (per skill definition), while adhering to anti-AI writing rules.

**Source:** `.agents/skills/personal-writer/SKILL.md` (instruction-only).

| Script / Tool | Exists in repo? | Purpose | Inputs | Outputs |
|---|---|---|---|---|
| *None in repo; may read external sample corpus per environment* | N/A | Voice-matched rewriting. | Source text + voice samples (if accessible). | Rewritten text preserving meaning/requirements. |

---

## Recommended Agent Script Pack (to create for a full Copilot implementation)

These are **not all present as named standalone files** in the repo but are implied by the skills; an implementation agent should add them (workspace-local or packaged) with stable I/O:

| Script | Used by skill(s) | Inputs | Outputs |
|---|---|---|---|
| `translate_markdown_to_worksheet_spec.py` | assessment-builder, curriculum-document-pipeline | Final/draft Markdown with sections/problems/choices/image/workspace/hint annotations. | Valid `WorksheetSpec` JSON (`_temp/specs/worksheet_spec.json`). |
| `generate_figures.py` / `generate_<assessment>_figures.py` | assessment-builder, curriculum-visual-generator | Figure manifest; asset dir. | Cropped 300 DPI PNGs in `_temp/assets/`; optional metadata map. |
| `render_pdf_pages.py` | visual-layout-checker | `output/*.pdf`, output dir, DPI. | `_temp/renders/pdf_pages/page_*.png`. |
| `authenticity_lint.py` | authentic-writer, critical-checker | Text/Markdown path. | Violations report (em dashes, banned phrases, preamble/conclusion markers). |
| `check_assessment_requirements.py` | requirement-checker | Draft/spec + requirement manifest (counts, points, topics, page budget). | Pass/fail report + suggested fixes. |
| `extract_course_content.py` | course-content-extractor | Source paths + metadata. | Provenance-rich extraction Markdown + copied/cropped assets list. |

---

## Quick Reference: Primary CLIs

```bash
# Worksheet packing
uv run worksheet-packer info|parse|pack|render|render-docx-pages|convert ...

# PDF -> DOCX
uv run pdf-to-docx ...
python -m pdf_to_docx <subcommand> ...

# PDF -> LaTeX
uv run pdf-to-latex ...
python -m pdf_to_latex <subcommand> ...

# Skill helper scripts
uv run python .agents/skills/pdf-to-docx/scripts/inspect_pdf.py <pdf>
uv run python .agents/skills/pdf-to-docx/scripts/crop_asset.py <pdf> --page N --bbox y0,x0,y1,x1 -o out.png
uv run python .agents/skills/pdf-to-docx/scripts/compile_pages.py <specs_dir> -o output/doc.docx
uv run python .agents/skills/pdf-to-docx/scripts/diff_layout.py <orig_page.png> <output.docx> --page N

uv run python scripts/pdf_to_latex/inspect_pdf.py <pdf>
uv run python scripts/pdf_to_latex/compile_pages.py <specs_dir> -o output/doc.tex --pdf
uv run python scripts/pdf_to_latex/compile_latex.py <doc.tex>
uv run python scripts/pdf_to_latex/diff_layout.py <orig_page.png> <compiled.pdf> --page N -o diff.png
```

*End of document.*

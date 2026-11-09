# Deterministic Document Pipeline: Design Proposal

**Status:** Proposal only. Nothing in the repo has been changed to implement this.
**Scope:** `pdf-to-docx`, `pdf-to-latex`, `worksheet-packer`, `docx-layout-refinement`, `visual-layout-checker`, and (secondary) the assessment/content skills that feed `worksheet-packer`.

---

## 0. TL;DR

Right now the coding agent (Copilot / OpenCode / Antigravity) is the orchestrator. It reads a long skill file, picks a pathway, runs CLI commands, "inspects" JSON, eyeballs renders, edits specs or writes one-off Python, and decides when the result is "flawless." Inside the CLI, the Gemini calls are also asked to make layout decisions (diagram widths, workspace heights, layout hints, font sizes) that are really policy, not perception.

The proposal is to flip that:

1. **One deterministic program owns the whole run** (`docpipe convert input.pdf --profile faithful|repack`). It is a fixed DAG of stages with cached, hashed inputs and outputs.
2. **LLMs are used as sensors, not as decision makers.** They get called in exactly two kinds of places:
   - **Perception:** OCR (reading text, math, tables, chart values) and object detection (finding and classifying regions, rough bounding boxes, reading order).
   - **Visual validation checks** on small crops, where pixel metrics alone can't answer the question. These run in a structured loop with fixed iteration caps.
3. **Everything else is code:** geometry, sizing, typography, numbering, layout, packing, rendering, QA scoring, repair, retries, file naming, resume logic.
4. **The coding agent is out of the happy path.** It only shows up when the pipeline exits with "needs review," and even then it can only apply structured patches (`overrides.yaml`) that are replayed on every rerun, not ad-hoc scripts.

The rest of this doc covers what exists today, where the freedom leaks in, a task-by-task ownership table, the target architecture, the LLM call contract, deterministic QA, and a phased migration plan.

---

## 1. What exists today

### 1.1 The pieces

| Layer | Files | What it does |
| :--- | :--- | :--- |
| Agent instructions | `.agents/skills/pdf-to-docx/SKILL.md` + `references/*`, `pdf-to-latex/SKILL.md`, `worksheet-packer/SKILL.md`, `docx-layout-refinement/SKILL.md`, `visual-layout-checker/SKILL.md`, `assessment-builder/SKILL.md`, `curriculum-document-pipeline/SKILL.md`, etc. | Tell the agent which commands to run and what to "check" |
| PDF access | `src/pdf_to_docx/pdf_extractor.py` | PyMuPDF rendering, region crop, text spans, typography/margins |
| LLM perception | `src/pdf_to_docx/layout_parser.py`, `src/worksheet_packer/worksheet_parser.py` | Gemini page image → `PageSpec` / `RawPageExtraction` JSON |
| IR | `src/pdf_to_docx/ir_schema.py`, `src/worksheet_packer/worksheet_ast.py` | `DocumentSpec`/`PageSpec`, `WorksheetSpec`/`RenderPlan` |
| Layout | `src/worksheet_packer/layout_engine.py`, `image_utils.py` | Footprints, side-by-side vs stacked, 2D packing, slack fill, font scaling |
| Compilers | `src/pdf_to_docx/docx_compiler.py`, `src/pdf_to_latex/latex_compiler.py`, `src/worksheet_packer/docx_renderer.py`, `latex_renderer.py` | IR → DOCX / LaTeX |
| QA | `src/pdf_to_docx/visual_diff.py`, `image_utils.audit_image_boundaries` | LLM fidelity score; edge cutoff audit |
| DOCX input | `src/worksheet_packer/docx_extractor.py` | DOCX → PDF (LibreOffice / Word COM), `word/media` extraction |

The deterministic core is actually in decent shape. The compilers, the packer, the auto-crop, and the cutoff auditor are all plain code. The problem is the glue around them and what the LLM is asked to output.

### 1.2 Where the agent has freedom today

These are direct quotes or close paraphrases from the skill files. Each one is a spot where two runs on the same PDF can diverge.

| Skill | Instruction | Why it's non-deterministic |
| :--- | :--- | :--- |
| `pdf-to-docx/SKILL.md` | Pick one of 4 pathways (IR, Markdown fast-track, "CodeAgent Sandbox", worksheet packer) | Agent judgment; no rule decides |
| `pdf-to-docx/SKILL.md` Phase 2 | "After each page, inspect `page_{k}_spec.json` to ensure table headers, cell values, and any charts/images are accurately captured." | No definition of "accurate," no checker, no stop condition |
| `pdf-to-docx/SKILL.md` Pathway 3 | "Direct executable Python scripts with `python-docx`" | Agent writes a new compiler per document |
| `pdf-to-docx/SKILL.md` Phase 4 | "fix it in the current session ... Perform surgical edits with docx-mcp tools" | Free-form edits to the output, not reproducible |
| `pdf-to-docx/references/workflow_playbook.md` | "Always dispatch subagents for pages 1..N" | Directly contradicts SKILL.md ("Do not start subagents"). README also describes parallel subagents. The agent has to pick which to believe |
| `worksheet-packer/SKILL.md` Phase B | "Inspect the rendered page images with multimodal vision to check question density." / "Customize section ordering or hints in spec.json" | Agent edits the spec by feel |
| `visual-layout-checker/SKILL.md` | Six-point visual checklist, then "update spec, re-pack, re-render; re-audit" | The remediation table is already a lookup table, but it's applied by the agent with no iteration cap |
| `assessment-builder/SKILL.md` Step 5 | LLM translates Markdown → `WorksheetSpec` JSON by hand | A grammar-driven parser could do this exactly |
| `assessment-builder/SKILL.md` Step 6 | "Create a dedicated Python script `_temp/build/generate_figures.py`" | New figure code per task |
| `assessment-builder/SKILL.md` Step 8 | "re-pack, and re-render until flawless" | No measurable target |
| `docx-layout-refinement/SKILL.md` | Whole skill is agent-driven docx-mcp edits | Same as above |

### 1.3 Evidence: how much code the agent is writing per task

Line counts of task-specific scripts under the document workspaces' `_temp/build/` folders:

| Workspace | Scripts | Lines |
| :--- | :--- | ---: |
| `unit1_test_repack/` | `build_final.py`, 6 probe scripts | ~230 |
| `unit_1_review_aligned/` | `compile_review_docx_2page.py` (578), `generate_fresh_figures.py` (430), `compile_review_latex_2page.py` (338), others | ~1,750 |
| `lesson_1_21_streamlined/` | `compile_docx_1page.py` (290), `build_streamlined.py` (205), others | ~660 |
| `codehs_unit1_retake/` | `generate_assessment.py` | 607 |
| `unit2_congruent_triangles/` | `docbuilder.py` (541), `figs.py` (510), others | ~1,150 |
| **Total one-off code** | | **~4,400** |
| For comparison, all of `src/` | | ~6,600 |

So for every 3 lines of library code there are 2 lines of throwaway code written by the agent. Much of it re-implements things that already exist or should exist in `src/`:

- `set_cell_width`, `set_cell_padding`, `make_row_cant_split`, `clear_table_borders` appear in `compile_review_docx_2page.py`, `compile_docx_1page.py`, **and** `src/worksheet_packer/docx_renderer.py`.
- Word COM DOCX→PDF rendering is re-written in `compile_and_render_all.py`, `compile_review_docx_2page.py`, `compile_docx_1page.py`, even though `docx_extractor.convert_docx_to_pdf` exists.
- A working **LaTeX → OMML (native Word math)** converter exists only in `unit2_congruent_triangles/_temp/build/docbuilder.py` (`latex_to_omml_inner`, `add_math`). Meanwhile `src/` renders math as italic Cambria text (`docx_compiler._render_equation`) or regex-to-Unicode (`docx_renderer.clean_math_text_for_docx`).
- A geometry figure helper library (polygons, angle arcs, rigid motions, labels, trim) exists only in `unit2_congruent_triangles/_temp/build/figs.py`.

This is the clearest sign that the agent is doing work that should be a library call.

### 1.4 What the LLM is currently asked to decide (inside the CLI)

`LAYOUT_EXTRACTION_PROMPT` (`src/pdf_to_docx/layout_parser.py:39-56`) with `response_schema=PageSpec` means Gemini can fill any `PageSpec` field. That includes perception fields (fine) and also:

- `width_pt`, `height_pt`, `orientation`, margins (code knows these exactly from `page.rect`)
- `font_size_pt`, `font_name`, `color_hex` on runs
- `alignment`, `list_type`, `list_level`, `line_spacing`, `space_before_pt`, `space_after_pt`
- `TableBlock.col_widths_pct`, `style_name`, `cant_split`, `repeat_header`, `booktabs`, `full_width`
- `ImageBlock.width_inches`, `height_inches`, `width_ratio`
- `ChartBlock.width_inches`, `height_inches`, `reproduce_programmatically`
- `QuestionBlock.response_box_height_pt`, `BoxBlock.height_pt`, `color_hex`

`WORKSHEET_VISION_PROMPT` (`src/worksheet_packer/worksheet_parser.py:80-100`) with `RawProblemExtraction` explicitly asks for:

- `diagram_category`, `diagram_min_width_in`, `diagram_max_width_in` (and `parse_worksheet` blends these into the code-computed bounds at lines 316-325)
- `layout_hint` (side-by-side vs stacked)
- `workspace_type`, `workspace_lines`, `workspace_height_pt`, `approx_workspace_height_in`, `approx_workspace_area_sq_in`

None of those are things a vision model is good at estimating. They're either measurable from the page or are layout policy that `image_utils.estimate_image_scale_bounds` and `LayoutEngine` already compute.

### 1.5 Other things that make runs drift

- **Model alias:** default model is `"gemini-flash-lite-latest"` (`layout_parser.py:75`, `worksheet_parser.py:130`). A `-latest` alias changes under you.
- **Temperature 0.1, no caching.** Every rerun re-asks the model and gets a slightly different answer. Even at temperature 0, hosted models aren't guaranteed bit-stable, so caching is the only real way to make reruns identical.
- **No validation beyond Pydantic.** Nothing checks that bboxes are sane, that table rows have the same width, that LaTeX parses, that question numbers are continuous.
- **Retries only in `worksheet_parser`.** `layout_parser` and `visual_diff` have none.
- **QA is an LLM score.** `VisualDiffInspector` returns a 0–100 `fidelity_score` plus free-text suggestions (`visual_diff.py:119-129`). And `convert --diff` only checks page 1 (`cli.py:407-412`).

---

## 2. Design principles

### 2.1 LLM as sensor

> An LLM call is allowed to answer **"what is on this page and roughly where?"**
> It is never allowed to answer **"how big should this be, where should it go, or is this good enough?"**

Concretely, LLM output must be limited to:

- **Read:** verbatim text, inline math as LaTeX, table cell contents and spans, chart titles/categories/values, code listings.
- **Detect:** region boxes (rough), region kind (from a closed enum), reading order, parent/child links (choice → question, caption → figure, part (b) → question 3), visual style flags it can see (bold, italic, underlined, boxed, shaded).
- **Classify:** a small number of closed-enum labels where semantics matter (document type; question kind like `mcq | numeric | show_work | proof | graphing`).

If a field could be computed from the PDF, the pixels, or a policy table, it doesn't go in the LLM schema.

### 2.2 Everything else is a pure function

Each stage is `outputs = f(inputs, config)`. Same inputs and config give the same outputs. Stages write to disk under `_temp/`, keyed by content hash, so reruns skip finished work automatically (this replaces the "resume by checking which `page_*_spec.json` exist" instructions).

### 2.3 Gates instead of judgment

Every "make sure it looks right" step becomes a measurable check with a threshold. A check either passes, gets auto-repaired by a rule, or ends up in a review list. There's a fixed iteration cap on repair loops.

### 2.4 Agent fixes are data, not code

When a human or coding agent needs to intervene, they edit `overrides.yaml` (structured patches keyed by stable region/problem IDs). The pipeline replays overrides on every run. No new `.py` files per document.

---

## 3. Task-by-task ownership

This is the core of the proposal. Every task that happens today in the PDF → DOCX / worksheet flows, who does it now, and who should own it.

Legend: **LLM** = model call; **Code** = deterministic; **Agent** = coding assistant judgment.

### 3.1 Intake & routing

| # | Task | Today | Proposed | How (code) / Why (LLM) |
| ---: | :--- | :--- | :--- | :--- |
| 1 | Create `output/`, `_temp/{assets,renders,specs,build}` | Agent runs `mkdir` | **Code** | Orchestrator creates them. Agent never touches folder layout |
| 2 | Inspect PDF (pages, size, rotation, images, drawings) | Code, agent invokes | **Code** | Already `PDFExtractor.get_document_info()`. Add `text_chars` per page and `has_text_layer` |
| 3 | Choose pathway (IR / Markdown / sandbox / packer) | Agent | **Code** + one optional **LLM** classify | Profile comes from the CLI flag (`--profile faithful` or `repack`). If not given, one cheap LLM call on page 1 returns `doc_type ∈ {worksheet, report, narrative, form, slides}` and a fixed table maps that to a profile. Drop the Markdown and "sandbox" pathways (see §6.8) |
| 4 | Render pages | Code, agent invokes | **Code** | Fixed DPI per purpose (200 for perception, 300 for crops). Fix naming mismatch (see §10) |

### 3.2 Perception (the LLM's job)

| # | Task | Today | Proposed | Notes |
| ---: | :--- | :--- | :--- | :--- |
| 5 | Find regions on the page and classify them | LLM | **LLM** | Closed enum of kinds (§5.3) |
| 6 | Reading order | LLM | **LLM**, code validates | Code compares to a geometric order (column clustering + top-to-bottom). Disagreements are logged, not silently changed |
| 7 | Rough bbox for each region | LLM | **LLM** rough → **Code** refines | See task 17 |
| 8 | Transcribe text (OCR) | LLM | **LLM** | Optional second pass on per-region crops at higher DPI for tables/math/low-confidence regions |
| 9 | Transcribe math to LaTeX | LLM | **LLM**, code validates | Code parses the LaTeX; failures trigger one targeted re-ask on that crop |
| 10 | Table structure and cell text | LLM | **LLM**, code validates | Code checks rectangularity after spans; mismatches trigger re-ask |
| 11 | Chart type, title, categories, values | LLM | **LLM**, code validates | Code checks `len(values) == len(categories)` per series |
| 12 | Visible style flags (bold/italic/underline/boxed) | LLM | **LLM** for scanned pages; **Code** from text layer when present | Text-layer flags (`span["flags"]`) are exact |
| 13 | Question boundaries, parent/child (parts, choices) | LLM | **LLM** | Semantic grouping is a good LLM task |
| 14 | "Is there a drawn answer box / grid / lines here?" | LLM (as `workspace_type`) | **LLM** detects as a region of kind `answer_space` with subtype `box | grid | lines | blank` | Size is measured by code (task 23) |
| 15 | Document type / question kind | Implicit | **LLM** classify (closed enum) | Feeds policy tables in code |

### 3.3 Geometry & typography (all code)

| # | Task | Today | Proposed | How |
| ---: | :--- | :--- | :--- | :--- |
| 16 | Page size, orientation, margins | LLM (schema) then backfilled | **Code** | `page.rect`; margins from union of all region bboxes + content pixels |
| 17 | Exact figure crop | Code crops LLM's bbox directly | **Code** snaps the LLM bbox | (a) intersect with `page.get_image_rects(xref)` for raster images; (b) union of intersecting `page.cluster_drawings()` rects for vector figures; (c) expand to include nearby short text spans (vertex labels like "A", "30°"); (d) pixel `auto_crop_image` last; (e) `audit_image_boundaries` must pass, else grow by N px and retry |
| 18 | Image display size | LLM `width_inches` (default 5.5 in, almost never set) | **Code** | Faithful profile: physical size from snapped bbox (`(xmax-xmin)/1000 * page_width_pt / 72`). Repack profile: `estimate_image_scale_bounds` + engine |
| 19 | Font size | LLM or substring backfill (`cli.py:116-128`) | **Code** | Text layer when present (match by bbox overlap, not substring). Otherwise measure x-height / line pitch from the crop's row-projection profile and convert px → pt |
| 20 | Heading level | LLM | **Code** from measured size | Cluster heading sizes on the doc, rank → level 1..4. LLM's "this is a heading" stays |
| 21 | Alignment | LLM | **Code** | Compare region bbox to column bounds: centered within tolerance → center; flush right → right; else left. Justified = both edges flush on multi-line paragraphs |
| 22 | List detection / numbering | LLM | **Code** | Regex on transcribed text (`^•`, `^\d+[.)]`, `^\(?[a-z]\)`). LLM just transcribes markers verbatim |
| 23 | Workspace / response box height (faithful) | LLM guesses `response_box_height_pt` | **Code** measures | Vertical blank band between a question's last region and the next region, found by row-projection on the page image. That is what the original author actually left |
| 24 | Workspace height (repack) | LLM guesses inches | **Code** policy table | `question_kind` (LLM) → inches table in config (e.g., `mcq: 0`, `numeric: 0.5`, `show_work: 1.0`, `proof: 1.5`, `graphing: grid 2.0`), scaled by area when column width changes. Optionally blend with the measured source gap |
| 25 | Text/region color | LLM `color_hex` | **Code** | Median of dark pixels inside the region; snap to a small palette |
| 26 | Callout border/shading color | LLM | **Code** | Sample border pixels / fill pixels |
| 27 | Table column widths | LLM `col_widths_pct` | **Code** | From vector ruling lines (`page.get_drawings()` line segments) or from the x-extents of cell bboxes. `page.find_tables()` can cross-check born-digital tables |
| 28 | Question number, part, points parsing | LLM | **Code** | Regex on LLM text: `^(\d+)[.)]`, `^\(?([a-z]|[ivx]+)\)`, `\[(\d+)\s*pts?\]`, `\((\d+)\s*points?\)`. Already partly in `worksheet_ast.parse_prompt_parts` |
| 29 | MC choice labels | LLM | **Code** normalizes | `A.`, `a)`, `(A)` → `(A)`; check continuity |
| 30 | Diagram category & min/max width | LLM + code blend | **Code only** | `estimate_image_scale_bounds` already does it. Remove the LLM fields |
| 31 | Side-by-side vs stacked | LLM `layout_hint` | **Code only** | `LayoutEngine.calculate_problem_footprint` already has the rule. Overrides file can force it |

### 3.4 Build, render, QA, repair

| # | Task | Today | Proposed | How |
| ---: | :--- | :--- | :--- | :--- |
| 32 | Verify each page spec | Agent "inspects" | **Code** validators | §7.1 |
| 33 | Build IR | Code (LLM output *is* the IR) | **Code** | Perception JSON → IR via a deterministic builder (§5.5) |
| 34 | Compile DOCX / LaTeX | Code | **Code** | Plus: OMML math, native charts, correct widths (§6.6) |
| 35 | Render output for QA | Code, agent invokes | **Code** | Word COM preferred on Windows (closest to what teachers see), LibreOffice fallback |
| 36 | Fidelity scoring | LLM 0–100 score | **Code** metrics | §7.2 |
| 37 | Decide what to fix | Agent / LLM free text | **Code** rule table | §7.3 |
| 38 | Apply fix | Agent (docx-mcp edits / spec edits / new scripts) | **Code** re-runs from the affected stage with changed params | Bounded loop |
| 39 | Narrow visual checks pixels can't answer | Agent eyeballs | **LLM** yes/no on crops, in a structured loop | §7.4 |
| 40 | Upgrade charts to native DrawingML | Agent via docx-mcp | **Code** in compiler | §6.6 |
| 41 | Table style polish | Agent via docx-mcp | **Code** theme profiles | Fixed style presets in config |
| 42 | Progress notes / summaries | Agent writes notes in chat | **Code** writes `run_report.json` / `.md` | |
| 43 | Escalation | n/a | **Agent / human**, structured | Only on exit code 2, only via `overrides.yaml` |

---

## 4. Target architecture

### 4.1 Stage graph

```text
                         ┌──────────────────────────────────────────────────────────────────┐
 input.pdf / input.docx  │                       docpipe (deterministic)                    │
 job.yaml (profile, etc) │                                                                  │
          │              │  S0 Intake ─► S1 Render ─► S2 Perceive* ─► S3 Refine Geo         │
          └─────────────►│                                │               │                 │
                         │                                ▼               ▼                 │
                         │                           S4 Validate ◄── re-ask* (≤2)           │
                         │                                │                                 │
                         │                                ▼                                 │
                         │        S5 Normalize semantics (regex, numbering, lists)          │
                         │                                │                                 │
                         │                                ▼                                 │
                         │        S6 Build IR  (DocumentSpec | WorksheetSpec)               │
                         │                                │      ▲ overrides.yaml           │
                         │                                ▼      │                          │
                         │        S7 Layout (repack profile: LayoutEngine.pack)             │
                         │                                │                                 │
                         │                                ▼                                 │
                         │        S8 Compile (DOCX / LaTeX)                                 │
                         │                                │                                 │
                         │                                ▼                                 │
                         │        S9 Render + Measure ──► S10 QA metric gates               │
                         │              ▲                       │                            │
                         │              │         ┌─ PASS ──►  S11 Visual validation loop*  │
                         │              │         │             ┌─────────────────────┐      │
                         │              │ auto-   │             │ For each visual     │      │
                         │              │ repair  │             │ check category:     │      │
                         │              │ (rule   │             │  LLM crop compare   │      │
                         │              │ table)  │             │  ► PASS → next      │      │
                         │              │         │             │  ► FAIL → rule      │      │
                         │              │         │             │    table repair      │      │
                         │              │         │             │    re-render         │      │
                         │              │         │             │    re-check (≤2)     │      │
                         │              │         │             └──────────┬──────────┘      │
                         │              │         │                        │                 │
                         │              ├─────────┘  ◄── FAIL (repair) ───┘                 │
                         │              │ (≤3 metric+visual rounds total)                    │
                         │              │                                  │ DONE            │
                         └──────────────┼──────────────────────────────────┼─────────────────┘
                                        │                                  ▼
                                        │       exit 0: output/*.docx  + run_report.md
                                        │       exit 2: output/*.docx  + review.md (+ crops)
                                        └──►    exit 1: error

   * = the only places an LLM is called
```

### 4.2 Workspace layout (matches AGENTS.md)

```text
<doc_workspace>/
├── input/                         original file (copied, hashed)
├── output/                        final .docx/.pdf/.tex + run_report.md
└── _temp/
    ├── renders/                   page_{k}@200.png, out_page_{k}.png
    ├── assets/                    fig_{region_id}.png (snapped + trimmed)
    ├── specs/
    │   ├── intake.json
    │   ├── perception/page_{k}.json      raw LLM output (validated)
    │   ├── geometry/page_{k}.json        refined boxes + measurements
    │   ├── ir.json                       DocumentSpec or WorksheetSpec
    │   ├── plan.json                     RenderPlan (repack)
    │   └── overrides.yaml                human/agent patches
    ├── llm_cache/{sha256}.json    every model request/response
    ├── qa/                        metrics.json, review.md, crops/
    │   └── visual/                per-check crops + LLM responses per round
    └── build/                     LaTeX aux/logs
```

### 4.3 Orchestrator sketch

No need for Airflow or Prefect. A small stage runner is enough:

```python
@dataclass(frozen=True)
class Stage:
    name: str
    fn: Callable[[Ctx], dict[str, Path]]
    inputs: list[str]          # artifact keys this stage reads
    outputs: list[str]         # artifact keys this stage writes
    version: str               # bump when stage logic changes

def run(stages: list[Stage], ctx: Ctx):
    for st in stages:
        key = sha256(st.name, st.version, ctx.config_hash, *[ctx.hash(i) for i in st.inputs])
        if ctx.manifest.get(st.name) == key and all(ctx.exists(o) for o in st.outputs):
            continue                       # cached, skip
        produced = st.fn(ctx)
        ctx.manifest[st.name] = key
        ctx.record(st.name, produced)
```

`manifest.json` records stage keys, model IDs, prompt versions, and thresholds, so every output can be traced back to exactly what produced it.

### 4.4 CLI surface

```bash
uv run docpipe convert input/quiz.pdf --profile repack --columns 2 -w quiz_ws/
uv run docpipe convert input/report.pdf --profile faithful -w report_ws/
uv run docpipe status -w quiz_ws/          # which stages are cached / stale
uv run docpipe review -w quiz_ws/          # prints review.md
uv run docpipe override set -w quiz_ws/ q7.layout stacked
uv run docpipe override set -w quiz_ws/ r12.text "Find $m\angle ABC$."
uv run docpipe rerun -w quiz_ws/ --from S6
```

Exit codes: `0` all gates pass, `2` output produced but review items remain, `1` hard failure.

The existing `pdf-to-docx`, `pdf-to-latex`, and `worksheet-packer` CLIs stay as lower-level tools; `docpipe` composes them.

---

## 5. Stage details

### 5.1 S0 Intake (code)

Inputs: source file, `job.yaml`.

- Copy source to `input/`, compute SHA-256.
- If `.docx`: convert to PDF (`docx_extractor.convert_docx_to_pdf`), and build a **media map** (§6.7).
- Per page: `rect`, rotation, `text_chars`, `image_xrefs` with rects, `drawings_count`, `cluster_drawings()` rects.
- Resolve profile: CLI flag > `job.yaml` > one LLM classify call (cached).

Output: `_temp/specs/intake.json`.

### 5.2 S1 Render (code)

- Perception renders at a fixed DPI (200). Crop renders at 300.
- One naming scheme everywhere: `page_{k}@{dpi}.png`. (Today `render_all_pages` writes `page_{k}.png` while the DOCX skill tells the agent to pass `orig_p{k}.png`, so `parse-page` silently re-renders into `_temp/specs/.temp_renders/`.)

### 5.3 S2 Perceive (LLM)

**Two passes**, both cached:

- **Pass A (page):** full page image → list of regions with kind, rough bbox, order, parent, and text for simple regions.
- **Pass B (region, selective):** crop at 300 DPI → precise transcription. Only for kinds `table`, `equation`, `chart`, `code`, and any region Pass A marked `confidence: low`, or any region that failed validation in S4. Crops are smaller and give the model fewer chances to drift.

**Perception schema.** This replaces `PageSpec` and `RawProblemExtraction` as the LLM `response_schema`. Note what's missing: no sizes, no fonts, no layout hints, no workspace inches.

```python
RegionKind = Literal[
    "title", "heading", "paragraph", "list_item", "equation", "table", "chart",
    "figure", "caption", "question", "question_part", "choice", "answer_space",
    "callout", "code", "header", "footer", "page_number", "other",
]

class StyleFlags(BaseModel):
    bold: bool = False
    italic: bool = False
    underline: bool = False
    boxed: bool = False
    shaded: bool = False

class Cell(BaseModel):
    text: str                          # inline math as $...$
    row_span: int = 1
    col_span: int = 1
    is_header: bool = False

class ChartData(BaseModel):
    chart_type: Literal["bar", "line", "pie", "scatter", "histogram", "dotplot", "boxplot", "other"]
    title: str | None = None
    x_label: str | None = None
    y_label: str | None = None
    categories: list[str] = []
    series: list[dict] = []            # {"name": str, "values": list[float]}

class Region(BaseModel):
    id: str                            # "p3_r07", assigned in reading order
    kind: RegionKind
    bbox: list[int]                    # [ymin, xmin, ymax, xmax], 0-1000 (Gemini's native convention)
    parent_id: str | None = None       # choice -> question, caption -> figure, part -> question
    text: str | None = None            # verbatim; inline math $...$; keep markers like "3." "(b)" "A."
    latex: str | None = None           # display equations only, no delimiters
    style: StyleFlags | None = None
    cells: list[list[Cell]] | None = None
    chart: ChartData | None = None
    answer_space_type: Literal["blank", "box", "grid", "lines"] | None = None
    question_kind: Literal["mcq", "numeric", "short_answer", "show_work", "proof", "graphing", "matching", "other"] | None = None
    confidence: Literal["high", "low"] = "high"

class PagePerception(BaseModel):
    page_number: int
    regions: list[Region]
```

**Prompt.** Short, because policy is gone. Stored in the repo as `prompts/perception_page_v1.md` and `prompts/perception_region_v1.md`, versioned, and included in the cache key. Rules in the prompt:

- Transcribe exactly; don't fix typos or rephrase.
- Keep numbering/labels in the text (`"3. Find..."`, `"(B) 42"`); code parses them.
- Inline math as `$...$`, display math in `latex`.
- Use only the listed kinds; use `other` if unsure; set `confidence: low` if any character is uncertain.
- Boxes should cover the whole visible element including its labels.
- Don't describe sizes, fonts, colors, or layout.

### 5.4 S3 Refine geometry (code)

For each region:

1. Convert 0–1000 → PDF points with `page.rect`.
2. **Figures:** snap as described in task 17. Record `snap_source ∈ {raster_xref, vector_cluster, pixels}`. If the PDF has the original raster (`page.get_images()`), extract it losslessly with `doc.extract_image(xref)` instead of re-rasterizing.
3. **Text regions:** shrink to content pixels; measure line pitch and x-height via horizontal projection; if a text layer exists, collect overlapping spans (by bbox intersection) for size/font/flags.
4. **Answer spaces:** measure the blank vertical band below the owning question (row-projection on the page image, ignoring light rules/grid lines).
5. **Tables:** detect vector ruling lines inside the bbox; compute column boundaries.
6. **Colors:** sample text and border/fill colors.

Output: `_temp/specs/geometry/page_{k}.json` with refined bboxes and measurements keyed by region ID.

### 5.5 S4 Validate (code) with targeted re-ask (LLM)

Validators (each emits `{region_id, check, severity, detail}`):

| Check | Rule |
| :--- | :--- |
| `bbox_sane` | inside page, positive area, not > 98% of page unless kind is `figure` |
| `overlap` | text-kind regions overlap each other < 15% of the smaller area |
| `orphan_parent` | every `parent_id` exists and has a compatible kind |
| `table_rect` | after expanding spans, every row has the same column count |
| `chart_lengths` | each series has `len(categories)` values (bar/line) |
| `latex_parses` | inline and display math parse (e.g., `pylatexenc`, or the OMML converter itself) |
| `question_numbering` | top-level question numbers are strictly increasing with no gaps (per section) |
| `choices` | choice labels contiguous (A, B, C, D...), no duplicates, parent is a `question` |
| `text_layer_agreement` | **only if a text layer exists and `text_layer_policy != ignore`**: normalized character error rate between LLM text and the text-layer spans inside the bbox < 3% |
| `reading_order` | LLM order vs geometric order; logged only |
| `empty_text` | text kinds have non-empty text |

On failure, S4 re-runs **Pass B for that one region** with the validator message appended ("Row 3 has 4 cells but the header has 5. Re-read the table."). Max 2 re-asks per region. Still failing → region marked `needs_review` with its crop saved to `_temp/qa/crops/`.

**On the text layer:** you said OCR should be done by LLMs, and the sample quiz shows why: page 1 of `tests/stats merged quiz unit 1.pdf` has 0 extractable characters and 1,115 vector drawings, so there's nothing to read except pixels. The design keeps the LLM as the only reader. The text layer, when it exists, is only used as a free second opinion to catch hallucinated or dropped characters. A config switch controls it:

```yaml
text_layer_policy: verify   # ignore | verify | prefer
```

`verify` (default) flags disagreements and re-asks. `prefer` would substitute text-layer text when they disagree (off by default, since you want LLM OCR to be the authority).

### 5.6 S5 Normalize semantics (code)

- Parse labels out of text: question numbers, parts, points, choice letters (task 28–29). Strip them from the body text and store them as fields.
- Lists: detect markers, compute nesting from x-indent clusters.
- Heading levels from measured size ranks (task 20).
- Alignment from bbox vs column bounds (task 21).
- Merge paragraphs the LLM split across a column or page break (last line not terminated + next region starts lowercase + same x-range).
- Drop or keep `header`/`footer`/`page_number` per profile config.

### 5.7 S6 Build IR (code)

Two builders, both deterministic:

- **`perception_to_document_spec()`** for the faithful profile → `DocumentSpec` (existing `ir_schema.py`).
- **`perception_to_worksheet_spec()`** for the repack profile → `WorksheetSpec` (existing `worksheet_ast.py`). Diagram bounds from `estimate_image_scale_bounds`; workspace from the policy table (task 24); `layout_hint = AUTO` unless overridden.

Then **apply `overrides.yaml`**. Overrides are path/value patches on stable IDs:

```yaml
# _temp/specs/overrides.yaml
- target: q7                 # problem id
  set: { layout_hint: stacked }
- target: p2_r04             # region id
  set: { text: "Find $m\\angle ABC$ if $\\overline{AB} \\cong \\overline{BC}$." }
- target: q12.image
  set: { min_width_in: 2.0 }
- target: section_2
  set: { ordering: flexible }
```

IDs are stable because perception is cached: the same input gives the same regions.

### 5.8 S7 Layout (code)

Repack profile only: `LayoutEngine(spec).pack()` as today. Faithful profile skips this (flow layout in Word).

### 5.9 S8 Compile (code)

Existing compilers with the fixes in §6.6.

### 5.10 S9 Render + Measure, S10 QA metric gates, S11 Visual validation loop

Covered in §7. The key change from the current design: S11 is **not optional**. After S10's metric-based gates pass (or exhaust their repair budget), S11 runs a structured visual validation loop using LLM crop comparisons. Metric gates catch measurable regressions (text fidelity, image cutoff, drift); visual validation catches semantic and perceptual issues that metrics miss (garbled math rendering, wrong diagram labels, missing graph elements, misaligned visual elements). Both tiers share a single repair budget (§7.5).

---

## 6. Component-level changes

### 6.1 LLM client (new, shared)

Today there are three copies of the Gemini client setup (`layout_parser.py`, `worksheet_parser.py`, `visual_diff.py`), each with its own markdown-fence stripping, and only one with retries. Replace with one module:

```python
class LLMOracle:
    def __init__(self, model_id: str, cache_dir: Path, prompt_dir: Path): ...

    def call(self, *, prompt_name: str, images: list[bytes], schema: type[BaseModel],
             extra: str = "") -> BaseModel:
        key = sha256(self.model_id, prompt_name, self.prompt_text(prompt_name),
                     schema_json(schema), *images, extra)
        if (hit := self.cache.get(key)): return schema.model_validate(hit)
        resp = self._with_retries(...)          # 429/503 backoff, fixed schedule
        obj = schema.model_validate_json(resp)  # strict; no fence stripping needed with response_schema
        self.cache.put(key, obj, meta={model, prompt_version, latency, tokens})
        return obj
```

Contract:

| Rule | Value |
| :--- | :--- |
| Model ID | Pinned, versioned ID in `job.yaml` (not a `-latest` alias) |
| Temperature | 0 |
| Output | `response_schema` always; strict validation |
| Cache key | model + prompt text + schema + image bytes + extra |
| Retries (transport) | 4 attempts, fixed backoff 2/4/8/16 s |
| Retries (validation) | ≤ 2 targeted re-asks with validator feedback |
| Logging | every call recorded in `manifest.json` with token counts |
| Offline mode | `--llm-cache-only` fails instead of calling; used in tests and reruns |

**Optional self-consistency:** for high-stakes regions (tables, equations), call Pass B twice with different crop paddings and diff. Agreement → accept. Disagreement → third call; majority wins; still split → `needs_review`. This is deterministic given the cache.

### 6.2 `pdf_extractor.py`

Add:

- `image_rects(page)` → `[(xref, Rect)]` via `page.get_image_info(xrefs=True)`.
- `vector_clusters(page)` → `page.cluster_drawings()` rects.
- `extract_original_image(xref)` → lossless bytes via `doc.extract_image`.
- `spans_in_rect(page, rect)` → spans whose bbox intersects (replaces the substring backfill in `cli.py:116-128`, which matches any span whose text is a substring of the run, so a run "a" picks up the first span containing "a").
- `row_projection(png, rect)` / `blank_bands(...)` for workspace measurement.

### 6.3 `layout_parser.py` / `worksheet_parser.py`

- Both become thin callers of `LLMOracle` with the perception schema.
- Remove `parse_markdown_fast_path` and `parse_latex_fast_path` from the default flow (see §6.8).
- `WorksheetParser.parse_worksheet` loses all LLM policy fields; lines 316–325 (blending LLM min/max widths) go away.

### 6.4 `image_utils.py`

- `estimate_image_scale_bounds` hard-codes page height as `11.0` (`source_h = round(h_ratio * 11.0, 2)`, line 146). Use the real page height.
- `has_fine_text` uses an edge-density threshold on a 120×120 downsample. Keep it, but also count text spans / LLM-detected labels inside the figure bbox when available.
- Wire `audit_image_boundaries` into S3 as a required post-crop check.

### 6.5 `layout_engine.py`: replace text height guessing with font metrics

`estimate_text_height` (lines 34–89) assumes `char_width = 0.48 × font_size` and counts characters per line. That's the main reason packed plans and real Word renders disagree, which is what pushes the agent into "re-pack until flawless" loops.

Deterministic replacement:

1. Load the actual font (`C:\Windows\Fonts\calibri.ttf`, etc.) with Pillow `ImageFont.truetype` or `fontTools`.
2. Greedy word-wrap using real advance widths (`font.getlength(word)`), with math segments measured after Unicode/OMML approximation.
3. Line height from the font's ascent + descent × Word's line-spacing factor (`1.05` is set in `_configure_document`).
4. Keep a small calibration factor per font, learned once from the render-measure step (§7.2, `plan_vs_render_drift`) and stored in config.

Same input, same plan, and the plan actually matches what Word renders.

### 6.6 Compilers

| Issue today | Fix |
| :--- | :--- |
| `docx_compiler._render_equation` writes LaTeX as italic Cambria text | Emit OMML. Two options: (a) promote `latex_to_omml_inner` from `unit2_congruent_triangles/_temp/build/docbuilder.py` into `src/` and extend it; (b) LaTeX → MathML (`latex2mathml`) → OMML using Office's `MML2OMML.XSL` via `lxml` XSLT. (b) covers far more LaTeX; (a) has no Office dependency. Either is deterministic |
| `docx_renderer.clean_math_text_for_docx` regex → Unicode (lossy: fractions, `\overline`, nested exponents) | Same OMML path, shared with `docx_compiler` |
| Inline `$...$` inside runs not converted in `docx_compiler` | Split runs on `$...$` (the `add_rich` tokenizer in `docbuilder.py` does this) |
| `_render_image` uses `width_inches` default 5.5 | Use size computed in S3 (faithful) or engine (repack) |
| `_render_table` assumes 6.5 in printable width | Use the section's real printable width |
| `_render_chart` names files `chart_{id(chart)}.png` (memory address, changes each run) | Name by region ID |
| Charts are always raster | Emit native charts in code. Options: call the docx-mcp chart tools programmatically from Python as an MCP client (deterministic tool calls, no agent), or generate the chart XML parts directly. Fall back to the Matplotlib PNG when chart type isn't supported |
| Table styling polish done by agent via docx-mcp | Style presets in config (`theme: navy_grid | booktabs_like | plain`) applied by the compiler |
| Helpers duplicated in task scripts | Move `set_cell_width`, `set_cell_padding`, `clear_table_borders`, `row_cant_split`, `row_height`, `table_indent`, `cell_bottom_border` into one `src/docx_primitives.py` used by both compilers |

### 6.7 DOCX input

`WorksheetParser` calls `extract_docx_media(...)` (line 240) and then ignores the result; diagrams are re-cropped from the rasterized PDF. Better, and fully deterministic:

1. Walk `document.xml` in order; for each `w:drawing`, record `r:embed` → `word/media/imageN.*`, extent (`wp:extent cx/cy`), and the paragraph index.
2. After LLM detection on the rendered page, match each `figure` region to a media file by perceptual hash of the crop vs. the media image (ties broken by document order).
3. Use the original media file in the output, not the crop.

### 6.8 Remove open-ended pathways

- **Markdown fast-track and LaTeX fast-track** let the LLM write the final format directly. That's the least deterministic option in the repo. Recommendation: drop them from the default flow. If a narrative-only document needs speed, the faithful profile with Pass A only is close in cost and still goes through validators.
- **"CodeAgent Sandbox" pathway:** remove. Anything it was used for becomes either a compiler feature, a config option, or an override.

---

## 7. Deterministic QA and repair

### 7.1 Pre-render checks (on IR / plan)

| Check | Profile | Rule |
| :--- | :--- | :--- |
| `region_coverage` | both | every non-dropped perception region maps to exactly one IR node |
| `no_blank_underlines` | repack | no `_{3,}` in any text; no `\hrule` in LaTeX |
| `choices_complete` | both | from S4 |
| `points_sum` | repack | if a header total exists, it equals the sum of problem points |
| `image_legibility` | repack | rendered width ≥ `min_width_in` for every image |
| `aspect_ratio` | both | rendered h/w within 1% of native h/w |
| `column_balance` | repack | per page, `|h(col0) - h(col1)| ≤ 0.75 in` unless ordering is strict and impossible |
| `page_budget` | repack | `plan.total_pages ≤ job.max_pages` |

### 7.2 Post-render checks (render output → PDF → measure)

S9 converts the DOCX to PDF (Word COM first, LibreOffice second) and opens it with PyMuPDF. Because the output is born-digital, its text layer is exact, which makes these checks cheap:

| Metric | How | Gate |
| :--- | :--- | :--- |
| `page_count` | `len(doc)` | faithful: equals source; repack: equals `plan.total_pages` |
| `orphan_spill` | last page content height | > 1.0 in, or flagged |
| `text_fidelity` | Normalized CER between all IR text and the output PDF's text, per page | < 1% |
| `missing_text` | Longest IR text runs not found in output (`page.search_for`) | 0 |
| `plan_vs_render_drift` | For each problem, find its label (e.g. `"7."`) with `search_for`; compare y to `PlacedProblem.y_in` | median drift < 0.15 in; max < 0.5 in |
| `image_cutoff` | `audit_image_boundaries` on every embedded image | all PASS |
| `image_extent` | read `wp:extent` from the DOCX; compare to plan widths | within 2% |
| `visual_similarity` (faithful only) | SSIM per page between source render and output render, at 100 DPI grayscale | logged; gate only if you want it (Word reflows text, so this is a weak signal) |

### 7.3 Repair rule table (replaces the agent loop)

The remediation table in `visual-layout-checker/SKILL.md` §3 is already basically this. Encode it. The table now covers both metric-gate failures (S10) and visual-validation failures (S11):

| Failing check | Source | Action (in order; first one that applies) | Rerun from |
| :--- | :--- | :--- | :--- |
| `page_count` too high (repack) | S10 | (1) font −0.5 pt down to floor 9.5; (2) workspace ×0.9 down to policy floor; (3) `ordering: flexible` for sections marked `allow_flexible: true` in job | S7 |
| `orphan_spill` | S10 | same as above, one step | S7 |
| `plan_vs_render_drift` high | S10 | update font calibration factor from measured drift, repack | S7 |
| `image_cutoff` | S10 | grow snap bbox by 8 px each side, re-crop | S3 |
| `image_legibility` | S10 | force `layout_hint: stacked` for that problem | S7 |
| `column_balance` | S10 | engine's balanced-split retry with different split candidate | S7 |
| `text_fidelity` / `missing_text` | S10 | no auto-fix: compiler bug or font substitution. → review | n/a |
| `aspect_ratio` | S10 | compiler bug → hard error | n/a |
| `diagram_mismatch` (missing labels, wrong geometry) | S11 | re-crop with expanded bbox + label inclusion (S3); if still failing, re-run perception Pass B on that figure region | S3 |
| `equation_mismatch` (rendered math doesn't match LaTeX) | S11 | re-run OMML conversion with fallback renderer; if LaTeX itself is wrong, re-ask Pass B for that equation region | S8 |
| `text_clipped` (LLM detects edge clipping) | S11 | grow region margins by 4 pt; if in repack, try `layout_hint: stacked` | S7 |
| `table_visual_mismatch` (wrong cell count, merged cells look wrong) | S11 | re-run perception Pass B on the table region with validator feedback | S3 |
| `overall_page_layout` (elements visually misplaced or overlapping) | S11 | no auto-fix for layout-level issues → review with annotated crop | n/a |

Rules apply in a fixed order, metric-gate rules first, then visual-validation rules. The combined budget is max 3 repair rounds (§7.5). Each round is logged in `run_report.json` with before/after metrics and visual check results. After 3 rounds, remaining failures go to `review.md`.

### 7.4 Visual validation loop (S11)

S11 is the second tier of QA, running **after** S10's metric gates pass or stabilize. Where S10 checks things that can be measured from the born-digital output (text CER, pixel cutoff, positional drift), S11 checks things that require semantic visual comparison — "does this rendered thing look like the right thing?" These are still perception tasks (comparing what's visible), so they fit the "LLM as sensor" rule.

#### 7.4.1 Why this isn't optional

The pipeline's biggest failure mode is: metrics pass but the output looks wrong to a human. Examples:

- An equation renders as `x² + y² = r²` in the metric layer but the OMML rendering shows garbled symbols or missing overlines.
- A geometry diagram has correct pixel dimensions but a label ("∠ABC") got cropped or placed on the wrong vertex.
- A table has the right cell count but merged cells render with borders in the wrong place.
- A chart image has correct aspect ratio but is the wrong chart (e.g., question 3's chart placed under question 5).

None of these fail any metric gate. They all fail the "does a teacher looking at this see the right thing?" test. That's what S11 catches.

#### 7.4.2 Visual check categories

Each check is a structured yes/no question on **small crops**, never a whole-page score. The LLM receives only the minimum context needed to answer.

| Check ID | Question | Input | Output schema | When to run |
| :--- | :--- | :--- | :--- | :--- |
| `diagram_fidelity` | "Do these two images show the same diagram, with all the same labels and markings?" | source figure crop + rendered figure crop | `{same: bool, missing_labels: list[str], extra_labels: list[str], notes: str}` | Every figure region |
| `equation_fidelity` | "Does this rendered equation match this LaTeX source?" | rendered equation crop + LaTeX string | `{match: bool, discrepancy: str \| null}` | Every display equation; sample of inline equations (every 5th, or all on first run) |
| `text_clipping` | "Is any text in this image cut off at an edge?" | rendered crop around each problem/section | `{clipped: bool, edge: "top" \| "bottom" \| "left" \| "right" \| "none", description: str \| null}` | Every problem crop in repack; page-edge regions in faithful |
| `table_structure` | "Does this rendered table match this source table? Same rows, columns, merged cells, header row?" | source table crop + rendered table crop | `{match: bool, row_count_match: bool, col_count_match: bool, notes: str}` | Every table |
| `chart_identity` | "Do these two charts show the same data?" | source chart crop + rendered chart crop | `{same: bool, notes: str}` | Every chart |
| `page_overview` | "Are all elements on this page properly positioned with no overlapping text, no large blank gaps, and no misaligned columns?" | full rendered page image | `{issues: list[{description: str, severity: "error" \| "warning", approx_location: str}]}` | Every page, as a final sweep |

All checks use `LLMOracle` → cached, deterministic on rerun, logged with token counts.

#### 7.4.3 Loop mechanics

```text
S11 Visual Validation Loop
─────────────────────────
  remaining_budget = 3 - (rounds_used_by_S10)

  for round in 1..remaining_budget:
      findings = []

      # Run all visual checks in parallel (independent crops)
      for check in visual_checks:
          result = LLMOracle.call(check.prompt, check.inputs, check.schema)
          if result indicates failure:
              findings.append((check.id, check.region_id, result))

      if no findings:
          → ALL PASS → exit S11, proceed to exit 0

      # Attempt auto-repair for each finding
      repairable = [f for f in findings if repair_table has action for f.check_id]
      unrepairable = [f for f in findings if f not in repairable]

      if no repairable findings:
          → write all findings to review.md with crops → exit 2

      # Apply repairs (rule table §7.3), re-run from earliest affected stage
      apply_repairs(repairable)
      re_execute(from_stage=earliest_affected_stage)  # S3, S7, or S8
      # This re-triggers S9 (render) and S10 (metric gates)
      # Then loops back to top of S11

  # Budget exhausted
  → write remaining findings to review.md → exit 2
```

Key constraints:
- **Shared budget:** S10 metric repairs and S11 visual repairs draw from the same pool of 3 rounds. If S10 used 2 rounds fixing `page_count`, S11 gets 1 round.
- **No double-counting:** if S11 finds an issue that S10 already checked and passed (e.g., `text_clipping` vs `image_cutoff`), the visual finding takes precedence and can trigger a repair, but the metric gate isn't re-evaluated separately.
- **Crops are saved:** every visual check saves its input crops and LLM response to `_temp/qa/visual/{check_id}_{region_id}_round{N}.json` (and the crop PNGs alongside). This makes debugging and `review.md` generation straightforward.
- **Parallel execution:** all visual checks within a round are independent and can be batched in a single `LLMOracle` multi-call.

#### 7.4.4 What goes in `review.md` from visual checks

When a visual check fails and can't be auto-repaired (or budget is exhausted), `review.md` includes:

```markdown
### Visual: diagram_fidelity — q7.figure (p2_r12)

**Check:** Do source and rendered diagrams match?
**Result:** FAIL — missing labels: ["∠ABC", "30°"]
**Source crop:** _temp/qa/visual/diagram_fidelity_p2_r12_round1_source.png
**Rendered crop:** _temp/qa/visual/diagram_fidelity_p2_r12_round1_rendered.png
**Suggested overrides:**
  - `docpipe override set -w . p2_r12.snap_padding 16`  (expand crop)
  - `docpipe override set -w . p2_r12.text "..."` (fix transcription)
```

This gives the agent (or human) exactly the crops to look at, what failed, and the specific override commands to try — no judgment calls, just "fill in this blank."

### 7.5 Combined QA budget and flow

The full S9→S11 flow, with the shared iteration budget:

1. **S9** renders the output and measures metrics.
2. **S10** evaluates metric gates. If any fail, apply the repair rule table, decrement the budget, re-run from the affected stage. Repeat until metrics pass or budget hits 0.
3. **S11** runs visual validation checks on the (now metric-passing) output. If any fail, apply the visual repair rule table, decrement the budget, re-run from the affected stage (which re-triggers S9→S10→S11). Repeat until visual checks pass or budget hits 0.
4. **Exit:** all pass → exit 0. Any remaining failures → exit 2 with `review.md`.

Total budget across S10+S11: **3 rounds**. This is a hard cap. The rationale: if 3 rounds of targeted, rule-based repairs can't fix it, the issue is structural (wrong perception, missing compiler feature, bad override) and needs human/agent review, not more iteration.

`VisualDiffInspector` with its 0–100 score and free-text suggestions would be retired.

---

## 8. Where an agent still fits

In the happy path, nowhere. The new `pdf-to-docx` skill file shrinks to roughly:

```markdown
1. Run: uv run docpipe convert "<input>" --profile <faithful|repack> -w "<workspace>"
2. If exit code is 0: report output/ paths and the summary from output/run_report.md. Stop.
3. If exit code is 2: open <workspace>/_temp/qa/review.md.
   For each item, use only `docpipe override set ...` with the target ID shown.
   Then: uv run docpipe rerun -w "<workspace>" --from <stage shown in review.md>
   Repeat at most twice. Then report remaining items to the user.
4. Do not write Python scripts, do not edit .docx files directly, do not edit JSON under _temp/specs except overrides.yaml.
```

`review.md` is generated by code and lists only actionable items, each with: the region/problem ID, the check that failed, the measured value vs threshold, the crop path, and the override fields that are allowed for that check. That turns "use your judgment" into "fill in this blank."

---

## 9. Content / assessment pipeline (secondary)

You asked mainly about PDF → DOCX, but `assessment-builder` and `curriculum-document-pipeline` feed the same packer, and they have a lot of deterministic work currently done by the agent. These are writing tasks, where an LLM is legitimately the right tool for drafting, so the split looks different: the LLM writes, code checks and formats.

| Step | Today | Proposed |
| :--- | :--- | :--- |
| Find source files (`course-content-extractor`) | Agent searches hard-coded OneDrive / repo paths | **Code:** a source index (`sources.yaml` with roots; indexer extracts text + images per file into a searchable cache). **LLM:** picks relevant items from search results |
| Draft items | LLM | **LLM** |
| Pedagogy revision | LLM | **LLM** |
| De-fluff / authentic phrasing | LLM, then LLM checks itself | **LLM** rewrites; **Code** lints: banned word list, em dashes (`—`, `--`), sentence-case headings, preamble/conclusion phrases, `_{3,}` underlines. Script was already proposed in `copilot_agent_skills_and_scripts.md` as `authenticity_lint.py` |
| "Preserve structure" during edits (`critical-checker`) | LLM promise | **Code:** frozen-token diff between draft versions. Numbers, LaTeX, code blocks, choice count, problem count must be identical; any change fails the gate |
| Markdown → `WorksheetSpec` (Step 5) | LLM translation | **Code:** strict Markdown grammar parser. The format in `assessment-builder` Step 2 (`#### Problem N (Title) [X pts]`, `- [A] ...`, `- **Image**:`, `- **Workspace**:`, `- **Layout**:`) is already regular enough. Proposed as `translate_markdown_to_worksheet_spec.py` in `copilot_agent_skills_and_scripts.md` |
| Requirement checks (`requirement-checker`) | LLM | **Code** for counts, numbering, points sum, A–D completeness, duplicate choices, answer-key coverage, page budget (via the packer). **LLM** only for "is there one unambiguous correct answer" and "does this cover standard X" |
| Figures (Step 6) | Agent writes `generate_figures.py` per task | **LLM** writes a declarative figure spec (points, segments, labels, angle marks, tick marks, grid ranges); **Code** renders it with a promoted version of `unit2_congruent_triangles/_temp/build/figs.py`. Code also checks geometric claims (e.g., the stated angle equals the drawn angle within 0.5°) |
| Exam integrity ("no verbatim copying") | LLM promise | **Code:** n-gram overlap vs the source exam text (e.g., no 8-gram matches) and "all numeric constants differ" check. LLM rewrites flagged items |
| Visual audit (Step 8) | Agent eyeballs | Same QA gates as §7 |

---

## 10. Bugs and inconsistencies found along the way

These are independent of the redesign and could be fixed early.

1. **Render naming mismatch.** `PDFExtractor.render_all_pages` writes `page_{k}.png` (`pdf_extractor.py:98`), but `pdf-to-docx/SKILL.md` Phase 2 passes `--image _temp/renders/orig_p{k}.png`. The file doesn't exist, so `parse-page` re-renders into `_temp/specs/.temp_renders/` (`cli.py:95-100`), doubling work and breaking workspace hygiene.
2. **`convert` and `parse-page` disagree.** Only `parse-page` backfills margins and typography from the PDF (`cli.py:106-130`); `convert` skips it (`cli.py:364-389`). Same input, different output depending on which command the agent picked.
3. **Substring typography backfill.** `cli.py:121-128` assigns the first span where `s["text"] in r_txt or r_txt in s["text"]`. Short runs match the wrong span.
4. **Image width default.** `ImageBlock.width_inches = 5.5` and the LLM rarely sets it, so most figures come out 5.5 in wide regardless of their original size.
5. **Table width.** `_render_table` assumes 6.5 in printable width even when page margins are backfilled from the PDF.
6. **Chart filenames** use `id(chart)`, which changes every run.
7. **Equations** are rendered as plain italic text in `docx_compiler`; the worksheet renderer converts LaTeX to Unicode with regexes. Neither produces real Word equations.
8. **DOCX media extracted but unused** in `worksheet_parser.py:240`.
9. **Hard-coded 11 in page height** in `image_utils.estimate_image_scale_bounds`.
10. **Visual diff only checks page 1** in `pdf_to_docx convert --diff`.
11. **Contradictory instructions.** `workflow_playbook.md` says "Always dispatch subagents"; `SKILL.md` says never. `workflow_playbook.md` and README use `.conversion_workspace/` and `./assets`; `SKILL.md` uses `_temp/specs/` and `_temp/assets/`.
12. **Model alias** `gemini-flash-lite-latest` plus temperature 0.1 plus no caching means no two runs are guaranteed to match.
13. **Duplicate LLM client code** in three modules, retries in only one.

---

## 11. Migration plan

Ordered so each phase is useful on its own and nothing breaks the current CLIs.

### Phase 0: Stop the drift (small)

- Pin model IDs in one config file; temperature 0.
- Add `LLMOracle` with cache; switch the three existing callers to it.
- Fix bugs 1, 2, 3, 6, 9, 13 from §10.
- Rewrite `workflow_playbook.md` and README to match the no-subagent `SKILL.md`, so the agent stops getting conflicting orders.

Result: rerunning the same PDF gives the same output; reruns are free.

### Phase 1: Perception schema split (medium)

- Introduce `PagePerception` / `Region` as the only LLM schema.
- Write `perception_to_document_spec()` and `perception_to_worksheet_spec()`.
- Remove policy fields from LLM prompts (`diagram_min/max_width_in`, `layout_hint`, workspace inches, sizes, fonts, colors).
- Workspace: measured gap (faithful) or policy table keyed by `question_kind` (repack).

Result: the LLM is a sensor. Layout is fully code.

### Phase 2: Geometry refinement + validators (medium)

- Figure snapping (raster xref, vector clusters, label expansion, pixel trim, cutoff audit).
- Original-image reuse for PDF xrefs and DOCX media.
- Measured font size, heading levels, alignment, colors, table column widths.
- S4 validators with targeted Pass B re-asks.

Result: crops stop clipping labels; tables and math get checked.

### Phase 3: Compiler upgrades (medium)

- `src/docx_primitives.py` (dedupe helpers).
- OMML math in both DOCX compilers.
- Native charts.
- Real widths for images and tables.
- Font-metric text measurement in `LayoutEngine`.

Result: the reasons agents wrote 500-line `docbuilder.py` files go away.

### Phase 4: QA gates + visual validation loop (medium)

- S9 render + measure, S10 metric gates, rule table, `run_report.md`, `review.md`.
- S11 visual validation loop with all six check categories (§7.4.2).
- Retire `VisualDiffInspector`'s 0–100 score; replace with structured per-region visual checks.
- Shared 3-round budget across S10 and S11 (§7.5).

Result: "until flawless" becomes "until metric gates and visual checks pass, max 3 rounds."

### Phase 5: Orchestrator + overrides + thin skills (small–medium)

- `docpipe` CLI with stage runner, manifest, `status`, `rerun --from`, `override set`.
- Rewrite `pdf-to-docx`, `pdf-to-latex`, `worksheet-packer`, `visual-layout-checker`, `docx-layout-refinement` skills as short wrappers (§8).

Result: the agent's role is "run one command, handle review items via overrides."

### Phase 6: Content pipeline tooling (medium)

- Markdown → `WorksheetSpec` parser, authenticity linter, frozen-token diff, requirement checker, figure spec renderer, source indexer, integrity checker.
- Rewrite `assessment-builder` and `curriculum-document-pipeline` so the LLM only drafts and revises, and code runs every check between steps.

---

## 12. Testing strategy

- **Recorded LLM responses.** Commit `llm_cache` entries for the fixture PDFs (`tests/sample.pdf`, `tests/stats merged quiz unit 1.pdf`). Run tests with `--llm-cache-only`. Tests become fully offline and repeatable.
- **Golden IR snapshots.** For each fixture, snapshot `perception/*.json`, `ir.json`, `plan.json`. Any code change that alters them shows up as a reviewable diff.
- **Determinism test.** Build the same fixture twice; compare canonicalized `document.xml` (or byte-identical `.docx` if zip timestamps and core properties are normalized).
- **Validator unit tests.** Hand-made bad perception JSON for each check (ragged table, missing choice C, broken LaTeX, overlapping text regions).
- **Layout engine property tests.** For random problem sets: no overlap, every problem placed once, strict ordering preserved, pages ≤ budget when feasible.
- **Render drift test (Windows only, marked).** Pack, render with Word COM, assert `plan_vs_render_drift` under threshold.

The existing `tests/test_worksheet_packer.py` (974 lines) already covers a lot of the engine; most of it should carry over unchanged.

---

## 13. Open questions for you

1. **Default profile.** For worksheets and quizzes, do you usually want a faithful copy of the original, or always the packed version? This decides which gates are on by default.
2. **Text layer policy.** Is `verify` (LLM is the reader, text layer only flags disagreements) OK, or do you want `ignore` so the text layer is never consulted?
3. **Pass B cost.** Per-region re-reads improve tables and math but add calls. Should Pass B be on for every table/equation, or only when validation fails?
4. **Fast-track pathways.** OK to drop the Markdown and direct-LaTeX fast paths entirely?
5. **Native charts.** How often do your documents have real data charts (vs. stats displays like dotplots and boxplots that are better kept as images)? That decides how much effort native DrawingML deserves.
6. **Visual validation cost tradeoff (S11).** S11 is now a required step, not optional. The six check categories (§7.4.2) add LLM calls per region. Should `page_overview` run on every page or only on pages where a region-level check failed? Should `equation_fidelity` cover all inline math or only display equations + a sample?
7. **Agent environment.** Copilot is the target per the skill files. Should `docpipe` also expose an MCP server so Copilot calls `convert` / `override_set` / `review` as tools instead of shell commands? That would make the agent's allowed actions even narrower.

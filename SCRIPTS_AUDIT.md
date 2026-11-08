# Python Scripts Inventory & Deprecation Audit

This document provides a comprehensive audit of all Python scripts and tooling across the `pdf-to-docx` repository. It identifies redundant duplicates, deprecated subsystems, obsolete scratch scripts, and superseded workspace files resulting from the architectural evolution of the project.

---

## 1. Executive Summary

Over the project's lifecycle, the codebase evolved through three distinct architectural phases:

1. **Phase 1 — Monolithic Prototype & Ad-Hoc Utilities:** Early development centered on [standalone_converter/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/standalone_converter) (local Laya triage + Gemini Flash Lite cascade + in-process docx dispatcher), manual conversion scripts ([tests/convert_quiz.py](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/convert_quiz.py)), and an unintegrated [audit_tools/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools) suite.
2. **Phase 2 — Unified CLI & Page-Parallel Subagents:** Migration to modern, installed packages under `src/` ([src/pdf_to_docx](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_docx), [src/pdf_to_latex](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_latex), and [src/worksheet_packer](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/worksheet_packer)) with registered entrypoints in `pyproject.toml` (`pdf-to-docx`, `pdf-to-latex`, `worksheet-packer`).
3. **Phase 3 — Antigravity Agent Skills & Workspace Packing:** Addition of `.agents/skills/` definitions and isolated task workspaces (`unit1_test_repack`, `unit_1_review_aligned`, `lesson_1_21_streamlined`, `codehs_unit1_retake`).

### Key Findings at a Glance

| Category | Script Count | Primary Finding | Status |
| :--- | :---: | :--- | :--- |
| **Consolidated CLI Scripts** | 11 | `scripts/pdf_to_docx/` and `scripts/pdf_to_latex/` provide convenient standalone runner scripts for subagents | **Consolidated at Root `scripts/`** (removed from `.agents/skills/`) |
| **Legacy Subsystem** | 12 | [standalone_converter/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/standalone_converter) is a superseded monolithic pipeline with an outdated schema | **Deprecated / Superseded by `src/`** |
| **External Batch Runner** | 1 | [batch_convert_stats_archive.py](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/batch_convert_stats_archive.py) targets an external machine path using `standalone_converter` | **Obsolete / Deprecated** |
| **Orphaned Audit Suite** | 7 | [audit_tools/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools) is unreferenced by any skill/test/CLI and imports `standalone_converter.ir_schema` | **Deprecated & Stagnant** |
| **Transient Scratch Scripts** | 8 | [scratch/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scratch) contains one-off experiments and loose PNGs for old debugging | **Safe to remove / Archive** |
| **Ad-Hoc Scripts in `tests/`** | 4 | [tests/convert_quiz.py](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/convert_quiz.py) (807 lines) and small dumpers are manual prototypes, not pytest suites | **Deprecated / Non-Test Clutter** |
| **Document Workspace Scripts** | 27 | Iterative scripts (`v1`/`v2`/`final`) and root clutter across document task folders | **Superseded Iterations / Workspace Hygiene Violations** |
| **Active Production Core** | 27 | Code in `src/` and official test suites (`tests/test_*.py`) | **Active & Maintained** |

---

## 2. Detailed Findings by Subsystem

### 2.1 Consolidated Runner Scripts: `scripts/pdf_to_docx/` & `scripts/pdf_to_latex/`
- **Locations:**
  - `scripts/pdf_to_docx/` (`compile_pages.py`, `convert.py`, `crop_asset.py`, `diff_layout.py`, `inspect_pdf.py`)
  - `scripts/pdf_to_latex/` (`compile_latex.py`, `compile_pages.py`, `convert.py`, `crop_asset.py`, `diff_layout.py`, `inspect_pdf.py`)
- **Analysis:**
  Previously, helper scripts lived inside `.agents/skills/pdf-to-docx/scripts/` and `.agents/skills/pdf-to-latex/scripts/`, with `scripts/pdf_to_latex/` duplicated at root.
  To establish symmetry and keep `.agents/` clean of runnable scripts, all helper scripts were consolidated into the standard root `scripts/` folder, and the duplicate folders in `.agents/skills/` were removed.
- **Verdict:** **Consolidated & Symmetric**.

---

### 2.2 Root Scripts vs. Installed CLI Entrypoints
- **Locations:**
  - `scripts/pdf_to_docx/`
  - `scripts/pdf_to_latex/`
- **Analysis:**
  All of these runner scripts are thin Typer wrappers (25–35 lines each) that forward directly to functions in `pdf_to_docx.cli` and `pdf_to_latex.cli`.
  
  In `pyproject.toml`, the project exposes three first-class CLIs:
  ```toml
  [project.scripts]
  pdf-to-docx = "pdf_to_docx:main"
  pdf-to-latex = "pdf_to_latex:main"
  worksheet-packer = "worksheet_packer:main"
  ```
  Every operation performed by these runner scripts is also available directly:
  - `python scripts/pdf_to_docx/convert.py ...` $\leftrightarrow$ `uv run pdf-to-docx convert ...`
  - `python scripts/pdf_to_docx/compile_pages.py ...` $\leftrightarrow$ `uv run pdf-to-docx compile-pages ...`
  - `python scripts/pdf_to_docx/crop_asset.py ...` $\leftrightarrow$ `uv run pdf-to-docx crop ...`
  - `python scripts/pdf_to_docx/inspect_pdf.py ...` $\leftrightarrow$ `uv run pdf-to-docx info` / `render-pages`
  - `python scripts/pdf_to_docx/diff_layout.py ...` $\leftrightarrow$ `uv run pdf-to-docx diff ...`
- **Verdict:** **Convenience Entrypoints for Subagents & Humans**. Kept in root `scripts/` for easy direct execution without needing to know CLI syntax.

---

### 2.3 Deprecated Subsystem: `standalone_converter/`
- **Location:** [standalone_converter/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/standalone_converter) (12 files, ~110 KB)
- **Files:**
  - `__init__.py`, `__main__.py`
  - `asset_harvester.py`, `asymmetric_cascade.py`, `chart_generator.py`
  - `converter.py`, `docx_compiler.py`, `ir_schema.py`
  - `laya_router.py`, `mcp_dispatcher.py`, `page_parser.py`, `pdf_extractor.py`
- **Analysis:**
  - This was the initial monolithic architecture designed to run Laya local triage, escalate complex pages to Gemini Flash Lite via raw API calls, and dispatch edits via an in-process MCP server.
  - The project shifted to the **Page-Parallel Subagent Architecture** housed in `src/pdf_to_docx/`, `src/pdf_to_latex/`, and `src/worksheet_packer/`.
  - `standalone_converter/ir_schema.py` is an older, frozen fork of `src/pdf_to_docx/ir_schema.py`. It lacks support for LaTeX document classes (`article`, `report`, `exam`, `scrartcl`), `PageBreakBlock`, `EquationBlock`, `BoxBlock`, `QuestionBlock`, and `CodeBlock`.
  - `standalone_converter/docx_compiler.py` and `chart_generator.py` lack updates made to `src/pdf_to_docx/`.
  - `standalone_converter` is not registered in `pyproject.toml` and is only referenced by `batch_convert_stats_archive.py` and `audit_tools/audit_ast.py`.
- **Verdict:** **Deprecated / Superseded Architecture**.

---

### 2.4 Obsolete External Batch Script: `batch_convert_stats_archive.py`
- **Location:** [batch_convert_stats_archive.py](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/batch_convert_stats_archive.py)
- **Analysis:**
  - Contains a hardcoded absolute path to an external directory on your local machine:
    `C:\Users\zubair\Documents\GitHub\stats-archive\02_Free_Response_Questions_by_Year`.
  - Executes subprocess calls to `python -m standalone_converter` with a 10-second sleep delay.
  - Relies entirely on the deprecated `standalone_converter` package.
- **Verdict:** **Deprecated / Obsolete One-Off Script**.

---

### 2.5 Abandoned Audit Framework: `audit_tools/`
- **Location:** [audit_tools/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools) (7 files)
- **Files:**
  - `audit_ast.py`
  - `audit_docx.py`
  - `audit_image_boundaries.py`
  - `audit_pdf_assets.py`
  - `compare_pdf_to_docx.py`
  - `run_all_audits.py`
  - `__init__.py`
- **Analysis:**
  - Built to audit PDF assets and compare generated DOCX against input PDFs.
  - `audit_ast.py` explicitly couples to `standalone_converter.ir_schema.DocumentSpec`:
    ```python
    try:
        from standalone_converter.ir_schema import DocumentSpec
    ```
  - None of the agent skills (`visual-layout-checker`, `docx-layout-refinement`, `pdf-to-docx`), CLI tools, or automated test runners invoke `audit_tools`.
  - Visual verification transitioned to `visual_diff.py` (rendered page comparisons) and `worksheet-packer info`.
- **Verdict:** **Deprecated & Orphaned**. While individual heuristic functions (like edge pixel cutoff detection in `audit_image_boundaries.py`) are clever, the package as a whole is abandoned.

---

### 2.6 Scratch & Prototyping Scripts: `scratch/`
- **Location:** [scratch/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scratch)
- **Files:**
  - `check_docx_drawings.py` (tests OpenXML relations for "stats merged quiz unit 1.docx")
  - `compile_ast.py` (tests AST compilation)
  - `inspect_docx.py` (dumps paragraph and drawing elements)
  - `test_asset_discovery.py` (hardcoded to "tests/stats merged quiz unit 1.pdf")
  - `test_harvest_and_resolve.py` (hardcoded to "tests/stats merged quiz unit 1.pdf")
  - `test_parse.py` (one-off test for layout parser with `.env`)
  - `test_reconciliation.py` (hardcoded to "tests/stats merged quiz unit 1.pdf")
  - `test_whitespace_snapping.py` (prototype for pixel border expansion)
  - Loose image files: `raw_p6_embedded_img.png`, `test_p1_top_resolved.png`, `test_p6_resolved.png`, `test_p7_resolved.png`
- **Analysis:**
  These scripts were temporary scratchpads used while developing vector drawing discovery and whitespace boundary snapping. None are imported anywhere in `src/` or part of standard test execution.
- **Verdict:** **Redundant / Stale Scratch Artifacts**.

---

### 2.7 Ad-Hoc Scripts in `tests/` vs. Real Test Suites
- **Location:** [tests/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests)
- **Analysis:**

| Script | Lines | Role | Verdict |
| :--- | :---: | :--- | :--- |
| `tests/convert_quiz.py` | 807 | Hardcoded, procedural python-docx builder written specifically to convert "stats merged quiz unit 1.pdf" manually | **Deprecated / Historical Prototype** (not an automated test; superseded by `worksheet_packer`) |
| `tests/dump_page_blocks.py` | 24 | Utility dumping PyMuPDF text spans for pages 2–7 of the stats quiz | **Redundant One-Off Utility** |
| `tests/extract_all_assets.py` | 46 | Utility extracting embedded images from the stats quiz | **Redundant One-Off Utility** |
| `tests/test_box.py` | 64 | Scratch script testing nested table border formatting in python-docx | **Obsolete Exploration Script** |
| `tests/test_cli_options.py` | 236 | Pytest unit tests for CLI options and AST saving | **Active Test** |
| `tests/test_latex_pipeline.py` | 227 | Pytest unit tests for LaTeX AST and compilation | **Active Test** |
| `tests/test_pipeline.py` | 100 | Verification test for DOCX AST compiler | **Active Test** |
| `tests/test_subagent_pipeline.py` | 91 | Pytest unit tests for subagent CLI workflows | **Active Test** |
| `tests/test_worksheet_packer.py` | 974 | Comprehensive test suite for AST, packing engine, and image auto-crop | **Active Test** |
| `tests/create_sample_pdf.py` | 96 | Generates `sample.pdf` fixture used by pipeline tests | **Active Test Fixture Generator** |

---

### 2.8 Document Task Workspace Scripts
Across the task folders created for specific document conversions, several scripts exhibit iteration redundancy or violate the workspace hygiene standard (`_temp/build/`):

#### A. `unit1_test_repack/`
All 12 scripts properly reside in `_temp/build/`, but contain multiple superseded development generations:
- **Superseded Iterations:**
  - `run_repack_v1.py` (superseded by `v2` and `build_final.py`)
  - `run_repack_v2.py` (superseded by `build_final.py`)
  - `test_repack.py`, `step1_clean.py`, `build_repack.py`
- **Probe/Diagnostic Scripts:**
  - `check_anchors.py`, `check_breaks.py`, `check_table6.py`, `dump_full_spec.py`, `find_shape_properties.py`, `inspect_images.py`
- **Final Driver:** `build_final.py` (the active script that rendered the final deliverable).

#### B. `unit_1_review_aligned/`
- **Clutter in Workspace Root:** 7 scripts were written to the document root rather than `_temp/build/`:
  - `build_aligned_review.py`, `compile_and_render_all.py`, `compile_review_docx_2page.py`, `compile_review_latex_2page.py`, `generate_fresh_figures.py`, `inspect_plan.py`, `map_images.py`.
- **Superseded Duplicates:**
  - `unit_1_review_aligned/_temp/build/generate_new_figures.py` (5.3 KB) was superseded by the root [generate_fresh_figures.py](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/unit_1_review_aligned/generate_fresh_figures.py) (16.6 KB).

#### C. `lesson_1_21_streamlined/`
- **Clutter in Workspace Root:** 5 scripts sit at document root rather than `_temp/build/`:
  - `clean_encoding.py`, `compile_latex.py`, `compile_latex_1page.py`, `compile_docx_1page.py`, `build_streamlined.py`.
- **Superseded Versions:**
  - `compile_latex.py` (10:23 AM, multi-page overflow) was superseded by `compile_latex_1page.py` (11:37 AM, packed single-page).

#### D. `codehs_unit1_retake/`
- Properly placed in [codehs_unit1_retake/_temp/build/generate_assessment.py](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/codehs_unit1_retake/_temp/build/generate_assessment.py). Self-contained, task-specific generator.

---

## 3. Comprehensive Master Scripts Inventory Table

The following table catalogs every script surveyed in the repository outside `.venv`:

| Path | Primary Function | Category | Status / Assessment |
| :--- | :--- | :--- | :--- |
| **Installed Core Tools (`src/`)** | | | |
| `src/pdf_to_docx/cli.py` | Typer CLI commands for DOCX pipeline | Core Architecture | **Active Production** |
| `src/pdf_to_docx/docx_compiler.py` | OpenXML DOCX builder | Core Architecture | **Active Production** |
| `src/pdf_to_docx/ir_schema.py` | Unified document AST schema | Core Architecture | **Active Production** |
| `src/pdf_to_docx/pdf_extractor.py` | PyMuPDF asset harvesting & rendering | Core Architecture | **Active Production** |
| `src/pdf_to_docx/layout_parser.py` | Vision layout analysis | Core Architecture | **Active Production** |
| `src/pdf_to_docx/chart_generator.py` | Chart rendering & DrawingML args | Core Architecture | **Active Production** |
| `src/pdf_to_docx/visual_diff.py` | Visual comparison inspector | Core Architecture | **Active Production** |
| `src/pdf_to_latex/cli.py` | Typer CLI commands for LaTeX pipeline | Core Architecture | **Active Production** |
| `src/pdf_to_latex/latex_compiler.py` | Deterministic LaTeX generator | Core Architecture | **Active Production** |
| `src/worksheet_packer/cli.py` | CLI commands for 2D packing pipeline | Core Architecture | **Active Production** |
| `src/worksheet_packer/layout_engine.py` | 2D bin-packing & column balancing | Core Architecture | **Active Production** |
| `src/worksheet_packer/worksheet_ast.py` | Worksheet problem AST schema | Core Architecture | **Active Production** |
| `src/worksheet_packer/docx_renderer.py` | Atomic table DOCX renderer | Core Architecture | **Active Production** |
| `src/worksheet_packer/latex_renderer.py` | Minipage LaTeX renderer | Core Architecture | **Active Production** |
| `src/worksheet_packer/worksheet_parser.py`| Multimodal worksheet parser | Core Architecture | **Active Production** |
| `src/worksheet_packer/docx_extractor.py` | Ingests existing DOCX into AST | Core Architecture | **Active Production** |
| `src/worksheet_packer/image_utils.py` | Auto-crop, whitespace trimming, AR | Core Architecture | **Active Production** |
| **Root Convenience Scripts** | | | |
| `scripts/pdf_to_docx/convert.py` | Wrapper calling `pdf_to_docx.cli` | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_docx/compile_pages.py` | Wrapper calling `pdf_to_docx.cli` | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_docx/crop_asset.py` | Wrapper calling `PDFExtractor` | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_docx/diff_layout.py` | Wrapper calling `VisualDiffInspector` | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_docx/inspect_pdf.py` | Wrapper calling `PDFExtractor` | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_latex/convert.py` | Wrapper calling `pdf_to_latex.cli` | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_latex/compile_pages.py` | Wrapper calling `pdf_to_latex.cli` | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_latex/compile_latex.py` | Wrapper calling compiler helper | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_latex/crop_asset.py` | Wrapper calling `PDFExtractor` | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_latex/diff_layout.py` | Wrapper calling visual diff | Root Runner | **Maintained** (convenience runner) |
| `scripts/pdf_to_latex/inspect_pdf.py` | Wrapper calling `PDFExtractor` | Root Runner | **Maintained** (convenience runner) |
| **Legacy Subsystem (`standalone_converter/`)** | | | |
| `standalone_converter/__main__.py` | CLI for monolithic converter | Legacy Subsystem | **Deprecated** (superseded by `pdf-to-docx`) |
| `standalone_converter/converter.py` | Monolithic converter pipeline | Legacy Subsystem | **Deprecated** |
| `standalone_converter/asymmetric_cascade.py` | Laya + Gemini API cascade | Legacy Subsystem | **Deprecated** |
| `standalone_converter/laya_router.py` | Local FastText/Laya triage | Legacy Subsystem | **Deprecated** |
| `standalone_converter/mcp_dispatcher.py` | In-process DOCX MCP server | Legacy Subsystem | **Deprecated** |
| `standalone_converter/ir_schema.py` | Outdated IR schema fork | Legacy Subsystem | **Deprecated** (lacks LaTeX, equations, etc.) |
| `standalone_converter/docx_compiler.py` | Older DOCX compiler | Legacy Subsystem | **Deprecated** (superseded by `src/pdf_to_docx/`) |
| `standalone_converter/chart_generator.py` | Older chart renderer | Legacy Subsystem | **Deprecated** (superseded by `src/pdf_to_docx/`) |
| `standalone_converter/page_parser.py` | Flash Lite page parser | Legacy Subsystem | **Deprecated** |
| `standalone_converter/pdf_extractor.py` | Older extractor | Legacy Subsystem | **Deprecated** |
| `standalone_converter/asset_harvester.py` | Older asset harvester | Legacy Subsystem | **Deprecated** |
| **Root Utilities** | | | |
| `batch_convert_stats_archive.py` | Hardcoded external directory runner | Ad-hoc Utility | **Deprecated / Obsolete** |
| **Audit Framework (`audit_tools/`)** | | | |
| `audit_tools/run_all_audits.py` | Runner for audit suite | Abandoned Audit | **Deprecated & Stagnant** |
| `audit_tools/audit_ast.py` | AST validator (imports `standalone`) | Abandoned Audit | **Deprecated** (tied to deprecated schema) |
| `audit_tools/audit_docx.py` | DOCX OpenXML inspector | Abandoned Audit | **Orphaned** (unreferenced) |
| `audit_tools/audit_image_boundaries.py` | Image cutoff border detector | Abandoned Audit | **Orphaned** (contains useful logic) |
| `audit_tools/audit_pdf_assets.py` | PDF asset auditor | Abandoned Audit | **Orphaned** (unreferenced) |
| `audit_tools/compare_pdf_to_docx.py` | PDF vs DOCX comparator | Abandoned Audit | **Orphaned** (unreferenced) |
| **Scratch Space (`scratch/`)** | | | |
| `scratch/check_docx_drawings.py` | Inspects docx drawing relations | One-off Experiment | **Stale Scratch** |
| `scratch/compile_ast.py` | Quick AST compilation test | One-off Experiment | **Stale Scratch** |
| `scratch/inspect_docx.py` | Dumps docx paragraphs | One-off Experiment | **Stale Scratch** |
| `scratch/test_asset_discovery.py` | Asset discovery probe | One-off Experiment | **Stale Scratch** |
| `scratch/test_harvest_and_resolve.py` | Image resolution test | One-off Experiment | **Stale Scratch** |
| `scratch/test_parse.py` | Parser check with `.env` | One-off Experiment | **Stale Scratch** |
| `scratch/test_reconciliation.py` | Bounding box reconciliation test | One-off Experiment | **Stale Scratch** |
| `scratch/test_whitespace_snapping.py`| Whitespace snapping prototype | One-off Experiment | **Stale Scratch** |
| **Test Directory Ad-Hoc Scripts (`tests/`)** | | | |
| `tests/convert_quiz.py` | 807-line hardcoded manual builder | Manual Prototype | **Deprecated Historical Script** |
| `tests/test_box.py` | Explores python-docx borders | Exploration | **Obsolete One-off** |
| `tests/dump_page_blocks.py` | Dumps text blocks from stats quiz | Utility | **Redundant One-off** |
| `tests/extract_all_assets.py` | Extracts assets from stats quiz | Utility | **Redundant One-off** |
| **Document Workspace Scripts** | | | |
| `unit1_test_repack/.../run_repack_v1.py` | Iteration 1 of test repack | Task Iteration | **Superseded by v2 and `build_final.py`** |
| `unit1_test_repack/.../run_repack_v2.py` | Iteration 2 of test repack | Task Iteration | **Superseded by `build_final.py`** |
| `unit1_test_repack/.../build_repack.py` | Repack builder iteration | Task Iteration | **Superseded by `build_final.py`** |
| `unit1_test_repack/.../step1_clean.py` | Intermediate cleanup | Task Iteration | **Superseded** |
| `unit1_test_repack/.../test_repack.py` | Intermediate smoke test | Task Iteration | **Superseded** |
| `unit1_test_repack/.../build_final.py` | Final render script for test repack | Task Deliverable | **Task Specific Active Driver** |
| `unit1_test_repack/.../check_*.py` (6 files) | Diagnostics (anchors, breaks, tables) | Task Diagnostics | **Task Scratch** |
| `unit_1_review_aligned/_temp/build/generate_new_figures.py` | Early figure generator | Task Iteration | **Superseded by `generate_fresh_figures.py`** |
| `unit_1_review_aligned/generate_fresh_figures.py` | 300 DPI Matplotlib figure generator | Task Deliverable | **Task Specific Active Driver** (needs move to `_temp/build`) |
| `unit_1_review_aligned/compile_review_docx_2page.py` | 2-page DOCX compiler | Task Deliverable | **Task Specific Active Driver** (needs move to `_temp/build`) |
| `unit_1_review_aligned/compile_review_latex_2page.py`| 2-page LaTeX compiler | Task Deliverable | **Task Specific Active Driver** (needs move to `_temp/build`) |
| `unit_1_review_aligned/build_aligned_review.py` | AST review builder | Task Deliverable | **Task Specific Active Driver** (needs move to `_temp/build`) |
| `unit_1_review_aligned/inspect_plan.py`, `map_images.py` | One-off inspections | Task Scratch | **Task Scratch** (needs move to `_temp/build`) |
| `lesson_1_21_streamlined/compile_latex.py` | Multi-page LaTeX compiler | Task Iteration | **Superseded by `compile_latex_1page.py`** |
| `lesson_1_21_streamlined/compile_latex_1page.py` | 1-page packed LaTeX compiler | Task Deliverable | **Task Specific Active Driver** (needs move to `_temp/build`) |
| `lesson_1_21_streamlined/compile_docx_1page.py` | 1-page packed DOCX compiler | Task Deliverable | **Task Specific Active Driver** (needs move to `_temp/build`) |
| `lesson_1_21_streamlined/build_streamlined.py` | Master orchestrator for lesson | Task Deliverable | **Task Specific Active Driver** (needs move to `_temp/build`) |
| `lesson_1_21_streamlined/clean_encoding.py` | Character encoding normalizer | Task Utility | **Task Scratch** |
| `codehs_unit1_retake/.../generate_assessment.py` | Generates retake assessment | Task Deliverable | **Task Specific Active Driver** |

---

## 4. Recommended Cleanup & Consolidation Strategy

Whenever you are ready to perform repository cleanup, here is the prioritized action plan:

### Tier 1: Zero-Risk Instant Deletions
1. **Consolidate Scripts to Root `scripts/` and Delete `.agents/skills/*/scripts`:**
   - Moved helper scripts to `scripts/pdf_to_docx/` and maintained `scripts/pdf_to_latex/`. Deleted `.agents/skills/pdf-to-docx/scripts/` and `.agents/skills/pdf-to-latex/scripts/` to eliminate clone confusion and enforce symmetry.
2. **Delete [batch_convert_stats_archive.py](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/batch_convert_stats_archive.py):**
   - Obsolete, hardcoded external machine path pointing to deprecated tooling.
3. **Delete [scratch/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scratch) directory:**
   - 8 obsolete exploratory scripts and 4 loose PNG files that are not part of the active pipeline.
4. **Clean up ad-hoc non-tests in [tests/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests):**
   - Delete `convert_quiz.py`, `dump_page_blocks.py`, `extract_all_assets.py`, and `test_box.py`.
   - Leaves `tests/` clean with only standard pytest suites (`test_worksheet_packer.py`, `test_subagent_pipeline.py`, `test_cli_options.py`, `test_latex_pipeline.py`, `test_pipeline.py`, and `create_sample_pdf.py`).

### Tier 2: Deprecate or Archive Legacy Subsystems
1. **Archive or Remove [standalone_converter/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/standalone_converter):**
   - The entire subsystem has been superseded by `src/pdf_to_docx`, `src/pdf_to_latex`, and `src/worksheet_packer`.
   - If historical preservation is desired, move to `legacy/standalone_converter/` or remove from git tracking.
2. **Re-evaluate [audit_tools/](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools):**
   - If image boundary cutoff detection (`audit_image_boundaries.py`) is valuable, migrate that specific class into `src/worksheet_packer/image_utils.py` or `src/pdf_to_docx/visual_diff.py`.
   - Remove the rest of `audit_tools/` to eliminate the broken dependency on `standalone_converter.ir_schema`.

### Tier 3: Workspace Hygiene Refinement
1. In `unit1_test_repack/_temp/build/`: Delete intermediate `run_repack_v1.py`, `run_repack_v2.py`, and `test_repack.py`, keeping only `build_final.py`.
2. In `unit_1_review_aligned/`: Move loose root scripts into `unit_1_review_aligned/_temp/build/` and remove superseded `generate_new_figures.py`.
3. In `lesson_1_21_streamlined/`: Move loose root scripts into `lesson_1_21_streamlined/_temp/build/` and delete superseded `compile_latex.py`.


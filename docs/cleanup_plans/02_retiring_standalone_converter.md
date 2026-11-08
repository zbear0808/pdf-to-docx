# Cleanup Plan 02: Retirement & Archival of `standalone_converter/`

This document details the architectural deprecation of the [`standalone_converter/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/standalone_converter) package, compares its legacy design against the production [`src/pdf_to_docx`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_docx) and [`src/worksheet_packer`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/worksheet_packer) subsystems, and specifies a safe deprecation/archival plan.

---

## 1. Background & Evolution Context

Early in this repository's history, the conversion pipeline was implemented as a monolithic single-process package:

- **Triage Router:** Used the `laya` package (FastText/ONNX classifiers) to triage whether a PDF page was simple enough for direct local text/table extraction or required AI vision.
- **API Escalation:** Pages below confidence ($< 0.85$) were sent sequentially or via thread workers directly to Gemini Flash Lite (`gemini--flash-lite-latest`) through the Google GenAI SDK.
- **In-Process MCP Dispatcher:** Executed Word modifications via an in-memory MCP tool dispatcher class mimicking the Model Context Protocol.

### Why This Architecture Was Replaced

1. **Context & Rate Limits:** Monolithic batch API calls incurred frequent rate limits and token spikes when processing multi-page documents.
2. **Subagent Architecture Transition:** Antigravity transitioned to **Page-Parallel Subagents** (`invoke_subagent`), where an orchestrator renders 200–300 DPI page images and dispatches isolated subagents per page. Each subagent parses its page into an isolated `page_{k}_spec.json` and crops visual assets into `_temp/assets/`.
3. **Deterministic Compilers in `src/`:** The final compilation was separated into clean, deterministic OpenXML ([`src/pdf_to_docx/docx_compiler.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_docx/docx_compiler.py)) and LaTeX ([`src/pdf_to_latex/latex_compiler.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_latex/latex_compiler.py)) engines registered in `pyproject.toml`.

As a result, `standalone_converter/` became a dormant codebase with frozen dependencies and an outdated schema.

---

## 2. File Inventory & Dead Code Metrics

[`standalone_converter/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/standalone_converter) contains 12 Python files totaling **~112 KB** of code:

| File                      | Size (Bytes) | Role in Legacy Architecture           | Current Status in Modern Pipeline                       |
| :------------------------ | :----------: | :------------------------------------ | :------------------------------------------------------ |
| `__init__.py`           |    1,187    | Package exports & convenience wrapper | Deprecated                                              |
| `__main__.py`           |    4,375    | ArgumentParser CLI runner             | Superseded by `pdf_to_docx.cli` (Typer)               |
| `asymmetric_cascade.py` |    18,026    | Laya triage + Gemini API escalation   | Abandoned monolithic architecture                       |
| `laya_router.py`        |    10,313    | FastText/Laya local classification    | Abandoned (adds heavy runtime dependencies)             |
| `mcp_dispatcher.py`     |    17,705    | In-process MCP tool simulator         | Abandoned (replaced by native `docx-mcp` or compiler) |
| `ir_schema.py`          |    5,835    | Outdated Pydantic AST schema          | **Stale Fork** (missing LaTeX & exam blocks)      |
| `docx_compiler.py`      |    23,122    | Early Word OpenXML builder            | Outdated copy of `src/pdf_to_docx/docx_compiler.py`   |
| `converter.py`          |    12,408    | Sequential page parsing loop          | Superseded by subagent orchestrator                     |
| `chart_generator.py`    |    3,354    | Early Matplotlib chart generator      | Outdated copy of `src/pdf_to_docx/chart_generator.py` |
| `page_parser.py`        |    8,396    | Direct prompt/response parser         | Superseded by `src/pdf_to_docx/layout_parser.py`      |
| `pdf_extractor.py`      |    5,955    | Early PyMuPDF extractor wrapper       | Superseded by `src/pdf_to_docx/pdf_extractor.py`      |
| `asset_harvester.py`    |    11,972    | Heuristic image asset discovery       | Superseded by subagent bounding-box crops               |

---

## 3. Detailed Technical Divergence

### 3.1 Schema Drift: `ir_schema.py`

Comparing [`standalone_converter/ir_schema.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/standalone_converter/ir_schema.py) with [`src/pdf_to_docx/ir_schema.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_docx/ir_schema.py) shows significant architectural drift:

```diff
# Features present in src/pdf_to_docx/ir_schema.py but MISSING in standalone_converter:
+ class DocumentClass(str, Enum): ARTICLE, REPORT, EXAM, SCRARTCL
+ class PageBreakBlock(BaseModel): explicit page break
+ class EquationBlock(BaseModel): LaTeX/MathML equation
+ class BoxBlock(BaseModel): callouts, shaded tips, exam formulas
+ class QuestionBlock(BaseModel): problem stems, points, choices
+ class CodeBlock(BaseModel): syntax-highlighted code blocks
+ DocumentSpec.margins_in, DocumentSpec.document_class, DocumentSpec.custom_preamble
```

The standalone schema only supported basic Word conversion. Running any modern AST JSON through `standalone_converter` will fail Pydantic validation due to missing block types.

### 3.2 Compilation Drift: `docx_compiler.py` & `chart_generator.py`

- [`src/pdf_to_docx/chart_generator.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_docx/chart_generator.py) supports native Office DrawingML conversion via `to_docx_mcp_chart_args`, area charts, and custom corporate themes. `standalone_converter/chart_generator.py` lacks these features.
- [`src/pdf_to_docx/docx_compiler.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_docx/docx_compiler.py) has advanced table borders, `w:cantSplit` row protections, and custom cell margin padding.

---

## 4. Blast Radius Analysis

What currently depends on `standalone_converter`?

A repository-wide search identified only two files:

1. **[`batch_convert_stats_archive.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/batch_convert_stats_archive.py):**
   - Line 77: Invokes `python -m standalone_converter`. (This script is an obsolete external batch runner, addressed in Cleanup Plan 04).
2. **[`audit_tools/audit_ast.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/audit_tools/audit_ast.py):**
   - Line 23: `from standalone_converter.ir_schema import DocumentSpec`. (Addressed in Cleanup Plan 03).
3. **`pyproject.toml`:**
   - Does NOT list `standalone_converter` in `[project.scripts]`.
4. **Active Tests (`tests/test_*.py`):**
   - Zero test files import `standalone_converter`. All tests import from `pdf_to_docx` or `worksheet_packer`.

**Conclusion:** Removing `standalone_converter` has **zero blast radius** on the active production CLIs or automated test suites.

---

## 5. Step-by-Step Remediation Plan

You have two clean options depending on whether you want to preserve git history locally or purge dead code:

### Option A: Clean Deletion (Recommended)

Since git retains full history, removing dead code keeps the repository focused and clean:

* [ ] 
  ```powershell
  # 1. Remove the entire directory
  Remove-Item -Recurse -Force standalone_converter

  # 2. Run test suite to verify no unintended breaks
  uv run pytest tests/
  ```

### Option B: Archive to `legacy/`

If you prefer keeping legacy code visibly accessible without it cluttering root:

```powershell
# 1. Create legacy archive directory
New-Item -ItemType Directory -Path legacy/standalone_converter -Force

# 2. Move files
Move-Item standalone_converter/* legacy/standalone_converter/
Remove-Item standalone_converter

# 3. Add a DEPRECATED.md marker
Set-Content -Path legacy/standalone_converter/DEPRECATED.md -Value @"
# DEPRECATED: Standalone Converter
This monolithic converter is obsolete and superseded by:
- src/pdf_to_docx
- src/pdf_to_latex
- src/worksheet_packer
"@
```

---

## 6. Verification Checklist

- [ ] `standalone_converter/` is removed from the root directory.
- [ ] No files in `src/` or `tests/` attempt to import from `standalone_converter`.
- [ ] `uv run pdf-to-docx --help` operates normally.
- [ ] `uv run worksheet-packer --help` operates normally.
- [ ] `uv run pytest tests/test_worksheet_packer.py tests/test_subagent_pipeline.py` passes 100%.

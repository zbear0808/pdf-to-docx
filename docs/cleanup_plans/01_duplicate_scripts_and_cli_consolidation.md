# Cleanup Plan 01: Duplicate Scripts & CLI Wrapper Consolidation

This document details the exact duplication between the root [`scripts/pdf_to_latex/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scripts/pdf_to_latex) directory, the skill helper directory [`.agents/skills/pdf-to-latex/scripts/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-latex/scripts), and their functional redundancy with the registered CLI entrypoints in `pyproject.toml`.

---

## 1. Background & Root Cause Analysis

During Phase 2/3 development, helper runner scripts were authored to allow subagents to execute discrete conversion steps (inspect, crop, compile, convert, diff).

However, an asymmetry was introduced across the codebase:
1. The Word pipeline put its helper runners in [`.agents/skills/pdf-to-docx/scripts/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-docx/scripts). No root `scripts/pdf_to_docx/` folder was ever created.
2. The LaTeX pipeline originally authored scripts in [`scripts/pdf_to_latex/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scripts/pdf_to_latex), and then copied them verbatim into [`.agents/skills/pdf-to-latex/scripts/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-latex/scripts).
3. In [`.agents/skills/pdf-to-latex/SKILL.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-latex/SKILL.md), documentation examples explicitly referenced `python scripts/pdf_to_latex/...`, while [`.agents/skills/pdf-to-docx/SKILL.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-docx/SKILL.md) referenced `python .agents/skills/pdf-to-docx/scripts/...`.
4. Concurrently, both [`src/pdf_to_docx/cli.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_docx/cli.py) and [`src/pdf_to_latex/cli.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/src/pdf_to_latex/cli.py) evolved to expose these exact capabilities as registered CLI commands via `pyproject.toml`.

---

## 2. File Inventory & Byte Comparison

The table below shows the exact byte-level match between the root directory and the skill folder:

| Script Name | Root Path Size ([`scripts/pdf_to_latex/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scripts/pdf_to_latex)) | Skill Path Size ([`.agents/skills/pdf-to-latex/scripts/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-latex/scripts)) | Checksum Diff Status |
| :--- | :---: | :---: | :---: |
| `compile_latex.py` | 1,358 bytes | 1,358 bytes | **100% Identical** |
| `compile_pages.py` | 1,695 bytes | 1,695 bytes | **100% Identical** |
| `convert.py` | 1,631 bytes | 1,631 bytes | **100% Identical** |
| `crop_asset.py` | 1,196 bytes | 1,196 bytes | **100% Identical** |
| `diff_layout.py` | 2,370 bytes | 2,370 bytes | **100% Identical** |
| `inspect_pdf.py` | 1,960 bytes | 1,960 bytes | **100% Identical** |

Total redundant bytes: **10,210 bytes** across 6 clone files.

---

## 3. Redundancy Analysis with Installed CLIs

In [`pyproject.toml`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/pyproject.toml), lines 23–27 register the production CLI console scripts:

```toml
[project.scripts]
pdf-to-docx = "pdf_to_docx:main"
pdf-to-latex = "pdf_to_latex:main"
worksheet-packer = "worksheet_packer:main"
```

Examining the implementation of any of these helper scripts reveals that they are trivial 20–35 line wrappers around the CLI library functions:

### Example: `convert.py`
```python
# .agents/skills/pdf-to-latex/scripts/convert.py
from pdf_to_latex.cli import convert as cli_convert

def main(pdf_path: Path, output: Path, ...):
    cli_convert(pdf_path, output_tex=output, ...)
```

### Complete CLI Command Mapping Table

| Runner Script | Underlying Library Function | Registered CLI Equivalent Command |
| :--- | :--- | :--- |
| `convert.py` | `pdf_to_latex.cli.convert` | `uv run pdf-to-latex convert <pdf> -o <tex> [flags]` |
| `compile_pages.py` | `pdf_to_latex.cli.compile_pages` | `uv run pdf-to-latex compile-pages <dir> -o <tex> --pdf` |
| `compile_latex.py` | `pdf_to_latex.latex_compiler.compile_tex_to_pdf` | `uv run pdf-to-latex compile-tex <tex> -o <pdf>` |
| `crop_asset.py` | `pdf_to_docx.pdf_extractor.PDFExtractor.extract_region` | `uv run pdf-to-latex crop <pdf> --page <n> --bbox <y1,x1,y2,x2> -o <out>` |
| `inspect_pdf.py` | `PDFExtractor.get_document_info` & `render_all_pages` | `uv run pdf-to-latex info <pdf>` / `uv run pdf-to-latex render-pages <pdf>` |
| `diff_layout.py` | `pdf_to_docx.visual_diff.VisualDiffInspector` | `uv run pdf-to-latex diff <orig_png> <compiled_pdf> --page <n>` |

The same 1:1 mapping applies to [`.agents/skills/pdf-to-docx/scripts/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-docx/scripts) against `uv run pdf-to-docx <command>`.

---

## 4. Blast Radius & Reference Audit

Before deleting [`scripts/pdf_to_latex/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scripts/pdf_to_latex), all references in documentation and markdown skills were audited:

1. **[`README.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/README.md#L30):**
   ```text
   Line 30: └─► LaTeX: python scripts/pdf_to_latex/compile_pages.py .conversion_workspace/ -o doc.tex --pdf
   ```
   *Action:* Change to:
   ```text
   └─► LaTeX: uv run pdf-to-latex compile-pages .conversion_workspace/ -o doc.tex --pdf
   ```

2. **[`.agents/skills/pdf-to-latex/SKILL.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-latex/SKILL.md):**
   - Line 64: `uv run python scripts/pdf_to_latex/compile_pages.py ...`
   - Line 75: `uv run python scripts/pdf_to_latex/inspect_pdf.py ...`
   - Line 131: `uv run python scripts/pdf_to_latex/compile_pages.py ...`
   - Line 152: `uv run python scripts/pdf_to_latex/compile_latex.py ...`
   - Line 163: `uv run python scripts/pdf_to_latex/diff_layout.py ...`
   *Action:* Align with standard CLI commands (`uv run pdf-to-latex compile-pages ...`, `uv run pdf-to-latex info ...`, etc.) or update to `.agents/skills/pdf-to-latex/scripts/...`.

3. **[`copilot_agent_skills_and_scripts.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/copilot_agent_skills_and_scripts.md#L119):**
   - Lines 5, 119, 188, 191–197 mention `scripts/pdf_to_latex/`.
   *Action:* Update to reflect the official CLI entrypoint or skill path.

4. **Code Imports:**
   - Zero `.py` files import from `scripts.pdf_to_latex`. All internal code imports directly from `pdf_to_latex` or `pdf_to_docx`.

---

## 5. Step-by-Step Remediation Plan

### Step 1: Remove the Root Clone Folder
```powershell
Remove-Item -Recurse -Force scripts/pdf_to_latex
# If scripts/ is now empty, remove scripts/
if ((Get-ChildItem scripts).Count -eq 0) { Remove-Item scripts }
```

### Step 2: Update References in [`README.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/README.md)
Update line 30 to use the installed CLI command:
```diff
- └─► LaTeX: python scripts/pdf_to_latex/compile_pages.py .conversion_workspace/ -o doc.tex --pdf
+ └─► LaTeX: uv run pdf-to-latex compile-pages .conversion_workspace/ -o doc.tex --pdf
```

### Step 3: Normalize Skill Instructions in [`.agents/skills/pdf-to-latex/SKILL.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/.agents/skills/pdf-to-latex/SKILL.md)
Update the command examples to either use `uv run pdf-to-latex <cmd>` (recommended) or use the internal path `.agents/skills/pdf-to-latex/scripts/<script>.py`.

### Step 4 (Optional): Skill Scripts Retention Decision
- **Option A (Recommended):** Keep `.agents/skills/pdf-to-docx/scripts/` and `.agents/skills/pdf-to-latex/scripts/` inside `.agents/` as standalone runner artifacts for autonomous subagents that prefer file execution.
- **Option B (Pure CLI):** Remove both `.agents/skills/*/scripts/` folders entirely and standardize 100% of subagent prompts on `uv run pdf-to-docx` and `uv run pdf-to-latex`.

---

## 6. Verification Checklist

- [ ] Directory `scripts/pdf_to_latex/` no longer exists.
- [ ] `git status` shows no untracked or deleted dependencies in `src/`.
- [ ] Running `uv run pdf-to-latex --help` outputs all expected CLI subcommands.
- [ ] Running `uv run pdf-to-docx --help` outputs all expected CLI subcommands.
- [ ] Running `uv run pytest tests/test_latex_pipeline.py` passes without errors.

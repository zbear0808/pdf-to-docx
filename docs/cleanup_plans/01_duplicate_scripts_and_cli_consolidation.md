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

## 2. Implementation & Resolution

### Actions Executed:
1. **Established `scripts/pdf_to_docx/`:**
   Moved all 5 Word pipeline runner scripts into the standard root `scripts/` directory:
   - `scripts/pdf_to_docx/compile_pages.py`
   - `scripts/pdf_to_docx/convert.py`
   - `scripts/pdf_to_docx/crop_asset.py`
   - `scripts/pdf_to_docx/diff_layout.py`
   - `scripts/pdf_to_docx/inspect_pdf.py`

2. **Standardized `scripts/pdf_to_latex/`:**
   Preserved the existing 6 LaTeX pipeline runner scripts in `scripts/pdf_to_latex/`:
   - `scripts/pdf_to_latex/compile_latex.py`
   - `scripts/pdf_to_latex/compile_pages.py`
   - `scripts/pdf_to_latex/convert.py`
   - `scripts/pdf_to_latex/crop_asset.py`
   - `scripts/pdf_to_latex/diff_layout.py`
   - `scripts/pdf_to_latex/inspect_pdf.py`

3. **Removed Duplicate Scripts from `.agents/`:**
   Completely removed:
   - `.agents/skills/pdf-to-docx/scripts/`
   - `.agents/skills/pdf-to-latex/scripts/`
   Ensured that no executable `.py` scripts live inside `.agents/skills/`.

4. **Updated References & Dependencies:**
   - `AGENTS.md`: Updated crop script command to point to `scripts/pdf_to_docx/crop_asset.py`.
   - `GEMINI.md`: Updated crop script command to point to `scripts/pdf_to_docx/crop_asset.py`.
   - `.agents/skills/pdf-to-docx/SKILL.md`: Updated runner script paths (`inspect_pdf.py`, `compile_pages.py`, `diff_layout.py`) to point to `scripts/pdf_to_docx/`.
   - `copilot_agent_skills_and_scripts.md`: Updated all references and tables to reflect `scripts/pdf_to_docx/` and `scripts/pdf_to_latex/`.
   - `SCRIPTS_AUDIT.md`: Updated inventory and status to reflect the symmetric structure and cleanup.

5. **Verification:**
   - Ran `uv run python scripts/pdf_to_docx/inspect_pdf.py --help` (verified functioning).
   - Ran `uv run python scripts/pdf_to_latex/inspect_pdf.py --help` (verified functioning).
   - Ran unit test suite (`uv run python -m unittest discover -s tests`) - all 16 tests pass with 0 errors.
   - Verified zero remaining script directories under `.agents/`.

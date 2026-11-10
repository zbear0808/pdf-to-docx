# LaTeX Workflow Playbook & Decision Matrix

This playbook outlines operational procedures, decision criteria, subagent prompt templates, and troubleshooting steps for the `pdf-to-latex` conversion skill.

---

## 1. Decision Matrix

Choose the best conversion pathway based on the document type:

| Document Profile | Recommended Pathway | Recommended Document Class |
| :--- | :--- | :--- |
| **Exam / Quiz / Worksheet** (AP tests, problem sets, answer blanks) | Pathway 1 (AST IR) | `exam` |
| **Research Paper / Scientific Report** (Formulas, figures, citations) | Pathway 1 (AST IR) | `article` or `scrartcl` |
| **Narrative Paper / Lecture Notes** (Linear text, simple equations) | Pathway 2 (Direct Fragments) | `article` |
| **Long Book / Whitepaper** (Multiple chapters, complex tables) | Pathway 1 (AST IR) | `report` |

---

## 2. Subagent Dispatch Patterns

Use one subagent per page (or per section) when the environment supports subagents: the orchestrator renders pages, launches page subagents with the page image path and the output spec path, and merges. If subagents are not available (e.g., Microsoft Copilot), process pages one at a time in this session with the same files, using these templates as your per-page checklist. Paths follow the repo `AGENTS.md` layout (`_temp/renders/`, `_temp/specs/`, `_temp/assets/`, `_temp/build/`, `output/`).

### Pathway 1: AST Extraction Subagent Prompt
```text
You are the dedicated LaTeX extractor for Page {PAGE} of '{PDF_PATH}'.
Rendered image: '_temp/renders/page_{PAGE}.png'.

Your task:
1. Parse Page {PAGE} into the canonical PageSpec AST JSON schema.
   Run: uv run python -m pdf_to_latex parse-page {PDF_PATH} --page {PAGE} --image _temp/renders/page_{PAGE}.png -o _temp/specs/page_{PAGE}_spec.json --assets-dir _temp/assets
2. Inspect _temp/specs/page_{PAGE}_spec.json to ensure:
   - Mathematical expressions are rendered in LaTeX ($...$ or EquationBlock).
   - Any question numbers, choices, and response box heights are preserved.
   - Tables use headers and rows cleanly.
3. Reply with a 2-line completion summary: total blocks, equations, tables, questions, and confirmation of file creation.
Do NOT dump large JSON in your final reply to keep parent context compact.
```

### Pathway 2: Fast-Track LaTeX Fragment Subagent Prompt
```text
You are the dedicated LaTeX extractor for Page {PAGE} of '{PDF_PATH}'.
Rendered image: '_temp/renders/page_{PAGE}.png'.

Your task:
1. Convert Page {PAGE} directly into a modular LaTeX fragment.
   Run: uv run python -m pdf_to_latex to-latex-page {PDF_PATH} --page {PAGE} --image _temp/renders/page_{PAGE}.png -o _temp/specs/page_{PAGE}.tex
2. Verify that formulas, tables, and question formats are well-formed LaTeX.
3. Reply with a 2-line completion summary confirming page_{PAGE}.tex creation.
Do NOT include markdown fences in your final reply.
```

---

## 3. Collecting Results

When orchestrating page subagents:
- **Never poll or sleep**: Stop calling tools and end your turn; the platform notifies you as each subagent completes.
- Without subagents, just finish page `k` before starting page `k+1`.
- Once every page output exists, assemble and compile (build files go to `_temp/build`; run from the workspace root):
  ```powershell
  uv run python scripts/pdf_to_latex/compile_pages.py _temp/specs/ -o output/document.tex --doc-class {CLASS} --assets-dir _temp/assets
  latexmk -pdf -interaction=nonstopmode -output-directory=_temp/build output/document.tex
  Copy-Item _temp/build/document.pdf output/
  ```

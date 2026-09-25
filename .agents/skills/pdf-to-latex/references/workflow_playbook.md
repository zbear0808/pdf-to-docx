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

### Pathway 1: AST Extraction Subagent Prompt
```text
You are the dedicated LaTeX extractor for Page {PAGE} of '{PDF_PATH}'.
Rendered image: './rendered_pages/page_{PAGE}.png'.

Your task:
1. Parse Page {PAGE} into the canonical PageSpec AST JSON schema.
   Run: uv run python -m pdf_to_latex parse-page {PDF_PATH} --page {PAGE} --image ./rendered_pages/page_{PAGE}.png -o .conversion_workspace/page_{PAGE}_spec.json --assets-dir ./assets
2. Inspect .conversion_workspace/page_{PAGE}_spec.json to ensure:
   - Mathematical expressions are rendered in LaTeX ($...$ or EquationBlock).
   - Any question numbers, choices, and response box heights are preserved.
   - Tables use headers and rows cleanly.
3. Reply with a 2-line completion summary: total blocks, equations, tables, questions, and confirmation of file creation.
Do NOT dump large JSON in your final reply to keep parent context compact.
```

### Pathway 2: Fast-Track LaTeX Fragment Subagent Prompt
```text
You are the dedicated LaTeX extractor for Page {PAGE} of '{PDF_PATH}'.
Rendered image: './rendered_pages/page_{PAGE}.png'.

Your task:
1. Convert Page {PAGE} directly into a modular LaTeX fragment.
   Run: uv run python -m pdf_to_latex to-latex-page {PDF_PATH} --page {PAGE} --image ./rendered_pages/page_{PAGE}.png -o .conversion_workspace/page_{PAGE}.tex
2. Verify that formulas, tables, and question formats are well-formed LaTeX.
3. Reply with a 2-line completion summary confirming page_{PAGE}.tex creation.
Do NOT include markdown fences in your final reply.
```

---

## 3. Reactive Wakeup Best Practice

When orchestrating multiple subagents via `invoke_subagent`:
- **Never poll or sleep**: Stop calling tools and end your turn.
- The platform will awaken your agent with a notification as each subagent completes.
- Once all subagents are complete, run the compilation script:
  ```bash
  uv run python scripts/pdf_to_latex/compile_pages.py .conversion_workspace/ -o document.tex --doc-class {CLASS} --pdf
  ```

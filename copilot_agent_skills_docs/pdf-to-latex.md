# Skill: pdf-to-latex

## Description

_Source: `C:\Users\zubair\Documents\GitHub\pdf-to-docx\.agents\skills\pdf-to-latex\SKILL.md`

```markdown
---
name: pdf-to-latex
description: >-
  Converts PDF documents into high-fidelity, compilable LaTeX (.tex) documents and PDFs using a multimodal
  LaTeX Intermediate Representation (IR), PyMuPDF asset harvesting, and deterministic compilation. Runs as a
  sequential, single-agent workflow (no subagents). Specializes in advanced mathematics, technical tables, and exam/quiz worksheets.
---

# PDF to High-Fidelity LaTeX Conversion Skill

This skill executes an autonomous, page-parallel pipeline to transform complex PDF documents into publication-ready, compilable LaTeX (`.tex`) documents and PDFs.

## Core Principle: Sequential Single-Agent Execution (No Subagents)

> [!IMPORTANT]
> **Do not start subagents or use agent-delegation tools** (e.g., `invoke_subagent`, `task`). Microsoft Copilot and similar environments may not support them.
>
> Process pages **one at a time in the current session**, writing each page’s outputs to disk (`_temp/specs/`, `_temp/assets/`, `_temp/renders/`) before moving to the next page. Keep progress durable and resume by skipping pages whose `page_*_spec.json` / `page_*.tex` output already exists.

---

## 3 Conversion Pathways

| Pathway | Document Characteristics | Primary Tooling | Execution Pattern |
| :--- | :--- | :--- | :--- |
| **Pathway 1: LaTeX AST IR (Default)** | Mathematical papers, multi-column reports, exams/quizzes, structured tables + charts + images | `pdf_to_latex` CLI AST Compiler | Extract `page_{k}_spec.json` per page sequentially; compile all specs |
| **Pathway 2: Direct LaTeX Fragments** | Standard narrative papers, lecture notes, straightforward equations | Gemini Vision fast-path + `pdf_to_latex merge-latex` | Extract `page_{k}.tex` per page sequentially; merge |
| **Pathway 3: CodeAgent Sandbox** | Complex TikZ diagrams, dynamic geometry, specialized custom exam environments | Python / TeX script sandbox | Run dedicated scripts in the current session |

---

## Directory Layout & Workspace Hygiene

All LaTeX conversion workflows must isolate outputs and temporary files into standard subfolders:
```text
<document_workspace>/
├── output/                 # Final deliverables (.tex, .pdf)
└── _temp/                  # ALL temporary & intermediate working files
    ├── assets/             # Harvested/cropped figures, diagrams, formulas
    ├── renders/            # High-resolution rendered page PNGs (page_{k}.png)
    ├── specs/              # Extracted AST JSONs (page_*_spec.json, document_spec.json)
    └── build/              # LaTeX compile artifacts (.aux, .log, .fls, .fdb_latexmk)
```
This guarantees that all transient files are automatically matched by gitignore rules (`**/_temp/`).

---

## Step-by-Step Execution Workflow

```
[ Single Agent / Current Session ]
       │
       ├─► 1. Inspect PDF structure (page count N, dimensions, local LaTeX compiler)
       ├─► 2. Render all pages to PNGs (_temp/renders/page_{k}.png)
       │
       ├─► 3. For each page k = 1..N (sequential)
       │         └──► Parse page k → _temp/specs/page_{k}_spec.json (or page_{k}.tex) and crop assets to _temp/assets/
       │              Resume by skipping pages whose output file already exists
       │
       ├─► 4. Compile assembled specs: uv run python scripts/pdf_to_latex/compile_pages.py _temp/specs/ -o output/document.tex --pdf
       │
       └─► 5. Optional QA: compare compiled PDF with original renderings (diff_layout.py)
```

---

### Phase 1: Orchestrator Intake & Page Rendering

1. Inspect PDF structure, total page count, orientation, and detected LaTeX compilers:
   ```bash
   uv run python scripts/pdf_to_latex/inspect_pdf.py path/to/document.pdf
   ```
2. Create standardized subfolders:
   ```bash
   mkdir -p output _temp/renders _temp/assets _temp/specs _temp/build
   ```
3. Render all pages to high-resolution PNG images (`200 DPI`) into `_temp/renders`:
   ```bash
   uv run python -m pdf_to_latex render-pages path/to/document.pdf -o _temp/renders
   ```

---

### Phase 2: Per-Page Extraction (Sequential)

Process each page in the current session. For every page `k` (1-indexed), run:

```bash
uv run python -m pdf_to_latex parse-page path/to/document.pdf --page {k} --image _temp/renders/page_{k}.png -o _temp/specs/page_{k}_spec.json --assets-dir _temp/assets
```

- After each page, inspect `_temp/specs/page_{k}_spec.json` to ensure mathematical formulas (`$...$`, display equations), table headers, and question blocks are accurately captured.
- Keep a brief running note (page number, block/equation/table counts, issues) instead of dumping large JSON into chat.
- **Resume-friendly:** if `_temp/specs/page_{k}_spec.json` already exists and is valid, skip and continue.

#### Fast-Track Direct LaTeX Fragment Alternative (Pathway 2)
```bash
uv run python -m pdf_to_latex to-latex-page path/to/document.pdf --page {k} --image _temp/renders/page_{k}.png -o _temp/specs/page_{k}.tex
```

---

### Phase 3: Assembly & Compilation

Once all required page outputs exist in `_temp/specs/` (`page_*_spec.json` for Pathway 1 or `page_*.tex` for Pathway 2):

#### For Pathway 1 (Block-Based IR):
Compile the assembled `page_*_spec.json` files directly into `.tex` and `.pdf` inside `output/`:

```bash
uv run python scripts/pdf_to_latex/compile_pages.py _temp/specs/ -o output/document.tex --title "Document Title" --doc-class article --pdf --save-ast
```

Available document classes:
- `--doc-class article` (Default: technical reports, research papers)
- `--doc-class exam` (Quizzes, tests, problem sets with `\question`, choices, and response boxes)
- `--doc-class report` (Long-form documents with chapters)
- `--doc-class scrartcl` (Modern KOMA-Script article)

#### For Pathway 2 (Direct LaTeX Fragments):
Assemble modular page fragments into a master document:
```bash
uv run python -m pdf_to_latex merge-latex .conversion_workspace/ -o document.tex --title "Document Title" --pdf
```

---

### Phase 4: Local Compilation or Remote Export

1. If a local LaTeX engine (`latexmk`, `tectonic`, `xelatex`, `pdflatex`, `lualatex`) is installed:
   ```bash
   uv run python scripts/pdf_to_latex/compile_latex.py document.tex -o output.pdf
   ```
2. If compiling remotely (e.g. Overleaf):
   - The generated `document.tex` and `assets/` directory are completely self-contained and ready to zip and upload.

---

### Phase 5: Visual QA & Comparison

To verify visual fidelity against the original PDF:
```bash
uv run python scripts/pdf_to_latex/diff_layout.py rendered_pages/page_1.png output.pdf --page 1 -o visual_diff_p1.png
```

---

## Detailed References

- [LaTeX Architecture & Preamble Specification](./references/latex_architecture_spec.md)
- [LaTeX Workflow Playbook & Decision Matrix](./references/workflow_playbook.md)
- [Math, Tables & Exam Formatting Guide](./references/math_and_tables_spec.md)

```

## Notes
Sequential single-agent workflow (no subagents). For Copilot compatibility.

## Relevant Python Code


### src\pdf_to_latex\__init__.py

```python
"""PDF to LaTeX conversion package.

Reuses the unified document extraction pipeline from pdf_to_docx and compiles
canonical AST specs into publication-grade LaTeX (.tex) and PDFs.
"""

from pdf_to_docx.ir_schema import (
    Alignment,
    BoundingBox,
    BoxBlock,
    ChartBlock,
    ChartSeries,
    ChartType,
    CodeBlock,
    DocumentBlock,
    DocumentClass,
    DocumentSpec,
    EquationBlock,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageBreakBlock,
    PageSpec,
    ParagraphBlock,
    QuestionBlock,
    QuestionChoice,
    TableBlock,
    TableCell,
    TextRun,
)
from pdf_to_docx.pdf_extractor import PDFExtractor
from pdf_to_docx.layout_parser import LayoutParser
from pdf_to_docx.chart_generator import render_chart_image

from .latex_compiler import LatexCompiler, compile_tex_to_pdf, escape_latex_text, find_latex_compiler
from .cli import main

__all__ = [
    "Alignment",
    "BoundingBox",
    "BoxBlock",
    "ChartBlock",
    "ChartSeries",
    "ChartType",
    "CodeBlock",
    "DocumentBlock",
    "DocumentClass",
    "DocumentSpec",
    "EquationBlock",
    "HeadingBlock",
    "ImageBlock",
    "LatexCompiler",
    "LayoutParser",
    "ListType",
    "PDFExtractor",
    "PageBreakBlock",
    "PageSpec",
    "ParagraphBlock",
    "QuestionBlock",
    "QuestionChoice",
    "TableBlock",
    "TableCell",
    "TextRun",
    "compile_tex_to_pdf",
    "escape_latex_text",
    "find_latex_compiler",
    "main",
    "render_chart_image",
]


```

### src\pdf_to_latex\latex_compiler.py

```python
"""Deterministic LaTeX Compiler.

Transforms a DocumentSpec AST into a production-grade, compilable LaTeX document (.tex)
and optionally invokes local LaTeX engines (pdflatex, xelatex, tectonic, latexmk)
to generate high-fidelity PDFs.
"""

from __future__ import annotations
import os
from pathlib import Path
import re
import shutil
import subprocess
from typing import Any, Dict, List, Optional, Tuple

from pdf_to_docx.ir_schema import (
    Alignment,
    BoundingBox,
    BoxBlock,
    ChartBlock,
    CodeBlock,
    DocumentBlock,
    DocumentClass,
    DocumentSpec,
    EquationBlock,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageBreakBlock,
    PageSpec,
    ParagraphBlock,
    QuestionBlock,
    QuestionChoice,
    TableBlock,
    TableCell,
    TextRun,
)


LATEX_SPECIAL_CHARS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex_text(text: str) -> str:
    """Escapes LaTeX special characters in text while preserving embedded math $...$ and \\(...\\)."""
    if not text:
        return ""

    # Split text into math segments and non-math segments
    # Matches $...$ or \(...\)
    pattern = re.compile(r"(\$(?:\\\$|[^$])+\$|\\\([^\)]+\\\))")
    parts = pattern.split(text)
    escaped_parts = []

    for part in parts:
        if (part.startswith("$") and part.endswith("$")) or (part.startswith(r"\(") and part.endswith(r"\)")):
            # Keep math intact
            escaped_parts.append(part)
        else:
            # Escape plain text
            out = part
            # Escape backslash first if not followed by special commands
            # Replace backslash with \textbackslash{}
            # But avoid breaking escaped characters if user already wrote \something
            out = re.sub(r"\\(?![$%&#_{}~^])", r"\\textbackslash{}", out)
            for char, replacement in LATEX_SPECIAL_CHARS.items():
                out = out.replace(char, replacement)
            escaped_parts.append(out)

    return "".join(escaped_parts)


def format_hex_color(hex_str: str) -> str:
    """Returns 6-digit hex uppercase without hash."""
    clean = hex_str.lstrip("#")
    if len(clean) == 3:
        clean = "".join([c * 2 for c in clean])
    return clean.upper()


class LatexCompiler:
    """Compiles a canonical DocumentSpec AST into formatted LaTeX (.tex) and PDF."""

    def __init__(self, spec: DocumentSpec):
        self.spec = spec
        self.doc_class = spec.document_class
        self.theme_color = format_hex_color(spec.theme_hex)

    def render_text_run(self, run: TextRun) -> str:
        """Renders an individual styled TextRun into LaTeX markup."""
        if run.is_math:
            content = run.text.strip()
            if not content.startswith("$") and not content.endswith("$"):
                return f"${content}$"
            return content

        txt = escape_latex_text(run.text)

        if run.code:
            txt = f"\\texttt{{{txt}}}"
        if run.bold and run.italic:
            txt = f"\\textbf{{\\textit{{{txt}}}}}"
        elif run.bold:
            txt = f"\\textbf{{{txt}}}"
        elif run.italic:
            txt = f"\\textit{{{txt}}}"
        if run.underline:
            txt = f"\\underline{{{txt}}}"
        if run.strike:
            txt = f"\\sout{{{txt}}}"
        if run.superscript:
            txt = f"\\textsuperscript{{{txt}}}"
        if run.subscript:
            txt = f"\\textsubscript{{{txt}}}"
        if run.color_hex:
            hex_code = format_hex_color(run.color_hex)
            txt = f"{{\\color[HTML]{{{hex_code}}}{txt}}}"

        return txt

    def render_paragraph_text(self, p: ParagraphBlock) -> str:
        """Renders paragraph runs into a concatenated string."""
        if not p.runs:
            return ""
        return "".join(self.render_text_run(run) for run in p.runs)

    def _render_preamble(self) -> str:
        """Generates document preamble based on document class and required packages."""
        lines = []

        if self.doc_class == DocumentClass.EXAM:
            lines.append(f"\\documentclass[{self.spec.font_size},addpoints]{{exam}}")
        elif self.doc_class == DocumentClass.SCRARTCL:
            lines.append(f"\\documentclass[{self.spec.font_size},{self.spec.paper_size}]{{scrartcl}}")
        elif self.doc_class == DocumentClass.REPORT:
            lines.append(f"\\documentclass[{self.spec.font_size},{self.spec.paper_size}]{{report}}")
        else:
            lines.append(f"\\documentclass[{self.spec.font_size},{self.spec.paper_size}]{{article}}")

        # Standard packages
        lines.extend([
            "% --- Core Typography & Geometry ---",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage[T1]{fontenc}",
            "\\usepackage{lmodern}",
            f"\\usepackage[{self.spec.paper_size},margin={self.spec.margins_in:.2f}in]{{geometry}}",
            "\\usepackage{microtype}",
            "",
            "% --- Math & Science ---",
            "\\usepackage{amsmath,amssymb,amsfonts,mathtools}",
            "\\usepackage{bm}",
            "",
            "% --- Tables & Graphics ---",
            "\\usepackage{graphicx}",
            "\\usepackage{booktabs}",
            "\\usepackage{tabularx}",
            "\\usepackage{multirow}",
            "\\usepackage{array}",
            "\\usepackage{colortbl}",
            "\\usepackage{caption}",
            "",
            "% --- Colors & Callout Boxes ---",
            "\\usepackage{xcolor}",
            "\\usepackage[most]{tcolorbox}",
            f"\\definecolor{{PrimaryColor}}{{HTML}}{{{self.theme_color}}}",
            "\\definecolor{CalloutBg}{HTML}{F4F6F9}",
            "\\definecolor{CalloutFrame}{HTML}{D0D7DE}",
            "",
            "% --- Lists & Formatting ---",
            "\\usepackage{enumitem}",
            "\\usepackage{ulem}",
            "\\normalem",
            "",
            "% --- Hyperlinks ---",
            "\\usepackage{hyperref}",
            "\\hypersetup{",
            "    colorlinks=true,",
            "    linkcolor=PrimaryColor,",
            "    filecolor=PrimaryColor,",
            "    urlcolor=PrimaryColor,",
            "    citecolor=PrimaryColor,",
            "}",
            "",
            "% --- Custom Environment Definitions ---",
            "\\newtcolorbox{calloutbox}[1][]{",
            "    colback=CalloutBg,",
            "    colframe=PrimaryColor,",
            "    boxrule=1.5pt,",
            "    arc=3pt,",
            "    left=10pt,right=10pt,top=8pt,bottom=8pt,",
            "    fonttitle=\\bfseries,",
            "    #1",
            "}",
            "\\newtcolorbox{responsebox}[1][]{",
            "    colback=white,",
            "    colframe=CalloutFrame,",
            "    boxrule=1pt,",
            "    arc=2pt,",
            "    left=8pt,right=8pt,top=8pt,bottom=8pt,",
            "    #1",
            "}",
        ])

        if self.doc_class == DocumentClass.EXAM:
            lines.extend([
                "",
                "% --- Exam Class Configurations ---",
                "\\pagestyle{headandfoot}",
                "\\firstpageheader{}{}{\\textbf{Name:} \\underline{\\hspace{2.5in}}}",
                "\\runningheader{" + escape_latex_text(self.spec.title) + "}{}{Page \\thepage\\ of \\numpages}",
                "\\firstpagefooter{}{}{}",
                "\\runningfooter{}{}{}",
                "\\pointsinrightmargin",
                "\\pointformat{\\textbf{[\\thepoints]}}",
            ])

        if self.spec.custom_preamble:
            lines.extend(["", "% --- User Custom Preamble ---", self.spec.custom_preamble])

        # Metadata
        lines.extend([
            "",
            f"\\title{{\\textbf{{{escape_latex_text(self.spec.title)}}}}}",
        ])
        if self.spec.author:
            lines.append(f"\\author{{{escape_latex_text(self.spec.author)}}}")
        if self.spec.date:
            lines.append(f"\\date{{{self.spec.date}}}")

        return "\n".join(lines)

    def _render_heading(self, block: HeadingBlock) -> str:
        text = escape_latex_text(block.text) if not block.runs else "".join(self.render_text_run(r) for r in block.runs)
        star = "" if block.numbered else "*"

        cmd = "\\section"
        if block.level == 2:
            cmd = "\\subsection"
        elif block.level == 3:
            cmd = "\\subsubsection"
        elif block.level == 4:
            cmd = "\\paragraph"

        res = f"{cmd}{star}{{{text}}}"
        if block.alignment == Alignment.CENTER:
            res = f"{{\\centering\n{res}\n\\par}}"
        return res

    def _render_paragraph(self, block: ParagraphBlock) -> str:
        text = self.render_paragraph_text(block)
        if not text.strip():
            return ""

        if block.is_callout:
            color = format_hex_color(block.callout_color_hex) if block.callout_color_hex else self.theme_color
            return f"\\begin{{calloutbox}}[colframe={color}]\n{text}\n\\end{{calloutbox}}"

        if block.alignment == Alignment.CENTER:
            return f"{{\\centering {text} \\par}}"
        elif block.alignment == Alignment.RIGHT:
            return f"{{\\raggedleft {text} \\par}}"
        elif block.alignment == Alignment.JUSTIFY:
            return f"{text}\n"
        return f"{text}\n"

    def _render_equation(self, block: EquationBlock) -> str:
        code = block.latex_code.strip()
        # Strip enclosing $$ or \[ \] if present
        if code.startswith("$$") and code.endswith("$$"):
            code = code[2:-2].strip()
        elif code.startswith(r"\[") and code.endswith(r"\]"):
            code = code[2:-2].strip()

        label_cmd = f"\\label{{{block.label}}}" if block.label else ""

        if block.numbered:
            return f"\\begin{{equation}}\n  {code}{label_cmd}\n\\end{{equation}}"
        else:
            return f"\\[\n  {code}\n\\]"

    def _render_table(self, block: TableBlock) -> str:
        num_cols = len(block.headers) if block.headers else (len(block.rows[0]) if block.rows else 0)
        if num_cols == 0:
            return ""

        # Determine column alignments
        col_specs = []
        for i in range(num_cols):
            if block.col_alignments and i < len(block.col_alignments):
                align = block.col_alignments[i]
                col_specs.append("c" if align == Alignment.CENTER else ("r" if align == Alignment.RIGHT else "l"))
            else:
                col_specs.append("l")

        if block.full_width:
            col_def = " ".join(["X" if c == "l" else c for c in col_specs])
            env_start = f"\\begin{{tabularx}}{{\\linewidth}}{{{col_def}}}"
            env_end = "\\end{tabularx}"
        else:
            col_def = " ".join(col_specs)
            env_start = f"\\begin{{tabular}}{{{col_def}}}"
            env_end = "\\end{tabular}"

        lines = ["\\begin{table}[htbp]", "\\centering"]
        if block.caption:
            lines.append(f"\\caption{{{escape_latex_text(block.caption)}}}")
        lines.append(env_start)

        if block.booktabs:
            lines.append("  \\toprule")
        else:
            lines.append("  \\hline")

        # Headers
        if block.header_cells:
            h_items = []
            for cell in block.header_cells:
                ct = cell.text if not cell.runs else "".join(self.render_text_run(r) for r in cell.runs)
                h_items.append(f"\\textbf{{{escape_latex_text(ct)}}}")
            lines.append("  " + " & ".join(h_items) + " \\\\")
            if block.booktabs:
                lines.append("  \\midrule")
            else:
                lines.append("  \\hline")
        elif block.headers:
            h_items = [f"\\textbf{{{escape_latex_text(h)}}}" for h in block.headers]
            lines.append("  " + " & ".join(h_items) + " \\\\")
            if block.booktabs:
                lines.append("  \\midrule")
            else:
                lines.append("  \\hline")

        # Rows
        if block.row_cells:
            for row in block.row_cells:
                r_items = []
                for cell in row:
                    ct = cell.text if not cell.runs else "".join(self.render_text_run(r) for r in cell.runs)
                    r_txt = escape_latex_text(ct)
                    if cell.bold:
                        r_txt = f"\\textbf{{{r_txt}}}"
                    if cell.italic:
                        r_txt = f"\\textit{{{r_txt}}}"
                    r_items.append(r_txt)
                lines.append("  " + " & ".join(r_items) + " \\\\")
        elif block.rows:
            for row in block.rows:
                r_items = [escape_latex_text(str(cell)) for cell in row]
                lines.append("  " + " & ".join(r_items) + " \\\\")

        if block.booktabs:
            lines.append("  \\bottomrule")
        else:
            lines.append("  \\hline")

        lines.append(env_end)
        lines.append("\\end{table}")
        return "\n".join(lines)

    def _render_image(self, block: ImageBlock, assets_dir: Path) -> str:
        img_path = block.image_path.replace("\\", "/")
        lines = ["\\begin{figure}[htbp]", "\\centering"]
        lines.append(f"\\includegraphics[width={block.width_ratio:.2f}\\linewidth]{{{img_path}}}")
        if block.caption:
            lines.append(f"\\caption{{{escape_latex_text(block.caption)}}}")
        if block.label:
            lines.append(f"\\label{{{block.label}}}")
        lines.append("\\end{figure}")
        return "\n".join(lines)

    def _render_chart(self, block: ChartBlock, assets_dir: Path) -> str:
        # If chart has a rendered image, include it as figure
        chart_img = block.generated_image_path
        if not chart_img or not Path(chart_img).exists():
            from pdf_to_docx.chart_generator import render_chart_image
            chart_filename = f"chart_{abs(hash(block.title)) % 100000}.png"
            chart_img = str((assets_dir / chart_filename).resolve())
            render_chart_image(block, chart_img)

        chart_path = chart_img.replace("\\", "/")
        lines = ["\\begin{figure}[htbp]", "\\centering"]
        lines.append(f"\\includegraphics[width=0.85\\linewidth]{{{chart_path}}}")
        caption = block.caption or block.title
        lines.append(f"\\caption{{{escape_latex_text(caption)}}}")
        lines.append("\\end{figure}")
        return "\n".join(lines)

    def _render_box(self, block: BoxBlock) -> str:
        color = format_hex_color(block.color_hex)
        options = []
        if block.title:
            options.append(f"title={{{escape_latex_text(block.title)}}}")
        if block.height_pt:
            options.append(f"height={block.height_pt:.1f}pt")
        if block.empty_for_response:
            options.append("colback=white,colframe=CalloutFrame")
        else:
            options.append(f"colframe={color}")

        opt_str = f"[{', '.join(options)}]" if options else ""
        lines = [f"\\begin{{tcolorbox}}{opt_str}"]
        for p in block.content:
            rendered_p = self._render_paragraph(p)
            if rendered_p:
                lines.append(rendered_p)
        lines.append("\\end{tcolorbox}")
        return "\n".join(lines)

    def _render_question(self, block: QuestionBlock) -> str:
        lines = []
        pts_str = f"[{block.points}]" if block.points else ""

        if self.doc_class == DocumentClass.EXAM:
            if block.part:
                lines.append(f"\\part{pts_str}")
            else:
                lines.append(f"\\question{pts_str}")

            for p in block.prompt:
                lines.append(self._render_paragraph(p))

            if block.choices:
                lines.append("\\begin{choices}")
                for choice in block.choices:
                    c_text = choice.text if not choice.runs else "".join(self.render_text_run(r) for r in choice.runs)
                    lines.append(f"  \\choice {escape_latex_text(c_text)}")
                lines.append("\\end{choices}")

            if block.response_box_height_pt:
                lines.append(f"\\makeemptybox{{{block.response_box_height_pt:.1f}pt}}")
        else:
            # Render question nicely in article or report class
            q_num_str = f"Question {block.number}" if block.number else "Problem"
            if block.part:
                q_num_str += f" ({block.part})"
            if block.points:
                q_num_str += f" [{block.points} pts]"

            lines.append(f"\\paragraph{{{q_num_str}}}")
            for p in block.prompt:
                lines.append(self._render_paragraph(p))

            if block.choices:
                lines.append("\\begin{enumerate}[label=(\\Alph*)]")
                for choice in block.choices:
                    c_text = choice.text if not choice.runs else "".join(self.render_text_run(r) for r in choice.runs)
                    lines.append(f"  \\item {escape_latex_text(c_text)}")
                lines.append("\\end{enumerate}")

            if block.response_box_height_pt:
                lines.append(f"\\begin{{responsebox}}[height={block.response_box_height_pt:.1f}pt]\n\\end{{responsebox}}")

        return "\n".join(lines)

    def _render_code(self, block: CodeBlock) -> str:
        lines = ["\\begin{verbatim}", block.code.strip(), "\\end{verbatim}"]
        return "\n".join(lines)

    def render_block(self, block: DocumentBlock, assets_dir: Path) -> str:
        """Renders any DocumentBlock variant into LaTeX string."""
        b_type = getattr(block, "type", "")
        if b_type == "heading":
            return self._render_heading(block)  # type: ignore
        elif b_type == "paragraph":
            return self._render_paragraph(block)  # type: ignore
        elif b_type == "equation":
            return self._render_equation(block)  # type: ignore
        elif b_type == "table":
            return self._render_table(block)  # type: ignore
        elif b_type == "image":
            return self._render_image(block, assets_dir)  # type: ignore
        elif b_type == "chart":
            return self._render_chart(block, assets_dir)  # type: ignore
        elif b_type == "box":
            return self._render_box(block)  # type: ignore
        elif b_type == "question":
            return self._render_question(block)  # type: ignore
        elif b_type == "code":
            return self._render_code(block)  # type: ignore
        elif b_type == "page_break":
            return "\\newpage"
        return ""

    def generate_latex_code(self, assets_dir: Optional[Path] = None) -> str:
        """Generates the full complete LaTeX document (.tex) as a string."""
        if assets_dir is None:
            assets_dir = Path("./assets")

        preamble = self._render_preamble()
        body_parts = ["\\begin{document}"]

        # Title for article/report/scrartcl
        if self.doc_class != DocumentClass.EXAM:
            body_parts.append("\\maketitle")
            body_parts.append("")

        exam_questions_open = False

        for page_idx, page in enumerate(self.spec.pages):
            if page_idx > 0:
                body_parts.append("\\newpage")
                body_parts.append(f"% --- Page {page.page_number} ---")

            for block in page.blocks:
                b_type = getattr(block, "type", "")

                # Handle question block environment wrapping for exam class
                if self.doc_class == DocumentClass.EXAM:
                    if b_type == "question" and not exam_questions_open:
                        body_parts.append("\\begin{questions}")
                        exam_questions_open = True
                    elif b_type != "question" and exam_questions_open:
                        body_parts.append("\\end{questions}")
                        exam_questions_open = False

                rendered = self.render_block(block, assets_dir)
                if rendered:
                    body_parts.append(rendered)
                    body_parts.append("")

        if exam_questions_open:
            body_parts.append("\\end{questions}")

        body_parts.append("\\end{document}")

        return preamble + "\n\n" + "\n".join(body_parts) + "\n"

    def compile(self, output_tex_path: str | Path, assets_dir: Optional[str | Path] = None) -> Path:
        """Writes the generated LaTeX code to disk."""
        out_path = Path(output_tex_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        assets_path = Path(assets_dir) if assets_dir else out_path.parent / "assets"
        assets_path.mkdir(parents=True, exist_ok=True)

        tex_code = self.generate_latex_code(assets_path)
        out_path.write_text(tex_code, encoding="utf-8")
        return out_path


def find_latex_compiler() -> Optional[str]:
    """Detects available LaTeX engine on system PATH."""
    engines = ["latexmk", "tectonic", "xelatex", "pdflatex", "lualatex"]
    for eng in engines:
        if shutil.which(eng):
            return eng
    return None


def compile_tex_to_pdf(tex_path: str | Path, output_pdf: Optional[str | Path] = None) -> Tuple[bool, str]:
    """Compiles a .tex file into .pdf using the best available LaTeX engine."""
    tex_p = Path(tex_path).resolve()
    if not tex_p.exists():
        return False, f"File not found: {tex_p}"

    engine = find_latex_compiler()
    if not engine:
        return False, "No LaTeX compiler found (checked latexmk, tectonic, xelatex, pdflatex, lualatex). The .tex file is ready for Overleaf or compilation on a machine with LaTeX."

    cwd = tex_p.parent
    try:
        if engine == "latexmk":
            cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", tex_p.name]
            res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
        elif engine == "tectonic":
            cmd = ["tectonic", tex_p.name]
            res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=120)
        else:
            # Run twice for cross-references
            cmd = [engine, "-interaction=nonstopmode", tex_p.name]
            subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=90)
            res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=90)

        expected_pdf = tex_p.with_suffix(".pdf")
        if expected_pdf.exists():
            if output_pdf:
                out_p = Path(output_pdf)
                shutil.copy2(expected_pdf, out_p)
                return True, f"Successfully compiled {out_p} using {engine}"
            return True, f"Successfully compiled {expected_pdf} using {engine}"
        else:
            return False, f"Compilation failed with {engine}. Log:\n{res.stdout[-1500:]}\n{res.stderr[-1000:]}"
    except Exception as e:
        return False, f"Error compiling LaTeX with {engine}: {e}"

```

### src\pdf_to_latex\cli.py

```python
"""Command-line interface for PDF to LaTeX conversion."""

from __future__ import annotations
import json
from pathlib import Path
import re
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table

from pdf_to_docx.ir_schema import DocumentClass, DocumentSpec, PageSpec
from pdf_to_docx.pdf_extractor import PDFExtractor
from pdf_to_docx.layout_parser import LayoutParser
from .latex_compiler import LatexCompiler, compile_tex_to_pdf, find_latex_compiler

app = typer.Typer(help="Autonomous, high-fidelity PDF to LaTeX (.tex) and PDF converter.")
console = Console()


@app.command()
def info(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
):
    """Inspects PDF structure, dimensions, fonts, and visual elements."""
    with PDFExtractor(pdf_path) as extractor:
        doc_info = extractor.get_document_info()

    console.print(f"[bold cyan]Document:[/] {doc_info['title']} ({doc_info['page_count']} pages)")
    table = Table(title="Pages Overview")
    table.add_column("Page #", justify="center")
    table.add_column("Dimensions (pt)")
    table.add_column("Orientation")
    table.add_column("Images", justify="right")
    table.add_column("Drawings", justify="right")

    for p in doc_info["pages"]:
        table.add_row(
            str(p["page_number"]),
            f"{p['width_pt']:.1f} x {p['height_pt']:.1f}",
            p["orientation"],
            str(p["image_count"]),
            str(p["drawings_count"]),
        )
    console.print(table)

    compiler = find_latex_compiler()
    if compiler:
        console.print(f"[green]Detected local LaTeX compiler:[/] [bold]{compiler}[/]")
    else:
        console.print("[dim yellow]No local LaTeX compiler detected (pdflatex, xelatex, tectonic). Generated .tex files will be ready for Overleaf or remote compilation.[/]")


@app.command()
def render_pages(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_dir: Optional[Path] = typer.Option(None, "--output-dir", "-o", help="Output directory for rendered PNGs"),
    dpi: int = typer.Option(200, "--dpi", help="Rendering resolution"),
):
    """Renders all PDF pages to high-resolution PNG images."""
    target_dir = output_dir or (Path("./rendered_pages") / pdf_path.stem)
    with PDFExtractor(pdf_path) as extractor:
        paths = extractor.render_all_pages(target_dir, dpi=dpi)
    console.print(f"[green]Successfully rendered {len(paths)} pages to {target_dir}[/]")


@app.command()
def crop(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(1, "--page", "-p", help="Page number (1-indexed)"),
    bbox: str = typer.Option(..., "--bbox", help="Normalized bbox as 'ymin,xmin,ymax,xmax' (0-1000)"),
    output_path: Path = typer.Option(Path("cropped_asset.png"), "--output", "-o"),
    dpi: int = typer.Option(300, "--dpi"),
):
    """Crops a specific bounding box region from a PDF page for \\includegraphics."""
    coords = [int(x.strip()) for x in bbox.split(",")]
    if len(coords) != 4:
        raise typer.BadParameter("BBox must have 4 comma-separated integers: ymin,xmin,ymax,xmax")

    with PDFExtractor(pdf_path) as extractor:
        out = extractor.extract_region(page, coords, output_path=output_path, dpi=dpi)
    console.print(f"[green]Cropped region saved to {out}[/]")


@app.command()
def parse_page(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(..., "--page", "-p", help="Page number (1-indexed)"),
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="Path to pre-rendered page PNG"),
    output_spec: Path = typer.Option(..., "--output", "-o", help="Output PageSpec JSON path"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Directory for cropped assets"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution if rendering"),
):
    """Parses a single PDF page into a PageSpec JSON and crops assets (designed for page subagents)."""
    resolved_assets = assets_dir or (output_spec.parent / "assets")
    resolved_assets.mkdir(parents=True, exist_ok=True)
    output_spec.parent.mkdir(parents=True, exist_ok=True)

    with PDFExtractor(pdf_path) as extractor:
        if image and image.exists():
            page_png = image
        else:
            temp_dir = output_spec.parent / ".temp_renders"
            temp_dir.mkdir(parents=True, exist_ok=True)
            page_png = extractor.render_page_to_png(page, temp_dir / f"orig_p{page}.png", dpi=dpi)

        console.print(f"[cyan]Parsing layout structure for page {page}...[/]")
        parser = LayoutParser()
        page_spec = parser.parse_page_image(page_png, page_number=page)

        # Crop any image/figure blocks flagged with bbox
        for b_idx, block in enumerate(page_spec.blocks):
            if getattr(block, "type", "") == "image" and block.bbox:  # type: ignore
                crop_dest = resolved_assets / f"p{page}_img{b_idx}.png"
                extractor.extract_region(
                    page,
                    [block.bbox.ymin, block.bbox.xmin, block.bbox.ymax, block.bbox.xmax],  # type: ignore
                    output_path=crop_dest,
                    dpi=300,
                )
                block.image_path = str(crop_dest)  # type: ignore

    output_spec.write_text(page_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]Page {page} AST saved to:[/] {output_spec}")


@app.command()
def to_latex_page(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(..., "--page", "-p", help="Page number (1-indexed)"),
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="Path to pre-rendered page PNG"),
    output_tex: Path = typer.Option(..., "--output", "-o", help="Output LaTeX fragment path"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution if rendering"),
):
    """Fast-track: Converts a single page directly into a LaTeX fragment (.tex) (designed for page subagents)."""
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    with PDFExtractor(pdf_path) as extractor:
        if image and image.exists():
            page_png = image
        else:
            temp_dir = output_tex.parent / ".temp_renders"
            temp_dir.mkdir(parents=True, exist_ok=True)
            page_png = extractor.render_page_to_png(page, temp_dir / f"p{page}.png", dpi=dpi)

        console.print(f"Parsing page {page} directly into LaTeX fragment...")
        parser = LayoutParser()
        tex_fragment = parser.parse_latex_fast_path(page_png, page_number=page)
        output_tex.write_text(f"% --- Page {page} ---\n{tex_fragment}\n", encoding="utf-8")
    console.print(f"[bold green]Page {page} LaTeX fragment saved to:[/] {output_tex}")


@app.command()
def compile_pages(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*_spec.json files"),
    output_tex: Path = typer.Option(Path("document.tex"), "--output", "-o", help="Output LaTeX file (.tex)"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    author: Optional[str] = typer.Option(None, "--author"),
    doc_class: DocumentClass = typer.Option(DocumentClass.ARTICLE, "--doc-class", "-c", help="Document class (article, report, exam, scrartcl)"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex", help="Primary theme color hex"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
    compile_pdf: bool = typer.Option(False, "--pdf", help="Also compile generated .tex into .pdf"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save the merged DocumentSpec AST JSON alongside the exported file"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path to save the DocumentSpec AST JSON"),
):
    """Compiles multiple PageSpec JSON files from a workspace into a production-grade LaTeX file and PDF."""
    if pages_dir.is_dir():
        spec_files = sorted(
            [f for f in pages_dir.glob("page_*_spec.json") if not f.name.endswith("_merged_ast.json")],
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
        if not spec_files:
            spec_files = sorted(
                [f for f in pages_dir.glob("*.json") if not f.name.endswith("_merged_ast.json") and not f.name.endswith("_ast.json")],
                key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
            )
    elif pages_dir.is_file():
        spec_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not spec_files:
        raise typer.BadParameter(f"No PageSpec JSON files found in {pages_dir}")

    console.print(f"[cyan]Found {len(spec_files)} page spec(s) to compile in order:[/]")
    for sf in spec_files:
        console.print(f"  - {sf.name}")

    pages = []
    for f in spec_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        pages.append(PageSpec.model_validate(data))

    doc_spec = DocumentSpec(
        title=title,
        author=author,
        document_class=doc_class,
        theme_hex=theme_hex,
        pages=pages,
    )

    if save_ast or ast_path is not None:
        target_ast = ast_path or (output_tex.parent / f"{output_tex.stem}_ast.json")
        target_ast.parent.mkdir(parents=True, exist_ok=True)
        target_ast.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[dim]DocumentSpec AST saved to: {target_ast}[/]")

    # Resolve assets directory if not provided
    resolved_assets = assets_dir
    if resolved_assets is None and pages_dir.is_dir() and (pages_dir / "assets").exists():
        resolved_assets = pages_dir / "assets"

    compiler = LatexCompiler(doc_spec)
    out = compiler.compile(output_tex, assets_dir=resolved_assets)
    console.print(f"[bold green]Successfully compiled {len(pages)} pages to LaTeX:[/] {out}")

    if compile_pdf:
        console.print("[cyan]Attempting to compile LaTeX to PDF...[/]")
        pdf_target = output_tex.with_suffix(".pdf")
        success, msg = compile_tex_to_pdf(out, pdf_target)
        if success:
            console.print(f"[bold green]{msg}[/]")
        else:
            console.print(f"[yellow]{msg}[/]")


@app.command()
def merge_latex(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*.tex fragment files"),
    output_tex: Path = typer.Option(Path("document.tex"), "--output", "-o", help="Output merged LaTeX document"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    author: Optional[str] = typer.Option(None, "--author"),
    doc_class: DocumentClass = typer.Option(DocumentClass.ARTICLE, "--doc-class", "-c"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex"),
    compile_pdf: bool = typer.Option(False, "--pdf", help="Also compile generated .tex into .pdf"),
):
    """Merges individual page_*.tex fragment files into a master compilable LaTeX document with preamble."""
    if pages_dir.is_dir():
        tex_files = sorted(
            pages_dir.glob("page_*.tex"),
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
    elif pages_dir.is_file():
        tex_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not tex_files:
        raise typer.BadParameter(f"No LaTeX fragment files found in {pages_dir}")

    dummy_spec = DocumentSpec(
        title=title,
        author=author,
        document_class=doc_class,
        theme_hex=theme_hex,
        pages=[],
    )
    compiler = LatexCompiler(dummy_spec)
    preamble = compiler._render_preamble()

    body_lines = ["\\begin{document}"]
    if doc_class != DocumentClass.EXAM:
        body_lines.append("\\maketitle\n")

    for idx, tf in enumerate(tex_files):
        if idx > 0:
            body_lines.append("\\newpage")
        body_lines.append(tf.read_text(encoding="utf-8").strip())
        body_lines.append("")

    body_lines.append("\\end{document}")

    full_tex = preamble + "\n\n" + "\n".join(body_lines) + "\n"
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_tex.write_text(full_tex, encoding="utf-8")
    console.print(f"[bold green]Successfully assembled {len(tex_files)} pages into:[/] {output_tex}")

    if compile_pdf:
        console.print("[cyan]Attempting to compile LaTeX to PDF...[/]")
        pdf_target = output_tex.with_suffix(".pdf")
        success, msg = compile_tex_to_pdf(output_tex, pdf_target)
        if success:
            console.print(f"[bold green]{msg}[/]")
        else:
            console.print(f"[yellow]{msg}[/]")


@app.command()
def compile_pdf(
    tex_path: Path = typer.Argument(..., help="Path to input .tex file"),
    output_pdf: Optional[Path] = typer.Option(None, "--output", "-o", help="Output PDF destination"),
):
    """Compiles an existing .tex file to PDF using local LaTeX engine (pdflatex, xelatex, tectonic, latexmk)."""
    success, msg = compile_tex_to_pdf(tex_path, output_pdf)
    if success:
        console.print(f"[bold green]{msg}[/]")
    else:
        console.print(f"[bold red]{msg}[/]")
        raise typer.Exit(code=1)


@app.command()
def convert(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_tex: Path = typer.Option(Path("document.tex"), "--output", "-o"),
    workspace_dir: Optional[Path] = typer.Option(None, "--workspace-dir", "-w", help="Independent temp workspace directory for this conversion"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory for cropped images and charts"),
    doc_class: DocumentClass = typer.Option(DocumentClass.ARTICLE, "--doc-class", "-c"),
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution"),
    compile_pdf: bool = typer.Option(False, "--pdf", help="Also compile generated .tex into .pdf"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save the DocumentSpec AST JSON alongside the exported file"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path to save the DocumentSpec AST JSON"),
):
    """Executes full autonomous conversion pipeline from PDF to LaTeX."""
    console.print(f"[bold cyan]Starting LaTeX conversion:[/] {pdf_path}")
    target_stem = output_tex.stem if output_tex.name != "document.tex" else pdf_path.stem
    if workspace_dir is not None:
        temp_dir = Path(workspace_dir)
    elif output_tex.parent.name == target_stem or output_tex.parent.name == pdf_path.stem:
        temp_dir = output_tex.parent / "workspace"
    else:
        temp_dir = output_tex.parent / f".workspace_{target_stem}"

    if assets_dir is not None:
        assets_path = Path(assets_dir)
    elif output_tex.parent.name == target_stem or output_tex.parent.name == pdf_path.stem:
        assets_path = output_tex.parent / "assets"
    else:
        assets_path = temp_dir / "assets"

    temp_dir.mkdir(parents=True, exist_ok=True)
    assets_path.mkdir(parents=True, exist_ok=True)

    with PDFExtractor(pdf_path) as extractor:
        doc_info = extractor.get_document_info()
        doc_title = title or doc_info["title"]
        doc_spec = DocumentSpec(title=doc_title, document_class=doc_class)
        parser = LayoutParser()

        for p_info in doc_info["pages"]:
            p_num = p_info["page_number"]
            console.print(f"[cyan]Rendering page {p_num}/{doc_info['page_count']}...[/]")
            page_png = extractor.render_page_to_png(p_num, temp_dir / f"orig_p{p_num}.png", dpi=dpi)

            console.print(f"[cyan]Parsing layout structure for page {p_num}...[/]")
            page_spec = parser.parse_page_image(page_png, page_number=p_num)

            # Crop any image/figure blocks flagged with bbox
            for b_idx, block in enumerate(page_spec.blocks):
                if getattr(block, "type", "") == "image" and block.bbox:  # type: ignore
                    crop_dest = assets_path / f"p{p_num}_img{b_idx}.png"
                    extractor.extract_region(
                        p_num,
                        [block.bbox.ymin, block.bbox.xmin, block.bbox.ymax, block.bbox.xmax],  # type: ignore
                        output_path=crop_dest,
                        dpi=300,
                    )
                    block.image_path = str(crop_dest)  # type: ignore

            doc_spec.pages.append(page_spec)

    # Save AST JSON if requested
    if save_ast or ast_path is not None:
        target_ast = ast_path or (output_tex.parent / f"{output_tex.stem}_ast.json")
        target_ast.parent.mkdir(parents=True, exist_ok=True)
        target_ast.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
        console.print(f"[dim]Intermediate Representation AST saved to: {target_ast}[/]")

    # Compile to LaTeX
    console.print("[cyan]Compiling AST into LaTeX (.tex)...[/]")
    compiler = LatexCompiler(doc_spec)
    compiler.compile(output_tex, assets_dir=assets_path)
    console.print(f"[bold green]Successfully created LaTeX document:[/] {output_tex}")

    if compile_pdf:
        console.print("[cyan]Attempting to compile LaTeX to PDF...[/]")
        pdf_target = output_tex.with_suffix(".pdf")
        success, msg = compile_tex_to_pdf(output_tex, pdf_target)
        if success:
            console.print(f"[bold green]{msg}[/]")
        else:
            console.print(f"[yellow]{msg}[/]")


def main():
    app()


if __name__ == "__main__":
    main()

```

### src\pdf_to_docx\ir_schema.py

```python
"""Unified Intermediate Representation (IR) Schema for Document Conversion.

Defines the strongly-typed Abstract Syntax Tree (AST) representing a document.
Extracted once from the input PDF by multimodal page subagents, this canonical
format is deterministically compiled into either:
  1. Professional Word documents (.docx) via DocxCompiler
  2. Publication-grade LaTeX documents (.tex / .pdf) via LatexCompiler
"""

from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class DocumentClass(str, Enum):
    ARTICLE = "article"
    REPORT = "report"
    EXAM = "exam"
    SCRARTCL = "scrartcl"


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class ListType(str, Enum):
    BULLET = "bullet"
    NUMBERED = "numbered"
    DESCRIPTION = "description"
    NONE = "none"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"


class TextRun(BaseModel):
    """A styled fragment of text within a paragraph, table cell, or callout box."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    color_hex: Optional[str] = None  # e.g., "#1F4E79"
    font_size_pt: Optional[float] = None
    font_name: Optional[str] = None
    superscript: bool = False
    subscript: bool = False
    code: bool = False
    is_math: bool = False  # True for raw mathematical formulas (e.g. \frac{a}{b}, x_i)


class BoundingBox(BaseModel):
    """Normalized bounding box coordinates on a 0-1000 scale [ymin, xmin, ymax, xmax]."""
    ymin: int = Field(..., ge=0, le=1000)
    xmin: int = Field(..., ge=0, le=1000)
    ymax: int = Field(..., ge=0, le=1000)
    xmax: int = Field(..., ge=0, le=1000)

    @property
    def height_ratio(self) -> float:
        return (self.ymax - self.ymin) / 1000.0

    @property
    def width_ratio(self) -> float:
        return (self.xmax - self.xmin) / 1000.0


class HeadingBlock(BaseModel):
    """Section heading with hierarchical level."""
    type: str = "heading"
    level: int = Field(1, ge=1, le=4)
    text: str
    runs: Optional[List[TextRun]] = None
    alignment: Alignment = Alignment.LEFT
    numbered: bool = True
    bbox: Optional[BoundingBox] = None


class ParagraphBlock(BaseModel):
    """Narrative text block with optional runs, list formatting, and callout styling."""
    type: str = "paragraph"
    runs: List[TextRun] = Field(default_factory=list)
    alignment: Alignment = Alignment.LEFT
    list_type: ListType = ListType.NONE
    list_level: int = 0
    is_callout: bool = False
    callout_color_hex: Optional[str] = None
    line_spacing: Optional[float] = None
    space_before_pt: Optional[float] = None
    space_after_pt: Optional[float] = None
    bbox: Optional[BoundingBox] = None


class EquationBlock(BaseModel):
    """Dedicated mathematical display equation block."""
    type: str = "equation"
    latex_code: str  # Raw LaTeX math without outer delimiters, e.g. "z = \frac{x - \mu}{\sigma}"
    numbered: bool = False
    label: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class TableCell(BaseModel):
    """A single cell inside a table."""
    text: str = ""
    runs: Optional[List[TextRun]] = None
    bg_color_hex: Optional[str] = None
    bold: bool = False
    italic: bool = False
    alignment: Alignment = Alignment.LEFT
    col_span: int = 1
    row_span: int = 1


class TableBlock(BaseModel):
    """Structured table block."""
    type: str = "table"
    caption: Optional[str] = None
    headers: List[str] = Field(default_factory=list)
    header_cells: Optional[List[TableCell]] = None
    rows: List[List[str]] = Field(default_factory=list)
    row_cells: Optional[List[List[TableCell]]] = None
    col_alignments: Optional[List[Alignment]] = None
    col_widths_pct: Optional[List[float]] = None  # e.g. [30.0, 35.0, 35.0]
    cant_split: bool = True  # Prevent row break across page boundaries (Word)
    repeat_header: bool = True  # Repeat header row if table crosses page
    style_name: Optional[str] = "Table Grid"
    booktabs: bool = True  # Professional table styling (LaTeX)
    full_width: bool = False
    bbox: Optional[BoundingBox] = None


class ChartSeries(BaseModel):
    name: str
    values: List[float]


class ChartBlock(BaseModel):
    """Chart or data visualization."""
    type: str = "chart"
    title: str
    chart_type: ChartType = ChartType.BAR
    categories: List[str] = Field(default_factory=list)
    series: List[ChartSeries] = Field(default_factory=list)
    reproduce_programmatically: bool = True
    generated_image_path: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    width_inches: float = 5.5
    height_inches: float = 3.5
    caption: Optional[str] = None


class ImageBlock(BaseModel):
    """Raster image or vector drawing extracted from PDF."""
    type: str = "image"
    image_path: str = ""
    caption: Optional[str] = None
    label: Optional[str] = None
    alt_text: Optional[str] = None
    width_inches: float = 5.5
    height_inches: Optional[float] = None
    width_ratio: float = 0.8
    alignment: Alignment = Alignment.CENTER
    bbox: Optional[BoundingBox] = None
    is_vector: bool = False


class BoxBlock(BaseModel):
    """Framed callout or response box (tcolorbox in LaTeX / shaded frame in Word)."""
    type: str = "box"
    title: Optional[str] = None
    content: List[ParagraphBlock] = Field(default_factory=list)
    color_hex: str = "#1F4E79"
    height_pt: Optional[float] = None
    empty_for_response: bool = False
    bbox: Optional[BoundingBox] = None


class QuestionChoice(BaseModel):
    """Multiple choice option."""
    label: str  # "(A)", "(B)", "(C)", etc.
    text: str
    runs: Optional[List[TextRun]] = None


class QuestionBlock(BaseModel):
    """Specialized block for exam / quiz problems."""
    type: str = "question"
    number: Optional[int] = None
    part: Optional[str] = None  # "a", "b", "c", etc.
    points: Optional[int] = None
    prompt: List[ParagraphBlock] = Field(default_factory=list)
    choices: Optional[List[QuestionChoice]] = None
    response_box_height_pt: Optional[float] = None
    solution: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class CodeBlock(BaseModel):
    """Verbatim or syntax-highlighted code block."""
    type: str = "code"
    language: Optional[str] = None
    code: str
    caption: Optional[str] = None


class PageBreakBlock(BaseModel):
    """Explicit page break."""
    type: str = "page_break"


DocumentBlock = Union[
    HeadingBlock,
    ParagraphBlock,
    EquationBlock,
    TableBlock,
    ChartBlock,
    ImageBlock,
    BoxBlock,
    QuestionBlock,
    CodeBlock,
    PageBreakBlock,
]


class PageSpec(BaseModel):
    """Specification for a single document page."""
    page_number: int
    width_pt: float = 612.0  # Standard letter (8.5 x 11 in points)
    height_pt: float = 792.0
    orientation: str = "portrait"  # portrait | landscape
    margin_top_pt: Optional[float] = None
    margin_bottom_pt: Optional[float] = None
    margin_left_pt: Optional[float] = None
    margin_right_pt: Optional[float] = None
    blocks: List[DocumentBlock] = Field(default_factory=list)


class DocumentSpec(BaseModel):
    """Root canonical representation of the entire document."""
    title: str = "Converted Document"
    author: Optional[str] = None
    company: Optional[str] = None
    date: Optional[str] = None
    document_class: DocumentClass = DocumentClass.ARTICLE
    font_size: str = "11pt"
    paper_size: str = "letterpaper"
    margins_in: float = 1.0
    theme_hex: str = "#1F4E79"
    default_font: str = "Calibri"
    default_font_size_pt: float = 11.0
    custom_preamble: Optional[str] = None
    pages: List[PageSpec] = Field(default_factory=list)


```

### src\pdf_to_docx\pdf_extractor.py

```python
"""PDF Extraction utilities powered by PyMuPDF (fitz).

Handles rendering pages to high-resolution images for vision analysis,
extracting embedded images, vector drawings, and cropping bounding-box regions.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import pymupdf as fitz


class PDFExtractor:
    """Extracts pages, text, and visual assets from PDF documents."""

    def __init__(self, pdf_path: str | Path):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {self.pdf_path}")
        self.doc = fitz.open(str(self.pdf_path))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        if self.doc:
            self.doc.close()

    @property
    def page_count(self) -> int:
        return len(self.doc)

    def get_document_info(self) -> Dict[str, Any]:
        """Returns document metadata and page geometry overview."""
        meta = self.doc.metadata or {}
        pages_summary = []
        for i, page in enumerate(self.doc):
            rect = page.rect
            pages_summary.append({
                "page_number": i + 1,
                "width_pt": rect.width,
                "height_pt": rect.height,
                "orientation": "landscape" if rect.width > rect.height else "portrait",
                "image_count": len(page.get_images()),
                "drawings_count": len(page.get_drawings()),
            })
        return {
            "title": meta.get("title") or self.pdf_path.stem,
            "author": meta.get("author"),
            "page_count": len(self.doc),
            "pages": pages_summary,
        }

    def render_page_to_png(
        self,
        page_number: int,
        output_path: Optional[str | Path] = None,
        dpi: int = 200,
    ) -> Path:
        """Renders a PDF page (1-indexed) as a high-resolution PNG image.

        Args:
            page_number: 1-indexed page number.
            output_path: Destination path for the PNG image.
            dpi: Rendering DPI (default 200 for Gemini multimodal analysis).
        """
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page number {page_number} out of range (1..{len(self.doc)})")

        page = self.doc[page_number - 1]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)

        if output_path is None:
            output_path = self.pdf_path.parent / f"{self.pdf_path.stem}_p{page_number}_{dpi}dpi.png"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(output_path))
        return output_path

    def render_all_pages(
        self,
        output_dir: str | Path,
        dpi: int = 200,
    ) -> List[Path]:
        """Renders all pages of the PDF to PNG images in output_dir."""
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        paths = []
        for i in range(1, len(self.doc) + 1):
            target = out_dir / f"page_{i}.png"
            paths.append(self.render_page_to_png(i, target, dpi=dpi))
        return paths

    def extract_region(
        self,
        page_number: int,
        bbox: List[int] | Tuple[int, int, int, int],  # [ymin, xmin, ymax, xmax] 0-1000
        output_path: Optional[str | Path] = None,
        dpi: int = 300,
        format: str = "png",
    ) -> Path:
        """Crops a normalized bounding box region from a page.

        Args:
            page_number: 1-indexed page number.
            bbox: [ymin, xmin, ymax, xmax] on a 0-1000 normalized scale.
            output_path: Path to save cropped asset.
            dpi: Rendering DPI for cropped raster image.
            format: 'png' or 'svg'.
        """
        page = self.doc[page_number - 1]
        rect = page.rect
        ymin, xmin, ymax, xmax = bbox

        # Convert normalized 0-1000 coords to PDF points
        x0 = (xmin / 1000.0) * rect.width
        y0 = (ymin / 1000.0) * rect.height
        x1 = (xmax / 1000.0) * rect.width
        y1 = (ymax / 1000.0) * rect.height

        clip_rect = fitz.Rect(x0, y0, x1, y1)

        if output_path is None:
            output_path = self.pdf_path.parent / f"crop_p{page_number}_{xmin}_{ymin}.{format}"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format.lower() == "svg":
            # Extract page SVG and clip
            svg_text = page.get_svg_image()
            # If full svg is extracted, save it (caller can handle clipping or PyMuPDF drawing paths)
            output_path.write_text(svg_text, encoding="utf-8")
        else:
            zoom = dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, clip=clip_rect, alpha=False)
            pix.save(str(output_path))

        return output_path

    def extract_text_spans(self, page_number: int) -> List[Dict[str, Any]]:
        """Extracts text spans with font size, bold/italic flags, and coordinates."""
        page = self.doc[page_number - 1]
        blocks = page.get_text("dict")["blocks"]
        spans_out = []
        rect = page.rect

        for b in blocks:
            if b.get("type") == 0:  # text block
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        text = span.get("text", "").strip()
                        if not text:
                            continue
                        s_bbox = span.get("bbox", [0, 0, 0, 0])
                        # Normalize to 0-1000
                        norm_bbox = [
                            int((s_bbox[1] / rect.height) * 1000),
                            int((s_bbox[0] / rect.width) * 1000),
                            int((s_bbox[3] / rect.height) * 1000),
                            int((s_bbox[2] / rect.width) * 1000),
                        ]
                        flags = span.get("flags", 0)
                        spans_out.append({
                            "text": text,
                            "size": span.get("size", 10),
                            "font": span.get("font", ""),
                            "bold": bool(flags & 2 or "bold" in span.get("font", "").lower()),
                            "italic": bool(flags & 1 or "italic" in span.get("font", "").lower()),
                            "color": f"#{span.get('color', 0):06x}",
                            "bbox": norm_bbox,
                        })
        return spans_out

    def get_page_typography(self, page_number: int) -> Dict[str, Any]:
        """Extracts exact page geometry, margins, and text spans from PDF content stream."""
        if page_number < 1 or page_number > len(self.doc):
            raise IndexError(f"Page {page_number} out of range (1..{len(self.doc)})")
        page = self.doc[page_number - 1]
        rect = page.rect
        text_page = page.get_text("dict")

        spans = []
        min_x, min_y = rect.width, rect.height
        max_x, max_y = 0.0, 0.0

        for block in text_page.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text:
                            continue
                        b = span["bbox"]
                        min_x = min(min_x, b[0])
                        min_y = min(min_y, b[1])
                        max_x = max(max_x, b[2])
                        max_y = max(max_y, b[3])
                        spans.append({
                            "text": text,
                            "font": span["font"],
                            "size": round(span["size"], 1),
                            "flags": span["flags"],
                            "color": f"#{span['color']:06x}" if span["color"] > 0 else None,
                            "bbox": b,
                        })

        margin_left = max(24.0, min_x) if min_x < rect.width else 36.0
        margin_top = max(18.0, min_y) if min_y < rect.height else 36.0
        margin_right = max(24.0, rect.width - max_x) if max_x > 0 else 36.0
        margin_bottom = max(18.0, rect.height - max_y) if max_y > 0 else 36.0

        return {
            "page_number": page_number,
            "width_pt": rect.width,
            "height_pt": rect.height,
            "margin_left_pt": round(margin_left, 1),
            "margin_top_pt": round(margin_top, 1),
            "margin_right_pt": round(margin_right, 1),
            "margin_bottom_pt": round(margin_bottom, 1),
            "spans": spans,
        }

```

### src\pdf_to_docx\layout_parser.py

```python
"""Unified Multimodal Layout Parser using Gemini 2.5 Flash.

Interprets rendered PDF page images, performs spatial layout decomposition,
and produces strongly-typed PageSpec / DocumentSpec AST instances.
Supports both Markdown fast-track (for DOCX) and LaTeX fragment fast-track (for LaTeX).
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from .ir_schema import (
    Alignment,
    BoundingBox,
    BoxBlock,
    ChartBlock,
    ChartSeries,
    ChartType,
    CodeBlock,
    DocumentBlock,
    DocumentSpec,
    EquationBlock,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageSpec,
    ParagraphBlock,
    QuestionBlock,
    QuestionChoice,
    TableBlock,
    TableCell,
    TextRun,
)


LAYOUT_EXTRACTION_PROMPT = """Analyze this document page image and output a precise structured JSON matching the PageSpec schema.

Guidelines:
1. Deconstruct the layout into logical blocks in reading order: headings, paragraphs, equations, tables, charts, images, boxes, or questions.
2. For HEADINGS: Identify hierarchical level (1-4), text, alignment, and bounding box [ymin, xmin, ymax, xmax] (0-1000 scale).
3. For PARAGRAPHS: Preserve typography (bold, italic, colors), detect if it's a bullet list or numbered list, and identify callouts/highlights.
4. For MATHEMATICAL FORMULAS & SYMBOLS:
   - Inline math: Set TextRun.is_math = true or enclose in $...$ (e.g. $z = \\frac{x - \\mu}{\\sigma}$, $\\bar{x}$, $\\sigma^2$, $\\hat{p}$).
   - Display equations: Use EquationBlock with latex_code.
   - Preserve all Greek letters, fractions, superscripts, subscripts, summations, integrals.
5. For EXAM & QUIZ QUESTIONS:
   - If this is an exam, test, or problem set, use QuestionBlock with number, points, prompt, multiple choice options, and response_box_height_pt.
6. For TABLES: Extract full tabular structure with headers and rows. Preserve exact mathematical symbols, numbers, and units.
7. For CHARTS: Identify chart type (bar, line, pie), extract the title, category labels, and series data values so it can be re-rendered programmatically. Also provide bbox.
8. For FIGURES / IMAGES / LOGOS / SIGNATURES: Provide bounding box [ymin, xmin, ymax, xmax] (0-1000 scale) so they can be cropped from the PDF.
9. For CALLOUT / FRAMED BOXES: Use BoxBlock with title and content.
10. Set page orientation to 'portrait' or 'landscape'.
"""


FAST_TRACK_LATEX_PROMPT = """Convert this document page image directly into a clean, modular LaTeX body fragment suitable for \\input{...}.

Formatting Rules:
1. Do NOT include \\documentclass, \\begin{document}, or preamble. Output ONLY the body content for this page.
2. Mathematics: Use proper LaTeX math environments ($...$ for inline, \\[...\\] or \\begin{equation} for display math, \\frac, \\sqrt, Greek letters, etc.).
3. Headings: Use \\section*, \\subsection*, \\subsubsection*.
4. Tables: Use clean booktabs formatting (\\begin{table}[htbp] \\centering \\begin{tabular}{...} \\toprule ... \\midrule ... \\bottomrule \\end{tabular} \\end{table}).
5. Exam / Quiz Questions: Format with \\paragraph{Question X} or \\question, multiple choices with enumerate or choices environment, and empty response boxes using \\begin{tcolorbox}[height=...cm] or \\makeemptybox{...}.
6. Figures / Diagrams: If there is a visual image or diagram, mark it as \\begin{figure}[htbp] \\centering \\includegraphics[width=0.8\\linewidth]{assets/p{PAGE}_asset.png} \\caption{...} \\end{figure}.
7. Do NOT include Markdown backticks (```latex) or conversational commentary.
"""


class LayoutParser:
    """Invokes Gemini Flash multimodal vision model to parse page layouts."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-flash-lite-latest"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self._client = None

    @property
    def client(self):
        if self._client is None:
            from google import genai
            import logging
            logging.getLogger("google_genai.models").addFilter(
                lambda record: "automatic function calling (AFC)" not in record.getMessage()
            )
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            else:
                self._client = genai.Client()
        return self._client

    def parse_page_image(self, image_path: str | Path, page_number: int = 1) -> PageSpec:
        """Parses a rendered page image using Gemini Flash into a unified PageSpec AST."""
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")

        img_bytes = img_path.read_bytes()

        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                LAYOUT_EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PageSpec,
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        try:
            parsed_json = json.loads(response.text)
            spec = PageSpec.model_validate(parsed_json)
            spec.page_number = page_number
            return spec
        except (json.JSONDecodeError, ValidationError) as e:
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()
            parsed_json = json.loads(raw_text)
            spec = PageSpec.model_validate(parsed_json)
            spec.page_number = page_number
            return spec

    def parse_markdown_fast_path(self, image_path: str | Path) -> str:
        """Fast-track parsing: Converts a page image directly into GitHub-Flavored Markdown (for Word)."""
        img_path = Path(image_path)
        img_bytes = img_path.read_bytes()

        from google.genai import types

        prompt = (
            "Convert this document page into clean GitHub-Flavored Markdown (GFM). "
            "Preserve all headings (#, ##), bold, italics, bullet lists, numbered lists, "
            "and standard markdown tables (| Header | ... |). Do not include conversational text or enclosing ```markdown blocks."
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        return response.text.strip()

    def parse_latex_fast_path(self, image_path: str | Path, page_number: int = 1) -> str:
        """Fast-track parsing: Converts a page image directly into a LaTeX fragment (.tex)."""
        img_path = Path(image_path)
        img_bytes = img_path.read_bytes()

        from google.genai import types

        prompt = FAST_TRACK_LATEX_PROMPT.replace("{PAGE}", str(page_number))

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        text = response.text.strip()
        if text.startswith("```latex"):
            text = text.split("```latex", 1)[1].split("```", 1)[0].strip()
        elif text.startswith("```tex"):
            text = text.split("```tex", 1)[1].split("```", 1)[0].strip()
        elif text.startswith("```"):
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        return text


```

### .agents\skills\pdf-to-latex\scripts\inspect_pdf.py

_File not found in repo._

### .agents\skills\pdf-to-latex\scripts\render_pages.py

_File not found in repo._

### .agents\skills\pdf-to-latex\scripts\crop_asset.py

_File not found in repo._

### .agents\skills\pdf-to-latex\scripts\compile_latex.py

_File not found in repo._

### .agents\skills\pdf-to-latex\scripts\compile_pages.py

_File not found in repo._

### .agents\skills\pdf-to-latex\scripts\convert.py

_File not found in repo._

### .agents\skills\pdf-to-latex\scripts\diff_layout.py

_File not found in repo._

### .agents\skills\pdf-to-latex\scripts\to_latex_page.py

_File not found in repo._

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

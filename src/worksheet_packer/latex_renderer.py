"""Deterministic LaTeX Renderer for Worksheets.

Compiles a RenderPlan AST into publication-grade, compilable LaTeX (.tex)
and invokes local LaTeX engines (pdflatex, xelatex, tectonic, latexmk) to output PDFs.
Uses side-by-side minipage environments and multicols for whitespace optimization.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple

from .worksheet_ast import (
    LayoutDecision,
    PlacedProblem,
    PlacedSectionHeader,
    Problem,
    RenderPlan,
    WorkspaceType,
    parse_prompt_parts,
)
from pdf_to_latex.latex_compiler import (
    compile_tex_to_pdf,
    escape_latex_text,
    format_hex_color,
)


class LatexWorksheetRenderer:
    """Compiles a RenderPlan into clean, compilable LaTeX code and PDFs."""

    def __init__(self, plan: RenderPlan):
        self.plan = plan
        self.ws = plan.worksheet
        self.theme_color = format_hex_color(self.ws.theme_hex)

    def _render_preamble(self) -> str:
        """Generates LaTeX document preamble with required packages."""
        lines = [
            "\\documentclass[10.5pt,letterpaper]{article}",
            "% --- Core Typography & Geometry ---",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage[T1]{fontenc}",
            "\\usepackage{lmodern}",
            f"\\usepackage[letterpaper,top={self.ws.margins.top_in:.2f}in,bottom={self.ws.margins.bottom_in:.2f}in,left={self.ws.margins.left_in:.2f}in,right={self.ws.margins.right_in:.2f}in]{{geometry}}",
            "\\usepackage{microtype}",
            "",
            "% --- Mathematics ---",
            "\\usepackage{amsmath,amssymb,amsfonts,mathtools}",
            "\\usepackage{bm}",
            "",
            "% --- Layout & Multi-column ---",
            "\\usepackage{multicol}",
            "\\usepackage{graphicx}",
            "\\usepackage{enumitem}",
            "\\usepackage{xcolor}",
            "\\usepackage[most]{tcolorbox}",
            f"\\definecolor{{PrimaryColor}}{{HTML}}{{{self.theme_color}}}",
            "\\definecolor{RuleColor}{HTML}{D0D7DE}",
            "",
            "% --- Spacing and Column Settings ---",
            f"\\setlength{{\\columnsep}}{{{self.ws.column_gap_in:.2f}in}}",
            "\\setlength{\\columnseprule}{0.2pt}",
            "\\setlength{\\parindent}{0pt}",
            "\\setlength{\\parskip}{2pt}",
            "",
            "% --- Worksheet Response Box ---",
            "\\newtcolorbox{worksheetbox}[1][]{",
            "    colback=white,",
            "    colframe=RuleColor,",
            "    boxrule=0.8pt,",
            "    arc=2pt,",
            "    left=6pt,right=6pt,top=6pt,bottom=6pt,",
            "    #1",
            "}",
            "",
            "\\pagestyle{empty}",
            "",
        ]
        return "\n".join(lines)

    def _render_header(self) -> str:
        """Renders title and student name/date header."""
        title_esc = escape_latex_text(self.ws.title)
        hdr_right = escape_latex_text(self.ws.header_right or "")

        lines = [
            "\\begin{minipage}[t]{0.50\\linewidth}",
            f"  {{\\large\\textbf{{\\color{{PrimaryColor}}{{{title_esc}}}}}}}",
        ]
        if self.ws.subtitle:
            sub_esc = escape_latex_text(self.ws.subtitle)
            lines.append(f"  \\\\[2pt] {{\\small\\textit{{{sub_esc}}}}}")
        lines.extend([
            "\\end{minipage}\\hfill",
            "\\begin{minipage}[t]{0.48\\linewidth}",
            "  \\raggedleft",
            f"  {{\\small {hdr_right}}}",
            "\\end{minipage}",
            "\\vspace{4pt}",
            "\\hrule height 0.5pt",
            "\\vspace{8pt}",
            "",
        ])
        return "\n".join(lines)

    def _render_prompt_text(
        self,
        problem: Problem,
        placed: Optional[PlacedProblem] = None,
        font_size_pt: Optional[float] = None,
    ) -> str:
        """Returns LaTeX-escaped text for problem prompt, preserving math and styling sub-parts."""
        fs = font_size_pt or self.ws.default_font_size_pt
        prefix = ""
        label = problem.full_label
        if label:
            prefix = f"\\textbf{{\\color{{PrimaryColor}}{{{escape_latex_text(label)}}}}} "

        if problem.prompt_runs and not problem.prompt_text:
            parts = []
            if prefix:
                parts.append(prefix)
            for r in problem.prompt_runs:
                if r.is_math:
                    math_txt = r.text.strip()
                    if not (math_txt.startswith("$") and math_txt.endswith("$")):
                        math_txt = f"${math_txt}$"
                    parts.append(math_txt)
                else:
                    t = escape_latex_text(r.text)
                    if r.bold and r.italic:
                        t = f"\\textbf{{\\textit{{{t}}}}}"
                    elif r.bold:
                        t = f"\\textbf{{{t}}}"
                    elif r.italic:
                        t = f"\\textit{{{t}}}"
                    parts.append(t)
            content = "".join(parts)
            if fs and abs(fs - self.ws.default_font_size_pt) >= 0.2:
                leading = fs * 1.25
                return f"{{\\fontsize{{{fs:.1f}pt}}{{{leading:.1f}pt}}\\selectfont {content}}}"
            return content

        raw_text = problem.prompt_text or ""
        if label and raw_text.startswith(label):
            raw_text = raw_text[len(label):].strip()

        segments = parse_prompt_parts(raw_text)
        if not segments:
            segments = [(None, "")]

        sub_parts = [(lbl, txt) for lbl, txt in segments if lbl is not None]
        num_sub_parts = len(sub_parts)

        # Detect available space to include open space between parts
        ws_h = placed.workspace_height_in if placed else 0.0
        spacing_after = getattr(placed, "spacing_after_in", 0.10) if placed else 0.10

        inter_part_space_pt = 3.0
        if num_sub_parts >= 2 and not getattr(placed, "_sub_parts_spaced", False):
            if ws_h >= 0.35 and placed and placed.problem.workspace.type in (WorkspaceType.BLANK, WorkspaceType.LINES):
                # Distribute part of the student workspace between sub-parts
                inter_space_in = min(0.40, max(0.12, (ws_h * 0.65) / num_sub_parts))
                inter_part_space_pt = inter_space_in * 72.0
                distributed_in = (num_sub_parts - 1) * inter_space_in
                placed.workspace_height_in = max(0.15, ws_h - distributed_in)
                placed._sub_parts_spaced = True
                placed._inter_part_space_pt = inter_part_space_pt
            elif spacing_after >= 0.30:
                inter_part_space_pt = min(14.0, max(6.0, spacing_after * 24.0))
                placed._sub_parts_spaced = True
                placed._inter_part_space_pt = inter_part_space_pt
        elif getattr(placed, "_sub_parts_spaced", False):
            inter_part_space_pt = getattr(placed, "_inter_part_space_pt", 3.0)

        lines_out = []
        for idx, (part_lbl, content) in enumerate(segments):
            part_line = ""
            if idx == 0 and prefix:
                part_line += prefix

            if part_lbl:
                part_bold = f"\\textbf{{\\color{{PrimaryColor}}{{{escape_latex_text(part_lbl)}}}}} "
                if idx > 0:
                    part_line += f"\\hspace*{{10pt}}{part_bold}"
                else:
                    part_line += part_bold

            if content:
                part_line += escape_latex_text(content)

            lines_out.append(part_line)

        if len(lines_out) > 1:
            sep = f"\\par\\vspace{{{inter_part_space_pt:.1f}pt}}\n"
            content = sep.join(lines_out)
        else:
            content = lines_out[0] if lines_out else ""

        if fs and abs(fs - self.ws.default_font_size_pt) >= 0.2:
            leading = fs * 1.25
            return f"{{\\fontsize{{{fs:.1f}pt}}{{{leading:.1f}pt}}\\selectfont {content}}}"
        return content

    def _render_choices(self, problem: Problem, font_size_pt: Optional[float] = None) -> str:
        """Renders multiple choice options using enumerate."""
        if not problem.choices:
            return ""
        font_cmd = ""
        if font_size_pt and abs(font_size_pt - self.ws.default_font_size_pt) >= 0.2:
            leading = font_size_pt * 1.25
            font_cmd = f"\\fontsize{{{font_size_pt:.1f}pt}}{{{leading:.1f}pt}}\\selectfont "

        lines = ["\\begin{enumerate}[label=(\\Alph*),itemsep=1pt,topsep=2pt,leftmargin=18pt]"]
        for ch in problem.choices:
            c_text = escape_latex_text(ch.text)
            if font_cmd:
                lines.append(f"  \\item {{{font_cmd}{c_text}}}")
            else:
                lines.append(f"  \\item {c_text}")
        lines.append("\\end{enumerate}")
        return "\n".join(lines)

    def _render_workspace(self, placed: PlacedProblem) -> str:
        """Renders work area lines, box, or blank space."""
        ws_cfg = placed.problem.workspace
        if ws_cfg.type == WorkspaceType.NONE:
            return ""

        h_pt = max(28.0, placed.workspace_height_in * 72.0)

        if ws_cfg.type == WorkspaceType.BOX:
            return f"\\begin{{worksheetbox}}[height={h_pt:.1f}pt]\\end{{worksheetbox}}"
        elif ws_cfg.type == WorkspaceType.GRID:
            return (
                f"\\begin{{worksheetbox}}[height={h_pt:.1f}pt]\n"
                f"  \\centering\\vspace*{{{h_pt / 3.0:.1f}pt}}\\textcolor{{gray!70}}{{\\scriptsize [ Graph / Grid Area ]}}\n"
                f"\\end{{worksheetbox}}"
            )
        elif ws_cfg.type in (WorkspaceType.BLANK, WorkspaceType.LINES):
            # Pure vertical whitespace for student work (no blank underlines)
            return f"\\vspace*{{{placed.workspace_height_in:.2f}in}}"
        else:
            return f"\\vspace*{{{placed.workspace_height_in:.2f}in}}"

    def _render_side_by_side_problem(self, placed: PlacedProblem) -> str:
        """Renders side-by-side text (62%) and image (35%) via minipage."""
        prob = placed.problem
        img = prob.image
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        prompt = self._render_prompt_text(prob, placed=placed, font_size_pt=fs)
        choices = self._render_choices(prob, font_size_pt=fs)
        workspace = self._render_workspace(placed)

        img_include = ""
        if img and img.media_path:
            img_path = img.media_path.replace("\\", "/")
            img_include = f"\\includegraphics[width=\\linewidth]{{{img_path}}}"
            if img.caption:
                img_include += f"\\\\[2pt]{{\\scriptsize\\textit{{{escape_latex_text(img.caption)}}}}}"

        tot_w = max(0.1, placed.width_in)
        img_ratio = min(0.50, max(0.25, placed.image_render_width_in / tot_w))
        text_ratio = round(0.96 - img_ratio, 2)
        img_ratio = round(img_ratio, 2)

        lines = [
            "\\noindent",
            f"\\begin{{minipage}}[t]{{{text_ratio:.2f}\\linewidth}}",
            f"  {prompt}",
        ]
        if choices:
            lines.append(f"  {choices}")
        lines.extend([
            "\\end{minipage}\\hfill",
            f"\\begin{{minipage}}[t]{{{img_ratio:.2f}\\linewidth}}",
            "  \\vspace{0pt}",
            "  \\centering",
            f"  {img_include}",
            "\\end{minipage}",
        ])
        if workspace:
            lines.append(f"\\par\\vspace{{2pt}}\n{workspace}")
        space_in = getattr(placed, "spacing_after_in", 0.10)
        lines.append(f"\\vspace{{{space_in:.2f}in}}")
        return "\n".join(lines)

    def _render_stacked_problem(self, placed: PlacedProblem) -> str:
        """Renders stacked problem: text, centered image, workspace."""
        prob = placed.problem
        img = prob.image
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        prompt = self._render_prompt_text(prob, placed=placed, font_size_pt=fs)
        choices = self._render_choices(prob, font_size_pt=fs)
        workspace = self._render_workspace(placed)

        lines = [
            "\\noindent",
            prompt,
        ]
        if choices:
            lines.append(choices)

        if img and img.media_path:
            img_path = img.media_path.replace("\\", "/")
            lines.extend([
                "\\begin{center}",
                f"  \\includegraphics[width={placed.image_render_width_in / placed.width_in:.2f}\\linewidth]{{{img_path}}}",
            ])
            if img.caption:
                lines.append(f"  \\\\[2pt]{{\\scriptsize\\textit{{{escape_latex_text(img.caption)}}}}}")
            lines.append("\\end{center}")

        if workspace:
            lines.append(workspace)

        space_in = getattr(placed, "spacing_after_in", 0.10)
        lines.append(f"\\vspace{{{space_in:.2f}in}}")
        return "\n".join(lines)

    def _render_text_only_problem(self, placed: PlacedProblem) -> str:
        """Renders text-only problem."""
        prob = placed.problem
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        prompt = self._render_prompt_text(prob, placed=placed, font_size_pt=fs)
        choices = self._render_choices(prob, font_size_pt=fs)
        workspace = self._render_workspace(placed)

        lines = [
            "\\noindent",
            prompt,
        ]
        if choices:
            lines.append(choices)
        if workspace:
            lines.append(workspace)
        space_in = getattr(placed, "spacing_after_in", 0.10)
        lines.append(f"\\vspace{{{space_in:.2f}in}}")
        return "\n".join(lines)

    def _render_section_header(self, header: PlacedSectionHeader) -> str:
        """Renders section title."""
        lines = []
        if header.title:
            t = escape_latex_text(header.title)
            lines.append(f"\\vspace{{6pt}}\\textbf{{\\color{{PrimaryColor}}{{{t}}}}}\\\\[2pt]")
        if header.instructions:
            inst = escape_latex_text(header.instructions)
            lines.append(f"{{\\small\\textit{{{inst}}}}}\\\\[4pt]")
        return "\n".join(lines)

    def generate_latex(self) -> str:
        """Produces complete LaTeX document string."""
        preamble = self._render_preamble()
        header = self._render_header()

        body_parts = ["\\begin{document}", header]

        use_multicols = self.ws.default_columns > 1

        for page_idx, page in enumerate(self.plan.pages):
            if page_idx > 0:
                body_parts.append("\\newpage")

            if use_multicols:
                body_parts.append(f"\\begin{{multicols*}}{{{self.ws.default_columns}}}")

            current_col = 0
            for item in page.items:
                if isinstance(item, PlacedSectionHeader):
                    body_parts.append(self._render_section_header(item))
                elif isinstance(item, PlacedProblem):
                    if use_multicols and item.col_index > current_col:
                        body_parts.append("\\columnbreak\n")
                        current_col = item.col_index

                    if item.layout == LayoutDecision.SIDE_BY_SIDE:
                        body_parts.append(self._render_side_by_side_problem(item))
                    elif item.layout == LayoutDecision.STACKED:
                        body_parts.append(self._render_stacked_problem(item))
                    else:
                        body_parts.append(self._render_text_only_problem(item))

            if use_multicols:
                body_parts.append("\\end{multicols*}")

        body_parts.append("\\end{document}")

        return preamble + "\n" + "\n".join(body_parts) + "\n"

    def render(self, output_tex_path: str | Path, compile_pdf: bool = False) -> Path:
        """Writes .tex file to disk and optionally invokes LaTeX engine to build PDF."""
        out_p = Path(output_tex_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        tex_code = self.generate_latex()
        out_p.write_text(tex_code, encoding="utf-8")

        if compile_pdf:
            compile_tex_to_pdf(out_p)

        return out_p


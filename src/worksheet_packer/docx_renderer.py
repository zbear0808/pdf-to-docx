"""Deterministic DOCX Renderer for Worksheets.

Transforms a RenderPlan AST into a high-density, professional Word document (.docx).
Enforces invisible structural tables with OpenXML w:cantSplit on all problem containers
so diagrams, text, and workspaces stay strictly bound together without page-boundary splits.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from .worksheet_ast import (
    LayoutDecision,
    PlacedProblem,
    PlacedSectionHeader,
    Problem,
    RenderPlan,
    WorkspaceType,
    parse_prompt_parts,
)
from pdf_to_docx.docx_compiler import hex_to_rgb


def clear_table_borders(table) -> None:
    """Removes all borders from a table to make it an invisible layout frame."""
    tblPr = table._tbl.tblPr
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def make_row_cant_split(row) -> None:
    """Prevents a table row from breaking mid-cell across a page boundary (w:cantSplit)."""
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:cantSplit")) is None:
        trPr.append(OxmlElement("w:cantSplit"))


def set_cell_width(cell, width_in: float) -> None:
    """Sets explicit cell width in twips (1/1440 of an inch)."""
    twips = max(100, int(width_in * 1440))
    tcPr = cell._tc.get_or_add_tcPr()
    # Remove existing tcW if present
    old_w = tcPr.find(qn("w:tcW"))
    if old_w is not None:
        tcPr.remove(old_w)
    tcW = parse_xml(f'<w:tcW {nsdecls("w")} w:w="{twips}" w:type="dxa"/>')
    tcPr.append(tcW)


def set_cell_padding(cell, top: int = 40, bottom: int = 40, left: int = 40, right: int = 40) -> None:
    """Sets cell padding in twips."""
    tcPr = cell._tc.get_or_add_tcPr()
    old_mar = tcPr.find(qn("w:tcMar"))
    if old_mar is not None:
        tcPr.remove(old_mar)
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def clean_math_text_for_docx(text: str) -> str:
    """Replaces common LaTeX math escape sequences with clean Unicode symbols for Word."""
    if not text:
        return ""
    import re

    out = text
    # Fix potential double-encoded UTF-8 artifacts (e.g. 180Â° -> 180°)
    out = out.replace("Â°", "°").replace("Â", "")

    # Superscript map for roots and powers
    sup_map = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
        "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
        "n": "ⁿ", "x": "ˣ", "y": "ʸ",
    }

    # Translate \sqrt[n]{x} -> ⁿ√(x)
    def _repl_root(m):
        idx = "".join(sup_map.get(ch, ch) for ch in m.group(1))
        content = m.group(2)
        return f"{idx}√({content})"
    out = re.sub(r"\\sqrt\[([^\]]+)\]\{([^\}]+)\}", _repl_root, out)

    # Translate \sqrt{x} -> √(x)
    out = re.sub(r"\\sqrt\{([^\}]+)\}", r"√(\1)", out)

    # Translate x^{n} or x^n -> xⁿ
    def _repl_sup(m):
        base = m.group(1)
        exp = m.group(2)
        sup = "".join(sup_map.get(ch, ch) for ch in exp)
        return f"{base}{sup}"
    out = re.sub(r"([A-Za-z0-9\)])\^\{([^\}]+)\}", _repl_sup, out)
    out = re.sub(r"([A-Za-z0-9\)])\^([0-9a-zA-Z\+\-])", _repl_sup, out)

    replacements = [
        (r"\ell", "ℓ"),
        (r"^{\circ}", "°"),
        (r"^\circ", "°"),
        (r"\circ", "°"),
        (r"\theta", "θ"),
        (r"\alpha", "α"),
        (r"\beta", "β"),
        (r"\pi", "π"),
        (r"\le", "≤"),
        (r"\ge", "≥"),
        (r"\neq", "≠"),
        (r"\approx", "≈"),
        (r"\times", "×"),
        (r"\div", "÷"),
        (r"\pm", "±"),
        (r"\parallel", "∥"),
        (r"\perp", "⊥"),
        (r"\angle", "∠"),
        (r"\cong", "≅"),
        (r"\sim", "∼"),
        (r"\Delta", "Δ"),
        (r"\triangle", "△"),
        (r"\(", ""),
        (r"\)", ""),
        (r"\[", ""),
        (r"\]", ""),
    ]
    for old, new in replacements:
        out = out.replace(old, new)
    out = out.replace("\\n", " ")
    out = re.sub(r"\$([^\$]+)\$", r"\1", out)
    # Clean up double-encoded or mangled characters (e.g. â„“, â€, Â)
    out = out.replace("Â°", "°").replace("Â", "").replace("â„“", "ℓ").replace("â€“", "–").replace("â€”", "—")
    return out


class DocxWorksheetRenderer:
    """Compiles a RenderPlan into an editable, space-optimized Word (.docx) document."""

    def __init__(self, plan: RenderPlan):
        self.plan = plan
        self.ws = plan.worksheet
        self.doc = Document()
        self._configure_document()

    def _configure_document(self) -> None:
        """Sets page dimensions, margins, and standard typography styles."""
        normal = self.doc.styles["Normal"]
        normal.font.name = self.ws.default_font
        normal.font.size = Pt(self.ws.default_font_size_pt)
        normal.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        normal.paragraph_format.line_spacing = 1.05
        normal.paragraph_format.space_after = Pt(2)

        section = self.doc.sections[0]
        section.page_width = Inches(self.ws.page_width_in)
        section.page_height = Inches(self.ws.page_height_in)
        section.top_margin = Inches(self.ws.margins.top_in)
        section.bottom_margin = Inches(self.ws.margins.bottom_in)
        section.left_margin = Inches(self.ws.margins.left_in)
        section.right_margin = Inches(self.ws.margins.right_in)

        # Configure columns on the section
        if self.ws.default_columns > 1:
            sectPr = section._sectPr
            cols = sectPr.xpath("./w:cols")
            gap_twips = int(self.ws.column_gap_in * 1440)
            if cols:
                cols[0].set(qn("w:num"), str(self.ws.default_columns))
                cols[0].set(qn("w:space"), str(gap_twips))
            else:
                col_elem = parse_xml(
                    f'<w:cols {nsdecls("w")} w:num="{self.ws.default_columns}" w:space="{gap_twips}"/>'
                )
                sectPr.append(col_elem)

    def _render_header_block(self) -> None:
        """Renders title and student name/date header at top of first page."""
        # Top title & student info table
        table = self.doc.add_table(rows=1, cols=2)
        clear_table_borders(table)
        make_row_cant_split(table.rows[0])
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        col_w = self.ws.printable_width_in / 2.0
        set_cell_width(table.cell(0, 0), col_w)
        set_cell_width(table.cell(0, 1), col_w)
        set_cell_padding(table.cell(0, 0), top=0, bottom=60, left=0, right=40)
        set_cell_padding(table.cell(0, 1), top=0, bottom=60, left=40, right=0)

        # Left cell: Title & Subtitle
        c_left = table.cell(0, 0)
        p_title = c_left.paragraphs[0]
        p_title.paragraph_format.space_after = Pt(2)
        r_title = p_title.add_run(self.ws.title)
        r_title.bold = True
        r_title.font.size = Pt(14)
        r_title.font.color.rgb = hex_to_rgb(self.ws.theme_hex)

        if self.ws.subtitle:
            p_sub = c_left.add_paragraph()
            p_sub.paragraph_format.space_after = Pt(2)
            r_sub = p_sub.add_run(self.ws.subtitle)
            r_sub.italic = True
            r_sub.font.size = Pt(10)
            r_sub.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

        # Right cell: Name / Date / Period line
        c_right = table.cell(0, 1)
        p_hdr = c_right.paragraphs[0]
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_hdr.paragraph_format.space_after = Pt(2)
        if self.ws.header_right:
            r_hdr = p_hdr.add_run(self.ws.header_right)
            r_hdr.font.size = Pt(9.5)
            r_hdr.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        # Subtle separator
        p_sep = self.doc.add_paragraph()
        p_sep.paragraph_format.space_before = Pt(2)
        p_sep.paragraph_format.space_after = Pt(8)
        p_sep_run = p_sep.add_run("―" * 55)
        p_sep_run.font.size = Pt(8)
        p_sep_run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

    def _apply_prompt_text(
        self,
        container_or_paragraph,
        problem: Problem,
        placed: Optional[PlacedProblem] = None,
        font_size_pt: Optional[float] = None,
    ) -> None:
        """Adds question number prefix, bold sub-part letters, and styled prompt runs to cell or paragraph."""
        fs = font_size_pt or self.ws.default_font_size_pt
        theme_rgb = hex_to_rgb(self.ws.theme_hex)

        is_cell = hasattr(container_or_paragraph, "paragraphs")
        first_p = container_or_paragraph.paragraphs[0] if is_cell else container_or_paragraph
        cell = container_or_paragraph if is_cell else None

        label = problem.full_label

        if problem.prompt_runs and not problem.prompt_text:
            if label:
                r_lbl = first_p.add_run(f"{label} ")
                r_lbl.bold = True
                r_lbl.font.color.rgb = theme_rgb
                r_lbl.font.size = Pt(fs)

            for r_spec in problem.prompt_runs:
                clean_txt = clean_math_text_for_docx(r_spec.text)
                r = first_p.add_run(clean_txt)
                r.bold = r_spec.bold
                r.italic = r_spec.italic
                r.underline = r_spec.underline
                if r_spec.is_math:
                    r.font.name = "Cambria Math"
                    r.italic = True
                if r_spec.color_hex:
                    r.font.color.rgb = hex_to_rgb(r_spec.color_hex)
                r_fs = r_spec.font_size_pt or fs
                r.font.size = Pt(r_fs)
            return

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
        if num_sub_parts >= 2 and cell is not None and not getattr(placed, "_sub_parts_spaced", False):
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

        for idx, (part_lbl, content) in enumerate(segments):
            if idx == 0:
                p = first_p
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2 if part_lbl is None else inter_part_space_pt)

                if label:
                    r_lbl = p.add_run(f"{label} ")
                    r_lbl.bold = True
                    r_lbl.font.color.rgb = theme_rgb
                    r_lbl.font.size = Pt(fs)

                if part_lbl:
                    r_part = p.add_run(f"{part_lbl} ")
                    r_part.bold = True
                    r_part.font.color.rgb = theme_rgb
                    r_part.font.size = Pt(fs)

                if content:
                    clean_c = clean_math_text_for_docx(content)
                    r_txt = p.add_run(clean_c)
                    r_txt.font.size = Pt(fs)
            else:
                if cell is not None:
                    p = cell.add_paragraph()
                else:
                    first_p.add_run("\n")
                    p = first_p

                if part_lbl:
                    if cell is not None:
                        p.paragraph_format.left_indent = Inches(0.15)
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(inter_part_space_pt if idx < len(segments) - 1 else 2)
                    r_part = p.add_run(f"{part_lbl} ")
                    r_part.bold = True
                    r_part.font.color.rgb = theme_rgb
                    r_part.font.size = Pt(fs)
                else:
                    if cell is not None:
                        p.paragraph_format.space_before = Pt(1)
                        p.paragraph_format.space_after = Pt(2)

                if content:
                    clean_c = clean_math_text_for_docx(content)
                    r_txt = p.add_run(clean_c)
                    r_txt.font.size = Pt(fs)

    def _apply_choices(self, container_cell, problem: Problem, font_size_pt: Optional[float] = None) -> None:
        """Appends multiple choice options to a cell."""
        if not problem.choices:
            return
        for ch in problem.choices:
            p = container_cell.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.15)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(1)
            r_lbl = p.add_run(f"{ch.label} ")
            r_lbl.bold = True
            if font_size_pt:
                r_lbl.font.size = Pt(font_size_pt)
            if ch.runs:
                for r_spec in ch.runs:
                    clean_c = clean_math_text_for_docx(r_spec.text)
                    r = p.add_run(clean_c)
                    r.bold = r_spec.bold
                    r.italic = r_spec.italic
                    r_fs = r_spec.font_size_pt or font_size_pt
                    if r_fs:
                        r.font.size = Pt(r_fs)
            else:
                clean_c = clean_math_text_for_docx(ch.text)
                r = p.add_run(clean_c)
                if font_size_pt:
                    r.font.size = Pt(font_size_pt)

    def _render_workspace_in_cell(self, cell, placed: PlacedProblem) -> None:
        """Renders answer lines or response box in designated cell."""
        ws_cfg = placed.problem.workspace
        if ws_cfg.type == WorkspaceType.NONE:
            return

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(2)

        if ws_cfg.type == WorkspaceType.BOX or ws_cfg.type == WorkspaceType.GRID:
            # Render a framed response box
            sub_tbl = cell.add_table(rows=1, cols=1)
            sub_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            box_cell = sub_tbl.cell(0, 0)
            h_pt = max(40.0, placed.workspace_height_in * 72.0)
            sub_tbl.rows[0].height = Pt(h_pt)
            make_row_cant_split(sub_tbl.rows[0])
            set_cell_width(box_cell, placed.width_in * 0.95)
            # Add light border
            tcPr = box_cell._tc.get_or_add_tcPr()
            borders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>\n'
                f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>\n'
                f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>\n'
                f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>\n'
                f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>\n'
                f'</w:tcBorders>'
            )
            tcPr.append(borders)
            if ws_cfg.type == WorkspaceType.GRID:
                p_grid = box_cell.paragraphs[0]
                r_grid = p_grid.add_run("[ Graph / Grid Area ]")
                r_grid.font.size = Pt(8.5)
                r_grid.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
        elif ws_cfg.type == WorkspaceType.LINES or ws_cfg.type == WorkspaceType.BLANK:
            # Clean empty whitespace for student work (no blank underlines)
            h_pt = max(14.0, placed.workspace_height_in * 72.0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.line_spacing = Pt(1)
            p.paragraph_format.space_after = Pt(max(4.0, h_pt - 8.0))

    def _render_side_by_side_problem(self, placed: PlacedProblem, has_next_in_column: bool = True) -> None:
        """Renders Layout A: Side-by-side text (left) and diagram (right) in an invisible table."""
        prob = placed.problem
        img = prob.image
        col_w = placed.width_in

        # 2 rows: Row 0 has (Text, Image), Row 1 has (Workspace across both)
        has_workspace = prob.workspace.type != WorkspaceType.NONE
        num_rows = 2 if has_workspace else 1

        table = self.doc.add_table(rows=num_rows, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        clear_table_borders(table)

        for row in table.rows:
            make_row_cant_split(row)

        text_w = placed.text_render_width_in
        img_w = placed.image_render_width_in

        table.columns[0].width = Inches(text_w)
        table.columns[1].width = Inches(img_w)
        set_cell_width(table.cell(0, 0), text_w)
        set_cell_width(table.cell(0, 1), img_w)
        set_cell_padding(table.cell(0, 0), top=20, bottom=20, left=20, right=40)
        set_cell_padding(table.cell(0, 1), top=20, bottom=20, left=20, right=20)

        # Row 0, Cell 0: Question Text + Choices
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        c_text = table.cell(0, 0)
        p_text = c_text.paragraphs[0]
        p_text.paragraph_format.space_before = Pt(0)
        p_text.paragraph_format.space_after = Pt(2)
        self._apply_prompt_text(c_text, prob, placed=placed, font_size_pt=fs)
        self._apply_choices(c_text, prob, font_size_pt=fs)

        # Row 0, Cell 1: Image
        c_img = table.cell(0, 1)
        p_img = c_img.paragraphs[0]
        p_img.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_img.paragraph_format.space_before = Pt(0)
        p_img.paragraph_format.space_after = Pt(0)

        if img and img.media_path and Path(img.media_path).exists():
            r_img = p_img.add_run()
            # Explicit width preserves native aspect ratio deterministically
            safe_img_w = max(0.5, img_w - 0.05)
            r_img.add_picture(img.media_path, width=Inches(safe_img_w))
            if img.caption:
                p_cap = c_img.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_cap.add_run(img.caption)
                r_cap.font.size = Pt(8)
                r_cap.italic = True

        # Row 1: Workspace spanning both columns
        if has_workspace:
            table.rows[1].height = Pt(max(14.0, placed.workspace_height_in * 72.0))
            c_work = table.cell(1, 0)
            c_work.merge(table.cell(1, 1))
            set_cell_width(c_work, col_w)
            set_cell_padding(c_work, top=20, bottom=20, left=20, right=20)
            self._render_workspace_in_cell(c_work, placed)

        # Inter-problem spacing paragraph (only between problems in the same column)
        if has_next_in_column:
            space_pt = max(4.0, getattr(placed, "spacing_after_in", 0.10) * 72.0)
            p_space = self.doc.add_paragraph()
            p_space.paragraph_format.space_before = Pt(0)
            p_space.paragraph_format.space_after = Pt(space_pt)

    def _render_stacked_problem(self, placed: PlacedProblem, has_next_in_column: bool = True) -> None:
        """Renders Layout B: Stacked text (top), diagram (middle), workspace (bottom)."""
        prob = placed.problem
        img = prob.image
        col_w = placed.width_in

        has_workspace = prob.workspace.type != WorkspaceType.NONE
        num_rows = 3 if has_workspace else 2

        table = self.doc.add_table(rows=num_rows, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        clear_table_borders(table)

        for row in table.rows:
            make_row_cant_split(row)

        for r_idx in range(num_rows):
            set_cell_width(table.cell(r_idx, 0), col_w)
            set_cell_padding(table.cell(r_idx, 0), top=20, bottom=20, left=20, right=20)

        # Row 0: Text + choices
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        c_text = table.cell(0, 0)
        p_text = c_text.paragraphs[0]
        p_text.paragraph_format.space_before = Pt(0)
        p_text.paragraph_format.space_after = Pt(2)
        self._apply_prompt_text(c_text, prob, placed=placed, font_size_pt=fs)
        self._apply_choices(c_text, prob, font_size_pt=fs)

        # Row 1: Centered diagram
        c_img = table.cell(1, 0)
        p_img = c_img.paragraphs[0]
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(2)
        p_img.paragraph_format.space_after = Pt(2)

        if img and img.media_path and Path(img.media_path).exists():
            r_img = p_img.add_run()
            r_img.add_picture(img.media_path, width=Inches(placed.image_render_width_in))
            if img.caption:
                p_cap = c_img.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_cap.add_run(img.caption)
                r_cap.font.size = Pt(8)
                r_cap.italic = True

        # Row 2: Workspace
        if has_workspace:
            table.rows[2].height = Pt(max(14.0, placed.workspace_height_in * 72.0))
            c_work = table.cell(2, 0)
            self._render_workspace_in_cell(c_work, placed)

        if has_next_in_column:
            space_pt = max(4.0, getattr(placed, "spacing_after_in", 0.10) * 72.0)
            p_space = self.doc.add_paragraph()
            p_space.paragraph_format.space_before = Pt(0)
            p_space.paragraph_format.space_after = Pt(space_pt)

    def _render_text_only_problem(self, placed: PlacedProblem, has_next_in_column: bool = True) -> None:
        """Renders text-only problem inside an atomic invisible table."""
        prob = placed.problem
        col_w = placed.width_in
        has_workspace = prob.workspace.type != WorkspaceType.NONE

        table = self.doc.add_table(rows=2 if has_workspace else 1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        clear_table_borders(table)

        for row in table.rows:
            make_row_cant_split(row)

        fs = placed.font_size_pt or self.ws.default_font_size_pt
        c_text = table.cell(0, 0)
        set_cell_width(c_text, col_w)
        set_cell_padding(c_text, top=20, bottom=20, left=20, right=20)
        p_text = c_text.paragraphs[0]
        p_text.paragraph_format.space_before = Pt(0)
        p_text.paragraph_format.space_after = Pt(2)
        self._apply_prompt_text(c_text, prob, placed=placed, font_size_pt=fs)
        self._apply_choices(c_text, prob, font_size_pt=fs)

        if has_workspace:
            table.rows[1].height = Pt(max(14.0, placed.workspace_height_in * 72.0))
            c_work = table.cell(1, 0)
            set_cell_width(c_work, col_w)
            set_cell_padding(c_work, top=20, bottom=20, left=20, right=20)
            self._render_workspace_in_cell(c_work, placed)

        if has_next_in_column:
            space_pt = max(4.0, getattr(placed, "spacing_after_in", 0.10) * 72.0)
            p_space = self.doc.add_paragraph()
            p_space.paragraph_format.space_before = Pt(0)
            p_space.paragraph_format.space_after = Pt(space_pt)

    def _render_section_header(self, header: PlacedSectionHeader) -> None:
        """Renders section title and instructions."""
        if header.title:
            p_title = self.doc.add_paragraph()
            p_title.paragraph_format.keep_with_next = True
            p_title.paragraph_format.space_before = Pt(8)
            p_title.paragraph_format.space_after = Pt(2)
            clean_title = clean_math_text_for_docx(header.title)
            r = p_title.add_run(clean_title)
            r.bold = True
            r.font.size = Pt(11.5)
            r.font.color.rgb = hex_to_rgb(self.ws.theme_hex)

        if header.instructions:
            p_inst = self.doc.add_paragraph()
            p_inst.paragraph_format.keep_with_next = True
            p_inst.paragraph_format.space_before = Pt(0)
            p_inst.paragraph_format.space_after = Pt(4)
            clean_inst = clean_math_text_for_docx(header.instructions)
            r = p_inst.add_run(clean_inst)
            r.italic = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    def render(self, output_docx_path: str | Path) -> Path:
        """Executes document rendering and writes out the formatted .docx file."""
        out_path = Path(output_docx_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        self._render_header_block()

        for page_idx, page in enumerate(self.plan.pages):
            if page_idx > 0:
                self.doc.add_page_break()

            current_col = 0
            for idx, item in enumerate(page.items):
                if isinstance(item, PlacedSectionHeader):
                    self._render_section_header(item)
                elif isinstance(item, PlacedProblem):
                    if self.ws.default_columns > 1 and item.col_index > current_col:
                        p_break = self.doc.add_paragraph()
                        p_break.paragraph_format.space_before = Pt(0)
                        p_break.paragraph_format.space_after = Pt(0)
                        p_break.paragraph_format.line_spacing = Pt(1)
                        run = p_break.add_run()
                        run.font.size = Pt(1)
                        run.add_break(WD_BREAK.COLUMN)
                        current_col = item.col_index

                    next_in_col = any(
                        isinstance(other, PlacedProblem) and other.col_index == item.col_index
                        for other in page.items[idx + 1 :]
                    )

                    if item.layout == LayoutDecision.SIDE_BY_SIDE:
                        self._render_side_by_side_problem(item, has_next_in_column=next_in_col)
                    elif item.layout == LayoutDecision.STACKED:
                        self._render_stacked_problem(item, has_next_in_column=next_in_col)
                    else:
                        self._render_text_only_problem(item, has_next_in_column=next_in_col)

        self.doc.save(str(out_path))
        return out_path


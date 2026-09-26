"""Deterministic DOCX Compiler.

Transforms a DocumentSpec AST into a production-grade Word document (.docx).
Enforces OpenXML rules for repeating table headers, atomic table rows,
and twip-precise column layouts.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from .ir_schema import (
    Alignment, ChartBlock, DocumentBlock, DocumentSpec,
    HeadingBlock, ImageBlock, ListType, PageBreakBlock,
    PageSpec, ParagraphBlock, TableBlock, TextRun,
)
from .chart_generator import render_chart_image


def hex_to_rgb(hex_str: str) -> RGBColor:
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    return RGBColor(int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16))


def set_cell_background(cell, hex_color: str):
    hex_clean = hex_color.lstrip("#")
    tcPr = cell._tc.get_or_add_tcPr()
    shd = tcPr.find(qn("w:shd"))
    if shd is not None:
        tcPr.remove(shd)
    shd_element = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_clean}" w:val="clear"/>')
    tcPr.append(shd_element)


def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def make_row_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:cantSplit")) is None:
        trPr.append(OxmlElement("w:cantSplit"))


def make_row_header(row):
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:tblHeader")) is None:
        trPr.append(OxmlElement("w:tblHeader"))


class DocxCompiler:
    """Compiles a canonical DocumentSpec AST into a formatted Word (.docx) file."""

    def __init__(self, spec: DocumentSpec):
        self.spec = spec
        self.doc = Document()
        self._configure_styles()

    def _configure_styles(self):
        normal_style = self.doc.styles["Normal"]
        font = normal_style.font
        font.name = self.spec.default_font
        font.size = Pt(self.spec.default_font_size_pt)
        font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        normal_style.paragraph_format.line_spacing = 1.15
        normal_style.paragraph_format.space_after = Pt(4)

    def compile(self, output_docx_path: str | Path, assets_dir: Optional[str | Path] = None) -> Path:
        out_path = Path(output_docx_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        assets_path = Path(assets_dir) if assets_dir else out_path.parent / "assets"
        assets_path.mkdir(parents=True, exist_ok=True)

        for page_idx, page in enumerate(self.spec.pages):
            if page_idx > 0:
                self.doc.add_page_break()
            for block in page.blocks:
                self._render_block(block, assets_path)

        self.doc.save(str(out_path))
        return out_path

    def _render_block(self, block: DocumentBlock, assets_path: Path):
        b_type = getattr(block, "type", "")
        if b_type == "heading":
            self._render_heading(block)
        elif b_type == "paragraph":
            self._render_paragraph(block)
        elif b_type == "table":
            self._render_table(block)
        elif b_type == "chart":
            self._render_chart(block, assets_path)
        elif b_type == "image":
            self._render_image(block)
        elif b_type == "page_break":
            self.doc.add_page_break()

    def _render_heading(self, h: HeadingBlock):
        p = self.doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(max(6, 18 - (h.level * 2)))
        p.paragraph_format.space_after = Pt(4)
        if h.alignment == Alignment.CENTER:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif h.alignment == Alignment.RIGHT:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if h.runs:
            for run in h.runs:
                self._apply_run(p.add_run(run.text), run, is_heading=True, level=h.level)
        else:
            run = p.add_run(h.text)
            run.bold = True
            run.font.size = Pt(max(12, 22 - (h.level * 2)))
            run.font.color.rgb = hex_to_rgb(self.spec.theme_hex)

    def _render_paragraph(self, p_block: ParagraphBlock):
        p = self.doc.add_paragraph()
        if p_block.list_type == ListType.BULLET:
            p.style = "List Bullet"
        elif p_block.list_type == ListType.NUMBERED:
            p.style = "List Number"
        if p_block.is_callout:
            p.paragraph_format.left_indent = Inches(0.25)
            p.paragraph_format.right_indent = Inches(0.25)
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
        if p_block.alignment == Alignment.CENTER:
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        elif p_block.alignment == Alignment.RIGHT:
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        elif p_block.alignment == Alignment.JUSTIFY:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        for r_spec in p_block.runs:
            self._apply_run(p.add_run(r_spec.text), r_spec)

    def _apply_run(self, docx_run, r_spec: TextRun, is_heading: bool = False, level: int = 1):
        docx_run.bold = r_spec.bold
        docx_run.italic = r_spec.italic
        docx_run.underline = r_spec.underline
        docx_run.font.strike = r_spec.strike
        if r_spec.font_size_pt:
            docx_run.font.size = Pt(r_spec.font_size_pt)
        elif is_heading:
            docx_run.font.size = Pt(max(12, 22 - (level * 2)))
        if r_spec.color_hex:
            docx_run.font.color.rgb = hex_to_rgb(r_spec.color_hex)
        elif is_heading:
            docx_run.font.color.rgb = hex_to_rgb(self.spec.theme_hex)
        if r_spec.font_name:
            docx_run.font.name = r_spec.font_name

    def _render_table(self, tbl: TableBlock):
        all_rows = []
        if tbl.headers:
            all_rows.append(tbl.headers)
        all_rows.extend(tbl.rows)
        if not all_rows:
            return

        num_rows = len(all_rows)
        num_cols = max(len(r) for r in all_rows)
        table = self.doc.add_table(rows=num_rows, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        if tbl.style_name:
            try:
                table.style = tbl.style_name
            except Exception:
                table.style = "Table Grid"

        for row_idx, row_data in enumerate(all_rows):
            doc_row = table.rows[row_idx]
            if tbl.cant_split:
                make_row_cant_split(doc_row)
            is_header = row_idx == 0 and bool(tbl.headers)
            if is_header and tbl.repeat_header:
                make_row_header(doc_row)
            for col_idx in range(num_cols):
                cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
                cell = doc_row.cells[col_idx]
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_margins(cell, top=120, bottom=120, left=140, right=140)
                p = cell.paragraphs[0]
                p.text = ""
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                run = p.add_run(cell_text)
                if is_header:
                    run.bold = True
                    run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                    run.font.size = Pt(10)
                    set_cell_background(cell, self.spec.theme_hex)
                else:
                    run.font.size = Pt(9.5)
                    if row_idx % 2 == 1:
                        set_cell_background(cell, "#F7F9FB")

        if tbl.col_widths_pct and len(tbl.col_widths_pct) == num_cols:
            total_width = Inches(6.5)
            for col_idx, pct in enumerate(tbl.col_widths_pct):
                col_w = total_width * (pct / 100.0)
                for row in table.rows:
                    row.cells[col_idx].width = col_w

    def _render_chart(self, chart: ChartBlock, assets_path: Path):
        chart_img_path = chart.generated_image_path
        if not chart_img_path or not Path(chart_img_path).exists():
            chart_filename = f"chart_{id(chart)}.png"
            chart_img_path = str(assets_path / chart_filename)
            render_chart_image(chart, chart_img_path)
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(8)
        self.doc.add_picture(str(chart_img_path), width=Inches(min(6.0, chart.width_inches)))

    def _render_image(self, img: ImageBlock):
        if not img.image_path or not Path(img.image_path).exists():
            return
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)
        w = Inches(img.width_inches) if img.width_inches else Inches(5.5)
        h = Inches(img.height_inches) if img.height_inches else None
        if h:
            self.doc.add_picture(img.image_path, width=w, height=h)
        else:
            self.doc.add_picture(img.image_path, width=w)
        if img.caption:
            cap_p = self.doc.add_paragraph()
            cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap_p.paragraph_format.space_before = Pt(2)
            cap_p.paragraph_format.space_after = Pt(6)
            run = cap_p.add_run(img.caption)
            run.italic = True
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

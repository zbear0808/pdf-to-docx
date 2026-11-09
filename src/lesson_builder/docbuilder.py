"""Small python-docx toolkit for black-and-white worksheet handouts with native Word math (OMML)."""
import re
from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_LINE_SPACING
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls, qn
from docx.shared import Inches, Pt, RGBColor
from PIL import Image

FONT = "Calibri"
SIZE = 11
BLACK = RGBColor(0, 0, 0)
M_NS = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math" ' \
       'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

# ----------------------------------------------------------------------------- math (LaTeX subset -> OMML)
SYMBOLS = {
    r"\triangle": "Δ", r"\angle": "∠", r"\cong": "≅", r"\to": "→", r"\parallel": "∥", r"\perp": "⊥",
    r"\circ": "°", r"\leftrightarrow": "↔", r"\ldots": "…", r"\cdot": "·", r"\neq": "≠", r"\approx": "≈",
    r"\ell": "ℓ", r"\quad": "  ", r"\,": " ", r"\ ": " ", r"\times": "×", r"\pm": "±", r"\le": "≤",
    r"\ge": "≥", r"\square": "□",
}


def _esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _mrun(text, size, upright=False):
    sty = '<m:rPr><m:sty m:val="p"/></m:rPr>' if upright else ""
    col = f'<w:color w:val="{_MATH_COLOR[0]}"/>' if _MATH_COLOR[0] else ""
    return (f'<m:r>{sty}<w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>{col}'
            f'<w:sz w:val="{int(size * 2)}"/><w:szCs w:val="{int(size * 2)}"/></w:rPr>'
            f'<m:t xml:space="preserve">{_esc(text)}</m:t></m:r>')


_MATH_COLOR = [None]


def _read_group(s, i):
    """s[i] == '{' -> return (content, index after closing brace)."""
    depth, j = 0, i
    while j < len(s):
        if s[j] == "{":
            depth += 1
        elif s[j] == "}":
            depth -= 1
            if depth == 0:
                return s[i + 1:j], j + 1
        j += 1
    raise ValueError(f"unbalanced braces in {s!r}")


def latex_to_omml_inner(s, size):
    out, buf = [], []

    def flush():
        if buf:
            out.append(_mrun("".join(buf), size))
            buf.clear()

    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "\\":
            m = re.match(r"\\([A-Za-z]+|.)", s[i:])
            cmd = "\\" + m.group(1)
            i += len(m.group(0))
            if cmd in (r"\overline", r"\overleftrightarrow", r"\overrightarrow"):
                while i < len(s) and s[i] == " ":
                    i += 1
                inner, i = _read_group(s, i)
                flush()
                body = latex_to_omml_inner(inner, size)
                if cmd == r"\overline":
                    out.append(f'<m:bar><m:barPr><m:pos m:val="top"/></m:barPr><m:e>{body}</m:e></m:bar>')
                else:
                    chr_ = "↔" if cmd == r"\overleftrightarrow" else "→"
                    out.append(f'<m:groupChr><m:groupChrPr><m:chr m:val="{chr_}"/><m:pos m:val="top"/>'
                               f'<m:vertJc m:val="bot"/></m:groupChrPr><m:e>{body}</m:e></m:groupChr>')
            elif cmd == r"\text":
                inner, i = _read_group(s, i)
                flush()
                out.append(_mrun(inner, size, upright=True))
            elif cmd == r"\triangle":
                flush()
                out.append(_mrun("Δ", size, upright=True))
            elif cmd in SYMBOLS:
                buf.append(SYMBOLS[cmd])
            else:
                raise ValueError(f"unknown latex command {cmd} in {s!r}")
        elif ch == "^":
            i += 1
            if s[i] == "{":
                inner, i = _read_group(s, i)
            elif s[i] == "\\":
                m = re.match(r"\\[A-Za-z]+", s[i:])
                inner = m.group(0)
                i += len(inner)
            else:
                inner, i = s[i], i + 1
            if inner.strip() in (r"\circ", "°"):
                buf.append("°")
            else:
                base = buf.pop() if buf else ""
                flush()
                out.append(f'<m:sSup><m:e>{_mrun(base, size) if base else ""}</m:e>'
                           f'<m:sup>{latex_to_omml_inner(inner, size)}</m:sup></m:sSup>')
        elif ch == "'":
            buf.append("′")
            i += 1
        elif ch == "-":
            buf.append("−")
            i += 1
        elif ch == " ":
            i += 1
        elif ch in "{}":
            i += 1
        else:
            buf.append(ch)
            i += 1
    flush()
    return "".join(out)


def add_math(paragraph, latex, size=SIZE):
    xml = f'<m:oMath {M_NS}>{latex_to_omml_inner(latex, size)}</m:oMath>'
    paragraph._p.append(parse_xml(xml))


# ----------------------------------------------------------------------------- rich text
TOKEN = re.compile(r"(\$[^$]+\$|\*\*[^*]+\*\*|\*[^*]+\*)")


def add_rich(paragraph, text, size=SIZE, bold=False, italic=False, color=None):
    for part in TOKEN.split(text):
        if not part:
            continue
        if part.startswith("$"):
            _MATH_COLOR[0] = None if color is None else str(color)
            add_math(paragraph, part[1:-1], size)
            _MATH_COLOR[0] = None
        elif part.startswith("**"):
            add_rich(paragraph, part[2:-2], size, bold=True, italic=italic, color=color)
        elif part.startswith("*"):
            add_rich(paragraph, part[1:-1], size, bold=bold, italic=True, color=color)
        else:
            r = paragraph.add_run(part)
            r.bold, r.italic = bold, italic
            r.font.size = Pt(size)
            r.font.name = FONT
            r.font.color.rgb = color or BLACK
    return paragraph


ANS = RGBColor(0xC0, 0x00, 0x00)


class A:
    """Answer slot: blank workspace of `height` inches on the student copy; answer text on the key."""

    def __init__(self, text, height=0.0):
        self.lines = text if isinstance(text, list) else [text]
        self.height = height


def _est_lines(text, width_in, size):
    plain = re.sub(r"\\[A-Za-z]+|[${}*]", "", text)
    per_line = max(10, int(width_in * 15 * 10.5 / size))
    return max(1, -(-len(plain) // per_line))


_FONTS = {}


def _font(name, size):
    from PIL import ImageFont
    key = (name, size)
    if key not in _FONTS:
        try:
            _FONTS[key] = ImageFont.truetype(name, int(size * 10))
        except OSError:
            _FONTS[key] = None
    return _FONTS[key]


def _measure_rich(text, size):
    """Printed width in inches of a rich string ($math$ and **bold** markup), measured with Calibri and
    Cambria Math at 10x scale."""
    total = 0.0
    for k, part in enumerate(text.split("$")):
        if k % 2:
            s = re.sub(r"\\(overline|overrightarrow|overleftrightarrow|text)", "", part)
            for cmd, ch in SYMBOLS.items():
                s = s.replace(cmd, ch)
            s = s.replace(r"\triangle", "Δ").replace("'", "′")
            s = re.sub(r"[{}\s]", "", s)
            f = _font("cambria.ttc", size) or _font("calibri.ttf", size)
            factor = 1.08
        else:
            s = part.replace("*", "")
            f = _font("calibri.ttf", size)
            factor = 1.03
        if not s:
            continue
        w = f.getlength(s) if f else len(s) * size * 0.5 * 10
        total += w * factor / 10 / 72  # points -> inches
    return total


def fmt(p, before=0, after=0, left=None, hanging=None, align=None, keep=False, line=None):
    pf = p.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    if left is not None:
        pf.left_indent = Inches(left)
    if hanging is not None:
        pf.first_line_indent = Inches(-hanging)
    if align == "center":
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "right":
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    if keep:
        pf.keep_with_next = True
    if line:
        pf.line_spacing = line
    return p


# ----------------------------------------------------------------------------- table helpers
def _borders_xml(tag, sz=6, val="single", sides=("top", "left", "bottom", "right")):
    inner = "".join(f'<w:{s} w:val="{val}" w:sz="{sz}" w:space="0" w:color="000000"/>' for s in sides)
    return f"<w:{tag} {nsdecls('w')}>{inner}</w:{tag}>"


def table_no_borders(table):
    tblPr = table._tbl.tblPr
    for el in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(el)
    tblPr.append(parse_xml(_borders_xml("tblBorders", val="nil",
                                        sides=("top", "left", "bottom", "right", "insideH", "insideV"))))


def table_borders(table, sz=6, inside=True):
    tblPr = table._tbl.tblPr
    for el in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(el)
    sides = ("top", "left", "bottom", "right") + (("insideH", "insideV") if inside else ())
    tblPr.append(parse_xml(_borders_xml("tblBorders", sz=sz, sides=sides)))


def cell_margins(cell, top=40, bottom=40, left=80, right=80):
    tcPr = cell._tc.get_or_add_tcPr()
    for el in tcPr.findall(qn("w:tcMar")):
        tcPr.remove(el)
    tcPr.append(parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/>'
                          f'<w:left w:w="{left}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/>'
                          f'<w:right w:w="{right}" w:type="dxa"/></w:tcMar>'))


def cell_bottom_border(cell, sz=6):
    tcPr = cell._tc.get_or_add_tcPr()
    tcPr.append(parse_xml(_borders_xml("tcBorders", sz=sz, sides=("bottom",))))


def set_widths(table, widths_in):
    table.autofit = False
    tblPr = table._tbl.tblPr
    for el in tblPr.findall(qn("w:tblLayout")):
        tblPr.remove(el)
    tblPr.append(parse_xml(f'<w:tblLayout {nsdecls("w")} w:type="fixed"/>'))
    for row in table.rows:
        for c, w in zip(row.cells, widths_in):
            c.width = Inches(w)
    grid = table._tbl.tblGrid
    for gc, w in zip(grid.findall(qn("w:gridCol")), widths_in):
        gc.set(qn("w:w"), str(int(w * 1440)))


def row_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    trPr.append(parse_xml(f'<w:cantSplit {nsdecls("w")}/>'))


def row_height(row, inches, exact=False):
    trPr = row._tr.get_or_add_trPr()
    rule = "exact" if exact else "atLeast"
    trPr.append(parse_xml(f'<w:trHeight {nsdecls("w")} w:val="{int(inches * 1440)}" w:hRule="{rule}"/>'))


def table_indent(table, inches):
    tblPr = table._tbl.tblPr
    for el in tblPr.findall(qn("w:tblInd")):
        tblPr.remove(el)
    tblPr.append(parse_xml(f'<w:tblInd {nsdecls("w")} w:w="{int(inches * 1440)}" w:type="dxa"/>'))


def first_par(cell):
    return cell.paragraphs[0]


# ----------------------------------------------------------------------------- document
class Handout:
    def __init__(self, margins=0.6, size=SIZE, key=False):
        self.key = key
        self.doc = Document()
        self.size = size
        sec = self.doc.sections[0]
        sec.page_width, sec.page_height = Inches(8.5), Inches(11)
        for side in ("left_margin", "right_margin"):
            setattr(sec, side, Inches(margins))
        sec.top_margin = Inches(0.5)
        sec.bottom_margin = Inches(0.5)
        sec.header_distance = Inches(0.3)
        sec.footer_distance = Inches(0.3)
        self.width = 8.5 - 2 * margins
        st = self.doc.styles["Normal"]
        st.font.name = FONT
        st.font.size = Pt(size)
        st.font.color.rgb = BLACK
        st.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
        st.paragraph_format.space_after = Pt(0)
        st.paragraph_format.space_before = Pt(0)
        st.paragraph_format.line_spacing = 1.0
        self._first = False

    # --- basic blocks
    def para(self, text="", size=None, bold=False, italic=False, before=0, after=0, align=None, left=None,
             hanging=None, keep=False, container=None):
        if container is None:
            if self._first:
                p = self.doc.paragraphs[0]
                self._first = False
            else:
                p = self.doc.add_paragraph()
        else:
            p = container.add_paragraph() if container.paragraphs[0].text or \
                container.paragraphs[0]._p.findall(qn("m:oMath")) or len(container.paragraphs[0].runs) else \
                container.paragraphs[0]
        fmt(p, before, after, left, hanging, align, keep)
        add_rich(p, text, size or self.size, bold, italic)
        return p

    def space(self, inches, container=None):
        """Blank workspace of an exact height."""
        if container is None:
            p = self.doc.add_paragraph() if not self._first else self.doc.paragraphs[0]
            self._first = False
        else:
            p = container.add_paragraph()
        pf = p.paragraph_format
        pf.space_before = pf.space_after = Pt(0)
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(max(1, inches * 72))
        return p

    def page_break(self):
        p = self.doc.add_paragraph()
        fmt(p)
        p.add_run().add_break(WD_BREAK.PAGE)
        pf = p.paragraph_format
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = Pt(1)

    def _table(self, rows, cols, widths, bordered=False):
        if self._first:
            # keep a tiny paragraph before first table (Word requires a paragraph somewhere)
            p = self.doc.paragraphs[0]
            pf = p.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
            pf.line_spacing = Pt(1)
            self._first = False
        t = self.doc.add_table(rows=rows, cols=cols)
        t.alignment = WD_TABLE_ALIGNMENT.LEFT
        if bordered:
            # Word hangs the left border outside the margin by the cell's left padding; shift it back
            table_indent(t, bordered if isinstance(bordered, float) else 0.0833)
        set_widths(t, widths)
        return t

    # --- header
    def header(self, title, lesson, right="Name ____________________  Period ____"):
        t = self._table(1, 2, [self.width * 0.62, self.width * 0.38])
        table_no_borders(t)
        a, b = t.rows[0].cells
        for c in (a, b):
            cell_margins(c, 0, 50, 0, 0)
            cell_bottom_border(c, sz=12)
            c.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.BOTTOM
        p = first_par(a)
        add_rich(p, lesson + "  ", 10.5, italic=False)
        p.runs[-1].font.color.rgb = RGBColor(0x40, 0x40, 0x40)
        add_rich(p, title, 15, bold=True)
        p = first_par(b)
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        add_rich(p, right or "", 10)
        self.space(0.08)

    # --- boxes
    def box(self, text_lines, before=0.0, after=0.1, size=None, italic=False, height=None, pad=90):
        if before:
            self.space(before)
        t = self._table(1, 1, [self.width], bordered=True)
        table_borders(t, sz=8, inside=False)
        c = t.rows[0].cells[0]
        cell_margins(c, pad, pad, 120, 120)
        if height:
            row_height(t.rows[0], height)
        for k, line in enumerate(text_lines if isinstance(text_lines, list) else [text_lines]):
            p = first_par(c) if k == 0 else c.add_paragraph()
            fmt(p, after=2)
            add_rich(p, line, size or self.size, italic=italic)
        if after:
            self.space(after)
        return c

    def notes_box(self, title, height, after=0.12, lines=None, size=None):
        """QuickNotes box. With `lines`, the notes are printed (both student copy and key) and the box grows to fit."""
        t = self._table(1, 1, [self.width], bordered=True)
        table_borders(t, sz=8, inside=False)
        c = t.rows[0].cells[0]
        cell_margins(c, 60, 60, 120, 120)
        row_height(t.rows[0], height, exact=not lines)
        p = first_par(c)
        add_rich(p, title, self.size, bold=True)
        sz = size or self.size - 0.5
        for line in lines or []:
            bullet = line.startswith("- ")
            text = line[2:] if bullet else line
            q = c.add_paragraph()
            if bullet:
                fmt(q, before=1, left=0.2, hanging=0.15)
                add_rich(q, "•\t" + text, sz)
                q.paragraph_format.tab_stops.add_tab_stop(Inches(0.2))
            else:
                fmt(q, before=4)
                add_rich(q, text, sz)
        if after:
            self.space(after)
        return c

    def answer(self, container, lines, height, indent=0.3, width=None):
        """Student copy: blank space. Key: red answer text, then whatever space is left."""
        if not self.key or not lines:
            if height:
                self.space(height, container=container)
            return
        width = (width or self.width) - indent
        used = 0.0
        sz = self.size - 0.5
        for text in lines:
            if text.lstrip().startswith("$"):
                text = "\u2009" + text  # leading text run keeps Word from turning lone math into centered display math
            p = container.add_paragraph() if container is not None else self.doc.add_paragraph()
            fmt(p, before=2, left=indent)
            add_rich(p, text, sz, color=ANS)
            used += _est_lines(text, width, sz) * sz * 1.25 / 72 + 2 / 72
        if height - used > 0.03:
            self.space(height - used, container=container)

    def section(self, label, sub=None, before=0.06, after=0.04):
        if before:
            self.space(before)
        t = self._table(1, 1, [self.width])
        table_no_borders(t)
        c = t.rows[0].cells[0]
        cell_margins(c, 0, 30, 0, 0)
        cell_bottom_border(c, sz=6)
        p = first_par(c)
        p.paragraph_format.keep_with_next = True
        add_rich(p, label, self.size + 1, bold=True)
        if sub:
            add_rich(p, "   " + sub, self.size - 0.5, italic=True)
        if after:
            self.space(after)

    # --- problems
    def problem(self, num, lines, image=None, img_w=None, work=0.8, choices=None, choice_cols=1,
                layout="side", after=0.08, work_box=None, img_scale=1.0, valign="top", text_w=None,
                post=None, ans=None):
        """num: '1.' etc (or None). lines: list of rich strings; strings starting with 'a. ' get hanging indent.
        image: path. layout: 'side' (text left, image right) or 'stacked' (image under text, centered).
        ans: answer lines shown in the final workspace on the key."""
        lines = lines if isinstance(lines, list) else [lines]
        img_w = img_w or (self._natural_w(image) * img_scale if image else 0)
        tw = self.width
        if image and layout == "side":
            tw = text_w or (self.width - img_w - 0.15)
            t = self._table(1, 2, [tw, self.width - tw])
        else:
            t = self._table(1, 1, [self.width])
        table_no_borders(t)
        row_cant_split(t.rows[0])
        cells = t.rows[0].cells
        left = cells[0]
        for c in cells:
            cell_margins(c, 0, 0, 0, 0)
        self._problem_text(left, num, lines, width=tw)
        if choices:
            self._choices(left, choices, choice_cols, indent=0.3 if num else 0)
        if image and layout == "side":
            r = cells[1]
            r.vertical_alignment = (WD_CELL_VERTICAL_ALIGNMENT.CENTER if valign == "center"
                                    else WD_CELL_VERTICAL_ALIGNMENT.TOP)
            p = first_par(r)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run().add_picture(str(image), width=Inches(img_w))
        elif image:
            p = left.add_paragraph()
            fmt(p, before=3, after=3, align="center")
            p.add_run().add_picture(str(image), width=Inches(img_w))
        if post:
            for line in post:
                if isinstance(line, A):
                    self.answer(left, line.lines, line.height, indent=0.3 if num else 0, width=tw)
                else:
                    self._line(left, line, indent=0.3 if num else 0)
        if work_box:
            self._inner_box(left, work_box, indent=0.3 if num else 0)
        if work or ans:
            self.answer(left, ans, work, indent=0.3 if num else 0, width=tw)
        if after:
            self.space(after)
        return t

    def _natural_w(self, image, dpi=300):
        with Image.open(image) as im:
            return im.width / dpi

    def _line(self, cell, text, indent=0.3):
        p = cell.add_paragraph()
        m = re.match(r"^([a-z]\.|\[[A-F]\]|Step \d:)\s+(.*)$", text)
        if m:
            lab_w = 0.25 if len(m.group(1)) <= 3 else 0.5
            fmt(p, before=2, left=indent + lab_w, hanging=lab_w)
            add_rich(p, m.group(1) + "\t", self.size, bold=m.group(1).startswith("Step"))
            add_rich(p, m.group(2), self.size)
            p.paragraph_format.tab_stops.add_tab_stop(Inches(indent + lab_w))
        else:
            fmt(p, before=2, left=indent)
            add_rich(p, text, self.size)
        return p

    def _problem_text(self, cell, num, lines, width=None):
        for k, text in enumerate(lines):
            if isinstance(text, (int, float)):
                self.space(float(text), container=cell)
                continue
            if isinstance(text, A):
                self.answer(cell, text.lines, text.height, indent=0.3 if num else 0, width=width)
                continue
            if k == 0:
                p = first_par(cell)
                if num:
                    fmt(p, left=0.3, hanging=0.3)
                    add_rich(p, num + "\t", self.size, bold=True)
                    p.paragraph_format.tab_stops.add_tab_stop(Inches(0.3))
                add_rich(p, text, self.size)
            else:
                self._line(cell, text, indent=0.3 if num else 0)

    def _choices(self, cell, choices, cols, indent=0.3):
        if cols == 1:
            for lab, text in zip("ABCDEF", choices):
                p = cell.add_paragraph()
                fmt(p, before=3, left=indent + 0.4, hanging=0.4)
                add_rich(p, f"[{lab}]\t", self.size)
                add_rich(p, text, self.size)
                p.paragraph_format.tab_stops.add_tab_stop(Inches(indent + 0.4))
            return
        n = len(choices)
        rows = (n + cols - 1) // cols
        avail = cell.width.inches - indent if cell.width else self.width - indent
        t = cell.add_table(rows=rows, cols=cols)
        table_no_borders(t)
        set_widths(t, [avail / cols] * cols)
        table_indent(t, indent)
        for i, (lab, text) in enumerate(zip("ABCDEF", choices)):
            r, c = divmod(i, cols)
            cc = t.rows[r].cells[c]
            cell_margins(cc, 30, 30, 0, 40)
            p = first_par(cc)
            fmt(p, left=0.4, hanging=0.4)
            add_rich(p, f"[{lab}]\t", self.size)
            add_rich(p, text, self.size)
            p.paragraph_format.tab_stops.add_tab_stop(Inches(0.4))
        fmt(cell.paragraphs[-1])  # python-docx already added a paragraph after the nested table
        cell.paragraphs[-1].paragraph_format.line_spacing = Pt(2)

    def _inner_box(self, cell, height, indent=0.3):
        avail = (cell.width.inches if cell.width else self.width) - indent
        t = cell.add_table(rows=1, cols=1)
        table_borders(t, sz=6, inside=False)
        set_widths(t, [avail])
        table_indent(t, indent)
        row_height(t.rows[0], height, exact=True)
        p = cell.paragraphs[-1]  # python-docx already added a paragraph after the nested table
        fmt(p)
        p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        p.paragraph_format.line_spacing = Pt(4)
        return t.rows[0].cells[0]

    # --- grids
    def grid(self, rows, cols, fill, widths=None, borders=True, heights=None, after=0.08, pad=70):
        """fill(cell, r, c) populates each cell."""
        widths = widths or [self.width / cols] * cols
        t = self._table(rows, cols, widths, bordered=0.0625 if borders else False)
        if borders:
            table_borders(t, sz=6, inside=True)
        else:
            table_no_borders(t)
        for r in range(rows):
            row_cant_split(t.rows[r])
            if heights and heights[r]:
                row_height(t.rows[r], heights[r])
            for c in range(cols):
                cell = t.rows[r].cells[c]
                cell_margins(cell, pad, pad, 90, 90)
                fill(cell, r, c)
        if after:
            self.space(after)
        return t

    def cell_text(self, cell, text, bold=False, italic=False, align=None, size=None, first=True, before=0,
                  after=0):
        p = first_par(cell) if first and not cell.paragraphs[0].runs and \
            not cell.paragraphs[0]._p.findall(qn("m:oMath")) else cell.add_paragraph()
        fmt(p, before=before, after=after, align=align)
        add_rich(p, text, size or self.size, bold, italic)
        return p

    def fill_boxes(self, container, items, cols=None, label_w=None, box_w=1.3, height=0.36, indent=0.3,
                   size=None, row_gap=0.06):
        """Fill-in-the-blank row(s): each item is (label, answer). The label sits left of a bordered box where
        students write. The key prints the answer inside the box in red. `container` is a table cell or None.
        Label width defaults to the longest label, so a single box sits right next to its label."""
        cols = cols or len(items)
        if label_w is None:
            longest = max(len(re.sub(r"\\[A-Za-z]+|[${}]", "", lab)) for lab, _ in items)
            label_w = 0.25 + 0.085 * longest
        widths = []
        for _ in range(cols):
            widths += [label_w, box_w, 0.25]
        sz = size or self.size
        last = None
        for start in range(0, len(items), cols):
            chunk = items[start:start + cols]
            if container is None:
                t = self._table(1, 3 * cols, widths)
            else:
                t = container.add_table(rows=1, cols=3 * cols)
                set_widths(t, widths)
            table_no_borders(t)
            table_indent(t, indent)
            row = t.rows[0]
            row_cant_split(row)
            row_height(row, height)
            for c, (label, ans) in enumerate(chunk):
                lab, box = row.cells[3 * c], row.cells[3 * c + 1]
                for cc in (lab, box):
                    cell_margins(cc, 20, 20, 40, 40)
                    cc.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
                p = first_par(lab)
                p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
                add_rich(p, label, sz)
                tcPr = box._tc.get_or_add_tcPr()
                tcPr.append(parse_xml(_borders_xml("tcBorders", sz=6)))
                if self.key and ans:
                    q = first_par(box)
                    q.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    add_rich(q, ans, sz - 0.5, color=ANS)
            # gap paragraph after each row (Word also needs a paragraph after a nested table)
            if container is not None:
                p = container.paragraphs[-1]  # python-docx adds this paragraph after a nested table
                fmt(p)
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                p.paragraph_format.line_spacing = Pt(max(2, row_gap * 72))
            else:
                self.space(row_gap)
            last = t
        return last

    def frame(self, container, rows, indent=0.3, box_w=1.3, height=0.36, row_gap=0.05, size=None, width=None):
        """Sentence frame: each row is (before, answer, after) or (before, answer, after, box_w).
        Prints `before` [box] `after` on one line, left to right. The key puts `answer` in the box (red).
        Use it for scaffolded explanations so every blank is a real, labeled place to write."""
        sz = size or self.size
        total = (width or ((container.width.inches if container is not None and container.width else self.width))) \
            - indent
        per_in = 16.5 * 11 / sz  # rough Calibri characters per inch at this size

        def text_w(s):
            return _measure_rich(s, sz) + 0.2

        if container is None:
            self.space(0.02)  # keeps Word from merging this table into the table just above it
        last = None
        for row in rows:
            before, ans, after = row[:3]
            bw = row[3] if len(row) > 3 else box_w
            lw = text_w(before) if before else 0.05
            aw = max(0.3, total - lw - bw)
            widths = [lw, bw, aw]
            if container is None:
                t = self._table(1, 3, widths)
            else:
                t = container.add_table(rows=1, cols=3)
                set_widths(t, widths)
            table_no_borders(t)
            table_indent(t, indent)
            r = t.rows[0]
            row_cant_split(r)
            row_height(r, height)
            lab, box, tail = r.cells
            for cc in (lab, box, tail):
                cell_margins(cc, 10, 10, 30, 30)
                cc.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if after and after[0].isalnum():
                cell_margins(tail, 10, 10, 80, 30)
            if before:
                add_rich(first_par(lab), before, sz)
            if after:
                add_rich(first_par(tail), after, sz)
            box._tc.get_or_add_tcPr().append(parse_xml(_borders_xml("tcBorders", sz=6)))
            if self.key and ans:
                q = first_par(box)
                q.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_rich(q, ans, sz - 0.5, color=ANS)
            if container is not None:
                p = container.paragraphs[-1]  # python-docx adds this paragraph after a nested table
                fmt(p)
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                p.paragraph_format.line_spacing = Pt(max(2, row_gap * 72))
            else:
                self.space(row_gap)
            last = t
        return last

    def key_image(self, container, image, width, align="center", before=2, after=2):
        """Answer figure (key only), e.g. a labeled sample drawing."""
        if not self.key:
            return None
        if container is None:
            p = self.doc.add_paragraph()
        else:
            empty = not container.paragraphs[0].runs and not container.paragraphs[0]._p.findall(qn("m:oMath"))
            p = first_par(container) if empty else container.add_paragraph()
        fmt(p, before=before, after=after, align=align)
        p.add_run().add_picture(str(image), width=Inches(width))
        return p

    def key_note(self, cell, text, size=None, align=None, before=2):
        """Red answer text inside a table cell; key only."""
        if not self.key:
            return None
        empty = not cell.paragraphs[0].runs and not cell.paragraphs[0]._p.findall(qn("m:oMath"))
        p = first_par(cell) if empty else cell.add_paragraph()
        fmt(p, before=before, align=align)
        if text.lstrip().startswith("$") and align is None:
            text = "\u2009" + text
        add_rich(p, text, size or self.size - 0.5, color=ANS)
        return p

    def cell_image(self, cell, image, width, align="center", before=2, after=2):
        p = cell.add_paragraph() if (cell.paragraphs[0].runs or cell.paragraphs[0]._p.findall(qn("m:oMath"))) \
            else first_par(cell)
        fmt(p, before=before, after=after, align=align)
        p.add_run().add_picture(str(image), width=Inches(width))
        return p

    def footer_text(self, text):
        sec = self.doc.sections[0]
        p = sec.footer.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        r = p.add_run(text)
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    def save(self, path):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(path))
        return path


# ----------------------------------------------------------------------------- practice-set grid
def table_inside_only(table, sz=6):
    tblPr = table._tbl.tblPr
    for el in tblPr.findall(qn("w:tblBorders")):
        tblPr.remove(el)
    inner = ('<w:top w:val="nil"/><w:left w:val="nil"/><w:bottom w:val="nil"/><w:right w:val="nil"/>'
             f'<w:insideH w:val="single" w:sz="{sz}" w:space="0" w:color="000000"/>'
             f'<w:insideV w:val="single" w:sz="{sz}" w:space="0" w:color="000000"/>')
    tblPr.append(parse_xml(f"<w:tblBorders {nsdecls('w')}>{inner}</w:tblBorders>"))


def cell_problem(h, cell, num, lines, image=None, img_w=None, choices=None, choice_cols=1, work=0.6,
                 img_align="center", post=None, ans=None):
    """Stacked problem inside a grid cell: text, image, choices, more text, workspace."""
    cw = cell.width.inches if cell.width else h.width / 2
    h._problem_text(cell, num, lines, width=cw)
    if image:
        w = img_w or h._natural_w(image)
        p = cell.add_paragraph()
        fmt(p, before=3, after=3, align=img_align, left=0.3 if img_align != "center" else None)
        p.add_run().add_picture(str(image), width=Inches(w))
    if choices:
        h._choices(cell, choices, choice_cols, indent=0.3)
    for line in post or []:
        if isinstance(line, (int, float)):
            h.space(float(line), container=cell)
        elif isinstance(line, A):
            h.answer(cell, line.lines, line.height, width=cw)
        else:
            h._line(cell, line, indent=0.3)
    if work or ans:
        h.answer(cell, ans, work, width=cw)


def practice_grid(h, rows, cols=2, heights=None):
    """Returns table whose cells are filled by caller; inside borders only (like the original sets)."""
    widths = [h.width / cols] * cols
    t = h._table(rows, cols, widths)
    table_inside_only(t)
    for r in range(rows):
        row_cant_split(t.rows[r])
        if heights and heights[r]:
            row_height(t.rows[r], heights[r])
        for c in range(cols):
            cell = t.rows[r].cells[c]
            cell_margins(cell, 80, 100, 90 if c else 0, 0 if c == cols - 1 else 90)
    return t


def key_table(h, items, cols=4, size=9.5):
    """Answer key to selected problems: list of (num, rich text)."""
    rows = (len(items) + cols - 1) // cols
    t = h._table(rows, cols, [h.width / cols] * cols)
    table_no_borders(t)
    for i, (n, txt) in enumerate(items):
        r, c = divmod(i, cols)
        cell = t.rows[r].cells[c]
        cell_margins(cell, 20, 20, 0, 60)
        p = first_par(cell)
        fmt(p, left=0.25, hanging=0.25)
        add_rich(p, f"{n}.\t", size, bold=True)
        add_rich(p, txt, size)
        p.paragraph_format.tab_stops.add_tab_stop(Inches(0.25))
    return t


# ----------------------------------------------------------------------------- markdown -> docx (teacher guides)
def _md_inline(text):
    return text.replace("`", "")


def md_to_doc(h, md, size=10.5):
    lines = md.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        s = line.strip()
        if not s or s == "---":
            i += 1
            continue
        if s.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                block.append(lines[i].strip())
                i += 1
            rows = [[c.strip() for c in r.strip("|").split("|")] for r in block if not re.match(r"^\|[-| :]+\|$", r)]
            ncol = max(len(r) for r in rows)
            t = h._table(len(rows), ncol, [h.width / ncol] * ncol, bordered=0.0625)
            table_borders(t, sz=4, inside=True)
            for r, row in enumerate(rows):
                for c in range(ncol):
                    cell = t.rows[r].cells[c]
                    cell_margins(cell, 30, 30, 90, 90)
                    p = first_par(cell)
                    add_rich(p, _md_inline(row[c] if c < len(row) else ""), size - 0.5, bold=(r == 0))
            h.space(0.06)
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            level = len(m.group(1))
            txt = _md_inline(m.group(2))
            sz = {1: 16, 2: 14, 3: 12.5, 4: 11.5}.get(level, 11)
            p = h.doc.add_paragraph()
            fmt(p, before=10 if level <= 2 else 6, after=3, keep=True)
            add_rich(p, txt, sz, bold=True)
            if level <= 2:
                pPr = p._p.get_or_add_pPr()
                pPr.append(parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="1" '
                                     f'w:color="000000"/></w:pBdr>'))
            i += 1
            continue
        indent = (len(line) - len(line.lstrip(" "))) // 2
        m = re.match(r"^(-|\d+\.|[a-z]\.)\s+(.*)$", s)
        if m:
            marker = "•" if m.group(1) == "-" else m.group(1)
            txt = m.group(2)
            # continuation lines (indented, not a new marker)
            while i + 1 < len(lines) and lines[i + 1].startswith(" ") and lines[i + 1].strip() and \
                    not re.match(r"^\s*(-|\d+\.|[a-z]\.)\s+", lines[i + 1]):
                i += 1
                txt += " " + lines[i].strip()
            left = 0.25 + 0.25 * indent
            p = h.doc.add_paragraph()
            fmt(p, after=2, left=left, hanging=0.25)
            add_rich(p, marker + "\t", size)
            add_rich(p, _md_inline(txt), size)
            p.paragraph_format.tab_stops.add_tab_stop(Inches(left))
            i += 1
            continue
        # paragraph: join following plain lines
        txt = s
        while i + 1 < len(lines) and lines[i + 1].strip() and not re.match(
                r"^\s*(#|-|\||\d+\.\s|[a-z]\.\s|---)", lines[i + 1]):
            i += 1
            txt += " " + lines[i].strip()
        p = h.doc.add_paragraph()
        fmt(p, after=4)
        add_rich(p, _md_inline(txt), size)
        i += 1

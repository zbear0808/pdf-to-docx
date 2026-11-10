"""LessonSpec -> student handout, lesson key, practice, practice key, teacher guide (DOCX)."""
from __future__ import annotations

from pathlib import Path

from . import docbuilder as db
from .docbuilder import Handout
from .spec import Item, LessonSpec, Part, UnitSpec, as_list

NAME_LINE = "Name ____________________  Period ____"
SECTION_TITLES = {"warmup": ("Warm-up", "on your own"), "together": ("Together", None),
                  "partner": ("With a partner", None), "cyu": ("Check your understanding", None),
                  "exit": ("Exit ticket", None), "plain": (None, None)}


class Figures:
    """Resolves a figure reference to a PNG: registered figure name (from figures.render_all) or asset path."""

    def __init__(self, unit: UnitSpec, rendered: dict | None = None):
        self.unit, self.rendered = unit, rendered or {}

    def get(self, ref: str | None, key: bool) -> Path | None:
        if not ref:
            return None
        if ref in self.rendered:
            r = self.rendered[ref]
            return r["key"] if key and r.get("key") else r["student"]
        p = (self.unit.dir / ref).resolve()
        if not p.exists():
            raise FileNotFoundError(f"figure '{ref}' is not a registered figure or a file under {self.unit.dir}")
        return p

    def has_key_layer(self, ref: str | None) -> bool:
        return bool(ref and self.rendered.get(ref, {}).get("key"))


def _num(it: Item) -> str | None:
    return f"{it.n}." if it.n else None


def _explicit(model, field: str) -> bool:
    return field in model.model_fields_set


def _cell_w(cell, h: Handout) -> float:
    return cell.width.inches if cell.width else h.width


def _body(h: Handout, cell, it: Item | Part, scale: float, indent: float, width: float):
    """Fill-ins, frames, write-in box, parts, then the answer workspace."""
    answer = as_list(it.answer)
    boxed = bool(it.fill or it.frame or getattr(it, "box", None))
    if isinstance(it, Part) and it.choices:
        h._choices(cell, it.choices, it.choice_cols, indent=indent + 0.25)
    if it.fill:
        h.fill_boxes(cell, [tuple(r) for r in it.fill], cols=it.fill_cols or 1, box_w=it.box_w,
                     indent=indent + 0.25 if isinstance(it, Part) else indent, height=0.38, row_gap=0.08)
    if it.frame:
        rows = [tuple(r) for r in it.frame]
        h.frame(cell, rows, indent=indent + 0.25, box_w=it.frame_box_w, height=0.36, row_gap=0.06)
    if getattr(it, "box", None):
        inner = h._inner_box(cell, it.box * scale, indent=indent)
        for a in answer:
            h.key_note(inner, a, size=10)
        answer = []
    work = it.work if (_explicit(it, "work") or not boxed) else 0
    if getattr(it, "parts", None) and not _explicit(it, "work"):
        work = 0
    if answer or work:
        h.answer(cell, answer, work * scale, indent=indent, width=width)
    for p in getattr(it, "parts", []):
        h._line(cell, f"{p.label} {p.prompt}{_pts(p.points)}", indent=indent)
        _body(h, cell, p, scale, indent, width)


def _draw(h: Handout, it: Item, figs: Figures, scale: float):
    d = it.draw
    t = h._table(1, 2, [d.steps_w, h.width - d.steps_w])
    db.table_no_borders(t)
    db.row_cant_split(t.rows[0])
    a, b = t.rows[0].cells
    for c in (a, b):
        db.cell_margins(c, 0, 0, 0, 60)
    h._problem_text(a, _num(it), as_list(it.prompt))
    box = h._inner_box(b, max(2.2, d.height * scale), indent=0.1, exact=False)  # grows to fit the key figure
    kf = figs.get(d.key_figure or it.key_figure or it.figure, key=True)
    if h.key and kf:
        h.key_image(box, kf, d.key_fig_w, before=4)
    if d.key_note:
        h.key_note(box, d.key_note, size=9.5)
    for a_ in as_list(it.answer):
        h.key_note(box, a_, size=9.5)
    h.space(it.after + 0.08)


def _columns(h: Handout, it: Item):
    c = it.columns

    def fill(cell, r, k):
        h.cell_text(cell, c.headers[k], bold=not c.italic, italic=c.italic, size=10)
        for t in (c.answers[k] if k < len(c.answers) else []):
            h.key_note(cell, t, size=9.5)
    h.grid(1, len(c.headers), fill, heights=[c.height], after=0.04, pad=50)


def _table(h: Handout, it: Item):
    tb = it.table
    n = len(tb.header)
    ws = [tb.first_w] + [(h.width - 0.3 - tb.first_w) / (n - 1)] * (n - 1)

    def fill(cell, r, k):
        if r == 0:
            h.cell_text(cell, tb.header[k], align="center" if k else None, size=10 if k == 0 else 11)
        elif k == 0:
            h.cell_text(cell, tb.row_label, size=10)
        else:
            h.key_note(cell, tb.answers[k - 1], size=11, align="center", before=4)
    t = h.grid(2, n, fill, widths=ws, heights=[None, tb.height], after=0.0, pad=50)
    db.table_indent(t, 0.3625)


def _pts(p) -> str:
    if p is None:
        return ""
    return f" ({p:g} pt{'s' if p != 1 else ''})"


def _item(h: Handout, it: Item, figs: Figures, scale: float):
    if it.draw:
        return _draw(h, it, figs, scale)
    img = figs.get(it.key_figure if (h.key and it.key_figure) else it.figure, h.key)
    lines = as_list(it.prompt)
    if it.points is not None and lines:
        lines = [lines[0] + _pts(it.points)] + lines[1:]
    t = h.problem(_num(it), lines, image=img, img_w=it.fig_w, work=0, after=0, choices=it.choices,
                  choice_cols=it.choice_cols, layout=it.layout)
    cell = t.rows[0].cells[0]
    _body(h, cell, it, scale, 0.3 if it.n else 0, _cell_w(cell, h))
    if it.columns:
        _columns(h, it)
    if it.table:
        _table(h, it)
    h.space(it.after)


def _section_sub(s) -> str | None:
    if s.sub is not None:
        return s.sub
    default = SECTION_TITLES[s.kind][1]
    nums = [int(i.n) for i in s.items if i.n and i.n.isdigit()]
    if s.kind in ("together", "partner") and nums:
        return f"Problems {min(nums)}-{max(nums)}" if len(nums) > 1 else f"Problem {nums[0]}"
    return default


def render_handout(unit: UnitSpec, lesson: LessonSpec, key: bool, figs: Figures, out: Path,
                   scale: float = 1.0) -> Path:
    h = Handout(key=key)
    lesson_doc = lesson.doc_type == "lesson"
    label = f"Lesson {lesson.id}" if lesson_doc else ""
    h.footer_text(unit.footer(lesson.id, doc_type=lesson.doc_type) + ("  |  Key" if key else ""))
    if key:
        right = "Lesson key" if lesson_doc else "Key"
    elif lesson.header_right:
        right = lesson.header_right
    elif lesson.doc_type == "assessment":
        total = lesson.total_points or lesson.points
        right = "Name ______________  Per ___" + (f"  Score ___ / {total:g}" if total else "")
    else:
        right = NAME_LINE
    h.header(lesson.title, label, right=right)
    if lesson.framing:
        h.box(lesson.framing, after=0.04)
    if lesson.directions:
        h.para(f"**{lesson.directions}**", size=10.5, after=4)
    if lesson.materials:
        h.para(f"*Materials:* {lesson.materials}", size=10, after=2)
    broke = False
    for s in lesson.sections:
        if s.kind == "notes":
            if not broke:
                h.page_break()
            broke = False
            h.header(lesson.notes_title or lesson.title, label, right=right)
            h.notes_box("QuickNotes", lesson.notes_height, lines=lesson.quicknotes)
            continue
        if s.page_break_before and not broke:
            h.page_break()
        title = s.title or SECTION_TITLES[s.kind][0]
        if title:
            h.section(title, _section_sub(s), before=0 if (s.page_break_before or broke) else 0.06)
        broke = False
        if s.box:
            h.box(as_list(s.box), size=9.5, after=0.08, pad=50)
        if s.intro:
            h.para(s.intro, after=4)
        for it in s.items:
            _item(h, it, figs, scale)
            broke = False
            if it.page_break_after:
                h.page_break()
                broke = True
    return h.save(out)


def _cell_item(h: Handout, cell, it: Item, figs: Figures, scale: float):
    img = figs.get(it.key_figure if (h.key and it.key_figure) else it.figure, h.key)
    db.cell_problem(h, cell, _num(it), as_list(it.prompt), image=img, img_w=it.fig_w, choices=it.choices,
                    choice_cols=it.choice_cols, work=0)
    _body(h, cell, it, scale, 0.3, _cell_w(cell, h))


def render_practice(unit: UnitSpec, lesson: LessonSpec, key: bool, figs: Figures, out: Path,
                    scale: float = 1.0) -> Path:
    pr = lesson.practice
    h = Handout(size=pr.font_size, key=key)
    h.footer_text(unit.footer(lesson.id, "Practice") + ("  |  Key" if key else ""))
    h.header(pr.title, f"Lesson {lesson.id}", right="Practice key" if key else NAME_LINE)
    blocks, cur = [], []
    for row in pr.rows:
        # a new block on a heading, a page break, or a change in column count (a 1-cell row after 2-cell rows
        # gets the full width instead of half)
        if cur and (row.heading or row.page_break_before or len(row.cells) != len(cur[-1].cells)):
            blocks.append(cur)
            cur = []
        cur.append(row)
    if cur:
        blocks.append(cur)
    for block in blocks:
        first = block[0]
        if first.page_break_before:
            h.page_break()
        if first.heading:
            h.section(first.heading, before=0.1)
        cols = max(len(r.cells) for r in block)
        t = db.practice_grid(h, len(block), cols=cols)
        for r, row in enumerate(block):
            for c, it in enumerate(row.cells):
                _cell_item(h, t.rows[r].cells[c], it, figs, scale)
    if not key and pr.selected:
        h.section("Answers to selected problems", before=0.1)
        db.key_table(h, [tuple(x) for x in pr.selected], cols=4)
    return h.save(out)


# ----------------------------------------------------------------------------- teacher guide
def _answers_md(it: Item | Part, prefix: str) -> list[str]:
    bits = []
    if isinstance(it, Item) and it.table:
        bits.append(", ".join(f"{a} $\\to$ {b}" for a, b in zip(it.table.header[1:], it.table.answers)))
    if isinstance(it, Item) and it.columns:
        for head, ans in zip(it.columns.headers, it.columns.answers):
            bits.append(f"*{head}* " + "; ".join(ans))
    for r in it.fill or []:
        bits.append(f"{r[0]} {r[1]}")
    for r in it.frame or []:
        tail = str(r[2]) if len(r) > 2 and r[2] else ""
        if tail and tail[0].isalnum():
            tail = " " + tail
        bits.append(f"{r[0]} **{r[1]}**{tail}")
    bits += as_list(it.answer)
    if isinstance(it, Item) and it.draw:
        bits += [b for b in (it.draw.key_note,) if b]
        bits.append("(labeled sample drawing on the lesson key)")
    text = ""
    for b in bits:
        b = b.strip()
        if text:
            text += " " if text.endswith((".", "?", "!", ":", ")")) else "; "
        text += b
    parts = [ln for p in getattr(it, "parts", []) for ln in _answers_md(p, f"   {p.label}")]
    if bits:
        return [f"{prefix} {text}"] + parts
    if parts:  # no stem answer: keep the item number on the first part's line
        return [f"{prefix} {parts[0].strip()}"] + parts[1:]
    return []


def guide_markdown(lesson: LessonSpec) -> str:
    out = ["## Answer key: student handout" if lesson.doc_type == "lesson" else "## Answer key"]
    for s in lesson.sections:
        if s.kind == "notes":
            out += ["### QuickNotes (printed on the handout and the key)"] + lesson.quicknotes
            continue
        title = s.title or SECTION_TITLES[s.kind][0]
        if title:
            out.append(f"### {title}")
        for it in s.items:
            out += _answers_md(it, f"{it.n}." if it.n else "-")
    if lesson.practice:
        out.append("## Practice problems: answer key")
        for row in lesson.practice.rows:
            for it in row.cells:
                out += _answers_md(it, f"{it.n}.")
    if lesson.plan:
        out += ["## Lesson plan" if lesson.doc_type == "lesson" else "## Notes for the teacher", lesson.plan]
    if lesson.guide_notes:
        out += [lesson.guide_notes]
    return "\n".join(out) + "\n"


def render_guide(unit: UnitSpec, lesson: LessonSpec, out: Path) -> Path:
    h = Handout(size=10.5)
    h.footer_text(unit.footer(lesson.id, doc_type=lesson.doc_type) + "  |  Teacher guide")
    label = f"Lesson {lesson.id}" if lesson.doc_type == "lesson" else ""
    h.header(lesson.notes_title or lesson.title, label, right="Teacher guide")
    db.md_to_doc(h, guide_markdown(lesson))
    return h.save(out)


def outputs(unit: UnitSpec, lesson: LessonSpec) -> dict[str, Path]:
    """Lessons: output/Lesson X/ with five files. Assessments: output/Assessments/<stem>.docx + Key (+ guide if
    there are teacher notes). Reference sheets: output/Reference/<stem>.docx only."""
    if lesson.doc_type == "lesson":
        d = unit.dir / "output" / f"Lesson {lesson.id}"
        names = {"handout": "Student Handout", "key": "Lesson Key", "practice": "Practice Problems",
                 "practice_key": "Practice Key", "guide": "Teacher Guide"}
        out = {k: d / f"Lesson {lesson.id} {v}.docx" for k, v in names.items()}
        if not lesson.practice:
            out.pop("practice"), out.pop("practice_key")
        return out
    title = lesson.id
    if lesson.doc_type == "reference":
        return {"handout": unit.dir / "output" / "Reference" / f"{title}.docx"}
    d = unit.dir / "output" / "Assessments"
    out = {"handout": d / f"{title}.docx", "key": d / f"{title} Key.docx"}
    if lesson.plan or lesson.guide_notes:
        out["guide"] = d / f"{title} Teacher Notes.docx"
    return out


def render_lesson(unit: UnitSpec, lesson: LessonSpec, figs: Figures, scale: dict | None = None) -> dict[str, Path]:
    scale = scale or {}
    o = outputs(unit, lesson)
    render_handout(unit, lesson, False, figs, o["handout"], scale.get("handout", 1.0))
    if "key" in o:
        render_handout(unit, lesson, True, figs, o["key"], scale.get("handout", 1.0))
    if "practice" in o:
        render_practice(unit, lesson, False, figs, o["practice"], scale.get("practice", 1.0))
        render_practice(unit, lesson, True, figs, o["practice_key"], scale.get("practice", 1.0))
    if "guide" in o:
        render_guide(unit, lesson, o["guide"])
    return o

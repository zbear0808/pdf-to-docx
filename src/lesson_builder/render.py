"""LessonSpec -> student handout, lesson key, practice, practice key, teacher guide (DOCX)."""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image

from . import docbuilder as db
from .check import draw_key_width
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


def _work(it: Item | Part) -> float:
    """Explicit `work` wins. Otherwise 0 when the item has its own place to write, 0.2 for choices."""
    if _explicit(it, "work"):
        return it.work
    if it.fill or it.frame or any(getattr(it, f, None) for f in ("box", "parts", "table", "columns", "draw")):
        return 0
    return 0.2 if it.choices else it.work


def _answer_lines(it: Item | Part) -> list[str]:
    """Answer lines; with `key` and an answer that doesn't start with '[', the key letter goes first."""
    lines = as_list(it.answer)
    if it.key and not (lines and lines[0].lstrip().startswith("[")):
        lines = [f"[{it.key}] {lines[0]}".rstrip()] + lines[1:] if lines else [f"[{it.key}]"]
    return lines


def _rubric_lines(it: Item | Part) -> list[str]:
    return [f"{r.level}: {r.desc}" for r in it.rubric]


def _prompt_lines(it: Item, points: bool = True) -> list:
    """Prompt lines, "(2 pts)" after the first line, then numbered steps."""
    lines = as_list(it.prompt)
    if points and it.points is not None and lines:
        lines = [lines[0] + _pts(it.points)] + lines[1:]
    return lines + [f"Step {k}: {s}" for k, s in enumerate(it.steps, 1)]


def _body(h: Handout, cell, it: Item | Part, scale: float, indent: float, width: float, where: str = "item"):
    """Fill-ins, frames, write-in box, parts, then the answer workspace (answer and rubric on the key).
    Workspace that grows to hold the key's answer is noted in h.grown as (where, field, set, needed)."""
    answer = _answer_lines(it)
    if isinstance(it, Part) and it.choices:
        h._choices(cell, it.choices, it.choice_cols, indent=indent + 0.25)
    if it.fill:
        h.fill_boxes(cell, [tuple(r) for r in it.fill], cols=it.fill_cols or 1, box_w=it.box_w,
                     indent=indent + 0.25 if isinstance(it, Part) else indent, height=0.38, row_gap=0.08)
    if it.frame:
        rows = [tuple(r) for r in it.frame]
        h.frame(cell, rows, indent=indent + 0.25, box_w=it.frame_box_w, height=0.36, row_gap=0.06)
    if getattr(it, "box", None):
        room = width - indent - 0.15
        need = db.answer_height(answer, room, 10) + db.answer_height(_rubric_lines(it), room, 9)
        if need > it.box * scale + 0.02:
            h.grown.append((where, "box", it.box * scale, need))
        inner = h._inner_box(cell, max(it.box * scale, need), indent=indent)
        for a in answer:
            h.key_note(inner, a, size=10)
        for a in _rubric_lines(it):
            h.key_note(inner, a, size=9)
        answer = []
    else:
        answer += _rubric_lines(it)
    work = _work(it)
    if answer or work:
        used = h.answer(cell, answer, work * scale, indent=indent, width=width)
        if answer and used > work * scale + 0.05:
            h.grown.append((where, "work", work * scale, used))
    for p in getattr(it, "parts", []):
        h._line(cell, f"{p.label} {p.prompt}{_pts(p.points)}", indent=indent)
        _body(h, cell, p, scale, indent, width, f"{where} part {p.label}")


def _draw(h: Handout, it: Item, figs: Figures, scale: float):
    d = it.draw
    t = h._table(1, 2, [d.steps_w, h.width - d.steps_w])
    db.table_no_borders(t)
    db.row_cant_split(t.rows[0])
    a, b = t.rows[0].cells
    for c in (a, b):
        db.cell_margins(c, 0, 0, 0, 60)
    h._problem_text(a, _num(it), _prompt_lines(it, points=False))
    kf = figs.get(d.key_figure or it.key_figure or it.figure, key=True)
    kw = draw_key_width(d, figs.rendered, d.key_figure or it.key_figure or it.figure)
    room = h.width - d.steps_w - 0.25
    need = 0.12 + db.answer_height([d.key_note] if d.key_note else [], room, 9.5)
    need += db.answer_height(_answer_lines(it), room, 9.5) + db.answer_height(_rubric_lines(it), room, 9)
    if kf:
        with Image.open(kf) as im:
            kw = kw or im.width / 300
            need += kw * im.height / im.width + 4 / 72
    if need > max(2.2, d.height * scale) + 0.02:
        h.grown.append((f"item {it.n or '(unnumbered)'}", "draw.height", max(2.2, d.height * scale), need))
    # one exact height on both copies, tall enough for the key drawing, so later items line up
    box = h._inner_box(b, max(2.2, d.height * scale, need), indent=0.1)
    if h.key and kf:
        h.key_image(box, kf, kw, before=4)
    if d.key_note:
        h.key_note(box, d.key_note, size=9.5)
    for a_ in _answer_lines(it):
        h.key_note(box, a_, size=9.5)
    for a_ in _rubric_lines(it):
        h.key_note(box, a_, size=9)
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
    t = h.problem(_num(it), _prompt_lines(it), image=img, img_w=it.width, work=0, after=0, choices=it.choices,
                  choice_cols=it.choice_cols, layout=it.layout)
    cell = t.rows[0].cells[0]
    _body(h, cell, it, scale, 0.3 if it.n else 0, _cell_w(cell, h), f"item {it.n or '(unnumbered)'}")
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
                   scale: float = 1.0, grown: list | None = None) -> Path:
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
            h.notes_box("QuickNotes", lesson.notes_height, lines=quicknote_lines(lesson),
                        image=figs.get(lesson.notes_figure, key), img_w=lesson.notes_fig_w)
            continue
        if s.page_break_before and not broke:
            h.page_break()
        title = s.title or SECTION_TITLES[s.kind][0]
        if title:
            h.section(title, _section_sub(s), before=0 if (s.page_break_before or broke) else 0.06)
        broke = False
        if s.box:
            h.box(as_list(s.box), size=9.5, after=0.08, pad=50)
        if s.bank:
            h.box("  |  ".join(s.bank), size=9.5, after=0.08, pad=50)
        if s.intro:
            h.para(s.intro, after=4)
        if s.columns == 2:
            broke = _two_columns(h, s.items, figs, scale)
            continue
        for it in s.items:
            _item(h, it, figs, scale)
            broke = False
            if it.page_break_after:
                h.page_break()
                broke = True
    if grown is not None:
        grown.extend(h.grown)
    return h.save(out)


def _cell_item(h: Handout, cell, it: Item, figs: Figures, scale: float, points: bool = False, where: str = "item"):
    img = figs.get(it.key_figure if (h.key and it.key_figure) else it.figure, h.key)
    db.cell_problem(h, cell, _num(it), _prompt_lines(it, points), image=img, img_w=it.width, choices=it.choices,
                    choice_cols=it.choice_cols, work=0)
    _body(h, cell, it, scale, 0.3, _cell_w(cell, h), f"{where} {it.n or '(unnumbered)'}")


def _two_columns(h: Handout, items: list[Item], figs: Figures, scale: float) -> bool:
    """Section `columns: 2`: items two per row in a borderless grid. draw/table/columns items take the full
    width. Returns True if the last item ended with a page break."""
    run, broke = [], False

    def flush():
        if not run:
            return
        t = db.practice_grid(h, (len(run) + 1) // 2, cols=2)
        db.table_no_borders(t)
        for k, it in enumerate(run):
            _cell_item(h, t.rows[k // 2].cells[k % 2], it, figs, scale, points=True)
        h.space(0.08)
        run.clear()

    for it in items:
        broke = False
        if it.draw or it.table or it.columns:
            flush()
            _item(h, it, figs, scale)
        else:
            run.append(it)
        if it.page_break_after:
            flush()
            h.page_break()
            broke = True
    flush()
    return broke


def render_practice(unit: UnitSpec, lesson: LessonSpec, key: bool, figs: Figures, out: Path,
                    scale: float = 1.0, grown: list | None = None) -> Path:
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
                _cell_item(h, t.rows[r].cells[c], it, figs, scale, where="practice item")
    sel = selected_answers(lesson)
    if not key and sel:
        h.section("Answers to selected problems", before=0.1)
        db.key_table(h, sel, cols=4)
    if grown is not None:
        grown.extend(h.grown)
    return h.save(out)


_MC = re.compile(r"^\s*\[([A-J](?:\s*,\s*[A-J])*)\]")


def _short(text: str, limit: int = 60) -> str:
    """Long answers keep their first sentence (a stop outside $...$ followed by a space)."""
    text = text.strip()
    if len(text) <= limit:
        return text
    for m in re.finditer(r"[.!?;](?=\s)", text):
        head = text[:m.start() + (m.group(0) != ";")]
        if len(head) >= 3 and head.count("$") % 2 == 0:
            return head
    return text


def _derive(it: Item | Part) -> str:
    """Short answer for the selected-answers table: MC letter(s), first answer line, fill/frame answers,
    or "a. .. b. .." from the parts."""
    if it.no_answer:
        return ""
    lines = as_list(it.answer)
    if it.key:
        return it.key
    m = _MC.match(lines[0]) if lines else None
    if m:
        return re.sub(r"\s*,\s*", ", ", m.group(1))
    if lines:
        return _short(lines[0])
    if it.fill or it.frame:
        return ", ".join(str(r[1]) for r in (it.fill or []) + (it.frame or []))
    return "  ".join(f"{p.label} {a}" for p in getattr(it, "parts", []) if (a := _derive(p)))


def _lookup(cells: list[Item], num: str) -> str:
    for it in cells:
        if it.n == num:
            return _derive(it)
        for p in it.parts:
            if it.n and f"{it.n}{p.label.rstrip('.').strip()}" == num:
                return _derive(p)
    return ""


def selected_answers(lesson: LessonSpec) -> list[tuple[str, str]]:
    """practice.selected as (number, answer) pairs. "auto": every numbered cell; bare numbers ("4", or "6a" for
    a part): those cells; [n, answer] pairs as written. Derived answers that come out empty are dropped."""
    pr = lesson.practice
    if not pr or not pr.selected:
        return []
    cells = [it for r in pr.rows for it in r.cells]
    if pr.selected == "auto":
        return [(it.n, a) for it in cells if it.n and (a := _derive(it))]
    out = []
    for x in pr.selected:
        if isinstance(x, (list, tuple)):
            out.append(tuple(str(v) for v in x))
        elif a := _lookup(cells, str(x)):
            out.append((str(x), a))
    return out


# ----------------------------------------------------------------------------- teacher guide
def _join(bits) -> str:
    """Join answer pieces: a space after a piece that ends a sentence, '; ' otherwise. Markup at the end
    (**, *, $) doesn't hide the punctuation, so 'half as long.**' + 'Next' never becomes '.; '."""
    text = ""
    for b in bits:
        b = str(b).strip()
        if not b:
            continue
        if text:
            end = re.sub(r"[*$\s]+$", "", text)
            text += " " if end.endswith((".", "?", "!", ":", ";", ")")) else "; "
        text += b
    return text


def _answers_md(it: Item | Part, prefix: str) -> list[str]:
    bits = []
    if isinstance(it, Item) and it.table:
        bits.append(", ".join(f"{a} $\\to$ {b}" for a, b in zip(it.table.header[1:], it.table.answers)))
    if isinstance(it, Item) and it.columns:
        for head, ans in zip(it.columns.headers, it.columns.answers):
            bits.append(f"*{head}* " + _join(ans))
    for r in it.fill or []:
        bits.append(f"{r[0]} {r[1]}")
    for r in it.frame or []:
        tail = str(r[2]) if len(r) > 2 and r[2] else ""
        if tail and tail[0] not in ".,;:!?)'’":
            tail = " " + tail
        bits.append(f"{r[0]} **{r[1]}**{tail}")
    bits += _answer_lines(it)
    if isinstance(it, Item) and it.draw:
        bits += [b for b in (it.draw.key_note,) if b]
        bits.append("(labeled sample drawing on the lesson key)")
    text = _join(bits)
    if it.scoring == "epi":
        text = f"{text} (scored E/P/I)".strip()
    pad = " " * (len(prefix) - len(prefix.lstrip()) + 2)
    rubric = [f"{pad}- Rubric {ln}" for ln in _rubric_lines(it)]
    if rubric and not text:
        text = "Rubric:"
    parts = [ln for p in getattr(it, "parts", []) for ln in _answers_md(p, f"   {p.label}")]
    if text or bits:
        return [f"{prefix} {text}"] + rubric + parts
    if parts:  # no stem answer: keep the item number on the first part's line
        return [f"{prefix} {parts[0].strip()}"] + parts[1:]
    return []


def quicknote_lines(lesson: LessonSpec) -> list[str]:
    """QuickNotes as printed lines: strings as written; a NoteBlock is a bold heading and '- ' bullets."""
    out = []
    for q in lesson.quicknotes:
        if isinstance(q, str):
            out.append(q)
            continue
        head = ": ".join(x for x in (q.target, q.title) if x)
        if head:
            out.append(f"**{head}**")
        out += [f"- {b}" for b in q.bullets]
    return out


def _scored(lesson: LessonSpec, practice: bool = True):
    """(label, item or part, parent item) for section items and parts, then practice cells ("Practice 3")."""
    groups = [(it, "") for _, it in lesson.items()]
    if practice and lesson.practice:
        groups += [(it, "Practice ") for r in lesson.practice.rows for it in r.cells]
    for it, pre in groups:
        yield pre + (it.n or "-"), it, it
        for p in it.parts:
            yield pre + f"{it.n or ''}{p.label.rstrip('.').strip()}", p, it


def _distractors_md(lesson: LessonSpec) -> list[str]:
    rows = [f"| {lab} | {x.key or ''} | {c} | {d} |" for lab, x, _ in _scored(lesson)
            for c, d in sorted(x.distractors.items())]
    if not rows:
        return []
    return ["### Distractors", "| Item | Key | Choice | What it shows |", "|---|---|---|---|"] + rows


def _blueprint_md(lesson: LessonSpec) -> list[str]:
    """Assessments with target/type/demand on any item or part: one row per item (per part when parts carry
    the fields), then a demand count."""
    def meta(x):
        return x.target or x.type or x.demand
    if lesson.doc_type != "assessment" or not any(meta(x) for _, x, _ in _scored(lesson, practice=False)):
        return []
    rows = []
    for _, it in lesson.items():
        if any(meta(p) for p in it.parts):
            for p in it.parts:
                rows.append((f"{it.n or '-'}{p.label.rstrip('.').strip()}", p.target or it.target,
                             p.type or it.type, p.demand or it.demand, p.points))
        elif it.n or meta(it):
            pts = [x.points for x in [it] + list(it.parts) if x.points is not None]
            rows.append((it.n or "-", it.target, it.type, it.demand, sum(pts) if pts else None))
    out = ["## Blueprint", "| Item | Target | Type | Demand | Points |", "|---|---|---|---|---|"]
    out += [f"| {n} | {t or ''} | {ty or ''} | {d or ''} | {'' if p is None else f'{p:g}'} |"
            for n, t, ty, d, p in rows]
    counts = {k: sum(r[3] == k for r in rows) for k in ("mem", "pwoc", "pwc", "dm")}
    line = "Demand count: " + ", ".join(f"{k} {v}" for k, v in counts.items())
    unset = sum(r[3] is None for r in rows)
    return out + ["", line + (f", not set {unset}" if unset else "")]


def guide_markdown(lesson: LessonSpec) -> str:
    out = ["## Answer key: student handout" if lesson.doc_type == "lesson" else "## Answer key"]
    for s in lesson.sections:
        if s.kind == "notes":
            out += ["### QuickNotes (printed on the handout and the key)"] + quicknote_lines(lesson)
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
    out += _distractors_md(lesson) + _blueprint_md(lesson)
    if lesson.plan:
        out += ["## Lesson plan" if lesson.doc_type == "lesson" else "## Notes for the teacher", lesson.plan]
    if lesson.guide_notes:
        out += ["", lesson.guide_notes]   # blank line: a paragraph just above would swallow its first line
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
    there are teacher notes, a blueprint, or distractor notes). Reference sheets: output/Reference/<stem>.docx."""
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
    if lesson.plan or lesson.guide_notes or _distractors_md(lesson) or _blueprint_md(lesson):
        out["guide"] = d / f"{title} Teacher Notes.docx"
    return out


def render_lesson(unit: UnitSpec, lesson: LessonSpec, figs: Figures, scale: dict | None = None,
                  grown: list | None = None) -> dict[str, Path]:
    """grown: if a list, filled with (where, field, set inches, inches used) for workspace that grew to hold the
    key's answer (the same on the student copy and the key)."""
    scale = scale or {}
    o = outputs(unit, lesson)
    render_handout(unit, lesson, False, figs, o["handout"], scale.get("handout", 1.0), grown)
    if "key" in o:
        render_handout(unit, lesson, True, figs, o["key"], scale.get("handout", 1.0))
    if "practice" in o:
        render_practice(unit, lesson, False, figs, o["practice"], scale.get("practice", 1.0), grown)
        render_practice(unit, lesson, True, figs, o["practice_key"], scale.get("practice", 1.0))
    if "guide" in o:
        render_guide(unit, lesson, o["guide"])
    return o

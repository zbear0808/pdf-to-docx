"""Rendering of the newer YAML schema fields (S3, S5-S7, S9-S12, S14). DOCX only; no Word needed."""
import textwrap
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from PIL import Image

from lesson_builder import render as R
from lesson_builder.spec import UnitSpec, load_lesson

RED = "C00000"


def _unit(tmp_path: Path) -> UnitSpec:
    u = UnitSpec(course="Geometry", unit="9", unit_title="Test unit", lessons=[])
    u.dir = tmp_path
    Image.new("RGB", (900, 600), "white").save(tmp_path / "fig.png")   # drawn 3.0 in wide at 300 dpi
    return u


def _load(tmp_path: Path, text: str, name="doc.yaml"):
    p = tmp_path / name
    p.write_text(textwrap.dedent(text), encoding="utf-8")
    return load_lesson(p)


def _paras(path: Path) -> list[tuple[str, bool]]:
    """(text, has red) for every paragraph, tables included, in document order."""
    out = []
    for p in Document(str(path)).element.body.iter(qn("w:p")):
        t = "".join(e.text or "" for e in p.iter() if e.tag in (qn("w:t"), qn("m:t")))
        red = any(c.get(qn("w:val")) == RED for c in p.iter(qn("w:color")))
        out.append((t, red))
    return out


def _text(path: Path) -> str:
    return "\n".join(t for t, _ in _paras(path))


def _red(path: Path) -> str:
    return "\n".join(t for t, r in _paras(path) if r)


def _render(tmp_path, lesson, key):
    u = _unit(tmp_path)
    return R.render_handout(u, lesson, key, R.Figures(u, {}), tmp_path / f"out_{int(key)}.docx")


def _pic_widths(path: Path) -> list[float]:
    ns = "{http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing}extent"
    return [int(e.get("cx")) / 914400 for e in Document(str(path)).element.body.iter(ns)]


LESSON = """\
id: '9.1'
title: Test lesson
notes_title: Notes
framing: Why.
numbering: auto
sections:
  - kind: together
    bank: [translate, reflect across a line, rotate around a point]
    items:
      - id: build
        prompt: 'Build the figure.'
        steps: ['Trace the triangle.', 'Rotate the paper.']
        figure: fig.png
        fig: small
        answer: 'Done.'
      - prompt: 'Use your work from {ref:build}.'
        choices: [one, two, three]
        key: C
        answer: 'three sides'
        distractors: {A: 'counted vertices', B: 'missed a side'}
      - prompt: 'Explain.'
        answer: 'Model answer.'
        rubric: [{level: 4, desc: 'complete and correct'}, {level: 2, desc: 'partial'}]
        scoring: epi
      - prompt: 'Frames.'
        frame:
          - ['Three', 'sides', '.']
          - ['Four', 'angles', '.', 1.5]
          - {before: 'A', answer: 'kite', after: 'shape.', w: 1.2}
  - kind: notes
quicknotes:
  - '**LT 0: plain**'
  - target: LT1
    title: Congruence
    bullets: ['Same size and shape.', 'Rigid motions keep lengths.']
practice:
  title: Practice
  rows:
    - cells:
        - prompt: 'MC with key.'
          choices: [a, b, c, d]
          key: B
        - prompt: 'MC with bracket.'
          choices: [a, b]
          answer: '[A] because it is.'
    - cells:
        - prompt: 'Long.'
          answer: 'The scale factor is 2. Each side doubles because the image is twice as far from the center.'
        - prompt: 'Fill.'
          fill: [['$x =$', '15'], ['$y =$', '9']]
          figure: fig.png
          fig: medium
    - cells:
        - prompt: 'Parts.'
          parts:
            - {label: a., prompt: 'First.', answer: '18'}
            - {label: b., prompt: 'Second.', answer: '9'}
  selected: auto
"""


def test_fig_size_word_sets_printed_width(tmp_path):   # S5
    l = _load(tmp_path, LESSON)
    assert l.sections[0].items[0].width == 1.6
    assert any(abs(w - 1.6) < 0.01 for w in _pic_widths(_render(tmp_path, l, False)))
    u = _unit(tmp_path)
    p = R.render_practice(u, l, False, R.Figures(u, {}), tmp_path / "p.docx")
    assert any(abs(w - 2.4) < 0.01 for w in _pic_widths(p))


def test_work_defaults(tmp_path):   # S3
    l = _load(tmp_path, """\
        id: x
        doc_type: assessment
        title: T
        sections:
          - kind: plain
            items:
              - {n: 1, prompt: p, choices: [a, b], answer: '[A]'}
              - {n: 2, prompt: p, table: {header: [V, A], answers: [B]}}
              - {n: 3, prompt: p, columns: {headers: [x, y]}}
              - {n: 4, prompt: p, choices: [a, b], answer: '[A]', work: 1.0}
              - {n: 5, prompt: p, answer: a}
              - {n: 6, prompt: p, parts: [{label: a., prompt: q, choices: [a, b], answer: '[B]'}]}
        """)
    its = l.sections[0].items
    assert [R._work(i) for i in its] == [0.2, 0, 0, 1.0, 0.8, 0]
    assert R._work(its[5].parts[0]) == 0.2
    body = Document(str(_render(tmp_path, l, False))).element.body
    rows = [h.get(qn("w:val")) for h in body.iter(qn("w:trHeight")) if h.get(qn("w:hRule")) == "exact"]
    # workspace is an exact-height slot plus its 1 pt tail paragraph: 1.0 in (twips); the 0.2 in choice slots
    # grow just enough to hold the key's "[A]" line, on both copies
    assert str(int((1.0 - 1 / 72) * 1440)) in rows and min(map(int, rows)) >= int((0.2 - 1 / 72) * 1440)


def test_workspace_is_the_same_on_student_and_key(tmp_path):
    """The key's answer text sits in the same exact-height slot as the student's blank workspace, and a long
    answer grows the slot on both copies (no student/key drift)."""
    long = "Because " + "the corresponding sides are proportional and " * 12 + "so they are similar."
    l = _load(tmp_path, f"""\
        id: x
        doc_type: assessment
        title: T
        sections:
          - kind: plain
            items:
              - {{n: 1, prompt: p, answer: short, work: 0.5}}
              - {{n: 2, prompt: p, answer: '{long}', work: 0.5}}
        """)

    def slots(key):
        body = Document(str(_render(tmp_path, l, key))).element.body
        return [h.get(qn("w:val")) for h in body.iter(qn("w:trHeight")) if h.get(qn("w:hRule")) == "exact"]
    student, key = slots(False), slots(True)
    assert student == key
    assert int(max(student, key=int)) > int((0.5 - 1 / 72) * 1440)   # the long answer grew both copies


def test_selected_auto_and_numbers(tmp_path):   # S6
    l = _load(tmp_path, LESSON)
    assert R.selected_answers(l) == [("1", "B"), ("2", "A"), ("3", "The scale factor is 2."), ("4", "15, 9"),
                                     ("5", "a. 18  b. 9")]
    l.practice.selected = ["2", "5a", "9"]
    assert R.selected_answers(l) == [("2", "A"), ("5a", "18")]
    l.practice.selected = [["1", "D"], "3"]
    assert R.selected_answers(l) == [("1", "D"), ("3", "The scale factor is 2.")]
    l.practice.selected = "auto"
    u = _unit(tmp_path)
    txt = _text(R.render_practice(u, l, False, R.Figures(u, {}), tmp_path / "p.docx"))
    assert "Answers to selected problems" in txt and "a. 18  b. 9" in txt


def test_mc_key_and_distractors(tmp_path):   # S9
    l = _load(tmp_path, LESSON)
    assert "[C] three sides" in _red(_render(tmp_path, l, True))
    assert "three sides" not in _text(_render(tmp_path, l, False))
    assert "Use your work from Problem 1." in _text(_render(tmp_path, l, False))
    md = R.guide_markdown(l)
    assert "2. [C] three sides" in md
    assert "### Distractors\n| Item | Key | Choice | What it shows |" in md
    assert "| 2 | C | A | counted vertices |" in md and "| 2 | C | B | missed a side |" in md
    u = _unit(tmp_path)
    assert "[B]" in _red(R.render_practice(u, l, True, R.Figures(u, {}), tmp_path / "pk.docx"))
    assert "[B]" in md   # practice key letter, no answer text


def test_rubric_key_only_and_epi(tmp_path):   # S10
    l = _load(tmp_path, LESSON)
    key, student = _render(tmp_path, l, True), _render(tmp_path, l, False)
    assert "4: complete and correct" in _red(key) and "2: partial" in _red(key)
    assert "complete and correct" not in _text(student)
    md = R.guide_markdown(l)
    assert "3. Model answer. (scored E/P/I)\n  - Rubric 4: complete and correct\n  - Rubric 2: partial" in md


ASSESSMENT = """\
id: 9 Quiz A
doc_type: assessment
title: Quiz
numbering: auto
set: 9 Quiz
form: A
targets: [{id: LT1, able_to: 'find a scale factor'}]
sections:
  - kind: plain
    columns: 2
    items:
      - {prompt: 'Left cell.', points: 2, target: LT1, type: sr, demand: pwoc, choices: [a, b, c], key: A}
      - {prompt: 'Right cell.', points: 1, target: LT1, type: cr, demand: pwc, answer: 'right answer',
         steps: ['First step.']}
      - prompt: 'Full width table.'
        table: {header: [V, A], answers: [B]}
      - prompt: 'Parts.'
        parts:
          - {label: a., prompt: 'Part a.', points: 1, target: LT1, demand: mem, answer: '4'}
          - {label: b., prompt: 'Part b.', points: 2, type: cr, demand: dm, answer: '5'}
"""


def test_blueprint_and_outputs(tmp_path):   # S7
    l = _load(tmp_path, ASSESSMENT)
    md = R.guide_markdown(l)
    assert "## Blueprint\n| Item | Target | Type | Demand | Points |" in md
    assert "| 1 | LT1 | sr | pwoc | 2 |" in md and "| 2 | LT1 | cr | pwc | 1 |" in md
    assert "| 3 |  |  |  |  |" in md
    assert "| 4a | LT1 |  | mem | 1 |" in md and "| 4b |  | cr | dm | 2 |" in md
    assert "Demand count: mem 1, pwoc 1, pwc 1, dm 1, not set 1" in md
    u = _unit(tmp_path)
    assert "guide" in R.outputs(u, l)
    plain = _load(tmp_path, LESSON, "l.yaml")
    plain.doc_type = "assessment"
    assert "## Blueprint" not in R.guide_markdown(plain)


def test_quicknote_blocks(tmp_path):   # S11
    l = _load(tmp_path, LESSON)
    assert R.quicknote_lines(l) == ["**LT 0: plain**", "**LT1: Congruence**", "- Same size and shape.",
                                    "- Rigid motions keep lengths."]
    for key in (False, True):
        paras = _paras(_render(tmp_path, l, key))
        txt = [t for t, _ in paras]
        assert "LT1: Congruence" in txt and "\u2022Same size and shape." in txt
    doc = Document(str(_render(tmp_path, l, False)))
    bold = [r.find(qn("w:t")).text for r in doc.element.body.iter(qn("w:r"))
            if r.find(qn("w:rPr") + "/" + qn("w:b")) is not None and r.find(qn("w:t")) is not None]
    assert "LT1: Congruence" in bold
    md = R.guide_markdown(l)
    assert "**LT1: Congruence**\n- Same size and shape." in md


def test_steps_and_bank(tmp_path):   # S12
    l = _load(tmp_path, LESSON)
    txt = [t for t, _ in _paras(_render(tmp_path, l, False))]
    assert "translate  |  reflect across a line  |  rotate around a point" in txt
    k = next(i for i, t in enumerate(txt) if t.endswith("Build the figure."))
    assert txt[k + 1:k + 3] == ["Step 1:Trace the triangle.", "Step 2:Rotate the paper."]   # tabs are w:tab


def test_two_columns(tmp_path):   # S14
    l = _load(tmp_path, ASSESSMENT)
    for key in (False, True):
        path = _render(tmp_path, l, key)
        doc = Document(str(path))
        grids = [t for t in doc.tables if len(t.columns) == 2 and "Left cell." in t.rows[0].cells[0].text]
        assert grids, "no two-column grid"
        row = grids[0].rows[0].cells
        assert "Right cell. (1 pt)" in row[1].text and "Step 1:" in row[1].text
        assert "Left cell. (2 pts)" in row[0].text
        assert "Full width table." not in grids[0]._tbl.xml
    assert "right answer" in _red(path) and "[A]" in _red(path)
    assert "right answer" not in _text(_render(tmp_path, l, False))


def test_frame_rows(tmp_path):   # S4 rows render (3, 4 elements, and mappings)
    l = _load(tmp_path, LESSON)
    red = _red(_render(tmp_path, l, True))
    assert all(a in red for a in ("sides", "angles", "kite"))
    assert "A **kite** shape." in R.guide_markdown(l)


def _styles(path: Path) -> list[tuple[str, bool, bool, bool, bool]]:
    """(text, red, bold, any bold markup, math) for every text run and math run, tables included. A math run
    is bold only with m:sty b/bi (Word and OnlyOffice ignore w:b on math) plus w:b; an m:nor run with w:b."""
    out = []
    for r in Document(str(path)).element.body.iter(qn("w:r"), qn("m:r")):
        rpr = r.find(qn("w:rPr"))
        b = rpr.find(qn("w:b")) if rpr is not None else None
        wb = b is not None and b.get(qn("w:val")) not in ("0", "false")
        red = rpr is not None and any(c.get(qn("w:val")) == RED for c in rpr.iter(qn("w:color")))
        math = r.tag == qn("m:r")
        sty = r.find(f"{qn('m:rPr')}/{qn('m:sty')}")
        sty_b = sty is not None and sty.get(qn("m:val")) in ("b", "bi")
        nor = r.find(f"{qn('m:rPr')}/{qn('m:nor')}") is not None
        bold = wb and (sty_b or nor) if math else wb
        text = "".join(t.text or "" for t in r.iter(qn("w:t"), qn("m:t")))
        out.append((text, red, bold, wb or sty_b, math))
    return out


EVERY_ANSWER = """\
id: x
doc_type: assessment
title: T
sections:
  - kind: plain
    items:
      - {n: 1, prompt: p, answer: '$m\\angle B = 52^\\circ$ by the Isosceles Triangle Theorem.', work: 0.6}
      - {n: 2, prompt: p, choices: [a, b, c], key: B, answer: "$\\\\text{SAS}$ maps $A'B'$ to $\\\\sin 41^\\\\circ$"}
      - {n: 3, prompt: p, fill: [['$x =$', '$\\sqrt{34} \\approx 5.83$'], ['$y =$', '9 ft']]}
      - {n: 4, prompt: p, frame: [['The angle is', 'right', '.']]}
      - {n: 5, prompt: p, box: 1.0, answer: 'Box answer.', rubric: [{level: 2, desc: 'full credit'}]}
      - {n: 6, prompt: p, draw: {height: 1.5, key_note: 'Draw note.'}, answer: 'drawn'}
      - {n: 7, prompt: p, table: {header: [V, A], answers: ['$B$']}}
      - {n: 8, prompt: p, columns: {headers: [x, y], answers: [['col one'], ['$y = 2$']]}}
      - n: 9
        prompt: p
        proof:
          rows:
            - ['$AB = CD$', {ans: '$\\overline{AB} \\cong \\overline{CD}$'}]
            - [{before: '$\\triangle ABD \\cong \\triangle$', ans: '$CDB$'}, {ans: 'SAS'}]
"""


def test_key_answers_print_bold_and_red(tmp_path):
    """Every red run on a key (text and math) is bold; student copies have no red and no bold math."""
    docs = [(_load(tmp_path, EVERY_ANSWER, "every.yaml"), "every"), (_load(tmp_path, LESSON), "lesson"),
            (_load(tmp_path, PROOF, "proof.yaml"), "proof")]
    u = _unit(tmp_path)
    red_math = 0
    for l, name in docs:
        pairs = [(R.render_handout(u, l, False, R.Figures(u, {}), tmp_path / f"{name}_s.docx"),
                  R.render_handout(u, l, True, R.Figures(u, {}), tmp_path / f"{name}_k.docx"))]
        if l.practice:
            pairs.append((R.render_practice(u, l, False, R.Figures(u, {}), tmp_path / f"{name}_ps.docx"),
                          R.render_practice(u, l, True, R.Figures(u, {}), tmp_path / f"{name}_pk.docx")))
        for student, key in pairs:
            k, s = _styles(key), _styles(student)
            assert any(x[1] and not x[4] for x in k), key.name
            red_math += sum(1 for x in k if x[1] and x[4])
            assert [x[0] for x in k if x[1] and not x[2]] == [], f"{key.name}: red runs that aren't bold"
            assert not any(x[1] for x in s), student.name
            assert not any(x[3] for x in s if x[4]), f"{student.name}: bold math on the student copy"
            # the student copy's bold text is the key's bold text minus the answers (the student practice copy
            # adds the selected-answers strip at the end)
            s_bold = [x[0] for x in s if x[2]]
            if "Answers to selected problems" in s_bold:
                s_bold = s_bold[:s_bold.index("Answers to selected problems")]
            assert s_bold == [x[0] for x in k if x[2] and not x[1]], student.name
    assert red_math > 10
    bold_red = "".join(x[0] for x in _styles(tmp_path / "every_k.docx") if x[1] and x[2])
    for a in ("52°", "Isosceles Triangle Theorem.", "[B]", "SAS", "5.83", "9 ft", "right", "Box answer.",
              "full credit", "Draw note.", "drawn", "col one", "y=2", "≅", "CDB"):
        assert a in bold_red, a


def test_answer_math_is_bold_only_in_answers():
    """add_answer marks math bold with m:sty (bi for letters, b for upright text and functions) and w:b, an
    m:nor prime with w:b; bold student text (add_rich bold=True) keeps its math regular."""
    from docx import Document as New
    from lesson_builder import docbuilder as db
    p = New().add_paragraph()
    db.add_answer(p, r"so $x = 15$, $\text{SAS}$, $\sin 41^\circ$ and $\overline{B'C'}$", 10.5)
    runs = list(p._p.iter(qn("m:r")))
    sty = {r.find(qn("m:t")).text: r.find(f"{qn('m:rPr')}/{qn('m:sty')}") for r in runs}
    assert sty["x=15"].get(qn("m:val")) == "bi" and sty["SAS"].get(qn("m:val")) == "b"
    assert sty["sin"].get(qn("m:val")) == "b"
    prime = [r for r in runs if r.find(qn("m:t")).text == "′"]
    assert prime and all(r.find(f"{qn('m:rPr')}/{qn('m:nor')}") is not None for r in prime)
    assert all(r.find(f"{qn('w:rPr')}/{qn('w:b')}") is not None for r in runs)
    assert all(r.find(f"{qn('w:rPr')}/{qn('w:b')}") is not None for r in p._p.iter(qn("w:r")))
    q = New().add_paragraph()
    db.add_rich(q, r"**Given:** $x = 15$ and $\text{SAS}$", 11, bold=True)
    assert not [r for r in q._p.iter(qn("m:r")) if r.find(f"{qn('w:rPr')}/{qn('w:b')}") is not None
                or (r.find(f"{qn('m:rPr')}/{qn('m:sty')}") is not None
                    and r.find(f"{qn('m:rPr')}/{qn('m:sty')}").get(qn("m:val")) != "p")]
    import pytest
    with pytest.raises(ValueError):
        db.add_answer(New().add_paragraph(), r"$\nosuchcommand$")
    assert db._MATH_BOLD[0] is False and db._MATH_COLOR[0] is None   # later (student) math stays plain


def test_box_widens_on_both_copies_for_a_bold_answer():
    """Regression (Unit 4 Review): a bold key answer wider than the 1.3 in fill box wrapped onto two lines in Word
    ("17.1" / "m"). The box gets wider on both copies, noted in h.grown; short answers keep box_w."""
    from lesson_builder.docbuilder import Handout
    long_, short = ("$h \\approx$", "$35\\tan 26^\\circ \\approx 17.1$ m"), ("$x =$", "8")

    def box_ws(key, items, frame=False):
        h = Handout(key=key)
        if frame:
            t = h.frame(None, [("The answer is", items[1], ".")], box_w=1.1)
        else:
            t = h.fill_boxes(None, [items])
        return [c.width.inches for c in t.rows[0].cells], h.grown
    (ws, grown), (wk, _) = box_ws(False, long_), box_ws(True, long_)
    assert ws == wk and ws[1] > 1.35 and grown[0][:3] == ("fill box", "box_w", 1.3)
    assert len(grown) == 1 and abs(grown[0][3] - ws[1]) < 0.01
    assert box_ws(False, short)[0][1] == 1.3 and box_ws(False, short)[1] == []
    (fs, fgrown), (fk, _) = box_ws(False, (None, "the angle between the two sides"), True), \
        box_ws(True, (None, "the angle between the two sides"), True)
    assert fs == fk and fs[1] > 1.1 and fgrown[0][1] == "frame_box_w"
    stacked = box_ws(False, ("$x =$", "$\\frac{1234567}{89}$ and some more words"))
    assert stacked[0][1] == 1.3 and stacked[1] == []   # stacked math gets a taller row instead


def test_templates_use_new_fields_and_pass_checks(tmp_path):
    from lesson_builder.check import check_spec
    from lesson_builder.figures import render_all
    tpl = Path(__file__).resolve().parents[1] / "templates" / "unit"
    u = _unit(tmp_path)
    figs = render_all(tpl / "figures.py", tmp_path / "_temp" / "figures")
    lesson = load_lesson(tpl / "lessons" / "example.yaml")
    assert check_spec(u, lesson, figs) == []
    assert "In Problem 2," in str(lesson.sections[2].items[0].frame[0][0])
    assert R.selected_answers(lesson) and lesson.sections[2].items[1].steps
    out = R.render_handout(u, lesson, True, R.Figures(u, figs), tmp_path / "lk.docx")
    assert "Step 1:" in _text(out) and "[B] one-line reason" in _red(out)
    a = load_lesson(tpl / "assessments" / "example.yaml")
    fake = {"dilate_abc": {"student": tmp_path / "fig.png", "key": None}}   # the real one: figures/example.py
    assert check_spec(u, a, fake) == []
    assert [it.n for _, it in a.items()] == ["1", "2", "3"] and a.form == "A"
    md = R.guide_markdown(a)
    assert "## Blueprint" in md and "### Distractors" in md and "Rubric 4:" in md
    assert "| 3a | LT1 |  | pwoc | 2 |" in md
    key = R.render_handout(u, a, True, R.Figures(u, fake), tmp_path / "ak.docx")
    assert "[A] A scale factor" in _red(key) and "4: All three image points" in _red(key)


def test_guide_unnumbered_practice_cell(tmp_path):
    """Regression (Unit 4 lesson 4.1): an unnumbered practice cell printed "None." in the teacher guide key."""
    l = _load(tmp_path, """\
        id: x
        doc_type: assessment
        title: T
        sections: [{kind: plain, items: [{n: 1, prompt: p, answer: a}]}]
        practice:
          title: P
          rows: [{cells: [{prompt: q, answer: shown}]}]
        """)
    md = R.guide_markdown(l)
    assert "None." not in md and "shown" in md


def test_fill_box_fits_a_narrow_cell():
    """Regression (Unit 4 lesson 4.7): a long fill label in a half-width practice cell pushed the box (and the
    key's answer) past the cell edge."""
    from docx.shared import Inches
    from lesson_builder.docbuilder import Handout, set_widths
    h = Handout(key=True)
    t = h._table(1, 2, [3.4, 3.9])
    cell = t.rows[0].cells[0]
    set_widths(t, [3.4, 3.9])
    inner = h.fill_boxes(cell, [("True or false: the ladder reaches the window ledge", "True")])
    total = sum(c.width.inches for c in inner.rows[0].cells)
    assert total <= 3.4 - 0.3 + 0.02 and inner.rows[0].cells[1].width.inches >= 0.9


def test_draw_item_keeps_fill_and_parts(tmp_path):
    """Regression (Unit 4 Review, 4.6-4.7 check): a draw item silently dropped its fill boxes and parts."""
    l = _load(tmp_path, """\
        id: x
        doc_type: assessment
        title: T
        sections:
          - kind: plain
            items:
              - n: 1
                prompt: Sketch the tree and its shadow.
                draw: {height: 2.0}
                answer: sketch
                fill: [['$h =$', '31 ft']]
                parts: [{label: b., prompt: Which ratio did you use, answer: tangent}]
        """)
    student, key = _text(_render(tmp_path, l, False)), _render(tmp_path, l, True)
    assert "Which ratio did you use" in student and "h=" in student.replace(" ", "")
    assert "31 ft" in _red(key) and "tangent" in _red(key)


def test_guide_joins_frame_rows_of_one_sentence(tmp_path):
    """Regression (Unit 4 Test Retake): two frame rows of one sentence printed as 'the angle is; less than'."""
    l = _load(tmp_path, """\
        id: x
        doc_type: assessment
        title: T
        sections:
          - kind: plain
            items:
              - n: 1
                prompt: Is the ladder safe?
                frame: [['The ladder', 'is not', 'safe because the angle is'], ['', 'less', 'than 70 degrees.']]
        """)
    md = R.guide_markdown(l)
    assert "the angle is **less** than 70 degrees." in md and "is; " not in md


PROOF = """\
id: '9.2'
title: Proof lesson
numbering: auto
sections:
  - kind: partner
    items:
      - prompt: 'Finish the proof.'
        proof:
          given: '$\\overline{AB} \\parallel \\overline{DC}$'
          prove: '$\\triangle ABD \\cong \\triangle CDB$'
          rows:
            - ['$\\overline{AB} \\parallel \\overline{DC}$', 'Given']
            - [{ans: '$\\angle ABD \\cong \\angle CDB$'}, 'Alternate interior angles']
            - ['$\\overline{BD} \\cong \\overline{DB}$', {ans: 'A segment is congruent to itself'}]
            - [{before: '$\\triangle ABD \\cong \\triangle$', ans: '$CDB$'}, {ans: 'ASA'}]
practice:
  title: Practice
  rows:
    - cells:
        - prompt: 'Practice proof.'
          proof:
            rows:
              - ['$AB = CD$', {ans: 'Given'}]
        - prompt: 'Two parts.'
          parts:
            - label: a.
              prompt: 'Prove it.'
              proof:
                rows:
                  - [{ans: '$EF = GH$'}, 'Given']
"""


def test_proof_table_blanks_and_key(tmp_path):
    from lesson_builder.check import check_spec
    import pytest
    from lesson_builder.spec import Proof
    l = _load(tmp_path, PROOF)
    assert l.sections[0].items[0].proof.blanks() == ['$\\angle ABD \\cong \\angle CDB$',
                                                     'A segment is congruent to itself', '$CDB$', 'ASA']
    assert not [e for e in check_spec(_unit(tmp_path), l, {}) if "no answer" in e.lower()]
    s, k = _render(tmp_path, l, False), _render(tmp_path, l, True)
    assert "Statement" in _text(s) and "Reason" in _text(s) and "2. Alternate interior angles" in _text(s)
    assert "congruent to itself" not in _text(s) and "congruent to itself" in _red(k)
    assert "Given:" in _text(s) and "Prove:" in _text(s)

    def heights(p):
        return [r.get(qn("w:val")) for r in Document(str(p)).element.body.iter(qn("w:trHeight"))
                if r.get(qn("w:hRule")) == "exact"]
    assert heights(s) == heights(k) and len(heights(s)) == 4
    assert "4.ΔABD≅Δ" in _text(s).replace(" ", "") and "CDB" not in _text(s).split("4.")[-1]   # same table height on both copies
    pr = R.render_practice(_unit(tmp_path), l, True, R.Figures(_unit(tmp_path), {}), tmp_path / "pk.docx")
    assert "Given" in _red(pr) and "EF = GH" not in _text(R.render_practice(
        _unit(tmp_path), l, False, R.Figures(_unit(tmp_path), {}), tmp_path / "ps.docx"))
    assert "EF" in _red(pr)   # a proof inside a part, answered on the key
    with pytest.raises(Exception):
        Proof(rows=[["only one cell"]])


def test_proof_under_side_figure_has_gap(tmp_path):
    """Word paints a side figure's white background over the proof table's top border if the tables touch."""
    l = _load(tmp_path, """\
        id: '9.3'
        title: Figure proof
        sections:
          - kind: partner
            items:
              - n: 1
                prompt: 'Prove it.'
                figure: fig.png
                fig_w: 1.0
                proof:
                  rows:
                    - [{ans: '$AB = CD$'}, 'Given']
        """)
    body = Document(str(_render(tmp_path, l, False))).element.body
    kids = [e for e in body if e.tag in (qn("w:tbl"), qn("w:p"))]
    i = next(k for k, e in enumerate(kids) if e.tag == qn("w:tbl") and "Statement" in "".join(
        t.text or "" for t in e.iter(qn("w:t"))))
    gap = kids[i - 1]
    assert gap.tag == qn("w:p") and kids[i - 2].tag == qn("w:tbl")
    assert any(s.get(qn("w:line")) == "40" for s in gap.iter(qn("w:spacing")))   # 2 pt exact


def test_inline_quicknotes_skip_the_new_page(tmp_path):
    text = """\
    id: '9.3'
    title: Short lesson
    notes_title: Notes page
    sections:
      - kind: partner
        items:
          - prompt: 'One item.'
            answer: 'Done.'
      - kind: notes
        new_page: NEW
      - kind: exit
        items:
          - prompt: 'Exit.'
            answer: 'Done.'
    quicknotes: ['A fact.']
    """
    def breaks(path):
        return sum(1 for b in Document(str(path)).element.body.iter(qn("w:br")) if b.get(qn("w:type")) == "page")
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir()
    on = _render(tmp_path / "a", _load(tmp_path, text.replace("NEW", "true"), "on.yaml"), False)
    off = _render(tmp_path / "b", _load(tmp_path, text.replace("NEW", "false"), "off.yaml"), False)
    assert breaks(on) == breaks(off) + 1
    assert "Notes page" in _text(on) and "Notes page" not in _text(off) and "A fact." in _text(off)


def test_steps_only_item_has_no_blank_prompt_line():
    it = R.Item(steps=["Draw it.", "Label it."])
    assert R._prompt_lines(it) == ["Step 1: Draw it.", "Step 2: Label it."]


def test_headings_warmup_prints_only_the_warmup_heading(tmp_path):
    text = """\
    id: '9.3'
    title: Headings
    notes_title: Notes
    numbering: auto
    headings: HEAD
    sections:
      - kind: warmup
        items:
          - prompt: 'Warm.'
            answer: 'W.'
      - kind: together
        items:
          - prompt: 'Together problem.'
            answer: 'T.'
      - kind: partner
        items:
          - prompt: 'Partner problem.'
            answer: 'P.'
      - kind: plain
        title: 'Ramp rules'
        items:
          - prompt: 'Read the rules.'
            answer: 'R.'
      - kind: notes
        new_page: false
    quicknotes: ['A fact.']
    """
    (tmp_path / "a").mkdir(); (tmp_path / "b").mkdir()
    full = _text(_render(tmp_path / "a", _load(tmp_path, text.replace("HEAD", "all"), "all.yaml"), False))
    lean = _text(_render(tmp_path / "b", _load(tmp_path, text.replace("HEAD", "warmup"), "lean.yaml"), True))
    assert "Together" in full and "With a partner" in full and "on your own" in full and "Problem 1" in full
    assert "Warm-up" in lean and "Ramp rules" in lean   # a title the YAML writes out still prints
    for label in ("Together", "With a partner", "on your own", "Problem 1", "Problem 2"):
        assert label not in lean.replace("Together problem.", "").replace("Partner problem.", "")
    assert "1." in lean and "2." in lean and "3." in lean   # numbering runs on


def test_problem_without_a_prompt_keeps_its_number(tmp_path):
    text = """\
    id: '9.4'
    title: No prompt
    notes_title: Notes
    numbering: auto
    sections:
      - kind: together
        items:
          - figure: fig.png
            fig: small
            parts:
              - {label: a., prompt: 'First part.', answer: 'A.'}
      - kind: notes
    quicknotes: ['A fact.']
    practice:
      title: Practice
      rows:
        - cells:
            - prompt: 'Has a prompt.'
              answer: 'X.'
            - figure: fig.png
              parts:
                - {label: a., prompt: 'Only parts.', answer: 'Y.'}
    """
    lesson = _load(tmp_path, text)
    handout = _text(_render(tmp_path, lesson, False))
    assert handout.lstrip().count("1.") >= 1 and "First part." in handout
    u = _unit(tmp_path)
    out = R.render_practice(u, lesson, False, R.Figures(u, {}), tmp_path / "pr.docx")
    paras = [t for t, _ in _paras(out)]
    assert any(t.startswith("2.") for t in paras), paras   # the prompt-less practice item still prints "2."


def test_assessment_title_has_no_leading_spaces(tmp_path):
    text = """\
    id: 'Quiz 9'
    doc_type: assessment
    title: A long assessment title
    total_points: 1
    sections:
      - kind: plain
        items:
          - prompt: 'One.'
            points: 1
            answer: 'A.'
    """
    out = _render(tmp_path, _load(tmp_path, text), False)
    first = next(t for t, _ in _paras(out) if t.strip())
    assert first == "A long assessment title"


def test_numbering_after_notes_continue(tmp_path):
    text = """\
    id: '9.5'
    title: In-class practice
    notes_title: Notes
    numbering: auto
    headings: warmup
    numbering_after_notes: NUM
    sections:
      - kind: warmup
        items:
          - prompt: 'Warm.'
            answer: 'W.'
      - kind: partner
        items:
          - id: first
            prompt: 'Partner problem.'
            answer: 'P.'
      - kind: notes
        new_page: false
      - kind: apply
        items:
          - prompt: 'On your own: like {ref:first}.'
            answer: 'A.'
    quicknotes: ['A fact.']
    """
    cont = _load(tmp_path, text.replace("NUM", "continue"), "cont.yaml")
    apply_item = [s for s in cont.sections if s.kind == "apply"][0].items[0]
    assert apply_item.n == "2" and apply_item.prompt == "On your own: like Problem 1."
    rest = _load(tmp_path, text.replace("NUM", "restart"), "rest.yaml")
    assert [s for s in rest.sections if s.kind == "apply"][0].items[0].n == "1"
    lean = _text(_render(tmp_path, cont, False))
    assert lean.count("In-class practice") == 1   # only the title; no section heading with headings: warmup

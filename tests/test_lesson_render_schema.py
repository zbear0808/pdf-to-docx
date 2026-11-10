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
    line = [p.find(qn("w:pPr") + "/" + qn("w:spacing")) for p in
            Document(str(_render(tmp_path, l, False))).element.body.iter(qn("w:p"))]
    lines = [s.get(qn("w:line")) for s in line if s is not None]
    assert "288" in lines and "1440" in lines   # 0.2 in and 1.0 in of workspace (twips)


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

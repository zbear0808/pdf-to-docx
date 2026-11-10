import os
import time
from pathlib import Path

from PIL import Image

from lesson_builder.diff import diff_renders
from lesson_builder.figures import render_all
from lesson_builder.render import Figures, outputs, render_lesson
from lesson_builder.retain import figure_uses, retain, verify
from lesson_builder.spec import load_unit
from lesson_builder.status import format_table, gap_lines, must_fix_lines, unit_status
from lesson_builder.tidy import apply, find_litter

FIG = '''from lesson_builder.figures import Figure, figure


@figure("quiz_tri")
def tri():
    f = Figure(2.0, 1.5)
    f.poly([(0, 0), (4, 0), (1, 3)])
    f.label_poly([(0, 0), (4, 0), (1, 3)], "ABC")
    f.seg((1, 3), (1, 0), layer="answer")
    return f


@figure("quiz_unused")
def unused():
    f = Figure(1.0, 1.0)
    f.seg((0, 0), (1, 1))
    return f
'''

QUIZ = '''id: Quiz A
doc_type: assessment
title: Triangles quiz
sections:
  - kind: plain
    items:
      - n: "1"
        prompt: Draw the altitude from C.
        figure: quiz_tri
        answer: see figure
      - n: "2"
        prompt: Name the shape.
        figure: assets/quiz/shape.png
        answer: square
      - n: "3"
        prompt: Fill in.
        fill: [["side", "AB"]]
        work: 0
      - n: "4"
        prompt: Explain.
        answer: because
        work: 0.8
      - n: "5"
        prompt: Explain more.
        answer: because
        work: 1.5
'''


def _unit(tmp_path: Path):
    u = tmp_path / "unit"
    for d in ("lessons", "assessments", "figures", "assets/quiz", "output/Assessments", "_temp"):
        (u / d).mkdir(parents=True, exist_ok=True)
    (u / "unit.yaml").write_text("course: Geometry\nunit: 9\nunit_title: Test\nlessons: []\n"
                                 "assessments: [assessments/*.yaml]\n", encoding="utf-8")
    (u / "assessments" / "quiz.yaml").write_text(QUIZ, encoding="utf-8")
    (u / "figures" / "quiz.py").write_text(FIG, encoding="utf-8")
    Image.new("RGB", (300, 300), "white").save(u / "assets" / "quiz" / "shape.png")
    (u / "assets" / "quiz" / "shape.png.txt").write_text("Quiz source p2 #4\n", encoding="utf-8")
    Image.new("RGB", (50, 50), "white").save(u / "assets" / "orphan.png")
    unit = load_unit(u)
    figs = render_all(u / "figures" / "quiz.py", u / "_temp" / "figures" / "quiz")
    return unit, unit.lesson_specs()[0], figs


def test_retain_writes_bundle_and_verifies(tmp_path):
    unit, quiz, figs = _unit(tmp_path)
    uses = figure_uses(unit, quiz)
    assert {(u.ref, u.copy) for u in uses} == {("quiz_tri", "student"), ("quiz_tri", "key"),
                                               ("assets/quiz/shape.png", "student"),
                                               ("assets/quiz/shape.png", "key")}
    out = tmp_path / "bundle"
    (out).mkdir()
    (out / "old_fig.png").write_bytes(b"x")
    res = retain(unit, quiz, figs, out)
    assert res.errors == []
    assert {p.name for p in out.iterdir()} == {"quiz_tri.png", "quiz_tri_key.png", "shape.png", "README.md"}
    assert [p.name for p in res.removed] == ["old_fig.png"]
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "| Item | Copy | File | Source |" in readme
    assert "figures/quiz.py:tri` (line 5)" in readme
    assert "Quiz source p2 #4" in readme and "lesson_builder/figures/__init__.py" in readme
    assert 'lesson-builder figs' in readme and '-l "quiz"' in readme
    assert any("not built" in i for i in verify(unit, quiz, out))
    render_lesson(unit, quiz, Figures(unit, figs))
    assert verify(unit, quiz, out) == []
    Image.new("RGB", (40, 40), "black").save(out / "quiz_tri_key.png")
    msgs = verify(unit, quiz, out)
    assert any(m.startswith("ERROR") and "quiz_tri_key.png" in m for m in msgs)


def test_verify_tolerates_reencoded_png(tmp_path):
    unit, quiz, figs = _unit(tmp_path)
    out = tmp_path / "bundle"
    retain(unit, quiz, figs, out)
    render_lesson(unit, quiz, Figures(unit, figs))
    with Image.open(out / "quiz_tri.png") as im:
        im.convert("RGBA").save(out / "quiz_tri.png", optimize=True, compress_level=1)
    assert verify(unit, quiz, out) == []


def test_tidy_finds_and_removes_only_litter(tmp_path):
    unit, quiz, figs = _unit(tmp_path)
    u = unit.dir
    (u / "output" / "Assessments" / "msoA1B2.tmp").write_bytes(b"")
    (u / "output" / "Assessments" / "~$quiz.docx").write_bytes(b"")
    (u / "figures" / "__pycache__").mkdir(exist_ok=True)
    (u / "lessons" / "draft.yaml").write_text("id: x\n", encoding="utf-8")
    (u / "figures" / "gone.py").write_text("", encoding="utf-8")
    diff, cur = u / "_temp" / "renders" / "diff" / "quiz", u / "_temp" / "renders" / "current" / "quiz"
    diff.mkdir(parents=True)
    cur.mkdir(parents=True)
    Image.new("RGB", (5, 5)).save(diff / "p1_diff.png")
    old = time.time() - 100
    os.utime(diff / "p1_diff.png", (old, old))
    Image.new("RGB", (5, 5)).save(cur / "p1.png")
    found = find_litter(unit)
    kinds = {}
    for f in found:
        kinds.setdefault(f.kind, []).append(f)
    assert len(kinds["word_temp"]) == 2 and len(kinds["pycache"]) >= 1 and len(kinds["stale_diff"]) == 1
    assert [f.path.name for f in kinds["orphan_asset"]] == ["orphan.png"]
    assert len(kinds["unused_figure"]) == 1 and "quiz_unused" in kinds["unused_figure"][0].reason
    assert [f.path.name for f in kinds["unlisted_yaml"]] == ["draft.yaml"]
    assert [f.path.name for f in kinds["orphan_figure_file"]] == ["gone.py"]
    work = sorted(f.reason for f in kinds["redundant_work"])
    assert len(work) == 2 and "item 3" in work[0] and "item 4" in work[1] and "line 18" in work[0]
    removed = apply(found, kinds=["word_temp", "pycache", "stale_diff", "orphan_asset", "unlisted_yaml"])
    assert (u / "assets" / "orphan.png").exists() and (u / "lessons" / "draft.yaml").exists()
    assert not (u / "output" / "Assessments" / "msoA1B2.tmp").exists() and not (diff / "p1_diff.png").exists()
    assert not any(p.name == "__pycache__" for p in u.rglob("*")) and len(removed) >= 4


def test_status_table(tmp_path):
    unit, quiz, figs = _unit(tmp_path)
    specs = unit.dir / "_temp" / "specs" / "quiz"
    specs.mkdir(parents=True)
    (specs / "audit.md").write_text("# Audit\n## Must fix\n- p1 item 2: crowded\n- [x] fixed\n- p2: split\n"
                                    "## Should fix\n- something\n", encoding="utf-8")
    (specs / "changes.md").write_text("1: cut\nGAP: render.py:frame: x | y\n- GAP: a | b\n", encoding="utf-8")
    assert len(must_fix_lines((specs / "audit.md").read_text())) == 2
    assert len(gap_lines((specs / "changes.md").read_text())) == 2
    (st,) = unit_status(unit)
    assert st.must_fix == 2 and st.gaps == 2 and st.built == [] and not st.stale
    render_lesson(unit, quiz, Figures(unit, figs))
    old = time.time() - 100
    for p in outputs(unit, quiz).values():
        os.utime(p, (old, old))
    retain(unit, quiz, figs)
    (st,) = unit_status(unit)
    assert st.built == ["handout", "key"] and st.stale and st.retained
    table = format_table([st])
    assert "| quiz | assessment | - cha aud | 2 | 2 | 2/2 | 0/2 | yes | yes |" in table


def test_diff_clears_old_diffs(tmp_path):
    new, prev, out = tmp_path / "new", tmp_path / "prev", tmp_path / "diff"
    for d in (new, prev, out):
        d.mkdir()
    Image.new("RGB", (10, 10), "white").save(new / "p1.png")
    Image.new("RGB", (10, 10), "white").save(prev / "p1.png")
    Image.new("RGB", (10, 10)).save(out / "p9_diff.png")
    assert diff_renders(new, prev, out) == []
    assert list(out.iterdir()) == []

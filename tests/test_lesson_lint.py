"""Label placement, figure lint, print-size and box checks, prime rendering, guide joins."""
import numpy as np

from lesson_builder import docbuilder as db
from lesson_builder.check import _box_issues, check_figures, check_guide_text
from lesson_builder.figures import P, render_all
from lesson_builder.figures.core import Figure, math_fix
from lesson_builder.render import _join
from lesson_builder.spec import LessonSpec


def test_math_fix_primes():
    assert math_fix("$A'B'$") == "$A\u2032B\u2032$"
    assert math_fix(r"$C^{\prime}$ and Lin's") == "$C\u2032$ and Lin's"


def test_colliding_label_moves_and_clear_label_stays():
    f = Figure(2.0, 1.2)
    a, b = P(0, 0), P(4, 0)
    f.seg(a, b)
    f.dots([a, b])
    f.label(a + (2, 0), "M", direction=(1, 0), offset_pt=0)     # dead on the segment: must move
    f.label(b, "B", direction=(1, 0))                          # clear: keeps its spot
    assert f.place() == []
    m, bl = f.labels
    assert m.choice != 0 and bl.choice == 0


def test_unfixable_label_is_reported():
    f = Figure(1.0, 1.0)
    for k in range(-3, 4):  # a cage of thick lines leaves no room
        f.seg((k * 0.06, -1), (k * 0.06, 1), lw=2)
        f.seg((-1, k * 0.06), (1, k * 0.06), lw=2)
    f.text((0, 0), "100°")
    assert any("touches" in m for m in f.place())


def test_fixed_label_is_not_moved():
    f = Figure(2.0, 1.2)
    f.seg(P(0, 0), P(4, 0))
    f.label(P(2, 0), "M", offset_pt=0, fixed=True)
    f.place()
    assert f.labels[0].choice == 0 and f.lint


def test_render_all_meta_and_print_size(tmp_path):
    src = tmp_path / "figs.py"
    src.write_text(
        "from lesson_builder.figures import Figure, figure, P\n"
        "@figure('tri')\n"
        "def tri():\n"
        "    f = Figure(3.0, 2.0)\n"
        "    t = P((0, 0), (4, 0), (1, 3))\n"
        "    f.poly(t); f.dots(t); f.label_poly(t, 'ABC')\n"
        "    return f\n", encoding="utf-8")
    res = render_all(src, tmp_path / "out")
    meta = res["tri"]["meta"]
    assert meta["min_text_pt"] == 13 and meta["width_in"] > 1 and meta["lint"] == []
    lesson = LessonSpec(id="t", title="t", sections=[{"kind": "plain", "items": [
        {"n": "1", "prompt": "p", "figure": "tri", "fig_w": meta["width_in"] / 2, "answer": "x"}]}])
    issues = check_figures(lesson, res)
    assert any(i.startswith("ERROR") and "6.5 pt" in i for i in issues)


def test_box_width_minimum():
    lesson = LessonSpec(id="t", title="t", sections=[{"kind": "plain", "items": [
        {"n": "1", "prompt": "p", "fill": [["x =", "3"]], "box_w": 0.8},
        {"n": "2", "prompt": "p", "frame": [["a", "b", "c", 0.7]]}]}])
    items = [it for _, it in lesson.items()]
    assert _box_issues(items[0], "1") and _box_issues(items[1], "2")


def test_guide_join_and_punctuation():
    assert _join(["Half as long.", "Next"]) == "Half as long. Next"
    assert _join(["**half as long.**", "Next"]) == "**half as long.** Next"
    assert _join(["6", "8"]) == "6; 8"
    assert check_guide_text("x = 3.; y", "t") and check_guide_text("is **4**units", "t")
    assert not check_guide_text("is **4** units. **Next**, go", "t")


def test_prime_is_superscript_in_fractions():
    xml = db.latex_to_omml_inner(r"\frac{A'D'}{AD}", 11)
    assert xml.count("<m:sSup>") == 2 and "′" in xml
    assert db.latex_to_omml_inner(r"C^{\prime}", 11).count("<m:sSup>") == 1


def test_choice_rows_share_a_baseline():
    h = db.Handout()
    cell = h.doc.add_table(rows=1, cols=1).rows[0].cells[0]
    h._choices(cell, ["$\\frac{1}{4}$", "2", "$\\frac{5}{4}$", "4"], 4)
    assert not cell.tables and len([p for p in cell.paragraphs if "[A]" in p.text]) == 1
    assert np.all([("[B]" in p.text) == ("[A]" in p.text) for p in cell.paragraphs if p.text])

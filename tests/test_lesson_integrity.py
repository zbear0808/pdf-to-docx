from fractions import Fraction
from pathlib import Path

import yaml

from lesson_builder.integrity import check_set, compare, do_not_reuse, fingerprint, has_errors, numbers
from lesson_builder.spec import load_lesson


def _doc(tmp_path: Path, stem: str, items: list[dict], **top) -> Path:
    data = {"id": stem, "doc_type": "assessment", "title": stem, "sections": [{"kind": "plain", "items": items}],
            **top}
    p = tmp_path / f"{stem}.yaml"
    p.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return p


def _load(tmp_path, stem, items, **top):
    return load_lesson(_doc(tmp_path, stem, items, **top))


SPLIT_A = {"n": 1, "points": 3, "prompt": r"In $\triangle ABC$, $\overline{DE} \parallel \overline{BC}$. "
           "$AD = 5$, $DB = 6$, $BC = 8$. Solve for $x$.", "fill": [["$x =$", r"$\frac{40}{11}$"]]}
MC_A = {"n": 2, "points": 1, "prompt": "Which scale factor makes the image smaller?",
        "choices": [r"$\frac{7}{10}$", "3", r"$\frac{5}{4}$", "4"], "answer": r"[A] $\frac{7}{10}$ is below 1."}


def test_numbers_ignore_points_refs_and_small():
    nums, angles = numbers(r"(2 pts) See Problem 4 and Lesson 3.4. $m\angle B = 40^\circ$, $k = \frac{3}{7}$, "
                           "side 1 and 2, length 12.5. Each wrong choice loses $\\frac{1}{4}$ point.")
    assert sorted(nums) == sorted([Fraction(40), Fraction(3, 7), Fraction(25, 2)])
    assert angles == [Fraction(40)]


def test_same_letters_is_error(tmp_path):
    a = _load(tmp_path, "Test A", [SPLIT_A])
    b_item = {**SPLIT_A, "prompt": SPLIT_A["prompt"].replace("5", "4").replace("6", "9").replace("8", "15"),
              "fill": [["$x =$", "$\\frac{20}{13}$"]]}
    b = _load(tmp_path, "Test B", [b_item])
    msgs = compare(a, b)
    assert any(m.startswith("ERROR Test A item 1 vs Test B item 1: same letters ABCDE") for m in msgs)


def test_new_letters_and_numbers_are_clean(tmp_path):
    a = _load(tmp_path, "Test A", [SPLIT_A, MC_A])
    b = _load(tmp_path, "Test B", [
        {"n": 1, "points": 3, "prompt": r"In $\triangle FGH$, $\overline{JK} \parallel \overline{GH}$. "
         "$FJ = 6$, $JG = 9$, $GH = 20$. Solve for $x$.", "fill": [["$x =$", "8"]]},
        {**MC_A, "choices": ["3", r"$\frac{4}{3}$", "5", r"$\frac{3}{5}$"], "answer": r"[D] $\frac{3}{5}$ shrinks."}])
    assert compare(a, b) == []


def test_identical_numbers_is_error(tmp_path):
    a = _load(tmp_path, "PC A", [{"n": 1, "prompt": r"Dilate $\triangle ABC$ from $P$ by 2.",
                                  "answer": "A is 3 right, 4 up, so A' is 6 right, 8 up."}])
    b = _load(tmp_path, "PC B", [{"n": 1, "prompt": r"Dilate $\triangle RST$ from $Q$ by 2.",
                                  "answer": "R is 3 left, 4 up, so R' is 6 left, 8 up."}])
    assert any(m.startswith("ERROR PC A item 1 vs PC B item 1: same numbers 3, 4, 6, 8") for m in compare(a, b))


def test_same_key_positions_warn(tmp_path):
    mk = lambda n, letters: {"n": n, "prompt": f"Pick one ({letters}).", "choices": ["w", "x", "y", "z"],
                             "key": "B"}
    a = _load(tmp_path, "Q A", [mk(1, "PQ"), mk(2, "RS")])
    b = _load(tmp_path, "Q B", [mk(1, "TU"), mk(2, "VW")])
    msgs = compare(a, b)
    assert any(m.startswith("WARN  Q A vs Q B: MC key in the same position on 2 of 2") for m in msgs)
    assert not has_errors(msgs)


def test_review_reusing_triple_is_error(tmp_path):
    test = _load(tmp_path, "Unit Test A", [{"n": 5, "points": 2, "prompt": "Rectangle $ABCD$. $EF = 8$ and "
                                            "$ED = 10$. Find $FD$.", "fill": [["$FD =$", "6"]]}])
    notes = _load(tmp_path, "Notes", [{"prompt": ["In the figure, $k = \\frac{6}{3} = 2$.", "Check: 8 and 10."]}],
                  doc_type="reference")
    msgs = do_not_reuse(notes, [test])
    assert any(m.startswith("ERROR Notes item #1 vs Unit Test A item 5: prints all of the test item's numbers "
                            "6, 8, 10 (answer 6)") for m in msgs)
    clean = _load(tmp_path, "Notes2", [{"prompt": ["Lengths 4, 5, 7 become 8, 10, 14."]}], doc_type="reference")
    assert not has_errors(do_not_reuse(clean, [test]))


def test_review_reusing_angles_is_error(tmp_path):
    test = _load(tmp_path, "T", [{"n": 3, "prompt": "The triangles are similar.", "figure": "t3",
                                  "fill": [[r"$m\angle J =$", r"$62^\circ$"]]}])
    review = _load(tmp_path, "R", [{"n": 8, "prompt": r"Find $x$ in $\triangle DOG$.", "figure": "r8",
                                    "fill": [["$x =$", "70"]]}])
    rt = {"t3": {"meta": {"labels": [{"text": r"$48^\circ$", "layer": "given"}, {"text": "70°", "layer": "given"}]}}}
    rr = {"r8": {"meta": {"labels": [{"text": "48°", "layer": "given"}, {"text": "70°", "layer": "given"},
                                     {"text": "62°", "layer": "given"}]}}}
    msgs = do_not_reuse(review, [test], fps={"T": fingerprint(test, rt), "R": fingerprint(review, rr)})
    assert any(m.startswith("ERROR R item 8 vs T item 3: same angles 48/62/70") for m in msgs)


def test_figure_labels_from_meta(tmp_path):
    item = {"n": 1, "prompt": "Use the figure. Find the missing side.", "figure": "f1", "fill": [["$x =$", "9"]]}
    a = _load(tmp_path, "A", [item])
    b = _load(tmp_path, "B", [{**item, "figure": "f2"}])
    meta = lambda pts: {"meta": {"labels": [{"text": p, "layer": "given"} for p in pts],
                                 "key_labels": [{"text": "9", "layer": "answer"}]}}
    fa = fingerprint(a, {"f1": meta(["$K$", "L", "M", "12", "15"])})
    assert fa["1"].letters == {"K", "L", "M"} and fa["1"].fig_letters == {"K", "L", "M"}
    assert Fraction(9) in fa["1"].answers
    fb = fingerprint(b, {"f2": meta(["K", "L", "M", "20", "25"])})
    assert any("same letters KLM" in m and m.startswith("ERROR") for m in compare(a, b, fa=fa, fb=fb))


def test_check_set_with_figure_sources(tmp_path):
    unit = tmp_path / "unit"
    (unit / "assessments").mkdir(parents=True)
    (unit / "figures").mkdir()
    (unit / "unit.yaml").write_text(yaml.safe_dump({"course": "Geometry", "unit": 3, "unit_title": "Similarity",
                                                    "lessons": [], "assessments": ["assessments/*.yaml"],
                                                    "figures": "figures"}), encoding="utf-8")
    item = {"n": 1, "prompt": "Find $x$.", "figure": "{stem}_f", "fill": [["$x =$", "8"]]}
    for stem, pts in (("PC A", ("A", "B", "C", "6", "9")), ("PC B", ("A", "B", "C", "4", "10"))):
        _doc(unit / "assessments", stem, [{**item, "figure": f"{stem}_f"}], set="PC", form=stem[-1])
        calls = "\n".join(f"    f.label((0, 0), {p!r})" for p in pts[:3])
        sides = "\n".join(f"    f.side_label((0, 0), (1, 0), {p!r}, (0, 1))" for p in pts[3:])
        (unit / "figures" / f"{stem}.py").write_text(
            f"from lesson_builder.figures import Figure, figure\n\n\n@figure({stem + '_f'!r})\ndef f():\n"
            f"    f = Figure()\n{calls}\n{sides}\n    f.label((1, 1), 'X', layer='answer')\n    return f\n",
            encoding="utf-8")
    _doc(unit / "assessments", "Review", [{"n": 1, "prompt": "Sides 6, 9, and 8."}], do_not_reuse=["PC*"])
    msgs = check_set(unit, ["PC"])
    assert any(m.startswith("ERROR PC A item 1 vs PC B item 1: same letters ABC") for m in msgs)
    assert any(m.startswith("ERROR Review item 1 vs PC A item 1: prints all") for m in msgs)
    assert has_errors(msgs)
    assert check_set(unit, ["nothing*"]) == ["ERROR no document matches 'nothing*'"]

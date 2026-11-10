"""check_spec rules: MC keys and choices, voice, targets, refs, money, block-scalar primes, figures, selected."""
import textwrap

import pymupdf

from lesson_builder.check import _labels, check_spec
from lesson_builder.spec import UnitSpec, load_lesson
from lesson_builder.voice import voice_issues

HEAD = "id: T1\ndoc_type: assessment\ntitle: Quiz\n"


def _unit(tmp_path, targets=()):
    u = UnitSpec(course="Geometry", unit="3", unit_title="Similarity", lessons=[], targets=list(targets))
    u.dir = tmp_path
    return u


def _check(tmp_path, body, targets=(), figures=None, head=HEAD):
    p = tmp_path / "doc.yaml"
    p.write_text(head + textwrap.dedent(body), encoding="utf-8")
    return check_spec(_unit(tmp_path, targets), load_lesson(p), figures)


def _mc(n, key, choices="['1', '2', '3', '4']", extra=""):
    return f"      - n: {n}\n        prompt: 'Pick one.'\n        choices: {choices}\n        answer: '[{key}] ok'\n{extra}"


def _sections(*items):
    return "sections:\n  - kind: plain\n    items:\n" + "".join(items)


def _has(issues, text, level=""):
    return any(text in i and i.startswith(level) for i in issues)


def test_mc_choice_rules(tmp_path):
    good = _check(tmp_path, _sections(_mc(1, "B"), _mc(2, "A", "['True', 'False']"),
                                      _mc(3, "A], [E", "['1', '2', '3', '4', '5']")))
    assert good == []
    bad = _check(tmp_path, _sections(
        _mc(1, "B", "['1', '2', '3', '4', '5']"),
        _mc(2, "A", "['1', '1', '', '4']"),
        _mc(3, "A", "['1', '2', 'all of the above', 'both A and B']"),
        _mc(4, "A", "['2', '3', '4', 'the triangles are similar by AA']"),
        _mc(5, "E"),
        _mc(6, "A", extra="        key: C\n")))
    assert _has(bad, "item 1: 5 choices", "WARN")
    assert _has(bad, "item 2: empty choice", "ERROR") and _has(bad, "item 2: duplicate choices", "ERROR")
    assert _has(bad, "item 3: choice C", "ERROR") and _has(bad, "item 3: choice D", "ERROR")
    assert _has(bad, "item 4: choice D is over twice", "WARN")
    assert _has(bad, "item 5: key letter E is outside the choices A-D", "ERROR")
    assert _has(bad, "item 6: key C but the answer starts with [A]", "ERROR")


def test_mc_key_pattern(tmp_path):
    same = _check(tmp_path, _sections(*(_mc(k, "B") for k in range(1, 5))))
    assert _has(same, "B is the key on 4 of 4", "WARN") and _has(same, "key B three times in a row", "WARN")
    mixed = _check(tmp_path, _sections(*(_mc(k, x) for k, x in zip(range(1, 6), "ABCDA"))))
    assert not _has(mixed, "is the key on") and not _has(mixed, "in a row")
    sel = _check(tmp_path, _sections(*(_mc(k, "B") for k in range(1, 4))).replace("'[B] ok'", "'[B], [C] ok'"))
    assert not _has(sel, "in a row")


def test_voice_issues():
    assert any("crucial" in m for m in voice_issues("This is a crucial step."))
    assert any("navigat" in m for m in voice_issues("Navigating the grid"))
    assert voice_issues("Find $x$ \u2014 then stop.") and voice_issues("Find it - then stop.")
    assert voice_issues("Great job!")
    assert voice_issues("Find $5!$ and $a - b$, then `i--` and 3 - 2.") == []
    assert voice_issues("Underscore is a character? No: the robustness test.") != []   # "underscore"


def test_voice_in_student_text_only(tmp_path):
    body = _sections("      - n: 1\n        prompt: 'A crucial step!'\n        answer: 'A pivotal answer!'\n")
    issues = _check(tmp_path, body)
    assert _has(issues, "item 1: banned word 'crucial'", "WARN") and _has(issues, "exclamation", "WARN")
    assert not _has(issues, "pivotal")


def test_targets_and_demand(tmp_path):
    t = [{"id": "LT1"}, {"id": "LT2"}]
    item = "      - n: {n}\n        prompt: p\n        answer: a\n        target: {t}\n        demand: {d}\n"
    body = "targets: [{id: LT1}]\n" + _sections(item.format(n=1, t="LT9", d="pwoc"),
                                                *(item.format(n=k, t="LT1", d="mem") for k in (2, 3, 4)))
    issues = _check(tmp_path, body, targets=t)
    assert _has(issues, "target id LT1 is defined 2 times", "ERROR")
    assert _has(issues, "item 1: target 'LT9' isn't in", "ERROR")
    assert _has(issues, "all 4 items with `demand` are mem/pwoc", "WARN")
    ok = _check(tmp_path, _sections(item.format(n=1, t="LT1", d="pwc"), item.format(n=2, t="LT1", d="mem")),
                targets=t)
    assert _has(ok, "target LT2 has no items", "WARN") and not _has(ok, "LT1")
    assert not _has(ok, "procedural")


def test_unresolved_refs_and_plan_problems(tmp_path):
    body = _sections("      - n: 1\n        id: first\n        prompt: 'Use {ref:first}.'\n        answer: a\n",
                     "      - n: 2\n        prompt: 'Use {ref:nope}.'\n        answer: '{num:first}'\n")
    body += "plan: 'Go over Problem 1, then Problems 2-3.'\nguide_notes: 'Problem 2 is fine.'\n"
    issues = _check(tmp_path, body)
    assert _has(issues, "{ref:nope}: unknown id", "ERROR") and not _has(issues, "{ref:first}")
    assert _has(issues, "plan: refers to Problem 3", "WARN") and not _has(issues, "Problem 1,")
    assert not _has(issues, "guide_notes")


def test_money_and_odd_dollars(tmp_path):
    body = _sections("      - n: 1\n        prompt: 'Pens cost $3 and $5 each.'\n        answer: '$x = 2$'\n",
                     "      - n: 2\n        prompt: 'It costs $4.'\n        answer: '$3 \\cdot 4$'\n")
    issues = _check(tmp_path, body)
    assert _has(issues, "item 1: '$3 and $' looks like money", "WARN")
    odd = [i for i in issues if "odd number" in i]
    assert odd and "dollars" in odd[0] and "\\$" not in odd[0]
    assert not _has(issues, "item 2: '$3")


def test_block_scalar_primes(tmp_path):
    body = _sections("      - n: 1\n        prompt: 'Lin''s image $A''$'\n        answer: |\n"
                     "          $A''$ is the image.\n")
    body += "plan: |\n  Ask where $B''$ lands.\n\n  Then go on.\nguide_notes: 'fine'\n"
    issues = [i for i in _check(tmp_path, body) if "double prime" in i]
    assert len(issues) == 2 and "line 10" in issues[0] and "line 12" in issues[1]


def test_figure_refs(tmp_path):
    item = "      - n: {n}\n        prompt: p\n        answer: a\n        figure: {f}\n"
    body = _sections(item.format(n=1, f="tri"), item.format(n=2, f="nope"), item.format(n=3, f="assets/gone.png"))
    issues = _check(tmp_path, body, figures={"tri": {"student": "x.png", "meta": {}}})
    assert _has(issues, "item 2: figure 'nope'", "ERROR") and _has(issues, "item 3: figure 'assets/gone.png'")
    assert not _has(issues, "'tri'")
    unrendered = _check(tmp_path, body)
    assert not _has(unrendered, "'nope'") and _has(unrendered, "'assets/gone.png'", "ERROR")
    empty = _check(tmp_path, body, figures={})
    assert _has(empty, "'tri' is not a registered figure", "ERROR")


def test_practice_selected_and_header_right(tmp_path):
    body = _sections("      - n: 1\n        prompt: p\n        answer: a\n")
    body += ("practice:\n  title: Practice\n  rows:\n    - cells:\n        - n: 1\n          prompt: p\n"
             "          answer: a\n  selected: [[1, a], [7, b], '2']\n")
    issues = _check(tmp_path, body, head=HEAD + "header_right: 'Score ___'\n")
    assert _has(issues, "practice selected: 7 isn't", "ERROR") and _has(issues, "practice selected: 2 isn't")
    assert not _has(issues, "selected: 1 ")
    assert _has(issues, "header_right is deprecated", "WARN")


def test_output_labels_three_digits_and_late_parts(tmp_path):
    doc = pymupdf.open()
    pg = doc.new_page()
    pg.insert_text((72, 100), "100.", fontname="hebo")
    pg.insert_text((72, 140), "f.", fontname="helv")
    pg.insert_text((72, 180), "1000.", fontname="hebo")
    labels = _labels(doc)
    assert [(lb["kind"], lb["text"]) for lb in labels] == [("num", "100."), ("part", "f.")]

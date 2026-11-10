from pathlib import Path

from typer.testing import CliRunner

from lesson_builder.check import check_spec
from lesson_builder.cli import app
from lesson_builder.render import Figures, guide_markdown, render_lesson
from lesson_builder.spec import Item, load_unit


def _unit(tmp_path: Path):
    dest = tmp_path / "unit"
    r = CliRunner().invoke(app, ["new-unit", str(dest), "--course", "Algebra 1", "--unit", "3",
                                 "--title", "Linear functions"])
    assert r.exit_code == 0, r.output
    return load_unit(dest)


def test_template_renders_and_passes_spec_checks(tmp_path):
    from lesson_builder.cli import _figs_for, _figures
    u = _unit(tmp_path)
    assert u.course == "Algebra 1" and u.budget.minutes == 40
    figs = _figures(u)
    assert figs[""]["build_fig"]["key"] is not None
    assert figs["example"]["dilate_abc"]["key"] is not None   # figures/example.py, used by the assessment
    lesson, assessment = u.lesson_specs()
    assert (lesson.doc_type, assessment.doc_type) == ("lesson", "assessment")
    for doc in (lesson, assessment):
        lf = _figs_for(figs, doc)
        assert check_spec(u, doc, lf) == [], doc.id
        out = render_lesson(u, doc, Figures(u, lf))
        assert all(p.exists() for p in out.values())
        assert len(out) == 5 if doc is lesson else {"handout", "key"} <= set(out)
    assert "Answer key" in guide_markdown(lesson)


def test_spec_checks_catch_known_problems(tmp_path):
    u = _unit(tmp_path)
    lesson = next(l for l in u.lesson_specs() if l.doc_type == "lesson")
    partner = next(s for s in lesson.sections if s.kind == "partner")
    partner.items.append(Item(n="9", prompt="Fill in: ___ is congruent. Use your claim from Problem 7.", work=1))
    partner.items.append(Item(n="10", prompt="Draw the image of the triangle.", work=1, answer="see figure"))
    partner.items[0].minutes = 60
    msgs = "\n".join(check_spec(u, lesson, {}))
    assert "'___' blank" in msgs
    assert "Problem 7, which isn't in this part" in msgs
    assert "item 9: no answer" in msgs
    assert "item 10: drawing task without a key figure" in msgs
    assert "budget is 40" in msgs

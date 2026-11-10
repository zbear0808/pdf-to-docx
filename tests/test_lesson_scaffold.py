from pathlib import Path

import pytest
from typer.testing import CliRunner

from lesson_builder.brief import brief, planned_figures, source_files, yaml_blocks
from lesson_builder.check import check_spec
from lesson_builder.cli import _figs_for, _figures, app
from lesson_builder.render import Figures, render_lesson
from lesson_builder.scaffold import add_to_list, lesson_minutes, scaffold
from lesson_builder.spec import load_lesson, load_unit


def _unit(tmp_path: Path, period: str = "Period 4") -> Path:
    dest = tmp_path / "unit"
    r = CliRunner().invoke(app, ["new-unit", str(dest), "--course", "Geometry", "--unit", "4",
                                 "--title", "Right triangles", "--period", period])
    assert r.exit_code == 0, r.output
    return dest


def _render_and_check(dest: Path, stems: list[str]):
    u = load_unit(dest)
    specs = u.lesson_specs(stems)
    assert {s.stem for s in specs} == set(stems)
    figs = _figures(u, docs=set(stems))
    for s in specs:
        lf = _figs_for(figs, s)
        assert f"{s.stem}_example" in lf
        issues = check_spec(u, s, lf)
        assert issues and all("TODO" in i for i in issues), (s.stem, issues)   # only the TODO placeholders
        out = render_lesson(u, s, Figures(u, lf))
        assert all(p.exists() for p in out.values())
    return u, specs


def test_scaffold_lesson(tmp_path):
    dest = _unit(tmp_path)
    written = scaffold(dest, "4.1", title="Pythagoras")
    names = {p.relative_to(dest).as_posix() for p in written}
    assert names == {"lessons/4.1.yaml", "figures/4.1.py", "_temp/specs/4.1/requirements.md",
                     "_temp/specs/4.1/changes.md", "unit.yaml"}
    text = (dest / "unit.yaml").read_text(encoding="utf-8")
    assert "  - example.yaml\n  - 4.1.yaml\n" in text and "# files in lessons/" in text
    u, (l,) = _render_and_check(dest, ["4.1"])
    assert l.title == "Pythagoras" and l.minutes <= u.budget.minutes
    assert [s.kind for s in l.sections] == ["warmup", "together", "partner", "notes", "cyu", "exit"]
    assert "TODO" in l.raw and "| 38-40 |" in l.plan and "Problem 1" in l.sections[2].items[0].prompt
    req = (dest / "_temp/specs/4.1/requirements.md").read_text(encoding="utf-8")
    for h in ("## 1. Intake", "## 2. Targets", "## 3. Blueprint", "## 4. Figure plan"):
        assert h in req
    assert "Version table" not in req
    # never overwrites; force does
    (dest / "lessons/4.1.yaml").write_text("id: '4.1'\n", encoding="utf-8")
    assert scaffold(dest, "4.1") == []
    assert (dest / "lessons/4.1.yaml").read_text(encoding="utf-8") == "id: '4.1'\n"
    assert dest / "lessons/4.1.yaml" in scaffold(dest, "4.1", force=True)
    assert load_unit(dest).lessons == ["example.yaml", "4.1.yaml"]


def test_scaffold_assessment_forms(tmp_path):
    dest = _unit(tmp_path)
    y = dest / "unit.yaml"
    y.write_text("\n".join(ln for ln in y.read_text(encoding="utf-8").splitlines()
                           if not ln.startswith("assessments:")) + "\n", encoding="utf-8")
    assert load_unit(dest).assessments == []
    written = scaffold(dest, "Unit 4 Test", "assessment", forms=["A", "B", "Retake"])
    assert y in written and "assessments: [assessments/*.yaml]" in y.read_text(encoding="utf-8")
    stems = ["Unit 4 Test A", "Unit 4 Test B", "Unit 4 Test Retake"]
    _, specs = _render_and_check(dest, stems)
    by = {s.stem: s for s in specs}
    assert by["Unit 4 Test B"].set == "Unit 4 Test" and by["Unit 4 Test B"].form == "B"
    assert by["Unit 4 Test B"].parallel_to == "Unit 4 Test A" and by["Unit 4 Test A"].parallel_to is None
    assert all(s.numbering == "auto" and s.total_points == s.points for s in specs)
    req = (dest / "_temp/specs/Unit 4 Test/requirements.md").read_text(encoding="utf-8")
    assert "## 5. Version table" in req and "| item | A | B | Retake |" in req
    assert planned_figures(req) == [f"{s}_example" for s in stems]
    assert all((dest / "_temp/specs" / s / "changes.md").exists() for s in stems)


def test_scaffold_reference_and_errors(tmp_path):
    dest = _unit(tmp_path)
    written = scaffold(dest, "Unit 4 Summary", "reference")
    assert dest / "unit.yaml" not in written   # assessments/*.yaml already covers it
    _, (s,) = _render_and_check(dest, ["Unit 4 Summary"])
    assert s.doc_type == "reference"
    with pytest.raises(ValueError):
        scaffold(dest, "4.2", "lesson", forms=["A"])
    with pytest.raises(ValueError):
        scaffold(dest, "4.2", "quiz")


def test_add_to_list_keeps_layout():
    block = "lessons:   # order\n  - a.yaml\n\n  # comment\nfigures: f.py\n"
    assert add_to_list(block, "lessons", "b.yaml") == "lessons:   # order\n  - a.yaml\n  - b.yaml\n\n  # comment\nfigures: f.py\n"
    assert add_to_list("assessments: [x/*.yaml]  # c\n", "assessments", "y/Test A.yaml") == \
        "assessments: [x/*.yaml, y/Test A.yaml]  # c\n"
    assert add_to_list("lessons: []\r\n", "lessons", "a.yaml") == "lessons: [a.yaml]\r\n"
    assert add_to_list("course: G", "assessments", "assessments/*.yaml") == "course: G\nassessments: [assessments/*.yaml]\n"
    assert lesson_minutes(40)[-1] >= 0 and sum(lesson_minutes(50)) == 50 and sum(lesson_minutes(5)) == 5


def _ingest(dest: Path):
    ing = dest / "_temp" / "ingest"
    (ing / "Lesson 4.1 Handout_pages").mkdir(parents=True)
    (ing / "Lesson 4.1 Handout_pages" / "page1.png").write_bytes(b"png")
    (ing / "Lesson 4.1 Handout.md").write_text("\n".join(f"source line {i}" for i in range(450)), encoding="utf-8")
    (ing / "Lesson 4.10 Handout.md").write_text("other lesson", encoding="utf-8")
    (ing / "Unit 4 Test Form A.md").write_text("test source", encoding="utf-8")


def test_brief_sections_per_step(tmp_path):
    dest = _unit(tmp_path)
    scaffold(dest, "4.1")
    _ingest(dest)
    u = load_unit(dest)
    srcs = source_files(u, "4.1", {"id": "4.1"})
    assert [p.name for p in srcs] == ["Lesson 4.1 Handout.md"]   # 4.10 is not 4.1
    common = ["## Load", "## Read", "## Write only", "## Done when", "## Rules", "## Reply", "Period 4",
              "Geometry Unit 4"]
    texts = {}
    for step in ("plan", "figures", "write", "audit"):
        p = brief(dest, "4.1", step)
        assert p == dest / "_temp/specs/4.1" / f"brief_{step}.md"
        texts[step] = t = p.read_text(encoding="utf-8")
        assert all(c in t for c in common), step
        assert brief(dest, "4.1", step).read_text(encoding="utf-8") == t   # deterministic
    plan, figs, write, audit = (texts[k] for k in ("plan", "figures", "write", "audit"))
    assert "## Source text" in plan and "source line 399" in plan and "source line 400" not in plan
    assert "truncated at 400 of 450 lines" in plan and "Lesson 4.1 Handout_pages/` (1 file;" in plan
    assert "`lesson-scope`" in plan and "`mll-literacy-scaffolding`" in plan and "sections 2-4" in plan
    assert "## Figure names" in figs and "`4.1_example`" in figs and "**Draw**" in figs
    assert "lesson-builder figs" in figs and "figures/4.1.py`" in figs
    assert "## Schema (lesson)" in write and "- `notes_title`" in write and "- `total_points`" not in write
    assert "### Section `kind: warmup`" in write and "### Section `kind: exit`" in write and "### `practice:`" in write
    assert "lesson-builder build" in write and "Student Handout.pdf" in audit and "audit.md` only" in audit
    with pytest.raises(ValueError):
        brief(dest, "4.1", "release")
    with pytest.raises(FileNotFoundError):
        brief(dest, "9.9", "plan")


def test_brief_assessment_form(tmp_path):
    dest = _unit(tmp_path, period="Period 5")
    scaffold(dest, "Unit 4 Test", "assessment", forms=["A", "B"])
    _ingest(dest)
    a = dest / "assessments" / "Unit 4 Test A.yaml"
    a.write_text(a.read_text(encoding="utf-8") + "source: 'Lesson 4.1 Handout'\n", encoding="utf-8")
    assert load_lesson(a).source == "Lesson 4.1 Handout"
    plan = brief(dest, "Unit 4 Test A", "plan").read_text(encoding="utf-8")
    assert "_temp/specs/Unit 4 Test/requirements.md" in plan and "sections 2-5" in plan
    assert "Lesson 4.1 Handout.md` (inline below)" in plan and "Exam integrity" in plan
    assert "mll-literacy-scaffolding" not in plan   # Period 5 is not the MLL period
    b = brief(dest, "Unit 4 Test B", "write").read_text(encoding="utf-8")
    assert "Unit 4 Test Form A.md" not in b   # sources are inlined only for the plan step
    assert "parallel to Unit 4 Test A" in b and "## Schema (assessment)" in b and "- `total_points`" in b
    assert "- `notes_title`" not in b and "### Section `kind: plain`" in b


def test_yaml_blocks_split_template():
    from lesson_builder.brief import TEMPLATES
    keys = [k for k, _ in yaml_blocks((TEMPLATES / "lessons" / "example.yaml").read_text(encoding="utf-8"))]
    assert keys[0] == "header" and "section:warmup" in keys and "section:notes" in keys and "plan" in keys

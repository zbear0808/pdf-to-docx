"""Kitchen-sink fixture (tooling plan T10): every schema field and figure helper, built end to end.

tests/fixtures/kitchen_sink is copied to tmp_path first, so nothing is ever written into the fixture."""
import re
import shutil
from pathlib import Path

import pytest
from docx import Document
from docx.oxml.ns import qn
from pydantic import BaseModel
from typer.testing import CliRunner

from lesson_builder import cli
from lesson_builder import docbuilder as db
from lesson_builder import spec as S
from lesson_builder.check import _printed_len, check_outputs, check_spec, placed_widths
from lesson_builder.export import word_available
from lesson_builder.integrity import check_set, has_errors
from lesson_builder.render import Figures, guide_markdown, outputs, render_lesson, selected_answers
from lesson_builder.retain import retain, verify

FIXTURE = Path(__file__).parent / "fixtures" / "kitchen_sink"
DOCS = {"ks", "KS Notes", "KS Review", "KS Test A", "KS Test B"}
needs_word = pytest.mark.skipif(not word_available(), reason="Microsoft Word / pywin32 not available")
runner = CliRunner()


def _copy(dest: Path) -> Path:
    shutil.copytree(FIXTURE, dest, ignore=shutil.ignore_patterns("__pycache__", "_temp", "output"))
    return dest


@pytest.fixture(scope="module")
def ks(tmp_path_factory):
    """One copy with figures rendered and every document rendered to DOCX (no Word)."""
    d = _copy(tmp_path_factory.mktemp("ks") / "kitchen_sink")
    unit = S.load_unit(d)
    figs = cli._figures(unit)
    docs = {l.stem: l for l in unit.lesson_specs()}
    out = {stem: render_lesson(unit, l, Figures(unit, cli._figs_for(figs, l))) for stem, l in docs.items()}
    return unit, figs, docs, out


@pytest.fixture
def fresh(tmp_path):
    return _copy(tmp_path / "kitchen_sink")


def _fields(models) -> dict[type, set[str]]:
    seen: dict[type, set[str]] = {}

    def walk(m):
        if isinstance(m, BaseModel):
            seen.setdefault(type(m), set()).update(m.model_fields_set)
            for k in m.model_fields_set:
                walk(getattr(m, k))
        elif isinstance(m, (list, tuple)):
            for x in m:
                walk(x)
        elif isinstance(m, dict):
            for x in m.values():
                walk(x)
    walk(list(models))
    return seen


def test_every_field_is_used(ks):
    unit, _, docs, _ = ks
    assert set(docs) == DOCS
    seen = _fields([unit, *docs.values()])
    scored = set(S._Scored.model_fields)
    used_scored = (seen.get(S.Item, set()) | seen.get(S.Part, set())) & scored
    assert used_scored == scored, f"_Scored fields never set: {sorted(scored - used_scored)}"
    exempt = {S.LessonSpec: {"header_right", "path", "raw"}, S.UnitSpec: {"dir"}}
    for cls in (S.UnitSpec, S.Budget, S.Target, S.LessonSpec, S.Section, S.Item, S.Part, S.Table, S.Columns,
                S.Draw, S.Practice, S.PracticeRow, S.RubricLevel, S.NoteBlock):
        want = set(cls.model_fields) - exempt.get(cls, set()) - (scored if cls in (S.Item, S.Part) else set())
        missing = want - seen.get(cls, set())
        assert not missing, f"{cls.__name__} fields never set in the fixture: {sorted(missing)}"
    kinds = {s.kind for l in docs.values() for s in l.sections}
    assert kinds == {"warmup", "together", "partner", "notes", "cyu", "exit", "plain"}
    assert {l.doc_type for l in docs.values()} == {"lesson", "assessment", "reference"}
    assert {it.fig for l in docs.values() for it in l.all_items() if it.fig} == {"small", "medium"}


def test_specs_are_clean(ks):
    unit, figs, docs, _ = ks
    for l in docs.values():
        assert check_spec(unit, l, cli._figs_for(figs, l)) == [], l.stem


def test_auto_numbers_and_refs(ks):
    _, _, docs, _ = ks
    l = docs["ks"]
    assert [it.n for _, it in l.items()] == [None, None, "1", "2", "3", "4", "5", "1", "2", "3", "4"]
    assert [c.n for r in l.practice.rows for c in r.cells] == [str(k) for k in range(1, 8)]
    items = {it.id: it for _, it in l.items() if it.id}
    assert items["arrow_table"].prompt == "Where does each vertex in Problem 1 land?"
    assert items["why_frame"].prompt == "Use your table from Problem 2. Fill in each box."
    assert items["why_frame"].frame[0][0] == "In Problem 2, $B$ landed on"
    assert items["why_frame"].frame[1] == ["A reflection does not change", "length", ".", 1.3]   # named row
    assert "Problem 1 sets up the\ntable in Problem 2; the frame in Problem 3 uses it." in l.plan
    assert "Partner problem 4 replaced" in l.guide_notes and "Part 5a has" in l.guide_notes
    assert [it.n for _, it in docs["KS Test A"].items()] == [str(k) for k in range(1, 8)]
    sel = selected_answers(l)
    assert sel[0][0] == "1" and ("2", "4") in sel and ("3", "1.5") in sel and len(sel) == 7
    assert next(l.items())[1].width == S.FIG_SIZES["small"]


def test_render_outputs_and_guides(ks):
    unit, _, docs, out = ks
    for stem, o in out.items():
        assert o == outputs(unit, docs[stem]) and all(p.is_file() for p in o.values()), stem
    assert set(out["ks"]) == {"handout", "key", "practice", "practice_key", "guide"}
    assert set(out["KS Notes"]) == {"handout"}
    for t in ("KS Test A", "KS Test B", "KS Review"):
        assert out[t]["guide"].name == f"{t} Teacher Notes.docx"
    md = guide_markdown(docs["KS Test A"])
    assert "## Blueprint" in md and "| 6a | LT2 | cr | pwoc | 2 |" in md and "| 7 | LT2 | performance | dm | 4 |" in md
    assert "Demand count: mem 2, pwoc 4, pwc 1, dm 1" in md
    assert "### Distractors" in md and "| 3 | B | C | divided by the scale factor |" in md
    assert "(scored E/P/I)" in md and "- Rubric E: Says no" in md
    # regression: guide_notes start a new paragraph instead of running on from the demand count
    assert "dm 1\n\n**Scoring notes.**" in md
    lmd = guide_markdown(docs["ks"])
    assert "| 5a | A | B | swaps the first two vertices |" in lmd and "## Lesson plan" in lmd
    for stem, o in out.items():
        for p in o.values():
            text = "\n".join(par.text for par in Document(str(p)).paragraphs)
            assert "{ref:" not in text and "{num:" not in text, p.name


def test_figures_retain_and_verify(ks):
    unit, figs, docs, _ = ks
    assert set(figs) == {"", "ks", "KS Review", "KS Test A", "KS Test B"}
    ks_figs = figs["ks"]
    assert {"ks_reflect", "ks_rotation", "ks_congruent", "ks_coord", "ks_numberline", "ks_dilate", "ks_split",
            "ks_rects", "ks_dotplot", "ks_array", "ks_union", "ks_custom"} <= set(ks_figs)
    for name in ("ks_union",):
        meta = ks_figs[name]["meta"]
        assert meta["key_frame"] == "union" and meta["key_width_in"] > meta["width_in"] + 0.5
    assert all(not r["meta"]["lint"] for f in figs.values() for r in f.values())
    # regression: the contact sheet sizes only explicit fig_w / fig uses; a union key at natural width keeps
    # its own (wider) width instead of being squeezed to the student width
    lf = cli._figs_for(figs, docs["ks"])
    assert "ks_union" in placed_widths(docs["ks"], lf)
    assert "ks_union" not in placed_widths(docs["ks"], lf, explicit=True)
    assert "ks_reflect" in placed_widths(docs["ks"], lf, explicit=True)
    # regression: importing figures/_helpers.py leaves no figures/__pycache__ for `tidy` to report
    assert not list(unit.dir.rglob("__pycache__"))
    for stem, l in docs.items():
        res = retain(unit, l, cli._figs_for(figs, l))
        assert res.errors == [], stem
        assert verify(unit, l) == [], stem
    readme = (unit.dir / "output" / "figures" / "ks" / "README.md").read_text(encoding="utf-8")
    assert "figures/ks.py:ks_union" in readme and "figures/_helpers.py" in readme
    assert "assets/ks_square.png` (Drawn for the kitchen-sink fixture" in readme


def test_integrity_clean_and_broken(ks, fresh):
    unit, figs, docs, _ = ks
    rendered = {stem: cli._figs_for(figs, l) for stem, l in docs.items()}
    assert check_set(unit, ["KS Test*"], ["KS Review"], rendered=rendered) == []
    assert check_set(unit, ["KS Test A"]) == []   # the Review's own do_not_reuse list still runs
    b = fresh / "assessments" / "KS Test B.yaml"
    swap = str.maketrans("DEG", "JKL")   # Form B's letters -> Form A's, inside math only
    b.write_text(re.sub(r"\$[^$]*\$", lambda m: m.group(0).translate(swap), b.read_text(encoding="utf-8")),
                 encoding="utf-8")
    msgs = check_set(S.load_unit(fresh), ["KS Test*"])
    assert has_errors(msgs)
    assert any(m.startswith("ERROR KS Test A item 1 vs KS Test B item 1: same letters JKL") for m in msgs), msgs


def test_helpers_are_per_folder(tmp_path):
    """Regression: `from _helpers import ...` got another folder's cached _helpers module."""
    other = tmp_path / "other"
    other.mkdir()
    (other / "_helpers.py").write_text("SIZE = 1.0\n", encoding="utf-8")
    (other / "doc.py").write_text("from _helpers import SIZE\n", encoding="utf-8")
    from lesson_builder.figures import load_module, render_all
    load_module(other / "doc.py")
    d = _copy(tmp_path / "kitchen_sink")
    got = render_all(d / "figures" / "KS Review.py", tmp_path / "out")
    assert set(got) == {"ksr_tri", "ksr_circle"}


def test_prime_math_starts_with_a_sized_run():
    """Regression: an equation that starts with A' (or a fraction) printed a tiny raised prime in Word at
    every size but 11 pt; add_math now puts a sized zero-width run in front."""
    def omml(tex, size):
        p = Document().add_paragraph()
        db.add_math(p, tex, size)
        return p._p.find(qn("m:oMath"))
    first, second = list(omml("A'", 10.5))[:2]
    assert first.tag == qn("m:r") and first.find(qn("m:t")).text == "\u200b"
    assert first.find(f"{qn('w:rPr')}/{qn('w:sz')}").get(qn("w:val")) == "21" and second.tag == qn("m:sSup")
    assert omml(r"\frac{A'D'}{AD}", 10)[0].find(qn("m:t")).text == "\u200b"
    for tex in (r"\triangle A'B'C'", "AB"):
        assert all(t.text != "\u200b" for t in omml(tex, 10).iter(qn("m:t"))), tex


def test_choice_length_reads_printed_text():
    """Regression: '$\\frac{5}{3}$' among whole numbers counted as 13 characters ("over twice the median")."""
    assert _printed_len(r"$\frac{5}{3}$") == 1 and _printed_len(r"$\angle W'$") == 3
    assert _printed_len("the triangles are similar by AA") == 31


def _ok(args):
    res = runner.invoke(cli.app, [str(a) for a in args])
    assert res.exit_code == 0, f"{args[0]} exited {res.exit_code}:\n{res.output}\n{res.exception!r}"
    return res.output


def test_cli_smoke(fresh):
    out = _ok(["figs", fresh])
    assert "0 errors, 0 warnings" in out and (fresh / "_temp" / "figures" / "ks_sheet.png").is_file()
    assert "0 errors, 0 warnings" in _ok(["check", fresh])
    assert "0 errors, 0 warnings" in _ok(["integrity", fresh, "--set", "KS Test*", "--vs", "KS Review"])
    out = _ok(["retain", fresh])   # not built yet: retained but not verified (WARN)
    assert "KS.1: 25 uses" in out and "0 errors" in out
    assert _ok(["tidy", fresh]).strip().endswith("clean")
    out = _ok(["status", fresh, "--checks"])
    assert all(stem in out for stem in DOCS)
    out = _ok(["brief", fresh, "ks", "--step", "write"])
    assert (fresh / "_temp" / "specs" / "ks" / "brief_write.md").is_file(), out
    _ok(["scaffold", fresh, "KS Quiz", "--type", "assessment", "--forms", "A,B"])
    assert (fresh / "figures" / "KS Quiz A.py").is_file() and (fresh / "figures" / "KS Quiz B.py").is_file()


@needs_word
def test_full_build_with_packets(fresh):
    out = _ok(["build", fresh])
    assert out.rstrip().splitlines()[-1].startswith("0 errors, 0 warnings"), out
    assert re.search(r"KS\.1 handout 3p/3: p1 [\d.]+ in \[1-3\]", out), out          # page-fill report
    assert re.search(r"KS Test A handout \dp/3", out) and "KS.1 practice 2p/2" in out
    o = fresh / "output"
    assert (o / "Geometry Unit KS Student Packet.pdf").is_file() and (o / "Geometry Unit KS Key Packet.docx").is_file()
    unit = S.load_unit(fresh)
    for l in unit.lesson_specs():
        pdfs = {k: v.with_suffix(".pdf") for k, v in outputs(unit, l).items()}
        assert all(p.is_file() for p in pdfs.values()), l.stem
        for a, b, n in cli._pairs(unit, l):
            if a in pdfs and b in pdfs:
                assert check_outputs(pdfs[a], pdfs[b], n) == [], (l.stem, a)
        assert verify(unit, l) == [], l.stem
    assert (fresh / "_temp" / "renders" / "current" / "ks" / "Lesson_KS.1_Student_Handout_p1.png").is_file()
    assert "0 errors, 0 warnings" in _ok(["check", fresh])
    assert _ok(["tidy", fresh]).strip().endswith("clean")

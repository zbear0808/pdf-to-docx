"""Shared-data pilot: a YAML edit must propagate to text, exact answers, and cached figures."""
import copy
import hashlib
import json
import os
import shutil
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
import yaml
from docx import Document
from pydantic import ValidationError

from lesson_builder.figures import render_all
from lesson_builder.figures.comparison import line_family, parallel_names, scaled_rectangles, split_triangle
from lesson_builder.problem_models import ScaledRectangles, format_value
from lesson_builder.render import Figures, guide_markdown, render_lesson
from lesson_builder.resolve import model_for_figure, resolve_values
from lesson_builder.spec import load_lesson, load_unit

UNIT = Path(__file__).parent / "fixtures/shared_data_pilot"
STEM = "3.1-3.5 Progress Check "


@pytest.mark.parametrize("form,k,answer,dimensions", [
    ("A", Fraction(3, 2), 15, ((10, 8), (15, 12))),
    ("B", Fraction(5, 2), 10, ((6, 4), (15, 10))),
    ("Retake A", Fraction(4, 3), 18, ((18, 9), (24, 12))),
    ("Retake B", Fraction(5, 3), 12, ((12, 6), (20, 10))),
])
def test_pilot_forms_use_their_checked_model(form, k, answer, dimensions):
    lesson = load_lesson(UNIT / "assessments" / f"{STEM}{form}.yaml")
    items = list(lesson.all_items())
    assert [it.n for it in items] == [str(i) for i in range(1, 7)]
    assert len({it.id for it in items}) == 6 and lesson.points == 10
    q3 = items[2]
    assert q3.model.scale == k and q3.model.facts()["answer"] == answer
    assert q3.model.dimensions() == dimensions
    assert q3.parts[0].fill[0][1] == f"${format_value(k)}$"
    assert q3.parts[1].fill[0][1] == str(answer)
    assert "{value:" not in lesson.model_dump_json(exclude={"raw"})
    assert all(it.key for it in items if it.choices)
    assert model_for_figure(UNIT / "figures" / f"{STEM}{form}.py", "q3") == q3.model


def model_data(**changes):
    return dict(kind="scaled_rectangles", source_name="M", image_name="N",
                source_known=8, image_known=12, given_other=10) | changes


@pytest.mark.parametrize("changes", [
    {"source_known": 0}, {"image_known": -1}, {"given_other": True},
    {"source_known": "nan"}, {"given_other": "1/0"}, {"given_on": "elsewhere"},
    {"kind": "arbitrary_python"}, {"image_name": "M"}, {"unknown_symbol": "x"},
    {"given_other": 1, "answer": 99},
])
def test_invalid_model_is_rejected(changes):
    with pytest.raises(ValidationError):
        ScaledRectangles(**model_data(**changes))


def test_decimal_inputs_are_exact_and_formats_are_explicit():
    m = ScaledRectangles(**model_data(source_known=0.1, image_known=0.3, given_other="2/7"))
    assert m.scale == 3 and m.image_other == Fraction(6, 7)
    assert format_value(m.image_other) == r"\frac{6}{7}"
    assert format_value(Fraction(5, 3), "comma2") == "1,67"
    assert format_value(Fraction(100, 3), "decimal1") == "33.3"
    assert format_value(Fraction(3, 2), "decimal2") == "1.5"


@pytest.mark.parametrize("ref", [
    "{value:absent.scale}", "{value:q3.not_a_fact}", "{value:q3.scale|exec}",
    "{value:q3.source_name|decimal2}", "{value:q3.scale", "{value:__import__('os')}",
])
def test_invalid_references_fail_before_render(ref):
    data = {"sections": [{"items": [{"id": "q3", "model": model_data(), "prompt": ref}]}]}
    with pytest.raises(ValueError):
        resolve_values(data)


def test_resolution_does_not_mutate_source_and_requires_stable_ids():
    data = {"sections": [{"items": [{"id": "q3", "model": model_data(),
                                     "prompt": "${value:q3.scale}$"}]}]}
    before = copy.deepcopy(data)
    assert resolve_values(data)["sections"][0]["items"][0]["prompt"] == r"$\frac{3}{2}$"
    assert data == before
    data["sections"][0]["items"][0].pop("id")
    with pytest.raises(ValueError, match="stable id"):
        resolve_values(data)


def test_unsupported_schema_version(tmp_path):
    p = tmp_path / "next.yaml"
    p.write_text("schema_version: 2\nid: test\ntitle: test\nsections: []\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="schema_version"):
        load_lesson(p)


def test_known_figure_constructions_and_inconsistent_labels():
    lines = [("a", (1, 1), 10, 1), ("b", (1, 2), 190, -1), ("c", (1, 2), 90, 1)]
    assert parallel_names(lines, "a") == {"a", "b"}
    assert len(line_family(lines).labels) == 3
    with pytest.raises(ValueError, match="unknown reference"):
        parallel_names(lines, "z")
    with pytest.raises(ValueError, match="unique"):
        line_family(lines + lines[:1])
    f, u, w = split_triangle((0, 0), (6, 0), (0, 9), 1 / 3,
                             ["V", "U", "W", "U'", "W'"], (("2", "4"), ("3", "6")))
    assert np.allclose(u, (2, 0)) and np.allclose(w, (0, 3))
    with pytest.raises(AssertionError, match="lengths"):
        split_triangle((0, 0), (6, 0), (0, 9), 1 / 3,
                       ["V", "U", "W", "U'", "W'"], (("2", "4"), ("3", "7")))


def test_yaml_change_updates_prompt_answer_guide_geometry_and_cache(tmp_path):
    stem = STEM + "A"
    unit = tmp_path / "unit"
    for folder, suffix in (("assessments", ".yaml"), ("figures", ".py")):
        (unit / folder).mkdir(parents=True)
        shutil.copy2(UNIT / folder / (stem + suffix), unit / folder / (stem + suffix))
    (unit / "unit.yaml").write_text("course: Geometry\nunit: 3\nunit_title: Pilot\nlessons: []\n"
                                   "assessments: [assessments/*.yaml]\n", encoding="utf-8")
    src = unit / "assessments" / (stem + ".yaml")
    fig_file = unit / "figures" / (stem + ".py")
    name = stem + "_q3"
    out = unit / "_temp" / "figures"
    first = render_all(fig_file, out, names=[name])
    png = first[name]["student"]
    digest = hashlib.sha256(png.read_bytes()).hexdigest()
    stamp = png.stat().st_mtime_ns
    render_all(fig_file, out, names=[name])
    assert png.stat().st_mtime_ns == stamp, "unchanged figures should use the cache"

    # The only mathematical edit: change the known image side from 12 to 16 (k becomes 2).
    data = yaml.safe_load(src.read_text(encoding="utf-8"))
    data["sections"][0]["items"][2]["model"]["image_known"] = 16
    src.write_text(yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
    # Ensure filesystem timestamp granularity cannot hide this edit.
    older = src.stat().st_mtime - 2
    for p in out.iterdir():
        os.utime(p, (older, older))
    lesson = load_lesson(src)
    q3 = lesson.sections[0].items[2]
    assert q3.parts[0].answer == "$16 \\div 8 = 2$"
    assert q3.parts[1].fill == [["$y =$", "20"]]
    assert "$y = 2 \\cdot 10 = 20$" in q3.parts[1].answer
    assert "credit $2$ or $2$" in guide_markdown(lesson)
    changed = render_all(fig_file, out, names=[name])
    assert hashlib.sha256(png.read_bytes()).hexdigest() != digest
    assert "16" in {lab["text"] for lab in changed[name]["meta"]["labels"]}
    model = model_for_figure(fig_file, "q3")
    assert model.dimensions() == ((10, 8), (20, 16))
    f = scaled_rectangles(model)
    polys = [op.pts for op in f._ops if op.kind == "ink"]
    assert np.ptp(polys[1], axis=0).tolist() == [20, 16]

    # Resolve all figures and compile through the normal renderer, not a custom document builder.
    figures = render_all(fig_file, out)
    docs = render_lesson(load_unit(unit), lesson, Figures(load_unit(unit), figures))
    for path in docs.values():
        xml = Document(path)._element.xml
        assert "{value:" not in xml
    assert "20" in Document(docs["key"])._element.xml
    # This source copy has never had input/ or the historical scratch builders.
    assert not (unit / "input").exists()


def test_model_ref_lookup_rejects_ambiguous_source(tmp_path):
    for d in ("figures", "lessons", "assessments"):
        (tmp_path / d).mkdir()
    for d in ("lessons", "assessments"):
        (tmp_path / d / "same.yaml").write_text("id: same\ntitle: Same\nsections: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="exactly one"):
        model_for_figure(tmp_path / "figures/same.py", "q3")


def test_resolve_cli_is_deterministic_and_does_not_render(tmp_path, monkeypatch):
    from typer.testing import CliRunner
    from lesson_builder import cli

    (tmp_path / "assessments").mkdir()
    src = tmp_path / "assessments" / f"{STEM}A.yaml"
    shutil.copy2(UNIT / "assessments" / src.name, src)
    (tmp_path / "unit.yaml").write_text("course: Geometry\nunit: 3\nunit_title: Pilot\nlessons: []\n"
                                      "assessments: [assessments/*.yaml]\n", encoding="utf-8")
    def no_figures(*args, **kwargs):
        raise AssertionError("resolve must not render")
    monkeypatch.setattr(cli, "_figures", no_figures)
    runner = CliRunner()
    args = ["resolve", str(tmp_path), "-l", STEM + "A"]
    result = runner.invoke(cli.app, args)
    assert result.exit_code == 0, result.output
    out = tmp_path / "_temp/specs" / (STEM + "A") / "resolved.json"
    first = out.read_bytes()
    report = json.loads(first)
    assert report["facts"]["q3"]["scale"] == "3/2" and report["facts"]["q3"]["answer"] == "15"
    assert "{value:" not in first.decode("utf-8")
    assert runner.invoke(cli.app, args).exit_code == 0
    assert out.read_bytes() == first
    assert not (tmp_path / "output").exists()
    assert runner.invoke(cli.app, ["resolve", str(tmp_path), "-l", "missing"]).exit_code != 0

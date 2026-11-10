"""Schema contract: numbering: auto, {ref:}/{num:} references, named frame rows, MC key normalisation."""
import pytest
import yaml

from lesson_builder.numbering import number_and_resolve, unresolved
from lesson_builder.spec import Item, LessonSpec, load_lesson

DOC = """
id: t
title: T
numbering: auto
sections:
  - kind: warmup
    items: [{prompt: hi, answer: x}]
  - kind: together
    items:
      - {id: arrow, prompt: a, answer: x, key: c, frame: [{before: b, answer: ans, after: ., w: 1.2}]}
      - {n: '7', prompt: kept, answer: x}
      - {prompt: 'Use {ref:arrow}, {num:arrow}, part {num:pb}.', answer: y,
         parts: [{id: pb, label: b., prompt: p, answer: z}]}
  - kind: notes
  - kind: cyu
    items: [{prompt: q, answer: '{ref:missing}'}]
practice: {title: P, selected: auto, rows: [{cells: [{prompt: x, answer: y}, {prompt: x2, answer: y2}]}]}
"""


def _load(text: str) -> LessonSpec:
    d = yaml.safe_load(text)
    number_and_resolve(d)
    return LessonSpec(**d)


def test_auto_numbering_groups_and_explicit_n():
    l = _load(DOC)
    assert [i.n for i in l.all_items()] == [None, "1", "7", "8", "1", "1", "2"]


def test_refs_resolve_and_unknown_kept():
    l = _load(DOC)
    items = list(l.all_items())
    assert items[3].prompt == "Use Problem 1, 1, part 8b."
    assert unresolved(items[4].answer) == ["{ref:missing}"]


def test_frame_mapping_and_key():
    it = list(_load(DOC).all_items())[1]
    assert it.frame == [["b", "ans", ".", 1.2]]
    assert it.key == "C"
    with pytest.raises(ValueError):
        Item(frame=[{"before": "a", "answer": "b", "oops": 1}])


def test_manual_numbering_is_default():
    l = _load(DOC.replace("numbering: auto", "numbering: manual"))
    assert [i.n for i in l.all_items()] == [None, None, "7", None, None, None, None]


def test_duplicate_ids_rejected():
    bad = DOC.replace("id: pb", "id: arrow")
    with pytest.raises(ValueError):
        _load(bad)


def test_load_lesson_keeps_raw_and_fig_words(tmp_path):
    p = tmp_path / "x.yaml"
    p.write_text(DOC.replace("prompt: hi,", "prompt: hi, fig: wide,"), encoding="utf-8")
    l = load_lesson(p)
    assert "numbering: auto" in l.raw
    assert next(l.all_items()).width == 3.4

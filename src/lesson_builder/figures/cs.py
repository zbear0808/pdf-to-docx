"""AP CSA figures: array boxes and reference (memory) diagrams.

Drawing units: one box is `cell` drawing units wide (default 1), so the Figure's width_in sets the printed
box size. Values print as given: pass strings with their quotes ('"cat"') and chars as "'a'".
Trace tables are not figures: write them as YAML tables.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .core import Figure

VAL_SIZE = 12
IDX_SIZE = 9


@dataclass(frozen=True)
class Ref:
    """A reference to the object named `target` in reference_diagram's `objects`."""
    target: str


def _txt(v) -> str:
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v).replace("$", r"\$")


def _box(f, x, y, w, h, layer="given"):
    f.poly([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], layer=layer)


def array_boxes(f: Figure, values, index=True, start=(0, 0), cell=1.0, answer=None, name=None, layer="given",
                size=VAL_SIZE):
    """A row of len(values) boxes from `start` (bottom-left), value centred in each, index under each when
    index=True, and `name` to the left. A None value is an empty box. answer: {index: value} printed in red
    on the key (boxes stay given). Returns the box centres."""
    vals = list(values)
    assert vals, "array_boxes: no values"
    answer = answer or {}
    assert all(0 <= i < len(vals) for i in answer), "array_boxes: answer index out of range"
    x0, y0 = map(float, start)
    centres = np.array([(x0 + (i + 0.5) * cell, y0 + cell / 2) for i in range(len(vals))])
    for i in range(len(vals)):
        _box(f, x0 + i * cell, y0, cell, cell, layer)
    for i, (c, v) in enumerate(zip(centres, vals)):
        if v is not None:
            f.text(c, _txt(v), layer=layer, size=size, fixed=True)
        if i in answer:
            f.text(c, _txt(answer[i]), layer="answer", size=size, fixed=True)
        if index:
            f._annotate((c[0], y0), f"${i}$", np.array([0.0, -(IDX_SIZE + 2)]), layer, IDX_SIZE, "side", True)
    if name:
        s = _txt(name)
        f._annotate((x0, y0 + cell / 2), s, np.array([-(5 + 0.3 * size * len(s)), 0.0]), layer, size, "side", True)
    return centres


def _object(f, name, obj, x, y, cell, layer, answer):
    """Draw one object with its top-left at (x, y); return (bbox, {field or index: centre}, next top y)."""
    if isinstance(obj, (list, tuple)):
        vals = [None if isinstance(v, Ref) or (name, i) in answer else v for i, v in enumerate(obj)]
        ans = {i: v for i, v in enumerate(obj) if (name, i) in answer and not isinstance(v, Ref)}
        c = array_boxes(f, vals, start=(x, y - cell), cell=cell, layer=layer, answer=ans)
        return (x, y - cell, x + len(obj) * cell, y), {i: p for i, p in enumerate(c)}, y - 2.2 * cell
    fields = {k: v for k, v in obj.items() if k != "_type"}
    rows = max(len(fields), 1)
    w, top = 3.2 * cell, y
    if "_type" in obj:
        f.text((x + w / 2, top + 0.3 * cell), _txt(obj["_type"]), layer=layer, size=VAL_SIZE - 1, fixed=True)
    _box(f, x, top - rows * cell, w, rows * cell, layer)
    centres = {}
    for k, (fn, v) in enumerate(fields.items()):
        cy = top - (k + 0.5) * cell
        f.text((x + 0.75 * cell, cy), _txt(fn), layer=layer, size=VAL_SIZE - 1, fixed=True)
        _box(f, x + 1.6 * cell, cy - 0.4 * cell, 1.4 * cell, 0.8 * cell, layer)
        centres[fn] = np.array([x + 2.3 * cell, cy])
        if not isinstance(v, Ref):
            f.text(centres[fn], _txt(v), layer="answer" if (name, fn) in answer else layer, size=VAL_SIZE - 1,
                   fixed=True)
    return (x, top - rows * cell, x + w, top), centres, top - rows * cell - 1.0 * cell


def _anchor(bbox, src):
    """Where an arrow from src meets the object box: the side facing src."""
    x0, y0, x1, y1 = bbox
    if src[0] < x0:
        return np.array([x0, (y0 + y1) / 2])
    if src[1] > y1:
        return np.array([(x0 + x1) / 2, y1])
    if src[1] < y0:
        return np.array([(x0 + x1) / 2, y0])
    return np.array([x1, (y0 + y1) / 2])


def reference_diagram(f: Figure, vars: dict, objects: dict | None = None, answer=(), cell=1.0, gap=2.5,
                      layer="given"):
    """Memory diagram. `vars` ({name: value or Ref}) go in a column on the left: name, then a box holding a
    primitive (None prints null), or a dot with an arrow to the object a Ref names. `objects` ({name: list
    for an array, or dict of fields with an optional "_type" heading}) stack in a column `gap` cells to the
    right; fields and array slots may hold Refs too. `answer`: variable names, or (object, field/index)
    pairs, whose contents (value or arrow) are drawn on the answer layer, so the student copy shows empty
    boxes to fill in. Returns {object name: bbox}."""
    objects = objects or {}
    answer = set(answer)
    for nm, v in [*vars.items(), *[(f"{o}.{k}", v) for o, ob in objects.items()
                                   for k, v in (ob.items() if isinstance(ob, dict) else enumerate(ob))]]:
        assert not isinstance(v, Ref) or v.target in objects, f"reference_diagram: {nm} -> unknown {v.target!r}"
    src = []          # (from point, target name, layer)
    for k, (nm, v) in enumerate(vars.items()):
        cy = -(k * 1.4 + 0.4) * cell
        _box(f, 0, cy - 0.4 * cell, 1.4 * cell, 0.8 * cell, layer)
        f._annotate((0, cy), _txt(nm), np.array([-(5 + 0.3 * VAL_SIZE * len(_txt(nm))), 0.0]), layer, VAL_SIZE,
                    "side", True)
        lay = "answer" if nm in answer else layer
        c = np.array([0.7 * cell, cy])
        if isinstance(v, Ref):
            src.append((c, v.target, lay))
        else:
            f.text(c, _txt(v), layer=lay, size=VAL_SIZE, fixed=True)
    boxes, x, y = {}, 1.4 * cell + gap * cell, 0.0
    for nm, ob in objects.items():
        boxes[nm], centres, y = _object(f, nm, ob, x, y, cell, layer, answer)
        items = ob.items() if isinstance(ob, dict) else enumerate(ob)
        src += [(centres[k], v.target, "answer" if (nm, k) in answer else layer)
                for k, v in items if isinstance(v, Ref)]
    for p, t, lay in src:
        f.dots([p], layer=lay, size=12)
        f.arrow(p, _anchor(boxes[t], p), layer=lay, dashed=False)
    return boxes

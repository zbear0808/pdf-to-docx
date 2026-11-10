"""Reusable comparison diagrams extracted from the Unit 3 progress checks."""
from __future__ import annotations

import numpy as np

from .core import Figure
from .geometry import P, assert_lengths, dilate, extend, rect_pair, side_splitter
from ..problem_models import ScaledRectangles


def scaled_rectangles(model: ScaledRectangles, width_in=3.0, height_in=1.5) -> Figure:
    """Draw checked givens from the same model used to resolve the prompt and answer."""
    (w, h), _ = model.dimensions()
    f, _ = rect_pair(float(w), float(h), float(model.scale),
                     names=(model.source_name, model.image_name), labels=model.labels(),
                     width_in=width_in, height_in=height_in, label_offset_pt=11)
    return f


def split_triangle(V, U, W, k, names, seg_labels, angle_at=None, angle_text=None, size=(2.4, 2.0),
                   inside=(), dirs=None, angle_dist=2.7):
    """Labeled side-splitter view. names = (V, U, W, U', W'); seg_labels = ((VU', U'U), (VW', W'W)).

    Uses the shared side-splitter construction and verifies that the four numeric labels match it.
    `inside` contains U/W for segment labels on the inside of that side.
    """
    tri = P(V, U, W)
    U2, W2 = dilate([U, W], k, V)
    values = [s for pair in seg_labels for s in pair]
    assert_lengths([(a, b, float(s)) for (a, b), s in zip(((V, U2), (U2, U), (V, W2), (W2, W)), values)])
    ctr = tri.mean(0)
    directions = {name: p - ctr for name, p in zip(names[:3], tri)}
    directions.update(dirs or {})
    f, _ = side_splitter(tri, k, names=names[:3], split_names=names[3:], seg_labels=values,
                         width_in=size[0], height_in=size[1], label_directions=directions,
                         inside_labels=tuple({"U": "AB", "W": "AC"}[s] for s in inside))
    if angle_at is not None:
        f.arc(*angle_at, r=0.7)
        f.angle_label(*angle_at, angle_text, dist=angle_dist)
    return f, U2, W2


def line_family(lines, box=(10, 6), size=(2.6, 1.6)) -> Figure:
    """Lines [(name, point, heading_degrees, label_end[, label_direction])]. End is +1 (top) or -1."""
    W, H = box
    if W <= 0 or H <= 0:
        raise ValueError("line-family box must have positive width and height")
    if len({row[0] for row in lines}) != len(lines):
        raise ValueError("line names must be unique")
    f = Figure(width_in=size[0], height_in=size[1])
    for name, point, deg, end, *directions in lines:
        if end not in (-1, 1):
            raise ValueError("label_end must be -1 or 1")
        p = np.asarray(point, float)
        u = np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])
        a, b = extend(p, p + u, (0, W, 0, H), ray=False)
        f.seg(a, b)
        top = b if (b[1] - a[1]) * end > 0 or (np.isclose(b[1], a[1]) and end > 0) else a
        inward = (a + b) / 2 - top
        d = directions[0] if directions else np.array([-u[1], u[0]]) * (1 if u[0] >= 0 else -1)
        f.label(top + 0.12 * inward, name, direction=d)
    return f


def parallel_names(lines, reference: str) -> set[str]:
    """Which named lines (including itself) are parallel to the reference? Headings are modulo 180."""
    angs = {n: a % 180 for n, _, a, *_ in lines}
    if reference not in angs:
        raise ValueError(f"unknown reference line {reference!r}")
    return {n for n, a in angs.items() if abs((a - angs[reference] + 90) % 180 - 90) < 1e-6}

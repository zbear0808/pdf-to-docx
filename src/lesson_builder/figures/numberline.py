"""Number lines: ticks and numbers, closed or open points, rays, and intervals (inequalities).

Drawing x is the number itself (one data unit = one unit on the line); the line sits at height `y`.
Call `number_line()` first: point, ray, and segment_interval read the line stored on the figure.
Answer marks go on layer="answer" (red, key only); the line itself is normally given.
"""
from __future__ import annotations

import numpy as np

from .coordinate import NUM_SIZE, _arrow, num_label
from .core import Figure

MARK_LW = 3.0     # rays and intervals are drawn thick over the line
DOT_S = 42        # point size (points squared)


def _line(f: Figure):
    nl = getattr(f, "numberline_spec", None)
    assert nl is not None, "call numberline.number_line(f, ...) first"
    return nl


def number_line(f: Figure, lo, hi, step=1, label_every=1, y=0, arrows=True, layer="given", size=NUM_SIZE,
                minor=None):
    """Line from lo to hi (arrowheads half a step past each end), a tick every `step`, a number under every
    `label_every`-th tick, and optional unnumbered `minor` ticks (a smaller step)."""
    assert hi > lo and step > 0, "number_line: need lo < hi and step > 0"
    ext = 0.5 * step if arrows else 0.0
    f.numberline_spec = (lo, hi, y, ext)
    xs = np.arange(lo, hi + 1e-9, step)
    ms = np.arange(lo, hi + 1e-9, minor) if minor else np.zeros(0)

    def draw(ax, c):
        a, b = (lo - ext, y), (hi + ext, y)
        if arrows:
            _arrow(ax, a, b, c)
        else:
            ax.plot(*zip(a, b), color=c, lw=1.0, clip_on=False)
        ax.plot(xs, np.full(len(xs), y), ls="none", marker="|", ms=8, mew=1.0, color=c, clip_on=False)
        if len(ms):
            ax.plot(ms, np.full(len(ms), y), ls="none", marker="|", ms=4, mew=0.8, color=c, clip_on=False)
    f.custom(draw, layer=layer, extent=[(lo - ext, y), (hi + ext, y)])
    for k, x in enumerate(xs):
        if k % label_every == 0:
            num_label(f, (x, y), x, (0, -(size + 4)), layer, size)


def point(f: Figure, x, open=False, layer="given"):
    """A closed (filled) or open (hollow) dot on the line at x."""
    lo, hi, y, _ = _line(f)
    assert lo - 1e-9 <= x <= hi + 1e-9, f"point: {x} is off the line [{lo}, {hi}]"

    def draw(ax, c):
        ax.scatter([x], [y], s=DOT_S, facecolors="white" if open else c, edgecolors=c, linewidths=1.4,
                   zorder=3.6, clip_on=False)
    f.custom(draw, layer=layer, extent=[(x, y)])


def segment_interval(f: Figure, a, b, open_a=False, open_b=False, layer="given"):
    """Thick segment from a to b with an open or closed dot at each end, e.g. -2 <= x < 3."""
    lo, hi, y, _ = _line(f)
    assert lo - 1e-9 <= a < b <= hi + 1e-9, f"segment_interval: need {lo} <= a < b <= {hi}"
    f.custom(lambda ax, c: ax.plot([a, b], [y, y], color=c, lw=MARK_LW, solid_capstyle="butt", zorder=2.6,
                                   clip_on=False), layer=layer)
    point(f, a, open_a, layer)
    point(f, b, open_b, layer)


def ray(f: Figure, x, direction, open=False, layer="given"):
    """Thick ray from x to the end of the line in `direction` ("left" / "right" or -1 / +1) with an arrowhead,
    and an open or closed dot at x: x > 2 is ray(f, 2, "right", open=True)."""
    lo, hi, y, ext = _line(f)
    d = {"left": -1, "right": 1}.get(direction, direction)
    assert d in (-1, 1), "ray: direction is 'left', 'right', -1 or 1"
    end = (hi + ext) if d > 0 else (lo - ext)
    assert (end - x) * d > 0, "ray: x is past the end of the line"
    f.custom(lambda ax, c: _arrow(ax, (x, y), (end, y), c, lw=MARK_LW, both=False), layer=layer,
             extent=[(x, y), (end, y)])
    point(f, x, open, layer)

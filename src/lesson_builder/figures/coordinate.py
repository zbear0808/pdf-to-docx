"""Coordinate-plane figures: numbered axes, points, lines, function graphs, slope triangles.

Drawing coordinates are the math coordinates (one data unit = one unit on the axes), and the Figure keeps
x and y at one scale, so slopes look right. Every helper takes `layer` ("given" black, "answer" red).
Call `axes()` first: the other helpers read the window it stores on the figure (`f.coord_window`).
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import FancyArrowPatch

from .core import Figure

AXIS_LW = 1.0
NUM_SIZE = 9


def fmt(v: float) -> str:
    """A tick number as mathtext: `$-3$` (true minus sign), `$2.5$`, no trailing `.0`."""
    v = float(v)
    s = f"{int(round(v))}" if abs(v - round(v)) < 1e-9 else f"{v:.6g}"
    return f"${s}$"


def _arrow(ax, a, b, c, lw=AXIS_LW, both=True, dashed=False):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="<|-|>" if both else "-|>", mutation_scale=9, color=c, lw=lw,
                                 ls=(0, (4, 2.5)) if dashed else "-", shrinkA=0, shrinkB=0, zorder=2,
                                 clip_on=False))


def num_label(f: Figure, pt, value, off_pt, layer="given", size=NUM_SIZE, fixed=True):
    """A number label `off_pt` points from pt. fixed=True keeps that spot; otherwise label placement may turn
    it a little to clear other ink (the tick numbers next to the origin)."""
    s = value if isinstance(value, str) else fmt(value)
    f._annotate(pt, s, np.asarray(off_pt, float), layer, size, "side", fixed=fixed)


def _window(f: Figure):
    w = getattr(f, "coord_window", None)
    assert w is not None, "call coordinate.axes(f, ...) before plotting"
    return w


def axes(f: Figure, x0, x1, y0, y1, step=1, labels_every=1, grid=True, arrows=True, layer="given",
         names=("x", "y"), size=NUM_SIZE):
    """x and y axes over [x0, x1] x [y0, y1] with a tick every `step` and a number on each multiple of
    labels_every * step (0 is not numbered). The axes cross at 0 when 0 is in the window, else at the low edge. Arrows
    extend each axis half a step past the window. names=None skips the x/y letters."""
    assert x1 > x0 and y1 > y0 and step > 0, "axes: need x0 < x1, y0 < y1, step > 0"
    f.coord_window = (x0, x1, y0, y1)
    if grid:
        f.grid(x0, x1, y0, y1, step, layer=layer)
    ay = 0.0 if y0 <= 0 <= y1 else y0
    ax_ = 0.0 if x0 <= 0 <= x1 else x0
    ext = 0.5 * step if arrows else 0.0
    xs = np.arange(np.ceil(x0 / step) * step, x1 + 1e-9, step)
    ys = np.arange(np.ceil(y0 / step) * step, y1 + 1e-9, step)

    def draw(ax, c):
        for a, b in (((x0 - ext, ay), (x1 + ext, ay)), ((ax_, y0 - ext), (ax_, y1 + ext))):
            if arrows:
                _arrow(ax, a, b, c)
            else:
                ax.plot(*zip(a, b), color=c, lw=AXIS_LW, clip_on=False)
        ax.plot(xs, np.full(len(xs), ay), ls="none", marker="|", ms=5, mew=AXIS_LW, color=c, clip_on=False)
        ax.plot(np.full(len(ys), ax_), ys, ls="none", marker="_", ms=5, mew=AXIS_LW, color=c, clip_on=False)
    f.custom(draw, layer=layer, extent=[(x0 - ext, y0 - ext), (x1 + ext, y1 + ext)])
    for x in xs:
        if abs(x) > 1e-9 and round(x / step) % labels_every == 0:
            num_label(f, (x, ay), x, (0, -(size + 2)), layer, size)
    for y in ys:
        if abs(y) > 1e-9 and round(y / step) % labels_every == 0:
            s = fmt(y)
            # the -1 next to the origin may turn a little to clear the x axis's -1
            num_label(f, (ax_, y), s, (-(5 + 0.28 * size * (len(s) - 2)), 0), layer, size,
                      fixed=not np.isclose(y, ay - step))
    if names:
        f.label((x1 + ext, ay), names[0], layer=layer, direction=(1, 0), offset_pt=9, size=size + 2, fixed=True)
        f.label((ax_, y1 + ext), names[1], layer=layer, direction=(0, 1), offset_pt=9, size=size + 2, fixed=True)


def plot_points(f: Figure, pts, names=None, layer="given", directions=None, coords=False):
    """Dots at pts (each inside the axes window), with optional names ("A" or ["A", None]) and, with
    coords=True, the coordinates after the name: A(2, -1). directions: one label direction per point."""
    pts = np.atleast_2d(np.asarray(pts, float))
    x0, x1, y0, y1 = _window(f)
    assert np.all((pts[:, 0] >= x0 - 1e-9) & (pts[:, 0] <= x1 + 1e-9) & (pts[:, 1] >= y0 - 1e-9)
                  & (pts[:, 1] <= y1 + 1e-9)), f"plot_points: point outside the window {(x0, x1, y0, y1)}"
    f.dots(pts, layer=layer, size=18)
    names = list(names) if names is not None else [None] * len(pts)
    assert len(names) == len(pts), "plot_points: one name per point"
    for i, (p, nm) in enumerate(zip(pts, names)):
        if nm is None and not coords:
            continue
        t = nm or ""
        if coords:
            t += f"({{{fmt(p[0])[1:-1]}}},\\,{{{fmt(p[1])[1:-1]}}})"
        d = directions[i] if directions is not None else (0.7, 1)
        f.label(p, t, layer=layer, direction=d, offset_pt=9, size=11)


def plot_line(f: Figure, m, b, x0=None, x1=None, layer="given", dashed=False, arrows=True):
    """The line y = m x + b from x0 to x1 (default: the axes window), cut to the window's y range, with
    arrowheads at both ends. For a vertical line use `f.seg((c, y0), (c, y1))`."""
    wx0, wx1, wy0, wy1 = _window(f)
    x0, x1 = wx0 if x0 is None else x0, wx1 if x1 is None else x1
    assert x1 > x0, "plot_line: x0 < x1"
    if abs(m) > 1e-12:  # cut to the y window
        xa, xb = sorted(((wy0 - b) / m, (wy1 - b) / m))
        x0, x1 = max(x0, xa), min(x1, xb)
    assert x1 > x0 and wy0 - 1e-9 <= m * (x0 + x1) / 2 + b <= wy1 + 1e-9, f"plot_line: y = {m}x + {b} misses the window"
    a, c = (x0, m * x0 + b), (x1, m * x1 + b)
    if not arrows:
        f.seg(a, c, layer=layer, dashed=dashed)
        return
    f.custom(lambda ax, col: _arrow(ax, a, c, col, lw=1.3, dashed=dashed), layer=layer, extent=[a, c])


def plot_fn(f: Figure, fn, x0=None, x1=None, n=200, layer="given", dashed=False):
    """Graph of y = fn(x) on [x0, x1] (default: the axes window) from n samples. Parts outside the window's
    y range, and non-finite values, are left out (the curve breaks there)."""
    wx0, wx1, wy0, wy1 = _window(f)
    x0, x1 = wx0 if x0 is None else x0, wx1 if x1 is None else x1
    xs = np.linspace(x0, x1, n)
    with np.errstate(all="ignore"):
        ys = np.array([fn(x) for x in xs], float)
    ys[~np.isfinite(ys) | (ys < wy0 - 1e-9) | (ys > wy1 + 1e-9)] = np.nan
    ok = np.isfinite(ys)
    assert ok.any(), "plot_fn: the graph misses the window"
    ext = [(xs[ok].min(), np.nanmin(ys)), (xs[ok].max(), np.nanmax(ys))]
    f.custom(lambda ax, c: ax.plot(xs, ys, color=c, lw=1.3, ls="--" if dashed else "-", clip_on=False),
             layer=layer, extent=ext)


def slope_triangle(f: Figure, p, q, layer="given", labels=True, dashed=True, size=10):
    """Run then rise from p to q (dashed legs), labelled with the signed run and rise. Returns the slope."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    run, rise = q - p
    assert abs(run) > 1e-12, "slope_triangle: vertical segment has no slope"
    corner = np.array([q[0], p[1]])
    f.seg(p, corner, layer=layer, dashed=dashed)
    if abs(rise) > 1e-12:
        f.seg(corner, q, layer=layer, dashed=dashed)
    if labels:
        f.side_label(p, corner, fmt(run), center=q, layer=layer, size=size, offset_pt=8)
        if abs(rise) > 1e-12:
            f.side_label(corner, q, fmt(rise), center=p, layer=layer, size=size, offset_pt=8)
    return rise / run

"""Statistics figures: dot plots, histograms, box plots, scatterplots, normal curves. Black and gray only.

Charts measure x and y in different units (scores, counts), but a Figure keeps one drawing scale, so data
goes through a `Scale`: drawing (X, Y) = ((x - x0) * sx, (y - y0) * sy). Each chart picks a default scale
(about 6 drawing units wide, 4 tall) and returns it, so later marks (a mean line, an answer) can use it.
Pass `scale=` to line up several charts. Dot plots and box plots use the number itself as X (scale 1),
so they line up with `numberline.number_line` on the same figure. Two-way and trace tables are not
figures: write them as YAML tables.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from matplotlib.patches import Circle, Rectangle

from .coordinate import NUM_SIZE, fmt, num_label
from .core import Figure
from .numberline import number_line

GRAY = "0.82"


@dataclass(frozen=True)
class Scale:
    """Data -> drawing coordinates: X = (x - x0) * sx, Y = (y - y0) * sy."""
    x0: float = 0.0
    y0: float = 0.0
    sx: float = 1.0
    sy: float = 1.0

    def pt(self, x, y) -> np.ndarray:
        return np.array([(x - self.x0) * self.sx, (y - self.y0) * self.sy], float)

    def pts(self, xs, ys) -> np.ndarray:
        return np.c_[(np.asarray(xs, float) - self.x0) * self.sx, (np.asarray(ys, float) - self.y0) * self.sy]


def nice_axis(lo, hi, n=5):
    """(start, stop, step) with a 1-2-2.5-5 step and about n intervals covering [lo, hi]."""
    assert hi >= lo, "nice_axis: hi < lo"
    span = (hi - lo) or abs(hi) or 1.0
    raw = span / n
    mag = 10 ** np.floor(np.log10(raw))
    step = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw - 1e-12)
    a, b = np.floor(lo / step + 1e-9) * step, np.ceil(hi / step - 1e-9) * step
    return float(a), float(b if b > a else a + step), float(step)


def chart_axes(f: Figure, xaxis, yaxis, scale: Scale, xlabel=None, ylabel=None, layer="given", size=NUM_SIZE,
               xticks=None):
    """L-shaped axes: x from xaxis = (lo, hi, step) along y = yaxis lo, y from yaxis = (lo, hi, step) along
    x = xaxis lo (yaxis=None: x axis only, at y = 0), numbered ticks, optional axis titles. xticks overrides
    the x tick values (histogram bin edges)."""
    xlo, xhi, xs = xaxis
    ylo = yaxis[0] if yaxis else 0.0
    xt = np.asarray(xticks, float) if xticks is not None else np.arange(xlo, xhi + 1e-9 * xs, xs)
    o, xe = scale.pt(xlo, ylo), scale.pt(xhi, ylo)
    pts = [o, xe]
    if yaxis:
        yt = np.arange(ylo, yaxis[1] + 1e-9 * yaxis[2], yaxis[2])
        ye = scale.pt(xlo, yaxis[1])
        pts.append(ye)

    def draw(ax, c):
        ax.plot([o[0], xe[0]], [o[1], xe[1]], color=c, lw=1.0, clip_on=False)
        P = scale.pts(xt, np.full(len(xt), ylo))
        ax.plot(P[:, 0], P[:, 1], ls="none", marker="|", ms=6, mew=1.0, color=c, clip_on=False)
        if yaxis:
            ax.plot([o[0], ye[0]], [o[1], ye[1]], color=c, lw=1.0, clip_on=False)
            Q = scale.pts(np.full(len(yt), xlo), yt)
            ax.plot(Q[:, 0], Q[:, 1], ls="none", marker="_", ms=6, mew=1.0, color=c, clip_on=False)
    f.custom(draw, layer=layer, extent=pts)
    for x in xt:
        num_label(f, scale.pt(x, ylo), x, (0, -(size + 4)), layer, size)
    if yaxis:
        for y in yt:
            s = fmt(y)
            num_label(f, scale.pt(xlo, y), s, (-(6 + 0.28 * size * (len(s) - 2)), 0), layer, size)
    if xlabel:
        num_label(f, (o + xe) / 2, xlabel, (0, -(2 * size + 12)), layer, size + 1)
    if ylabel and yaxis:
        num_label(f, ye, ylabel, (0, size + 6), layer, size + 1)


def dotplot(f: Figure, data, lo, hi, step=1, label_every=1, layer="given", r=None, xlabel=None):
    """Number line from lo to hi with a stack of dots over each value. Dots are circles of radius r drawing
    units (default 0.2 * step) stacked 2.5 r apart. The dots go on `layer`; the line is always given."""
    data = np.asarray(data, float)
    assert len(data) and np.all((data >= lo - 1e-9) & (data <= hi + 1e-9)), f"dotplot: data outside [{lo}, {hi}]"
    r = r or 0.2 * step
    number_line(f, lo, hi, step, label_every, y=0, arrows=False)
    vals, counts = np.unique(np.round(data, 9), return_counts=True)
    centers = [(v, 2 * r + 2.5 * r * k) for v, n in zip(vals, counts) for k in range(n)]

    def draw(ax, c):
        for xy in centers:
            ax.add_patch(Circle(xy, r, facecolor=c, edgecolor=c, lw=0.6, zorder=3, clip_on=False))
    ys = [y for _, y in centers]
    f.custom(draw, layer=layer, extent=[(vals.min() - r, 0), (vals.max() + r, max(ys) + r)])
    if xlabel:
        num_label(f, ((lo + hi) / 2, 0), xlabel, (0, -(2 * NUM_SIZE + 12)), "given", NUM_SIZE + 1)
    return dict(zip(vals.tolist(), counts.tolist()))


def histogram(f: Figure, data, bins, counts=None, scale=None, ystep=None, xlabel=None, ylabel="Frequency",
              layer="given", fill=GRAY):
    """Bars over bin edges `bins` (ascending). counts default to np.histogram(data, bins): each bin holds
    [a, b) except the last, which holds both ends. The axes are given; the bars go on `layer` (gray fill,
    outline in the layer colour). Returns (counts, scale)."""
    edges = np.asarray(bins, float)
    assert len(edges) >= 2 and np.all(np.diff(edges) > 0), "histogram: bins are ascending edges"
    if counts is None:
        data = np.asarray(data, float)
        assert np.all((data >= edges[0]) & (data <= edges[-1])), "histogram: data outside the bins"
        counts = np.histogram(data, edges)[0]
    counts = np.asarray(counts, float)
    assert len(counts) == len(edges) - 1 and np.all(counts >= 0), "histogram: one count per bin"
    ya = nice_axis(0, counts.max() or 1, 4) if ystep is None else (0.0, float(np.ceil(counts.max() / ystep) * ystep),
                                                                   float(ystep))
    scale = scale or Scale(edges[0], 0.0, 6 / (edges[-1] - edges[0]), 4 / ya[1])
    chart_axes(f, (edges[0], edges[-1], edges[1] - edges[0]), ya, scale, xlabel, ylabel, xticks=edges)
    bars = [(scale.pt(a, 0), scale.pt(b, n)) for a, b, n in zip(edges[:-1], edges[1:], counts) if n > 0]

    def draw(ax, c):
        for p, q in bars:
            ax.add_patch(Rectangle(p, q[0] - p[0], q[1] - p[1], facecolor=fill, edgecolor=c, lw=1.0, zorder=2,
                                   clip_on=False))
    if bars:
        f.custom(draw, layer=layer, extent=[bars[0][0], (bars[-1][1][0], max(q[1] for _, q in bars))])
    return counts.astype(int).tolist(), scale


def five_number(data):
    """(min, Q1, median, Q3, max). Quartiles are medians of the lower and upper halves, leaving out the
    median when n is odd (the TI-84 and AP Statistics convention)."""
    x = np.sort(np.asarray(data, float))
    assert len(x) >= 2, "five_number: need at least 2 values"
    n, h = len(x), len(x) // 2
    return float(x[0]), float(np.median(x[:h])), float(np.median(x)), float(np.median(x[n - h:])), float(x[-1])


def boxplot(f: Figure, values, y=1.0, height=0.6, layer="given", five=False, outliers=True, scale=None):
    """Box plot at height y (drawing units) over the number line's x (scale default 1:1). values is the data,
    or (min, Q1, median, Q3, max) with five=True. With outliers=True (data only) points past 1.5 IQR from the
    box are dots and the whiskers stop at the last value inside. Returns the summary dict."""
    scale = scale or Scale()
    data = np.asarray(values, float)
    if five:
        assert len(data) == 5 and np.all(np.diff(data) >= 0), "boxplot: five=True needs min <= Q1 <= med <= Q3 <= max"
        mn, q1, med, q3, mx = data
        out = np.zeros(0)
    else:
        mn, q1, med, q3, mx = five_number(data)
        out = np.zeros(0)
        if outliers:
            iqr = q3 - q1
            inside = data[(data >= q1 - 1.5 * iqr) & (data <= q3 + 1.5 * iqr)]
            out = data[(data < q1 - 1.5 * iqr) | (data > q3 + 1.5 * iqr)]
            mn, mx = inside.min(), inside.max()
    X = lambda v: scale.pt(v, 0)[0]  # noqa: E731
    h = height / 2
    f.poly([(X(q1), y - h), (X(q3), y - h), (X(q3), y + h), (X(q1), y + h)], layer=layer)
    f.seg((X(med), y - h), (X(med), y + h), layer=layer)
    for a, b in ((mn, q1), (q3, mx)):
        if abs(b - a) > 1e-12:
            f.seg((X(a), y), (X(b), y), layer=layer)
    for v in (mn, mx):
        f.seg((X(v), y - h / 2), (X(v), y + h / 2), layer=layer)
    if len(out):
        f.dots([(X(v), y) for v in out], layer=layer, size=16)
    return {"min": float(mn), "q1": float(q1), "median": float(med), "q3": float(q3), "max": float(mx),
            "outliers": sorted(out.tolist())}


def scatter(f: Figure, xs, ys, line=None, scale=None, xaxis=None, yaxis=None, xlabel=None, ylabel=None,
            layer="given", line_layer="given", dashed=False):
    """Scatterplot with numbered axes (default: nice_axis of the data). line=(slope, intercept) in data
    units draws y = slope * x + intercept across the x axis, cut to the y axis range. Returns the scale."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    assert len(xs) == len(ys) and len(xs), "scatter: xs and ys need the same nonzero length"
    xa, ya = xaxis or nice_axis(xs.min(), xs.max()), yaxis or nice_axis(ys.min(), ys.max())
    assert xa[0] <= xs.min() and xs.max() <= xa[1] and ya[0] <= ys.min() and ys.max() <= ya[1], \
        "scatter: data outside the axes"
    scale = scale or Scale(xa[0], ya[0], 6 / (xa[1] - xa[0]), 4 / (ya[1] - ya[0]))
    chart_axes(f, xa, ya, scale, xlabel, ylabel)
    f.dots(scale.pts(xs, ys), layer=layer, size=16)
    if line is not None:
        m, b = line
        x0, x1 = xa[0], xa[1]
        if abs(m) > 1e-12:
            lo, hi = sorted(((ya[0] - b) / m, (ya[1] - b) / m))
            x0, x1 = max(x0, lo), min(x1, hi)
        assert x1 > x0, "scatter: the line misses the axes"
        f.seg(scale.pt(x0, m * x0 + b), scale.pt(x1, m * x1 + b), layer=line_layer, dashed=dashed)
    return scale


def normal_curve(f: Figure, mu, sigma, shade=None, layer="given", sds=3, width=6.0, peak=2.0, ticks="values",
                 hatch=None):
    """Normal density curve over mu +/- sds sigma on a baseline with a tick at each whole sigma. The curve is
    `width` drawing units wide and `peak` tall (so the scale is X = (x - mu) / sigma * width / (2 sds)).
    ticks: "values" (mu + k sigma), "z" (k), or None. shade=(a, b) shades a <= x <= b on `layer`, with None
    for an open tail: gray fill on the given layer, hatching in the layer colour on the answer layer
    (or `hatch=` on either). Returns the scale."""
    assert sigma > 0, "normal_curve: sigma > 0"
    s = Scale(mu, 0.0, width / (2 * sds) / sigma, peak * sigma * np.sqrt(2 * np.pi))
    lo, hi = mu - sds * sigma, mu + sds * sigma
    pdf = lambda x: np.exp(-0.5 * ((np.asarray(x, float) - mu) / sigma) ** 2) / (sigma * np.sqrt(2 * np.pi))  # noqa: E731
    xs = np.linspace(lo, hi, 241)
    C = s.pts(xs, pdf(xs))
    f.poly(C, closed=False)
    f.seg(s.pt(lo, 0), s.pt(hi, 0))
    ks = np.arange(-sds, sds + 1)
    tk = [s.pt(mu + k * sigma, 0) for k in ks]
    f.custom(lambda ax, c: ax.plot([p[0] for p in tk], [0] * len(tk), ls="none", marker="|", ms=6, mew=1.0,
                                   color=c, clip_on=False), extent=tk)
    if ticks:
        for k, p in zip(ks, tk):
            num_label(f, p, mu + k * sigma if ticks == "values" else k, (0, -(NUM_SIZE + 4)))
    if shade is not None:
        a, b = shade
        a, b = lo if a is None else max(a, lo), hi if b is None else min(b, hi)
        assert b > a, "normal_curve: shade needs a < b"
        sx = np.linspace(a, b, 120)
        S = s.pts(sx, pdf(sx))
        h = hatch or (None if layer == "given" else "////")

        def draw(ax, c):
            ax.fill_between(S[:, 0], 0, S[:, 1], facecolor="none" if h else GRAY, edgecolor=c, hatch=h, lw=0,
                            zorder=1, clip_on=False)
            for p in (S[0], S[-1]):
                ax.plot([p[0], p[0]], [0, p[1]], color=c, lw=1.0, clip_on=False)
        f.custom(draw, layer=layer, extent=[(S[0, 0], 0), (S[-1, 0], S[:, 1].max())])
    return s

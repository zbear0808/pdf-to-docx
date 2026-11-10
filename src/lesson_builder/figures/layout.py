"""Deterministic label placement and figure lint.

Every label has a list of candidate positions (its requested spot first). At render time each label keeps the
first candidate whose ink doesn't touch a line, dot, arrow, or an already placed label, and isn't closer to
another point than to its own. Labels with no clear candidate keep the least-bad spot and are reported.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch

LIGHT_LW = 0.6      # lines thinner than this (grid lines) are not obstacles
CLEAR_PT = 1.0      # required gap between a label's ink and anything else, in points
LABEL_GAP = 3.0     # labels keep CLEAR_PT * LABEL_GAP from each other, so "48°62°" can't run together
SAMPLE_PX = 1.5     # spacing of sample points along obstacle lines


@dataclass
class Label:
    layer: str
    s: str
    size: float
    kind: str                         # point | side | angle | text
    anchor: np.ndarray                # the thing the label names (vertex, segment midpoint, angle vertex)
    cands: list = field(default_factory=list)   # [(data xy, offset pt)], preferred first
    fixed: bool = False
    choice: int = 0
    raw: str = ""                     # the text as written, before math_fix (for the prime-style lint)

    @property
    def xy(self):
        return self.cands[self.choice][0]

    @property
    def off(self):
        return self.cands[self.choice][1]


def _rot(v, deg):
    t = np.radians(deg)
    return np.array([v[0] * np.cos(t) - v[1] * np.sin(t), v[0] * np.sin(t) + v[1] * np.cos(t)])


def offset_candidates(xy, off_pt, size):
    """Same distance first, turning away from the requested direction; then farther out."""
    off = np.asarray(off_pt, float)
    r = float(np.linalg.norm(off))
    base = off / r if r > 1e-9 else np.array([0.0, 1.0])
    r = r if r > 1e-9 else 0.8 * size
    out = []
    for m in (1.0, 1.3, 1.65):
        for d in (0, 20, -20, 40, -40, 60, -60, 85, -85, 115, -115, 145, -145, 180):
            cost = abs(d) / 45 + (m - 1) * 3
            out.append((cost, xy, _rot(base, d) * r * m))
    out.sort(key=lambda c: c[0])
    return [(np.asarray(xy, float), off)] + [(p, o) for _, p, o in out[1:]]


def nudge_candidates(xy, size):
    """Free text: small shifts around the requested spot."""
    out = [(np.asarray(xy, float), np.zeros(2))]
    for r in (0.25 * size, 0.5 * size, 0.8 * size):
        for d in range(0, 360, 45):
            out.append((np.asarray(xy, float), _rot(np.array([1.0, 0.0]), d) * r))
    return out


def angle_candidates(v, b, dist, half_deg):
    """Along the angle bisector b from vertex v, farther or nearer, then turned a little inside the angle."""
    spread = [0] + [s for d in (8, 16, 24) if d < 0.6 * half_deg for s in (d, -d)]
    out = []
    for m in (1.0, 1.2, 0.85, 1.45, 1.75, 0.7, 2.1, 2.5, 3.0):
        for d in spread:
            out.append((abs(m - 1) * 2 + abs(d) / 16, v + _rot(b, d) * dist * m))
    out.sort(key=lambda c: c[0])
    return [(p, np.zeros(2)) for _, p in out]


@lru_cache(maxsize=512)
def _ink_insets(s: str, size: float, dpi: int):
    """Fractions of the text's layout box that hold no ink: (left, bottom, right, top)."""
    from .core import RC
    with plt.rc_context(RC):
        fig = plt.figure(figsize=(3, 1.5), dpi=dpi, facecolor="white")
        try:
            t = fig.text(0.5, 0.5, s, fontsize=size, ha="center", va="center", color="black")
            fig.canvas.draw()
            bb = t.get_window_extent(fig.canvas.get_renderer())
            img = np.asarray(fig.canvas.buffer_rgba())[..., 0]
        finally:
            plt.close(fig)
    H = img.shape[0]
    ys, xs = np.nonzero(img < 128)
    if not len(xs) or bb.width <= 0 or bb.height <= 0:
        return (0.0, 0.0, 0.0, 0.0)
    x0, x1 = xs.min(), xs.max() + 1
    y0, y1 = H - (ys.max() + 1), H - ys.min()   # display coordinates (origin bottom-left)
    clamp = lambda v: float(min(max(v, 0.0), 0.45))  # noqa: E731
    return (clamp((x0 - bb.x0) / bb.width), clamp((y0 - bb.y0) / bb.height),
            clamp((bb.x1 - x1) / bb.width), clamp((bb.y1 - y1) / bb.height))


class _Scene:
    """Obstacles of a drawn axes, in display pixels."""

    def __init__(self, fig, ax, dpi):
        self.dpi = dpi
        self.px = dpi / 72
        pts, half = [], []
        for ln in ax.lines:
            lw = ln.get_linewidth()
            if lw < LIGHT_LW:
                continue
            xy = ax.transData.transform(np.asarray(ln.get_xydata(), float))
            for a, b in zip(xy[:-1], xy[1:]):
                if not (np.isfinite(a).all() and np.isfinite(b).all()):  # NaN breaks a curve into pieces
                    continue
                n = max(2, int(np.linalg.norm(b - a) / SAMPLE_PX) + 1)
                t = np.linspace(0, 1, n)[:, None]
                pts.append(a + (b - a) * t)
                half.append(np.full(n, lw * self.px / 2))

        def sample(v, lw):
            for a, b in zip(v[:-1], v[1:]):
                n = max(2, int(np.linalg.norm(b - a) / SAMPLE_PX) + 1)
                pts.append(a + (b - a) * np.linspace(0, 1, n)[:, None])
                half.append(np.full(n, lw * self.px / 2))

        for p in ax.patches:
            if isinstance(p, FancyArrowPatch):
                # split at MOVETO, so the shaft and the arrowheads aren't joined by a phantom segment
                path = p.get_path().transformed(p.get_transform()) if p.get_transform() else p.get_path()
                for v in path.to_polygons(closed_only=False):
                    sample(np.asarray(v, float), p.get_linewidth())
            elif p.get_linewidth() >= LIGHT_LW and p.get_edgecolor()[3] > 0:
                # outlines drawn by Figure.custom (bars, boxes, circles); fills with lw=0 are not obstacles
                for v in p.get_path().transformed(p.get_transform()).to_polygons(closed_only=False):
                    sample(np.asarray(v, float), p.get_linewidth())
        for c in ax.collections:
            if isinstance(c, LineCollection):
                lws = np.resize(np.asarray(c.get_linewidths(), float), len(c.get_segments()) or 1)
                for seg, lw in zip(c.get_segments(), lws):
                    if lw >= LIGHT_LW and len(seg) > 1:
                        sample(c.get_transform().transform(np.asarray(seg, float)), lw)
        self.line_pts = np.vstack(pts) if pts else np.zeros((0, 2))
        self.line_half = np.concatenate(half) if half else np.zeros(0)
        dots, rad = [], []
        for c in ax.collections:
            if isinstance(c, PathCollection):
                off = ax.transData.transform(np.asarray(c.get_offsets(), float))
                sizes = np.resize(np.asarray(c.get_sizes(), float), len(off))
                dots.append(off)
                rad.append(np.sqrt(sizes) / 2 * self.px)
        self.dots = np.vstack(dots) if dots else np.zeros((0, 2))
        self.dot_r = np.concatenate(rad) if rad else np.zeros(0)
        self.boxes: list[tuple[np.ndarray, str]] = []
        renderer = fig.canvas.get_renderer()
        for t in ax.texts:  # text drawn by Figure.custom (labels are not drawn yet when the scene is built)
            if t.get_visible() and t.get_text().strip():
                bb = t.get_window_extent(renderer)
                self.boxes.append((np.array([bb.x0, bb.y0, bb.x1, bb.y1]), _plain(t.get_text())))
        W, H = fig.canvas.get_width_height()
        self.canvas = (0, 0, W, H)

    def hits(self, box, clear):
        """Names of what the box (x0, y0, x1, y1) touches."""
        x0, y0, x1, y1 = box
        out = []
        if len(self.line_pts):
            e = clear + self.line_half
            p = self.line_pts
            if np.any((p[:, 0] > x0 - e) & (p[:, 0] < x1 + e) & (p[:, 1] > y0 - e) & (p[:, 1] < y1 + e)):
                out.append("a line")
        if len(self.dots):
            e = clear + self.dot_r
            d = self.dots
            if np.any((d[:, 0] > x0 - e) & (d[:, 0] < x1 + e) & (d[:, 1] > y0 - e) & (d[:, 1] < y1 + e)):
                out.append("a dot")
        for b, name in self.boxes:
            c2 = clear * LABEL_GAP
            if not (x1 + c2 < b[0] or b[2] + c2 < x0 or y1 + c2 < b[1] or b[3] + c2 < y0):
                out.append(f"label {name}")
        cx0, cy0, cx1, cy1 = self.canvas
        if x0 < cx0 or y0 < cy0 or x1 > cx1 or y1 > cy1:
            out.append("the edge")
        return out


def _plain(s: str) -> str:
    """Label text as read: no $, ° for ^\\circ, math spacing commands dropped, no grouping braces."""
    s = s.replace("$", "").replace(r"^\circ", "°").replace(r"^{\circ}", "°")
    return s.replace(r"\,", "").replace(r"\ ", " ").replace("{", "").replace("}", "").replace("\\", "")


def _box(ax, renderer, lab: Label, xy, off, dpi):
    a = ax.annotate(lab.s, xy=xy, xytext=tuple(off), textcoords="offset points", fontsize=lab.size,
                    ha="center", va="center", annotation_clip=False)
    try:
        bb = a.get_window_extent(renderer)
    finally:
        a.remove()
    l, b, r, t = _ink_insets(lab.s, lab.size, dpi)
    return np.array([bb.x0 + l * bb.width, bb.y0 + b * bb.height, bb.x1 - r * bb.width, bb.y1 - t * bb.height])


def place_labels(fig, ax, labels: list[Label], point_anchors: np.ndarray, dpi: int) -> list[str]:
    """Pick a candidate for every label. Returns lint messages for labels that still touch something."""
    renderer = fig.canvas.get_renderer()
    scene = _Scene(fig, ax, dpi)
    clear = CLEAR_PT * scene.px
    anchors_px = ax.transData.transform(point_anchors) if len(point_anchors) else np.zeros((0, 2))
    issues = []
    for lab in labels:
        own = ax.transData.transform(lab.anchor[None])[0]
        best = None
        cands = lab.cands[:1] if lab.fixed else lab.cands
        for i, (xy, off) in enumerate(cands):
            box = _box(ax, renderer, lab, xy, off, dpi)
            hit = scene.hits(box, clear)
            if lab.kind == "point" and len(anchors_px):
                c = np.array([(box[0] + box[2]) / 2, (box[1] + box[3]) / 2])
                d_own = np.linalg.norm(c - own)
                d = np.linalg.norm(anchors_px - c, axis=1)
                others = d[np.linalg.norm(anchors_px - own, axis=1) > 2]
                if len(others) and others.min() < d_own - 2:
                    hit = hit + ["another point"]
            if best is None or len(hit) < len(best[2]):
                best = (i, box, hit)
            if not hit:
                break
        i, box, hit = best
        lab.choice = i
        scene.boxes.append((box, _plain(lab.s)))
        if hit:
            issues.append(f"label {_plain(lab.s)!r} touches {', '.join(dict.fromkeys(hit))}")
    return issues


_MATH_SEG = re.compile(r"\$[^$]*\$")


def prime_styles(s: str) -> set[str]:
    """Prime forms used in one label as written: the U+2032 glyph anywhere, and `^{\\prime}`, `\\prime` or an
    ASCII `'` inside `$..$` (an apostrophe outside math is plain text, not a prime)."""
    out = {"\u2032"} if "\u2032" in s else set()
    for m in _MATH_SEG.finditer(s):
        t = m.group(0)
        if r"^{\prime}" in t:
            out.add(r"^{\prime}")
            t = t.replace(r"^{\prime}", "")
        if r"\prime" in t:
            out.add(r"\prime")
        if "'" in t:
            out.add("'")
    return out


def prime_lint(labels: list[Label]) -> list[str]:
    """One message when the labels of one figure mix prime forms (they print the same, but the source should
    read one way so search, integrity checks, and later edits find every label)."""
    styles = set().union(*(prime_styles(lab.raw or lab.s) for lab in labels)) if labels else set()
    if len(styles) < 2:
        return []
    return [f"mixed prime styles in labels: {' '.join(sorted(styles))} (write A' everywhere)"]

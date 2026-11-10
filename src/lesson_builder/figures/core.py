"""Figure with a "given" layer (black, student copy) and an "answer" layer (red, key only)."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.patches import FancyArrowPatch  # noqa: E402
from PIL import Image, ImageOps  # noqa: E402

from .geometry import vertex_directions  # noqa: E402
from .layout import (  # noqa: E402
    Label, _plain, angle_candidates, nudge_candidates, offset_candidates, place_labels, prime_lint,
)

BLACK = "#000000"
RED = "#C00000"
LW = 1.3
FS = 13
DPI = 300
TRIM_PAD = 8
MARGIN_IN = 0.75  # blank canvas around the axes so nothing is clipped; trimmed away afterwards
RC = {"mathtext.fontset": "stix", "font.family": "STIXGeneral"}
LAYERS = ("given", "answer")
COLORS = {"given": BLACK, "answer": RED}


@dataclass
class _Op:
    layer: str
    draw: Callable
    pts: np.ndarray
    pad_pt: float = 0.0  # extra room (points) needed around pts, e.g. for offset labels
    z: float = 0.0
    kind: str = "ink"    # ink | dots | label | custom
    label: Label | None = None


_MATH = re.compile(r"\$[^$]*\$")


def math_fix(s: str) -> str:
    """Primes as the U+2032 glyph inside mathtext: `$A'$` sets the prime tight against the letter."""
    return _MATH.sub(lambda m: m.group(0).replace(r"^{\prime}", "\u2032").replace(r"\prime", "\u2032")
                     .replace("'", "\u2032"), s)


def _probe_extent(draw) -> np.ndarray:
    """Data extent [(x0, y0), (x1, y1)] of what a custom drawing adds to an axes' data limits."""
    fig = plt.figure(figsize=(2, 2), dpi=72)
    try:
        ax = fig.add_axes((0, 0, 1, 1))
        draw(ax)
        dl = ax.dataLim
        box = np.array([[dl.x0, dl.y0], [dl.x1, dl.y1]], float)
    finally:
        plt.close(fig)
    if not np.all(np.isfinite(box)) or np.any(box[1] < box[0]):
        raise ValueError("Figure.custom: the drawing has no data extent (only text?); pass extent=[(x0, y0), (x1, y1)]")
    return box


@dataclass
class Figure:
    """Canvas of width_in x height_in inches with one shared x/y scale.

    key_frame="same" (default): limits come from all layers, and the student and key images share one frame,
    so the student copy has blank room where the answer goes. key_frame="union": the student frame fits the
    given layer only; the key keeps the same scale (data units per inch) and its canvas grows to the union of
    given and answer ink, so an answer that reaches past the given drawing isn't cut off or shrunk into the
    student frame. The key image is then larger than the student image (sidecar `key_width_in`)."""
    width_in: float
    height_in: float
    name: str | None = None
    key_frame: str = "same"
    _ops: list[_Op] = field(default_factory=list, repr=False)
    lint: list[str] = field(default_factory=list, repr=False)
    _placed: bool = field(default=False, repr=False)

    def __post_init__(self):
        if self.key_frame not in ("same", "union"):
            raise ValueError(f"key_frame must be 'same' or 'union', not {self.key_frame!r}")

    # ------------------------------------------------------------ recording
    def _add(self, layer, draw, pts, pad_pt=0.0, kind="ink", label=None):
        if layer not in LAYERS:
            raise ValueError(f"layer must be 'given' or 'answer', not {layer!r}")
        self._ops.append(_Op(layer, draw, np.atleast_2d(np.asarray(pts, float)), pad_pt, kind=kind, label=label))
        self._placed = False

    def custom(self, fn: Callable, layer="given", extent=None, pad_pt=0.0):
        """Arbitrary matplotlib drawing in data units: `fn(ax, color)` is called on every render (so it must
        not depend on state it changes). `color` is black on the given layer and red on the answer layer; pass
        it to every artist. While fn runs, the colour cycle, line, patch edge, hatch and text colours are set
        to `color`, but explicit colours win: keep given-layer ink black, gray or white (render_all lints
        colour on the student image). The frame comes from `extent` [(x0, y0), (x1, y1)] if given, else from
        what fn adds to the axes data limits (lines, patches, collections; ax.text does not count).
        Drawn after the ink recorded before it and before every label. Label placement treats its lines,
        LineCollections, outlined patches (lw >= 0.6), scatter dots, and texts as obstacles; filled areas
        without an outline are not obstacles. pad_pt reserves room (points) around the extent."""
        if layer not in LAYERS:
            raise ValueError(f"layer must be 'given' or 'answer', not {layer!r}")
        c = COLORS[layer]
        rc = {"lines.color": c, "patch.edgecolor": c, "hatch.color": c, "text.color": c,
              "axes.prop_cycle": matplotlib.cycler(color=[c]), "image.cmap": "gray"}

        def draw(ax):
            ax.set_prop_cycle(color=[c])
            with plt.rc_context(rc):
                fn(ax, c)
        if extent is None:
            extent = _probe_extent(draw)
        self._add(layer, draw, extent, pad_pt, kind="custom")

    def grid(self, x0, x1, y0, y1, step=1, lw=0.3, layer="given"):
        """Light square grid. Grid lines are thinner than LIGHT_LW, so labels may sit on them."""
        for x in np.arange(x0, x1 + 1e-9, step):
            self.seg((x, y0), (x, y1), lw=lw, layer=layer)
        for y in np.arange(y0, y1 + 1e-9, step):
            self.seg((x0, y), (x1, y), lw=lw, layer=layer)

    def poly(self, pts, closed=True, layer="given", lw=None, dashed=False, fill=None, hatch=None):
        pts = np.asarray(pts, float)
        path = np.vstack([pts, pts[:1]]) if closed else pts
        c = COLORS[layer]

        def draw(ax):
            if fill or hatch:
                ax.fill(path[:, 0], path[:, 1], facecolor=fill or "none", edgecolor=c, hatch=hatch, lw=0,
                        zorder=1, clip_on=False)
            ax.plot(path[:, 0], path[:, 1], color=c, lw=lw or LW, ls="--" if dashed else "-",
                    solid_joinstyle="round", zorder=2.5 if layer == "answer" else 2, clip_on=False)
        self._add(layer, draw, pts)

    def seg(self, a, b, layer="given", lw=None, dashed=False):
        self.poly([a, b], closed=False, layer=layer, lw=lw, dashed=dashed)

    def dots(self, pts, layer="given", size=14):
        pts = np.atleast_2d(np.asarray(pts, float))
        self._add(layer, lambda ax: ax.scatter(pts[:, 0], pts[:, 1], s=size, color=COLORS[layer],
                                               zorder=3.5 if layer == "answer" else 3, clip_on=False), pts,
                  kind="dots")

    def label(self, pt, text, layer="given", direction=None, center=None, offset_pt=10, size=None, italic=True,
              fixed=False):
        """Point label. `direction` is the preferred side; if that spot touches ink, the nearest clear spot
        is used (see layout.py). fixed=True keeps the requested spot."""
        pt = np.asarray(pt, float)
        d = np.asarray(direction, float) if direction is not None else (
            pt - np.asarray(center, float) if center is not None else np.array([0.0, 1.0]))
        n = np.linalg.norm(d)
        d = d / n if n else np.array([0.0, 1.0])
        self._annotate(pt, f"${text}$" if italic else text, d * offset_pt, layer, size or FS, "point", fixed)

    def _annotate(self, pt, s, off_pt, layer, size, kind="point", fixed=False, anchor=None):
        raw, s = s, math_fix(s)
        pt = np.asarray(pt, float)
        lab = Label(layer, s, size, kind, np.asarray(anchor if anchor is not None else pt, float),
                    offset_candidates(pt, off_pt, size), fixed, raw=raw)
        self._add(layer, lambda ax: ax.annotate(
            lab.s, xy=lab.xy, xytext=tuple(lab.off), textcoords="offset points", fontsize=size, ha="center",
            va="center", color=COLORS[layer], zorder=4, annotation_clip=False), pt,
            pad_pt=float(np.linalg.norm(off_pt)) + 0.9 * size, kind="label", label=lab)

    def label_poly(self, pts, names, layer="given", overrides=None, offset_pt=10):
        pts = np.asarray(pts, float)
        overrides = overrides or {}
        for p, nm, d in zip(pts, list(names), vertex_directions(pts)):
            if nm is not None:
                self.label(p, nm, layer=layer, direction=overrides.get(nm, d), offset_pt=offset_pt)

    def ticks(self, a, b, n=1, layer="given", size=0.12):
        a, b = np.asarray(a, float), np.asarray(b, float)
        u = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([-u[1], u[0]])
        m = (a + b) / 2
        gap = 0.75 * size
        strokes = []
        for k in range(n):
            c = m + u * (k - (n - 1) / 2) * gap
            strokes.append((c - nrm * size, c + nrm * size))

        def draw(ax):
            for p, q in strokes:
                ax.plot([p[0], q[0]], [p[1], q[1]], color=COLORS[layer], lw=1.1, zorder=3,
                        solid_capstyle="butt", clip_on=False)
        self._add(layer, draw, np.array([p for s in strokes for p in s]))

    def parallel_marks(self, a, b, n=1, layer="given", size=0.13):
        """n arrowheads (>, >>) at the middle of segment ab, pointing from a to b: the usual 'parallel' mark."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        u = (b - a) / np.linalg.norm(b - a)
        nrm = np.array([-u[1], u[0]])
        m = (a + b) / 2
        heads = []
        for k in range(n):
            tip = m + u * (k - (n - 1) / 2) * 0.9 * size + u * size / 2
            heads.append(np.array([tip - u * size + nrm * size * 0.6, tip, tip - u * size - nrm * size * 0.6]))

        def draw(ax):
            for h in heads:
                ax.plot(h[:, 0], h[:, 1], color=COLORS[layer], lw=1.1, zorder=3, solid_joinstyle="miter",
                        clip_on=False)
        self._add(layer, draw, np.vstack(heads))

    def arc(self, vertex, p1, p2, n=1, r=0.35, layer="given", gap=0.07):
        v, p1, p2 = (np.asarray(x, float) for x in (vertex, p1, p2))
        a1 = np.degrees(np.arctan2(*(p1 - v)[::-1]))
        a2 = np.degrees(np.arctan2(*(p2 - v)[::-1]))
        d = (a2 - a1) % 360
        if d > 180:
            a1, d = a2, 360 - d
        t = np.radians(np.linspace(a1, a1 + d, 40))
        curves = [np.c_[v[0] + (r + k * gap) * np.cos(t), v[1] + (r + k * gap) * np.sin(t)] for k in range(n)]

        def draw(ax):
            for c in curves:
                ax.plot(c[:, 0], c[:, 1], color=COLORS[layer], lw=1.0, zorder=3, clip_on=False)
        self._add(layer, draw, np.vstack(curves))

    def right_angle(self, vertex, p1, p2, size=0.18, layer="given"):
        v, p1, p2 = (np.asarray(x, float) for x in (vertex, p1, p2))
        u1 = (p1 - v) / np.linalg.norm(p1 - v) * size
        u2 = (p2 - v) / np.linalg.norm(p2 - v) * size
        pts = np.array([v + u1, v + u1 + u2, v + u2])
        self._add(layer, lambda ax: ax.plot(pts[:, 0], pts[:, 1], color=COLORS[layer], lw=1.0, zorder=3,
                                            clip_on=False), pts)

    def side_label(self, a, b, text, center, layer="given", offset_pt=10, italic=False, size=None, fixed=False):
        a, b = np.asarray(a, float), np.asarray(b, float)
        m = (a + b) / 2
        nrm = np.array([-(b - a)[1], (b - a)[0]])
        nrm /= np.linalg.norm(nrm)
        if np.dot(nrm, m - np.asarray(center, float)) < 0:
            nrm = -nrm
        self._annotate(m, f"${text}$" if italic else text, nrm * offset_pt, layer, size or FS, "side", fixed)

    def angle_label(self, vertex, p1, p2, text, dist=None, layer="given", size=None, fixed=False):
        v, p1, p2 = (np.asarray(x, float) for x in (vertex, p1, p2))
        u1, u2 = (p1 - v) / np.linalg.norm(p1 - v), (p2 - v) / np.linalg.norm(p2 - v)
        b = u1 + u2
        b = b / np.linalg.norm(b) if np.linalg.norm(b) > 1e-9 else np.array([-u1[1], u1[0]])
        if dist is None:
            dist = 0.18 * min(np.linalg.norm(p1 - v), np.linalg.norm(p2 - v)) + 0.3
        half = float(np.degrees(np.arccos(np.clip(np.dot(u1, u2), -1, 1)))) / 2
        self._text(v + b * dist, text, layer, size or FS - 2, "angle", fixed, angle_candidates(v, b, dist, half), v)

    def arrow(self, a, b, layer="answer", dashed=True):
        a, b = np.asarray(a, float), np.asarray(b, float)
        self._add(layer, lambda ax: ax.add_patch(FancyArrowPatch(
            a, b, arrowstyle="-|>", mutation_scale=10, color=COLORS[layer], lw=1.0,
            ls=(0, (3, 2)) if dashed else "-", shrinkA=4, shrinkB=4, zorder=3, clip_on=False)), [a, b])

    def text(self, pt, s, layer="given", size=None, fixed=False):
        """Free text centered at pt. Nudged a little if it touches ink, unless fixed=True."""
        pt = np.asarray(pt, float)
        size = size or FS
        self._text(pt, s, layer, size, "text", fixed, nudge_candidates(pt, size), pt)

    def _text(self, pt, s, layer, size, kind, fixed, cands, anchor):
        lab = Label(layer, math_fix(s), size, kind, np.asarray(anchor, float), cands, fixed, raw=s)
        self._add(layer, lambda ax: ax.annotate(
            lab.s, xy=lab.xy, xytext=tuple(lab.off), textcoords="offset points", fontsize=size, ha="center",
            va="center", color=COLORS[layer], zorder=4, annotation_clip=False), pt, pad_pt=0.9 * size,
            kind="label", label=lab)

    # ------------------------------------------------------------ rendering
    def has_answer(self) -> bool:
        return any(op.layer == "answer" for op in self._ops)

    @property
    def labels(self) -> list[Label]:
        return [op.label for op in self._ops if op.label is not None]

    @property
    def min_text_pt(self) -> float | None:
        sizes = [lab.size for lab in self.labels]
        return min(sizes) if sizes else None

    def _new_axes(self, frame="student"):
        xl, yl, w_in, h_in = self._frame(frame)
        W, H = w_in + 2 * MARGIN_IN, h_in + 2 * MARGIN_IN
        fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="white")
        ax = fig.add_axes((MARGIN_IN / W, MARGIN_IN / H, w_in / W, h_in / H))
        ax.set_xlim(*xl)
        ax.set_ylim(*yl)
        ax.axis("off")
        return fig, ax

    def place(self) -> list[str]:
        """Choose label spots once, against the ink of ALL layers, so student and key labels match. Labels are
        placed on the key canvas; both frames share one scale, so the spots are the same on the student copy."""
        if self._placed:
            return self.lint
        with plt.rc_context(RC):
            fig, ax = self._new_axes("key")
            try:
                for op in self._ops:
                    if op.kind != "label":
                        op.draw(ax)
                fig.canvas.draw()
                anchors = [op.pts for op in self._ops if op.kind == "dots"]
                anchors += [op.label.anchor[None] for op in self._ops if op.label and op.label.kind == "point"]
                anchors = np.unique(np.round(np.vstack(anchors), 9), axis=0) if anchors else np.zeros((0, 2))
                self.lint = place_labels(fig, ax, self.labels, anchors, DPI) + prime_lint(self.labels)
            finally:
                plt.close(fig)
        self._placed = True
        return self.lint

    def _fit(self, ops):
        """Limits that fit `ops` (plus their label padding) into width_in x height_in at one shared scale."""
        allp = np.vstack([op.pts for op in ops])
        lo, hi = allp.min(0), allp.max(0)
        pad_in = max(op.pad_pt for op in ops) / 72 + 0.05
        w, h = max(self.width_in - 2 * pad_in, 0.3), max(self.height_in - 2 * pad_in, 0.3)
        span = np.maximum(hi - lo, 1e-6)
        scale = max(span[0] / w, span[1] / h)  # data units per inch
        c = (lo + hi) / 2
        hx, hy = self.width_in * scale / 2, self.height_in * scale / 2
        return (c[0] - hx, c[0] + hx), (c[1] - hy, c[1] + hy)

    def _frame(self, frame="student"):
        """(xlim, ylim, width_in, height_in) of the student or key canvas. See key_frame on the class."""
        if not self._ops:
            return (0, 1), (0, 1), self.width_in, self.height_in
        if self.key_frame == "same":
            xl, yl = self._fit(self._ops)
            return xl, yl, self.width_in, self.height_in
        given = [op for op in self._ops if op.layer == "given"] or self._ops
        xl, yl = self._fit(given)
        if frame != "key":
            return xl, yl, self.width_in, self.height_in
        s = (xl[1] - xl[0]) / self.width_in
        allp = np.vstack([op.pts for op in self._ops])
        pad = (max(op.pad_pt for op in self._ops) / 72 + 0.05) * s
        lo, hi = allp.min(0) - pad, allp.max(0) + pad
        xl = (min(xl[0], lo[0]), max(xl[1], hi[0]))
        yl = (min(yl[0], lo[1]), max(yl[1], hi[1]))
        return xl, yl, (xl[1] - xl[0]) / s, (yl[1] - yl[0]) / s

    def _limits(self, frame="student"):
        """Axis limits. With key_frame="same" they come from ALL layers, so student and key share one frame."""
        xl, yl, _, _ = self._frame(frame)
        return xl, yl

    def render(self, layers=("given",), frame=None) -> Image.Image:
        """Untrimmed RGB image of the requested layers on the full (margin-padded) canvas. The canvas is the key
        frame when the answer layer is drawn, else the student frame (identical unless key_frame="union")."""
        self.place()
        frame = frame or ("key" if "answer" in layers else "student")
        with plt.rc_context(RC):
            fig, ax = self._new_axes(frame)
            try:
                for op in self._ops:
                    if op.layer in layers:
                        op.draw(ax)
                fig.canvas.draw()
                img = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
            finally:
                plt.close(fig)
        return img

    def save(self, path, layers=("given",), bbox=None) -> Path:
        """Draw only `layers`, crop to the frame of the full drawing (all layers) unless `bbox` is given.
        With key_frame="union" each image crops to its own ink."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img = self.render(layers)
        if bbox is None:
            bbox = content_bbox(img)
            if self.has_answer() and not set(LAYERS) <= set(layers) and self.key_frame == "same":
                bbox = union_bbox(bbox, content_bbox(self.render(LAYERS)))
        crop(img, bbox).save(path, dpi=(DPI, DPI))
        return path


def content_bbox(img: Image.Image, pad=TRIM_PAD):
    """Bounding box of non-white pixels plus pad, or None if the image is blank."""
    bbox = ImageOps.invert(img.convert("L")).point(lambda v: 255 if v > 12 else 0).getbbox()
    if not bbox:
        return None
    l, t, r, b = bbox
    return (max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad))


def union_bbox(*boxes):
    boxes = [b for b in boxes if b]
    if not boxes:
        return None
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def crop(img: Image.Image, bbox) -> Image.Image:
    return img.crop(bbox) if bbox else img


def trim(path, pad=TRIM_PAD) -> Path:
    im = Image.open(path).convert("RGB")
    crop(im, content_bbox(im, pad)).save(path)
    return Path(path)


# ---------------------------------------------------------------- registry
_REGISTRY: dict[str, Callable[[], Figure]] = {}


def figure(name: str):
    def deco(fn: Callable[[], Figure]):
        _REGISTRY[name] = fn
        fn.figure_name = name
        return fn
    return deco


def _module_name(path: Path) -> str:
    h = hashlib.md5(str(path).lower().encode()).hexdigest()[:8]
    return f"_lesson_figures_{re.sub(r'\W', '_', path.stem)}_{h}"


def load_module(path: Path) -> ModuleType:
    """Import a figures file by path. Its folder is on sys.path while it runs, so sibling helper modules
    (for example figures/_helpers.py) can be imported with `from _helpers import ...`."""
    path = Path(path).resolve()
    name = _module_name(path)
    for k in [k for k, fn in _REGISTRY.items() if fn.__module__ == name]:
        del _REGISTRY[k]
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    folder = str(path.parent)
    # helpers are imported by bare name (`from _helpers import ...`): drop any cached module of that name, so
    # this file gets its own sibling (not another unit's _helpers.py) and an edited helper is re-read
    for h in path.parent.glob("_*.py"):
        sys.modules.pop(h.stem, None)
    sys.path.insert(0, folder)
    no_pyc, sys.dont_write_bytecode = sys.dont_write_bytecode, True   # no figures/__pycache__ litter
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    finally:
        sys.dont_write_bytecode = no_pyc
        if folder in sys.path:
            sys.path.remove(folder)
    return mod


def registered(module: ModuleType) -> dict[str, Callable[[], Figure]]:
    return {k: fn for k, fn in _REGISTRY.items() if fn.__module__ == module.__name__}


_LIB_DIR = Path(__file__).parent


def _deps(src: Path) -> list[Path]:
    """Files whose edits make a figure module's outputs stale: the module, its `_*.py` siblings (shared helpers
    such as figures/_helpers.py), every library file in this package, and the files in an `assets/` folder
    next to the module or one level up (the unit's assets/ for figures/<stem>.py)."""
    deps = [src, *src.parent.glob("_*.py"), *_LIB_DIR.glob("*.py")]
    for a in (src.parent / "assets", src.parent.parent / "assets"):
        if a.is_dir():
            deps += [p for p in a.rglob("*") if p.is_file()]
    return deps


def render_all(module_or_path, out_dir: Path, names: list[str] | None = None, force: bool = False
               ) -> dict[str, dict[str, Path | None]]:
    mod = module_or_path if isinstance(module_or_path, ModuleType) else load_module(Path(module_or_path))
    figs = registered(mod)
    if names is not None:
        missing = [n for n in names if n not in figs]
        if missing:
            raise KeyError(f"figures not registered in {mod.__name__}: {missing}")
        figs = {n: figs[n] for n in names}
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    src = getattr(mod, "__file__", None)
    # no source file -> never cached; otherwise outputs must be newer than the module, helpers, and library
    src_mtime = float("inf") if not src else max(p.stat().st_mtime for p in _deps(Path(src)))

    def fresh(p: Path):
        return not force and p.exists() and p.stat().st_mtime > src_mtime

    result = {}
    for name, fn in figs.items():
        f = fn()
        if not isinstance(f, Figure):
            raise TypeError(f"@figure({name!r}) returned {type(f).__name__}, not Figure")
        f.name = f.name or name
        student, key = out_dir / f"{name}.png", out_dir / f"{name}_key.png"
        meta_p = out_dir / f"{name}.json"
        if not f.has_answer():
            key.unlink(missing_ok=True)
            if not (fresh(student) and fresh(meta_p)):
                f.save(student)
                _write_meta(meta_p, f, student)
            result[name] = {"student": student, "key": None, "meta": json.loads(meta_p.read_text("utf-8"))}
            continue
        if not (fresh(student) and fresh(key) and fresh(meta_p)):
            full, given = f.render(LAYERS), f.render(("given",))
            if f.key_frame == "same":
                bbox = union_bbox(content_bbox(full), content_bbox(given))  # one frame for both images
                kbox = sbox = bbox
            else:
                kbox, sbox = content_bbox(full), content_bbox(given)  # each image fits its own ink
            crop(full, kbox).save(key, dpi=(DPI, DPI))
            crop(given, sbox).save(student, dpi=(DPI, DPI))
            _write_meta(meta_p, f, student, key)
        result[name] = {"student": student, "key": key, "meta": json.loads(meta_p.read_text("utf-8"))}
    return result


def _colour_lint(im: Image.Image) -> list[str]:
    """The student copy prints in black and white: flag coloured pixels (a matplotlib default colour leaking
    out of Figure.custom, or answer-red ink drawn on the given layer)."""
    a = np.asarray(im.convert("RGB")).astype(int)
    n = int(((a.max(-1) - a.min(-1)) > 60).sum())
    return [f"student copy has colour ink ({n} px); given layers must be black or gray"] if n > 20 else []


def _label_meta(f: Figure, layers=LAYERS) -> list[dict]:
    """Label texts for the integrity checks: text (as printed, $ and backslashes dropped, primes as U+2032),
    raw (as written), layer, kind (point | side | angle | text)."""
    return [{"text": _plain(lab.s), "raw": lab.raw or lab.s, "layer": lab.layer, "kind": lab.kind}
            for lab in f.labels if lab.layer in layers]


def _write_meta(path: Path, f: Figure, png: Path, key_png: Path | None = None):
    """Sidecar for the checks: drawn width (inches at 300 dpi), smallest text size, lint, label texts
    (`labels` on every layer, `key_labels` on the answer layer only), and the key's width when it has one."""
    with Image.open(png) as im:
        w_in = im.width / DPI
        lint = list(f.place()) + _colour_lint(im)
    meta = {"width_in": round(w_in, 3), "min_text_pt": f.min_text_pt, "lint": lint, "key_frame": f.key_frame,
            "labels": _label_meta(f), "key_labels": _label_meta(f, ("answer",))}
    if key_png is not None:
        with Image.open(key_png) as im:
            meta["key_width_in"] = round(im.width / DPI, 3)
    path.write_text(json.dumps(meta, indent=1, ensure_ascii=False), encoding="utf-8")

"""Figure with a "given" layer (black, student copy) and an "answer" layer (red, key only)."""
from __future__ import annotations

import hashlib
import importlib.util
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


@dataclass
class Figure:
    width_in: float
    height_in: float
    name: str | None = None
    _ops: list[_Op] = field(default_factory=list, repr=False)

    # ------------------------------------------------------------ recording
    def _add(self, layer, draw, pts, pad_pt=0.0):
        if layer not in LAYERS:
            raise ValueError(f"layer must be 'given' or 'answer', not {layer!r}")
        self._ops.append(_Op(layer, draw, np.atleast_2d(np.asarray(pts, float)), pad_pt))

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
                                               zorder=3.5 if layer == "answer" else 3, clip_on=False), pts)

    def label(self, pt, text, layer="given", direction=None, center=None, offset_pt=10, size=None, italic=True):
        pt = np.asarray(pt, float)
        d = np.asarray(direction, float) if direction is not None else (
            pt - np.asarray(center, float) if center is not None else np.array([0.0, 1.0]))
        n = np.linalg.norm(d)
        d = d / n if n else np.array([0.0, 1.0])
        self._annotate(pt, f"${text}$" if italic else text, d * offset_pt, layer, size or FS)

    def _annotate(self, pt, s, off_pt, layer, size):
        self._add(layer, lambda ax: ax.annotate(
            s, xy=pt, xytext=tuple(off_pt), textcoords="offset points", fontsize=size, ha="center",
            va="center", color=COLORS[layer], zorder=4, annotation_clip=False), pt,
            pad_pt=float(np.linalg.norm(off_pt)) + 0.9 * size)

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

    def side_label(self, a, b, text, center, layer="given", offset_pt=10, italic=False, size=None):
        a, b = np.asarray(a, float), np.asarray(b, float)
        m = (a + b) / 2
        nrm = np.array([-(b - a)[1], (b - a)[0]])
        nrm /= np.linalg.norm(nrm)
        if np.dot(nrm, m - np.asarray(center, float)) < 0:
            nrm = -nrm
        self._annotate(m, f"${text}$" if italic else text, nrm * offset_pt, layer, size or FS)

    def angle_label(self, vertex, p1, p2, text, dist=None, layer="given", size=None):
        v, p1, p2 = (np.asarray(x, float) for x in (vertex, p1, p2))
        u1, u2 = (p1 - v) / np.linalg.norm(p1 - v), (p2 - v) / np.linalg.norm(p2 - v)
        b = u1 + u2
        b = b / np.linalg.norm(b) if np.linalg.norm(b) > 1e-9 else np.array([-u1[1], u1[0]])
        if dist is None:
            dist = 0.18 * min(np.linalg.norm(p1 - v), np.linalg.norm(p2 - v)) + 0.3
        self.text(v + b * dist, text, layer=layer, size=size or FS - 2)

    def arrow(self, a, b, layer="answer", dashed=True):
        a, b = np.asarray(a, float), np.asarray(b, float)
        self._add(layer, lambda ax: ax.add_patch(FancyArrowPatch(
            a, b, arrowstyle="-|>", mutation_scale=10, color=COLORS[layer], lw=1.0,
            ls=(0, (3, 2)) if dashed else "-", shrinkA=4, shrinkB=4, zorder=3, clip_on=False)), [a, b])

    def text(self, pt, s, layer="given", size=None):
        pt = np.asarray(pt, float)
        size = size or FS
        self._add(layer, lambda ax: ax.text(pt[0], pt[1], s, fontsize=size, ha="center", va="center",
                                            color=COLORS[layer], zorder=4, clip_on=False), pt,
                  pad_pt=0.9 * size)

    # ------------------------------------------------------------ rendering
    def has_answer(self) -> bool:
        return any(op.layer == "answer" for op in self._ops)

    def _limits(self):
        """Axis limits from ALL layers, so student and key share one scale and frame."""
        if not self._ops:
            return (0, 1), (0, 1)
        allp = np.vstack([op.pts for op in self._ops])
        lo, hi = allp.min(0), allp.max(0)
        pad_in = max(op.pad_pt for op in self._ops) / 72 + 0.05
        w, h = max(self.width_in - 2 * pad_in, 0.3), max(self.height_in - 2 * pad_in, 0.3)
        span = np.maximum(hi - lo, 1e-6)
        scale = max(span[0] / w, span[1] / h)  # data units per inch
        c = (lo + hi) / 2
        hx, hy = self.width_in * scale / 2, self.height_in * scale / 2
        return (c[0] - hx, c[0] + hx), (c[1] - hy, c[1] + hy)

    def render(self, layers=("given",)) -> Image.Image:
        """Untrimmed RGB image of the requested layers on the full (margin-padded) canvas."""
        xl, yl = self._limits()
        W, H = self.width_in + 2 * MARGIN_IN, self.height_in + 2 * MARGIN_IN
        with plt.rc_context(RC):
            fig = plt.figure(figsize=(W, H), dpi=DPI, facecolor="white")
            try:
                ax = fig.add_axes((MARGIN_IN / W, MARGIN_IN / H, self.width_in / W, self.height_in / H))
                ax.set_xlim(*xl)
                ax.set_ylim(*yl)
                ax.axis("off")
                for op in self._ops:
                    if op.layer in layers:
                        op.draw(ax)
                fig.canvas.draw()
                img = Image.fromarray(np.asarray(fig.canvas.buffer_rgba())[..., :3].copy())
            finally:
                plt.close(fig)
        return img

    def save(self, path, layers=("given",), bbox=None) -> Path:
        """Draw only `layers`, crop to the frame of the full drawing (all layers) unless `bbox` is given."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        img = self.render(layers)
        if bbox is None:
            bbox = content_bbox(img)
            if self.has_answer() and not set(LAYERS) <= set(layers):
                bbox = union_bbox(bbox, content_bbox(self.render(LAYERS)))
        crop(img, bbox).save(path, dpi=(DPI, DPI))
        return path


def content_bbox(img: Image.Image, pad=TRIM_PAD):
    bbox = ImageOps.invert(img.convert("L")).point(lambda v: 255 if v > 12 else 0).getbbox()
    if not bbox:
        return (0, 0, img.width, img.height)
    l, t, r, b = bbox
    return (max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad))


def union_bbox(*boxes):
    return (min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes))


def crop(img: Image.Image, bbox) -> Image.Image:
    return img.crop(bbox)


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
    path = Path(path).resolve()
    name = _module_name(path)
    for k in [k for k, fn in _REGISTRY.items() if fn.__module__ == name]:
        del _REGISTRY[k]
    sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return mod


def registered(module: ModuleType) -> dict[str, Callable[[], Figure]]:
    return {k: fn for k, fn in _REGISTRY.items() if fn.__module__ == module.__name__}


_LIB_FILES = (Path(__file__), Path(__file__).with_name("geometry.py"))


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
    # no source file -> never cached; otherwise outputs must be newer than the module and this library
    src_mtime = float("inf") if not src else max(p.stat().st_mtime for p in (Path(src), *_LIB_FILES))

    def fresh(p: Path):
        return not force and p.exists() and p.stat().st_mtime > src_mtime

    result = {}
    for name, fn in figs.items():
        f = fn()
        if not isinstance(f, Figure):
            raise TypeError(f"@figure({name!r}) returned {type(f).__name__}, not Figure")
        f.name = f.name or name
        student, key = out_dir / f"{name}.png", out_dir / f"{name}_key.png"
        if not f.has_answer():
            key.unlink(missing_ok=True)
            if not fresh(student):
                f.save(student)
            result[name] = {"student": student, "key": None}
            continue
        if not (fresh(student) and fresh(key)):
            full, given = f.render(LAYERS), f.render(("given",))
            bbox = union_bbox(content_bbox(full), content_bbox(given))  # one frame for both images
            crop(full, bbox).save(key, dpi=(DPI, DPI))
            crop(given, bbox).save(student, dpi=(DPI, DPI))
        result[name] = {"student": student, "key": key}
    return result

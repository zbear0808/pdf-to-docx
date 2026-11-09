"""Rigid-motion and correspondence helpers (numpy only), plus two Figure templates."""
from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np


def P(*pts) -> np.ndarray:
    return np.array(pts, dtype=float)


def _arr(pts) -> np.ndarray:
    return np.atleast_2d(np.asarray(pts, dtype=float))


def rotate(pts, deg, about=(0, 0)) -> np.ndarray:
    t = np.radians(deg)
    R = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
    a = np.asarray(about, float)
    return (_arr(pts) - a) @ R.T + a


def reflect(pts, p1, p2) -> np.ndarray:
    p1, p2 = np.asarray(p1, float), np.asarray(p2, float)
    d = (p2 - p1) / np.linalg.norm(p2 - p1)
    v = _arr(pts) - p1
    return p1 + 2 * np.outer(v @ d, d) - v


def translate(pts, v) -> np.ndarray:
    return _arr(pts) + np.asarray(v, float)


def fit_rigid(src, dst_approx, allow_reflection=True) -> np.ndarray:
    src, dst = _arr(src), _arr(dst_approx)
    cs, cd = src.mean(0), dst.mean(0)
    U, _, Vt = np.linalg.svd((src - cs).T @ (dst - cd))
    R = (U @ Vt).T
    if not allow_reflection and np.linalg.det(R) < 0:
        Vt[-1] *= -1
        R = (U @ Vt).T
    return (src - cs) @ R.T + cd


def _pairwise(pts) -> np.ndarray:
    pts = _arr(pts)
    return np.linalg.norm(pts[:, None] - pts[None], axis=-1)


def is_rigid_image(src, img, tol=1e-6) -> bool:
    src, img = _arr(src), _arr(img)
    return src.shape == img.shape and bool(np.allclose(_pairwise(src), _pairwise(img), atol=tol))


def signed_area(pts) -> float:
    x, y = _arr(pts).T
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def orientation(pts) -> int:
    return 1 if signed_area(pts) > 0 else -1


def needs_reflection(src, img) -> bool:
    return orientation(src) != orientation(img)


def _names(names) -> list[str]:
    return list(names) if isinstance(names, str) else [str(n) for n in names]


def correspondence(names_src, names_img) -> dict[str, str]:
    a, b = _names(names_src), _names(names_img)
    if len(a) != len(b):
        raise ValueError(f"{names_src!r} and {names_img!r} have different lengths")
    return dict(zip(a, b))


def congruence_statement(names_src, names_img, order) -> str:
    corr = correspondence(names_src, names_img)
    return "".join(corr[c] for c in _names(order))


def ssa_triangles(adj, opp, angle_deg) -> tuple[np.ndarray, np.ndarray]:
    """Vertex V at the origin, VW = adj along +x, angle V = angle_deg, WU = opp.
    Returns (long, short): the two triangles [V, W, U] with the longer / shorter third side VU."""
    a = np.radians(angle_deg)
    # U = t(cos a, sin a) with |U - W| = opp:  t^2 - 2 t adj cos a + adj^2 - opp^2 = 0
    disc2 = (adj * np.cos(a)) ** 2 - (adj ** 2 - opp ** 2)
    if disc2 <= 0:
        raise ValueError("these measures do not give two SSA triangles")
    ts = adj * np.cos(a) + np.array([1, -1]) * np.sqrt(disc2)
    if ts.min() <= 0:
        raise ValueError("these measures do not give two SSA triangles")
    return tuple(P((0, 0), (adj, 0), (t * np.cos(a), t * np.sin(a))) for t in ts)


def midpoint(a, b) -> np.ndarray:
    return (np.asarray(a, float) + np.asarray(b, float)) / 2


def dist(a, b) -> float:
    return float(np.linalg.norm(np.asarray(b, float) - np.asarray(a, float)))


def angle_deg(vertex, p1, p2) -> float:
    v = np.asarray(vertex, float)
    u, w = np.asarray(p1, float) - v, np.asarray(p2, float) - v
    c = np.dot(u, w) / (np.linalg.norm(u) * np.linalg.norm(w))
    return float(np.degrees(np.arccos(np.clip(c, -1, 1))))


def _cross(u, v) -> float:
    return float(u[0] * v[1] - u[1] * v[0])


# ---------------------------------------------------------------- templates
def _mark_scale(pts) -> float:
    pts = _arr(pts)
    sides = [dist(pts[i], pts[(i + 1) % len(pts)]) for i in range(len(pts))]
    return min(sides)


def congruent_pair(src_pts, names_src, motion: Callable, names_img, offset=(0, 0), marks=True,
                   width_in=5.5, height_in=2.4):
    from .core import Figure

    src = _arr(src_pts)
    img = translate(motion(src), offset)
    assert is_rigid_image(src, img), "motion is not rigid"
    n = len(src)
    s = _mark_scale(src)
    f = Figure(width_in, height_in)
    mark_layer = "answer" if marks == "answer" else "given"
    for pts, names in ((src, names_src), (img, names_img)):
        f.poly(pts)
        f.dots(pts)
        if marks:
            for i in range(n):
                f.ticks(pts[i], pts[(i + 1) % n], n=i + 1, size=0.07 * s, layer=mark_layer)
                f.arc(pts[i], pts[i - 1], pts[(i + 1) % n], n=i + 1, r=0.16 * s, gap=0.035 * s, layer=mark_layer)
        f.label_poly(pts, _names(names))
    info = {"image_pts": img, "correspondence": correspondence(names_src, names_img),
            "needs_reflection": needs_reflection(src, img)}
    return f, info


def rotation_build(tri_pts, names="ABC", image_name="D", width_in=3.0):
    from .core import Figure

    tri = _arr(tri_pts)
    assert tri.shape == (3, 2)
    names = _names(names)
    # i, j = ends of the longest side, k = the opposite vertex
    k = int(np.argmax([dist(tri[(m + 1) % 3], tri[(m + 2) % 3]) for m in range(3)]))
    i, j = (k + 1) % 3, (k + 2) % 3
    A, B, C = tri[i], tri[k], tri[j]          # parallelogram A-B-C-D with diagonal AC
    nA, nB, nC = names[i], names[k], names[j]
    M = midpoint(A, C)
    D = rotate(B, 180, about=M)[0]
    assert np.allclose(rotate([A, C], 180, about=M), [C, A])
    assert np.isclose(dist(A, B), dist(C, D)) and np.isclose(dist(B, C), dist(D, A))
    assert np.isclose(_cross(B - A, D - C), 0) and np.isclose(_cross(C - B, D - A), 0)
    assert np.allclose(midpoint(B, D), M)

    quad = np.array([A, B, C, D])
    dx, dy = np.ptp(quad, axis=0)
    f = Figure(width_in, float(np.clip(width_in * dy / dx + 0.6, 1.4, 3.6)))
    s = dist(A, C) / 4.0
    f.poly(tri)
    f.seg(C, D, layer="answer")
    f.seg(D, A, layer="answer")
    f.dots(tri)
    f.dots([M, D], layer="answer")
    for a, b, n in ((A, B, 1), (C, D, 1), (B, C, 2), (D, A, 2)):
        f.ticks(a, b, n, layer="answer", size=0.1 * s)
    gap = 0.07 * s
    f.arc(B, A, C, 1, r=0.32 * s, gap=gap, layer="answer")
    f.arc(D, C, A, 1, r=0.32 * s, gap=gap, layer="answer")
    f.arc(A, B, C, 2, r=0.42 * s, gap=gap, layer="answer")
    f.arc(C, D, A, 2, r=0.42 * s, gap=gap, layer="answer")
    f.arc(A, D, C, 3, r=0.62 * s, gap=gap, layer="answer")
    f.arc(C, B, A, 3, r=0.62 * s, gap=gap, layer="answer")
    dirs = vertex_directions(quad)
    for p, nm, d in zip((A, B, C), (nA, nB, nC), dirs):
        f.label(p, nm, direction=d)
    f.label(D, image_name, direction=dirs[3], layer="answer")
    # M sits on diagonal AC; put its label off the diagonal, on the D side, tilted toward C
    u = (C - A) / dist(A, C)
    nrm = (D - M) - np.dot(D - M, u) * u
    f.label(M, "M", direction=nrm / np.linalg.norm(nrm) + 0.35 * u, layer="answer")
    return f


def vertex_directions(pts) -> list[np.ndarray]:
    """Outward unit direction at each vertex of a simple polygon (exterior angle bisector)."""
    pts = _arr(pts)
    n = len(pts)
    if n < 3:
        c = pts.mean(0)
        out = [p - c for p in pts]
        return [d / np.linalg.norm(d) if np.linalg.norm(d) else np.array([0.0, 1.0]) for d in out]
    o = orientation(pts)
    out = []
    for m in range(n):
        v, a, b = pts[m], pts[m - 1], pts[(m + 1) % n]
        u1, u2 = (a - v) / dist(a, v), (b - v) / dist(b, v)
        s = u1 + u2
        if np.linalg.norm(s) < 1e-9:  # straight angle: use the outward normal
            d = np.array([u2[1], -u2[0]]) * o
        else:
            convex = _cross(v - a, b - v) * o > 0
            d = -s if convex else s
        out.append(d / np.linalg.norm(d))
    return out


__all__: Sequence[str] = [
    "P", "rotate", "reflect", "translate", "fit_rigid", "is_rigid_image", "orientation", "signed_area",
    "needs_reflection", "correspondence", "congruence_statement", "ssa_triangles", "midpoint", "dist",
    "angle_deg", "vertex_directions", "congruent_pair", "rotation_build",
]

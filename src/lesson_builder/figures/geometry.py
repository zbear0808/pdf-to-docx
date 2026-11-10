"""Geometry helpers (numpy only): transforms, predicates, constructions, figure asserts, marks, and templates."""
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


def dilate(pts, k, center=(0, 0)) -> np.ndarray:
    """Dilation with scale factor k about center."""
    c = np.asarray(center, float)
    return c + k * (_arr(pts) - c)


def similarity_ratio(src, img, tol=1e-6):
    """Scale factor k if img is a similar copy of src (every pairwise distance times the same k), else None."""
    a, b = _pairwise(src), _pairwise(img)
    nz = a > 1e-12
    if _arr(src).shape != _arr(img).shape or not nz.any():
        return None
    k = float(np.median(b[nz] / a[nz]))
    return k if np.allclose(b, k * a, atol=tol * max(1.0, k)) else None


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


def cross2(u, v) -> float:
    """2-D cross product u x v (the z component). np.cross on 2-D vectors raises in numpy 2."""
    return float(u[0] * v[1] - u[1] * v[0])


_cross = cross2


def _pt(p) -> np.ndarray:
    """One point as a (2,) array. Accepts (x, y), a (2,) array or a (1, 2) array."""
    return np.asarray(p, float).reshape(2)


def _unit(u) -> np.ndarray:
    n = np.linalg.norm(u)
    if n < 1e-12:
        raise ValueError("zero-length direction")
    return u / n


def is_parallel(a, b, c, d, tol=1e-6) -> bool:
    """True if segment ab is parallel to segment cd. tol bounds the sine of the angle between them,
    so the test does not depend on the drawing's scale."""
    u, v = _pt(b) - _pt(a), _pt(d) - _pt(c)
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu < 1e-12 or nv < 1e-12:
        raise ValueError("is_parallel needs two segments of nonzero length")
    return abs(cross2(u, v)) <= tol * nu * nv


def collinear(*pts, tol=1e-6) -> bool:
    """True if all points lie on one line. tol is a fraction of the points' spread."""
    pts = np.array([_pt(p) for p in pts])
    if len(pts) < 3:
        return True
    d = np.linalg.norm(pts - pts[0], axis=1)
    far = pts[int(np.argmax(d))]
    span = float(d.max())
    if span < 1e-12:
        return True
    u = (far - pts[0]) / span
    off = np.abs([cross2(u, p - pts[0]) for p in pts])
    return bool(off.max() <= tol * span)


def on_ray(origin, through, p, tol=1e-6) -> bool:
    """True if p lies on the ray that starts at origin and passes through `through` (origin counts)."""
    o = _pt(origin)
    u, v = _pt(through) - o, _pt(p) - o
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu < 1e-12:
        raise ValueError("on_ray needs origin != through")
    if nv <= tol * nu:
        return True
    return abs(cross2(u, v)) <= tol * nu * nv and float(np.dot(u, v)) > 0


def foot(p, a, b) -> np.ndarray:
    """Foot of the perpendicular from p to line ab, as a (2,) array."""
    a, b, p = _pt(a), _pt(b), _pt(p)
    u = _unit(b - a)
    return a + np.dot(p - a, u) * u


def extend(a, b, box, ray=True) -> np.ndarray:
    """(2, 2) endpoints of line ab clipped to box = (x0, x1, y0, y1). ray=True starts at a and goes
    through b to the edge; ray=False draws the full line from edge to edge."""
    a, b = _pt(a), _pt(b)
    u = b - a
    if np.linalg.norm(u) < 1e-12:
        raise ValueError("extend needs a != b")
    x0, x1, y0, y1 = box
    lo, hi = -np.inf, np.inf
    for i, (m, n) in enumerate(((x0, x1), (y0, y1))):
        if abs(u[i]) < 1e-12:
            if not m - 1e-9 <= a[i] <= n + 1e-9:
                raise ValueError(f"line {a}->{b} misses box {box}")
            continue
        t1, t2 = sorted(((m - a[i]) / u[i], (n - a[i]) / u[i]))
        lo, hi = max(lo, t1), min(hi, t2)
    if ray:
        lo = max(lo, 0.0)
    if lo > hi + 1e-12:
        raise ValueError(f"{'ray' if ray else 'line'} {a}->{b} misses box {box}")
    return np.array([a + lo * u, a + hi * u])


def law_of_sines_side(known, opp_known, opp_want) -> float:
    """Side opposite the angle opp_want (degrees), given side `known` opposite the angle opp_known."""
    return float(known * np.sin(np.radians(opp_want)) / np.sin(np.radians(opp_known)))


def triangle_from_angles(base_a, base_b, angle_a, angle_b, above=True) -> np.ndarray:
    """(3, 2) triangle [A, B, C] on base AB with angle angle_a at A and angle_b at B (degrees).
    above=True puts C to the left of A->B (counterclockwise), False to the right."""
    A, B = _pt(base_a), _pt(base_b)
    if angle_a <= 0 or angle_b <= 0 or angle_a + angle_b >= 180:
        raise ValueError(f"angles {angle_a} and {angle_b} do not make a triangle")
    side = law_of_sines_side(dist(A, B), 180 - angle_a - angle_b, angle_b)
    C = A + side * rotate(_unit(B - A), angle_a if above else -angle_a)[0]
    tri = np.array([A, B, C])
    assert np.isclose(angle_deg(A, B, C), angle_a) and np.isclose(angle_deg(B, A, C), angle_b)
    return tri


def triangle_sas(a, b, angle_deg_at_a, side_len, above=True) -> np.ndarray:
    """(3, 2) triangle [A, B, C] with angle BAC = angle_deg_at_a and AC = side_len.
    above=True puts C to the left of A->B (counterclockwise)."""
    A, B = _pt(a), _pt(b)
    if not 0 < angle_deg_at_a < 180 or side_len <= 0:
        raise ValueError("triangle_sas needs 0 < angle < 180 and side_len > 0")
    C = A + side_len * rotate(_unit(B - A), angle_deg_at_a if above else -angle_deg_at_a)[0]
    return np.array([A, B, C])


# ---------------------------------------------------------------- asserts
def assert_dilation(center, src, img, k, tol=1e-6) -> None:
    """Check img is the dilation of src about center with scale factor k: each image point sits on the
    ray from center through its source point (the opposite ray if k < 0), at k times the distance,
    and (for 2+ points) every side is scaled by |k|."""
    c = _pt(center)
    src, img = _arr(src), _arr(img)
    assert src.shape == img.shape, f"src has {len(src)} points but img has {len(img)}"
    scale = max(1.0, float(np.abs(np.vstack([src, img]) - c).max()))
    for i, (p, q) in enumerate(zip(src, img)):
        dp, dq = dist(c, p), dist(c, q)
        if dp <= tol * scale:
            assert dq <= tol * scale, f"point {i}: source is the center {c} but the image {q} is not"
            continue
        through = p if k > 0 else 2 * c - p
        assert on_ray(c, through, q, tol), f"point {i}: image {q} is not on the ray from {c} through {through}"
        assert abs(dq - abs(k) * dp) <= tol * scale, (
            f"point {i}: center-to-image {dq:.4g} is not {abs(k):g} x center-to-source {dp:.4g} (ratio {dq / dp:.4g})")
    if len(src) > 1:
        r = similarity_ratio(src, img, tol)
        assert r is not None and np.isclose(r, abs(k), atol=tol), f"side ratio {r} is not {abs(k):g}"


def assert_lengths(pairs, tol=0.03) -> float:
    """pairs = [(a, b, label_length), ...]. Check the drawn lengths |ab| are proportional to the labels
    within tol (3%). The scale comes from the first pair, so labels may be in any unit. Returns the scale
    (drawing units per label unit)."""
    pairs = list(pairs)
    assert pairs, "assert_lengths needs at least one pair"
    a0, b0, L0 = pairs[0]
    assert L0 > 0, f"label length must be positive, got {L0}"
    scale = dist(a0, b0) / L0
    bad = []
    for i, (a, b, L) in enumerate(pairs[1:], 1):
        assert L > 0, f"pair {i}: label length must be positive, got {L}"
        r = dist(a, b) / (L * scale)
        if abs(r - 1) > tol:
            bad.append(f"pair {i}: label {L:g} is drawn as {dist(a, b) / scale:.3g} ({(r - 1) * 100:+.1f}%)")
    assert not bad, "drawn lengths don't match labels (scale from pair 0): " + "; ".join(bad)
    return scale


def assert_distinct(angles_deg, min_deg=4) -> None:
    """Check no two angles are within min_deg of each other, so angles meant to differ also look different."""
    a = sorted(float(x) for x in angles_deg)
    close = [(x, y) for x, y in zip(a, a[1:]) if y - x < min_deg]
    assert not close, f"angles closer than {min_deg} deg: " + ", ".join(f"{x:g} and {y:g}" for x, y in close)


def assert_similar(src, img, k=None, tol=1e-6) -> float:
    """Check img is similar to src (same vertex order) and, if k is given, that the scale factor is k.
    Returns the scale factor."""
    r = similarity_ratio(src, img, tol)
    assert r is not None, "img is not a similar copy of src (side ratios differ)"
    if k is not None:
        assert np.isclose(r, k, atol=tol * max(1.0, abs(k))), f"scale factor is {r:.6g}, not {k:g}"
    return r


# ---------------------------------------------------------------- marks
def mark_congruent(f, pairs, layer="given", size=0.12, r=0.35, gap=0.07) -> None:
    """Congruence marks. pairs is a list of groups; each group lists congruent parts.
    A segment group is ((a, b), (c, d), ...): every segment gets n ticks. An angle group is
    ((v, p1, p2), (v2, q1, q2), ...): every angle gets n arcs. n counts segment groups and angle groups
    separately (first segment group 1 tick, second 2, ...). size is the tick size; r is the arc radius,
    either one number or a list with one radius per angle group."""
    n_seg = n_ang = 0
    for group in pairs:
        group = list(group)
        kinds = {len(part) for part in group}
        assert kinds <= {2} or kinds <= {3}, f"mix of segments and angles in one group: {group}"
        if kinds <= {2}:
            n_seg += 1
            for a, b in group:
                f.ticks(a, b, n=n_seg, layer=layer, size=size)
        else:
            rad = r[n_ang] if isinstance(r, (list, tuple)) else r
            n_ang += 1
            for v, p1, p2 in group:
                f.arc(v, p1, p2, n=n_ang, r=rad, gap=gap, layer=layer)


def mark_parallel(f, segs, n=1, layer="given", size=0.13) -> None:
    """Parallel arrowheads (n chevrons) on each segment (a, b) in segs, pointing from a to b."""
    for a, b in segs:
        f.parallel_marks(a, b, n=n, layer=layer, size=size)


def _fit_height(pts, width_in, lo=1.2, hi=3.6, pad=0.6) -> float:
    """Canvas height that keeps the drawing's aspect ratio at width_in, plus room for labels."""
    dx, dy = np.ptp(_arr(pts), axis=0)
    return float(np.clip((width_in - pad) * dy / max(dx, 1e-9) + pad, lo, hi))


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
            sides = [((pts[i], pts[(i + 1) % n]),) for i in range(n)]
            angles = [((pts[i], pts[i - 1], pts[(i + 1) % n]),) for i in range(n)]
            mark_congruent(f, sides + angles, layer=mark_layer, size=0.07 * s, r=0.16 * s, gap=0.035 * s)
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
    mark_congruent(f, [((A, B), (C, D)), ((B, C), (D, A)),
                       ((B, A, C), (D, C, A)), ((A, B, C), (C, D, A)), ((A, D, C), (C, B, A))],
                   layer="answer", size=0.1 * s, r=[0.32 * s, 0.42 * s, 0.62 * s], gap=0.07 * s)
    dirs = vertex_directions(quad)
    for p, nm, d in zip((A, B, C), (nA, nB, nC), dirs):
        f.label(p, nm, direction=d)
    f.label(D, image_name, direction=dirs[3], layer="answer")
    # M sits on diagonal AC; put its label off the diagonal, on the D side, tilted toward C
    u = (C - A) / dist(A, C)
    nrm = (D - M) - np.dot(D - M, u) * u
    f.label(M, "M", direction=nrm / np.linalg.norm(nrm) + 0.35 * u, layer="answer")
    return f


def _primes(names) -> list[str]:
    return [nm + "'" for nm in _names(names)]


def reflection_build(tri, line_p1, line_p2, names="ABC", image_names=None, width_in=3.0, answer=True,
                     marks=True, line_name=None, height_in=None):
    """Polygon (given) and its reflection across line p1p2. The line is drawn across the figure (given).
    The image, primed labels, dashed connectors and matching side ticks go on the answer layer
    (answer=False draws them as given). Vertices on the line are their own image and are not relabeled;
    connectors that would pass through such a vertex are skipped.
    Returns (Figure, {image_pts, correspondence, line})."""
    from .core import Figure

    src = _arr(tri)
    names = _names(names)
    img_names = _names(image_names) if image_names is not None else _primes(names)
    p1, p2 = _pt(line_p1), _pt(line_p2)
    u = _unit(p2 - p1)
    img = reflect(src, p1, p2)
    assert is_rigid_image(src, img), "reflection is not rigid"
    for i, (p, q) in enumerate(zip(src, img)):
        m = midpoint(p, q)
        assert abs(cross2(u, m - p1)) <= 1e-9 * max(1.0, dist(p1, m)), f"vertex {names[i]}: midpoint off the line"
        assert abs(np.dot(q - p, u)) <= 1e-9 * max(1.0, dist(p, q)), f"vertex {names[i]}: PP' not perpendicular"
    if abs(signed_area(src)) > 1e-9:
        assert needs_reflection(src, img), "image orientation did not flip"
    fixed = [dist(p, q) < 1e-9 for p, q in zip(src, img)]
    pts = np.vstack([src, img])
    lo, hi = pts.min(0), pts.max(0)
    pad = 0.12 * float(max(hi - lo))
    ends = extend(p1, p2, (lo[0] - pad, hi[0] + pad, lo[1] - pad, hi[1] + pad), ray=False)
    f = Figure(width_in, height_in or _fit_height(np.vstack([pts, ends]), width_in))
    lay = "answer" if answer else "given"
    f.seg(ends[0], ends[1])
    if line_name:
        f.label(ends[1], line_name, direction=u)
    f.poly(src)
    f.dots(src)
    f.label_poly(src, names)
    f.poly(img, layer=lay)
    moving = [i for i in range(len(src)) if not fixed[i]]
    f.dots(img[moving], layer=lay)
    f.label_poly(img, [None if fixed[i] else img_names[i] for i in range(len(src))], layer=lay)
    if answer:
        on_line = [src[j] for j in range(len(src)) if fixed[j]]
        for i in moving:
            # a connector through a vertex on the line would trace over the sides there
            if not any(collinear(src[i], img[i], v) for v in on_line):
                f.seg(src[i], img[i], layer="answer", dashed=True, lw=0.8)
    if marks:
        n = len(src)
        groups = [((src[i], src[(i + 1) % n]), (img[i], img[(i + 1) % n])) for i in range(n)
                  if not (fixed[i] and fixed[(i + 1) % n])]
        mark_congruent(f, groups, layer=lay, size=0.08 * _mark_scale(src))
    return f, {"image_pts": img, "correspondence": correspondence(names, img_names), "line": ends}


def dilation_task(pts, k, center, names="ABC", grid=None, rays=True, width_in=3.0, height_in=None,
                  center_name="P", center_dir=None, overrides=None, ray_past=0.0, lattice=None):
    """Dilation item: original points/polygon and center (given); dashed guide rays, the image and primed
    labels (answer). grid = (x0, x1, y0, y1) draws a light grid and checks everything fits on it; with a
    grid the image must land on grid points unless lattice=False. Rays run from the center to the farther
    of each point and its image, plus ray_past units. overrides = {name: label direction}, also used
    for the primed name. Returns (Figure, {image_pts, k, center})."""
    from .core import Figure

    src, c = _arr(pts), _pt(center)
    img = dilate(src, k, c)
    assert_dilation(c, src, img, k)
    names = _names(names)
    overrides = overrides or {}
    allpts = np.vstack([src, img, [c]])
    frame = allpts
    if grid is not None:
        x0, x1, y0, y1 = grid
        assert (allpts[:, 0].min() >= x0 - 1e-9 and allpts[:, 0].max() <= x1 + 1e-9
                and allpts[:, 1].min() >= y0 - 1e-9 and allpts[:, 1].max() <= y1 + 1e-9), \
            f"points or image fall outside grid {grid}"
        if lattice is None or lattice:
            assert np.allclose(img, np.round(img)), "image vertices must land on grid points"
        frame = P((x0, y0), (x1, y1))
    f = Figure(width_in, height_in or _fit_height(frame, width_in, pad=0.3 if grid is not None else 0.6))
    if grid is not None:
        f.grid(*grid, lw=0.25)
    closed = len(src) > 2
    f.poly(src, closed=closed)
    f.dots(np.vstack([src, [c]]))
    f.label(c, center_name, direction=center_dir if center_dir is not None else c - src.mean(0))
    primes = _primes(names)
    if closed:
        f.label_poly(src, names, overrides=overrides)
    else:
        for p, nm in zip(src, names):
            f.label(p, nm, direction=overrides.get(nm, p - c))
    if rays:
        for p, q in zip(src, img):
            if k < 0:
                f.seg(p, q, layer="answer", dashed=True, lw=0.8)
                continue
            far = q if k >= 1 else p
            if dist(c, far) > 1e-9:
                f.seg(c, far + ray_past * _unit(far - c), layer="answer", dashed=True, lw=0.8)
    f.poly(img, closed=closed, layer="answer")
    f.dots(img, layer="answer")
    pover = {nm + "'": d for nm, d in overrides.items()}
    if closed:
        f.label_poly(img, primes, layer="answer", overrides=pover)
    else:
        for q, nm in zip(img, primes):
            f.label(q, nm, layer="answer", direction=pover.get(nm, q - c))
    return f, {"image_pts": img, "k": k, "center": c}


def side_splitter(tri, t, names="ABC", split_names="DE", width_in=3.0, height_in=None, seg_labels=None,
                  marks=False):
    """Triangle ABC with D on AB and E on AC at fraction t from A (AD = t AB), so DE is parallel to BC.
    seg_labels = (AD, DB, AE, EC) side texts (None skips one). marks=True adds parallel arrows on DE and BC
    (given). Returns (Figure, {split_pts, t, k}) where k = AB/AD."""
    from .core import Figure

    T = _arr(tri)
    assert T.shape == (3, 2), "side_splitter needs a triangle"
    assert 0 < t < 1, f"t must be between 0 and 1, got {t}"
    A, B, C = T
    D, E = A + t * (B - A), A + t * (C - A)
    assert is_parallel(D, E, B, C), "DE is not parallel to BC"
    assert np.isclose(dist(A, D) / dist(D, B), dist(A, E) / dist(E, C)), "AD/DB != AE/EC"
    assert_similar([A, D, E], [A, B, C], 1 / t)
    f = Figure(width_in, height_in or _fit_height(T, width_in))
    f.poly(T)
    f.seg(D, E)
    f.dots(np.vstack([T, [D, E]]))
    f.label_poly(T, _names(names))
    ctr = T.mean(0)
    for p, q, nm in ((D, B, split_names[0]), (E, C, split_names[1])):
        v = q - A
        out = np.array([-v[1], v[0]])
        f.label(p, nm, direction=out if np.dot(out, p - ctr) > 0 else -out)
    if seg_labels:
        for (p, q), s in zip(((A, D), (D, B), (A, E), (E, C)), seg_labels):
            if s is not None:
                f.side_label(p, q, s, ctr)
    if marks:
        mark_parallel(f, [(D, E), (B, C)], size=0.06 * dist(B, C))
    return f, {"split_pts": np.array([D, E]), "t": t, "k": 1 / t}


def rect_pair(w, h, k, names=("M", "N"), labels=None, gap=None, width_in=3.0, height_in=None):
    """Rectangle w x h and its copy scaled by k, side by side on one baseline, names centered inside.
    labels = (w1, h1, w2, h2) side texts, bottom and left of each (None skips one; default: the lengths).
    Returns (Figure, {rects, k})."""
    from .core import Figure

    gap = 0.6 * min(w, k * w) if gap is None else gap
    a = P((0, 0), (w, 0), (w, h), (0, h))
    b = translate(dilate(a, k), (w + gap, 0))
    assert_similar(a, b, k)
    if labels is None:
        labels = (f"{w:g}", f"{h:g}", f"{k * w:g}", f"{k * h:g}")
    f = Figure(width_in, height_in or _fit_height(np.vstack([a, b]), width_in, lo=1.0))
    for r, nm, (wl, hl) in ((a, names[0], labels[:2]), (b, names[1], labels[2:])):
        f.poly(r)
        c = r.mean(0)
        if nm:
            f.text(c, f"${nm}$")
        if wl is not None:
            f.side_label(r[0], r[1], wl, c)
        if hl is not None:
            f.side_label(r[0], r[3], hl, c)
    return f, {"rects": (a, b), "k": k}


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
    "P", "rotate", "reflect", "translate", "dilate", "fit_rigid", "is_rigid_image", "similarity_ratio",
    "orientation", "signed_area", "needs_reflection", "correspondence", "congruence_statement", "ssa_triangles",
    "midpoint", "dist", "angle_deg", "vertex_directions", "congruent_pair", "rotation_build",
    "cross2", "is_parallel", "collinear", "on_ray", "foot", "extend", "law_of_sines_side", "triangle_from_angles",
    "triangle_sas", "assert_dilation", "assert_lengths", "assert_distinct", "assert_similar", "mark_congruent",
    "mark_parallel", "reflection_build", "dilation_task", "side_splitter", "rect_pair",
]

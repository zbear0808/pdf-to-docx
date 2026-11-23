"""3.3-3.5 Progress Check A figures. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, assert_lengths, dilate, dist, figure, similarity_ratio

S = "3.3-3.5 Progress Check A"


def _parallel(a, b, c, d, tol=1e-9) -> bool:
    u, v = np.asarray(b, float) - a, np.asarray(d, float) - c
    return abs(u[0] * v[1] - u[1] * v[0]) < tol * max(1.0, np.linalg.norm(u) * np.linalg.norm(v))


def _grid(f: Figure, x1, y1, lw=0.35):
    for x in range(x1 + 1):
        f.seg((x, 0), (x, y1), lw=lw)
    for y in range(y1 + 1):
        f.seg((0, y), (x1, y), lw=lw)


def _dilate_task(f, tri, names, center, cname, k, cdir):
    img = dilate(tri, k, center)
    f.poly(tri, lw=1.4)
    f.dots(list(tri) + [center], size=16)
    f.label_poly(tri, names, offset_pt=8)
    f.label(center, cname, direction=cdir, offset_pt=8)
    for p in tri:
        u = (p - center) / dist(center, p)
        f.seg(center, p + 0.4 * u, layer="answer", dashed=True, lw=0.8)
    f.poly(img, layer="answer", lw=1.4)
    f.dots(img, layer="answer", size=16)
    c = img.mean(0)
    for p, nm in zip(img, names):
        u, out = (p - center) / dist(center, p), p - c
        side = out - np.dot(out, u) * u   # away from the triangle, across the ray (not along it)
        f.label(p, nm + "'", layer="answer", direction=side + 0.25 * out, offset_pt=10)
    return img


def _rects(f, small, big, names, labels, gap=2.0):
    """Two rectangles (w, h) side by side; labels = (h_small, w_small, h_big, w_big)."""
    (w1, h1), (w2, h2) = small, big
    a = P((0, 0), (w1, 0), (w1, h1), (0, h1))
    b = P((w1 + gap, 0), (w1 + gap + w2, 0), (w1 + gap + w2, h2), (w1 + gap, h2))
    for r, nm, (hl, wl) in ((a, names[0], labels[:2]), (b, names[1], labels[2:])):
        f.poly(r)
        c = r.mean(0)
        f.label(c, nm, direction=(0, 1), offset_pt=0)
        f.side_label(r[0], r[3], hl, c, italic=hl.isalpha())
        f.side_label(r[0], r[1], wl, c, italic=wl.isalpha())


def _split(f, V, W, X, t_vw, t_xw, labels, angle_text, names):
    """Triangle V (angle vertex), W (shared center), X. V2 on VW, X2 on XW, both at fraction t from W."""
    V2, X2 = W + t_vw * (V - W), W + t_xw * (X - W)
    f.poly([V, W, X])
    f.seg(V2, X2)
    f.dots([V, W, X, V2, X2])
    c = (V + W + X) / 3
    for p, nm in zip((V, W, X), names[:3]):
        f.label(p, nm, direction=p - c, offset_pt=9)
    for p, q, nm in ((V2, V, names[3]), (X2, X, names[4])):
        u = (q - W) / dist(q, W)
        out = np.array([-u[1], u[0]])
        out = out if np.dot(out, p - c) > 0 else -out
        f.label(p, nm, direction=out, offset_pt=11)
    for (p, q), s in zip(((V, V2), (V2, W), (W, X2), (X2, X)), labels):
        f.side_label(p, q, s, c, offset_pt=9)
    span = max(dist(V, W), dist(V, X))
    f.arc(V, W, X, r=0.1 * span)
    f.angle_label(V, W, X, angle_text, dist=0.22 * span)
    return V2, X2


def _lines(f, lines, spots, sides):
    for name, (a, b) in lines.items():
        a, b = np.asarray(a, float), np.asarray(b, float)
        f.seg(a, b)
        f.label(a + spots[name] * (b - a), name, direction=sides[name], offset_pt=9)


# Item 1: triangle ABC, center P, scale factor 1/2, on a grid
D_P = np.array((0, 2), float)
D_TRI = P((6, 6), (10, 4), (8, 0))
D_IMG = dilate(D_TRI, 0.5, D_P)
assert np.allclose(D_IMG, [(3, 4), (5, 3), (4, 1)])
assert abs(similarity_ratio(D_TRI, D_IMG) - 0.5) < 1e-9


@figure(f"{S}_dilate")
def dilate_fig() -> Figure:
    f = Figure(width_in=3.0, height_in=1.9)
    _grid(f, 10, 6)
    _dilate_task(f, D_TRI, "ABC", D_P, "P", 0.5, (-1, 0.3))
    return f


# Item 3: polygon N is a dilation of polygon M, k = 3/2 (8 -> 12, x = 12 -> y = 18)
R_SMALL, R_BIG = (12, 8), (18, 12)
assert R_BIG[0] / R_SMALL[0] == R_BIG[1] / R_SMALL[1] == 1.5
assert_lengths([((0, 0), (0, 8), 8), ((0, 0), (12, 0), 12), ((0, 0), (0, 12), 12), ((0, 0), (18, 0), 18)])


@figure(f"{S}_rects")
def rects() -> Figure:
    f = Figure(width_in=2.8, height_in=1.3)
    _rects(f, R_SMALL, R_BIG, ("M", "N"), ("8", "x", "12", "y"), gap=6)
    return f


# Item 4: angle at R = 45 deg, RR' = 4, R'S = 8, SQ' = 6, Q'Q = 3 (both 2/3 of the way from S).
# Letters and a top-to-bottom flip (directions 15 and 60 deg) keep it from looking like Lesson 3.5 practice 1.
T_R = np.array((0, 0), float)
u_rs, u_rq = (np.array([np.cos(np.radians(a)), np.sin(np.radians(a))]) for a in (15, 60))
T_S = 12 * u_rs
_b = -2 * np.dot(u_rq, T_S)
_t = (-_b + np.sqrt(_b * _b - 4 * (144 - 81))) / 2
T_Q = _t * u_rq
assert abs(dist(T_S, T_Q) - 9) < 1e-9 and abs(angle_deg(T_R, T_Q, T_S) - 45) < 1e-9


@figure(f"{S}_angle")
def angle_fig() -> Figure:
    f = Figure(width_in=2.3, height_in=2.1)
    R2, Q2 = _split(f, T_R, T_S, T_Q, 8 / 12, 6 / 9, ("4", "8", "6", "3"), r"$45^\circ$",
                    ("R", "S", "Q", "R'", "Q'"))
    assert _parallel(R2, Q2, T_R, T_Q)
    assert abs(angle_deg(R2, Q2, T_S) - 45) < 1e-9
    assert_lengths([(T_R, R2, 4), (R2, T_S, 8), (T_S, Q2, 6), (Q2, T_Q, 3)])
    return f


def _deg(a, b) -> float:
    """Direction of segment ab in degrees."""
    d = np.asarray(b, float) - np.asarray(a, float)
    return float(np.degrees(np.arctan2(d[1], d[0])))


# Item 5: image of line t. v and z are parallel to t (steep, slope 2.5); u and w are not.
# Not Lesson 3.4 practice 2 (l, m, n, o, p; parallels at 45 deg) or practice 3 (f, g).
LINES = {
    "t": ((0.5, 0), (2.26, 4.4)),
    "u": ((0, 2.4), (5.4, 0.2)),
    "v": ((2.0, 0), (3.76, 4.4)),
    "w": ((0, 3.2), (5.4, 3.848)),
    "z": ((3.5, 0), (5.26, 4.4)),
}
for _nm in ("v", "z"):
    assert _parallel(*np.array(LINES["t"], float), *np.array(LINES[_nm], float))
for _nm in ("u", "w"):
    assert not _parallel(*np.array(LINES["t"], float), *np.array(LINES[_nm], float), tol=1e-2)
    _gap = abs(_deg(*LINES[_nm]) - _deg(*LINES["t"])) % 180
    assert min(_gap, 180 - _gap) >= 40   # crossing lines sit well off the parallels


@figure(f"{S}_lines")
def lines_fig() -> Figure:
    f = Figure(width_in=2.2, height_in=1.7)
    _lines(f, LINES, {"t": 0.97, "u": 0.97, "v": 0.97, "w": 0.03, "z": 0.97},
           {"t": (0, 1), "u": (1, 0), "v": (0, 1), "w": (-1, 0), "z": (0, 1)})
    return f

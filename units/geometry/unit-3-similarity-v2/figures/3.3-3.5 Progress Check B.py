"""3.3-3.5 Progress Check B figures. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, assert_lengths, dilate, dist, figure, similarity_ratio

S = "3.3-3.5 Progress Check B"


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


def _split(f, V, W, X, t_vw, t_xw, labels, angle_text, names, arc_r=0.1, label_d=0.22):
    """Triangle V (angle vertex), W (shared center), X. V2 on VW, X2 on XW, both at fraction t from W.
    arc_r and label_d (fractions of the longer side at V) place the angle mark and its label."""
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
    f.arc(V, W, X, r=arc_r * span)
    f.angle_label(V, W, X, angle_text, dist=label_d * span)
    return V2, X2


def _lines(f, lines, spots, sides):
    for name, (a, b) in lines.items():
        a, b = np.asarray(a, float), np.asarray(b, float)
        f.seg(a, b)
        f.label(a + spots[name] * (b - a), name, direction=sides[name], offset_pt=9)


# Item 1: triangle DEF, center Q, scale factor 1/2, on a grid
D_Q = np.array((12, 5), float)
D_TRI = P((0, 7), (6, 1), (0, 3))
D_IMG = dilate(D_TRI, 0.5, D_Q)
assert np.allclose(D_IMG, [(6, 6), (9, 3), (6, 4)])
assert abs(similarity_ratio(D_TRI, D_IMG) - 0.5) < 1e-9


@figure(f"{S}_dilate")
def dilate_fig() -> Figure:
    f = Figure(width_in=3.2, height_in=2.0)
    _grid(f, 12, 7)
    _dilate_task(f, D_TRI, "DEF", D_Q, "Q", 0.5, (1, 0.3))
    return f


# Item 3: polygon S is a dilation of polygon R, k = 3/2 (6 -> 9, x = 10 -> y = 15). S is drawn on the left
R_R, R_S = (10, 6), (15, 9)
assert R_S[0] / R_R[0] == R_S[1] / R_R[1] == 1.5
assert_lengths([((0, 0), (0, 9), 9), ((0, 0), (15, 0), 15), ((0, 0), (0, 6), 6), ((0, 0), (10, 0), 10)])


@figure(f"{S}_rects")
def rects() -> Figure:
    f = Figure(width_in=2.8, height_in=1.3)
    _rects(f, R_S, R_R, ("S", "R"), ("9", "y", "6", "x"), gap=6)
    return f


# Item 4: angle at E = 50 deg, EE' = 6, E'F = 12, FD' = 10, D'D = 5 (both 2/3 of the way from F).
# Two different fractions (12/18, 10/15), as on A (8/12, 6/9), so checking them takes the same work.
T_E = np.array((0, 0), float)
u_ef, u_ed = (np.array([np.cos(np.radians(a)), np.sin(np.radians(a))]) for a in (195, 245))
T_F = 18 * u_ef
_b = -2 * np.dot(u_ed, T_F)
_t = (-_b + np.sqrt(_b * _b - 4 * (324 - 225))) / 2
T_D = _t * u_ed
assert abs(dist(T_F, T_D) - 15) < 1e-9 and abs(angle_deg(T_E, T_D, T_F) - 50) < 1e-9
assert 55 < angle_deg(T_F, T_E, T_D) < 75 and 55 < angle_deg(T_D, T_E, T_F) < 75   # no near-right angle


@figure(f"{S}_angle")
def angle_fig() -> Figure:
    f = Figure(width_in=2.3, height_in=2.1)
    E2, D2 = _split(f, T_E, T_F, T_D, 12 / 18, 10 / 15, ("6", "12", "10", "5"), r"$50^\circ$",
                    ("E", "F", "D", "E'", "D'"), arc_r=0.12, label_d=0.2)
    assert _parallel(E2, D2, T_E, T_D)
    assert abs(angle_deg(E2, D2, T_F) - 50) < 1e-9
    assert_lengths([(T_E, E2, 6), (E2, T_F, 12), (T_F, D2, 10), (D2, T_D, 5)])
    return f


# Item 5: image of line n. j and m are parallel to n; k and l are not
LINES = {
    "j": ((0, 2.4), (3.0, 0)),
    "k": ((3.4, 0), (4.4, 4.4)),
    r"\ell": ((0, 0.8), (5.4, 2.6)),
    "m": ((1.5, 4.4), (5.5, 1.2)),
    "n": ((0, 4.0), (4.5, 0.4)),
}
for _nm in ("j", "m"):
    assert _parallel(*np.array(LINES["n"], float), *np.array(LINES[_nm], float))
for _nm in ("k", r"\ell"):
    assert not _parallel(*np.array(LINES["n"], float), *np.array(LINES[_nm], float), tol=1e-2)


@figure(f"{S}_lines")
def lines_fig() -> Figure:
    f = Figure(width_in=2.2, height_in=1.7)
    _lines(f, LINES, {"j": 0.03, "k": 0.97, r"\ell": 0.97, "m": 0.97, "n": 0.03},
           {"j": (-1, 0), "k": (1, 0), r"\ell": (1, 0), "m": (1, 0), "n": (-1, 0)})
    return f

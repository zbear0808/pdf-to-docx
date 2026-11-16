"""3.3-3.5 Progress Check Retake figures. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, assert_lengths, dilate, dist, figure, similarity_ratio

S = "3.3-3.5 Progress Check Retake"


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


# Item 1: triangle RST, center O in the lower right, scale factor 1/2, on a grid
D_O = np.array((10, 0), float)
D_TRI = P((4, 6), (8, 6), (4, 2))
D_IMG = dilate(D_TRI, 0.5, D_O)
assert np.allclose(D_IMG, [(7, 3), (9, 3), (7, 1)])
assert abs(similarity_ratio(D_TRI, D_IMG) - 0.5) < 1e-9


@figure(f"{S}_dilate")
def dilate_fig() -> Figure:
    f = Figure(width_in=3.0, height_in=2.1)
    _grid(f, 10, 7)
    _dilate_task(f, D_TRI, "RST", D_O, "O", 0.5, (1, -0.3))
    return f


# Item 3: polygon V is a dilation of polygon U, k = 5/2 (8 -> 20); x = 25 on V, so y = 10 on U
R_M, R_N = (10, 8), (25, 20)
assert R_N[0] / R_M[0] == R_N[1] / R_M[1] == 2.5
assert_lengths([((0, 0), (0, 8), 8), ((0, 0), (10, 0), 10), ((0, 0), (0, 20), 20), ((0, 0), (25, 0), 25)])


@figure(f"{S}_rects")
def rects() -> Figure:
    f = Figure(width_in=2.8, height_in=1.5)
    _rects(f, R_M, R_N, ("U", "V"), ("8", "y", "20", "x"), gap=8)
    return f


# Item 4: KM' = 6, M'M = 2, KL' = 9, L'L = 3, ML = 16. Both cuts are 3/4 of the way from K, so L'M' = 12
T_M, T_L = P((0, 0), (16, 0))
_kx = (64 - 144 + 256) / 32
T_K = np.array((_kx, np.sqrt(64 - _kx ** 2)))
assert abs(dist(T_K, T_M) - 8) < 1e-9 and abs(dist(T_K, T_L) - 12) < 1e-9
T_M2, T_L2 = T_K + 6 / 8 * (T_M - T_K), T_K + 9 / 12 * (T_L - T_K)
assert _parallel(T_M2, T_L2, T_M, T_L) and abs(dist(T_M2, T_L2) - 12) < 1e-9
assert_lengths([(T_K, T_M2, 6), (T_M2, T_M, 2), (T_K, T_L2, 9), (T_L2, T_L, 3), (T_M, T_L, 16), (T_M2, T_L2, 12)])


def _out(p, a, b, c):
    """Unit normal to side ab at p, pointing away from point c."""
    u = (b - a) / dist(a, b)
    n = np.array([-u[1], u[0]])
    return n if np.dot(n, p - c) > 0 else -n


@figure(f"{S}_split")
def split_fig() -> Figure:
    f = Figure(width_in=3.3, height_in=1.7)
    f.poly([T_K, T_L, T_M])
    f.seg(T_M2, T_L2)
    f.dots([T_K, T_L, T_M, T_M2, T_L2])
    c = (T_K + T_L + T_M) / 3
    f.label(T_K, "K", direction=(0, 1))
    f.label(T_L, "L", direction=(1, -0.3))
    f.label(T_M, "M", direction=(-1, -0.3))
    f.label(T_M2, "M'", direction=_out(T_M2, T_K, T_M, c) + (0, 0.6), offset_pt=12)
    f.label(T_L2, "L'", direction=_out(T_L2, T_K, T_L, c) + (0, 0.6), offset_pt=12)
    for (p, q), s in zip(((T_K, T_M2), (T_M2, T_M), (T_K, T_L2), (T_L2, T_L), (T_M, T_L)),
                         ("6", "2", "9", "3", "16")):
        f.side_label(p, q, s, c, offset_pt=9)
    f.side_label(T_M2, T_L2, "12", T_K, layer="answer", offset_pt=8)
    return f


# Item 5: image of line c. b and e are parallel to c; a and d are not
LINES = {
    "a": ((1.4, 4.6), (2.6, 0)),
    "c": ((0, 1.0), (5.0, 4.0)),
    "d": ((0, 4.2), (5.4, 1.5)),
    "b": ((0, 2.8), (3.0, 4.6)),
    "e": ((1.0, 0), (5.4, 2.64)),
}
for _nm in ("b", "e"):
    assert _parallel(*np.array(LINES["c"], float), *np.array(LINES[_nm], float))
for _nm in ("a", "d"):
    assert not _parallel(*np.array(LINES["c"], float), *np.array(LINES[_nm], float), tol=1e-2)


@figure(f"{S}_lines")
def lines_fig() -> Figure:
    f = Figure(width_in=2.2, height_in=1.8)
    _lines(f, LINES, {"a": 0.03, "c": 0.97, "d": 0.97, "b": 0.97, "e": 0.97},
           {"a": (-1, 0), "c": (0.3, 1), "d": (1, 0), "b": (0.3, 1), "e": (1, 0)})
    return f


# Item 6: triangle ABC dilated with scale factor 3 (center not shown) onto triangle DEF
Z_O = np.array((-1.0, -1.4), float)
Z_ABC = P((0, 1.2), (0, 0), (1.0, 0))
Z_DEF = dilate(Z_ABC, 3, Z_O)
assert abs(similarity_ratio(Z_ABC, Z_DEF) - 3) < 1e-9
assert _parallel(Z_ABC[0], Z_ABC[1], Z_DEF[0], Z_DEF[1])
assert abs(angle_deg(Z_ABC[0], Z_ABC[1], Z_ABC[2]) - angle_deg(Z_DEF[0], Z_DEF[1], Z_DEF[2])) < 1e-9


@figure(f"{S}_k3")
def k3_fig() -> Figure:
    f = Figure(width_in=1.9, height_in=2.2)
    for tri, names, sz in ((Z_ABC, "ABC", 0.12), (Z_DEF, "DEF", 0.3)):
        f.poly(tri)
        f.right_angle(tri[1], tri[0], tri[2], size=sz)
        f.label_poly(tri, names, offset_pt=8)
    return f

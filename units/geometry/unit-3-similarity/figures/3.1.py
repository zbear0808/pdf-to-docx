"""Lesson 3.1 figures: dilations on a grid. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (Figure, P, assert_lengths, assert_similar, dilate, dist, figure,
                                    similarity_ratio)


def _grid(f: Figure, x0, x1, y0, y1):
    for x in range(x0, x1 + 1):
        f.seg((x, y0), (x, y1), lw=0.25)
    for y in range(y0, y1 + 1):
        f.seg((x0, y), (x1, y), lw=0.25)


def _on_ray(c, p, q, tol=1e-9) -> bool:
    """q lies on ray c->p."""
    u, v = np.asarray(p) - np.asarray(c), np.asarray(q) - np.asarray(c)
    return abs(u[0] * v[1] - u[1] * v[0]) < tol and float(np.dot(u, v)) > 0


def _check(center, pts, img, k):
    assert np.allclose(img, dilate(pts, k, center))
    for p, q in zip(pts, img):
        assert _on_ray(center, p, q)
        assert np.isclose(dist(center, q), k * dist(center, p))
    if len(pts) > 1:
        assert np.isclose(similarity_ratio(pts, img), k)


def _rays(f: Figure, center, img_or_pts):
    """Dashed red guide rays from the center to the farther of each point pair."""
    for q in img_or_pts:
        f.seg(center, q, layer="answer", dashed=True, lw=0.8)


# Together 1: center C, point H, k = 3
T1_C, T1_H = P(0, 0), P(2, 1)
T1_H2 = dilate([T1_H], 3, T1_C)[0]
_check(T1_C, [T1_H], [T1_H2], 3)
assert np.allclose(T1_H2, (6, 3))


@figure("3.1_t1")
def t1() -> Figure:
    f = Figure(width_in=2.5, height_in=1.6)
    _grid(f, 0, 7, -1, 4)
    f.dots([T1_C, T1_H])
    f.label(T1_C, "C", direction=(-1, -0.6))
    f.label(T1_H, "H", direction=(-0.3, 1))
    _rays(f, T1_C, [T1_H2])
    f.dots([T1_H2], layer="answer")
    f.label(T1_H2, "H′", layer="answer", direction=(0.3, 1))
    return f


# Together 2: center O, point K, k = 3/4
T2_O, T2_K = P(0, 0), P(4, 4)
T2_K2 = dilate([T2_K], 0.75, T2_O)[0]
_check(T2_O, [T2_K], [T2_K2], 0.75)
assert np.allclose(T2_K2, (3, 3))


@figure("3.1_t2")
def t2() -> Figure:
    f = Figure(width_in=1.7, height_in=1.7)
    _grid(f, -1, 5, -1, 5)
    f.dots([T2_O, T2_K])
    f.label(T2_O, "O", direction=(-1, -0.6))
    f.label(T2_K, "K", direction=(0.6, 1))
    _rays(f, T2_O, [T2_K])
    f.dots([T2_K2], layer="answer")
    f.label(T2_K2, "K′", layer="answer", direction=(1, -0.6))
    return f


def _poly_dilation(center, pts, names, k, grid, size, cname="P", cdir=(-1, -0.6), overrides=None):
    img = dilate(pts, k, center)
    _check(center, pts, img, k)
    f = Figure(width_in=size[0], height_in=size[1])
    _grid(f, *grid)
    closed = len(pts) > 2
    f.poly(pts, closed=closed)
    f.dots(np.vstack([pts, [center]]))
    f.label(center, cname, direction=cdir)
    f.label_poly(pts, names, overrides=overrides) if closed else [
        f.label(p, n, direction=(overrides or {}).get(n, (0.6, 0.8))) for p, n in zip(pts, names)]
    far = [q if k > 1 else p for p, q in zip(pts, img)]
    _rays(f, center, far)
    f.poly(img, closed=closed, layer="answer")
    f.dots(img, layer="answer")
    primes = [n + "′" for n in names]
    if closed:
        f.label_poly(img, primes, layer="answer", overrides={n + "′": d for n, d in (overrides or {}).items()})
    else:
        for q, n, d in zip(img, primes, [(0.7, -1), (-1, 0.3)]):
            f.label(q, n, layer="answer", direction=d)
    return f, img


# Problem 3: triangle ABC, center P, k = 2
P3_P = P(1, 1)
P3_PTS = P((2, 3), (4, 2), (3, 4))
assert np.allclose(dilate(P3_PTS, 2, P3_P), [(3, 5), (7, 3), (5, 7)])


@figure("3.1_p3")
def p3() -> Figure:
    return _poly_dilation(P3_P, P3_PTS, "ABC", 2, (0, 8, 0, 8), (2.4, 2.4), overrides={"C": (1, 0.2), "A": (-1, 0.2)})[0]


# Problem 4: quadrilateral DEFG, center P, k = 1/2
P4_P = P(0, 0)
P4_PTS = P((6, 4), (8, 4), (8, 8), (4, 8))
assert np.allclose(dilate(P4_PTS, 0.5, P4_P), [(3, 2), (4, 2), (4, 4), (2, 4)])


@figure("3.1_p4")
def p4() -> Figure:
    return _poly_dilation(P4_P, P4_PTS, "DEFG", 0.5, (0, 9, 0, 9), (2.5, 2.5), overrides={"D": (0.4, -1)})[0]


# Exit ticket: segment ST, center P, k = 1/3
EX_P = P(0, 0)
EX_PTS = P((6, 3), (3, 6))
assert np.allclose(dilate(EX_PTS, 1 / 3, EX_P), [(2, 1), (1, 2)])


@figure("3.1_exit")
def exit_fig() -> Figure:
    return _poly_dilation(EX_P, EX_PTS, "ST", 1 / 3, (0, 7, 0, 7), (2.0, 2.0),
                          overrides={"S": (1, 0.3), "T": (0.3, 1)})[0]


# Practice 1: triangle JKL, center J (a vertex), k = 2
PR_J = P(1, 1)
PR_PTS = P((1, 1), (3, 1), (1, 3))
assert np.allclose(dilate(PR_PTS, 2, PR_J), [(1, 1), (5, 1), (1, 5)])


@figure("3.1_prac1")
def prac1() -> Figure:
    img = dilate(PR_PTS, 2, PR_J)
    _check(PR_J, PR_PTS[1:], img[1:], 2)
    f = Figure(width_in=1.9, height_in=1.9)
    _grid(f, 0, 6, 0, 6)
    f.poly(PR_PTS)
    f.dots(PR_PTS)
    f.label_poly(PR_PTS, "JKL")
    f.poly(img, layer="answer")
    f.dots(img[1:], layer="answer")
    f.label(img[0], "J′", layer="answer", direction=(0.8, -1))
    f.label(img[1], "K′", layer="answer", direction=(0.6, -1))
    f.label(img[2], "L′", layer="answer", direction=(-1, 0.4))
    return f


# Practice 2: Polygon Q is a 3/4 scaled copy of Polygon P (top 4 -> 3, x = 6 -> y = 4.5)
PP_TR = P(4, 6)
PP_BR = PP_TR + np.array([0.9, -np.sqrt(36 - 0.81)])
PP = np.array([(0, 6), PP_TR, PP_BR, (-1, 1)], float)
PQ = dilate(PP, 0.75) + np.array([8.0, 1.2])
assert_similar(PP, PQ, 0.75)
assert_lengths([(PP[0], PP[1], 4), (PP[1], PP[2], 6), (PQ[0], PQ[1], 3), (PQ[1], PQ[2], 4.5)])


@figure("3.1_prac2")
def prac2() -> Figure:
    f = Figure(width_in=2.3, height_in=1.2)
    for pts, name, top, side in ((PP, "P", "4", "x"), (PQ, "Q", "3", "y")):
        c = pts.mean(axis=0)
        f.poly(pts)
        f.text(c, f"${name}$")
        f.side_label(pts[0], pts[1], top, c)
        f.side_label(pts[1], pts[2], side, c, italic=True)
    return f


# Practice 3: Figure f is a 2/3 scaled copy of Figure e (AB 6 -> XY 4, CD 3 -> ZW a = 2)
OV_E = {"A": P(-3, 0), "B": P(3, 0), "C": P(0, 0), "D": P(0, 3)}
OV_EC, OV_EAX = P(0, 0.5), (4.2, 2.5)
OV_T = np.array([8.6, 1.4])
OV_F = {n: dilate([p], 2 / 3)[0] + OV_T for n, p in zip("XYWZ", OV_E.values())}
OV_FC, OV_FAX = dilate([OV_EC], 2 / 3)[0] + OV_T, tuple(2 / 3 * a for a in OV_EAX)
assert np.isclose(((OV_E["D"] - OV_EC)[1] / OV_EAX[1]) ** 2, 1)
assert_lengths([(OV_E["A"], OV_E["B"], 6), (OV_E["C"], OV_E["D"], 3), (OV_F["X"], OV_F["Y"], 4),
                (OV_F["W"], OV_F["Z"], 2)])


@figure("3.1_prac3")
def prac3() -> Figure:
    from matplotlib.patches import Ellipse
    f = Figure(width_in=3.6, height_in=1.7)
    for ctr, ax_len, name in ((OV_EC, OV_EAX, "e"), (OV_FC, OV_FAX, "f")):
        f.custom(lambda ax, col, ctr=ctr, a=ax_len: ax.add_patch(Ellipse(
            tuple(ctr), 2 * a[0], 2 * a[1], fill=False, edgecolor=col, lw=1.3, clip_on=False)),
            extent=[(ctr[0] - ax_len[0], ctr[1] - ax_len[1]), (ctr[0] + ax_len[0], ctr[1] + ax_len[1])])
        f.label(ctr + np.array([-0.75 * ax_len[0], 0.75 * ax_len[1]]), name, direction=(-1, 1), offset_pt=6)
    for pts, (h0, h1, mid, top), lens in ((OV_E, "ABCD", ("6", "3")), (OV_F, "XYWZ", ("4", "a"))):
        small = h0 == "X"
        f.seg(pts[h0], pts[h1])
        f.seg(pts[mid], pts[top])
        f.dots([pts[h0], pts[h1], pts[mid], pts[top]])
        f.label(pts[h0], h0, direction=(-0.3, 1))
        f.label(pts[h1], h1, direction=(0.3, 1))
        f.label(pts[mid], mid, direction=(-1, 0.8))
        f.label(pts[top], top, direction=(0, 1))
        f.side_label(pts[h0], pts[h1], lens[0], pts[top])
        f.side_label(pts[mid], pts[top], lens[1], pts[h1] - np.array([10, 0]), italic=lens[1] == "a",
                     offset_pt=7 if small else 10)
    return f

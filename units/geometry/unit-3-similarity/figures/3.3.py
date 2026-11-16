"""Lesson 3.3 figures: measuring dilations. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import Figure, P, assert_lengths, dilate, dist, figure, similarity_ratio


def _grid(f: Figure, x0, x1, y0, y1, lw=0.35):
    for x in range(x0, x1 + 1):
        f.seg((x, y0), (x, y1), lw=lw)
    for y in range(y0, y1 + 1):
        f.seg((x0, y), (x1, y), lw=lw)


def _ray(f: Figure, c, p, past=0.6, layer="answer"):
    u = (np.asarray(p, float) - c) / dist(c, p)
    f.seg(c, np.asarray(p, float) + past * u, layer=layer, dashed=True, lw=0.8)


def _inside(pt, tri) -> bool:
    def cr(u, v):
        return u[0] * v[1] - u[1] * v[0]
    s = [np.sign(cr(tri[(i + 1) % 3] - tri[i], pt - tri[i])) for i in range(3)]
    return abs(sum(s)) == 3


# Warm-up a: triangle FGH with center C inside it, scale factor 3
WC = np.array((0, 0), float)
WF, WG, WH = P((2, 0), (-2, 2), (0, -2))
WF2, WG2, WH2 = dilate([WF, WG, WH], 3, WC)
assert _inside(WC, [WF, WG, WH])
assert similarity_ratio([WF, WG, WH], [WF2, WG2, WH2]) == 3
assert all(abs(v) <= 6 for p in (WF2, WG2, WH2) for v in p)


@figure("3.3_warm_dilate")
def warm_dilate() -> Figure:
    f = Figure(width_in=2.6, height_in=2.6)
    _grid(f, -6, 6, -6, 6, lw=0.3)
    f.poly([WF, WG, WH], lw=1.4)
    f.dots([WF, WG, WH, WC], size=16)
    f.label(WF, "F", direction=(1, 0.6), offset_pt=6, size=11)
    f.label(WG, "G", direction=(-0.87, -0.5), offset_pt=9, size=11)
    f.label(WH, "H", direction=(0.6, -1), offset_pt=6, size=11)
    f.label(WC, "C", direction=(0.64, -0.77), offset_pt=9, size=10)
    for p in (WF2, WG2, WH2):
        _ray(f, WC, p, past=0.4)
    f.poly([WF2, WG2, WH2], layer="answer", lw=1.4)
    f.dots([WF2, WG2, WH2], layer="answer", size=16)
    f.label(WF2, "F'", layer="answer", direction=(0.4, 1), offset_pt=6, size=11)
    f.label(WG2, "G'", layer="answer", direction=(0.3, 1), offset_pt=6, size=11)
    f.label(WH2, "H'", layer="answer", direction=(1, -0.2), offset_pt=7, size=11)
    return f


# Warm-up b: triangle JKL from C with scale factor 2, but L' was placed at 3 times CL
EC = np.array((0, 0), float)
EJ, EK, EL = P((2, 1), (3, 1), (2, 2))
EJ2, EK2 = dilate([EJ, EK], 2, EC)
EL2 = dilate([EL], 3, EC)[0]
assert np.allclose(EJ2, (4, 2)) and np.allclose(EK2, (6, 2)) and np.allclose(EL2, (6, 6))
assert abs(dist(EC, EL2) / dist(EC, EL) - 3) < 1e-12


@figure("3.3_warm_error")
def warm_error() -> Figure:
    f = Figure(width_in=2.2, height_in=2.2)
    _grid(f, 0, 7, 0, 7)
    for p in (EJ2, EK2, EL2):
        _ray(f, EC, p, past=0.7, layer="given")
    f.poly([EJ, EK, EL], lw=1.4)
    f.poly([EJ2, EK2, EL2], lw=1.4)
    f.dots([EC, EJ, EK, EL, EJ2, EK2, EL2], size=16)
    f.label(EC, "C", direction=(-1, -0.4), offset_pt=7)
    f.label(EJ, "J", direction=(0.17, -0.98), offset_pt=12, size=10)
    f.label(EK, "K", direction=(0.5, -1), offset_pt=7)
    f.label(EL, "L", direction=(-1, 0.3), offset_pt=7)
    f.label(EJ2, "J'", direction=(-0.3, 1), offset_pt=8)
    f.label(EK2, "K'", direction=(1, -0.6), offset_pt=8)
    f.label(EL2, "L'", direction=(-1, 0.3), offset_pt=8)
    return f


# Problems 1-5: right triangle EFG (3-4-5) from center C, scale factor 2; Problem 5 uses 1/2
AC = np.array((0, 0), float)
AE, AF, AG = P((1, 1), (1, 4), (5, 1))
TRI = [AE, AF, AG]
TRI2 = dilate(TRI, 2, AC)
TRI_HALF = dilate(TRI, 0.5, AC)
SIDES = {"EF": 3, "EG": 4, "FG": 5}
assert dist(AE, AF) == 3 and dist(AE, AG) == 4 and dist(AF, AG) == 5
assert np.allclose(TRI2, P((2, 2), (2, 8), (10, 2)))
assert similarity_ratio(TRI, TRI2) == 2 and similarity_ratio(TRI, TRI_HALF) == 0.5
assert np.isclose(sum(SIDES.values()) * 0.5, 6)


@figure("3.3_efg")
def efg() -> Figure:
    f = Figure(width_in=3.0, height_in=2.5)
    _grid(f, 0, 11, 0, 9)
    f.poly(TRI, lw=1.5)
    f.dots(TRI + [AC], size=18)
    f.label(AC, "C", direction=(-1, -1), offset_pt=8)
    f.label(AE, "E", direction=(0.77, -0.64), offset_pt=9, size=9)
    f.label(AF, "F", direction=(-1, 0.4), offset_pt=8)
    f.label(AG, "G", direction=(0.6, -1), offset_pt=8)
    f.side_label(AF, AG, "5", AE, offset_pt=8, size=11)
    e2, f2, g2 = TRI2
    for p in TRI2:
        _ray(f, AC, p, past=0.3)
    f.poly(list(TRI2), layer="answer", lw=1.5)
    f.dots(list(TRI2), layer="answer", size=18)
    f.label(e2, "E'", layer="answer", direction=(1, -0.8), offset_pt=9)
    f.label(f2, "F'", layer="answer", direction=(-1, 0.4), offset_pt=9)
    f.label(g2, "G'", layer="answer", direction=(0.6, -1), offset_pt=9)
    f.side_label(f2, g2, "10", e2, layer="answer", offset_pt=8, size=11)
    return f


# Exit ticket: triangle PQR with side lengths, center C, scale factor 1.5
XC = np.array((0.0, 4.4))
XP, XQ, XR = P((4.31, 3.75), (1.0, 0.0), (4.84, 0.70))
EXIT = {"PQ": 5, "PR": 3.1, "QR": 3.9}
assert_lengths([(XP, XQ, EXIT["PQ"]), (XP, XR, EXIT["PR"]), (XQ, XR, EXIT["QR"])], tol=0.01)
assert EXIT["PQ"] * 1.5 == 7.5


@figure("3.3_exit")
def exit_fig() -> Figure:
    f = Figure(width_in=1.9, height_in=2.0)
    f.poly([XP, XQ, XR])
    f.dots([XC, XP, XQ, XR])
    f.label(XC, "C", direction=(0, 1))
    f.label(XP, "P", direction=(0.3, 1))
    f.label(XQ, "Q", direction=(-0.6, -1))
    f.label(XR, "R", direction=(1, -0.3))
    mid = np.mean([XP, XQ, XR], axis=0)
    f.side_label(XP, XQ, "5", mid, size=11)
    f.side_label(XP, XR, "3.1", mid, size=11)
    f.side_label(XQ, XR, "3.9", mid, size=11)
    return f


# Practice 4: quadrilateral ABCD dilated from D with scale factor 2
QD = np.array((2, 0), float)
QA, QB, QC = P((1, 2), (3, 3), (5, 2))
QUAD = [QA, QB, QC, QD]
QUAD2 = dilate(QUAD, 2, QD)
assert np.allclose(QUAD2, P((0, 4), (4, 6), (8, 4), (2, 0)))
assert similarity_ratio(QUAD, QUAD2) == 2


@figure("3.3_prac_quad")
def prac_quad() -> Figure:
    f = Figure(width_in=2.4, height_in=2.0)
    _grid(f, 0, 10, 0, 7)
    f.poly(QUAD, lw=1.5)
    f.dots(QUAD, size=18)
    f.label_poly(QUAD, "ABCD", offset_pt=8)
    a2, b2, c2, _ = QUAD2
    for p in (a2, b2, c2):
        _ray(f, QD, p, past=0.4)
    f.poly(list(QUAD2), layer="answer", lw=1.5)
    f.dots([a2, b2, c2], layer="answer", size=18)
    f.label(a2, "A'", layer="answer", direction=(-1, 0.3), offset_pt=8)
    f.label(b2, "B'", layer="answer", direction=(0, 1), offset_pt=8)
    f.label(c2, "C'", layer="answer", direction=(0.3, 1), offset_pt=9)
    return f


# Practice 5: figure G (a "cone": two segments and a half circle) dilated from B with scale factor 3.
# B and the three marked points sit on lattice points so students can count.
GB = np.array((0.0, 0.0))
GL, GR, GV = P((1, 1), (3, 1), (2, -1))
_ctr, _r = (GL + GR) / 2, dist(GL, GR) / 2
ARC = [_ctr + _r * np.array((np.cos(t), np.sin(t))) for t in np.linspace(0, np.pi, 40)]
assert np.allclose(ARC[0], GR) and np.allclose(ARC[-1], GL)
SHAPE = [GL, GV, GR] + ARC[1:-1]
SHAPE3 = list(dilate(SHAPE, 3, GB))
assert np.allclose(SHAPE3[:3], P((3, 3), (6, -3), (9, 3)))
assert abs(similarity_ratio(SHAPE, SHAPE3) - 3) < 1e-9


@figure("3.3_prac_cone")
def prac_cone() -> Figure:
    f = Figure(width_in=2.6, height_in=2.9)
    _grid(f, -1, 10, -4, 7, lw=0.3)
    f.poly(SHAPE, lw=1.4)
    f.dots([GB, GL, GV, GR], size=16)
    f.label(GB, "B", direction=(-1, 0.3), offset_pt=7)
    f.label(ARC[20], "G", direction=(0, 1), offset_pt=7)
    pts3 = [SHAPE3[0], SHAPE3[1], SHAPE3[2]]
    for p in pts3:
        _ray(f, GB, p, past=0.3)
    f.poly(SHAPE3, layer="answer", lw=1.4)
    f.dots(pts3, layer="answer", size=16)
    f.label(dilate([ARC[20]], 3, GB)[0], "G'", layer="answer", direction=(0, 1), offset_pt=7)
    return f


# Practice 1: pentagon ABCDE (sides 3, 6, 3, 3, 6) dilated from F with scale factor 5/3
_cy = 3 + np.sqrt(36 - (63 / 12) ** 2)
PENT = list(P((0, 0), (0, 3), (63 / 12, _cy), (6, 3), (6, 0)))
PENT_F = np.array((3.0, 2.6))
PENT2 = list(dilate(PENT, 5 / 3, PENT_F))
PENT_SIDES = [3, 6, 3, 3, 6]
assert_lengths([(PENT[i], PENT[(i + 1) % 5], L) for i, L in enumerate(PENT_SIDES)], tol=0.005)
assert_lengths([(PENT[0], PENT[1], 3)] + [(PENT2[i], PENT2[(i + 1) % 5], L * 5 / 3)
                                          for i, L in enumerate(PENT_SIDES)], tol=0.005)
assert _inside(PENT_F, PENT[:3]) or _inside(PENT_F, [PENT[0], PENT[2], PENT[4]])


@figure("3.3_prac_pentagon")
def prac_pentagon() -> Figure:
    f = Figure(width_in=2.8, height_in=2.8)
    f.poly(PENT, lw=1.3)
    f.poly(PENT2, lw=1.3)
    f.dots(PENT + PENT2 + [PENT_F], size=12)
    f.label(PENT_F, "F", direction=(0, 1), offset_pt=6, size=11)
    for pts, names in ((PENT, "ABCDE"), (PENT2, ["A'", "B'", "C'", "D'", "E'"])):
        for p, n in zip(pts, names):
            f.label(p, n, direction=p - PENT_F, offset_pt=6, size=11)
    for i, L in enumerate(PENT_SIDES):
        j = (i + 1) % 5
        f.side_label(PENT[i], PENT[j], f"{L}", PENT_F, offset_pt=6, size=11)
        f.side_label(PENT2[i], PENT2[j], f"{L * 5 // 3}", PENT_F, offset_pt=6, size=11)
    return f


# Practice 6: polygon Q is a dilation of polygon P with k = 3/4 (top 4 -> 3, side x = 6 -> y = 4.5)
QP = list(P((1, 6), (5, 6), (5.6, 6 - np.sqrt(36 - 0.36)), (0, 1)))
QQ = list(dilate(QP, 0.75, (28, 3)))
assert_lengths([(QP[0], QP[1], 4), (QP[1], QP[2], 6), (QQ[0], QQ[1], 3), (QQ[1], QQ[2], 4.5)], tol=0.005)
assert np.isclose(similarity_ratio(QP, QQ), 0.75)


@figure("3.3_prac_polygons")
def prac_polygons() -> Figure:
    f = Figure(width_in=2.6, height_in=1.5)
    for pts, name, top, side in ((QP, "P", "4", "x"), (QQ, "Q", "3", "y")):
        f.poly(pts, lw=1.3)
        mid = np.mean(pts, axis=0)
        f.text(mid, name, size=11)
        f.side_label(pts[0], pts[1], top, mid, offset_pt=6, size=11)
        f.side_label(pts[1], pts[2], side, mid, offset_pt=6, size=11, italic=True)
    return f
def _par(x):
    return x ** 2 + 6 * x + 5


assert _par(-1) == 0 and _par(-5) == 0 and _par(-3) == -4


@figure("3.3_prac_parabola")
def prac_parabola() -> Figure:
    f = Figure(width_in=2.2, height_in=2.2)
    _grid(f, -7, 1, -5, 4, lw=0.3)
    f.seg((-7, 0), (1, 0), lw=1.1)
    f.seg((0, -5), (0, 4), lw=1.1)
    f.label((1, 0), "x", direction=(1, 0), offset_pt=6)
    f.label((0, 4), "y", direction=(0, 1), offset_pt=6)
    for x in (-6, -4, -2):
        f.text((x, 0.45), f"−{-x}", size=10)
    for y in (-4, 2):
        f.text((0.45, y), f"{y}".replace("-", "−"), size=10)
    xs = np.linspace(-5.8, -0.2, 57)
    f.poly([np.array((x, _par(x))) for x in xs], closed=False, layer="answer", lw=1.5)
    f.dots(P((-1, 0), (-5, 0), (-3, -4)), layer="answer", size=18)
    return f

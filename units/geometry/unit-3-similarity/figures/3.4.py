"""Lesson 3.4 figures: dilating lines and angles. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, assert_lengths, dilate, dist, figure, similarity_ratio,
                                    ssa_triangles)


def _parallel(a, b, c, d, tol=1e-9) -> bool:
    u, v = np.asarray(b) - np.asarray(a), np.asarray(d) - np.asarray(c)
    return abs(u[0] * v[1] - u[1] * v[0]) < tol * max(1.0, np.linalg.norm(u) * np.linalg.norm(v))


def _collinear(a, b, c, tol=1e-9) -> bool:
    return _parallel(a, b, a, c, tol)


# Warm-up and Problem 4: triangle ABC dilated from P with scale factor 2
WP = np.array((-0.6, -0.8), float)
WA, WB, WC = P((1.6, 2.6), (2.8, 1.8), (0.9, 1.8))
WA2, WB2, WC2 = dilate([WA, WB, WC], 2, WP)
assert abs(similarity_ratio([WA, WB, WC], [WA2, WB2, WC2]) - 2) < 1e-9
for (x, y), (x2, y2) in [((WA, WB), (WA2, WB2)), ((WB, WC), (WB2, WC2)), ((WA, WC), (WA2, WC2))]:
    assert _parallel(x, y, x2, y2)
for v, v2, a, b, a2, b2 in [(WA, WA2, WB, WC, WB2, WC2), (WB, WB2, WA, WC, WA2, WC2), (WC, WC2, WA, WB, WA2, WB2)]:
    assert abs(angle_deg(v, a, b) - angle_deg(v2, a2, b2)) < 1e-9


def _pair(f: Figure):
    f.poly([WA, WB, WC])
    f.poly([WA2, WB2, WC2])
    f.dots([WA, WB, WC, WA2, WB2, WC2, WP])
    f.label_poly([WA, WB, WC], "ABC")
    f.label_poly([WA2, WB2, WC2], ["A'", "B'", "C'"], overrides={"C'": (-1, 0.15)})
    f.label(WP, "P", direction=(0, -1))


@figure("3.4_warmup")
def warmup() -> Figure:
    f = Figure(width_in=2.4, height_in=2.3)
    _pair(f)
    return f


# Problem 4: E between P and B (key uses PE = 0.35 PB), E' is its image
WE = WP + 0.35 * (WB - WP)
WE2 = dilate([WE], 2, WP)[0]
assert _collinear(WP, WB, WE2) and dist(WP, WE2) < dist(WP, WB)
assert abs(angle_deg(WB, WE, WC) - angle_deg(WB2, WE2, WC2)) < 1e-9


@figure("3.4_proof")
def proof() -> Figure:
    f = Figure(width_in=2.6, height_in=2.5)
    _pair(f)
    f.seg(WP, WB2 + 0.12 * (WB2 - WP), dashed=True, lw=0.9)
    side = np.array([(WB - WP)[1], -(WB - WP)[0]])
    f.dots([WE, WE2], layer="answer")
    f.label(WE, "E", layer="answer", direction=side)
    f.label(WE2, "E'", layer="answer", direction=side)
    f.arc(WB, WE, WC, n=1, r=0.85, layer="answer")
    f.arc(WB2, WE2, WC2, n=1, r=0.85, layer="answer")
    return f


# Problem 1 (Together): center C on line AB (D on the other side of C) and on line CE
U = np.array([np.cos(np.radians(55)), np.sin(np.radians(55))])
TC = np.array((0, 0), float)
TA, TB, TD = 4 * U, 2 * U, -2 * U
TE = np.array((2.6, 0.1), float)
TA2 = dilate([TA], 0.75, TC)[0]
TB2 = dilate([TB], 1 / 3, TC)[0]
TD2 = dilate([TD], 1.5, TC)[0]
TE2 = dilate([TE], 2, TC)[0]
for p in (TA2, TB2, TD2):
    assert _collinear(TC, TA, p)
assert _collinear(TC, TE, TE2)
assert np.dot(TD2 - TC, TD - TC) > 0  # D' stays on D's side of C


@figure("3.4_lines")
def lines() -> Figure:
    f = Figure(width_in=2.9, height_in=3.0)
    f.seg(-3.6 * U, 4.7 * U)
    ue = TE / np.linalg.norm(TE)
    f.seg(-0.8 * ue, TE2 + 0.5 * ue)
    f.dots([TA, TB, TC, TD, TE])
    nrm = np.array([U[1], -U[0]])
    f.label(TA, "A", direction=nrm)
    f.label(TB, "B", direction=nrm)
    f.label(TD, "D", direction=nrm)
    f.label(TC, "C", direction=(0.6, -1))
    f.label(TE, "E", direction=(0, -1))
    f.dots([TA2, TB2, TD2, TE2], layer="answer")
    f.label(TA2, "A'", layer="answer", direction=-nrm)
    f.label(TB2, "B'", layer="answer", direction=-nrm)
    f.label(TD2, "D'", layer="answer", direction=-nrm)
    f.label(TE2, "E'", layer="answer", direction=(0, -1))
    return f


# Problem 3: the same idea on a grid. P = (0, 0), scale factor 2
GP = np.array((0, 0), float)
GA, GB, GC = P((1, 3), (3, 2), (2, 1))
GA2, GB2, GC2 = dilate([GA, GB, GC], 2, GP)
SLOPES = {"AB": -1 / 2, "AC": -2, "BC": 1}


def _slope(a, b):
    return (b[1] - a[1]) / (b[0] - a[0])


assert abs(_slope(GA, GB) - SLOPES["AB"]) < 1e-12 and abs(_slope(GA2, GB2) - SLOPES["AB"]) < 1e-12
assert abs(_slope(GA, GC) - SLOPES["AC"]) < 1e-12 and abs(_slope(GA2, GC2) - SLOPES["AC"]) < 1e-12
assert abs(_slope(GB, GC) - SLOPES["BC"]) < 1e-12 and abs(_slope(GB2, GC2) - SLOPES["BC"]) < 1e-12


@figure("3.4_grid")
def grid() -> Figure:
    f = Figure(width_in=2.5, height_in=2.5)
    n = 7
    for k in range(n + 1):
        f.seg((k, 0), (k, n), lw=0.35)
        f.seg((0, k), (n, k), lw=0.35)
    f.poly([GA, GB, GC], lw=1.5)
    f.poly([GA2, GB2, GC2], lw=1.5)
    f.dots([GP, GA, GB, GC, GA2, GB2, GC2], size=18)
    f.label(GP, "P", direction=(-1, -1), offset_pt=8)
    f.label(GA, "A", direction=(-1, 0.4), offset_pt=8)
    f.label(GB, "B", direction=(0.2, 1), offset_pt=8)
    f.label(GC, "C", direction=(0.4, -1), offset_pt=8)
    f.label(GA2, "A'", direction=(-0.6, 1), offset_pt=9)
    f.label(GB2, "B'", direction=(1, 0.4), offset_pt=10)
    f.label(GC2, "C'", direction=(0.5, -1), offset_pt=9)
    return f


# CYU: triangle ABC dilated from D with scale factor 2; C is the midpoint of DB, so C' = B
V = np.array([np.cos(np.radians(38)), np.sin(np.radians(38))])
CD = np.array((0, 0), float)
CC, CB = 1.5 * V, 3.0 * V
CA = CC + np.array((-0.55, 1.05), float)
CA2, CB2, CC2 = dilate([CA, CB, CC], 2, CD)
assert np.allclose(CC2, CB)
assert _parallel(CA, CB, CA2, CB2) and abs(dist(CA2, CB2) - 2 * dist(CA, CB)) < 1e-9
assert _collinear(CD, CA, CA2) and abs(dist(CD, CA2) - 2 * dist(CD, CA)) < 1e-9
assert _collinear(CD, CB, CB2) and _collinear(CB, CC, CB2)
assert abs(angle_deg(CB, CA, CC) - angle_deg(CB2, CA2, CC2)) < 1e-9


@figure("3.4_cyu")
def cyu() -> Figure:
    f = Figure(width_in=2.4, height_in=2.4)
    f.seg(CD - 0.25 * V, CB2 + 0.35 * V)
    f.poly([CA, CB, CC])
    f.poly([CA2, CB2, CC2])
    f.dots([CD, CA, CB, CC, CA2, CB2])
    f.ticks(CD, CC, 1)
    f.ticks(CC, CB, 1)
    nrm = np.array([V[1], -V[0]])
    f.label(CD, "D", direction=nrm)
    f.label(CC, "C", direction=nrm)
    f.label(CB, "B = C'", direction=nrm, offset_pt=20)
    f.label(CB2, "B'", direction=nrm)
    f.label(CA, "A", direction=(-1, 0.3))
    f.label(CA2, "A'", direction=(-0.6, 1))
    return f


# Practice 2: five lines; m, n, p are parallel
LINES = {
    "o": (np.array((0, 3.2), float), np.array((5.2, 0.2), float)),
    r"\ell": (np.array((1.9, 4.2), float), np.array((1.3, 0), float)),
    "m": (np.array((0, 0), float), np.array((4.2, 4.0), float)),
    "n": (np.array((0.8, 0), float), np.array((5.0, 4.0), float)),
    "p": (np.array((2.4, 0), float), np.array((5.0, 2.476), float)),
}
for name in ("n", "p"):
    assert _parallel(*LINES["m"], *LINES[name], tol=1e-3)
assert not _parallel(*LINES["m"], *LINES["o"]) and not _parallel(*LINES["m"], *LINES[r"\ell"])


@figure("3.4_five_lines")
def five_lines() -> Figure:
    f = Figure(width_in=2.4, height_in=1.9)
    spots = {"o": 0.12, r"\ell": 0.12, "m": 0.88, "n": 0.88, "p": 0.85}
    sides = {"o": (0.3, 1), r"\ell": (-1, 0), "m": (-0.7, 0.7), "n": (0.7, -0.7), "p": (0.7, -0.7)}
    for name, (a, b) in LINES.items():
        f.seg(a, b)
        f.label(a + spots[name] * (b - a), name, direction=sides[name], offset_pt=9)
    return f


# Practice 3: line f through C, its image g (scale factor 2) through B; the center is D
QD = np.array((3.0, 0.0), float)
QC = np.array((3.4, 1.2), float)
DIR = np.array([1.0, 0.72]) / np.linalg.norm([1.0, 0.72])
QB = dilate([QC], 2, QD)[0]
QA = np.array((1.0, 2.6), float)
f_ends = (QC - 2.2 * DIR, QC + 1.7 * DIR)
g_ends = (QB - 3.4 * DIR, QB + 2.2 * DIR)
assert np.allclose(dilate(list(f_ends), 2, QD)[0] - QB, 2 * (f_ends[0] - QC))  # g = image of f from D
cross = lambda p, a: (p - a)[0] * DIR[1] - (p - a)[1] * DIR[0]
assert cross(QA, QB) * cross(QC, QB) < 0  # A is on the far side of g, so A is not the center


@figure("3.4_center")
def center() -> Figure:
    f = Figure(width_in=2.4, height_in=2.0)
    f.seg(*f_ends)
    f.seg(*g_ends)
    f.dots([QA, QB, QC, QD])
    nrm = np.array([-DIR[1], DIR[0]])
    f.label(QA, "A", direction=(0, 1))
    f.label(QB, "B", direction=nrm)
    f.label(QC, "C", direction=nrm)
    f.label(QD, "D", direction=(0, 1))
    f.label(f_ends[1], "f", direction=(1, 0), offset_pt=8)
    f.label(g_ends[1], "g", direction=(1, 0), offset_pt=8)
    return f


# Practice 4: quadrilateral ABCE dilated from F onto A'B'C'E', scale factor 1/2
t = np.radians(10)
QA4 = np.array((0, 0), float)
QB4 = np.array((0, 3), float)
QC4 = QB4 + 6 * np.array([np.cos(t), np.sin(t)])
QE4 = QC4 - np.array((0, 5), float)
QF = np.array((2.9, 1.3), float)
QUAD = [QA4, QB4, QC4, QE4]
QUAD2 = dilate(QUAD, 0.5, QF)
assert abs(similarity_ratio(QUAD, QUAD2) - 0.5) < 1e-9
assert_lengths([(QA4, QB4, 3), (QB4, QC4, 6), (QC4, QE4, 5),
                (QUAD2[0], QUAD2[1], 1.5), (QUAD2[1], QUAD2[2], 3), (QUAD2[2], QUAD2[3], 2.5)])


@figure("3.4_quad")
def quad() -> Figure:
    f = Figure(width_in=2.4, height_in=2.0)
    f.poly(QUAD)
    f.poly(QUAD2)
    f.dots(QUAD + list(QUAD2) + [QF])
    f.label_poly(QUAD, "ABCE", offset_pt=9)
    f.label_poly(QUAD2, ["A'", "B'", "C'", "E'"], offset_pt=9, overrides={"A'": (0.6, -1)})
    f.label(QF, "F", direction=(0, -1), offset_pt=9)
    mid = np.mean(QUAD, axis=0)
    f.side_label(QA4, QB4, "3", mid)
    f.side_label(QB4, QC4, "6", mid)
    f.side_label(QC4, QE4, "5", mid)
    a2, b2, c2, e2 = QUAD2
    mid2 = np.mean(QUAD2, axis=0)
    for p, q, s in ((a2, b2, "1.5"), (c2, e2, "2.5")):
        m = (p + q) / 2
        f.side_label(p, q, s, 2 * m - mid2, size=11, offset_pt=11)  # inside the small quadrilateral
    f.side_label(b2, c2, "3", mid2, size=11, offset_pt=7)  # between the two top edges, away from F
    return f


# Practice 7: two non-congruent triangles with angle A = 30, AC = 3, CB = 2 (SSA)
long_t, short_t = ssa_triangles(3, 2, 30)
for tri in (long_t, short_t):
    assert abs(dist(tri[1], tri[2]) - 2) < 1e-9 and abs(angle_deg(tri[0], tri[1], tri[2]) - 30) < 1e-9
assert abs(dist(long_t[0], long_t[2]) - dist(short_t[0], short_t[2])) > 0.5  # not congruent
assert_lengths([(long_t[0], long_t[1], 3), (long_t[1], long_t[2], 2), (short_t[1], short_t[2], 2)])


@figure("3.4_ssa")
def ssa() -> Figure:
    # given: angle A = 30 and AC = 3 (the start both triangles share); answer: the two places B can go
    f = Figure(width_in=2.6, height_in=1.4)
    a, c, b1 = long_t
    _, _, b2 = short_t
    ray = b1 / np.linalg.norm(b1)
    f.seg(a, c)
    f.seg(a, b1 + 0.6 * ray)
    f.dots([a, c])
    f.label(a, "A", direction=(-1, -0.3))
    f.label(c, "C", direction=(1, -0.3))
    f.side_label(a, c, "3", b1)
    f.arc(a, c, b1, r=0.5)
    f.angle_label(a, c, b1, r"$30^\circ$", dist=0.78, size=10)
    f.seg(c, b1, layer="answer")
    f.seg(c, b2, layer="answer", dashed=True)
    f.dots([b1, b2], layer="answer")
    f.label(b1, "B", layer="answer", direction=(-0.6, 1))
    f.label(b2, "Y", layer="answer", direction=(-0.6, 1))
    f.side_label(c, b1, "2", a, layer="answer", offset_pt=8)
    up = np.array([-(b2 - c)[1], (b2 - c)[0]])
    up = up if up[1] > 0 else -up
    f.label(c + 0.3 * (b2 - c), "2", layer="answer", direction=up, offset_pt=8, italic=False)  # clear of 30°
    return f

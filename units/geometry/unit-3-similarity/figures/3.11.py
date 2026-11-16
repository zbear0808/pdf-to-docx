"""Lesson 3.11 figures: side splitter theorem. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, assert_lengths, dilate, dist, figure, rotate, translate


def _par(f, a, b, s, n=1, layer="given"):
    """Parallel-line arrowheads (n chevrons) at the midpoint of ab, pointing a -> b; s = size in data units."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = (b - a) / np.linalg.norm(b - a)
    nrm = np.array([-u[1], u[0]])
    m = (a + b) / 2
    for k in range(n):
        tip = m + u * (k - (n - 1) / 2) * 0.8 * s + u * s / 2
        f.seg(tip - u * s + nrm * 0.6 * s, tip, layer=layer)
        f.seg(tip - u * s - nrm * 0.6 * s, tip, layer=layer)


def _is_par(a, b, c, d):
    u, v = np.asarray(b) - np.asarray(a), np.asarray(d) - np.asarray(c)
    return abs(u[0] * v[1] - u[1] * v[0]) < 1e-9 * np.linalg.norm(u) * np.linalg.norm(v)


def _line(f, a, b, ext=0.25, layer="given"):
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = b - a
    f.seg(a - ext * d, b + ext * d, layer=layer)


def _labels(f, pts, names_dirs):
    for pt, (nm, d) in zip(pts, names_dirs):
        f.label(pt, nm, direction=d)


@figure("3.11_warmup")
def warmup() -> Figure:
    # Warm-up: line AC || line MN, M on BA, N on BC. MN is the image of AC under a dilation at B (k = 0.55).
    B, A, C = P((0, 0), (-1.3, 3.0), (1.5, 2.3))
    M, N = dilate([A, C], 0.55, B)
    assert _is_par(A, C, M, N)
    f = Figure(width_in=2.3, height_in=2.2)
    _line(f, A, C, 0.3)
    _line(f, M, N, 0.55)
    f.seg(B, A)
    f.seg(B, C)
    _par(f, A, C, 0.28)
    _par(f, M, N, 0.28)
    f.dots([A, B, C, M, N])
    _labels(f, [A, B, C, M, N], [("A", (-0.6, 1)), ("B", (0, -1)), ("C", (0.4, 1)), ("M", (-1, 0)),
                                 ("N", (1, -0.4))])
    return f


@figure("3.11_t2")
def together2() -> Figure:
    # Together 2: BD || FG, BD = 5, FG = 15, EG = 12, EB = 2.5 -> k = 3, ED = 4, EF = 7.5
    F, G = P((0, 0), (15, 0))
    ex = (7.5 ** 2 - 12 ** 2 + 15 ** 2) / 30
    E = np.array([ex, -np.sqrt(7.5 ** 2 - ex ** 2)])
    B, D = dilate([F, G], 1 / 3, E)
    assert np.isclose(dist(E, F), 7.5) and np.isclose(dist(E, G), 12) and np.isclose(dist(B, D), 5)
    assert np.isclose(dist(E, B), 2.5) and np.isclose(dist(E, D), 4) and _is_par(B, D, F, G)
    assert_lengths([(F, G, 15), (B, D, 5), (E, G, 12), (E, B, 2.5)])
    f = Figure(width_in=2.4, height_in=1.3)
    f.poly([F, G, E])
    f.seg(B, D)
    _par(f, F, G, 0.9)
    _par(f, B, D, 0.9)
    f.dots([E, F, G, B, D])
    _labels(f, [F, G, E, B, D], [("F", (-1, 0.5)), ("G", (1, 0.5)), ("E", (0, -1)), ("B", (-1, -0.3)),
                                 ("D", (1, -0.3))])
    f.side_label(F, G, "15", center=E, size=11)
    f.side_label(B, D, "5", center=E, size=11)
    return f


# Street map (hundreds of feet). Library L; Lincoln Rd is LPQ, Oak Ave is LAB; Maple St || Chestnut St.
_L, _Pm, _Q = P((0, 15), (0, 6), (0, 0))
_A = np.array([-np.sqrt(12 ** 2 - 9 ** 2), 6.0])
_B = dilate([_A], 15 / 9, _L)[0]


@figure("3.11_map")
def street_map() -> Figure:
    L, Pm, Q, A, B = _L, _Pm, _Q, _A, _B
    assert np.isclose(dist(L, A), 12) and np.isclose(dist(L, B), 20) and np.isclose(dist(A, B), 8)
    assert np.isclose(dist(L, Pm) / dist(Pm, Q), dist(L, A) / dist(A, B))   # 900 : 600 = 1200 : 800
    assert _is_par(A, Pm, B, Q)
    assert_lengths([(L, Pm, 900), (Pm, Q, 600), (L, A, 1200)])   # hundreds of feet
    f = Figure(width_in=2.9, height_in=2.7)
    f.seg((-21, 6), (2.5, 6))
    f.seg((-21, 0), (2.5, 0))
    _par(f, (-5.0, 6), (-3.0, 6), 0.9)
    _par(f, (-5.0, 0), (-3.0, 0), 0.9)
    f.seg((0, 16.3), (0, -1.8))
    f.seg(L, L + 1.06 * (B - L))
    f.dots([L, Pm, Q, A, B])
    _labels(f, [L, Pm, Q, A, B], [("L", (1, 0.3)), ("P", (1, 1)), ("Q", (1, -1)), ("A", (-0.6, 1)),
                                  ("B", (0.6, -1))])
    f.text((-18.0, 6.9), "Maple St.", size=10)
    f.text((-17.6, 0.9), "Chestnut St.", size=10)
    f.text((0, -3.0), "Lincoln Rd.", size=10)
    f.text((-6.0, 2.6), "Oak Ave.", size=10)
    f.text((-3.6, 15.8), "library", size=10)
    f.side_label(L, Pm, "900 ft", center=A, size=10, offset_pt=18)
    f.side_label(Pm, Q, "600 ft", center=B, size=10, offset_pt=18)
    f.side_label(L, A, "1200 ft", center=Pm, size=10, offset_pt=14)
    f.arc(Pm, L, A, n=1, r=1.0, layer="answer")
    f.arc(Q, L, B, n=1, r=1.0, layer="answer")
    f.arc(A, L, Pm, n=2, r=1.0, gap=0.4, layer="answer")
    f.arc(B, L, Q, n=2, r=1.0, gap=0.4, layer="answer")
    return f


@figure("3.11_cyu")
def cyu() -> Figure:
    # CYU 1: right angle at D, AB || EF, DA = 3, DB = 4, DE = 7.5 -> k = 2.5, AB = 5, DF = 10, EF = 12.5
    D, B, A = P((0, 7.5), (4, 7.5), (0, 4.5))
    E, F = dilate([A, B], 2.5, D)
    assert np.isclose(dist(A, B), 5) and np.isclose(dist(D, F), 10) and np.isclose(dist(E, F), 12.5)
    assert np.isclose(dist(D, E), 7.5) and _is_par(A, B, E, F) and np.isclose(angle_deg(D, B, E), 90)
    assert_lengths([(D, B, 4), (D, A, 3), (D, E, 7.5)])
    f = Figure(width_in=2.2, height_in=1.75)
    f.seg(D, F)
    f.seg(D, E)
    f.seg(A, B)
    f.seg(E, F)
    f.right_angle(D, B, E, size=0.5)
    _par(f, A, B, 0.55)
    _par(f, E, F, 0.55)
    f.dots([D, B, A, E, F])
    _labels(f, [D, B, A, E, F], [("D", (-1, 0.6)), ("B", (0, 1)), ("A", (-1, 0)), ("E", (-1, -0.6)),
                                 ("F", (1, 0.6))])
    f.side_label(D, B, "4", center=A, size=11)
    f.side_label(D, A, "3", center=B, size=11)
    return f


@figure("3.11_exit")
def exit_ticket() -> Figure:
    # Exit: DE || AC, BD = 2, BE = 4, EC = 6, DE = 5 -> k = 10/4 = 2.5, BA = 5, AD = 3, AC = 12.5
    Bv, C = P((0, 0), (10, 0))
    ax = (25 - 12.5 ** 2 + 100) / 20
    A = np.array([ax, -np.sqrt(25 - ax ** 2)])
    tri = rotate([Bv, A, C], 18, Bv)
    Bv, A, C = tri
    D, E = dilate([A, C], 0.4, Bv)
    assert np.isclose(dist(Bv, D), 2) and np.isclose(dist(Bv, E), 4) and np.isclose(dist(E, C), 6)
    assert np.isclose(dist(D, E), 5) and np.isclose(dist(A, C), 12.5) and np.isclose(dist(A, D), 3)
    assert _is_par(D, E, A, C)
    assert_lengths([(Bv, D, 2), (Bv, E, 4), (E, C, 6), (D, E, 5)])
    f = Figure(width_in=2.5, height_in=1.8)
    f.poly([Bv, A, C])
    f.seg(D, E)
    _par(f, D, E, 0.6)
    _par(f, A, C, 0.6)
    f.dots([Bv, A, C, D, E])
    _labels(f, [Bv, A, C, D, E], [("B", (-1, 0.4)), ("A", (-0.6, -1)), ("C", (1, 0.4)), ("D", (1, -0.9)),
                                  ("E", (0, 1))])
    cen = (Bv + A + C) / 3
    f.side_label(Bv, D, "2", center=cen, size=11)
    f.side_label(Bv, E, "4", center=cen, size=11)
    f.side_label(E, C, "6", center=cen, size=11)
    f.side_label(D, E, "5", center=Bv, size=11)
    return f


@figure("3.11_notes")
def notes() -> Figure:
    # QuickNotes: MN || PR, M on QP, N on QR (dilation at Q, k = 0.45). Letters differ from the exit ticket.
    Q, P_, R = P((0, 0), (-1.0, 3.0), (3.2, 2.2))
    M, N = dilate([P_, R], 0.45, Q)
    assert _is_par(M, N, P_, R)
    f = Figure(width_in=1.6, height_in=1.4)
    f.poly([Q, P_, R])
    f.seg(M, N)
    _par(f, M, N, 0.3)
    _par(f, P_, R, 0.3)
    f.dots([Q, P_, R, M, N])
    _labels(f, [Q, P_, R, M, N], [("Q", (0, -1)), ("P", (-0.6, 1)), ("R", (1, 0.4)), ("M", (-1, 0)),
                                  ("N", (1, -0.4))])
    return f


@figure("3.11_p1")
def prac1() -> Figure:
    # Practice 1: A'B' || AB, CA' = 6, A'A = 3, CB' = 7, A'B' = 5 -> k = 9/6 = 1.5, AB = 7.5, B'B = 3.5
    C = np.array([0.0, 0.0])
    A = np.array([-9.0, 0.0])
    B = np.array([-7.5, np.sqrt(10.5 ** 2 - 7.5 ** 2)])
    C, A, B = rotate([C, A, B], 20, C)
    A2, B2 = dilate([A, B], 2 / 3, C)
    assert np.isclose(dist(A, B), 7.5) and np.isclose(dist(C, B), 10.5) and np.isclose(dist(B2, B), 3.5)
    assert np.isclose(dist(A2, B2), 5) and np.isclose(dist(C, B2), 7) and _is_par(A, B, A2, B2)
    assert_lengths([(A, A2, 3), (A2, C, 6), (B2, C, 7), (A2, B2, 5)])
    f = Figure(width_in=2.4, height_in=1.75)
    f.poly([A, B, C])
    f.seg(A2, B2)
    _par(f, A, B, 0.6)
    _par(f, A2, B2, 0.6)
    f.dots([A, B, C, A2, B2])
    _labels(f, [A, B, C, A2, B2], [("A", (-0.6, -1)), ("B", (-0.6, 1)), ("C", (1, 0)), ("A'", (0.3, -1)),
                                   ("B'", (0, 1))])
    cen = (A + B + C) / 3
    f.side_label(A, A2, "3", center=cen, size=11)
    f.side_label(A2, C, "6", center=cen, size=11)
    f.side_label(B2, C, "7", center=cen, size=11)
    f.side_label(A2, B2, "5", center=C, size=11)
    return f


@figure("3.11_p2")
def prac2() -> Figure:
    # Practice 2: AD = 4, DB = 2, AE = 9, EC = 5, DE = 11. 4/2 != 9/5, so DE is not parallel to BC.
    A, E, C = P((0, 0), (9, 0), (14, 0))
    dx = (16 - 121 + 81) / 18
    D = np.array([dx, np.sqrt(16 - dx ** 2)])
    B = 1.5 * D
    assert np.isclose(dist(D, E), 11) and np.isclose(dist(D, B), 2) and not _is_par(D, E, B, C)
    assert_lengths([(A, D, 4), (D, B, 2), (A, E, 9), (E, C, 5), (D, E, 11)])
    f = Figure(width_in=2.8, height_in=1.5)
    f.poly([A, B, C])
    f.seg(D, E)
    f.dots([A, B, C, D, E])
    _labels(f, [A, B, C, D, E], [("A", (-1, 0)), ("B", (0, 1)), ("C", (1, 0)), ("D", (-1, -0.2)),
                                 ("E", (0, -1))])
    cen = (A + B + C) / 3
    inside = (20.0, 4.0)
    f.side_label(A, D, "4", center=inside, size=11)
    f.side_label(D, B, "2", center=inside, size=11)
    f.side_label(A, E, "9", center=cen, size=11)
    f.side_label(E, C, "5", center=cen, size=11)
    f.side_label(D, E, "11", center=B, size=11)
    return f


@figure("3.11_p3")
def prac3() -> Figure:
    # Practice 3: MN || XZ, YN = 3, YM = 5, MX = 5, MN = 6 -> k = 2, NZ = 3, XZ = 12
    Y = np.array([0.0, 0.0])
    M = np.array([5.0, 0.0])
    N = np.array([-0.2, np.sqrt(9 - 0.04)])
    Y, M, N = rotate([Y, M, N], -15, Y)
    X, Z = dilate([M, N], 2, Y)
    assert np.isclose(dist(M, N), 6) and np.isclose(dist(N, Z), 3) and np.isclose(dist(X, Z), 12)
    assert _is_par(M, N, X, Z)
    assert_lengths([(Y, N, 3), (Y, M, 5), (M, X, 5), (M, N, 6)])
    f = Figure(width_in=2.2, height_in=1.7)
    f.poly([Y, X, Z])
    f.seg(M, N)
    _par(f, N, M, 0.6)
    _par(f, Z, X, 0.6)
    f.dots([Y, X, Z, M, N])
    _labels(f, [Y, X, Z, M, N], [("Y", (-1, -0.3)), ("X", (1, -0.3)), ("Z", (0, 1)), ("M", (0, -1)),
                                 ("N", (-1, 0))])
    cen = (Y + X + Z) / 3
    f.side_label(Y, N, "3", center=cen, size=11)
    f.side_label(Y, M, "5", center=cen, size=11)
    f.side_label(M, X, "5", center=cen, size=11)
    f.side_label(M, N, "6", center=Y, size=11)
    return f


def _tri(v0, dir_deg, side, ang0, ang1, turn=1):
    """Triangle from vertex v0, side v0v1 of length `side` at heading dir_deg, angles ang0 at v0 and ang1 at v1.
    turn=+1 puts the third vertex counterclockwise of v0v1, -1 clockwise."""
    v0 = np.asarray(v0, float)
    h = np.radians(dir_deg)
    v1 = v0 + side * np.array([np.cos(h), np.sin(h)])
    third = 180 - ang0 - ang1
    other = side * np.sin(np.radians(ang1)) / np.sin(np.radians(third))
    h2 = h + turn * np.radians(ang0)
    v2 = v0 + other * np.array([np.cos(h2), np.sin(h2)])
    assert np.isclose(angle_deg(v0, v1, v2), ang0) and np.isclose(angle_deg(v1, v0, v2), ang1)
    return v0, v1, v2


@figure("3.11_p4")
def prac4() -> Figure:
    # Practice 4: right triangle, AC = 4, BC = 5, D and E midpoints of AC and BC
    C, B, A = P((0, 0), (5, 0), (0, 4))
    D, E = (A + C) / 2, (B + C) / 2
    assert np.isclose(0.5 * 4 * 5, 10) and np.isclose(0.5 * dist(C, D) * dist(C, E), 2.5)
    f = Figure(width_in=1.8, height_in=1.5)
    f.poly([A, B, C])
    f.seg(D, E)
    f.right_angle(C, B, A, size=0.35)
    f.ticks(A, D, 1)
    f.ticks(D, C, 1)
    f.ticks(C, E, 2)
    f.ticks(E, B, 2)
    f.dots([A, B, C, D, E])
    _labels(f, [A, B, C, D, E], [("A", (0, 1)), ("B", (1, -0.3)), ("C", (-1, -0.6)), ("D", (-1, 0)),
                                 ("E", (0, -1))])
    return f


@figure("3.11_p5")
def prac5() -> Figure:
    # Practice 5: angle A = 47, angle C = 33 (so B = 100); angle D = 47, angle E = 100 -> ABC ~ DEF by AA.
    # AB = 9 matches DE = 12 (k = 4/3); BC = 12 matches EF = 16.
    A, C, B = _tri((0, 0), 0, 9 * np.sin(np.radians(100)) / np.sin(np.radians(33)), 47, 33, turn=-1)
    assert np.isclose(dist(A, B), 9) and abs(dist(B, C) - 12) < 0.15
    D, E, F = _tri((17.5, -4.0), -75, 12, 47, 100, turn=-1)
    assert np.isclose(dist(E, F) / dist(B, C), 12 / 9)
    assert_lengths([(A, B, 9), (B, C, 12), (D, E, 12)])
    assert np.isclose(angle_deg(B, A, C), 100) and np.isclose(angle_deg(E, D, F), 100)
    f = Figure(width_in=2.7, height_in=2.6)
    f.poly([A, B, C])
    f.poly([D, E, F])
    f.dots([A, B, C, D, E, F])
    _labels(f, [A, B, C], [("A", (-1, 0.5)), ("B", (0, -1)), ("C", (1, 0.5))])
    _labels(f, [D, E, F], [("D", (0.3, 1)), ("E", (1, 0)), ("F", (-1, -0.3))])
    f.angle_label(A, C, B, "47°", dist=2.8, size=10)
    f.angle_label(C, A, B, "33°", dist=3.2, size=10)
    f.angle_label(D, E, F, "47°", dist=3.2, size=10)
    f.angle_label(E, D, F, "100°", dist=2.8, size=10)
    f.side_label(A, B, "9", center=C, size=11)
    f.side_label(B, C, "12", center=A, size=11)
    f.side_label(D, E, "12", center=F, size=11)
    return f


@figure("3.11_p6")
def prac6() -> Figure:
    # Practice 6: angle A = 68, angle B = 30; angle D = 68, angle F = 30 -> A-D, B-F, C-E.
    # AC = 2 matches DE = 8 (k = 4); AB = 4 matches DF = 16.
    A, C, B = _tri((0, 0), 0, 4 * np.sin(np.radians(30)) / np.sin(np.radians(82)), 68, 82, turn=1)
    assert np.isclose(dist(A, B), 4) and abs(dist(A, C) - 2) < 0.05
    D, F, E = _tri((9.5, 0), -3, 16, 68, 30, turn=1)
    assert np.isclose(dist(D, E) / dist(A, C), 4) and np.isclose(dist(D, F), 16)
    assert np.isclose(angle_deg(B, A, C), 30) and np.isclose(angle_deg(F, D, E), 30)
    assert_lengths([(A, B, 4), (A, C, 2)])
    assert_lengths([(D, E, 8), (D, F, 16)])   # each triangle to its own scale; prompt says not to scale
    A, C, B = dilate([A, C, B], 2.6, A)   # small triangle drawn larger so its labels fit (not to scale)
    D, F, E = translate([D, F, E], (4.0, 0))
    f = Figure(width_in=3.2, height_in=1.8)
    f.poly([A, B, C])
    f.poly([D, E, F])
    f.dots([A, B, C, D, E, F])
    _labels(f, [A, B, C], [("A", (-1, -0.3)), ("B", (0, 1)), ("C", (1, -0.3))])
    _labels(f, [D, E, F], [("D", (-0.2, -1)), ("E", (0, 1)), ("F", (1, -0.3))])
    f.angle_label(A, C, B, "68°", dist=2.2, size=10)
    f.angle_label(B, A, C, "30°", dist=4.6, size=10)
    f.angle_label(D, F, E, "68°", dist=2.0, size=10)
    f.angle_label(F, D, E, "30°", dist=3.2, size=10)
    f.side_label(A, B, "4", center=C, size=11)
    f.side_label(A, C, "2", center=B, size=11)
    f.side_label(D, E, "8", center=F, size=11)
    return f

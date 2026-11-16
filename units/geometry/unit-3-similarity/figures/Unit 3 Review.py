"""Unit 3 Review figures. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, assert_distinct, assert_lengths, dilate, dist, figure, rotate,
                                    similarity_ratio, translate)


def _close(a, b, tol=1e-6) -> bool:
    return abs(a - b) < tol


def _grid(f: Figure, x0, x1, y0, y1):
    for x in range(x0, x1 + 1):
        f.seg((x, y0), (x, y1), lw=0.25)
    for y in range(y0, y1 + 1):
        f.seg((x0, y), (x1, y), lw=0.25)


def _on_ray(c, p, q, tol=1e-9) -> bool:
    u, v = np.asarray(p) - np.asarray(c), np.asarray(q) - np.asarray(c)
    return abs(u[0] * v[1] - u[1] * v[0]) < tol and float(np.dot(u, v)) > 0


def _parallel(a, b, c, d, tol=1e-9) -> bool:
    u, v = np.asarray(b) - np.asarray(a), np.asarray(d) - np.asarray(c)
    return abs(u[0] * v[1] - u[1] * v[0]) < tol


# ---------------------------------------------------------------- Problem 2: dilate EFGH, center C, k = 2
D_C = P(2, 0)
D_PTS = P((0, 1), (2, 2), (3, 4), (4, 1))          # E, F, G, H (concave at F)
D_IMG = dilate(D_PTS, 2, D_C)
assert np.allclose(D_IMG, [(-2, 2), (2, 4), (4, 8), (6, 2)])
for _p, _q in zip(D_PTS, D_IMG):
    assert _on_ray(D_C, _p, _q) and _close(dist(D_C, _q), 2 * dist(D_C, _p))
assert _close(similarity_ratio(D_PTS, D_IMG), 2)
assert _close(angle_deg(D_PTS[0], D_PTS[1], D_PTS[3]), angle_deg(D_IMG[0], D_IMG[1], D_IMG[3]))
assert _parallel(D_PTS[0], D_PTS[3], D_IMG[0], D_IMG[3])


@figure("Unit 3 Review_dilate")
def dilate_fig() -> Figure:
    f = Figure(width_in=2.9, height_in=2.6)
    _grid(f, -3, 7, 0, 9)
    f.poly(D_PTS)
    f.dots(np.vstack([D_PTS, [D_C]]))
    f.label(D_C, "C", direction=(0.6, -1))
    dirs = {"E": (-1, -0.4), "F": (-0.3, -1), "G": (-0.8, 0.8), "H": (1, -0.4)}
    for p, n in zip(D_PTS, "EFGH"):
        f.label(p, n, direction=dirs[n], offset_pt=8, size=11)
    for q in D_IMG:
        f.seg(D_C, q, layer="answer", dashed=True, lw=0.8)
    f.poly(D_IMG, layer="answer")
    f.dots(D_IMG, layer="answer")
    for q, n in zip(D_IMG, "EFGH"):
        d = {"F": (-1, 0.3), "E": (-0.6, 1)}.get(n, dirs[n])
        f.label(q, n + "′", layer="answer", direction=d, offset_pt=8, size=11)
    return f


# ---------------------------------------------------------------- Problem 4: midsegment MN of triangle ABC
@figure("Unit 3 Review_midseg")
def midseg() -> Figure:
    B, C = P((0, 0), (6, 0))
    A = B + 4.2 * np.array([np.cos(np.radians(64)), np.sin(np.radians(64))])
    M, N = (A + B) / 2, (A + C) / 2
    assert _close(angle_deg(B, A, C), 64) and _parallel(M, N, B, C) and _close(dist(M, N), dist(B, C) / 2)
    assert _close(angle_deg(M, A, N), angle_deg(B, A, C))
    assert_lengths([(B, C, 18), (M, N, 9)])
    k = 0.36
    A, B, C, M, N = (x * k for x in (A, B, C, M, N))
    f = Figure(width_in=2.2, height_in=1.6)
    f.poly([A, B, C])
    f.seg(M, N)
    f.dots([A, B, C, M, N])
    f.label(A, "A", direction=(0, 1))
    f.label(B, "B", direction=(-1, -0.4))
    f.label(C, "C", direction=(1, -0.4))
    f.label(M, "M", direction=(-1, 0.2))
    f.label(N, "N", direction=(1, 0.3))
    f.ticks(A, M, 1)
    f.ticks(M, B, 1)
    f.ticks(A, N, 2)
    f.ticks(N, C, 2)
    f.side_label(B, C, "18", A, size=11)
    f.arc(B, A, C, r=0.16)
    f.angle_label(B, A, C, "64°", dist=0.3, size=10)
    return f


# ---------------------------------------------------------------- Problem 5: ST parallel to QR in triangle PQR
@figure("Unit 3 Review_pqr")
def pqr() -> Figure:
    Q, R = P((0, 0), (16, 0))
    # PQ = 8, PR = 16
    x = (8 ** 2 - 16 ** 2 + 16 ** 2) / (2 * 16)
    Pt = P(x, np.sqrt(8 ** 2 - x ** 2))
    S = Pt + (Q - Pt) * 5 / 8
    T = Pt + (R - Pt) * 10 / 16
    assert _close(dist(Pt, Q), 8) and _close(dist(Pt, R), 16)
    assert _parallel(S, T, Q, R) and _close(dist(S, T), 10) and _close(dist(T, R), 6)
    assert _close(similarity_ratio([Pt, S, T], [Pt, Q, R]), 8 / 5)
    assert_lengths([(Q, R, 16), (Pt, S, 5), (S, Q, 3), (Pt, T, 10)])
    k = 0.17
    Q, R, Pt, S, T = (p * k for p in (Q, R, Pt, S, T))
    f = Figure(width_in=2.8, height_in=1.5)
    f.poly([Pt, Q, R])
    f.seg(S, T)
    f.dots([Pt, Q, R, S, T])
    f.label(Pt, "P", direction=(0, 1))
    f.label(Q, "Q", direction=(-1, -0.4))
    f.label(R, "R", direction=(1, -0.4))
    f.label(S, "S", direction=(-1, 0.2))
    f.label(T, "T", direction=(0.4, 1))
    cen = (Pt + Q + R) / 3
    f.side_label(Pt, S, "5", cen, size=10)
    f.side_label(S, Q, "3", cen, size=10)
    f.side_label(Pt, T, "10", cen, size=10)
    f.side_label(Q, R, "16", Pt, size=10)
    f.parallel_marks(S, T)
    f.parallel_marks(Q, R)
    return f


# ---------------------------------------------------------------- Problem 6: triangle RST and triangle XYZ
TR_R, TR_S = P((0, 0), (6, 0))
_dir = np.array([np.cos(np.radians(180 - 95)), np.sin(np.radians(180 - 95))])
TR_T = TR_S + 8 * _dir                                    # SAS: RS = 6, angle S = 95, ST = 8
assert _close(angle_deg(TR_S, TR_R, TR_T), 95)
assert abs(angle_deg(TR_R, TR_S, TR_T) - 50) < 0.1 and abs(angle_deg(TR_T, TR_R, TR_S) - 35) < 0.1
# image: dilate from R by 1.5, rotate 90 degrees clockwise around R, translate R to Z
_img = translate(rotate(dilate([TR_R, TR_S, TR_T], 1.5, TR_R), -90, TR_R), (12, 9))
XZ, XY_, XX = _img                                        # R -> Z, S -> Y, T -> X
assert _close(similarity_ratio([TR_R, TR_S, TR_T], [XZ, XY_, XX]), 1.5)
assert _close(dist(XZ, XY_), 9) and _close(dist(XY_, XX), 12)
assert_lengths([(TR_R, TR_S, 6), (TR_S, TR_T, 8), (XZ, XY_, 9)])
assert abs(angle_deg(XY_, XZ, XX) - 95) < 0.1 and abs(angle_deg(XZ, XY_, XX) - 50) < 0.1
assert_distinct([50, 35, 95])


@figure("Unit 3 Review_rst")
def rst() -> Figure:
    k = 0.17
    R, S, T = (p * k for p in (TR_R, TR_S, TR_T))
    Z, Y, X = (p * k for p in (XZ, XY_, XX))
    f = Figure(width_in=3.2, height_in=2.0)
    f.poly([R, S, T])
    f.poly([X, Y, Z])
    f.dots([R, S, T, X, Y, Z])
    f.label(R, "R", direction=(-1, -0.4))
    f.label(S, "S", direction=(1, -0.6))
    f.label(T, "T", direction=(0, 1))
    f.label(Z, "Z", direction=(-0.6, 1))
    f.label(Y, "Y", direction=(-0.6, -1))
    f.label(X, "X", direction=(1, 0.3))
    f.side_label(R, S, "6", T, size=10)
    f.side_label(S, T, "8", R, size=10)
    f.side_label(Z, Y, "9", X, size=10)
    f.angle_label(R, S, T, "50°", dist=0.38, size=9)
    f.angle_label(T, R, S, "35°", dist=0.62, size=9)
    f.angle_label(Y, X, Z, "95°", dist=0.3, size=9)
    f.angle_label(Z, X, Y, "50°", dist=0.42, size=9)
    return f


# ---------------------------------------------------------------- Problem 8: triangle DOG and triangle CAT
def _tri(a_deg, b_deg, base):
    """Base from (0, 0) to (base, 0); a_deg at the left vertex, b_deg at the right vertex."""
    A, B = P((0, 0), (base, 0))
    t = base * np.sin(np.radians(b_deg)) / np.sin(np.radians(180 - a_deg - b_deg))
    return A, B, A + t * np.array([np.cos(np.radians(a_deg)), np.sin(np.radians(a_deg))])


@figure("Unit 3 Review_dogcat")
def dogcat() -> Figure:
    D, O, G = _tri(40, 75, 4.8)                          # angle D = 40, angle O = 75, so angle G = 65
    C, A, T = _tri(65, 75, 3.0)                          # drawn for x = 75: angle C = 65, angle A = 75, angle T = 40
    C, A, T = translate([C, A, T], (7.4, 0))
    assert _close(angle_deg(D, O, G), 40) and _close(angle_deg(O, D, G), 75) and _close(angle_deg(G, D, O), 65)
    assert _close(angle_deg(C, A, T), 65) and _close(angle_deg(A, C, T), 75) and _close(angle_deg(T, C, A), 40)
    assert_distinct([40, 65, 75])
    assert similarity_ratio([D, O, G], [T, A, C]) is not None
    k = 0.38
    D, O, G, C, A, T = (p * k for p in (D, O, G, C, A, T))
    f = Figure(width_in=3.4, height_in=1.4)
    f.poly([D, O, G])
    f.poly([C, A, T])
    f.dots([D, O, G, C, A, T])
    for p, n, d in ((D, "D", (-1, -0.4)), (O, "O", (0.5, -1)), (G, "G", (0, 1)),
                    (C, "C", (-0.5, -1)), (A, "A", (1, -0.4)), (T, "T", (0, 1))):
        f.label(p, n, direction=d)
    for v, p1, p2 in ((D, O, G), (O, D, G), (C, A, T), (A, C, T)):
        f.arc(v, p1, p2, r=0.16)
    f.angle_label(D, O, G, "40°", dist=0.6, size=10)
    f.angle_label(O, D, G, "75°", dist=0.4, size=10)
    f.angle_label(C, A, T, "65°", dist=0.36, size=10)
    f.angle_label(A, C, T, "$x°$", dist=0.3, size=10)
    return f


# ---------------------------------------------------------------- Problem 9: P on KL, Q on KM (no marks)
@figure("Unit 3 Review_splitter")
def splitter() -> Figure:
    K, L, M = P((1.2, 2.6), (0, 0), (4, 0))
    Pp, Q = K + (L - K) * 0.4, K + (M - K) * 0.4
    f = Figure(width_in=1.8, height_in=1.25)
    f.poly([K, L, M])
    f.seg(Pp, Q)
    f.dots([K, L, M, Pp, Q])
    f.label(K, "K", direction=(0, 1))
    f.label(L, "L", direction=(-1, -0.4))
    f.label(M, "M", direction=(1, -0.4))
    f.label(Pp, "P", direction=(-1, 0.2))
    f.label(Q, "Q", direction=(1, 0.3))
    return f


# ---------------------------------------------------------------- Problem 10: right triangle ACB, altitude CD
AL_A, AL_D, AL_B, AL_C = P((0, 0), (16, 0), (25, 0), (16, 12))
assert _close(angle_deg(AL_C, AL_A, AL_B), 90)
assert _close(dist(AL_A, AL_C), 20) and _close(dist(AL_C, AL_B), 15)
assert _close(similarity_ratio([AL_A, AL_D, AL_C], [AL_C, AL_D, AL_B]), 0.75)
assert_lengths([(AL_A, AL_D, 16), (AL_D, AL_B, 9), (AL_C, AL_D, 12)])


@figure("Unit 3 Review_altitude")
def altitude() -> Figure:
    k = 0.11
    A, D, B, C = (p * k for p in (AL_A, AL_D, AL_B, AL_C))
    f = Figure(width_in=2.8, height_in=1.45)
    f.poly([A, B, C])
    f.seg(C, D)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, -0.3))
    f.label(B, "B", direction=(1, -0.3))
    f.label(D, "D", direction=(0, -1))
    f.label(C, "C", direction=(0, 1))
    f.right_angle(C, A, B, size=0.13)
    f.right_angle(D, B, C, size=0.13)
    f.side_label(A, D, "16", C, size=10)
    f.side_label(D, B, "9", C, size=10)
    f.text((C + D) / 2 + P(-0.15, 0), "$h$", size=11)
    return f

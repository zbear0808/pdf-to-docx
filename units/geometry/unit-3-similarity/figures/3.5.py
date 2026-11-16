"""Lesson 3.5 figures: the midsegment and the 2/3 splitter. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import Figure, P, assert_lengths, dilate, dist, figure, midpoint, similarity_ratio


def _parallel(a, b, c, d, tol=1e-9) -> bool:
    u, v = np.asarray(b) - np.asarray(a), np.asarray(d) - np.asarray(c)
    return abs(u[0] * v[1] - u[1] * v[0]) < tol * max(1.0, np.linalg.norm(u) * np.linalg.norm(v))


def _chevron(f: Figure, a, b, n=1, size=0.13, layer="given"):
    """Parallel-line arrow mark(s) at the middle of segment ab, pointing from a to b."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = (b - a) / np.linalg.norm(b - a)
    nrm = np.array([-u[1], u[0]])
    m = (a + b) / 2
    for k in range(n):
        tip = m + u * (k - (n - 1) / 2) * 0.7 * size + u * size / 2
        f.seg(tip, tip - u * size + nrm * size * 0.8, layer=layer, lw=1.1)
        f.seg(tip, tip - u * size - nrm * size * 0.8, layer=layer, lw=1.1)


# Warm-up and Problem 6: triangle ABC with midpoints M (AB), L (BC), N (AC)
A, B, C = P((0, 0), (4.4, 0), (1.6, 3.0))
M, L, N = midpoint(A, B), midpoint(B, C), midpoint(A, C)
for small, center in (([A, M, N], A), ([M, B, L], B), ([N, L, C], C)):
    big = dilate(small, 2, center)
    assert np.isclose(similarity_ratio(small, big), 2)
assert np.allclose(dilate([M, N], 2, A), [B, C]) and np.allclose(dilate([M, L], 2, B), [A, C])
assert np.allclose(dilate([N, L], 2, C), [A, B])
assert _parallel(M, N, B, C) and _parallel(M, L, A, C) and _parallel(N, L, A, B)
assert np.isclose(dist(B, C), 2 * dist(M, N))


@figure("3.5_midpoints")
def midpoints() -> Figure:
    f = Figure(width_in=2.5, height_in=1.8)
    f.poly([A, B, C])
    f.poly([M, L, N])
    f.dots([A, B, C, M, L, N])
    f.ticks(A, M, 1)
    f.ticks(M, B, 1)
    f.ticks(B, L, 2)
    f.ticks(L, C, 2)
    f.ticks(C, N, 3)
    f.ticks(N, A, 3)
    f.label_poly([A, B, C], "ABC")
    f.label(M, "M", direction=(0, -1))
    f.label(L, "L", direction=(1, 0.5))
    f.label(N, "N", direction=(-1, 0.4))
    return f


# Problems 1-3: M, N midpoints of AB, AC. A dilation from A with k = 2 takes AMN onto ABC
def _amn_given(f: Figure):
    f.poly([A, B, C])
    f.seg(M, N)
    f.dots([A, B, C, M, N])
    f.ticks(A, M, 1)
    f.ticks(M, B, 1)
    f.ticks(A, N, 2)
    f.ticks(N, C, 2)
    f.label_poly([A, B, C], "ABC")
    f.label(M, "M", direction=(0, -1))
    f.label(N, "N", direction=(-1, 0.4))


@figure("3.5_amn_plain")
def amn_plain() -> Figure:
    f = Figure(width_in=2.5, height_in=1.8)
    _amn_given(f)
    return f


@figure("3.5_amn")
def amn() -> Figure:
    f = Figure(width_in=2.5, height_in=1.8)
    _amn_given(f)
    _chevron(f, N, M, layer="answer")
    _chevron(f, C, B, layer="answer")
    f.arc(M, A, N, n=1, r=0.32, layer="answer")
    f.arc(B, A, C, n=1, r=0.32, layer="answer")
    f.arc(N, A, M, n=2, r=0.28, layer="answer")
    f.arc(C, A, B, n=2, r=0.28, layer="answer")
    return f


# Problem 4: M is 2/3 of the way from A to B, N is 2/3 of the way from A to C
TA, TB, TC = P((4.2, 3.0), (0, 3.0), (1.7, 0))
TM, TN = TA + 2 / 3 * (TB - TA), TA + 2 / 3 * (TC - TA)
assert np.allclose(dilate([TM, TN], 1.5, TA), [TB, TC])
assert _parallel(TM, TN, TB, TC) and np.isclose(dist(TM, TN), 2 / 3 * dist(TB, TC))


@figure("3.5_two_thirds")
def two_thirds() -> Figure:
    f = Figure(width_in=2.4, height_in=1.8)
    f.poly([TA, TB, TC])
    f.seg(TM, TN)
    f.dots([TA, TB, TC, TM, TN])
    f.label(TA, "A", direction=(0.4, 1))
    f.label(TB, "B", direction=(-0.4, 1))
    f.label(TC, "C", direction=(0, -1))
    f.label(TM, "M", direction=(0, 1))
    f.label(TN, "N", direction=(1, -0.3))
    _chevron(f, TN, TM, layer="answer")
    _chevron(f, TC, TB, layer="answer")
    return f


# Exit ticket: AN = 1, NC = 2, AM = 1.8, MB = 3.6, CB = 6
EC, EB = P((0, 0), (6, 0))
ex = (3 ** 2 - 5.4 ** 2 + 6 ** 2) / 12
EA = np.array((ex, np.sqrt(9 - ex ** 2)))
EN, EM = EA + (EC - EA) / 3, EA + (EB - EA) / 3
assert np.isclose(dist(EA, EC), 3) and np.isclose(dist(EA, EB), 5.4) and np.isclose(dist(EA, EN), 1)
assert np.isclose(dist(EA, EM), 1.8) and np.isclose(dist(EM, EN), 2) and _parallel(EN, EM, EC, EB)
assert_lengths([(EA, EN, 1), (EN, EC, 2), (EA, EM, 1.8), (EM, EB, 3.6), (EC, EB, 6), (EN, EM, 2)])


@figure("3.5_exit")
def exit_fig() -> Figure:
    f = Figure(width_in=2.5, height_in=1.5)
    tri = [EA, EB, EC]
    f.poly(tri)
    f.seg(EN, EM)
    f.dots([EA, EB, EC, EM, EN])
    f.label(EA, "A", direction=(0, 1))
    f.label(EB, "B", direction=(1, -0.3))
    f.label(EC, "C", direction=(-1, -0.3))
    f.label(EN, "N", direction=(-1, 0.2))
    f.label(EM, "M", direction=(0.4, 1))
    cen = np.mean(tri, axis=0)
    f.side_label(EA, EN, "1", cen, size=11)
    f.side_label(EN, EC, "2", cen, size=11)
    f.side_label(EA, EM, "1.8", cen, size=11)
    f.side_label(EM, EB, "3.6", cen, size=11)
    f.side_label(EC, EB, "6", cen, size=11)
    f.side_label(EN, EM, "MN = 2", EA, layer="answer", size=11, offset_pt=9)
    _chevron(f, EN, EM, layer="answer", size=0.18)
    _chevron(f, EC, EB, layer="answer", size=0.18)
    return f


# CYU 1: midsegment MN = x + 2, BC = 3x - 4  ->  3x - 4 = 2(x + 2), x = 8
CYU_X = 8
assert 3 * CYU_X - 4 == 2 * (CYU_X + 2)


@figure("3.5_cyu")
def cyu() -> Figure:
    f = Figure(width_in=3.0, height_in=2.1)
    f.poly([A, B, C])
    f.seg(M, N)
    f.dots([A, B, C, M, N])
    f.ticks(A, M, 1)
    f.ticks(M, B, 1)
    f.ticks(A, N, 2)
    f.ticks(N, C, 2)
    f.label_poly([A, B, C], "ABC")
    f.label(M, "M", direction=(0, -1))
    f.label(N, "N", direction=(-1, 0.4))
    f.text(midpoint(M, N) + 0.62 * np.array((0.73, 0.68)), "$x + 2$", size=14)
    f.side_label(B, C, "3x - 4", A, size=14, offset_pt=20, italic=True)
    return f


# Practice 4: lines l and m; images of m under a dilation are parallel to m (or m itself)
O = np.array((0, 0), float)
UM = np.array((1, 0.85)) / np.linalg.norm((1, 0.85))
UL = np.array((1, -0.6)) / np.linalg.norm((1, -0.6))
NRM = np.array((-UM[1], UM[0]))
n_line = (O + 0.9 * NRM - 1.6 * UM, O + 0.9 * NRM + 1.4 * UM)
p_line = (O - 0.9 * NRM - 1.4 * UM, O - 0.9 * NRM + 1.6 * UM)
assert _parallel(*n_line, -2 * UM, 2 * UM) and _parallel(*p_line, -2 * UM, 2 * UM)


@figure("3.5_lines")
def lines() -> Figure:
    f = Figure(width_in=2.3, height_in=1.9)
    f.seg(-2 * UM, 2 * UM)
    f.seg(-2 * UL, 2 * UL)
    f.label(1.8 * UM, "m", direction=(1, -0.6), offset_pt=8)
    f.label(-1.8 * UL, r"\ell", direction=(0, 1), offset_pt=8)
    f.seg(*n_line, layer="answer")
    f.seg(*p_line, layer="answer")
    f.label(n_line[1], "n", layer="answer", direction=(0, 1), offset_pt=8)
    f.label(p_line[1], "p", layer="answer", direction=(1, 0), offset_pt=8)
    return f

"""Lesson 3.5 figures: the midsegment and the 2/3 splitter. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (Figure, P, assert_dilation, assert_lengths, dilate, dist, figure, is_parallel,
                                    midpoint, similarity_ratio)


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


# Warm-up: PQ and its image P'Q' after a dilation with center O and scale factor 2 (PQ = 1.5, so P'Q' = 3)
WO = np.array((0.0, 0.0))
WP = np.array((0.55, 1.35))
WQ = WP + 1.5 * np.array((0.6, -0.8))
WP2, WQ2 = dilate([WP, WQ], 2, WO)
assert_dilation(WO, [WP, WQ], [WP2, WQ2], 2)
assert_lengths([(WP, WQ, 1.5), (WP2, WQ2, 3)])
assert is_parallel(WP, WQ, WP2, WQ2)


@figure("3.5_warmup")
def warmup() -> Figure:
    f = Figure(width_in=1.9, height_in=1.8)
    f.seg(WP, WQ)
    f.seg(WP2, WQ2)
    f.dots([WO, WP, WQ, WP2, WQ2])
    f.label(WO, "O", direction=(-1, -0.6))
    f.label(WP, "P", direction=(-1, 0.2))
    f.label(WQ, "Q", direction=(0, -1))
    f.label(WP2, "P'", direction=(-0.6, 1))
    f.label(WQ2, "Q'", direction=(1, -0.4))
    f.side_label(WP, WQ, "1.5", midpoint(WP2, WQ2), size=11)
    return f


# Problem 1: M, N midpoints of AB, AC. A dilation from A with k = 2 takes AMN onto ABC
A, B, C = P((0, 0), (4.4, 0), (1.6, 3.0))
M, N = midpoint(A, B), midpoint(A, C)
assert np.allclose(dilate([M, N], 2, A), [B, C])
assert np.isclose(similarity_ratio([A, M, N], [A, B, C]), 2)
assert _parallel(M, N, B, C) and np.isclose(dist(B, C), 2 * dist(M, N))


@figure("3.5_amn")
def amn() -> Figure:
    f = Figure(width_in=2.5, height_in=1.8)
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
    _chevron(f, N, M, layer="answer")
    _chevron(f, C, B, layer="answer")
    return f


# Problem 2: M is 2/3 of the way from A to B, N is 2/3 of the way from A to C
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

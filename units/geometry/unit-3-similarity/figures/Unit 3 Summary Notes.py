"""Unit 3 Summary Notes figures (reference sheet: given layer only, black)."""
import numpy as np

from lesson_builder.figures import (P, Figure, angle_deg, assert_lengths, dilate, dist, figure, midpoint, rotate,
                                    similarity_ratio)

S = "Unit 3 Summary Notes"


def _parallel(a, b, c, d) -> bool:
    u, v = np.asarray(b) - np.asarray(a), np.asarray(d) - np.asarray(c)
    return abs(u[0] * v[1] - u[1] * v[0]) < 1e-9 * max(1.0, np.linalg.norm(u) * np.linalg.norm(v))


def _tri(a, b, c):
    """Triangle with side lengths BC = a, CA = b, AB = c: A at the origin, B on the x-axis."""
    x = (b * b + c * c - a * a) / (2 * c)
    return P((0, 0), (c, 0), (x, np.sqrt(b * b - x * x)))


# 3.1: dilation with center P, k = 2
P31 = np.array([0.0, 0.0])
T31 = P((1.5, 0.2), (2.1, 0.5), (1.6, 1.1))
T31 = T31.mean(0) + 1.5 * (T31 - T31.mean(0))
I31 = dilate(T31, 2, P31)
assert np.isclose(similarity_ratio(T31, I31), 2)


@figure(f"{S}_3.1")
def fig_31() -> Figure:
    f = Figure(width_in=2.4, height_in=1.6)
    for a in I31:
        f.seg(P31, a, dashed=True, lw=0.8)
    f.poly(T31)
    f.poly(I31)
    f.dots([P31, *T31, *I31])
    f.label(P31, "P", direction=(-1, 0))
    f.label_poly(T31, "ABC", overrides={"A": (0, -1), "B": (0.2, -1), "C": (-1, 0.4)})
    f.label_poly(I31, ["A'", "B'", "C'"], overrides={"A'": (0.7, -1)}, offset_pt=12)
    return f


# 3.3: lengths scale by k (AB = 4, BC = 5, CA = 7 to 8, 10, 14; not a right triangle)
T33 = _tri(5, 7, 4)
I33 = dilate(T33, 2, T33[0]) + np.array([9.5, 0.0])
assert np.isclose(similarity_ratio(T33, I33), 2)
assert_lengths([(T33[0], T33[1], 4), (T33[1], T33[2], 5), (T33[2], T33[0], 7),
                (I33[0], I33[1], 8), (I33[1], I33[2], 10), (I33[2], I33[0], 14)])


@figure(f"{S}_3.3")
def fig_33() -> Figure:
    f = Figure(width_in=2.6, height_in=1.8)
    for t, names, lens in ((T33, "ABC", ("4", "5", "7")), (I33, ["A'", "B'", "C'"], ("8", "10", "14"))):
        ctr = t.mean(0)
        f.poly(t)
        f.label_poly(t, names)
        f.side_label(t[0], t[1], lens[0], ctr)
        f.side_label(t[1], t[2], lens[1], ctr)
        f.side_label(t[2], t[0], lens[2], ctr)
    return f


# 3.4: line m (not through P) goes to a parallel line; line n through P stays put
P34 = np.array([0.0, 0.0])
D, E = P((1.0, -0.6), (0.6, 1.0))
D2, E2 = dilate([D, E], 2, P34)
assert _parallel(D, E, D2, E2)


@figure(f"{S}_3.4")
def fig_34() -> Figure:
    f = Figure(width_in=2.3, height_in=2.0)
    u = (E - D) / np.linalg.norm(E - D)
    f.seg(D - 0.5 * u, E + 0.9 * u)
    f.seg(D2 - 0.5 * u, E2 + 0.9 * u)
    n_dir = np.array([1.0, 0.15]) / np.linalg.norm([1.0, 0.15])
    f.seg(P34 - 0.6 * n_dir, P34 + 3.2 * n_dir)
    f.seg(P34, D2, dashed=True, lw=0.8)
    f.seg(P34, E2, dashed=True, lw=0.8)
    f.dots([P34, D, E, D2, E2])
    f.label(P34, "P", direction=(-0.3, 1))
    f.label(D, "D", direction=(-1, -0.4))
    f.label(E, "E", direction=(-1, 0.3))
    f.label(D2, "D'", direction=(1, -0.3))
    f.label(E2, "E'", direction=(1, 0.3))
    f.label(E + 0.9 * u, "m", direction=(-1, 0))
    f.label(E2 + 0.9 * u, "m'", direction=(1, 0))
    f.label(P34 + 3.2 * n_dir, "n", direction=(1, 0))
    return f


# 3.5: midsegment MN, half of BC
A5, B5, C5 = P((1.4, 2.8), (0, 0), (4.2, 0))
M5, N5 = midpoint(A5, B5), midpoint(A5, C5)
assert _parallel(M5, N5, B5, C5) and np.isclose(dist(B5, C5), 2 * dist(M5, N5))
assert_lengths([(M5, N5, 5), (B5, C5, 10)])


@figure(f"{S}_3.5")
def fig_35() -> Figure:
    f = Figure(width_in=2.3, height_in=1.6)
    f.poly([A5, B5, C5])
    f.seg(M5, N5)
    f.dots([A5, B5, C5, M5, N5])
    f.ticks(A5, M5, 1)
    f.ticks(M5, B5, 1)
    f.ticks(A5, N5, 2)
    f.ticks(N5, C5, 2)
    f.parallel_marks(M5, N5)
    f.parallel_marks(B5, C5)
    f.label_poly([A5, B5, C5], "ABC")
    f.label(M5, "M", direction=(-1, 0.2))
    f.label(N5, "N", direction=(1, 0.2))
    f.side_label(M5, N5, "5", A5, offset_pt=-8)
    f.side_label(B5, C5, "10", A5)
    return f


# 3.6: ABC ~ DEF (rotate 90 degrees, then dilate by 1.5)
T36 = P((0, 0), (2.0, 0), (0.6, 1.3))
I36 = dilate(rotate(T36, 90), 1.5) + np.array([5.0, 0.0])
assert np.isclose(similarity_ratio(T36, I36), 1.5)
for k in range(3):
    assert np.isclose(angle_deg(T36[k], T36[k - 1], T36[(k + 1) % 3]), angle_deg(I36[k], I36[k - 1], I36[(k + 1) % 3]))


@figure(f"{S}_3.6")
def fig_36() -> Figure:
    f = Figure(width_in=2.7, height_in=1.8)
    for t, names, r in ((T36, "ABC", 0.3), (I36, "DEF", 0.45)):
        f.poly(t)
        f.label_poly(t, names)
        for k in range(3):
            f.arc(t[k], t[k - 1], t[(k + 1) % 3], n=k + 1, r=r)
    return f


# 3.7: corresponding sides proportional, k = 3
T37 = _tri(5, 6, 3)            # AB = 3, BC = 5, CA = 6
I37 = dilate(T37, 3, T37[0]) + np.array([9.0, 0.0])
assert np.isclose(similarity_ratio(T37, I37), 3)
assert_lengths([(T37[0], T37[1], 3), (T37[1], T37[2], 5), (T37[2], T37[0], 6),
                (I37[0], I37[1], 9), (I37[1], I37[2], 15), (I37[2], I37[0], 18)])


@figure(f"{S}_3.7")
def fig_37() -> Figure:
    f = Figure(width_in=2.8, height_in=1.8)
    for t, names, lens in ((T37, "ABC", ("3", "5", "6")), (I37, "DEF", ("9", "15", "18"))):
        ctr = t.mean(0)
        f.poly(t)
        f.label_poly(t, names)
        f.side_label(t[0], t[1], lens[0], ctr)
        f.side_label(t[1], t[2], lens[1], ctr)
        f.side_label(t[2], t[0], lens[2], ctr)
    return f


# 3.9: bowtie. DA || BC, so angle A = angle C; vertical angles at E. DEA ~ BEC
E9 = np.array([0.0, 0.0])
D9, A9 = P((-2.0, 1.4), (-2.0, -1.1))
B9, C9 = dilate([D9, A9], -0.6, E9)
assert np.isclose(angle_deg(A9, D9, E9), angle_deg(C9, B9, E9))
assert np.isclose(angle_deg(E9, D9, A9), angle_deg(E9, B9, C9))


@figure(f"{S}_3.9")
def fig_39() -> Figure:
    f = Figure(width_in=2.4, height_in=1.6)
    f.poly([D9, E9, A9])
    f.poly([B9, E9, C9])
    f.dots([D9, E9, A9, B9, C9])
    f.arc(A9, D9, E9, n=1, r=0.35)
    f.arc(C9, B9, E9, n=1, r=0.3)
    f.arc(E9, D9, A9, n=2, r=0.28)
    f.arc(E9, B9, C9, n=2, r=0.28)
    f.label(D9, "D", direction=(-1, 0.3))
    f.label(A9, "A", direction=(-1, -0.3))
    f.label(E9, "E", direction=(0, 1))
    f.label(B9, "B", direction=(1, -0.3))
    f.label(C9, "C", direction=(1, 0.3))
    return f


# 3.11: side splitter. DE || AC, BD = 4, DA = 2, BE = 6, EC = 3
B11, A11 = P((0, 0), (1.2, 2.7))
C11 = np.array([4.0, 0.6]) / np.linalg.norm([4.0, 0.6]) * 1.5 * dist(B11, A11)   # BA : BC = 6 : 9
D11, E11 = dilate([A11, C11], 2 / 3, B11)
assert _parallel(D11, E11, A11, C11) and np.isclose(4 / 2, 6 / 3)
assert_lengths([(B11, D11, 4), (D11, A11, 2), (B11, E11, 6), (E11, C11, 3)])


@figure(f"{S}_3.11")
def fig_311() -> Figure:
    f = Figure(width_in=2.4, height_in=1.7)
    ctr = np.array([1.5, 1.5])
    f.poly([B11, A11, C11])
    f.seg(D11, E11)
    f.dots([A11, B11, C11, D11, E11])
    f.parallel_marks(D11, E11)
    f.parallel_marks(A11, C11)
    f.label(A11, "A", direction=(0, 1))
    f.label(B11, "B", direction=(-1, -0.4))
    f.label(C11, "C", direction=(1, 0))
    f.label(D11, "D", direction=(-1, 0.2))
    f.label(E11, "E", direction=(0.3, -1))
    f.side_label(B11, D11, "4", ctr)
    f.side_label(D11, A11, "2", ctr)
    f.side_label(B11, E11, "6", ctr, offset_pt=9)
    f.side_label(E11, C11, "3", ctr, offset_pt=9)
    return f


# 3.13: right triangle ABC (right angle at C), altitude CD
A13, B13 = P((0, 0), (5.0, 0))
C13 = np.array([3.2, np.sqrt(3.2 * 1.8)])
D13 = np.array([3.2, 0.0])
assert np.isclose(angle_deg(C13, A13, B13), 90)
assert np.isclose(dist(A13, C13) ** 2 + dist(B13, C13) ** 2, dist(A13, B13) ** 2)


@figure(f"{S}_3.13")
def fig_313() -> Figure:
    f = Figure(width_in=2.5, height_in=1.4)
    f.poly([A13, B13, C13])
    f.seg(C13, D13)
    f.dots([A13, B13, C13, D13])
    f.right_angle(C13, A13, B13)
    f.right_angle(D13, B13, C13)
    f.label(A13, "A", direction=(-1, -0.3))
    f.label(B13, "B", direction=(1, -0.3))
    f.label(C13, "C", direction=(0, 1))
    f.label(D13, "D", direction=(0, -1))
    ctr = np.array([3.0, 0.6])
    f.side_label(A13, C13, "b", ctr, italic=True)
    f.side_label(B13, C13, "a", ctr, italic=True)
    f.label(np.array([2.2, 0.0]), "c", direction=(0, -1), italic=True)
    return f

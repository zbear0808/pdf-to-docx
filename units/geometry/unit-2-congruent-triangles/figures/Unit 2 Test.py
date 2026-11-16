"""Figures for assessment "Unit 2 Test" (assessments/Unit 2 Test.yaml).
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Shapes follow the source drawings in UNIT 2 TEST 2025-26 (first copy), redrawn because the source images print
under 150 dpi and two of them use colour (blue dots in #5, green angle arcs in #8).
Loop: uv run lesson-builder figs units/geometry/unit-2-congruent-triangles -l "Unit 2 Test"
"""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, dist, figure, is_parallel, is_rigid_image, mark_congruent,
                                    midpoint, needs_reflection, reflect, rotate, translate)

S = 'Unit 2 Test'


def _seg_cross(a, b, c, d):
    """Point where segment ab meets segment cd."""
    a, b, c, d = (np.asarray(x, float) for x in (a, b, c, d))
    t = np.linalg.solve(np.column_stack([b - a, c - d]), c - a)
    return a + t[0] * (b - a)


# ---------------------------------------------------------------- 2: key sketch, GRT = MPN, TG and MN marked
_GRT = P((0, 0), (1.6, 0), (0.5, 1.2))
_MPN = translate(_GRT, (2.9, 0))
assert is_rigid_image(_GRT, _MPN)
assert np.isclose(dist(_GRT[2], _GRT[0]), dist(_MPN[2], _MPN[0]))   # TG = NM


@figure(f"{S}_q2")
def q2() -> Figure:
    """Key only (draw box): a sample sketch of triangles GRT and MPN with TG and MN marked congruent."""
    L = "answer"
    f = Figure(width_in=2.6, height_in=1.05)
    for tri, names in ((_GRT, "GRT"), (_MPN, "MPN")):
        f.poly(tri, layer=L)
        f.dots(tri, layer=L, size=10)
        f.label_poly(tri, names, layer=L)
    f.ticks(_GRT[2], _GRT[0], n=2, layer=L, size=0.14)
    f.ticks(_MPN[2], _MPN[0], n=2, layer=L, size=0.14)
    return f


# ---------------------------------------------------------------- 3: JKLM with diagonal KL
K3, M3, J3, L3 = P((0, 0), (3, 0), (1, 1), (4, 1))
assert np.isclose(dist(J3, L3), dist(M3, K3)) and np.isclose(dist(J3, K3), dist(M3, L3))
assert np.isclose(angle_deg(J3, K3, L3), angle_deg(M3, L3, K3))


@figure(f"{S}_q3")
def q3() -> Figure:
    f = Figure(width_in=2.7, height_in=1.25)
    f.poly([J3, L3, M3, K3])
    f.seg(K3, L3)
    f.dots([J3, K3, L3, M3], size=10)
    f.label(J3, "J", direction=(-0.3, 1))
    f.label(L3, "L", direction=(1, 0.3))
    f.label(K3, "K", direction=(-1, -0.3))
    f.label(M3, "M", direction=(0.3, -1))
    mark_congruent(f, [((J3, L3), (M3, K3)), ((J3, K3), (M3, L3)), ((J3, K3, L3), (M3, L3, K3))], size=0.13,
                   r=0.28)
    return f


# ---------------------------------------------------------------- 4: DEF onto CBA (SSS, opposite orientation)
D4, E4, F4 = P((0, 0), (1.84, 0.70), (1.38, -0.16))
C4, B4, A4 = translate(rotate(reflect([D4, E4, F4], (0, 0), (1, 0)), 70.3, about=(0, 0)), (-0.9, 0))
assert is_rigid_image([D4, E4, F4], [C4, B4, A4])
assert needs_reflection([D4, E4, F4], [C4, B4, A4])   # translate + rotate alone can't do it


@figure(f"{S}_q4")
def q4() -> Figure:
    f = Figure(width_in=2.3, height_in=2.0)
    for tri, names in (([D4, E4, F4], "DEF"), ([C4, B4, A4], "CBA")):
        f.poly(tri)
        f.dots(tri, size=10)
        f.label_poly(tri, names)
    mark_congruent(f, [((F4, D4), (A4, C4)), ((F4, E4), (A4, B4)), ((E4, D4), (B4, C4))], size=0.11)
    return f


# ---------------------------------------------------------------- 5: kite CADB, reflect across AB
A5, B5, C5, D5 = P((0, 0.6), (0, -0.8), (-2, 0.3), (2, 0.3))
assert np.allclose(reflect(C5, A5, B5)[0], D5)
assert np.isclose(dist(C5, A5), dist(D5, A5)) and np.isclose(dist(C5, B5), dist(D5, B5))


@figure(f"{S}_q5")
def q5() -> Figure:
    f = Figure(width_in=2.3, height_in=1.25)
    f.poly([C5, A5, D5, B5])
    f.seg(A5, B5)
    f.dots([A5, B5, C5, D5], size=10)
    f.label(A5, "A", direction=(0, 1))
    f.label(B5, "B", direction=(0, -1))
    f.label(C5, "C", direction=(-1, 0))
    f.label(D5, "D", direction=(1, 0))
    mark_congruent(f, [((C5, A5), (D5, A5)), ((C5, B5), (D5, B5))], size=0.12)
    return f


# ---------------------------------------------------------------- 6: parallelogram RSTU, diagonals meet at A
U6, T6, S6, R6 = P((0, 0), (2.8, 0), (3.4, 1.4), (0.6, 1.4))
A6 = _seg_cross(R6, T6, S6, U6)
assert is_parallel(R6, S6, U6, T6) and is_parallel(R6, U6, S6, T6)
assert np.allclose(A6, midpoint(R6, T6)) and np.allclose(A6, midpoint(S6, U6))


@figure(f"{S}_q6")
def q6() -> Figure:
    f = Figure(width_in=2.1, height_in=1.3)
    f.poly([R6, S6, T6, U6])
    f.seg(R6, T6)
    f.seg(S6, U6)
    f.dots([R6, S6, T6, U6, A6], size=10)
    f.label_poly([R6, S6, T6, U6], "RSTU")
    f.label(A6, "A", direction=(0, -1))
    return f


# ---------------------------------------------------------------- 7: parallelogram ABCD, angle A = 30
A7, D7 = P((0, 0), (3.6, 0))
B7 = 2.2 * np.array([np.cos(np.radians(30)), np.sin(np.radians(30))])
C7 = B7 + D7
assert np.isclose(angle_deg(A7, B7, D7), 30) and np.isclose(angle_deg(D7, A7, C7), 150)


@figure(f"{S}_q7")
def q7() -> Figure:
    f = Figure(width_in=2.4, height_in=1.15)
    f.poly([A7, B7, C7, D7])
    f.label_poly([A7, B7, C7, D7], "ABCD")
    mark_congruent(f, [((A7, B7), (C7, D7)), ((B7, C7), (D7, A7))], size=0.13)
    f.arc(A7, D7, B7, r=0.5)
    return f


# ---------------------------------------------------------------- 8: bent figures ABC and DEF (SAS marks)
def _polar(p, r, deg):
    return np.asarray(p, float) + r * np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])


B8 = np.array((1.2, 2.0))
A8, C8 = _polar(B8, 1.6, 125), _polar(B8, 1.8, 241)
_ABC = np.array([A8, B8, C8])
D8, E8, F8 = translate(rotate(reflect(_ABC, B8, B8 + (0, 1)), -14, about=B8), (1.75, 0.45))
assert is_rigid_image(_ABC, [D8, E8, F8]) and needs_reflection(_ABC, [D8, E8, F8])
assert np.isclose(angle_deg(B8, A8, C8), angle_deg(E8, D8, F8))


@figure(f"{S}_q8")
def q8() -> Figure:
    f = Figure(width_in=2.3, height_in=2.1)
    for pts, names in ((_ABC, "ABC"), ([D8, E8, F8], "DEF")):
        f.poly(pts, closed=False)
        f.dots(pts, size=10)
    f.label(A8, "A", direction=(-0.5, 1))
    f.label(B8, "B", direction=(1, 0))
    f.label(C8, "C", direction=(-0.5, -1))
    f.label(D8, "D", direction=(0.5, 1))
    f.label(E8, "E", direction=(-1, 0))
    f.label(F8, "F", direction=(0.5, -1))
    mark_congruent(f, [((A8, B8), (D8, E8)), ((B8, C8), (E8, F8)), ((B8, A8, C8), (E8, D8, F8))], size=0.13,
                   r=0.3)
    return f


# ---------------------------------------------------------------- 9: O, K, C, N, Y (ASA with vertical angles)
O9, K9, C9, N9 = P((0, 2), (4, 2), (1.3, 0), (2.7, 0))
Y9 = _seg_cross(O9, N9, K9, C9)
assert np.isclose(dist(C9, Y9), dist(N9, Y9))
assert np.isclose(angle_deg(C9, O9, Y9), angle_deg(N9, K9, Y9))
assert is_rigid_image([Y9, K9, N9], [Y9, O9, C9])   # YKN = YOC


@figure(f"{S}_q9")
def q9() -> Figure:
    f = Figure(width_in=2.1, height_in=1.4)
    f.seg(O9, K9)
    for a, b in ((O9, C9), (O9, N9), (K9, C9), (K9, N9)):
        f.seg(a, b)
    f.label(O9, "O", direction=(-1, 0.3))
    f.label(K9, "K", direction=(1, 0.3))
    f.label(C9, "C", direction=(0, -1))
    f.label(N9, "N", direction=(0, -1))
    f.label(Y9, "Y", direction=(0, -1))
    f.angle_label(Y9, O9, C9, "1", dist=0.3)
    f.angle_label(Y9, K9, N9, "2", dist=0.3)
    return f

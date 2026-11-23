"""Figures for assessment "Unit 2 Test" (assessments/Unit 2 Test.yaml).
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Shapes follow the source drawings in UNIT 2 TEST 2025-26 (first copy), redrawn because the source images print
under 150 dpi and two of them use colour (blue dots in #5, green angle arcs in #8).
Names keep the source item numbers. Nov 19: old items 1 and 4 were cut (the _q4 figure is gone), so _q2 is item 1,
_q3 item 2, _q5 item 3, _q6 item 4, _q7 item 5, _q8 item 6, _q9 item 7. _q8 was redrawn with new letters.
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
    f.angle_label(A7, D7, B7, r'$30^\circ$', dist=1.05, size=10)   # Nov 19: the stem's 30 degrees, on the figure
    return f


# ---------------------------------------------------------------- 8: bent figures PQR and KLM (SAS marks)
# Nov 19: new letters and drawing. The old figures ABC and DEF had the names, SAS marks, and task of Lesson 2.5
# practice 1. PQR is a V (72 degrees at Q); KLM is its mirror image turned upside down, so a reflection is needed.
def _polar(p, r, deg):
    return np.asarray(p, float) + r * np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])


Q8 = np.array((0.9, 0.0))
P8, R8 = _polar(Q8, 1.5, 112), _polar(Q8, 1.9, 40)
_PQR = np.array([P8, Q8, R8])
K8, L8, M8 = translate(rotate(reflect(_PQR, Q8, Q8 + (0, 1)), 165, about=Q8), (3.0, 0.9))
assert is_rigid_image(_PQR, [K8, L8, M8]) and needs_reflection(_PQR, [K8, L8, M8])
assert np.isclose(angle_deg(Q8, P8, R8), 72) and np.isclose(angle_deg(L8, K8, M8), 72)
assert np.isclose(dist(P8, Q8), dist(K8, L8)) and np.isclose(dist(Q8, R8), dist(L8, M8))


@figure(f"{S}_q8")
def q8() -> Figure:
    f = Figure(width_in=2.25, height_in=1.45)
    for pts in (_PQR, [K8, L8, M8]):
        f.poly(pts, closed=False)
        f.dots(pts, size=10)
    f.label(P8, "P", direction=(-0.5, 1))
    f.label(Q8, "Q", direction=(0, -1))
    f.label(R8, "R", direction=(0.6, 1))
    f.label(K8, "K", direction=(-0.6, -1))
    f.label(L8, "L", direction=(0, 1))
    f.label(M8, "M", direction=(0.6, -1))
    mark_congruent(f, [((P8, Q8), (K8, L8)), ((Q8, R8), (L8, M8)), ((Q8, P8, R8), (L8, K8, M8))], size=0.13,
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

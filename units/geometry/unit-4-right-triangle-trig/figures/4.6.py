"""Figures for lesson "4.6" (lessons/4.6.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Lesson 4.10 redraws triangle END in its own file (4.10_7); nothing here is shared.
Loop: uv run lesson-builder figs <unit> -l "4.6" (0 errors, no label warnings).
"""
import math

import numpy as np

from lesson_builder.figures import Figure, angle_deg, assert_lengths, dist, figure

S = '4.6'
D = math.radians


def _tri(f, pts, names, layer="given", ra=None, ra_size=0.25, overrides=None):
    """Triangle outline, vertex dots, vertex names, and a right-angle mark at index ra."""
    pts = np.asarray(pts, dtype=float)
    f.poly(pts, layer=layer)
    f.dots(pts, layer=layer)
    f.label_poly(pts, names, layer=layer, overrides=overrides)
    if ra is not None:
        v = pts[ra]
        o = [pts[i] for i in range(3) if i != ra]
        assert abs(angle_deg(v, o[0], o[1]) - 90) < 1e-6
        f.right_angle(v, o[0], o[1], size=ra_size, layer=layer)


def _ang(f, v, p1, p2, deg, r, d, layer="given", size=None):
    assert abs(angle_deg(v, p1, p2) - deg) < 1e-6
    f.arc(v, p1, p2, r=r, layer=layer)
    f.angle_label(v, p1, p2, rf"${deg:g}^\circ$", dist=d, layer=layer, size=size)


def _out(f, a, b, center, text, layer="given", size=None, offset_pt=10):
    """Label at the midpoint of ab, pushed away from center (upright text, auto spot)."""
    m = (np.asarray(a, float) + np.asarray(b, float)) / 2
    d = m - np.asarray(center, float)
    f.label(m, text, layer=layer, direction=tuple(d / np.linalg.norm(d)), size=size,
            offset_pt=offset_pt, italic=False)


# Warm-up / Problem 1: right angle at G, GH = 3, angle J = 40, angle H = 50.
W_G = np.array((0.0, 0.0))
W_H = np.array((3.0, 0.0))
W_J = np.array((0.0, 3 / math.tan(D(40))))
W_Z = 3 / math.sin(D(40))
assert abs(W_J[1] - 3.5753) < 1e-4 and abs(W_Z - 4.6672) < 1e-4
assert abs(dist(W_J, W_H) - W_Z) < 1e-9 and round(W_Z, 1) == 4.7


@figure(f"{S}_warmup")
def warmup() -> Figure:
    f = Figure(width_in=2.4, height_in=2.6)
    _tri(f, [W_G, W_H, W_J], "GHJ", ra=0, ra_size=0.25)
    _ang(f, W_J, W_G, W_H, 40, 0.6, 1.0)
    _ang(f, W_H, W_G, W_J, 50, 0.5, 0.95)
    f.side_label(W_G, W_H, "3", W_J)
    f.side_label(W_J, W_H, "$z$", W_G)
    a = "answer"
    f.text((2.7, 2.55), "hypotenuse", layer=a, size=11)
    f.text((2.7, 2.15), r"$z \approx 4.7$", layer=a, size=11)
    f.text((-0.95, 1.79), "adjacent", layer=a, size=11)
    f.text((1.5, -0.75), "opposite", layer=a, size=11)
    return f


# QuickNotes: generic right triangle, theta at the right vertex.
V_R, V_T, V_A = np.array((0.0, 0.0)), np.array((4.0, 0.0)), np.array((0.0, 2.0))


@figure(f"{S}_vocab")
def vocab() -> Figure:
    f = Figure(width_in=2.6, height_in=1.6)
    pts = np.array([V_R, V_T, V_A])
    _tri(f, pts, [None, None, None], ra=0, ra_size=0.25)
    f.arc(V_T, V_R, V_A, r=0.7)
    f.angle_label(V_T, V_R, V_A, r"$\theta$", dist=1.15)
    f.text((-0.75, 1.0), "opposite", size=11)
    _out(f, V_R, V_T, V_A, "adjacent", size=11)
    f.text((2.75, 1.55), "hypotenuse", size=11)
    return f


# Problem 2: right angle at A, AB = 10, angle B = 17.
T3_A = np.array((0.0, 0.0))
T3_B = np.array((10.0, 0.0))
T3_C = np.array((0.0, 10 * math.tan(D(17))))
T3_X = 10 / math.cos(D(17))
assert abs(T3_C[1] - 3.057) < 1e-3 and abs(T3_X - 10.4569) < 1e-4
assert abs(dist(T3_B, T3_C) - T3_X) < 1e-9


@figure(f"{S}_3")
def p3() -> Figure:
    f = Figure(width_in=3.0, height_in=1.3)
    _tri(f, [T3_A, T3_B, T3_C], "ABC", ra=0, ra_size=0.5)
    _ang(f, T3_B, T3_A, T3_C, 17, 2.2, 3.4)
    f.side_label(T3_A, T3_B, "10", T3_C)
    f.side_label(T3_B, T3_C, "$x$", T3_A)
    f.text((6.9, 2.45), r"$\approx 10.5$", layer="answer", size=11)
    return f


# Problem 3: right angle at F (mark added), DE = 7 base, angle D = 42, angle E = 48.
T4_D = np.array((0.0, 0.0))
T4_E = np.array((7.0, 0.0))
T4_Y = 7 * math.cos(D(42))
T4_F = T4_Y * np.array((math.cos(D(42)), math.sin(D(42))))
assert abs(T4_F[0] - 3.866) < 1e-3 and abs(T4_F[1] - 3.481) < 1e-3
assert abs(np.dot(T4_D - T4_F, T4_E - T4_F)) < 1e-9
assert_lengths([(T4_D, T4_F, 5.2020), (T4_E, T4_F, 4.6839)], tol=1e-3)


@figure(f"{S}_4")
def p4() -> Figure:
    f = Figure(width_in=2.8, height_in=1.8)
    _tri(f, [T4_D, T4_E, T4_F], "DEF", ra=2, ra_size=0.4)
    _ang(f, T4_D, T4_E, T4_F, 42, 0.8, 1.4)
    _ang(f, T4_E, T4_D, T4_F, 48, 0.7, 1.3)
    f.side_label(T4_D, T4_E, "7", T4_F)
    f.side_label(T4_D, T4_F, "$y$", T4_E)
    f.side_label(T4_D, T4_F, r"$\approx 5.2$", T4_E, layer="answer", size=11)
    return f


# Problem 4: right angle at Q, QN = 4, angle N = 60.
T5_Q = np.array((0.0, 0.0))
T5_N = np.array((4.0, 0.0))
T5_P = np.array((0.0, 4 * math.tan(D(60))))
assert abs(T5_P[1] - 6.9282) < 1e-4 and abs(dist(T5_P, T5_N) - 8) < 1e-9
assert abs(angle_deg(T5_P, T5_Q, T5_N) - 30) < 1e-6


@figure(f"{S}_5")
def p5() -> Figure:
    f = Figure(width_in=1.7, height_in=2.4)
    _tri(f, [T5_P, T5_Q, T5_N], "PQN", ra=1, ra_size=0.4)
    _ang(f, T5_N, T5_Q, T5_P, 60, 0.6, 1.1)
    f.side_label(T5_Q, T5_N, "4", T5_P)
    a = "answer"
    _ang(f, T5_P, T5_Q, T5_N, 30, 1.2, 2.0, layer=a, size=11)
    f.side_label(T5_P, T5_Q, r"$\approx 6.9$", T5_N, layer=a, size=11)
    f.side_label(T5_P, T5_N, "8", T5_Q, layer=a, size=11)
    return f


# Practice 1: right angle at C, AC = 9, BC = 4, AB = sqrt(97); theta at A, beta at B.
R1_A, R1_C, R1_B = np.array((0.0, 0.0)), np.array((9.0, 0.0)), np.array((9.0, 4.0))
assert 9 ** 2 + 4 ** 2 == 97 and abs(dist(R1_A, R1_B) - math.sqrt(97)) < 1e-9


@figure(f"{S}_p1")
def pr1() -> Figure:
    f = Figure(width_in=2.4, height_in=1.3)
    _tri(f, [R1_A, R1_C, R1_B], "ACB", ra=1, ra_size=0.45)
    f.arc(R1_A, R1_C, R1_B, r=1.4)
    f.angle_label(R1_A, R1_C, R1_B, r"$\theta$", dist=2.2)
    f.arc(R1_B, R1_A, R1_C, r=0.9)
    f.angle_label(R1_B, R1_A, R1_C, r"$\beta$", dist=1.6)
    f.side_label(R1_A, R1_C, "9", R1_B)
    f.side_label(R1_C, R1_B, "4", R1_A)
    f.side_label(R1_A, R1_B, r"$\sqrt{97}$", R1_C)
    return f


# Practice 3: right angle at Q, RP = 4, angle R = 30, angle P = 60.
R4_Q, R4_P = np.array((0.0, 0.0)), np.array((2.0, 0.0))
R4_R = np.array((0.0, 2 * math.sqrt(3)))
assert abs(dist(R4_R, R4_P) - 4) < 1e-9 and abs(R4_R[1] - 3.4641) < 1e-4
assert abs(angle_deg(R4_R, R4_Q, R4_P) - 30) < 1e-6


@figure(f"{S}_p4")
def pr4() -> Figure:
    f = Figure(width_in=1.5, height_in=2.2)
    _tri(f, [R4_R, R4_Q, R4_P], "RQP", ra=1, ra_size=0.25)
    _ang(f, R4_R, R4_Q, R4_P, 30, 0.6, 1.0)
    _ang(f, R4_P, R4_Q, R4_R, 60, 0.35, 0.65)
    f.side_label(R4_R, R4_P, "4", R4_Q)
    a = "answer"
    f.side_label(R4_Q, R4_P, "2", R4_R, layer=a, size=11)
    f.text((-1.0, 1.7), r"$2\sqrt{3} \approx 3.5$", layer=a, size=10)
    return f

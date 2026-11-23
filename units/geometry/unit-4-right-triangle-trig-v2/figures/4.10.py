"""Figures for lesson "4.10" (lessons/4.10.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
4.10_7 draws the source synthesis triangle END with the measurements in requirements.md.
v2 (Nov 23): 4.10_exit (the parking-garage ramp) is back as the in-class practice, Problem 5.
Loop: uv run lesson-builder figs <unit> -l "4.10" (0 errors, no label warnings).
"""
import math

import numpy as np

from lesson_builder.figures import Figure, angle_deg, assert_lengths, dist, figure

S = '4.10'
A_ = "answer"


def _deg(x):
    return math.degrees(x)


def _tri(f, pts, names, layer="given", ra=None, ra_size=0.25, overrides=None):
    """Triangle outline, vertex dots, vertex names, and a right-angle mark at index ra."""
    pts = np.asarray(pts, dtype=float)
    f.poly(pts, layer=layer)
    f.dots(pts, layer=layer)
    if any(n is not None for n in names):
        f.label_poly(pts, names, layer=layer, overrides=overrides)
    if ra is not None:
        v = pts[ra]
        o = [pts[i] for i in range(3) if i != ra]
        assert abs(angle_deg(v, o[0], o[1]) - 90) < 1e-6
        f.right_angle(v, o[0], o[1], size=ra_size, layer=layer)


def _ang(f, v, p1, p2, text, r, d, layer="given", size=None, arc=True):
    if arc:
        f.arc(v, p1, p2, r=r, layer=layer)
    f.angle_label(v, p1, p2, text, dist=d, layer=layer, size=size)


# QuickNotes figure: generic right triangle, right angle at (0,0), theta at (4,0).
V_R, V_T, V_A = np.array((0.0, 0.0)), np.array((4.0, 0.0)), np.array((0.0, 2.0))
assert abs(angle_deg(V_R, V_T, V_A) - 90) < 1e-9


@figure(f"{S}_def")
def defn() -> Figure:
    f = Figure(width_in=3.0, height_in=1.7)
    _tri(f, [V_R, V_T, V_A], [None, None, None], ra=0, ra_size=0.25)
    _ang(f, V_T, V_R, V_A, r"$\theta$", 0.7, 1.15)
    f.side_label(V_R, V_A, "opposite", V_T, size=11, offset_pt=14)
    f.side_label(V_R, V_T, "adjacent", V_A, size=11)
    f.side_label(V_A, V_T, "hypotenuse", V_R, size=11, offset_pt=14)
    return f


# Problem 1 (Together, arcsin): right angle A, AB = 9 down, BC = 10, AC = sqrt(19).
T1_A, T1_B = np.array((0.0, 0.0)), np.array((0.0, -9.0))
T1_C = np.array((math.sqrt(19), 0.0))
T1_angC = _deg(math.asin(0.9))
assert abs(dist(T1_B, T1_C) - 10) < 1e-9 and abs(T1_C[0] - 4.3589) < 1e-4
assert abs(T1_angC - 64.1581) < 1e-4 and abs(angle_deg(T1_C, T1_A, T1_B) - T1_angC) < 1e-6
assert abs(angle_deg(T1_B, T1_A, T1_C) - 25.8419) < 1e-4


@figure(f"{S}_1")
def p1() -> Figure:
    f = Figure(width_in=1.5, height_in=2.6)
    _tri(f, [T1_A, T1_B, T1_C], "ABC", ra=0, ra_size=0.6)
    f.side_label(T1_A, T1_B, "9", T1_C)
    f.side_label(T1_B, T1_C, "10", T1_A)
    f.side_label(T1_A, T1_C, r"$\approx 4.4$", T1_B, layer=A_, size=11)
    _ang(f, T1_B, T1_A, T1_C, r"$\approx 26^\circ$", 1.5, 5.0, layer=A_, size=10)
    _ang(f, T1_C, T1_A, T1_B, r"$\approx 64^\circ$", 0.8, 2.0, layer=A_, size=10)
    return f


# Problem 3 (partner, arccos): right angle F, DE = 7 on top, DF = 4, EF = sqrt(33) (not asked).
T2_D, T2_E = np.array((0.0, 0.0)), np.array((7.0, 0.0))
T2_angD = _deg(math.acos(4 / 7))
T2_F = 4 * np.array((math.cos(math.radians(-T2_angD)), math.sin(math.radians(-T2_angD))))
assert abs(T2_F[0] - 2.286) < 1e-3 and abs(T2_F[1] + 3.282) < 1e-3
assert abs(angle_deg(T2_F, T2_D, T2_E) - 90) < 1e-6
assert_lengths([(T2_D, T2_F, 4), (T2_E, T2_F, 5.7446)], tol=1e-3)
assert abs(T2_angD - 55.1501) < 1e-4 and abs(angle_deg(T2_E, T2_D, T2_F) - 34.8499) < 1e-4


@figure(f"{S}_2")
def p2() -> Figure:
    f = Figure(width_in=2.6, height_in=1.5)
    _tri(f, [T2_D, T2_E, T2_F], "DEF", ra=2, ra_size=0.4)
    f.side_label(T2_D, T2_E, "7", T2_F)
    f.side_label(T2_D, T2_F, "4", T2_E)
    _ang(f, T2_D, T2_E, T2_F, r"$\approx 55^\circ$", 0.7, 1.5, layer=A_, size=10)
    _ang(f, T2_E, T2_D, T2_F, r"$\approx 35^\circ$", 1.2, 2.4, layer=A_, size=10)
    return f


def _q_tri(f, pts, ra, vtx, others, sides, ans, ans_at, r, d, ra_size, mark="?"):
    """Unnamed right triangle with a marked angle at pts[vtx], side labels, and a red answer note."""
    _tri(f, pts, [None, None, None], ra=ra, ra_size=ra_size)
    _ang(f, pts[vtx], pts[others[0]], pts[others[1]], mark, r, d)
    for a, b, text, c in sides:
        f.side_label(pts[a], pts[b], text, pts[c])
    if ans:
        f.text(ans_at, ans, layer=A_, size=11)


# Problem 2 (partner, arctan): legs 38 and 27, ? at the left vertex.
T5 = np.array([(0.0, 0.0), (38.0, 0.0), (38.0, 27.0)])
assert abs(angle_deg(T5[0], T5[1], T5[2]) - 35.3948) < 1e-4


@figure(f"{S}_5")
def p5() -> Figure:
    f = Figure(width_in=2.2, height_in=1.6)
    _q_tri(f, T5, 1, 0, (1, 2), [(0, 1, "38", 2), (1, 2, "27", 0)],
           r"$? \approx 35^\circ$", (10.0, 22.0), 6.0, 10.0, 2.5)
    return f


# Problem 4 (partner, synthesis): triangle END, right angle N; theta at E, alpha at D.
T7_N, T7_E, T7_D = np.array((0.0, 0.0)), np.array((1.6, 0.0)), np.array((0.0, -1.2))
assert abs(dist(T7_N, T7_E) ** 2 + dist(T7_N, T7_D) ** 2 - dist(T7_D, T7_E) ** 2) < 1e-9
assert abs(dist(T7_D, T7_E) - 2.0) < 1e-9


@figure(f"{S}_7")
def p7() -> Figure:
    f = Figure(width_in=2.2, height_in=1.7)
    _tri(f, [T7_N, T7_E, T7_D], "NED", ra=0, ra_size=0.12)
    _ang(f, T7_E, T7_N, T7_D, r"$\theta$", 0.3, 0.5)
    _ang(f, T7_D, T7_N, T7_E, r"$\alpha$", 0.25, 0.42)
    f.side_label(T7_N, T7_E, "$d$", T7_D)
    f.side_label(T7_N, T7_D, "$e$", T7_E)
    f.side_label(T7_D, T7_E, "$n$", T7_N)
    return f


# Problem 5 (in-class practice, the old exit ticket; restored Nov 23 from before_noexit/4.10.py):
# ramp, run 95, rise 15; angle = arctan(15/95) ~ 9 > 8.5, not safe.
# arcsin(15/95) ~ 9.08 also rounds to 9, so the first box asks for the inverse, not just the angle.
X = np.array([(0.0, 0.0), (95.0, 0.0), (95.0, 15.0)])
X_ang = angle_deg(X[0], X[1], X[2])
assert abs(X_ang - 8.9726) < 1e-4 and X_ang > 8.5
assert round(_deg(math.asin(15 / 95))) == 9


@figure(f"{S}_exit")
def exit_() -> Figure:
    f = Figure(width_in=3.2, height_in=1.0)
    _tri(f, X, [None, None, None], ra=1, ra_size=4.0)
    f.arc(X[0], X[1], X[2], r=30.0)
    f.side_label(X[0], X[1], "95", X[2])
    f.side_label(X[1], X[2], "15", X[0])
    f.text((40.0, 16.0), r"$\approx 9^\circ$, not safe", layer=A_, size=11)
    return f


# Practice 2: legs 24 (adjacent) and 7 (opposite); theta = arctan(7/24).
R2 = np.array([(0.0, 0.0), (24.0, 0.0), (24.0, 7.0)])
assert abs(angle_deg(R2[0], R2[1], R2[2]) - 16.2602) < 1e-4


@figure(f"{S}_p2")
def pr2() -> Figure:
    f = Figure(width_in=2.4, height_in=1.1)
    _q_tri(f, R2, 1, 0, (1, 2), [(0, 1, "24", 2), (1, 2, "7", 0)],
           r"$\theta \approx 16^\circ$", (6.0, 6.0), 5.0, 8.5, 1.4, mark=r"$\theta$")
    return f


# Practice 3: adjacent 13, hypotenuse 20; theta = arccos(0.65).
R3 = np.array([(0.0, 0.0), (13.0, 0.0), (13.0, math.sqrt(231))])
assert abs(dist(R3[0], R3[2]) - 20) < 1e-9 and abs(R3[2][1] - 15.199) < 1e-3
assert abs(angle_deg(R3[0], R3[1], R3[2]) - 49.4584) < 1e-4


@figure(f"{S}_p3")
def pr3() -> Figure:
    f = Figure(width_in=1.7, height_in=1.9)
    _q_tri(f, R3, 1, 0, (1, 2), [(0, 1, "13", 2), (0, 2, "20", 1)],
           r"$\theta \approx 49^\circ$", (2.0, 14.0), 2.5, 4.5, 1.2, mark=r"$\theta$")
    return f


# Practice 4: opposite 6, hypotenuse 11; theta = arcsin(6/11).
R4 = np.array([(0.0, 0.0), (math.sqrt(85), 0.0), (math.sqrt(85), 6.0)])
assert abs(dist(R4[0], R4[2]) - 11) < 1e-9 and abs(R4[1][0] - 9.220) < 1e-3
assert abs(angle_deg(R4[0], R4[1], R4[2]) - 33.0557) < 1e-4


@figure(f"{S}_p4")
def pr4() -> Figure:
    f = Figure(width_in=2.0, height_in=1.4)
    _q_tri(f, R4, 1, 0, (1, 2), [(1, 2, "6", 0), (0, 2, "11", 1)],
           r"$\theta \approx 33^\circ$", (1.5, 5.5), 2.0, 3.4, 0.7, mark=r"$\theta$")
    return f


# Practice 5: 9-12-15 triangle, theta at the left; answer B (arctan(9/12)).
R5 = np.array([(0.0, 0.0), (12.0, 0.0), (12.0, 9.0)])
assert 9 ** 2 + 12 ** 2 == 15 ** 2 and abs(dist(R5[0], R5[2]) - 15) < 1e-9
assert abs(angle_deg(R5[0], R5[1], R5[2]) - _deg(math.atan(9 / 12))) < 1e-9
assert abs(_deg(math.atan(9 / 12)) - 36.8699) < 1e-4


@figure(f"{S}_p5")
def pr5() -> Figure:
    f = Figure(width_in=2.0, height_in=1.6)
    _q_tri(f, R5, 1, 0, (1, 2), [(0, 1, "12", 2), (1, 2, "9", 0), (0, 2, "15", 1)],
           None, None, 2.2, 3.8, 0.8, mark=r"$\theta$")
    return f


# Practice 7: ladder 15 ft, foot 4 ft from the wall; angle with ground = arccos(4/15).
L_foot, L_base = np.array((0.0, 0.0)), np.array((4.0, 0.0))
L_top = np.array((4.0, math.sqrt(209)))
L_ang = angle_deg(L_foot, L_base, L_top)
assert abs(dist(L_foot, L_top) - 15) < 1e-9 and abs(L_top[1] - 14.457) < 1e-3
assert abs(L_ang - 74.534) < 1e-3 and 70 <= L_ang <= 80


@figure(f"{S}_p7")
def pr7() -> Figure:
    f = Figure(width_in=1.6, height_in=2.6)
    f.seg((-2.0, 0.0), (6.0, 0.0))
    f.seg(L_base, (4.0, 16.0), lw=3.0)
    f.seg(L_foot, L_top, lw=2.0)
    f.right_angle(L_base, L_foot, L_top, size=0.7)
    f.arc(L_foot, L_base, L_top, r=1.4)
    f.label((4.0, 16.0), "wall", italic=False, direction=(1, 0), size=10)
    f.label((-1.5, 0.0), "ground", italic=False, direction=(0, 1), size=10)
    f.side_label(L_foot, L_top, "15 ft", L_base, size=11)
    f.side_label(L_foot, L_base, "4 ft", L_top, size=11)
    f.text((-1.5, 9.0), r"$\approx 75^\circ$, safe", layer=A_, size=11)
    return f


# Practice 8: legs AC = 12, BC = 5; hyp 13; angle A = arctan(5/12).
R8_A, R8_C, R8_B = np.array((0.0, 0.0)), np.array((12.0, 0.0)), np.array((12.0, 5.0))
assert abs(dist(R8_A, R8_B) - 13) < 1e-9
assert abs(angle_deg(R8_A, R8_C, R8_B) - 22.6199) < 1e-4


@figure(f"{S}_p8")
def pr8() -> Figure:
    f = Figure(width_in=2.4, height_in=1.3)
    _tri(f, [R8_A, R8_C, R8_B], "ACB", ra=1, ra_size=0.7)
    f.side_label(R8_A, R8_C, "12", R8_B)
    f.side_label(R8_C, R8_B, "5", R8_A)
    f.side_label(R8_A, R8_B, "13", R8_C, layer=A_, size=11)
    _ang(f, R8_A, R8_C, R8_B, r"$\approx 23^\circ$", 3.0, 5.5, layer=A_, size=10)
    return f

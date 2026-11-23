"""Figures for lesson "4.5" (lessons/4.5.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Nov 19: the warm-up, 7-24-25, and hypotenuse triangles are printed (given layer); the key adds opp/adj/hyp
tags and the answers in red. The extension sketch is gone with the extension.
Loop: uv run lesson-builder figs <unit> -l "4.5" (0 errors, no label warnings).
"""
import math

import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, assert_lengths, dist, figure, midpoint
from lesson_builder.figures.coordinate import axes, plot_line

S = '4.5'
D = math.radians


def _tri(f, pts, names, layer="given", ra=None, ra_size=0.25):
    """Triangle outline, vertex dots, vertex names, and a right-angle mark at index ra."""
    f.poly(pts, layer=layer)
    f.dots(pts, layer=layer)
    f.label_poly(pts, names, layer=layer)
    if ra is not None:
        v = pts[ra]
        o = [pts[i] for i in range(3) if i != ra]
        assert abs(angle_deg(v, o[0], o[1]) - 90) < 1e-6
        f.right_angle(v, o[0], o[1], size=ra_size, layer=layer)


# Warm-up: rocket climbs 50 ft per 13 ft across (drawn at 1 unit = 10 ft). Launch point, ground point, rocket.
WU = P((0, 0), (1.3, 0), (1.3, 5.0))
WU_ANG = math.degrees(math.atan2(50, 13))
assert abs(WU_ANG - 75.43) < 0.01
assert abs(angle_deg(WU[0], WU[1], WU[2]) - WU_ANG) < 1e-6


@figure(f"{S}_warmup")
def warmup() -> Figure:
    f = Figure(width_in=2.4, height_in=2.3)
    _tri(f, WU, [None, None, None], ra=1, ra_size=0.18)
    f.side_label(WU[0], WU[1], "13 ft", WU[2], size=11)
    f.side_label(WU[1], WU[2], "50 ft", WU[0], size=11)
    f.arc(WU[0], WU[1], WU[2], r=0.45)
    f.text((-1.7, 0.1), "launch angle", size=10)
    f.label(WU[2], "rocket", direction=(-1, 0), size=10, italic=False)
    return f


# Together: 7-24-25 triangle, A top, B right angle, C right (teacher's labeling). 1 unit = 4.
T_B, T_C, T_A = np.array((0.0, 0.0)), np.array((7 / 4, 0.0)), np.array((0.0, 24 / 4))
assert 7 ** 2 + 24 ** 2 == 25 ** 2
assert_lengths([(T_A, T_B, 6.0), (T_B, T_C, 1.75), (T_A, T_C, 6.25)])
T_ANG_A = math.degrees(math.acos(24 / 25))
assert abs(T_ANG_A - 16.26) < 0.005 and abs(90 - T_ANG_A - 73.74) < 0.005
assert abs(angle_deg(T_A, T_B, T_C) - T_ANG_A) < 1e-6


@figure(f"{S}_together")
def together() -> Figure:
    f = Figure(width_in=2.2, height_in=2.5)
    pts = np.array([T_A, T_B, T_C])
    _tri(f, pts, "ABC", ra=1)
    f.side_label(T_A, T_B, "24", T_C)
    f.side_label(T_B, T_C, "7", T_A)
    f.side_label(T_A, T_C, "25", T_B)
    a = "answer"
    f.side_label(T_A, midpoint(T_A, T_B), "adj", T_C, layer=a, size=11)
    f.side_label(T_B, T_C, "opp", T_A, layer=a, offset_pt=24, size=11)
    f.side_label(T_A, midpoint(T_A, T_C), "hyp", T_B, layer=a, size=11)
    f.arc(T_A, T_B, T_C, r=0.9, layer=a)
    f.label(T_A, r"16.26^\circ", layer=a, direction=(1, -0.2), offset_pt=16, size=10)
    f.arc(T_C, T_A, T_B, r=0.35, layer=a)
    f.label(T_C, r"73.74^\circ", layer=a, direction=(1, 1), offset_pt=16, size=10)
    return f


# Partner 1: right angle at A, hypotenuse CB = 8.5, angle B = 20 deg.
P1_A = np.array((0.0, 0.0))
P1_B = np.array((8.5 * math.cos(D(20)), 0.0))
P1_C = np.array((0.0, 8.5 * math.sin(D(20))))
assert abs(dist(P1_B, P1_C) - 8.5) < 1e-9 and abs(P1_B[0] - 7.987) < 0.001
assert abs(angle_deg(P1_B, P1_A, P1_C) - 20) < 1e-6


@figure(f"{S}_partner_1")
def partner_1() -> Figure:
    f = Figure(width_in=3.0, height_in=1.4)
    pts = np.array([P1_A, P1_B, P1_C])
    _tri(f, pts, "ABC", ra=0)
    f.side_label(P1_C, P1_B, "8.5", P1_A)
    f.arc(P1_B, P1_A, P1_C, r=1.1)
    f.angle_label(P1_B, P1_A, P1_C, r"$20^\circ$", dist=1.9)
    a = "answer"
    f.side_label(P1_A, P1_C, "opp", P1_B, layer=a)
    f.side_label(P1_A, P1_B, r"adj, $AB \approx 7.99$", P1_C, layer=a)
    f.text(P1_C + np.array((2.6, 0.2)), "hyp", layer=a)
    return f


# Partner 2: right angle at B, angle A = 40 deg, BC = 5 cm opposite A. Printed (was a sketch from words).
P2_B = np.array((0.0, 0.0))
P2_C = np.array((5.0, 0.0))
P2_A = np.array((0.0, 5 / math.tan(D(40))))
P2_HYP = 5 / math.sin(D(40))
assert abs(P2_HYP - 7.78) < 0.005 and abs(dist(P2_A, P2_C) - P2_HYP) < 1e-9
assert abs(angle_deg(P2_A, P2_B, P2_C) - 40) < 1e-6 and abs(dist(P2_A, P2_B) - 5.96) < 0.005


@figure(f"{S}_partner_2")
def partner_2() -> Figure:
    f = Figure(width_in=2.0, height_in=1.9)
    pts = np.array([P2_A, P2_B, P2_C])
    _tri(f, pts, "ABC", ra=1, ra_size=0.35)
    f.arc(P2_A, P2_B, P2_C, r=0.9)
    f.angle_label(P2_A, P2_B, P2_C, r"$40^\circ$", dist=1.6)
    f.side_label(P2_B, P2_C, "5 cm", P2_A)
    a = "answer"
    f.side_label(P2_B, P2_C, "opp", P2_A, layer=a, offset_pt=24)
    f.side_label(P2_A, P2_B, "adj", P2_C, layer=a)
    f.side_label(P2_A, P2_C, "hyp", P2_B, layer=a, offset_pt=12)
    f.text((3.5, 4.7), r"$AC \approx 7.78$", layer=a)
    return f


# Partner 3: right angle at E, EF = 6, angle F = 50 deg, DF on the bottom.
P3_DF = 6 / math.cos(D(50))
P3_D = np.array((0.0, 0.0))
P3_F = np.array((P3_DF, 0.0))
P3_E = P3_F + 6 * np.array((math.cos(D(130)), math.sin(D(130))))
P3_DE = 6 * math.tan(D(50))
assert abs(angle_deg(P3_E, P3_D, P3_F) - 90) < 1e-6 and abs(dist(P3_D, P3_E) - P3_DE) < 1e-9
assert abs(P3_DE - 7.15) < 0.005 and abs(P3_DF - 9.334) < 0.001


@figure(f"{S}_partner_3")
def partner_3() -> Figure:
    f = Figure(width_in=2.9, height_in=1.6)
    pts = np.array([P3_D, P3_E, P3_F])
    _tri(f, pts, "DEF", ra=1, ra_size=0.45)
    f.side_label(P3_E, P3_F, "6", P3_D)
    f.arc(P3_F, P3_D, P3_E, r=0.8)
    f.angle_label(P3_F, P3_D, P3_E, r"$50^\circ$", dist=1.5)
    a = "answer"
    f.side_label(P3_D, P3_E, "opp", P3_F, layer=a)
    f.text((1.2, 3.6), r"$DE \approx 7.15$", layer=a)
    f.side_label(P3_D, P3_F, "hyp", P3_E, layer=a)
    f.text(P3_E + np.array((0.9, -2.2)), "adj", layer=a)
    return f


# Exit: right angle at C, hypotenuse AB = 7 on top, angle B = 70 deg.
X_A = np.array((0.0, 0.0))
X_B = np.array((7.0, 0.0))
X_C = X_B + 7 * math.cos(D(70)) * np.array((math.cos(D(250)), math.sin(D(250))))
assert abs(angle_deg(X_C, X_A, X_B) - 90) < 1e-6 and abs(angle_deg(X_B, X_A, X_C) - 70) < 1e-6
assert abs(dist(X_B, X_C) - 2.394) < 0.001 and abs(dist(X_A, X_C) - 6.578) < 0.001


@figure(f"{S}_exit")
def exit_() -> Figure:
    f = Figure(width_in=3.0, height_in=1.3)
    pts = np.array([X_A, X_B, X_C])
    _tri(f, pts, "ABC", ra=2, ra_size=0.3)
    f.side_label(X_A, X_B, "7", X_C)
    f.arc(X_B, X_A, X_C, r=0.6)
    f.angle_label(X_B, X_A, X_C, r"$70^\circ$", dist=1.15)
    a = "answer"
    f.text((8.1, -1.0), r"$\approx 2.39$", layer=a)
    f.side_label(X_A, X_C, r"$\approx 6.58$", X_B, layer=a)
    f.angle_label(X_A, X_B, X_C, r"$20^\circ$", dist=2.7, layer=a, size=10)
    return f


# Practice 2: kite string 18 ft at 30 deg; right angle under the kite.
K_S = np.array((0.0, 0.0))
K_G = np.array((18 * math.cos(D(30)), 0.0))
K_K = np.array((K_G[0], 18 * math.sin(D(30))))
assert abs(K_K[1] - 9) < 1e-9 and abs(dist(K_S, K_K) - 18) < 1e-9


@figure(f"{S}_pr2")
def pr2() -> Figure:
    f = Figure(width_in=2.6, height_in=1.75)
    f.poly([K_S, K_G, K_K])
    f.dots([K_S, K_G])
    f.right_angle(K_G, K_S, K_K, size=0.8)
    f.side_label(K_S, K_K, "18 ft", K_G)
    f.arc(K_S, K_G, K_K, r=2.6)
    f.angle_label(K_S, K_G, K_K, r"$30^\circ$", dist=4.3)
    k = K_K + np.array([(0, 0), (-1.3, 1.9), (0.6, 4.4), (2.2, 1.5)])
    f.poly(k, fill="0.85")
    f.seg(k[0], k[2], lw=0.6)
    f.seg(k[1], k[3], lw=0.6)
    tail = K_K + np.array([(0, 0), (1.0, -0.8), (2.0, -0.3), (3.0, -1.0)])
    f.poly(tail, closed=False, lw=0.6)
    f.side_label(K_G, K_K, "9 ft", K_S, layer="answer")
    return f


# Practice 3: right angle at C, B top, A right; no measurements.
R3 = P((3, 0), (0, 2), (0, 0))


@figure(f"{S}_pr3")
def pr3() -> Figure:
    f = Figure(width_in=1.9, height_in=1.3)
    _tri(f, R3, "ABC", ra=2, ra_size=0.16)
    return f


# Practice 5: right angle at A, AC = 6, angle C = 30 deg.
F_A = np.array((0.0, 0.0))
F_C = np.array((6.0, 0.0))
F_B = np.array((0.0, 6 * math.tan(D(30))))
assert abs(F_B[1] - 2 * math.sqrt(3)) < 1e-9 and abs(angle_deg(F_C, F_A, F_B) - 30) < 1e-6


@figure(f"{S}_pr5")
def pr5() -> Figure:
    f = Figure(width_in=2.3, height_in=1.4)
    _tri(f, np.array([F_A, F_B, F_C]), "ABC", ra=0, ra_size=0.3)
    f.side_label(F_A, F_C, "6", F_B)
    f.arc(F_C, F_A, F_B, r=0.8)
    f.angle_label(F_C, F_A, F_B, r"$30^\circ$", dist=1.5)
    f.text((4.7, 3.7), r"$AB = 2\sqrt{3} \approx 3.46$", layer="answer", size=11)
    return f


# Practice 6: right angle at B, altitude BD; BC = 13, DC = 12, so BD = 5 and AD = 25/12.
G_AD = 25 / 12
G_A = np.array((0.0, 0.0))
G_D = np.array((G_AD, 0.0))
G_C = np.array((G_AD + 12, 0.0))
G_B = np.array((G_AD, 5.0))
assert abs(dist(G_B, G_C) - 13) < 1e-9
assert abs(angle_deg(G_B, G_A, G_C) - 90) < 1e-6 and abs(angle_deg(G_D, G_B, G_C) - 90) < 1e-9


@figure(f"{S}_pr6")
def pr6() -> Figure:
    f = Figure(width_in=3.2, height_in=2.0)
    pts = np.array([G_A, G_B, G_C])
    f.poly(pts)
    f.dots(pts)
    f.label_poly(pts, "ABC", overrides={"A": (-1, -0.2), "B": (0, 1), "C": (1, -0.2)})
    f.right_angle(G_B, G_A, G_C, size=0.75)
    f.seg(G_B, G_D)
    f.dots([G_D])
    f.label(G_D, "D", direction=(0.4, -1), offset_pt=12)
    f.right_angle(G_D, G_B, G_C, size=0.75)
    f.side_label(G_B, G_C, "13", G_A)
    f.side_label(G_D, G_C, "12", G_B)
    a = "answer"
    f.label((G_AD, 2.5), "5", layer=a, direction=(1, 0), offset_pt=8, italic=False)
    f.text((G_AD / 2, -2.2), r"$AD \approx 2.08$", layer=a)
    return f


# Practice 7: line y = x/2 through the origin.
assert abs(0.5 * 40 - 20) < 1e-9 and abs(0.5 * 70 - 35) < 1e-9


@figure(f"{S}_pr7")
def pr7() -> Figure:
    f = Figure(width_in=2.6, height_in=1.5)
    axes(f, 0, 80, 0, 40, step=5, labels_every=2, size=8)
    plot_line(f, 0.5, 0, 0, 70, arrows=False)
    f.arrow((70, 35), (76, 38), layer="given", dashed=False)
    return f

"""Figures for assessment "Unit 4 Test A" (assessments/Unit 4 Test A.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
"""
import math

import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, dist, figure

S = 'Unit 4 Test A'


@figure(f"{S}_1")
def q1() -> Figure:
    B, C, A = P((0, 0), (4.092, 0), (4.092, 4.388))
    assert abs(angle_deg(C, A, B) - 90) < 1e-6
    assert abs(angle_deg(B, A, C) - 47) < 0.1
    assert abs(angle_deg(A, B, C) - 43) < 0.1
    f = Figure(width_in=2.3, height_in=2.3)
    f.poly([A, B, C])
    f.right_angle(C, A, B, size=0.35)
    f.label_poly([A, B, C], "ABC")
    f.arc(B, C, A, r=0.8)
    f.angle_label(B, C, A, r'$47^\circ$', dist=1.3)
    f.side_label(B, C, "a", center=A, italic=True)
    f.side_label(C, A, "b", center=B, italic=True)
    f.side_label(A, B, "c", center=C, italic=True)
    f.angle_label(A, B, C, r'$43^\circ$', dist=1.1, layer="answer")
    return f


@figure(f"{S}_2")
def q2() -> Figure:
    k = 5  # vertical stretch so the small angle is visible
    R, T, H = P((0, 0), (28, 0), (0, 2 * k))
    theta = math.degrees(math.atan(2 / 28))
    assert abs(theta - 4.09) < 0.01
    f = Figure(width_in=3.0, height_in=1.6)
    f.poly([R, T, H])
    f.right_angle(R, T, H, size=1.2)
    f.side_label(R, H, "2 ft", center=T)
    f.side_label(R, T, "28 ft", center=H)
    f.arc(T, R, H, r=6)
    f.angle_label(T, R, H, r'$\theta$', dist=8.5)
    f.text((14, -5.5), "(not drawn to scale)", size=10)
    f.label((21, 6), r'$\theta \approx 4.1^\circ$', layer="answer", italic=False)
    return f


@figure(f"{S}_3")
def q3() -> Figure:
    O, R, T = P((0, 0), (39.601, 0), (39.601, 16))
    assert abs(angle_deg(O, R, T) - 22) < 0.1
    assert abs(dist(R, T) - 16) < 1e-6
    x = 16 / math.sin(math.radians(22))
    assert abs(dist(O, T) - x) < 0.01 and abs(x - 42.71) < 0.01
    f = Figure(width_in=2.8, height_in=1.5)
    f.poly([O, R, T])
    f.right_angle(R, O, T, size=2.2)
    f.arc(O, R, T, r=9)
    f.angle_label(O, R, T, r'$22^\circ$', dist=14)
    f.side_label(R, T, "16", center=O)
    f.side_label(O, T, "x", center=R, italic=True)
    f.label((14, 13), r'$x \approx 42.7$', layer="answer", italic=False)
    return f


@figure(f"{S}_4")
def q4() -> Figure:
    """Leg adjacent to beta (4.9) and the hypotenuse (8.9) are given, so beta = arccos(4.9/8.9); the vertical leg
    is unlabeled. Nov 20: was legs 5 and 12 (Lesson 4.10 practice 8's triangle, arctan)."""
    adj, hyp = 4.9, 8.9
    opp = math.sqrt(hyp ** 2 - adj ** 2)
    O, R, T = P((0, 0), (adj, 0), (adj, opp))
    assert abs(dist(O, R) - adj) < 1e-9 and abs(dist(O, T) - hyp) < 1e-9
    assert abs(angle_deg(R, O, T) - 90) < 1e-6
    beta = angle_deg(O, R, T)
    assert abs(beta - math.degrees(math.acos(adj / hyp))) < 1e-6 and round(beta, 1) == 56.6
    assert round(math.degrees(math.asin(adj / hyp)), 1) == 33.4    # wrong inverse (the other angle), in the key
    assert round(math.degrees(math.atan(adj / hyp)), 1) == 28.8    # tan of leg over hypotenuse, in the key
    f = Figure(width_in=1.6, height_in=2.4)
    f.poly([O, R, T])
    f.right_angle(R, O, T, size=0.5)
    f.arc(O, R, T, r=1.0)
    f.angle_label(O, R, T, r'$\beta$', dist=1.5)
    f.side_label(O, R, "4.9", center=T)
    f.side_label(O, T, "8.9", center=R)
    f.label((0.2, 5.4), r'$\beta \approx 56.6^\circ$', layer="answer", italic=False)
    return f


@figure(f"{S}_5")
def q5() -> Figure:
    """Triangle LMN, right angle at N, LM = 7, 66 degrees at M (Nov 20: relettered from ABC, item 1's name)."""
    L, N, M = P((0, 0), (6.395, 0), (6.395, 2.847))
    assert abs(dist(L, M) - 7) < 0.01
    assert abs(angle_deg(M, L, N) - 66) < 0.1
    assert abs(angle_deg(N, L, M) - 90) < 0.1
    assert abs(7 * math.sin(math.radians(66)) - dist(L, N)) < 0.01
    assert abs(7 * math.cos(math.radians(66)) - dist(M, N)) < 0.01
    f = Figure(width_in=2.9, height_in=1.6)
    f.poly([L, N, M])
    f.right_angle(N, L, M, size=0.35)
    f.label_poly([L, N, M], "LNM")
    f.arc(M, L, N, r=0.6)
    f.angle_label(M, L, N, r'$66^\circ$', dist=1.0)
    f.side_label(L, M, "7", center=N)
    f.side_label(L, N, r'$\approx 6.4$', center=M, layer="answer")
    f.side_label(N, M, r'$\approx 2.8$', center=L, layer="answer")
    return f


@figure(f"{S}_6")
def q6() -> Figure:
    O, Bt, Tp = P((0, 0), (150, 0), (150, 371.26))
    h = 150 * math.tan(math.radians(68))
    assert abs(dist(Bt, Tp) - h) < 0.01
    assert abs(angle_deg(O, Bt, Tp) - 68) < 0.1
    assert Bt[0] == Tp[0]
    f = Figure(width_in=1.9, height_in=2.7, key_frame="union")
    f.poly([Bt + (0, 0), Bt + (10, 0), Bt + (10, 10), Bt + (0, 10)], lw=1.0, fill="0.6")
    f.seg(Bt, Tp, lw=2.2)
    f.seg(Tp - (8, 0), Tp + (8, 0))
    f.seg((-30, 0), (190, 0))
    f.seg(O, Tp, dashed=True)
    f.dots([O])
    f.text(O + (0, -22), "you", size=10)
    f.right_angle(Bt, O, Tp, size=20)
    f.arc(O, Bt, Tp, r=40)
    f.angle_label(O, Bt, Tp, r'$68^\circ$', dist=62)
    f.side_label(O, Bt, "150 ft", center=Tp, offset_pt=18)
    f.label(Tp + (0, -200), "h", direction=(1, 0), offset_pt=12)
    f.label(Tp + (0, -60), r'$h \approx 371$ ft', direction=(1, 0), offset_pt=16, layer="answer", italic=False)
    return f

"""Figures for assessment "Unit 4 Test Retake" (assessments/Unit 4 Test Retake.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
"""
import math

import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, dist, figure

S = 'Unit 4 Test Retake'


@figure(f"{S}_1")
def q1() -> Figure:
    """Triangle DEF, right angle at F, 58 degrees at E; sides d, e, f lowercase."""
    F, D, E = P(0, 0), P(5.088, 0), P(0, 3.180)
    assert np.isclose(angle_deg(F, D, E), 90)
    assert abs(angle_deg(E, D, F) - 58) < 0.1
    tri = np.array([D, E, F])
    f = Figure(width_in=2.4, height_in=1.7)
    f.poly(tri)
    f.right_angle(F, D, E, size=0.3)
    f.label_poly(tri, "DEF")
    f.side_label(E, F, "$d$", center=D)
    f.side_label(D, F, "$e$", center=E)
    f.side_label(D, E, "$f$", center=F)
    f.angle_label(E, D, F, "$58^\\circ$", dist=0.9)
    f.angle_label(D, E, F, "$32^\\circ$", dist=1.4, layer="answer")
    return f


@figure(f"{S}_2")
def q2() -> Figure:
    """Ladder: foot 6 ft from the wall, top 14 ft up; angle x at the foot."""
    foot, base, top = P(0, 0), P(6, 0), P(6, 14)
    assert np.isclose(dist(foot, base), 6) and np.isclose(dist(base, top), 14)
    assert abs(angle_deg(foot, base, top) - 66.80) < 0.05
    f = Figure(width_in=2.2, height_in=2.6)
    f.poly(P((6, 0), (7.2, 0), (7.2, 15.5), (6, 15.5)), lw=1.0, hatch="///")
    f.seg(P(-6, 0), P(10, 0))
    f.seg(foot, top, lw=2.5)
    f.right_angle(base, foot, top, size=0.6)
    f.side_label(foot, base, "6 ft", center=top)
    f.text(P(9, 7), "14 ft")
    f.text(P(1.0, 9), "ladder", size=10)
    f.angle_label(foot, base, top, "$x$", dist=1.8)
    f.text(P(-3.2, 2.2), "$x \\approx 66.8^\\circ$", layer="answer", size=10)
    return f


@figure(f"{S}_3")
def q3() -> Figure:
    """Right angle bottom-left, vertical leg 11, 28 degrees bottom-right, hypotenuse y."""
    R, A, T = P(0, 0), P(20.688, 0), P(0, 11)
    assert np.isclose(dist(R, T), 11)
    assert abs(angle_deg(A, R, T) - 28) < 0.1
    assert abs(dist(A, T) - 23.43) < 0.01
    tri = np.array([R, A, T])
    f = Figure(width_in=2.6, height_in=1.5)
    f.poly(tri)
    f.right_angle(R, A, T, size=1.3)
    f.side_label(R, T, "11", center=A)
    f.side_label(A, T, "$y$", center=R)
    f.angle_label(A, R, T, "$28^\\circ$", dist=4.5)
    f.text(P(15.0, 10.2), "$y \\approx 23.4$", layer="answer")
    return f


@figure(f"{S}_4")
def q4() -> Figure:
    """Right angle bottom-left; the leg opposite alpha (5.3) and the hypotenuse (10.2) are given, so
    alpha = arcsin(5.3/10.2); the base is unlabeled. Nov 20: was legs 9 and 20 (arctan)."""
    opp, hyp = 5.3, 10.2
    adj = math.sqrt(hyp ** 2 - opp ** 2)
    R, A, T = P(0, 0), P(adj, 0), P(0, opp)
    assert np.isclose(dist(R, T), opp) and np.isclose(dist(A, T), hyp)
    assert np.isclose(angle_deg(R, A, T), 90)
    alpha = angle_deg(A, R, T)
    assert np.isclose(alpha, math.degrees(math.asin(opp / hyp))) and round(alpha, 1) == 31.3
    assert round(math.degrees(math.acos(opp / hyp)), 1) == 58.7    # wrong inverse (the other angle), in the key
    assert round(math.degrees(math.atan(opp / hyp)), 1) == 27.5    # tan of leg over hypotenuse, in the key
    tri = np.array([R, A, T])
    f = Figure(width_in=2.4, height_in=1.5)
    f.poly(tri)
    f.right_angle(R, A, T, size=0.5)
    f.arc(A, R, T, r=1.6)
    f.side_label(R, T, "5.3", center=A)
    f.side_label(A, T, "10.2", center=R)
    f.angle_label(A, R, T, "$\\alpha$", dist=2.3)
    f.text(P(6.6, 3.9), "$\\alpha \\approx 31.3^\\circ$", layer="answer")
    return f


@figure(f"{S}_5")
def q5() -> Figure:
    """Triangle PQR, right angle at R, PQ = 9, 29 degrees at P; angle Q is not asked (no arc)."""
    Pp, R, Q = P(0, 0), P(7.872, 0), P(7.872, 4.363)
    assert abs(dist(Pp, Q) - 9) < 0.01
    assert abs(angle_deg(Pp, Q, R) - 29) < 0.1
    assert np.isclose(angle_deg(R, Pp, Q), 90)
    tri = np.array([Pp, Q, R])
    f = Figure(width_in=2.6, height_in=1.6)
    f.poly(tri)
    f.right_angle(R, Pp, Q, size=0.4)
    f.label_poly(tri, "PQR")
    f.side_label(Pp, Q, "9", center=R)
    f.angle_label(Pp, Q, R, "$29^\\circ$", dist=1.7)
    f.side_label(Q, R, "$\\approx 4.4$", center=Pp, layer="answer")
    f.side_label(Pp, R, "$\\approx 7.9$", center=Q, layer="answer")
    return f


@figure(f"{S}_6")
def q6() -> Figure:
    """Lighthouse 130 ft from the observer, 58 degree angle of elevation, height h."""
    O, B, T = P(0, 0), P(130, 0), P(130, 208.04)
    assert np.isclose(dist(O, B), 130)
    assert abs(angle_deg(O, B, T) - 58) < 0.1
    assert np.isclose(angle_deg(B, O, T), 90)
    f = Figure(width_in=2.4, height_in=2.5)
    f.poly(P((130, 0), (160, 0), (152, 200), (130, 200)), lw=1.0)
    f.poly(P((128, 200), (156, 200), (154, 208.04), (130, 208.04)), lw=1.0)
    for y in (50, 100, 150):
        f.seg(P(130, y), P(160 - 8 * y / 200, y), lw=0.6)
    f.seg(P(-15, 0), P(235, 0))
    f.seg(O, T, dashed=True)
    f.seg(B, T, lw=1.5)
    f.right_angle(B, O, T, size=10)
    f.dots(np.array([O]))
    f.text(P(0, -22), "you", size=10)
    f.text(P(85, -22), "130 ft")
    f.text(P(180, 125), "$h$")
    f.seg(P(165, 208.04), P(185, 208.04), lw=0.6)
    f.seg(P(175, 208.04), P(175, 140), lw=0.6)
    f.seg(P(175, 110), P(175, 0), lw=0.6)
    f.angle_label(O, B, T, "$58^\\circ$", dist=30)
    f.text(P(200, 80), "$h \\approx 208$ ft", layer="answer", size=10)
    return f

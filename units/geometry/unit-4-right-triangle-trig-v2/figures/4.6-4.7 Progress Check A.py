"""Figures for assessment "4.6-4.7 Progress Check A" (assessments/4.6-4.7 Progress Check A.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
"""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, dist, figure

S = '4.6-4.7 Progress Check A'


@figure(f"{S}_1")
def q1() -> Figure:
    """Key-only sketch: triangle ABC, right angle at B; AB is opposite angle C."""
    A, B, C = P(0, 3), P(0, 0), P(4, 0)
    assert np.isclose(angle_deg(B, A, C), 90)
    f = Figure(width_in=2.2, height_in=1.8)
    f.poly(P((-3.9, -0.7), (4.7, -0.7), (4.7, 3.7), (-3.9, 3.7)), lw=0.4)
    tri = np.array([A, B, C])
    f.poly(tri, layer="answer")
    f.right_angle(B, A, C, size=0.4, layer="answer")
    f.label_poly(tri, "ABC", layer="answer")
    f.seg(A, B, layer="answer", lw=3)
    f.text(P(-1.9, 1.5), "opposite $\\angle C$", layer="answer", size=11)
    return f


@figure(f"{S}_2")
def q2() -> Figure:
    """Triangle GHR, right angle at R, GH = 11, HR = x, 74 degrees at H (top right). Nov 20: relettered from ABC so
    it doesn't share item 1's letters (1b asks about angle C and side AB just above it)."""
    G, R, H = P(0, 0), P(10.574, 0), P(10.574, 3.032)
    assert abs(dist(G, H) - 11) < 0.01
    assert abs(angle_deg(H, G, R) - 74) < 0.1
    assert np.isclose(angle_deg(R, G, H), 90)
    tri = np.array([G, H, R])
    f = Figure(width_in=2.6, height_in=1.2)
    f.poly(tri)
    f.right_angle(R, G, H, size=0.6)
    f.label_poly(tri, "GHR")
    f.side_label(G, H, "11", center=R)
    f.side_label(H, R, "$x$", center=G)
    f.angle_label(H, G, R, "$74^\\circ$", dist=1.5)
    return f


@figure(f"{S}_3")
def q3() -> Figure:
    """Triangle DEF, right angle at E, DF = 11, 55 degrees at D."""
    F, E, D = P(0, 0), P(9.011, 0), P(9.011, 6.309)
    assert abs(dist(D, F) - 11) < 0.01
    assert abs(angle_deg(D, E, F) - 55) < 0.1
    assert np.isclose(angle_deg(E, D, F), 90)
    tri = np.array([D, E, F])
    f = Figure(width_in=2.4, height_in=1.8)
    f.poly(tri)
    f.right_angle(E, D, F, size=0.7)
    f.label_poly(tri, "DEF")
    f.side_label(D, F, "11", center=E)
    f.angle_label(D, E, F, "$55^\\circ$", dist=1.8)
    f.angle_label(F, D, E, "$35^\\circ$", dist=2.6, layer="answer")
    f.side_label(E, F, "$\\approx 9.0$", center=D, layer="answer")
    f.side_label(D, E, "$\\approx 6.3$", center=F, layer="answer")
    return f


@figure(f"{S}_4")
def q4() -> Figure:
    """Building AB, Lin at C, BC = 50 ft, 71 degree angle of elevation at C."""
    B, C, A = P(0, 0), P(50, 0), P(0, 145.21)
    assert np.isclose(dist(B, C), 50)
    assert abs(angle_deg(C, A, B) - 71) < 0.1
    assert np.isclose(angle_deg(B, A, C), 90)
    f = Figure(width_in=2.4, height_in=2.6)
    f.poly(P((-22, 0), (0, 0), (0, 145.21), (-22, 145.21)), lw=1.0)
    for y in range(20, 140, 25):
        f.poly(P((-17, y), (-11, y), (-11, y + 10), (-17, y + 10)), lw=0.6)
        f.poly(P((-8, y), (-3, y), (-3, y + 10), (-8, y + 10)), lw=0.6)
    f.seg(P(-85, 0), P(85, 0))
    f.seg(A, C, dashed=True)
    f.right_angle(B, A, C, size=7)
    f.dots(np.array([A, B, C]))
    f.label(A, "A", direction=(1, 1))
    f.label(B, "B", direction=(1, -1))
    f.label(C, "C", direction=(0, -1))
    f.text(P(52, 18), "Lin", size=10)
    f.side_label(B, C, "50 ft", center=A, offset_pt=14)
    f.text(P(11, 75), "$h$", size=12, fixed=True)
    f.angle_label(C, A, B, "$71^\\circ$", dist=24)
    f.text(P(-53, 75), "$\\approx 145$ ft", layer="answer", size=10)
    return f

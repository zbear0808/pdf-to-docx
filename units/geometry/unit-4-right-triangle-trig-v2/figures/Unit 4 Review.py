"""Figures for assessment "Unit 4 Review" (assessments/Unit 4 Review.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
"""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, dist, figure

S = 'Unit 4 Review'
DEG = "^\\circ$"


def _tri(f, pts, names, right, size):
    tri = np.array(pts)
    f.poly(tri)
    f.dots(tri)
    f.label_poly(tri, names)
    v, a, b = right
    f.right_angle(v, a, b, size=size)
    return tri


@figure(f"{S}_1")
def q1() -> Figure:
    """ABC right at C, AB = 52, BC = 20 (half scale); FJZ right at Z, JZ = 3, FZ = 8 (1.5x scale)."""
    A, C, B = P(0, 0), P(24, 0), P(24, 10)
    Z, Y, X = P(37, 0), P(41.5, 0), P(37, 12)
    assert np.isclose(2 * dist(A, B), 52) and np.isclose(2 * dist(B, C), 20) and np.isclose(2 * dist(A, C), 48)
    assert np.isclose(dist(Y, Z) / 1.5, 3) and np.isclose(dist(X, Z) / 1.5, 8)
    assert abs(dist(X, Y) / 1.5 - 8.544) < 0.01
    assert np.isclose(angle_deg(C, A, B), 90) and np.isclose(angle_deg(Z, X, Y), 90)
    f = Figure(width_in=3.4, height_in=1.5)
    _tri(f, [A, B, C], "ABC", (C, A, B), 1.0)
    _tri(f, [X, Y, Z], "FJZ", (Z, X, Y), 1.0)
    f.side_label(A, B, "52", center=C)
    f.side_label(B, C, "20", center=A)
    f.side_label(Y, Z, "3", center=X)
    f.side_label(X, Z, "8", center=Y)
    f.side_label(A, C, "$48$", center=B, layer="answer")
    f.side_label(X, Y, "$\\approx 8.5$", center=Z, layer="answer")
    return f


@figure(f"{S}_4")
def q4() -> Figure:
    """RST right at T, RT = 10, ST = 3; theta at R, beta at S."""
    R, T, S_ = P(0, 0), P(10, 0), P(10, 3)
    assert np.isclose(dist(R, T), 10) and np.isclose(dist(S_, T), 3)
    assert abs(dist(R, S_) - 10.440) < 0.01 and np.isclose(angle_deg(T, R, S_), 90)
    f = Figure(width_in=2.6, height_in=1.1)
    _tri(f, [R, S_, T], "RST", (T, R, S_), 0.5)
    f.side_label(R, T, "10", center=S_)
    f.side_label(S_, T, "3", center=R)
    f.side_label(R, S_, "$\\sqrt{109}$", center=T)
    f.arc(R, T, S_, r=4.4)   # Nov 20: arcs tie theta to R and beta to S (the 17 deg wedge is narrow, so the arc
    f.arc(S_, R, T, r=0.55)  # reaches out to where theta's label fits)
    f.angle_label(R, T, S_, "$\\theta$", dist=5.2)
    f.angle_label(S_, R, T, "$\\beta$", dist=0.95)
    return f


@figure(f"{S}_5")
def q5() -> Figure:
    """ABC right at C, AB = 13, 36 degrees at B, BC = x."""
    A, C, B = P(0, 0), P(7.641, 0), P(7.641, 10.517)
    assert abs(dist(A, B) - 13) < 0.01 and abs(angle_deg(B, A, C) - 36) < 0.1
    assert np.isclose(angle_deg(C, A, B), 90)
    f = Figure(width_in=1.6, height_in=2.0)
    _tri(f, [A, B, C], "DEG", (C, A, B), 0.8)
    f.side_label(A, B, "13", center=C)
    f.side_label(B, C, "$x$", center=A)
    f.angle_label(B, A, C, "$36" + DEG, dist=2.6)
    return f


@figure(f"{S}_6")
def q6() -> Figure:
    """JKL right at L, KL = 10, 52 degrees at K."""
    L, K, J = P(0, 0), P(10, 0), P(0, 12.799)
    assert np.isclose(dist(K, L), 10) and abs(angle_deg(K, L, J) - 52) < 0.1
    assert np.isclose(angle_deg(L, K, J), 90)
    assert abs(dist(L, J) - 12.8) < 0.01 and abs(dist(K, J) - 16.24) < 0.01
    f = Figure(width_in=1.9, height_in=2.2)
    _tri(f, [J, K, L], "PQN", (L, K, J), 0.9)
    f.side_label(K, L, "10", center=J)
    f.angle_label(K, L, J, "$52" + DEG, dist=2.2)
    f.angle_label(J, K, L, "$38" + DEG, dist=3.0, layer="answer")
    f.side_label(L, J, "$\\approx 12.8$", center=K, layer="answer", offset_pt=20)
    f.side_label(K, J, "$\\approx 16.2$", center=L, layer="answer")
    return f


@figure(f"{S}_7")
def q7() -> Figure:
    """UVW right at W, UV = 10, 34 degrees at U, 56 at V; UW = x = 10 cos 34, VW = y = 10 sin 34.
    Nov 19: was 38/52 (old item 6, just above, asks for 38 from 52; x was 7.9, a Test Retake answer)."""
    x, y = 10 * np.cos(np.radians(34)), 10 * np.sin(np.radians(34))
    A, C, B = P(0, 0), P(x, 0), P(x, y)
    assert abs(dist(A, B) - 10) < 1e-9 and abs(angle_deg(A, B, C) - 34) < 1e-6
    assert abs(angle_deg(B, A, C) - 56) < 1e-6 and np.isclose(angle_deg(C, A, B), 90)
    assert round(x, 1) == 8.3 and round(y, 1) == 5.6
    f = Figure(width_in=2.3, height_in=1.8)
    _tri(f, [A, B, C], "UVW", (C, A, B), 0.6)
    f.side_label(A, B, "10", center=C)
    f.side_label(A, C, "$x$", center=B)
    f.side_label(B, C, "$y$", center=A)
    f.angle_label(A, B, C, "$34" + DEG, dist=2.0)
    f.angle_label(B, A, C, "$56" + DEG, dist=1.8)
    f.text(P(1.2, 5.6), "$x \\approx 8.3$", layer="answer", size=11)
    f.text(P(1.2, 4.4), "$y \\approx 5.6$", layer="answer", size=11)
    return f


@figure(f"{S}_8")
def q8() -> Figure:
    """WXY right at X, WX = 9.1 (opposite alpha at Y), WY = 25.4; beta at W, alpha at Y; alpha = arcsin(9.1/25.4).
    Nov 20: was WX = 13, WY = 24 (32.8/57.2), almost new Test A item 4 (33.4/56.6). 21/69 and 9.1, 25.4, 23.7 are
    in no Unit 4 test, progress check, or lesson."""
    wx, wy = 9.1, 25.4
    xy = np.sqrt(wy ** 2 - wx ** 2)
    X, W, Y = P(0, 0), P(0, wx), P(xy, 0)
    assert np.isclose(dist(W, X), wx) and np.isclose(dist(W, Y), wy) and np.isclose(angle_deg(X, W, Y), 90)
    alpha, beta = angle_deg(Y, W, X), angle_deg(W, X, Y)
    assert np.isclose(alpha, np.degrees(np.arcsin(wx / wy))) and np.isclose(alpha + beta, 90)
    assert round(alpha) == 21 and round(beta) == 69 and round(xy, 1) == 23.7
    f = Figure(width_in=2.5, height_in=1.3)
    _tri(f, [W, X, Y], "WXY", (X, W, Y), 0.9)
    f.side_label(W, X, "9.1", center=Y)
    f.side_label(W, Y, "25.4", center=X)
    f.angle_label(W, X, Y, "$\\beta$", dist=2.2)
    f.angle_label(Y, W, X, "$\\alpha$", dist=5.5)
    f.side_label(X, Y, "$\\approx 23.7$", center=W, layer="answer")
    f.text(P(22.4, 5.6), "$\\alpha \\approx 21^\\circ$", layer="answer", size=11)
    f.text(P(22.4, 3.3), "$\\beta \\approx 69^\\circ$", layer="answer", size=11)
    return f


@figure(f"{S}_9")
def q9() -> Figure:
    """Key sketch: flagpole, 35 m from the base, 26 degrees up, h = 35 tan 26."""
    h = 35 * np.tan(np.radians(26))
    B, T, Y = P(0, 0), P(0, h), P(35, 0)
    assert abs(h - 17.07) < 0.01 and abs(angle_deg(Y, T, B) - 26) < 0.1
    f = Figure(width_in=2.2, height_in=1.2)
    f.poly(np.array([B, T, Y]), layer="answer")
    f.right_angle(B, T, Y, size=2.0, layer="answer")
    f.side_label(B, Y, "35 m", center=T, layer="answer")
    f.side_label(B, T, "$h$", center=Y, layer="answer")
    f.angle_label(Y, T, B, "$26" + DEG, dist=9, layer="answer")
    return f


@figure(f"{S}_11")
def q11() -> Figure:
    """Key sketch: school 44 ft tall, Mai looks up 64 degrees, d = 44 / tan 64."""
    d = 44 / np.tan(np.radians(64))
    B, T, M = P(0, 0), P(0, 44), P(d, 0)
    assert abs(d - 21.46) < 0.01 and abs(angle_deg(M, T, B) - 64) < 0.1
    f = Figure(width_in=1.4, height_in=1.8)
    f.poly(np.array([B, T, M]), layer="answer")
    f.right_angle(B, T, M, size=2.5, layer="answer")
    f.side_label(B, T, "44 ft", center=M, layer="answer")
    f.side_label(B, M, "$d$", center=T, layer="answer")
    f.angle_label(M, T, B, "$64" + DEG, dist=6, layer="answer")
    return f


@figure(f"{S}_10")
def q10() -> Figure:
    """Tent with vertical pole side; rope 54 ft from the top corner at 18 degrees to the ground."""
    B, T, St = P(0, 0), P(0, 16.687), P(51.357, 0)
    assert abs(dist(T, St) - 54) < 0.01 and abs(angle_deg(St, T, B) - 18) < 0.1
    assert np.isclose(angle_deg(B, T, St), 90)
    f = Figure(width_in=2.8, height_in=1.2)
    f.poly(P((-14, 0), (0, 16.687), (0, 0)), fill="0.9")
    f.seg(P(-18, 0), P(58, 0))
    f.seg(T, St)
    f.right_angle(B, T, St, size=2.2)
    f.side_label(T, St, "54 ft", center=B)
    f.side_label(B, T, "$h$", center=P(-14, 0))
    f.angle_label(St, T, B, "$18" + DEG, dist=12)
    f.text(P(30, 15), "$h \\approx 16.7$ ft", layer="answer", size=11)
    return f

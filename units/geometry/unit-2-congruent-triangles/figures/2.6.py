"""Lesson 2.6 figures: Side-Angle-Side triangle congruence (lessons/2.6.yaml).
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Source images were 72-144 dpi (and one EMF), so every figure is redrawn here from the source layout.
"""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_lengths, collinear, dist, figure, is_rigid_image, needs_reflection,
    rotate, translate,
)

S = '2.6'


def pol(r, deg, origin=(0.0, 0.0)):
    """Point at distance r and direction deg (degrees) from origin."""
    t = np.radians(deg)
    return np.array(origin, dtype=float) + r * np.array((np.cos(t), np.sin(t)))


# ---------------------------------------------------------------- warm-up key: triangle DEF, actual size
@figure(f"{S}_warmup")
def warmup() -> Figure:
    E = np.array((0.0, 0.0))
    F = pol(5, 0)
    D = pol(4, 50)
    assert_lengths([(E, D, 4), (E, F, 5)])
    assert np.isclose(angle_deg(E, D, F), 50)
    f = Figure(actual_size="cm")
    f.poly([D, E, F], layer="answer")
    f.dots([D, E, F], layer="answer")
    f.label_poly([D, E, F], "DEF", layer="answer")
    f.arc(E, F, D, r=0.8, layer="answer")
    f.angle_label(E, F, D, "$50^\\circ$", dist=1.35, layer="answer", size=10)
    f.side_label(E, D, "4 cm", center=F, layer="answer", size=10)
    f.side_label(E, F, "5 cm", center=D, layer="answer", size=10)
    return f


# ---------------------------------------------------------------- Problem 1: SAS theorem (source image1)
@figure(f"{S}_sas")
def sas() -> Figure:
    B = np.array((0.0, 0.0))
    A, G, C = P((-1.2, 1.2), (-1.2, -1.2), (2.8, 0))
    assert np.isclose(dist(A, B), dist(G, B))
    assert np.isclose(angle_deg(B, A, C), angle_deg(B, G, C))
    f = Figure(width_in=2.1, height_in=1.6)
    for a, b in ((A, B), (G, B), (B, C), (A, C), (G, C)):
        f.seg(a, b)
    f.dots([A, B, C, G])
    f.label(A, "A", direction=(-1, 0.6))
    f.label(G, "G", direction=(-1, -0.6))
    f.label(C, "C", direction=(1, 0))
    f.label(B, "B", direction=(-1, 0))
    f.ticks(A, B, n=1)
    f.ticks(G, B, n=1)
    f.ticks(B, C, n=2)
    f.arc(B, A, C, r=0.3)
    f.arc(B, G, C, r=0.3)
    return f


# ---------------------------------------------------------------- Problem 2: bowtie POQ, ROS (source image2)
@figure(f"{S}_bowtie")
def bowtie() -> Figure:
    O = np.array((0.0, 0.0))
    Pp, Q = P((-0.9, 1.3), (0.65, 1.3))
    R, Sv = -Pp, -Q
    assert collinear(Pp, O, R) and collinear(Q, O, Sv)
    assert np.isclose(dist(Pp, O), dist(R, O)) and np.isclose(dist(Q, O), dist(Sv, O))
    f = Figure(width_in=1.5, height_in=1.9)
    f.seg(Pp, R)
    f.seg(Q, Sv)
    f.seg(Pp, Q)
    f.seg(Sv, R)
    f.dots([Pp, Q, R, Sv, O])
    f.label(Pp, "P", direction=(-1, 0.3))
    f.label(Q, "Q", direction=(1, 0.3))
    f.label(R, "R", direction=(1, -0.3))
    f.label(Sv, "S", direction=(-1, -0.3))
    f.label(O, "O", direction=(-1, 0))
    f.ticks(Pp, O, n=1)
    f.ticks(O, R, n=1)
    f.ticks(Q, O, n=2)
    f.ticks(O, Sv, n=2)
    f.arc(O, Pp, Q, r=0.3, layer="answer")
    f.arc(O, R, Sv, r=0.3, layer="answer")
    return f


# ---------------------------------------------------------------- Problem 3: isosceles ABP, auxiliary line PM
@figure(f"{S}_iso")
def iso() -> Figure:
    Pv, B, A = P((0, 2.6), (-0.85, 0), (0.85, 0))
    M = (A + B) / 2
    assert np.isclose(dist(B, Pv), dist(A, Pv))
    assert np.isclose(angle_deg(Pv, B, M), angle_deg(Pv, A, M))
    f = Figure(width_in=1.9, height_in=2.9)
    f.poly([Pv, B, A])
    f.dots([Pv, B, A])
    f.label(Pv, "P", direction=(0, 1))
    f.label(B, "B", direction=(-1, -0.5))
    f.label(A, "A", direction=(1, -0.5))
    f.seg(Pv, M, layer="answer")
    f.dots([M], layer="answer")
    f.label(M, "M", direction=(0, -1), layer="answer")
    f.arc(Pv, B, M, n=1, r=0.8, ticks=1, layer="answer")
    f.arc(Pv, A, M, n=1, r=0.8, ticks=1, layer="answer")
    f.ticks(B, Pv, n=1, layer="answer")
    f.ticks(A, Pv, n=1, layer="answer")
    return f


# ---------------------------------------------------------------- CYU 1: square FEHG, diagonal FH (source image5)
@figure(f"{S}_square")
def square() -> Figure:
    G, H, E, F = rotate(P((0, 0), (2, 0), (2, 2), (0, 2)), 10, about=(1, 1))
    for a, b, c in ((F, E, G), (E, H, F), (H, G, E), (G, F, H)):
        assert np.isclose(angle_deg(a, b, c), 90)
    assert_lengths([(F, E, 2), (E, H, 2), (H, G, 2), (G, F, 2)])
    assert np.isclose(angle_deg(F, E, H), 45) and np.isclose(angle_deg(H, E, F), 45)
    f = Figure(width_in=1.7, height_in=1.7)
    f.poly([F, E, H, G])
    f.dots([F, E, H, G])
    f.label_poly([F, E, H, G], "FEHG")
    f.seg(F, H, layer="answer")
    f.angle_label(F, E, H, "$45^\\circ$", dist=0.55, layer="answer", size=10)
    f.angle_label(F, G, H, "$45^\\circ$", dist=0.55, layer="answer", size=10)
    return f


# ---------------------------------------------------------------- exit 2 key: a sample SAS pair
@figure(f"{S}_exit")
def exit_key() -> Figure:
    B = np.array((0.0, 0.0))
    A, C = pol(1.2, 105), pol(1.7, 10)
    D, E, F = translate(np.array([A, B, C]), (2.8, 0))
    assert is_rigid_image(np.array([A, B, C]), np.array([D, E, F]))
    assert not needs_reflection(np.array([A, B, C]), np.array([D, E, F]))
    f = Figure(width_in=2.8, height_in=1.25)
    for (x, y, z), nm in (((A, B, C), "ABC"), ((D, E, F), "DEF")):
        f.poly([x, y, z], layer="answer")
        f.dots([x, y, z], layer="answer")
        f.label_poly([x, y, z], nm, layer="answer")
        f.ticks(x, y, n=1, layer="answer")
        f.ticks(y, z, n=2, layer="answer")
        f.arc(y, x, z, r=0.3, layer="answer")
    return f


# ---------------------------------------------------------------- practice 1: SAS by rigid motions (SN image9)
@figure(f"{S}_pr_order")
def pr_order() -> Figure:
    B = np.array((0.0, 0.0))
    C, A = pol(1.3, 30), pol(1.6, -80)
    E = np.array((2.5, 0.1))
    F, D = pol(1.3, 95, E), pol(1.6, -15, E)
    assert is_rigid_image(np.array([A, B, C]), np.array([D, E, F]))
    assert np.isclose(angle_deg(B, A, C), angle_deg(E, D, F))
    f = Figure(width_in=2.0, height_in=1.5)
    for x, y in ((B, C), (B, A), (E, F), (E, D)):
        f.seg(x, y)
    f.dots([A, B, C, D, E, F])
    f.label(A, "A", direction=(-1, -0.3))
    f.label(B, "B", direction=(-1, 0.2))
    f.label(C, "C", direction=(1, 0.3))
    f.label(D, "D", direction=(0.6, -1))
    f.label(E, "E", direction=(-1, -0.3))
    f.label(F, "F", direction=(0.8, 0.6))
    f.ticks(B, C, n=1)
    f.ticks(E, F, n=1)
    f.ticks(B, A, n=2)
    f.ticks(E, D, n=2)
    f.arc(B, A, C, r=0.25)
    f.arc(E, D, F, r=0.25)
    return f


# ---------------------------------------------------------------- practice 2: C is the midpoint (source image3)
@figure(f"{S}_pr_mid")
def pr_mid() -> Figure:
    C = np.array((0.0, 0.0))
    A, B, D, E = P((-1.1, 1), (1.1, 1), (-1.1, -1), (1.1, -1))
    assert collinear(A, C, E) and collinear(B, C, D)
    assert np.allclose((B + D) / 2, C)
    f = Figure(width_in=1.5, height_in=1.4)
    for x, y in ((A, B), (D, E), (A, E), (B, D)):
        f.seg(x, y)
    f.dots([A, B, C, D, E])
    f.label(A, "A", direction=(-1, 0.4))
    f.label(B, "B", direction=(1, 0.4))
    f.label(D, "D", direction=(-1, -0.4))
    f.label(E, "E", direction=(1, -0.4))
    f.label(C, "C", direction=(1, 0))
    return f


# ---------------------------------------------------------------- practice 3: kite KQAB, QB bisects angle KQA
@figure(f"{S}_pr_kite")
def pr_kite() -> Figure:
    Q = np.array((0.0, 0.0))
    down = -116.0
    B = pol(1.7, down)
    K, A = pol(1.0, down - 58), pol(1.0, down + 58)
    assert np.isclose(dist(Q, K), dist(Q, A))
    assert np.isclose(angle_deg(Q, K, B), angle_deg(Q, A, B))
    f = Figure(width_in=1.1, height_in=1.25)
    f.poly([Q, A, B, K])
    f.seg(Q, B)
    f.dots([Q, A, B, K])
    f.label(Q, "Q", direction=(0.3, 1))
    f.label(A, "A", direction=(1, 0))
    f.label(B, "B", direction=(0, -1))
    f.label(K, "K", direction=(-1, 0.3))
    return f


# ---------------------------------------------------------------- practice 4: m angle T (base angles 58)
@figure(f"{S}_pr_t")
def pr_t() -> Figure:
    R, I = P((0, 0), (2, 0))
    T = np.array((1.0, np.tan(np.radians(58))))
    assert np.isclose(dist(R, T), dist(I, T))
    assert np.isclose(angle_deg(T, R, I), 64)
    f = Figure(width_in=1.4, height_in=1.2)
    f.poly([R, I, T])
    f.dots([R, I, T])
    f.label_poly([R, I, T], "RIT")
    f.ticks(R, T, n=2)
    f.ticks(I, T, n=2)
    f.angle_label(R, I, T, "$58^\\circ$", dist=0.45, size=10)
    return f


# ---------------------------------------------------------------- practice 5: m angle G (right isosceles)
@figure(f"{S}_pr_g")
def pr_g() -> Figure:
    N, A, G = P((0, 0), (0, 1.6), (1.6, 0))
    assert np.isclose(angle_deg(N, A, G), 90) and np.isclose(angle_deg(G, A, N), 45)
    f = Figure(width_in=1.35, height_in=1.35)
    f.poly([N, G, A])
    f.dots([N, G, A])
    f.label_poly([N, G, A], "NGA")
    f.ticks(A, N, n=1)
    f.ticks(N, G, n=1)
    f.right_angle(N, A, G, size=0.16)
    return f


# ---------------------------------------------------------------- practice 6: x (exterior angles, source image8)
@figure(f"{S}_pr_x")
def pr_x() -> Figure:
    L = np.array((0.0, 0.0))
    Rv = pol(2.0, 0)
    Bv = pol(2.0, -70)
    assert np.isclose(angle_deg(L, Rv, Bv), 70)
    assert np.isclose(angle_deg(Rv, L, Bv), 55) and np.isclose(angle_deg(Bv, L, Rv), 55)
    up_l = L + 0.9 * (L - Bv) / dist(L, Bv)
    up_r = Rv + 0.9 * (Rv - Bv) / dist(Rv, Bv)
    assert np.isclose(angle_deg(L, up_l, Rv), 110) and np.isclose(angle_deg(Rv, up_r, L), 125)
    f = Figure(width_in=1.35, height_in=1.45)
    f.seg(L, Rv)
    f.seg(Bv, L)
    f.seg(Bv, Rv)
    f.arrow(L, up_l, layer="given", dashed=False)
    f.arrow(Rv, up_r, layer="given", dashed=False)
    f.ticks(L, Rv, n=2)
    f.ticks(L, Bv, n=2)
    f.angle_label(L, up_l, Rv, "$110^\\circ$", dist=0.42, size=10)
    f.angle_label(Rv, up_r, L, "$x$", dist=0.35, size=11)
    return f


# ---------------------------------------------------------------- practice 7: m angle QPR (source image13)
@figure(f"{S}_pr_qpr")
def pr_qpr() -> Figure:
    R, Sv = P((0, 0), (1, 0))
    Q = pol(1.0, 60, Sv)
    Pv = np.array((-dist(Q, R), 0.0))
    assert collinear(Pv, R, Sv)
    assert np.isclose(dist(Pv, R), dist(Q, R)) and np.isclose(dist(Q, Sv), dist(R, Sv))
    assert np.isclose(angle_deg(Sv, R, Q), 120) and np.isclose(angle_deg(Pv, Q, R), 15)
    f = Figure(width_in=2.4, height_in=0.85)
    f.seg(Pv, Sv)
    f.seg(Pv, Q)
    f.seg(R, Q)
    f.seg(Q, Sv)
    f.dots([Pv, R, Sv, Q])
    f.label(Pv, "P", direction=(-1, 0))
    f.label(R, "R", direction=(0, -1))
    f.label(Sv, "S", direction=(0.4, -1))
    f.label(Q, "Q", direction=(1, 0.5))
    return f

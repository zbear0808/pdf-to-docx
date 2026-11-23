"""Figures for lesson "4.7" (lessons/4.7.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
4.7_1 and 4.7_exit are key-only sketches (everything on the answer layer), used as key figures.
4.7_3 (Burj Khalifa) and 4.7_4 (City Hall) are B&W line drawings that replace the source photos.
Loop: uv run lesson-builder figs <unit> -l "4.7" (0 errors, no label warnings).
"""
import math

import numpy as np

from lesson_builder.figures import Figure, angle_deg, dist, figure, mark_congruent

S = '4.7'
R = "answer"
D = math.radians


def pt(x, y):
    return np.array((float(x), float(y)))


def tan(d):
    return math.tan(D(d))


def _tri(f, pts, names, layer="given", ra=None, ra_size=0.25, overrides=None):
    """Triangle outline, vertex dots, vertex names, and a right-angle mark at index ra."""
    pts = np.asarray(pts, dtype=float)
    f.poly(pts, layer=layer)
    f.dots(pts, layer=layer)
    if names is not None:
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


def _outline(cx, tiers):
    """Symmetric stepped outline about x = cx. tiers: [(y_bottom, y_top, half_width), ...] bottom to top."""
    left = []
    for y0, y1, w in tiers:
        left += [pt(cx - w, y0), pt(cx - w, y1)]
    right = [pt(2 * cx - p[0], p[1]) for p in reversed(left)]
    return left + right


# Warm-up: hypotenuse AB = 6 on top, angle B = 20, right angle at C below.
W_A, W_B = pt(0, 0), pt(6, 0)
W_C = W_A + 6 * math.sin(D(20)) * np.array((math.cos(D(-70)), math.sin(D(-70))))
assert abs(angle_deg(W_C, W_A, W_B) - 90) < 1e-6 and abs(angle_deg(W_B, W_A, W_C) - 20) < 1e-6
assert abs(dist(W_A, W_C) - 2.0521) < 1e-4 and abs(dist(W_B, W_C) - 5.6382) < 1e-4


@figure(f"{S}_warmup")
def warmup() -> Figure:
    """Student and key share this image: the side names and AC go in the fill boxes."""
    f = Figure(width_in=3.6, height_in=1.6)
    _tri(f, [W_A, W_B, W_C], "ABC", ra=2, ra_size=0.25)
    _ang(f, W_B, W_A, W_C, 20, 1.3, 1.9)
    f.side_label(W_A, W_B, "6", W_C)
    return f


# Problem 1 (key sketch): right angle at C, angle A = 42, AC = 4 cm; the item asks for AB only.
T1_C, T1_A = pt(0, 0), pt(4, 0)
T1_B = pt(0, 4 * tan(42))
assert abs(T1_B[1] - 3.6016) < 1e-4 and abs(dist(T1_A, T1_B) - 4 / math.cos(D(42))) < 1e-9
assert round(dist(T1_A, T1_B), 1) == 5.4 and abs(angle_deg(T1_B, T1_A, T1_C) - 48) < 1e-6


@figure(f"{S}_1")
def p1() -> Figure:
    f = Figure(width_in=2.8, height_in=2.4)
    _tri(f, [T1_A, T1_B, T1_C], "ABC", layer=R, ra=2, ra_size=0.3)
    _ang(f, T1_A, T1_B, T1_C, 42, 0.8, 1.3, layer=R, size=10)
    f.side_label(T1_A, T1_C, "4 cm", T1_B, layer=R, size=10)
    f.side_label(T1_A, T1_B, r"$AB \approx 5.4$", T1_C, layer=R, size=10, offset_pt=24)
    return f


# Problem 2: Burj Khalifa, observer C 250 m from the base B, 73 degrees up to the top A. Drawn to scale (m).
B3_C, B3_B = pt(0, 0), pt(250, 0)
B3_A = pt(250, 250 * tan(73))
assert abs(B3_A[1] - 817.7132) < 1e-3 and abs(angle_deg(B3_C, B3_B, B3_A) - 73) < 1e-6


@figure(f"{S}_3")
def p3() -> Figure:
    f = Figure(width_in=2.4, height_in=3.0)
    tiers = [(0, 90, 46), (90, 300, 34), (300, 470, 24), (470, 590, 15), (590, 690, 8), (690, 760, 3)]
    out = _outline(250, tiers)
    out = out[:len(out) // 2] + [B3_A] + out[len(out) // 2:]
    f.poly(out, closed=False, lw=0.8)
    f.seg(pt(-25, 0), pt(330, 0))
    _tri(f, [B3_A, B3_B, B3_C], "ABC", ra=1, ra_size=22, overrides={"B": (0.4, -1)})
    _ang(f, B3_C, B3_B, B3_A, 73, 45, 85)
    f.side_label(B3_C, B3_B, "250 m", B3_A, size=11)
    f.side_label(B3_A, B3_B, r"$AB \approx 817.7$ m", B3_C, layer=R, size=10, offset_pt=42)
    return f


# QuickNotes: generic angle of elevation picture.
Q_E, Q_B, Q_T = pt(0, 0), pt(5, 0), pt(5, 3)


@figure(f"{S}_qn")
def qn() -> Figure:
    assert abs(angle_deg(Q_B, Q_E, Q_T) - 90) < 1e-9
    f = Figure(width_in=2.9, height_in=1.7)
    f.seg(pt(-0.4, 0), pt(5.6, 0))
    f.seg(Q_B, Q_T, lw=2.0)
    f.seg(Q_E, Q_T)
    f.dots([Q_E, Q_T])
    f.right_angle(Q_B, Q_E, Q_T, size=0.25)
    f.arc(Q_E, Q_B, Q_T, r=1.0)
    f.text(pt(3.15, 0.36), "angle of elevation", size=9)
    f.label(Q_E, "you", italic=False, direction=(-1, -0.3), size=9)
    f.label(Q_T, "top", italic=False, direction=(1, 0.3), size=9)
    f.side_label(Q_B, Q_T, "height", Q_E, size=9)
    f.side_label(Q_E, Q_B, "distance from the bottom", Q_T, size=9)
    f.side_label(Q_E, Q_T, "line of sight", Q_B, size=9, offset_pt=14)
    return f


# Problem 3: City Hall line drawing. Given: building, street, "you" 1,300 ft from the base (routine givens).
# Key adds the triangle, the right angle, the 23 degree angle at you, and h. Drawn to scale (ft).
H4_C, H4_B = pt(0, 0), pt(1300, 0)
H4_A = pt(1300, 1300 * tan(23))
assert abs(H4_A[1] - 551.8173) < 1e-3 and abs(angle_deg(H4_C, H4_B, H4_A) - 23) < 1e-6


@figure(f"{S}_4")
def p4() -> Figure:
    f = Figure(width_in=4.6, height_in=1.8)
    cx, top = 1300, H4_A[1]
    f.seg(pt(-40, 0), pt(1600, 0))
    block = [pt(1060, 0), pt(1060, 180), pt(1110, 180), pt(1110, 150), pt(1240, 150), pt(1240, 190),
             pt(1255, 190), pt(1255, 400), pt(1265, 400), pt(1265, 460), pt(1285, 520), pt(cx, 520)]
    half = block + [pt(2 * cx - p[0], p[1]) for p in reversed(block)]
    f.poly(half, closed=False, lw=0.9)
    for y in (50, 100):
        f.seg(pt(1060, y), pt(1540, y), lw=0.4)
    f.seg(pt(1255, 300), pt(1345, 300), lw=0.4)
    f.seg(pt(cx, 520), H4_A, lw=1.5)
    f.dots([H4_C])
    f.label(H4_C, "you", italic=False, direction=(-1, -0.4), size=12)
    f.side_label(H4_C, H4_B, "1,300 ft", H4_A, size=12)
    _tri(f, [H4_A, H4_B, H4_C], [None, None, None], layer=R, ra=1, ra_size=30)
    _ang(f, H4_C, H4_B, H4_A, 23, 200, 340, layer=R, size=12)
    f.text(pt(1615, 330), r"$h \approx 551.8$ ft", layer=R, size=12, fixed=True)
    return f


# Exit ticket (key sketch): redwood, you 220 ft from the base, 60 degrees up.
X_C, X_B = pt(0, 0), pt(220, 0)
X_A = pt(220, 220 * tan(60))
assert abs(X_A[1] - 381.0512) < 1e-3 and abs(angle_deg(X_C, X_B, X_A) - 60) < 1e-6


@figure(f"{S}_exit")
def exit_() -> Figure:
    f = Figure(width_in=1.8, height_in=2.2)
    f.poly([pt(212, 0), pt(212, 70)], closed=False, layer=R, lw=0.8)
    f.poly([pt(228, 0), pt(228, 70)], closed=False, layer=R, lw=0.8)
    f.poly([pt(212, 70), pt(180, 70), X_A, pt(260, 70), pt(228, 70)], closed=False, layer=R, lw=0.8)
    _tri(f, [X_A, X_B, X_C], [None, None, None], layer=R, ra=1, ra_size=16)
    _ang(f, X_C, X_B, X_A, 60, 40, 72, layer=R, size=10)
    f.label(X_C, "you", italic=False, direction=(-1, -0.4), layer=R, size=10)
    f.side_label(X_C, X_B, "220 ft", X_A, layer=R, size=10)
    f.side_label(X_B, X_A, r"$h \approx 381.1$ ft", X_C, layer=R, size=10, offset_pt=26)
    return f

# Practice 1: Eiffel Tower. Mai 80 ft away, 85.7 degrees up. x is stretched 4x so the picture reads;
# the label says 85.7 degrees and the arc is not to scale.
E_K = 4
E_H = 80 * tan(85.7)
assert abs(E_H - 1063.9659) < 1e-3 and round(E_H, 1) == 1064.0
E_M, E_B, E_T = pt(0, 0), pt(80 * E_K, 0), pt(80 * E_K, E_H)


def _eiffel_w(y):
    return 8 + 70 * (1 - min(y, 1000) / 1000) ** 3


@figure(f"{S}_p1")
def pr1() -> Figure:
    f = Figure(width_in=2.0, height_in=2.8)
    cx = E_B[0]
    ys = np.linspace(0, 1000, 41)
    for s in (-1, 1):
        f.poly([pt(cx + s * _eiffel_w(y), y) for y in ys] + [pt(cx, 1000)], closed=False, lw=0.8)
    arch = [pt(cx + 45 * math.cos(t), 60 * math.sin(t)) for t in np.linspace(0, math.pi, 19)]
    f.poly(arch, closed=False, lw=0.8)
    for y in (200, 400):
        w = _eiffel_w(y) + 8
        f.seg(pt(cx - w, y), pt(cx + w, y), lw=0.8)
    f.seg(pt(cx, 1000), E_T, lw=1.2)
    f.seg(pt(-25, 0), pt(cx + 110, 0))
    _tri(f, [E_M, E_B, E_T], [None, None, None], ra=1, ra_size=22)
    f.arc(E_M, E_B, E_T, r=60)
    f.angle_label(E_M, E_B, E_T, r"$85.7^\circ$", dist=200, size=10)
    f.label(E_M, "Mai", italic=False, direction=(-1, -0.4), size=10)
    f.side_label(E_M, E_B, "80 ft", E_T, size=10)
    f.side_label(E_B, E_T, r"$h \approx 1{,}064$ ft", E_M, layer=R, size=10, offset_pt=22)
    return f


# Practice 3 (key sketch): Gateway Arch 630 ft tall, Priya looks up 50 degrees; d = 630 / tan 50.
G_D = 630 / tan(50)
assert abs(G_D - 528.633) < 1e-3
G_P, G_B, G_T = pt(0, 0), pt(G_D, 0), pt(G_D, 630)


@figure(f"{S}_p3")
def pr3() -> Figure:
    """Given layer: an empty sketch box (student copy). Answer layer: the labeled sketch inside it."""
    assert abs(angle_deg(G_P, G_B, G_T) - 50) < 1e-6
    f = Figure(width_in=3.2, height_in=2.4)
    f.poly([pt(-330, -170), pt(1000, -170), pt(1000, 760), pt(-330, 760)], lw=0.5)
    _tri(f, [G_T, G_B, G_P], None, layer=R, ra=1, ra_size=40)
    _ang(f, G_P, G_B, G_T, 50, 90, 150, layer=R, size=10)
    f.label(G_P, "Priya", italic=False, direction=(-1, -0.4), layer=R, size=10)
    f.side_label(G_B, G_T, "630 ft", G_P, layer=R, size=10)
    f.side_label(G_P, G_B, r"$d \approx 528.6$ ft", G_T, layer=R, size=10)
    return f


# Practice 2: right angle at C, BC = 12, angle A = 27.
R2_A = pt(0, 0)
R2_C = pt(12 / tan(27), 0)
R2_B = pt(R2_C[0], 12)
assert abs(R2_C[0] - 23.5513) < 1e-4 and abs(dist(R2_A, R2_B) - 26.4323) < 1e-4
assert abs(angle_deg(R2_B, R2_A, R2_C) - 63) < 1e-6


@figure(f"{S}_p2")
def pr2() -> Figure:
    f = Figure(width_in=2.4, height_in=1.3)
    _tri(f, [R2_A, R2_C, R2_B], "ACB", ra=1, ra_size=1.2)
    _ang(f, R2_A, R2_C, R2_B, 27, 4.0, 6.5)
    f.side_label(R2_C, R2_B, "12", R2_A)
    _ang(f, R2_B, R2_A, R2_C, 63, 2.2, 4.0, layer=R, size=10)
    f.side_label(R2_A, R2_B, r"$\approx 26.4$", R2_C, layer=R, size=10)
    f.side_label(R2_A, R2_C, r"$\approx 23.6$", R2_B, layer=R, size=10)
    return f


# Practice 4: right angle at C, BC = 8.5, AB = x, angle A = 32 (sin 32 = 8.5 / x).
R4_A = pt(0, 0)
R4_C = pt(8.5 / tan(32), 0)
R4_B = pt(R4_C[0], 8.5)
assert abs(R4_C[0] - 13.603) < 1e-3 and abs(8.5 / dist(R4_A, R4_B) - math.sin(D(32))) < 1e-9


@figure(f"{S}_p4")
def pr4() -> Figure:
    f = Figure(width_in=2.2, height_in=1.3)
    _tri(f, [R4_A, R4_C, R4_B], "ACB", ra=1, ra_size=0.8)
    _ang(f, R4_A, R4_C, R4_B, 32, 2.6, 4.3)
    f.side_label(R4_C, R4_B, "8.5", R4_A)
    f.side_label(R4_A, R4_B, "$x$", R4_C)
    return f


# Practice 5: kite string 12 ft at 45 degrees; height = 12 sin 45 = 12 / sqrt 2.
K_S = pt(0, 0)
K_F = pt(12 * math.cos(D(45)), 0)
K_K = pt(K_F[0], 12 * math.sin(D(45)))
assert abs(K_K[1] - 12 / math.sqrt(2)) < 1e-9 and abs(dist(K_S, K_K) - 12) < 1e-9


@figure(f"{S}_p5")
def pr5() -> Figure:
    f = Figure(width_in=1.9, height_in=1.9)
    _tri(f, [K_S, K_F, K_K], None, ra=1, ra_size=0.5)
    kite = [K_K, K_K + pt(-0.7, 1.3), K_K + pt(0.4, 2.4), K_K + pt(1.3, 1.0)]
    f.poly(kite, fill="0.85")
    f.seg(kite[0], kite[2], lw=0.6)
    f.seg(kite[1], kite[3], lw=0.6)
    _ang(f, K_S, K_F, K_K, 45, 1.2, 2.0, size=10)
    f.side_label(K_S, K_K, "12 ft", K_F, size=10)
    return f

# Practice 6: triangles ABC (right angle C) and EBD (right angle D) share vertex B; angle ABC = angle EBD.
S6_B, S6_C, S6_A = pt(0, 12), pt(0, 0), pt(-5, 0)
S6_D, S6_E = pt(0, 4.8), pt(3, 4.8)
assert abs(dist(S6_A, S6_B) - 13) < 1e-9 and abs(dist(S6_B, S6_D) - 7.2) < 1e-9
assert abs(angle_deg(S6_B, S6_A, S6_C) - angle_deg(S6_B, S6_E, S6_D)) < 1e-9
assert abs(dist(S6_B, S6_E) - 3 / (5 / 13)) < 1e-9 and abs(dist(S6_B, S6_E) - 7.8) < 1e-9


@figure(f"{S}_p6")
def pr6() -> Figure:
    f = Figure(width_in=2.1, height_in=2.9)
    f.poly([S6_A, S6_B, S6_C])
    f.poly([S6_B, S6_E, S6_D], closed=False)
    f.dots([S6_A, S6_B, S6_C, S6_D, S6_E])
    f.right_angle(S6_C, S6_A, S6_B, size=0.5)
    f.right_angle(S6_D, S6_B, S6_E, size=0.5)
    mark_congruent(f, [((S6_B, S6_A, S6_C), (S6_B, S6_E, S6_D))], r=1.6)
    f.label(S6_A, "A", direction=(-1, -0.3))
    f.label(S6_B, "B", direction=(0, 1))
    f.label(S6_C, "C", direction=(0.6, -1))
    f.label(S6_D, "D", direction=(-1, 0))
    f.label(S6_E, "E", direction=(1, -0.3))
    f.side_label(S6_A, S6_B, "13", S6_C)
    f.side_label(S6_A, S6_C, "5", S6_B)
    f.side_label(S6_D, S6_E, "3", S6_B)
    f.side_label(S6_B, S6_E, "$BE = 7.8$", S6_D, layer=R, size=10, offset_pt=26)
    return f

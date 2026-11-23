"""Lesson 3.9 figures: Angle-Angle similarity. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_distinct, assert_lengths, dilate, dist, figure, is_rigid_image,
    law_of_sines_side, midpoint, needs_reflection, reflect, rotate, similarity_ratio, translate,
)


def tri(base, a_left, a_right, left=(0, 0), turn=0.0):
    """[left, right, apex]: base along +x (then turned), base angles a_left and a_right (degrees)."""
    a, b = np.radians(a_left), np.radians(a_right)
    t = base * np.sin(b) / np.sin(a + b)              # law of sines: left side
    pts = P((0, 0), (base, 0), (t * np.cos(a), t * np.sin(a)))
    pts = translate(rotate(pts, turn), left)
    assert np.isclose(angle_deg(pts[0], pts[1], pts[2]), a_left)
    assert np.isclose(angle_deg(pts[1], pts[0], pts[2]), a_right)
    return pts


def _names(f, pts, names, dirs=None):
    f.poly(pts)
    f.dots(pts)
    c = np.mean(pts, axis=0)
    for i, (p, nm) in enumerate(zip(pts, names)):
        d = dirs[i] if dirs and dirs[i] is not None else p - c
        f.label(p, nm, direction=d)


# ---------------------------------------------------------------- warm-up: ASA as a tool
# PQR: QR = 2, angle Q = 70 (one arc), angle R = 80 (two arcs). P'Q'R' = dilation of PQR, k = 1/2.
# STU: a reflected copy of P'Q'R' with T <-> Q', U <-> R', S <-> P', so TU = 1.
@figure("3.9_warmup")
def warmup() -> Figure:
    Q, R, Pp = tri(2, 70, 80)
    big = np.array([Q, R, Pp])
    small = translate(dilate(big, 0.5, Q), (4.7, 0))
    Q1, R1, P1 = small
    stu = translate(reflect(small, (0, 0), (0, 1)), (13.8, 0))   # mirror image, shifted right
    T, U, S = stu
    assert np.isclose(similarity_ratio(big, small), 0.5)
    assert is_rigid_image(small, stu) and needs_reflection(small, stu)
    assert np.isclose(dist(T, U), 1) and np.isclose(dist(Q1, R1), 1) and np.isclose(dist(Q, R), 2)
    f = Figure(width_in=3.6, height_in=1.6)
    side = [(-1.3, -0.3), (1.3, -0.3), None]
    for pts, nm, dirs in ((big, ["Q", "R", "P"], side), (small, ["Q^{\\prime}", "R^{\\prime}", "P^{\\prime}"], side),
                          (stu, ["T", "U", "S"], [side[1], side[0], None])):
        _names(f, pts, nm, dirs=dirs)
        a, b, c = pts
        s = dist(a, b)
        f.arc(a, b, c, n=1, r=0.22 * s + 0.1)
        f.arc(b, a, c, n=2, r=0.22 * s + 0.1, gap=0.12)
    f.side_label(Q, R, "2", center=Pp, size=11)
    f.side_label(Q1, R1, "1", center=P1, size=11)
    f.side_label(T, U, "1", center=S, size=11)
    return f


# ---------------------------------------------------------------- Together 1: one pair of congruent angles is not enough
# Both triangles have a 45 degree angle (one arc); every angle is printed, so students only compare.
P1_A = tri(2.8, 45, 100)                            # 45, 100, 35
P1_B = translate(tri(3.3, 45, 60), (4.1, 0))       # 45, 60, 75
assert np.isclose(angle_deg(P1_A[2], P1_A[0], P1_A[1]), 35)
assert np.isclose(angle_deg(P1_B[2], P1_B[0], P1_B[1]), 75)
assert_distinct([100, 35, 60, 75])                  # only the 45 degree angles match


@figure("3.9_p1")
def p1() -> Figure:
    f = Figure(width_in=2.7, height_in=1.3)
    for t, (a, b, c) in ((P1_A, ("45°", "100°", "35°")), (P1_B, ("45°", "60°", "75°"))):
        f.poly(t)
        f.arc(t[0], t[1], t[2], r=0.4)
        f.angle_label(t[0], t[1], t[2], a, dist=0.95, size=9)
        f.angle_label(t[1], t[0], t[2], b, dist=0.6, size=9)
        f.angle_label(t[2], t[0], t[1], c, dist=1.0, size=9)
    return f


# ---------------------------------------------------------------- Partner 2: two angles fix the shape (actual size, cm)
# Base angles 45 (left) and 30 (right); the side between them is 2 cm and 6 cm, so k = 3 and the third angle is 105.
# Given: each side, its 45 degree ray (long enough to pass the apex), and since Nov 23 the start of its 30 degree side
# (short of the apex). Answer: the rest of each 30 degree side, the apex, "105°".
P2_SMALL = tri(2.0, 45, 30)
P2_BIG = translate(tri(6.0, 45, 30), (3.3, 0))
P2_RAYS = (1.5, 3.9)                                # printed length of each 45 degree ray, cm
P2_STARTS = (0.65, 1.4)                             # printed start of each 30 degree side, cm
assert np.isclose(similarity_ratio(P2_SMALL, P2_BIG), 3)
assert all(dist(t[0], t[2]) < r - 0.3 for t, r in zip((P2_SMALL, P2_BIG), P2_RAYS))
assert all(s < dist(t[1], t[2]) - 0.5 for t, s in zip((P2_SMALL, P2_BIG), P2_STARTS))   # students extend each one
assert np.isclose(angle_deg(P2_BIG[2], P2_BIG[0], P2_BIG[1]), 105)


@figure("3.9_p2")
def p2() -> Figure:
    f = Figure(actual_size="cm")
    assert_lengths([(P2_SMALL[0], P2_SMALL[1], 2), (P2_BIG[0], P2_BIG[1], 6)])
    for t, ray, start, base, name, r in ((P2_SMALL, P2_RAYS[0], P2_STARTS[0], "2 cm", "Triangle 1", 0.3),
                                         (P2_BIG, P2_RAYS[1], P2_STARTS[1], "6 cm", "Triangle 2", 0.45)):
        L, R, A = t
        u = (A - L) / dist(L, A)
        v = (A - R) / dist(R, A)
        assert np.isclose(angle_deg(R, L, R + start * v), 30)
        f.seg(L, R)
        f.seg(L, L + ray * u)
        f.seg(R, R + start * v)
        f.dots([L, R])
        f.arc(L, R, A, r=r)
        f.arc(R, L, A, n=2, r=r, gap=0.08)
        f.side_label(L, R, base, center=A, size=10)
        f.text(midpoint(L, R) + (0, -0.95), name, size=10)
        f.seg(R + start * v, A, layer="answer")
        f.dots([A], layer="answer")
    L, R, A = P2_BIG
    f.angle_label(L, R, A, "45°", dist=1.25, size=10)
    f.angle_label(R, L, A, "30°", dist=1.35, size=10)
    f.angle_label(A, L, R, "105°", dist=0.75, size=10, layer="answer")
    return f


# ---------------------------------------------------------------- in-class practice (v2): 40-60 and 40-80 triangles
# The Nov 19 exit ticket figure (3.9_exit), redrawn without the x label (part b asks only for y).
# ABC: A = 40, B = 60 (C = 80, not labeled). BC = 3, AB = 4.6 (rounded).
# DFE: D = 40, E = 80 (F = 60, not labeled). EF = 6, DE = 8.1 (rounded), DF = y.  A->D, B->F, C->E, k = 2.
# DFE sits on side DE (8.1), so "bottom side" matching (4.6 with 8.1) gives the wrong scale factor.
AP1 = tri(4.596, 40, 60)                                   # A, B, C
_aD, _aE, _aF = translate(tri(law_of_sines_side(6, 40, 60), 40, 80), (7.0, -0.4))   # D, E, F (left, right, apex)
AP2 = np.array([_aD, _aF, _aE])                            # D, F, E: same order as A, B, C
assert np.isclose(dist(AP1[1], AP1[2]), 3, atol=0.01) and np.isclose(dist(AP1[0], AP1[1]), 4.596)
assert np.isclose(angle_deg(AP1[2], AP1[0], AP1[1]), 80)  # the third angle students find
assert np.isclose(similarity_ratio(AP1, AP2), 2, atol=1e-3)
assert np.isclose(dist(AP2[0], AP2[2]), 8.08, atol=0.01)              # DE
assert np.isclose(2 * 4.6, 9.2)                                       # y = DF
assert_lengths([(AP1[1], AP1[2], 3), (AP1[0], AP1[1], 4.6), (AP2[2], AP2[1], 6), (AP2[0], AP2[2], 8.1),
                (AP2[0], AP2[1], 9.2)])


@figure("3.9_apply")
def apply_fig() -> Figure:
    A, B, C = AP1
    D, F, E = AP2
    f = Figure(width_in=4.6, height_in=2.05)
    _names(f, [A, B, C], "ABC")
    _names(f, [D, F, E], "DFE")
    f.angle_label(A, B, C, "40°", dist=1.15, size=10)
    f.angle_label(B, A, C, "60°", dist=0.95, size=10)
    f.angle_label(D, F, E, "40°", dist=2.3, size=10)
    f.angle_label(E, D, F, "80°", dist=1.05, size=10)
    f.side_label(B, C, "3", center=A, size=11)
    f.side_label(A, B, "4.6", center=C, size=11)
    f.side_label(E, F, "6", center=D, size=11)
    f.side_label(D, E, "8.1", center=F, size=11)
    f.side_label(D, F, "y", center=E, italic=True, size=11)
    return f


# ---------------------------------------------------------------- practice
# Pr 1: ABC with A = 68, AB = 8, AC = 6 (so B = 44). DEF: D = 68, F = 44, DE = 18. A->D, B->F, C->E, k = 3.
_pa = P((0, 0), (6, 0), (8 * np.cos(np.radians(68)), 8 * np.sin(np.radians(68))))   # A, C, B
assert np.isclose(angle_deg(_pa[2], _pa[0], _pa[1]), 44, atol=0.1)
assert np.isclose(3 * 8, 24)                                                       # DF = 3 * AB


@figure("3.9_pr1")
def pr1() -> Figure:
    A, C, B = _pa
    D2, E2, F2 = translate(rotate(dilate(_pa, 1.6, _pa[0]), -12), (13.0, 0.3))     # not to scale (k = 3 in the labels)
    assert np.isclose(similarity_ratio([A, C, B], [D2, E2, F2]), 1.6)
    assert_lengths([(A, B, 8), (A, C, 6)])
    f = Figure(width_in=3.1, height_in=1.9)
    _names(f, [A, C, B], "ACB")
    _names(f, [D2, E2, F2], "DEF")
    f.angle_label(A, C, B, "68°", dist=1.8, size=10)
    f.angle_label(B, A, C, "44°", dist=3.4, size=10)
    f.angle_label(D2, E2, F2, "68°", dist=2.4, size=10)
    f.angle_label(F2, D2, E2, "44°", dist=4.4, size=10)
    f.side_label(A, B, "8", center=C, size=10)
    f.side_label(A, C, "6", center=B, size=10)
    f.side_label(D2, E2, "18", center=F2, size=10)
    return f


# Pr 3: C is the center of a dilation with k = -0.9 (no lengths are printed): D = image of A, E = image of B.
_C3 = P((0, 0))[0]
_A3 = P((-2.6, -1.3))[0]
_B3 = translate(rotate(_A3 - _C3, 123), _C3)[0]
_B3 = _C3 + (_B3 - _C3) / dist(_B3, _C3) * dist(_A3, _C3) * np.sin(np.radians(36)) / np.sin(np.radians(21))
_D3, _E3 = dilate([_A3, _B3], -0.9, _C3)
assert np.isclose(angle_deg(_C3, _A3, _B3), 123)
assert np.isclose(angle_deg(_A3, _C3, _B3), 36) and np.isclose(angle_deg(_B3, _C3, _A3), 21)
assert np.isclose(angle_deg(_D3, _C3, _E3), 36)


@figure("3.9_pr3")
def pr3() -> Figure:
    f = Figure(width_in=2.8, height_in=1.85)
    f.poly([_A3, _B3, _C3])
    f.poly([_D3, _E3, _C3])
    f.dots([_A3, _B3, _C3, _D3, _E3])
    for p, nm, d in ((_A3, "A", (-1, -0.4)), (_B3, "B", (1, 0)), (_C3, "C", (0, 1)), (_D3, "D", (1, 0.3)),
                     (_E3, "E", (-1, 0.3))):
        f.label(p, nm, direction=d)
    f.angle_label(_A3, _B3, _C3, "36°", dist=1.0, size=10)
    f.angle_label(_B3, _A3, _C3, "21°", dist=1.6, size=10)
    f.angle_label(_D3, _E3, _C3, "36°", dist=0.9, size=10)
    f.arc(_A3, _B3, _C3, r=0.45)
    f.arc(_D3, _E3, _C3, r=0.45)
    f.angle_label(_C3, _A3, _B3, "123°", dist=0.8, size=10)
    return f


# Pr 5: sides are proportional (6:2 and 9:3), but the angles are not given, so we can't tell.
def _pgram(base, side, deg, at):
    a = np.asarray(at, float)
    u = side * np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])
    return np.array([a, a + u, a + u + (base, 0), a + (base, 0)])   # A, B, C, D


@figure("3.9_pr7")
def pr7() -> Figure:
    abcd = _pgram(6, 2, 70, (1.0, 6.6))
    wxyz = _pgram(9, 3, 72, (-0.6, 0))
    assert np.isclose(dist(wxyz[0], wxyz[3]) / dist(abcd[0], abcd[3]), dist(wxyz[0], wxyz[1]) / dist(abcd[0], abcd[1]))
    assert_lengths([(abcd[0], abcd[3], 6), (abcd[0], abcd[1], 2), (wxyz[0], wxyz[3], 9), (wxyz[0], wxyz[1], 3)])
    f = Figure(width_in=2.4, height_in=1.7)
    for q, nm in ((abcd, "ABCD"), (wxyz, "WXYZ")):
        f.poly(q)
        f.dots(q)
        for p, n, d in zip(q, nm, ((-1, -0.6), (-0.5, 1), (0.5, 1), (1, -0.6))):
            f.label(p, n, direction=d, size=11)
    c1, c2 = abcd.mean(0), wxyz.mean(0)
    for q, c, b, s in ((abcd, c1, "6", "2"), (wxyz, c2, "9", "3")):
        f.side_label(q[1], q[2], b, center=c, size=10)
        f.side_label(q[0], q[1], s, center=c, size=10)
        f.side_label(q[2], q[3], s, center=c, size=10)
        f.side_label(q[3], q[0], b, center=c, size=10)
    return f

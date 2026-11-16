"""Lesson 3.9 figures: Angle-Angle similarity. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_distinct, assert_lengths, dilate, dist, figure, is_rigid_image,
    needs_reflection, reflect, rotate, similarity_ratio, translate,
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


def law_of_sines_side(known, opp_known, opp_want):
    return known * np.sin(np.radians(opp_want)) / np.sin(np.radians(opp_known))


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


# ---------------------------------------------------------------- Together 1 and Partner 3 (key drawings)
@figure("3.9_p1_key")
def p1_key() -> Figure:
    t1 = tri(2.8, 45, 100)
    t2 = translate(tri(3.2, 45, 90), (4.0, 0))
    assert_distinct([angle_deg(t1[1], t1[0], t1[2]), angle_deg(t2[1], t2[0], t2[2])])
    f = Figure(width_in=3.2, height_in=1.4)
    for t, nm in ((t1, "Triangle 1"), (t2, "Triangle 2")):
        f.poly(t, layer="answer")
        f.arc(t[0], t[1], t[2], r=0.35, layer="answer")
        f.angle_label(t[0], t[1], t[2], "45°", dist=0.75, layer="answer", size=9)
        f.text(((t[0] + t[1]) / 2) + (0, -0.35), nm, layer="answer", size=10)
    f.angle_label(t1[1], t1[0], t1[2], "100°", dist=0.5, layer="answer", size=9)
    f.angle_label(t2[1], t2[0], t2[2], "90°", dist=0.55, layer="answer", size=9)
    return f


# 45 and 30 degree base angles; side between them 2 cm and 6 cm, so k = 3 and the third angle is 105.
P3_SMALL = tri(2.0, 45, 30)
P3_BIG = translate(tri(6.0, 45, 30), (2.8, 0))
assert np.isclose(similarity_ratio(P3_SMALL, P3_BIG), 3)


@figure("3.9_p3_key")
def p3_key() -> Figure:
    f = Figure(width_in=3.0, height_in=1.3)
    assert_lengths([(P3_SMALL[0], P3_SMALL[1], 2), (P3_BIG[0], P3_BIG[1], 6)])
    for t, base in ((P3_SMALL, "2 cm"), (P3_BIG, "6 cm")):
        f.poly(t, layer="answer")
        r = 0.4 if base == "6 cm" else 0.25
        f.arc(t[0], t[1], t[2], r=r, layer="answer")
        f.arc(t[1], t[0], t[2], n=2, r=r, gap=0.08, layer="answer")
        f.side_label(t[0], t[1], base, center=t[2], layer="answer", size=11)
    for txt, v, a, b, d in (("45°", 0, 1, 2, 0.85), ("30°", 1, 0, 2, 0.95), ("105°", 2, 0, 1, 0.6)):
        f.angle_label(P3_BIG[v], P3_BIG[a], P3_BIG[b], txt, dist=d, layer="answer", size=11)
    return f


# ---------------------------------------------------------------- Partner 6: add one measurement
# JKL: J = 50, K = 70 (so L = 60). XYZ: only X = 50 is given. The key adds Y = 70 (Z = 60 also works).
@figure("3.9_p6")
def p6() -> Figure:
    J, K, L = tri(4.4, 50, 70)
    X, Y, Z = tri(5.5, 50, 70, left=(13.6, 1.6), turn=160)
    assert np.isclose(angle_deg(L, J, K), 60) and np.isclose(angle_deg(Z, X, Y), 60)
    assert np.isclose(similarity_ratio([J, K, L], [X, Y, Z]), 1.25)
    f = Figure(width_in=3.6, height_in=1.5)
    _names(f, [J, K, L], "JKL")
    _names(f, [X, Y, Z], "XYZ")
    f.angle_label(J, K, L, "50°", dist=1.0, size=9)
    f.angle_label(K, J, L, "70°", dist=0.95, size=9)
    f.angle_label(X, Y, Z, "50°", dist=1.3, size=9)
    f.angle_label(Y, X, Z, "70°", dist=1.1, layer="answer", size=9)
    return f


# ---------------------------------------------------------------- CYU 1: bowtie, AD parallel CB
_A, _D = P((0, 0), (0, 2.6))
_E = P((2.7, 2.05))[0]
_C = _A + (3.6 / 2.7) * (_E - _A)
_B = _D + (3.6 / 2.7) * (_E - _D)
assert np.isclose(_C[0], _B[0])                           # CB vertical, so CB parallel to AD
assert np.isclose(angle_deg(_A, _D, _E), angle_deg(_C, _B, _E))
assert np.isclose(similarity_ratio([_D, _E, _A], [_B, _E, _C]), 1 / 3)   # DEA ~ BEC


@figure("3.9_cyu")
def cyu() -> Figure:
    f = Figure(width_in=2.4, height_in=1.75)
    f.seg(_A, _C)
    f.seg(_D, _B)
    f.seg(_A, _D)
    f.seg(_C, _B)
    f.dots([_A, _B, _C, _D, _E])
    for p, nm, d in ((_A, "A", (-1, -0.5)), (_D, "D", (-1, 0.5)), (_E, "E", (0, 1)), (_C, "C", (0.6, 1)),
                     (_B, "B", (0.6, -1))):
        f.label(p, nm, direction=d)
    f.arc(_A, _D, _E, r=0.45)
    f.arc(_C, _B, _E, r=0.3)
    f.arc(_E, _D, _A, n=2, r=0.25, gap=0.07, layer="answer")
    f.arc(_E, _B, _C, n=2, r=0.25, gap=0.07, layer="answer")
    return f


# ---------------------------------------------------------------- exit ticket: 40-60 and 40-80 triangles
# ABC: A = 40, B = 60 (C = 80). BC = 3, AB = 4.6 (rounded), AC = x.
# DEF: D = 40, E = 80 (F = 60). EF = 6, DE = 8.1 (rounded), DF = y.  A->D, B->F, C->E, k = 2.
# DEF sits on side DE (8.1), so "bottom side" matching (4.6 with 8.1) gives the wrong scale factor.
EX1 = tri(4.596, 40, 60)                                   # A, B, C
_eD, _eE, _eF = translate(tri(law_of_sines_side(6, 40, 60), 40, 80), (7.0, -0.4))   # D, E, F (left, right, apex)
EX2 = np.array([_eD, _eF, _eE])                            # D, F, E: same order as A, B, C
assert np.isclose(dist(EX1[1], EX1[2]), 3, atol=0.01) and np.isclose(dist(EX1[0], EX1[1]), 4.596)
assert np.isclose(similarity_ratio(EX1, EX2), 2, atol=1e-3)
assert np.isclose(law_of_sines_side(3, 40, 60), 4.042, atol=1e-3)     # x, true value; 8.1 / 2 = 4.05
assert np.isclose(dist(EX2[0], EX2[2]), 8.08, atol=0.01)              # DE
assert np.isclose(2 * 4.6, 9.2)                                       # y
assert_lengths([(EX1[1], EX1[2], 3), (EX1[0], EX1[1], 4.6), (EX1[0], EX1[2], 4.05),
                (EX2[2], EX2[1], 6), (EX2[0], EX2[2], 8.1), (EX2[0], EX2[1], 9.2)])


@figure("3.9_exit")
def exit_fig() -> Figure:
    A, B, C = EX1
    D, F, E = EX2
    f = Figure(width_in=3.6, height_in=1.6)
    _names(f, [A, B, C], "ABC")
    _names(f, [D, F, E], "DFE")
    f.angle_label(A, B, C, "40°", dist=1.25, size=8.5)
    f.angle_label(B, A, C, "60°", dist=1.05, size=8.5)
    f.angle_label(D, F, E, "40°", dist=2.2, size=8.5)
    f.angle_label(E, D, F, "80°", dist=1.0, size=8.5)
    f.side_label(B, C, "3", center=A, size=11)
    f.side_label(A, B, "4.6", center=C, size=11)
    f.side_label(A, C, "x", center=B, italic=True, size=11)
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


# Pr 5: quadrilateral Q is a dilation of P with k = 5/4 (4 -> 5, 2 -> 2.5).
_T1, _T2 = P((0, 0), (4, 0))
_I = _T2 + 3 * np.array([np.cos(np.radians(205)), np.sin(np.radians(205))])
_Bt = _I + 2 * np.array([-0.15, -1]) / np.hypot(0.15, 1)
_QP = np.array([_T1, _T2, _I, _Bt])
_QQ = translate(dilate(_QP, 1.25, _T1), (5.2, -2.6))
assert np.isclose(similarity_ratio(_QP, _QQ), 1.25)
assert np.isclose(dist(_QQ[2], _QQ[3]), 2.5) and np.isclose(dist(_QQ[0], _QQ[1]), 5)
assert_lengths([(_QP[0], _QP[1], 4), (_QP[1], _QP[2], 3), (_QP[2], _QP[3], 2), (_QQ[0], _QQ[1], 5), (_QQ[2], _QQ[3], 2.5)])


@figure("3.9_pr5")
def pr5() -> Figure:
    f = Figure(width_in=2.3, height_in=1.6)
    for q, nm, at in ((_QP, "P", (-0.9, -1.6)), (_QQ, "Q", None)):
        f.poly(q)
        f.dots(q)
        c = (q[0] + q[1] + q[2]) / 3 + (-0.2, -0.15) if at is None else np.asarray(at, float)
        f.text(c, f"${nm}$", size=12)
    f.side_label(_QP[0], _QP[1], "4", center=_QP[2], size=10)
    f.side_label(_QP[1], _QP[2], "3", center=_QP[0], size=10)
    f.side_label(_QP[2], _QP[3], "2", center=_QP[0], size=10)
    f.side_label(_QQ[0], _QQ[1], "5", center=_QQ[2], size=10)
    f.side_label(_QQ[2], _QQ[3], "2.5", center=_QQ[0], size=10)
    return f


# Pr 7: sides are proportional (6:2 and 9:3), but the angles are not given, so we can't tell.
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


# Pr 8: right triangles inscribed on a diameter. Small: 3-x-5 with x = 4. Big: diameter 20, k = 4, leg 16.
def _circle(f, c, r):
    t = np.linspace(0, 2 * np.pi, 120)
    f.poly(np.c_[c[0] + r * np.cos(t), c[1] + r * np.sin(t)])


@figure("3.9_pr8")
def pr8() -> Figure:
    f = Figure(width_in=3.0, height_in=1.5)
    for c, r, lab in (((0, 0), 2.5, "small"), ((8.6, 0), 5.0, "big")):
        c = np.asarray(c, float)
        L, R = c + (-r, 0), c + (r, 0)
        V = L + (3 / 5) * (2 * r) * np.array([3 / 5, 4 / 5])           # 3-4-5 shape, right angle at V
        assert np.isclose(angle_deg(V, L, R), 90)
        _circle(f, c, r)
        f.poly([L, R, V])
        f.right_angle(V, L, R, size=0.12 * r)
        f.dots([c])
        if lab == "small":
            assert np.isclose(dist(V, R), 4) and np.isclose(dist(L, V), 3)
            f.label(c, "R", direction=(0, -1), size=11)
            f.side_label(L, V, "3", center=R, size=10)
            f.side_label(V, R, "x", center=L, italic=True, size=10)
        else:
            f.label(c, "Q", direction=(0, -1), size=11)
            f.side_label(V, R, "16", center=2 * (V + R) / 2 - L, size=10)    # inside the triangle
    return f

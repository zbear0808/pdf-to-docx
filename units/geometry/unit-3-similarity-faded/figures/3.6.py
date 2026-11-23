"""Lesson 3.6 figures: similarity and transformations. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_lengths, dilate, dist, figure, needs_reflection, rotate,
    similarity_ratio, translate,
)


def _ray(f, a, b, extend=1.25, layer="given", dashed=False):
    a, b = np.asarray(a, float), np.asarray(b, float)
    f.seg(a, a + extend * (b - a), layer=layer, dashed=dashed)


def _warmup():
    # Square ADCB (side 2), center P. G and H are true images of A and D (k = 2), but GE and HF were not scaled.
    Pc = P((0, 0))[0]
    A, D, C, B = P((-3, 1.2), (-3, -0.8), (-5, -0.8), (-5, 1.2))
    G, H = dilate([A, D], 2, Pc)
    E, F = G + (B - A), H + (C - D)          # widths copied, not doubled
    assert np.isclose(dist(G, H), 2 * dist(A, D)) and np.isclose(dist(G, E), dist(A, B))
    assert similarity_ratio([A, D, C, B], [G, H, F, E]) is None   # not a similar copy
    assert_lengths([(A, D, 2), (B, A, 2), (G, H, 4), (E, G, 2)])
    f = Figure(width_in=3.0, height_in=1.9)
    _ray(f, Pc, G, 1.08)
    _ray(f, Pc, H, 1.08)
    for q in ([A, D, C, B], [G, H, F, E]):
        f.poly(q)
        f.dots(q)
    f.dots([Pc])
    for pt, nm, d in ((Pc, "P", (0.3, -1)), (A, "A", (0.5, 1)), (D, "D", (0.5, -1)), (C, "C", (-1, 0.4)),
                      (B, "B", (0.3, 1)), (G, "G", (0.4, 1)), (H, "H", (0.4, -1)), (E, "E", (-1, 0.4)),
                      (F, "F", (-1, -0.4))):
        f.label(pt, nm, direction=d)
    Sc, Rc = (A + C) / 2, (G + F) / 2
    f.side_label(A, D, "2", Sc, size=10, offset_pt=-9)
    f.side_label(B, A, "2", Sc, size=10, offset_pt=-9)
    f.side_label(G, H, "4", Rc, size=10, offset_pt=-9)
    f.side_label(E, G, "2", Rc, size=10, offset_pt=-9)
    return f, (Pc, B, C, G, H)


@figure("3.6_warmup")
def warmup() -> Figure:
    return _warmup()[0]


@figure("3.6_warmup_key")
def warmup_key() -> Figure:
    # key: the true image (k = 2) puts E and F on rays PB and PC
    f, (Pc, B, C, G, H) = _warmup()
    E2, F2 = dilate([B, C], 2, Pc)
    _ray(f, Pc, E2, 1.0, layer="answer", dashed=True)
    _ray(f, Pc, F2, 1.0, layer="answer", dashed=True)
    f.poly([G, H, F2, E2], layer="answer", dashed=True)
    return f


# Together: right triangle ABC (6-8-10) onto DEF (3-4-5)
_A, _B, _C = P((0, 0), (4, 0), (0, 3))
_SRC = np.array([_A, _B, _C])
_D = P((7.4, 0.3))[0]
_IMG = translate(rotate(dilate(_SRC, 0.5, _A), 90, _A), _D - _A)   # D, E, F


@figure("3.6_together")
def together() -> Figure:
    D, E, Fp = _IMG
    assert np.isclose(similarity_ratio(_SRC, _IMG), 0.5) and not needs_reflection(_SRC, _IMG)
    # the sequence in the key: translate A to D, rotate 90 deg CCW about D, dilate center D by 1/2
    step = dilate(rotate(translate(_SRC, _D - _A), 90, _D), 0.5, _D)
    assert np.allclose(step, _IMG)
    assert_lengths([(_A, _B, 8), (_A, _C, 6), (_B, _C, 10), (D, E, 4), (D, Fp, 3), (E, Fp, 5)])
    assert np.isclose(angle_deg(_A, _B, _C), 90) and np.isclose(angle_deg(D, E, Fp), 90)
    f = Figure(width_in=3.6, height_in=1.6)
    for pts, names in ((_SRC, "ABC"), (_IMG, "DEF")):
        f.poly(pts)
        f.dots(pts)
    f.right_angle(_A, _B, _C, size=0.3)
    f.right_angle(D, E, Fp, size=0.2)
    f.label(_A, "A", direction=(-1, -0.6))
    f.label(_B, "B", direction=(1, -0.6))
    f.label(_C, "C", direction=(-0.6, 1))
    f.label(D, "D", direction=(1, -0.6))
    f.label(E, "E", direction=(0.3, 1))
    f.label(Fp, "F", direction=(-1, -0.6))
    c1, c2 = _SRC.mean(0), _IMG.mean(0)
    f.side_label(_A, _B, "8", c1, size=10)
    f.side_label(_A, _C, "6", c1, size=10)
    f.side_label(_B, _C, "10", c1, size=10)
    f.side_label(D, E, "4", c2, size=10)
    f.side_label(D, Fp, "3", c2, size=10)
    f.side_label(E, Fp, "5", c2, size=10)
    return f


# Partner 3: nested right triangles, center O
_O = P((0, 0))[0]
_un = np.array([np.cos(np.radians(100)), np.sin(np.radians(100))])     # direction of ray ON
_up = np.array([-_un[1], _un[0]]) * -1                                  # perpendicular, toward P
_R, _N = _O + 4 * _un, _O + 6 * _un
_Q, _Pt = _R + 5 * _up, _N + 7.5 * _up


def _nested(lsize=10) -> Figure:
    k = dist(_O, _N) / dist(_O, _R)
    assert_lengths([(_R, _Q, 5), (_N, _Pt, 7.5)])
    assert np.isclose(k, 1.5) and np.allclose(dilate([_Q, _R], k, _O), [_Pt, _N])
    assert np.isclose(angle_deg(_R, _O, _Q), 90) and np.isclose(angle_deg(_N, _O, _Pt), 90)
    f = Figure(width_in=3.6, height_in=2.3)
    f.poly([_O, _N, _Pt])
    f.seg(_R, _Q)
    f.dots([_O, _R, _N, _Q, _Pt])
    f.right_angle(_R, _O, _Q, size=0.4)
    f.right_angle(_N, _R, _Pt, size=0.4)
    for pt, nm, d in ((_O, "O", (0, -1)), (_R, "R", (-1, 0)), (_N, "N", (-1, 0.3)), (_Q, "Q", (1, -0.3)),
                      (_Pt, "P", (1, 0.3))):
        f.label(pt, nm, direction=d)
    c = (_O + _N + _Pt) / 3
    f.side_label(_R, _Q, "5", c + 2 * _un, size=lsize)
    f.side_label(_N, _Pt, "7.5", _O, size=lsize)
    return f


# Partner 4: square F (side 3) and square G (side 12) share vertex V
_V = P((0, 0))[0]
_u1 = np.array([np.cos(np.radians(-40)), np.sin(np.radians(-40))])
_u2 = np.array([-_u1[1], _u1[0]]) * -1
_G = np.array([_V, _V + 12 * _u1, _V + 12 * (_u1 + _u2), _V + 12 * _u2])
_F = np.array([_V, _V - 3 * _u1, _V - 3 * (_u1 + _u2), _V - 3 * _u2])


# Partner 5: right triangles EAB and TQR; AB || QR, AE || QT
_Aq, _Bq, _Eq = P((0, 0), (8, 0), (0, 15))
_TQR = translate(dilate([_Eq, _Aq, _Bq], 0.4, _Aq), (13, 7))


@figure("3.6_soup")
def soup() -> Figure:
    T, Q, R = _TQR
    EAB = np.array([_Eq, _Aq, _Bq])
    assert np.isclose(similarity_ratio(EAB, _TQR), 0.4)
    assert_lengths([(_Aq, _Eq, 15), (_Aq, _Bq, 8), (_Eq, _Bq, 17), (Q, T, 6), (Q, R, 3.2), (T, R, 6.8)])
    assert np.isclose(angle_deg(_Aq, _Bq, _Eq), 90) and np.isclose(angle_deg(Q, R, T), 90)
    f = Figure(width_in=2.6, height_in=2.4)
    for tri in (EAB, _TQR):
        f.poly(tri)
        f.dots(tri)
    f.right_angle(_Aq, _Bq, _Eq, size=0.9)
    f.right_angle(Q, R, T, size=0.6)
    for pt, nm, d in ((_Eq, "E", (-0.5, 1)), (_Aq, "A", (-1, -0.5)), (_Bq, "B", (1, -0.5)), (T, "T", (-0.5, 1)),
                      (Q, "Q", (-1, -0.5)), (R, "R", (1, -0.5))):
        f.label(pt, nm, direction=d)
    c1, c2 = EAB.mean(0), _TQR.mean(0)
    f.side_label(_Aq, _Eq, "15", c1, size=12)
    f.side_label(_Aq, _Bq, "8", c1, size=12)
    f.side_label(_Eq, _Bq, "17", c1, size=12)
    f.side_label(Q, T, "6", c2, size=12)
    f.side_label(Q, R, "3.2", c2, size=12)
    f.side_label(T, R, "6.8", c2, size=12)
    return f


# Practice 1: square ABCD (side 5) onto square EFGH (side 2)
_SQ = P((0, 5), (0, 0), (5, 0), (5, 5))                         # A, B, C, D
_E = P((8.2, 0.6))[0]
_EFGH = translate(dilate(rotate(_SQ - _SQ[0], 45 + 90, (0, 0)), 0.4, (0, 0)), _E)


@figure("3.6_pr_squares")
def pr_squares() -> Figure:
    E, Fq, G, H = _EFGH
    assert np.isclose(similarity_ratio(_SQ, _EFGH), 0.4) and not needs_reflection(_SQ, _EFGH)
    # key sequence: translate A to E, rotate about E (B' onto ray EF), dilate center E by 2/5
    moved = translate(_SQ, _E - _SQ[0])
    ang = np.degrees(np.arctan2(*(Fq - E)[::-1]) - np.arctan2(*(moved[1] - E)[::-1]))
    assert np.allclose(dilate(rotate(moved, ang, E), 0.4, E), _EFGH)
    assert_lengths([(_SQ[0], _SQ[1], 5), (E, Fq, 2)])
    f = Figure(width_in=2.6, height_in=1.3)
    for sq, names in ((_SQ, "ABCD"), (_EFGH, "EFGH")):
        f.poly(sq)
        f.dots(sq)
        f.label_poly(sq, names)
    f.side_label(_SQ[0], _SQ[1], "5", _SQ.mean(0), size=10)
    f.side_label(E, Fq, "2", _EFGH.mean(0), size=10)
    return f


# Practice 7: dilate C (k = 3/4) and segment AB (k = 1/2) from center D
_Dd = P((0, 0))[0]
_Cd = P((-2.1, 2.8))[0]
_Ad, _Bd = P((1.6, 1.3))[0], P((4.0, 3.25))[0]


# Practice 7: dilation with center C takes ABC onto A'B'C (CB = 9, CB' = 6, CA = 6, CA' = 4, angle B = 40)
_Cp = np.array([0.0, 0.0])
_uB = np.array([np.cos(np.radians(160)), np.sin(np.radians(160))])
_angC = 180 - 40 - (180 - np.degrees(np.arcsin(9 * np.sin(np.radians(40)) / 6)))   # A is acute (about 74.6)
_uA = rotate([_uB], _angC, (0, 0))[0]
_Bp, _Ap = _Cp + 9 * _uB, _Cp + 6 * _uA
_B2p, _A2p = _Cp + 6 * _uB, _Cp + 4 * _uA

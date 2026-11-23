"""Unit 3 Test, Version A. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_lengths, dilate, dist, figure, needs_reflection, reflect, rotate, similarity_ratio,
    translate,
)


# 1: triangle ABC and its image A'B'C' (rotate 75 deg, scale factor 2)
_ABC = P((0, 0), (1.6, 0), (2.0, 0.7))
_IMG1 = translate(rotate(dilate(_ABC, 2.0, _ABC[0]), 75, _ABC[0]), (-1.2, -1.6))


@figure("Unit 3 Test A_ratios")
def ratios() -> Figure:
    assert np.isclose(similarity_ratio(_ABC, _IMG1), 2.0) and not needs_reflection(_ABC, _IMG1)
    f = Figure(width_in=2.4, height_in=2.0)
    f.poly(_ABC)
    f.dots(_ABC)
    f.label_poly(_ABC, ["A", "B", "C"])
    f.poly(_IMG1)
    f.dots(_IMG1)
    f.label_poly(_IMG1, ["A'", "B'", "C'"], overrides={"A'": (-1, 0), "C'": (-1, 0)}, offset_pt=14)
    return f


# 2: side splitter. D on AB, E on AC, DE || BC. AD = 5, DB = 6, BC = 8, DE = x
_A2, _B2, _C2 = P((0, 0), (11, 0), (6.2, 6.4))
_D2 = _A2 + 5 / 11 * (_B2 - _A2)
_E2 = _A2 + 5 / 11 * (_C2 - _A2)


@figure("Unit 3 Test A_splitter")
def splitter() -> Figure:
    assert np.isclose(dist(_B2, _C2), 8) and np.isclose(dist(_D2, _E2), 40 / 11)
    assert_lengths([(_A2, _D2, 5), (_D2, _B2, 6), (_B2, _C2, 8), (_D2, _E2, 40 / 11)])
    f = Figure(width_in=2.4, height_in=1.5)
    tri = np.array([_A2, _B2, _C2])
    f.poly(tri)
    f.seg(_D2, _E2)
    f.dots([_A2, _B2, _C2, _D2, _E2])
    f.parallel_marks(_D2, _E2, size=0.45)
    f.parallel_marks(_B2, _C2, size=0.45)
    f.label(_A2, "A", direction=(-1, -0.4))
    f.label(_B2, "B", direction=(1, -0.4))
    f.label(_C2, "C", direction=(0, 1))
    f.label(_D2, "D", direction=(0, -1))
    f.label(_E2, "E", direction=(-1, 0.4))
    c = tri.mean(0)
    f.side_label(_A2, _D2, "5", c, size=11)
    f.side_label(_D2, _B2, "6", c, size=11)
    f.side_label(_B2, _C2, "8", c, size=11)
    f.side_label(_D2, _E2, "x", _A2, size=12, italic=True)
    return f


# 3: triangle ABC (AB = 15, AC = 20, BC = 24, angle A = 85, angle B = 56) and triangle DEF (EF = 6, E = 39, F = 56)
_B3 = P((0, 0))[0]
_C3 = P((24, 0))[0]
_A3 = 15 * np.array([np.cos(np.radians(56)), np.sin(np.radians(56))])
_BIG = rotate(np.array([_A3, _B3, _C3]), -12, (0, 0))                   # A, B, C
# D, F, E (A->D, B->F, C->E). True scale factor is 1/4; drawn at 0.55 so the angle labels fit (labels carry the math)
_SMALL = translate(rotate(dilate(_BIG, 0.55, (0, 0)), 40, (0, 0)), (28, 6))


@figure("Unit 3 Test A_similar")
def similar() -> Figure:
    A, B, C = _BIG
    D, Fp, E = _SMALL
    assert round(angle_deg(A, B, C)) == 85 and round(angle_deg(B, A, C)) == 56 and round(angle_deg(C, A, B)) == 39
    assert round(dist(A, C)) == 20 and round(dist(B, C)) == 24 and round(dist(A, B)) == 15
    assert similarity_ratio(_BIG, _SMALL) is not None          # same angles: E = C = 39, F = B = 56, D = A = 85
    assert np.isclose(24 * 0.25, 6) and np.isclose(15 * 0.25, 3.75) and np.isclose(20 * 0.25, 5)
    assert_lengths([(A, B, 15), (A, C, 20), (B, C, 24)])   # small triangle is not to scale with the big one (prompt says so)
    assert round(angle_deg(E, D, Fp)) == 39 and round(angle_deg(Fp, D, E)) == 56 and round(angle_deg(D, E, Fp)) == 85
    f = Figure(width_in=3.6, height_in=2.1)
    for tri, names in ((_BIG, "ABC"), (_SMALL, "DFE")):
        f.poly(tri)
        f.dots(tri)
        f.label_poly(tri, names)
    f.side_label(A, B, "15", _BIG.mean(0), size=11)
    f.side_label(A, C, "20", _BIG.mean(0), size=11)
    f.side_label(B, C, "24", _BIG.mean(0), size=11)
    f.side_label(E, Fp, "6", _SMALL.mean(0), size=11)
    f.arc(A, B, C, r=1.6)
    f.angle_label(A, B, C, r"$85^\circ$", dist=3.4, size=10)
    f.arc(B, A, C, r=2.4)
    f.angle_label(B, A, C, r"$56^\circ$", dist=4.4, size=10)
    f.arc(C, A, B, r=3.2)      # third angle printed (Nov 19): the triangle sum is routine for part a
    f.angle_label(C, A, B, r"$39^\circ$", dist=6.4, size=10)
    f.arc(E, D, Fp, r=1.4)
    f.angle_label(E, D, Fp, r"$39^\circ$", dist=3.4, size=10)
    f.arc(Fp, D, E, r=1.2)
    f.angle_label(Fp, D, E, r"$56^\circ$", dist=3.4, size=10)
    return f


# 4: dilate triangle ABC, center P on side AC, scale factor 3
_A4, _B4, _C4, _P4 = P((0, 0), (1.6, 1.6), (0, 2.0), (0, 0.8))


@figure("Unit 3 Test A_dilate")
def dilate_abc() -> Figure:
    src = np.array([_A4, _B4, _C4])
    img = dilate(src, 3, _P4)
    assert np.allclose(img, [(0, -1.6), (4.8, 3.2), (0, 4.4)])
    f = Figure(width_in=2.4, height_in=2.8)
    f.poly(src)
    f.dots([_A4, _B4, _C4, _P4])
    f.label(_A4, "A", direction=(-1, -0.3))
    f.label(_B4, "B", direction=(1, 0))
    f.label(_C4, "C", direction=(-1, 0.3))
    f.label(_P4, "P", direction=(-1, 0))
    f.seg(_P4, img[1], layer="answer", dashed=True)
    f.poly(img, layer="answer")
    f.dots(img, layer="answer")
    f.label(img[0], "A'", direction=(-1, -0.3), layer="answer")
    f.label(img[1], "B'", direction=(1, 0), layer="answer")
    f.label(img[2], "C'", direction=(-1, 0.3), layer="answer")
    return f


# 5: rectangle ABCD, E on BC, F on AD, EF perpendicular to AD, angle AED = 90. EF = 8, ED = 10, so FD = 6
_A5, _F5, _D5 = P((0, 0), (32 / 3, 0), (50 / 3, 0))
_B5, _E5, _C5 = P((0, 8), (32 / 3, 8), (50 / 3, 8))


@figure("Unit 3 Test A_rect")
def rect() -> Figure:
    assert np.isclose(dist(_E5, _D5), 10) and np.isclose(dist(_F5, _D5), 6)
    assert np.isclose(angle_deg(_E5, _A5, _D5), 90)
    assert_lengths([(_E5, _F5, 8), (_E5, _D5, 10)])
    f = Figure(width_in=2.8, height_in=1.5)
    f.poly([_A5, _B5, _C5, _D5])
    f.seg(_A5, _E5)
    f.seg(_E5, _D5)
    f.seg(_E5, _F5)
    f.dots([_A5, _B5, _C5, _D5, _E5, _F5])
    f.right_angle(_F5, _E5, _D5, size=0.9)
    f.right_angle(_E5, _A5, _D5, size=0.9)
    for pt, nm, d in ((_A5, "A", (-1, -1)), (_B5, "B", (-1, 1)), (_C5, "C", (1, 1)), (_D5, "D", (1, -1)),
                      (_E5, "E", (0, 1)), (_F5, "F", (0, -1))):
        f.label(pt, nm, direction=d)
    f.side_label(_E5, _F5, "8", _A5, size=11)
    f.side_label(_E5, _D5, "10", _F5, size=11)
    return f


# 6: right triangles ABC (AC = 7) and DEF (DF = 3). Dilate center B by 3/7, reflect across AB, translate B to E
_B6, _A6, _C6 = P((0, 0), (0, 5.6), (4.2, 0))
_E6 = P((-1.4, 0))[0]
_DEF = translate(reflect(dilate([_A6, _B6, _C6], 3 / 7, _B6), _A6, _B6), _E6 - _B6)   # D, E, F


@figure("Unit 3 Test A_seq")
def seq() -> Figure:
    D, E, Fp = _DEF
    ABC = np.array([_A6, _B6, _C6])
    assert np.isclose(dist(D, Fp), 3) and np.isclose(dist(_A6, _C6), 7) and np.allclose(E, _E6)
    assert np.isclose(similarity_ratio(ABC, _DEF), 3 / 7) and needs_reflection(ABC, _DEF)
    assert_lengths([(_A6, _C6, 7), (D, Fp, 3)])
    f = Figure(width_in=2.2, height_in=2.0)
    for tri in (ABC, _DEF):
        f.poly(tri)
        f.dots(tri)
    f.right_angle(_B6, _A6, _C6, size=0.35)
    f.right_angle(E, D, Fp, size=0.3)
    for pt, nm, d in ((_A6, "A", (0, 1)), (_B6, "B", (0, -1)), (_C6, "C", (1, -0.5)),
                      (D, "D", (0, 1)), (E, "E", (0, -1)), (Fp, "F", (-1, -0.5))):
        f.label(pt, nm, direction=d)
    f.side_label(_A6, _C6, "7", ABC.mean(0), size=11)
    f.side_label(D, Fp, "3", _DEF.mean(0), size=11)
    return f

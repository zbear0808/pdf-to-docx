"""Figures for lesson "2.7" (lessons/2.7.yaml): ASA triangle congruence and the parallelogram theorem.
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Shapes follow the teacher's source drawings (2.7 & 2.9 Student Notes, 2.7 Practice Problems), redrawn because the
source images are under 150 dpi at print size.
Loop: uv run lesson-builder figs units/geometry/unit-2-congruent-triangles -l 2.7
"""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, collinear, dist, figure, is_parallel, is_rigid_image,
                                    mark_congruent, mark_parallel, midpoint, needs_reflection, reflect, rotate,
                                    translate, triangle_from_angles)

S = '2.7'


# ---------------------------------------------------------------- warm-up: DOG (two angles) vs CAT (ASA)
@figure(f"{S}_warmup_key")
def warmup_key() -> Figure:
    """Key for the warm-up drawing: two DOGs of different sizes (same angles) and the one CAT (CA = 5 cm)."""
    big = triangle_from_angles((0, 0), (4.0, 0), 75, 45)
    small = triangle_from_angles((5.6, 0), (7.8, 0), 75, 45)
    C, A, T = triangle_from_angles((9.6, 0), (14.6, 0), 75, 45)
    for tri in (big, small, (C, A, T)):
        assert np.isclose(angle_deg(tri[2], tri[0], tri[1]), 60)
    assert np.isclose(dist(C, A), 5) and not np.isclose(dist(big[0], big[1]), dist(small[0], small[1]))
    f = Figure(width_in=4.6, height_in=1.75)
    L = "answer"
    for D, G, O in (big, small):
        f.poly([D, G, O], layer=L)
        f.dots([D, G, O], layer=L)
        f.label(D, "D", layer=L, direction=(-1, -0.4))
        f.label(G, "G", layer=L, direction=(1, -0.4))
        f.label(O, "O", layer=L, direction=(0, 1))
    f.angle_label(big[0], big[1], big[2], r'$75^\circ$', layer=L)
    f.angle_label(big[1], big[0], big[2], r'$45^\circ$', layer=L, dist=1.5)
    f.text((3.9, -0.95), "two DOGs: same angles, different sizes", layer=L)
    f.poly([C, A, T], layer=L)
    f.dots([C, A, T], layer=L)
    f.label(C, "C", layer=L, direction=(-1, -0.4))
    f.label(A, "A", layer=L, direction=(1, -0.4))
    f.label(T, "T", layer=L, direction=(0, 1))
    f.angle_label(C, A, T, r'$75^\circ$', layer=L)
    f.angle_label(A, C, T, r'$45^\circ$', layer=L, dist=1.5)
    f.side_label(C, A, "5 cm", center=T, layer=L)
    return f


# ---------------------------------------------------------------- Together 1: the ASA proof pair (source image1)
_L = P((0.77, -0.35), (0.08, -1.55), (1.82, -3.33))           # source left triangle, px / 100, y up
_R = translate(rotate(_L, -60, about=_L[0]), (3.86, -0.10))   # right triangle: same shape, turned 60 deg clockwise
assert is_rigid_image(_L, _R) and not needs_reflection(_L, _R)


@figure(f"{S}_asa_pair")
def asa_pair() -> Figure:
    """Two congruent triangles. Key: one labeling with W -> D, X -> E, Y -> F and the ASA marks."""
    W, X, Y = _L
    D, E, F = _R
    f = Figure(width_in=2.8, height_in=1.9)
    f.poly(_L)
    f.poly(_R)
    L = "answer"
    f.label_poly(_L, "WXY", layer=L)
    f.label_poly(_R, "DEF", layer=L)
    mark_congruent(f, [((W, X), (D, E)), ((W, X, Y), (D, E, F)), ((X, W, Y), (E, D, F))], layer=L,
                   size=0.16, r=[0.42, 0.42])
    return f


# ---------------------------------------------------------------- bowtie (notes ASA example and practice 1)
_A, _C = P((0, 0), (2.2, 1.8))
_E = midpoint(_A, _C)
_D = np.array((0.0, 1.15))
_B = 2 * _E - _D
assert collinear(_D, _E, _B) and is_parallel(_D, _A, _C, _B)
assert np.isclose(angle_deg(_A, _D, _E), angle_deg(_C, _B, _E))


def _bowtie(vertical_marks: bool) -> Figure:
    f = Figure(width_in=2.0, height_in=1.65)
    f.seg(_D, _A)
    f.seg(_A, _C)
    f.seg(_D, _B)
    f.seg(_C, _B)
    f.dots([_A, _B, _C, _D, _E])
    f.label(_D, "D", direction=(-1, 0.3))
    f.label(_A, "A", direction=(-0.6, -1))
    f.label(_E, "E", direction=(0, 1))
    f.label(_C, "C", direction=(0.6, 1))
    f.label(_B, "B", direction=(1, -0.3))
    groups = [((_A, _E), (_E, _C)), ((_A, _D, _E), (_C, _B, _E))]
    if vertical_marks:
        groups.append(((_E, _D, _A), (_E, _B, _C)))
    mark_congruent(f, groups, size=0.13, r=[0.3, 0.26])
    return f


@figure(f"{S}_bowtie")
def bowtie() -> Figure:
    """Together 2: angle A, side AE, vertical angle at E marked; DEA matches BEC."""
    return _bowtie(vertical_marks=True)


@figure(f"{S}_pr_bowtie")
def pr_bowtie() -> Figure:
    """Practice 1: only the given marks (angle A, angle C, AE = CE); students find the vertical angles."""
    return _bowtie(vertical_marks=False)


# ---------------------------------------------------------------- partner: parallelogram ABCD (Cool-down figure)
_PA, _PB, _PC, _PD = P((0.8, 1.5), (3.2, 1.5), (2.4, 0), (0, 0))
assert is_parallel(_PA, _PB, _PD, _PC) and is_parallel(_PA, _PD, _PB, _PC)
assert np.isclose(angle_deg(_PB, _PA, _PD), angle_deg(_PD, _PC, _PB))   # alternate interior, diagonal BD
assert np.isclose(angle_deg(_PD, _PA, _PB), angle_deg(_PB, _PC, _PD))


@figure(f"{S}_para")
def para() -> Figure:
    """Student: labeled ABCD. Key: parallel arrows, diagonal BD, and the two pairs of alternate interior angles."""
    A, B, C, D = _PA, _PB, _PC, _PD
    f = Figure(width_in=2.5, height_in=1.35)
    f.poly([A, B, C, D])
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-0.5, 1))
    f.label(B, "B", direction=(0.5, 1))
    f.label(C, "C", direction=(0.5, -1))
    f.label(D, "D", direction=(-0.5, -1))
    L = "answer"
    mark_parallel(f, [(D, A), (C, B)], n=1, layer=L, size=0.15)
    mark_parallel(f, [(A, B), (D, C)], n=2, layer=L, size=0.15)
    f.seg(B, D, layer=L)
    mark_congruent(f, [((B, A, D), (D, C, B)), ((D, A, B), (B, C, D))], layer=L, r=[0.42, 0.62])
    return f


@figure(f"{S}_mnkl")
def mnkl() -> Figure:
    """CYU: parallelogram MNKL with MN parallel to KL and NK parallel to ML (given marks only)."""
    M, N, K, L = P((0, 0), (0.6, 1.1), (2.6, 1.1), (2.0, 0))
    assert is_parallel(M, N, L, K) and is_parallel(N, K, M, L)
    f = Figure(width_in=1.9, height_in=0.95)
    f.poly([M, N, K, L])
    f.dots([M, N, K, L])
    f.label(M, "M", direction=(-0.5, -1))
    f.label(N, "N", direction=(-0.5, 1))
    f.label(K, "K", direction=(0.5, 1))
    f.label(L, "L", direction=(0.5, -1))
    mark_parallel(f, [(M, N), (L, K)], n=1, size=0.13)
    mark_parallel(f, [(N, K), (M, L)], n=2, size=0.13)
    return f


# ---------------------------------------------------------------- practice
@figure(f"{S}_pr_kite")
def pr_kite() -> Figure:
    """Practice 2: EG bisects angle HEF and angle FGH."""
    E, H, F, G = P((0, 1.45), (-0.45, 0.85), (0.45, 0.85), (0, 0))
    assert np.isclose(angle_deg(E, H, G), angle_deg(E, F, G)) and np.isclose(angle_deg(G, H, E), angle_deg(G, F, E))
    f = Figure(width_in=1.1, height_in=1.6)
    f.poly([E, F, G, H])
    f.seg(E, G)
    f.dots([E, F, G, H])
    f.label(E, "E", direction=(0, 1))
    f.label(H, "H", direction=(-1, 0))
    f.label(F, "F", direction=(1, 0))
    f.label(G, "G", direction=(0, -1))
    return f


@figure(f"{S}_pr_rect")
def pr_rect() -> Figure:
    """Practice 3 (Han's proof): DC parallel to AB, right angles at A and C, diagonal DB."""
    A, B, C, D = P((0, 0), (1.5, 0), (1.5, 1.1), (0, 1.1))
    assert is_parallel(D, C, A, B)
    f = Figure(width_in=1.6, height_in=1.25)
    f.poly([A, B, C, D])
    f.seg(D, B)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, -1))
    f.label(B, "B", direction=(1, -1))
    f.label(C, "C", direction=(1, 1))
    f.label(D, "D", direction=(-1, 1))
    f.right_angle(A, B, D, size=0.14)
    f.right_angle(C, D, B, size=0.14)
    mark_parallel(f, [(D, C), (A, B)], n=1, size=0.13)
    return f


_ZA, _ZC = P((0, 0), (2.0, 2.1))
_ZO = midpoint(_ZA, _ZC)
_ZF = _ZA + 0.4 * (_ZC - _ZA)
_ZB = np.array((-0.1, 0.9))
_ZD, _ZE = rotate([_ZB, _ZF], 180, about=_ZO)
assert is_rigid_image(P(_ZA, _ZB, _ZF), P(_ZC, _ZD, _ZE))
assert is_parallel(_ZA, _ZB, _ZC, _ZD) and collinear(_ZA, _ZF, _ZE, _ZC)


@figure(f"{S}_pr_zigzag")
def pr_zigzag() -> Figure:
    """Practice 5: AB parallel to CD, angle B = angle D, AB = CD; triangles ABF and CDE on line AC."""
    A, B, C, D, E, F = _ZA, _ZB, _ZC, _ZD, _ZE, _ZF
    f = Figure(width_in=1.55, height_in=1.55)
    f.poly([A, B, F])
    f.poly([C, D, E])
    f.seg(F, E)
    f.dots([A, B, C, D, E, F])
    f.label(A, "A", direction=(0, -1))
    f.label(B, "B", direction=(-1, 0.3))
    f.label(C, "C", direction=(0, 1))
    f.label(D, "D", direction=(1, -0.3))
    f.label(E, "E", direction=(-0.6, 1))
    f.label(F, "F", direction=(0.6, -1))
    f.ticks(A, B, 2, size=0.12)
    f.ticks(C, D, 2, size=0.12)
    mark_congruent(f, [((B, A, F), (D, C, E))], r=0.22)
    return f


_KQ, _KB, _KA = P((0, 0), (-0.42, -0.96), (0.30, -0.68))
_KK = reflect([_KA], _KQ, _KB)[0]
assert np.isclose(dist(_KQ, _KK), dist(_KQ, _KA))
assert np.isclose(angle_deg(_KQ, _KK, _KB), angle_deg(_KQ, _KA, _KB))


@figure(f"{S}_pr_kqab")
def pr_kqab() -> Figure:
    """Practice 6: QK = QA and QB bisects angle KQA (no marks, as in the source)."""
    Q, B, A, K = _KQ, _KB, _KA, _KK
    f = Figure(width_in=1.2, height_in=1.2)
    f.poly([K, Q, A, B])
    f.seg(Q, B)
    f.dots([K, Q, A, B])
    f.label(K, "K", direction=(-1, 0.5))
    f.label(Q, "Q", direction=(0, 1))
    f.label(A, "A", direction=(1, 0))
    f.label(B, "B", direction=(0, -1))
    return f

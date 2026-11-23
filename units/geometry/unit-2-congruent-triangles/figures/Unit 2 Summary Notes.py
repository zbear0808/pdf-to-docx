"""Figures for reference "Unit 2 Summary Notes" (assessments/Unit 2 Summary Notes.yaml).
Reference sheet: no key, so every figure is given ink only (black). Shapes follow the teacher's source drawings,
redrawn because the source images are low resolution. Two examples get new letters and shapes so they don't
match test items (see _temp/specs/Unit 2 Summary Notes/changes.md).
Nov 20: one parallelogram figure (_para, sides and angles) replaces _para_sides and _para_angles; the 39 degree
label in _25b sits next to R.
Loop: uv run lesson-builder figs units/geometry/unit-2-congruent-triangles -l "Unit 2 Summary Notes"
"""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, collinear, dist, figure, is_parallel, is_rigid_image,
                                    mark_congruent, mark_parallel, midpoint, needs_reflection, reflect, rotate,
                                    translate, triangle_from_angles)

S = 'Unit 2 Summary Notes'


def _tri(f: Figure, pts, names=None, dots=True):
    f.poly(pts)
    if dots:
        f.dots(pts)
    if names:
        f.label_poly(pts, names)


# ---------------------------------------------------------------- 2.1 Example 1: LOVE onto MATH
_LOVE = P((3, 0), (2.2, 2.2), (0, 1.3), (1, 0))
_MATH = translate(rotate(_LOVE, -90, about=_LOVE[0]), np.array((4.2, 0)) - _LOVE[0])
assert is_rigid_image(_LOVE, _MATH) and not needs_reflection(_LOVE, _MATH)
assert np.allclose(_MATH[0], (4.2, 0))


@figure(f"{S}_ex1")
def ex1() -> Figure:
    """LOVE and its image MATH (90 deg clockwise around L, then translate L to M)."""
    f = Figure(width_in=2.9, height_in=1.6)
    _tri(f, _LOVE, "LOVE")
    _tri(f, _MATH, "MATH")
    return f


# ---------------------------------------------------------------- 2.1 Example 2: PQR = DEF (reflection)
_PQR = P((0, 0), (2.2, 1.9), (2.0, 0))
_DEF = reflect(_PQR, (2.9, 0), (2.9, 1))
assert is_rigid_image(_PQR, _DEF) and needs_reflection(_PQR, _DEF)


@figure(f"{S}_ex2")
def ex2() -> Figure:
    """PQR and DEF with matching ticks and arcs (P-D, Q-E, R-F)."""
    p, q, r = _PQR
    d, e, fv = _DEF
    f = Figure(width_in=2.8, height_in=1.35)
    _tri(f, _PQR, "PQR")
    _tri(f, _DEF, "DEF")
    mark_congruent(f, [((p, q), (d, e)), ((q, r), (e, fv)), ((p, r), (d, fv)),
                       ((p, q, r), (d, e, fv)), ((q, p, r), (e, d, fv)), ((r, p, q), (fv, d, e))],
                   size=0.12, r=[0.42, 0.3, 0.26])
    return f


# ---------------------------------------------------------------- 2.3 example: UVW onto XYZ (needs a reflection)
_UVW = P((0, 0), (2.4, 0.5), (0.7, 1.9))
_XYZ = translate(rotate(reflect(_UVW, (0, 0), (1, 0)), 20, about=(0, 0)), (3.3, 0.5))
assert is_rigid_image(_UVW, _XYZ) and needs_reflection(_UVW, _XYZ)


@figure(f"{S}_seq")
def seq() -> Figure:
    """UVW and XYZ, all six pairs marked. The triangles face opposite ways."""
    u, v, w = _UVW
    x, y, z = _XYZ
    f = Figure(width_in=2.9, height_in=1.75)
    _tri(f, _UVW, "UVW")
    _tri(f, _XYZ, "XYZ")
    mark_congruent(f, [((u, v), (x, y)), ((v, w), (y, z)), ((u, w), (x, z)),
                       ((u, v, w), (x, y, z)), ((v, u, w), (y, x, z)), ((w, u, v), (z, x, y))],
                   size=0.12, r=[0.34, 0.3, 0.26])
    return f


# ---------------------------------------------------------------- 2.3 theorem pictures (no letters)
_T0 = P((0, 0), (1.5, 0), (0.35, 1.05))
_T1 = translate(rotate(_T0, 115, about=_T0[0]), (3.3, 0.15))
assert is_rigid_image(_T0, _T1) and not needs_reflection(_T0, _T1)


def _pair(groups) -> Figure:
    f = Figure(width_in=2.3, height_in=1.35)
    _tri(f, _T0, dots=False)
    _tri(f, _T1, dots=False)
    mark_congruent(f, groups, size=0.11, r=[0.26, 0.2])
    return f


def _parts(t):
    a, b, c = t
    return {"AB": (a, b), "AC": (a, c), "BC": (b, c), "A": (a, b, c), "B": (b, a, c), "C": (c, a, b)}


_K0, _K1 = _parts(_T0), _parts(_T1)


def _groups(*keys):
    return [(_K0[k], _K1[k]) for k in keys]


@figure(f"{S}_sas")
def sas() -> Figure:
    """Two sides and the angle between them."""
    return _pair(_groups("AB", "AC", "A"))


@figure(f"{S}_asa")
def asa() -> Figure:
    """Two angles and the side between them."""
    return _pair(_groups("AB", "A", "B"))


@figure(f"{S}_sss")
def sss() -> Figure:
    """Three sides."""
    return _pair(_groups("AB", "AC", "BC"))


@figure(f"{S}_saa")
def saa() -> Figure:
    """Two angles and a side that is not between them (BC is across from angle A)."""
    return _pair(_groups("BC", "A", "B"))


# ---------------------------------------------------------------- 2.5 Example 1: MNOP (SSS with shared side PN)
_M, _N, _O, _P = P((0, 0), (2, 0), (4, 0), (2, 1.8))
assert np.isclose(dist(_M, _P), dist(_O, _P)) and collinear(_M, _N, _O)


@figure(f"{S}_25a")
def ex25a() -> Figure:
    f = Figure(width_in=2.3, height_in=1.2)
    f.poly([_M, _O, _P])
    f.seg(_P, _N)
    f.dots([_M, _N, _O, _P])
    f.label(_M, "M", direction=(-1, -0.3))
    f.label(_N, "N", direction=(0, -1))
    f.label(_O, "O", direction=(1, -0.3))
    f.label(_P, "P", direction=(0, 1))
    mark_congruent(f, [((_M, _P), (_O, _P)), ((_M, _N), (_N, _O))], size=0.13)
    return f


# ---------------------------------------------------------------- 2.5 Example 2: angles match, sides don't
_PR = triangle_from_angles((0, 0), (0.75, 1.25), 112, 39, above=False)   # [P, R, Q]
_pP, _pR, _pQ = _PR
_kj = dist(_pP, _pQ)                                                     # KJ is marked congruent to PQ
_kJ = np.array((1.7, -0.9))
_kK = _kJ + _kj * np.array((np.cos(np.radians(62)), np.sin(np.radians(62))))
_JKL = triangle_from_angles(_kJ, _kK, 39, 112, above=False)              # [J, K, L]
_, _, _kL = _JKL
assert np.isclose(angle_deg(_pP, _pR, _pQ), 112) and np.isclose(angle_deg(_pR, _pP, _pQ), 39)
assert np.isclose(angle_deg(_kK, _kJ, _kL), 112) and np.isclose(angle_deg(_kJ, _kK, _kL), 39)
assert not np.isclose(dist(_kK, _kL), _kj)   # PQ matches KL by the angles, not the marked KJ


def _inside(v, a, b, t, d):
    """Point d from vertex v inside angle avb, turned fraction t from ray va toward ray vb."""
    ua, ub = (a - v) / dist(a, v), (b - v) / dist(b, v)
    u = (1 - t) * ua + t * ub
    return v + d * u / np.linalg.norm(u)


@figure(f"{S}_25b")
def ex25b() -> Figure:
    f = Figure(width_in=3.4, height_in=2.1)
    _tri(f, [_pP, _pR, _pQ])
    _tri(f, [_kK, _kJ, _kL])
    f.label(_pP, "P", direction=(-1, 0))
    f.label(_pR, "R", direction=(0, 1))
    f.label(_pQ, "Q", direction=(0, -1))
    f.label(_kK, "K", direction=(0, 1))
    f.label(_kJ, "J", direction=(-1, -0.4))
    f.label(_kL, "L", direction=(1, 0))
    f.arc(_pP, _pR, _pQ, r=0.2)
    f.arc(_pR, _pP, _pQ, r=0.32)
    f.arc(_kK, _kJ, _kL, r=0.2)
    f.arc(_kJ, _kK, _kL, r=0.32)
    f.angle_label(_pP, _pR, _pQ, r'$112^\circ$', dist=0.5, size=9, fixed=True)
    # Nov 20: R's wedge is too narrow for the label, so 39 sits just outside R, beside its arc (not near P)
    f.text(_pR + 0.45 * np.array([np.cos(np.radians(-40)), np.sin(np.radians(-40))]), r'$39^\circ$', size=9,
           fixed=True)
    f.angle_label(_kK, _kJ, _kL, r'$112^\circ$', dist=0.5, size=9, fixed=True)
    f.text(_inside(_kJ, _kL, _kK, 0.3, 1.05), r'$39^\circ$', size=9, fixed=True)
    f.ticks(_pP, _pQ, 1, size=0.11)
    f.ticks(_kK, _kJ, 1, size=0.11)
    return f


# ---------------------------------------------------------------- 2.5 Example 3: bowtie TUXWV
_T, _U, _W, _V = P((0, 2), (1.8, 2), (0.6, 0), (2.4, 0))
_X = midpoint(_T, _V)
assert is_parallel(_T, _U, _W, _V) and collinear(_U, _X, _W)


@figure(f"{S}_25c")
def ex25c() -> Figure:
    f = Figure(width_in=1.6, height_in=1.5)
    f.seg(_T, _U)
    f.seg(_W, _V)
    f.seg(_T, _V)
    f.seg(_U, _W)
    f.dots([_T, _U, _W, _V, _X])
    f.label(_T, "T", direction=(-1, 0.3))
    f.label(_U, "U", direction=(1, 0.3))
    f.label(_W, "W", direction=(-1, -0.3))
    f.label(_V, "V", direction=(1, -0.3))
    f.label(_X, "X", direction=(-1, 0))
    mark_parallel(f, [(_T, _U), (_W, _V)], n=2)
    mark_congruent(f, [((_T, _X), (_X, _V))], size=0.12)
    return f


# ---------------------------------------------------------------- 2.6 SAS example: ABC and GBC
_A6, _B6, _C6, _G6 = P((0, 2), (1.1, 1), (3.4, 1), (0, 0))
assert np.isclose(dist(_A6, _B6), dist(_G6, _B6))
assert np.isclose(angle_deg(_B6, _A6, _C6), angle_deg(_B6, _G6, _C6))


@figure(f"{S}_sas_ex")
def sas_ex() -> Figure:
    f = Figure(width_in=2.2, height_in=1.45)
    f.poly([_A6, _B6, _G6, _C6])
    f.seg(_B6, _C6)
    f.dots([_A6, _B6, _C6, _G6])
    f.label(_A6, "A", direction=(-1, 0.4))
    f.label(_B6, "B", direction=(-1, 0))
    f.label(_C6, "C", direction=(1, 0))
    f.label(_G6, "G", direction=(-1, -0.4))
    mark_congruent(f, [((_A6, _B6), (_G6, _B6))], size=0.13)
    f.arc(_B6, _A6, _C6, r=0.24, ticks=1)
    f.arc(_B6, _G6, _C6, r=0.24, ticks=1)
    return f


# ---------------------------------------------------------------- 2.6 Isosceles Triangle Theorem: ABP
_iA, _iB, _iP = P((0, 0), (1.2, 0), (0.6, 2))
assert np.isclose(dist(_iA, _iP), dist(_iB, _iP))


@figure(f"{S}_iso")
def iso() -> Figure:
    f = Figure(width_in=1.0, height_in=1.45)
    _tri(f, [_iA, _iB, _iP], "ABP")
    mark_congruent(f, [((_iA, _iP), (_iB, _iP)), ((_iA, _iB, _iP), (_iB, _iA, _iP))], size=0.12, r=0.22)
    return f


# ---------------------------------------------------------------- 2.7 ASA example: bowtie LEP and SET
_aP, _aE = P((0, 0), (1.6, 1.2))
_aT = 2 * _aE - _aP
_aL = np.array((0.0, 2.1))
_aS = 2 * _aE - _aL
assert collinear(_aL, _aE, _aS) and collinear(_aP, _aE, _aT)
assert np.isclose(angle_deg(_aP, _aL, _aE), angle_deg(_aT, _aS, _aE))


@figure(f"{S}_asa_ex")
def asa_ex() -> Figure:
    f = Figure(width_in=2.0, height_in=1.55)
    f.seg(_aL, _aP)
    f.seg(_aP, _aT)
    f.seg(_aL, _aS)
    f.seg(_aT, _aS)
    f.dots([_aL, _aP, _aE, _aT, _aS])
    f.label(_aL, "L", direction=(-1, 0.3))
    f.label(_aP, "P", direction=(-1, -0.3))
    f.label(_aE, "E", direction=(0, -1))
    f.label(_aT, "T", direction=(1, 0.3))
    f.label(_aS, "S", direction=(1, -0.3))
    mark_congruent(f, [((_aP, _aE), (_aE, _aT)), ((_aP, _aL, _aE), (_aT, _aS, _aE)),
                       ((_aE, _aL, _aP), (_aE, _aS, _aT))], size=0.13, r=[0.3, 0.24])
    return f


# ---------------------------------------------------------------- 2.7 parallelogram MNKL (sides and angles)
# Nov 20: one figure for the one Parallelogram Theorem (2.7 QuickNotes); it replaces para_sides and para_angles.
_pM, _pN, _pK, _pL = P((0, 0), (0.7, 1.3), (3.0, 1.3), (2.3, 0))
assert is_parallel(_pM, _pN, _pK, _pL) and is_parallel(_pN, _pK, _pM, _pL)
assert np.isclose(angle_deg(_pM, _pN, _pL), angle_deg(_pK, _pN, _pL))
assert np.isclose(angle_deg(_pN, _pM, _pK), angle_deg(_pL, _pM, _pK))


@figure(f"{S}_para")
def para() -> Figure:
    f = Figure(width_in=2.3, height_in=1.25)
    _tri(f, [_pM, _pN, _pK, _pL], "MNKL")
    mark_congruent(f, [((_pM, _pN), (_pL, _pK)), ((_pN, _pK), (_pM, _pL)),
                       ((_pM, _pN, _pL), (_pK, _pN, _pL)), ((_pN, _pM, _pK), (_pL, _pM, _pK))],
                   size=0.12, r=[0.24, 0.2])
    return f


# ---------------------------------------------------------------- 2.9 SSS example: kite GUHJ
_sG, _sH, _sU = P((0, 0), (2.8, 0.9), (1.4, 1.7))
_sJ = reflect(_sU, _sG, _sH)[0]
assert np.isclose(dist(_sG, _sU), dist(_sG, _sJ)) and np.isclose(dist(_sH, _sU), dist(_sH, _sJ))


@figure(f"{S}_sss_ex")
def sss_ex() -> Figure:
    f = Figure(width_in=2.0, height_in=1.4)
    f.poly([_sG, _sU, _sH, _sJ])
    f.seg(_sG, _sH)
    f.dots([_sG, _sU, _sH, _sJ])
    f.label(_sG, "G", direction=(-1, 0))
    f.label(_sU, "U", direction=(0, 1))
    f.label(_sH, "H", direction=(1, 0))
    f.label(_sJ, "J", direction=(0, -1))
    mark_congruent(f, [((_sG, _sU), (_sG, _sJ)), ((_sH, _sU), (_sH, _sJ))], size=0.13)
    return f

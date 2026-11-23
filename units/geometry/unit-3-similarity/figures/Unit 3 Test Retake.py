"""Unit 3 Test, Retake. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_lengths, dilate, dist, figure, needs_reflection, rotate, similarity_ratio, translate,
)


def _cross(u, v):
    return u[0] * v[1] - u[1] * v[0]


def _dir(deg):
    return np.array([np.cos(np.radians(deg)), np.sin(np.radians(deg))])


# 1: triangle XYZ and its image X'Y'Z' (rotate 150 deg, scale factor 2)
_XYZ = P((0, 0), (1.6, 0.8), (1.2, 1.9))
_IMG1 = translate(rotate(dilate(_XYZ, 2.0, _XYZ[0]), 150, _XYZ[0]), (1.4, -1.6))


@figure("Unit 3 Test Retake_ratios")
def ratios() -> Figure:
    assert np.isclose(similarity_ratio(_XYZ, _IMG1), 2.0) and not needs_reflection(_XYZ, _IMG1)
    f = Figure(width_in=2.2, height_in=2.0)
    f.poly(_XYZ)
    f.dots(_XYZ)
    f.label_poly(_XYZ, ["X", "Y", "Z"])
    f.poly(_IMG1)
    f.dots(_IMG1)
    f.label_poly(_IMG1, ["X'", "Y'", "Z'"], overrides={"Z'": (-1, 0)}, offset_pt=14)
    return f


# 2: D on CA, E on CB. CD = 4, DA = 12, CE = 6, CB = 24 (whole side)
_C2 = P((0, 0))[0]
_A2 = 16 * np.array([-0.6, -0.8])
_B2 = np.array([np.sqrt(24 ** 2 - 12.8 ** 2), -12.8])
_D2 = _C2 + 4 / 16 * (_A2 - _C2)
_E2 = _C2 + 6 / 24 * (_B2 - _C2)


@figure("Unit 3 Test Retake_parallel")
def parallel() -> Figure:
    assert np.isclose(dist(_C2, _B2), 24) and np.isclose(dist(_C2, _A2), 16)
    assert np.allclose(dilate([_D2, _E2], 4, _C2), [_A2, _B2])     # CAB is a dilation of CDE, k = 4
    assert_lengths([(_C2, _D2, 4), (_D2, _A2, 12), (_C2, _E2, 6), (_C2, _B2, 24)])
    f = Figure(width_in=2.6, height_in=1.5)
    tri = np.array([_C2, _A2, _B2])
    f.poly(tri)
    f.seg(_D2, _E2)
    f.dots([_C2, _A2, _B2, _D2, _E2])
    c = tri.mean(0)
    for pt, nm, d in ((_C2, "C", (0, 1)), (_A2, "A", (-1, -0.3)), (_B2, "B", (1, -0.6)), (_D2, "D", (-1, 0.2)),
                      (_E2, "E", (0.2, -1))):
        f.label(pt, nm, direction=d)
    f.side_label(_C2, _D2, "4", c, size=11)
    f.side_label(_D2, _A2, "12", c, size=11)
    f.side_label(_C2, _E2, "6", c, size=11, fixed=True)     # beside CE, not under DE (a "6" under DE reads as DE = 6)
    # dimension line for the whole side CB
    u = (_B2 - _C2) / 24
    n = np.array([u[1], -u[0]])
    if np.dot(n, (_C2 + _B2) / 2 - c) < 0:
        n = -n
    p, q = _C2 + 6.0 * n, _B2 + 6.0 * n
    f.seg(p, q, lw=0.9)
    f.seg(p - 0.6 * n, p + 0.6 * n, lw=0.9)
    f.seg(q - 0.6 * n, q + 0.6 * n, lw=0.9)
    f.side_label(p, q, "24", c, size=11)
    return f


# 3: PQ = 25, PR = 55, FH = 22, FG = 10, angle P = angle F. PQR ~ FGH (k = 0.4), so PQR ~ FHG is false
_P3, _R3 = P((0, 0), (55, 0))
_Q3 = 25 * _dir(65)
_F3 = P((50, -12))[0]
_G3 = _F3 + np.array([0, -10])
_H3 = _F3 + 22 * np.array([-np.sin(np.radians(65)), -np.cos(np.radians(65))])


@figure("Unit 3 Test Retake_sas")
def sas() -> Figure:
    PQR, FGH = np.array([_P3, _Q3, _R3]), np.array([_F3, _G3, _H3])
    assert np.isclose(similarity_ratio(PQR, FGH), 0.4)
    assert similarity_ratio(PQR, np.array([_F3, _H3, _G3])) is None
    assert np.isclose(angle_deg(_P3, _Q3, _R3), angle_deg(_F3, _G3, _H3))
    assert_lengths([(_P3, _Q3, 25), (_P3, _R3, 55), (_F3, _H3, 22), (_F3, _G3, 10)])
    f = Figure(width_in=2.4, height_in=2.0)
    for tri in (PQR, FGH):
        f.poly(tri)
        f.dots(tri)
    f.arc(_P3, _Q3, _R3, n=2, r=3.5, gap=1.0)
    f.arc(_F3, _G3, _H3, n=2, r=3.0, gap=1.0)
    for pt, nm, d in ((_P3, "P", (-1, -0.5)), (_Q3, "Q", (0, 1)), (_R3, "R", (1, 0)),
                      (_F3, "F", (0.5, 1)), (_G3, "G", (0.5, -1)), (_H3, "H", (-1, 0))):
        f.label(pt, nm, direction=d)
    f.side_label(_P3, _Q3, "25", PQR.mean(0), size=11)
    f.side_label(_P3, _R3, "55", PQR.mean(0), size=11)
    f.side_label(_F3, _H3, "22", FGH.mean(0), size=11)
    f.side_label(_F3, _G3, "10", FGH.mean(0), size=11)
    return f


# 4: Heritage Lake. Big right triangle: legs x (across the lake) and 16 + 10 = 26. Small: legs 15 and 10. x = 39
_L4, _T4 = P((0, 0), (0, 39))
_M4, _N4, _R4 = P((16, 0), (16, 15), (26, 0))


@figure("Unit 3 Test Retake_lake")
def lake() -> Figure:
    assert np.isclose(dist(_L4, _T4) / dist(_M4, _N4), dist(_L4, _R4) / dist(_M4, _R4))   # 39/15 = 26/10
    assert np.isclose(_cross(_T4 - _R4, _N4 - _R4), 0)                                    # N is on TR
    assert_lengths([(_L4, _M4, 16), (_M4, _R4, 10), (_M4, _N4, 15), (_L4, _T4, 39)])
    t = np.linspace(0, 2 * np.pi, 120)
    oval = np.c_[4.5 * np.cos(t), 19.5 + 22 * np.sin(t)]
    f = Figure(width_in=2.2, height_in=2.3)
    f.poly(oval, fill="#d9d9d9")
    f.poly([_L4, _T4, _R4])
    f.seg(_M4, _N4)
    f.right_angle(_L4, _T4, _R4, size=2.0)
    f.right_angle(_M4, _N4, _R4, size=2.0)
    f.side_label(_L4, _M4, "16 m", _T4, size=10)
    f.side_label(_M4, _R4, "10 m", _T4, size=10)
    f.side_label(_M4, _N4, "15 m", _R4, size=10, offset_pt=15)
    f.text((-2.5, 24), "$x$", size=12)
    f.text((-17, 33), "Heritage\nLake", size=10)
    f.arrow((-12, 31), (-5.5, 30), layer="given", dashed=False)
    return f


# 5: triangle DAB (AD = 10, D = 88, B = 53) and triangle NUP (N = 88, U = 39, P = 53, PN = 16, NU = 20, PU = 25)
_s6 = 25 / np.sin(np.radians(88))
_P6, _U6 = P((0, 0), (25, 0))
_N6 = _s6 * np.sin(np.radians(39)) * _dir(53)
_NUP = rotate(np.array([_N6, _U6, _P6]), 4, (0, 0))
# D, A, B (N->D, U->A, P->B), scale factor 1/2
_DAB = translate(rotate(dilate(_NUP, 0.5, (0, 0)), -12, (0, 0)), (16, 16))


@figure("Unit 3 Test Retake_similar")
def similar() -> Figure:
    N, U, Pp = _NUP
    D, A, B = _DAB
    assert round(angle_deg(N, U, Pp)) == 88 and round(angle_deg(U, N, Pp)) == 39 and round(angle_deg(Pp, N, U)) == 53
    assert round(dist(Pp, N)) == 16 and round(dist(N, U)) == 20 and round(dist(Pp, U)) == 25
    assert np.isclose(similarity_ratio(_NUP, _DAB), 0.5) and round(dist(A, D)) == 10
    assert_lengths([(Pp, N, 16), (N, U, 20), (Pp, U, 25), (A, D, 10)])
    assert round(angle_deg(D, A, B)) == 88 and round(angle_deg(B, D, A)) == 53
    f = Figure(width_in=2.8, height_in=2.4)
    for tri, names in ((_NUP, "NUP"), (_DAB, "DAB")):
        f.poly(tri)
        f.dots(tri)
        f.label_poly(tri, names)
    f.side_label(Pp, N, "16", _NUP.mean(0), size=11)
    f.side_label(N, U, "20", _NUP.mean(0), size=11)
    f.side_label(Pp, U, "25", _NUP.mean(0), size=11)
    f.side_label(A, D, "10", _DAB.mean(0), size=11)
    f.arc(N, U, Pp, r=1.5)
    f.angle_label(N, U, Pp, r"$88^\circ$", dist=3.2, size=10)
    f.arc(U, N, Pp, r=2.6)
    f.angle_label(U, N, Pp, r"$39^\circ$", dist=5.0, size=10)
    f.arc(Pp, N, U, r=2.2)     # third angle printed (Nov 19): the triangle sum is routine for part a
    f.angle_label(Pp, N, U, r"$53^\circ$", dist=4.4, size=10)
    f.arc(D, A, B, r=1.0)
    f.angle_label(D, A, B, r"$88^\circ$", dist=2.4, size=10)
    f.arc(B, D, A, r=1.2)
    f.angle_label(B, D, A, r"$53^\circ$", dist=3.6, size=10)
    return f


# 6: dilate triangle WIN, center Z on side WI, scale factor 2
_W7, _I7, _N7 = P((0, 2.2), (2.6, 2.6), (1.3, 0))
_Z7 = _W7 + 0.3 * (_I7 - _W7)


@figure("Unit 3 Test Retake_dilate")
def dilate_win() -> Figure:
    src = np.array([_W7, _I7, _N7])
    img = dilate(src, 2, _Z7)
    assert np.isclose(dist(_Z7, img[2]), 2 * dist(_Z7, _N7))
    f = Figure(width_in=2.4, height_in=2.6)
    f.poly(src)
    f.dots([_W7, _I7, _N7, _Z7])
    f.label(_W7, "W", direction=(-1, 0.5))
    f.label(_I7, "I", direction=(1, 0.5))
    f.label(_N7, "N", direction=(1, -0.3))
    f.label(_Z7, "Z", direction=(0, 1))
    f.seg(_Z7, img[2], layer="answer", dashed=True)
    f.poly(img, layer="answer")
    f.dots(img, layer="answer")
    f.label(img[0], "W'", direction=(-1, 0.5), layer="answer")
    f.label(img[1], "I'", direction=(1, 0.5), layer="answer")
    f.label(img[2], "N'", direction=(0, -1), layer="answer")
    return f


# 8: rectangle ABDE, C on BD, F on AE, CF perpendicular to AE, angle ACE = 90, angle AEC = 60. CE = 10, FE = 5, AF = 15
_h = 5 * np.sqrt(3)
_A10, _F10, _E10 = P((0, _h), (15, _h), (20, _h))
_B10, _C10, _D10 = P((0, 0), (15, 0), (20, 0))


@figure("Unit 3 Test Retake_rect")
def rect() -> Figure:
    assert np.isclose(angle_deg(_C10, _A10, _E10), 90) and np.isclose(angle_deg(_E10, _A10, _C10), 60)
    assert np.isclose(dist(_C10, _E10), 10) and np.isclose(dist(_B10, _C10), 15) and np.isclose(dist(_A10, _F10), 15)
    assert_lengths([(_C10, _E10, 10), (_F10, _E10, 5)])
    f = Figure(width_in=3.0, height_in=1.7)
    f.poly([_A10, _B10, _D10, _E10])
    f.seg(_A10, _C10)
    f.seg(_C10, _E10)
    f.seg(_C10, _F10)
    f.dots([_A10, _B10, _C10, _D10, _E10, _F10])
    f.right_angle(_C10, _A10, _E10, size=0.9)
    f.right_angle(_F10, _C10, _E10, size=0.9)
    f.arc(_E10, _A10, _C10, r=1.6)
    f.angle_label(_E10, _A10, _C10, r"$60^\circ$", dist=3.4, size=10)
    for pt, nm, d in ((_A10, "A", (-1, 1)), (_B10, "B", (-1, -1)), (_C10, "C", (0, -1)), (_D10, "D", (1, -1)),
                      (_E10, "E", (1, 1)), (_F10, "F", (0, 1))):
        f.label(pt, nm, direction=d)
    f.side_label(_C10, _E10, "10", _A10, size=11)
    f.side_label(_F10, _E10, "5", _C10, size=11)
    return f

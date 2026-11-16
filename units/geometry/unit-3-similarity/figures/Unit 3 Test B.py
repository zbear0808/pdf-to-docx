"""Unit 3 Test, Version B (mirrors A with new letters, numbers, and orientation). Answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_lengths, dilate, dist, figure, needs_reflection, reflect, rotate, similarity_ratio,
    translate,
)


# 1: triangle JKL and its image J'K'L' (rotate -110 deg, scale factor 1/2)
_JKL = P((0, 0), (3.4, 0.6), (1.2, 2.6))
_IMG1 = translate(rotate(dilate(_JKL, 0.5, _JKL[0]), -110, _JKL[0]), (8.0, 2.4))


@figure("Unit 3 Test B_ratios")
def ratios() -> Figure:
    assert np.isclose(similarity_ratio(_JKL, _IMG1), 0.5) and not needs_reflection(_JKL, _IMG1)
    f = Figure(width_in=2.4, height_in=1.8)
    f.poly(_JKL)
    f.dots(_JKL)
    f.label_poly(_JKL, ["J", "K", "L"])
    f.poly(_IMG1)
    f.dots(_IMG1)
    f.label_poly(_IMG1, ["J'", "K'", "L'"], overrides={"K'": (-1, 0)}, offset_pt=14)
    return f


# 2: side splitter. J on FG, K on FH, JK || GH. FJ = 6, JG = 7, GH = 20, JK = x = 120/13
_G2, _H2 = P((0, 0), (20, 0))
_F2 = 13 * np.array([np.cos(np.radians(60)), np.sin(np.radians(60))])
_J2 = _F2 + 6 / 13 * (_G2 - _F2)
_K2 = _F2 + 6 / 13 * (_H2 - _F2)


@figure("Unit 3 Test B_splitter")
def splitter() -> Figure:
    assert np.isclose(dist(_F2, _G2), 13) and np.isclose(dist(_J2, _K2), 120 / 13)
    assert_lengths([(_F2, _J2, 6), (_J2, _G2, 7), (_G2, _H2, 20), (_J2, _K2, 120 / 13)])
    f = Figure(width_in=2.4, height_in=1.6)
    tri = np.array([_F2, _G2, _H2])
    f.poly(tri)
    f.seg(_J2, _K2)
    f.dots([_F2, _G2, _H2, _J2, _K2])
    f.parallel_marks(_J2, _K2, size=0.8)
    f.parallel_marks(_G2, _H2, size=0.8)
    f.label(_F2, "F", direction=(0, 1))
    f.label(_G2, "G", direction=(-1, -0.4))
    f.label(_H2, "H", direction=(1, -0.4))
    f.label(_J2, "J", direction=(-1, 0.3))
    f.label(_K2, "K", direction=(1, 0.3))
    c = tri.mean(0)
    f.side_label(_F2, _J2, "6", c, size=11)
    f.side_label(_J2, _G2, "7", c, size=11)
    f.side_label(_G2, _H2, "20", c, size=11)
    f.side_label(_J2, _K2, "x", _F2, size=12, italic=True)
    return f


# 3: triangle GHJ (G = 48, H = 70, GH = 19, HJ = 16, GJ = 20) and triangle XYZ (Y = 62, Z = 48, YZ = 5)
_s = 20 / np.sin(np.radians(70))
_G3 = P((0, 0))[0]
_J3 = P((20, 0))[0]
_H3 = _s * np.sin(np.radians(62)) * np.array([np.cos(np.radians(48)), np.sin(np.radians(48))])
_BIG = rotate(np.array([_G3, _H3, _J3]), 8, (0, 0))                      # G, H, J
# Z, X, Y (G->Z, H->X, J->Y). True scale factor 1/4; drawn at 0.5 so the angle labels fit (prompt says not to scale)
_SMALL = translate(reflect(dilate(_BIG, 0.5, (0, 0)), (0, 0), (1, 0)), (-15, 13))


@figure("Unit 3 Test B_similar")
def similar() -> Figure:
    G, H, J = _BIG
    Z, X, Y = _SMALL
    assert round(angle_deg(G, H, J)) == 48 and round(angle_deg(H, G, J)) == 70 and round(angle_deg(J, G, H)) == 62
    assert round(dist(G, H)) == 19 and round(dist(H, J)) == 16 and round(dist(G, J)) == 20
    assert similarity_ratio(_BIG, _SMALL) is not None
    assert_lengths([(G, H, 19), (H, J, 16), (G, J, 20)])
    assert round(angle_deg(Y, X, Z)) == 62 and round(angle_deg(Z, X, Y)) == 48 and round(angle_deg(X, Y, Z)) == 70
    f = Figure(width_in=3.6, height_in=2.1)
    for tri, names in ((_BIG, "GHJ"), (_SMALL, "ZXY")):
        f.poly(tri)
        f.dots(tri)
        f.label_poly(tri, names)
    f.side_label(G, H, "19", _BIG.mean(0), size=11)
    f.side_label(H, J, "16", _BIG.mean(0), size=11)
    f.side_label(G, J, "20", _BIG.mean(0), size=11)
    f.side_label(Y, Z, "5", _SMALL.mean(0), size=11)
    f.arc(G, H, J, r=2.2)
    f.angle_label(G, H, J, r"$48^\circ$", dist=4.2, size=10)
    f.arc(H, G, J, r=1.6)
    f.angle_label(H, G, J, r"$70^\circ$", dist=3.4, size=10)
    f.arc(Y, X, Z, r=1.2)
    f.angle_label(Y, X, Z, r"$62^\circ$", dist=2.8, size=10)
    f.arc(Z, X, Y, r=1.4)
    f.angle_label(Z, X, Y, r"$48^\circ$", dist=3.2, size=10)
    return f


# 4: dilate triangle JKL, center Q on side JK, scale factor 3
_J4, _K4, _L4, _Q4 = P((0, 0), (2.0, 0), (0.5, 1.4), (1.2, 0))


@figure("Unit 3 Test B_dilate")
def dilate_jkl() -> Figure:
    src = np.array([_J4, _K4, _L4])
    img = dilate(src, 3, _Q4)
    assert np.allclose(img, [(-2.4, 0), (3.6, 0), (-0.9, 4.2)])
    f = Figure(width_in=2.6, height_in=2.3)
    f.poly(src)
    f.dots([_J4, _K4, _L4, _Q4])
    f.label(_J4, "J", direction=(0, -1))
    f.label(_K4, "K", direction=(0, -1))
    f.label(_L4, "L", direction=(-1, 0.4))
    f.label(_Q4, "Q", direction=(0, -1))
    f.seg(_Q4, img[2], layer="answer", dashed=True)
    f.poly(img, layer="answer")
    f.dots(img, layer="answer")
    f.label(img[0], "J'", direction=(-1, -0.5), layer="answer")
    f.label(img[1], "K'", direction=(1, -0.5), layer="answer")
    f.label(img[2], "L'", direction=(0, 1), layer="answer")
    return f


# 5: rectangle GHJK, M on GH, N on KJ, MN perpendicular to KJ, angle KMJ = 90. MN = 9, MK = 15, so KN = 12
_K5, _N5, _J5 = P((0, 0), (12, 0), (18.75, 0))
_G5, _M5, _H5 = P((0, 9), (12, 9), (18.75, 9))


@figure("Unit 3 Test B_rect")
def rect() -> Figure:
    assert np.isclose(dist(_M5, _K5), 15) and np.isclose(dist(_K5, _N5), 12)
    assert np.isclose(angle_deg(_M5, _K5, _J5), 90)
    assert_lengths([(_M5, _N5, 9), (_M5, _K5, 15)])
    f = Figure(width_in=2.8, height_in=1.6)
    f.poly([_G5, _H5, _J5, _K5])
    f.seg(_M5, _K5)
    f.seg(_M5, _J5)
    f.seg(_M5, _N5)
    f.dots([_G5, _H5, _J5, _K5, _M5, _N5])
    f.right_angle(_N5, _M5, _K5, size=0.9)
    f.right_angle(_M5, _K5, _J5, size=0.9)
    for pt, nm, d in ((_G5, "G", (-1, 1)), (_H5, "H", (1, 1)), (_J5, "J", (1, -1)), (_K5, "K", (-1, -1)),
                      (_M5, "M", (0, 1)), (_N5, "N", (0, -1))):
        f.label(pt, nm, direction=d)
    f.side_label(_M5, _N5, "9", _J5, size=11)
    f.side_label(_M5, _K5, "15", _N5, size=11)
    return f


# 6: right triangles PQR (PR = 4) and XYZ (XZ = 10). Dilate center Q by 5/2, reflect across QR, translate Q to Y
_Q6, _P6, _R6 = P((0, 0), (0, 2.4), (3.2, 0))
_Y6 = P((5.6, 6))[0]
_XYZ = translate(reflect(dilate([_P6, _Q6, _R6], 2.5, _Q6), _Q6, _R6), _Y6 - _Q6)   # X, Y, Z


@figure("Unit 3 Test B_seq")
def seq() -> Figure:
    X, Y, Z = _XYZ
    PQR = np.array([_P6, _Q6, _R6])
    assert np.isclose(dist(X, Z), 10) and np.isclose(dist(_P6, _R6), 4) and np.allclose(Y, _Y6)
    assert np.isclose(similarity_ratio(PQR, _XYZ), 2.5) and needs_reflection(PQR, _XYZ)
    assert_lengths([(_P6, _R6, 4), (X, Z, 10)])
    f = Figure(width_in=2.6, height_in=1.9)
    for tri in (PQR, _XYZ):
        f.poly(tri)
        f.dots(tri)
    f.right_angle(_Q6, _P6, _R6, size=0.35)
    f.right_angle(Y, X, Z, size=0.5)
    for pt, nm, d in ((_P6, "P", (0, 1)), (_Q6, "Q", (-1, -0.5)), (_R6, "R", (1, -0.5)),
                      (X, "X", (0, -1)), (Y, "Y", (-1, 0.5)), (Z, "Z", (1, 0.5))):
        f.label(pt, nm, direction=d)
    f.side_label(_P6, _R6, "4", PQR.mean(0), size=11)
    f.side_label(X, Z, "10", _XYZ.mean(0), size=11)
    return f

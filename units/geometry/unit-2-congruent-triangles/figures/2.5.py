"""Figures for lesson "2.5" (lessons/2.5.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Loop: uv run lesson-builder figs <unit> -l "2.5" (0 errors, no label warnings).
Redrawn from the 2.5 Student Notes (source marks were pink, so they are redrawn in black).
"""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, assert_lengths, cross2, dist, figure, fit_rigid,
                                    is_parallel, is_rigid_image, mark_congruent, mark_parallel, midpoint,
                                    rotate)

S = '2.5'


def _meet(p, q, r, s):
    """Intersection of line pq and line rs."""
    p, q, r, s = (np.asarray(x, float) for x in (p, q, r, s))
    d1, d2 = q - p, s - r
    return p + cross2(r - p, d2) / cross2(d1, d2) * d1


@figure(f"{S}_warmup")
def warmup() -> Figure:
    """Source warm-up 1, 2, 6: alternate interior (parallel), vertical, and no parallel marks."""
    f = Figure(width_in=5.6, height_in=1.75)
    # 1: parallel lines, a below the top line on the left, b above the bottom line on the right
    top, bot, tr = P((0, 2.0), (3, 2.0)), P((0, 0.5), (3, 0.5)), P((1.05, 2.6), (1.8, -0.1))
    assert is_parallel(top[0], top[1], bot[0], bot[1])
    for a, b in (top, bot, tr):
        f.seg(a, b)
    mark_parallel(f, [(top[0], top[0] + (0.9, 0)), (bot[0], bot[0] + (0.9, 0))], n=2)
    c1, c2 = _meet(*top, *tr), _meet(*bot, *tr)
    f.angle_label(c1, top[0], tr[1], '$a$', dist=0.38)
    f.angle_label(c2, bot[1], tr[0], '$b$', dist=0.38)
    f.text((0.1, 2.55), '1.', fixed=True)
    # 2: two crossing lines, a above and b below the crossing
    o = np.array((5.5, 1.25))
    u, v = np.array((1.3, 0.75)), np.array((-1.3, 0.75))
    f.seg(o - u, o + u)
    f.seg(o - v, o + v)
    f.angle_label(o, o + u, o + v, '$a$', dist=0.38)
    f.angle_label(o, o - u, o - v, '$b$', dist=0.38)
    f.text((4.1, 2.55), '2.', fixed=True)
    # 3: two lines with no parallel marks; a and b both above-right of the crossing points
    l1, l2, tr = P((8.0, 2.15), (11.0, 1.8)), P((8.0, 0.5), (11.0, 0.55)), P((9.2, 2.6), (9.85, -0.1))
    assert not is_parallel(l1[0], l1[1], l2[0], l2[1])
    for a, b in (l1, l2, tr):
        f.seg(a, b)
    c1, c2 = _meet(*l1, *tr), _meet(*l2, *tr)
    f.angle_label(c1, l1[1], tr[0], '$a$', dist=0.38)
    f.angle_label(c2, l2[1], tr[0], '$b$', dist=0.38)
    f.text((8.1, 2.55), '3.', fixed=True)
    return f


# Act 1 #1: SAS with numbers. LZ = 22, LU = 18, angle L = 65; IA = 22, ID = 18, angle I = 65.
K = 0.13
L_ = np.array((0.0, 0.0))
LZU = np.array([L_, L_ + (22 * K, 0), L_ + 18 * K * np.array((np.cos(np.radians(-65)), np.sin(np.radians(-65))))])
IAD = rotate(LZU, 180, about=(2.6, -0.6)) + (1.9, 0.0)
assert is_rigid_image(LZU, IAD)
assert np.isclose(angle_deg(LZU[0], LZU[1], LZU[2]), 65)


@figure(f"{S}_sas")
def sas() -> Figure:
    f = Figure(width_in=3.3, height_in=1.45)
    L, Z, U = LZU
    I, A, D = IAD
    f.poly(LZU)
    f.poly(IAD)
    f.label_poly(LZU, "LZU")
    f.label_poly(IAD, "IAD")
    f.side_label(L, Z, '22 cm', U, size=10)
    f.side_label(L, U, '18 cm', Z, size=10)
    f.angle_label(L, Z, U, r'$65^\circ$', size=9)
    f.side_label(I, A, '22 cm', D, size=10)
    f.side_label(I, D, '18 cm', A, size=10)
    f.angle_label(I, A, D, r'$65^\circ$', size=9)
    return f


# Act 1 #2: SSS with numbers. SD = 6, SI = 8, DI = 9; NJ = 6, AJ = 8, AN = 9 (S -> J, D -> N, I -> A).
D0, I0 = np.array((0.0, 0.0)), np.array((9.0, 0.0))
_sx = (36 - 64 + 81) / 18
SDI = 0.3 * np.array([(_sx, np.sqrt(36 - _sx ** 2)), D0, I0])
JNA = fit_rigid(SDI, 0.3 * np.array([(18.5, -0.3), (19.6, 5.4), (12.0, 1.5)]))
assert is_rigid_image(SDI, JNA)


@figure(f"{S}_sss")
def sss() -> Figure:
    f = Figure(width_in=3.1, height_in=1.3)
    S_, D, I = SDI
    J, N, A = JNA
    assert_lengths([(S_, D, 6), (S_, I, 8), (D, I, 9), (N, J, 6), (A, J, 8), (A, N, 9)])
    f.poly(SDI)
    f.poly(JNA)
    f.label_poly(SDI, "SDI")
    f.label_poly(JNA, "JNA")
    for a, b, t, c in [(S_, D, '6', I), (S_, I, '8', D), (D, I, '9', S_), (N, J, '6', A), (A, J, '8', N),
                       (A, N, '9', J)]:
        f.side_label(a, b, t, c, size=10)
    return f


# Act 1 #3: ASA from marks. angle A (2 arcs), AY (2 ticks), angle Y (1 arc); A -> M, Y -> W, C -> B.
CAY = np.array([(0.0, 2.9), (0.15, 0.0), (2.7, 0.0)])
CAY[0] = CAY[1] + 2.9 * np.array((np.cos(np.radians(83)), np.sin(np.radians(83))))
BMW = fit_rigid(CAY, np.array([(5.9, -0.3), (5.6, 2.6), (3.0, 2.6)]))
assert is_rigid_image(CAY, BMW)


@figure(f"{S}_asa")
def asa() -> Figure:
    f = Figure(width_in=3.0, height_in=1.65)
    C, A, Y = CAY
    B, M, W = BMW
    f.poly(CAY)
    f.poly(BMW)
    f.label_poly(CAY, "CAY")
    f.label_poly(BMW, "BMW")
    mark_congruent(f, [((Y, C, A), (W, B, M)), ((A, Y, C), (M, W, B))], r=[0.3, 0.3])
    f.ticks(A, Y, n=2)
    f.ticks(M, W, n=2)
    return f


# Act 1 #5: SSA. RE = BU (1 tick), RD = BL (2 ticks), angle D = angle L (1 arc); not congruent.
def _ssa(adj, opp, deg):
    """Vertex V at the origin, VW = adj at (180 - deg) degrees, U on the ray at 180 degrees with WU = opp."""
    a = np.radians(deg)
    root = np.sqrt(opp ** 2 - (adj * np.sin(a)) ** 2)
    W = adj * np.array((-np.cos(a), np.sin(a)))
    return [np.array([(0.0, 0.0), W, (-(adj * np.cos(a) + s * root), 0.0)]) for s in (1, -1)]


DRE, LBU = _ssa(2.6, 2.1, 52)
DRE = DRE + (2.6, 0.0)
LBU = LBU + (5.3, 0.0)
for _t in (DRE, LBU):
    assert np.isclose(angle_deg(_t[0], _t[1], _t[2]), 52) and np.isclose(dist(_t[1], _t[2]), 2.1)
assert not is_rigid_image(DRE, LBU)


@figure(f"{S}_ssa")
def ssa() -> Figure:
    f = Figure(width_in=2.6, height_in=1.35)
    D, R, E = DRE
    L, B, U = LBU
    f.poly(DRE)
    f.poly(LBU)
    f.label_poly(DRE, "DRE")
    f.label_poly(LBU, "LBU")
    mark_congruent(f, [((R, E), (B, U)), ((D, R), (L, B)), ((D, E, R), (L, U, B))], r=0.32)
    return f


# Act 2 #1: kite CEVA with diagonal CV. CE = CA (1 tick), EV = AV (2 ticks). Key: CV is shared (3 ticks).
C_, V_, E_ = np.array((0.0, 0.0)), np.array((4.0, 0.0)), np.array((1.1, 1.0))
A_ = np.array((E_[0], -E_[1]))
assert np.isclose(dist(C_, E_), dist(C_, A_)) and np.isclose(dist(E_, V_), dist(A_, V_))


@figure(f"{S}_kite")
def kite() -> Figure:
    f = Figure(width_in=2.3, height_in=1.35)
    quad = np.array([C_, E_, V_, A_])
    f.poly(quad)
    f.seg(C_, V_)
    f.dots(quad)
    f.label_poly(quad, "CEVA")
    mark_congruent(f, [((C_, E_), (C_, A_)), ((E_, V_), (A_, V_))])
    f.ticks(C_, V_, n=3, layer="answer")
    return f


# Act 2 #2: VY and UX cross at W, the midpoint of both. VW = YW (1 tick), UW = XW (2 ticks).
# Key: the vertical angles VWU and YWX (1 arc each).
W_ = np.array((0.0, 0.0))
V_b, U_b = np.array((-2.2, 0.8)), np.array((-2.5, -0.55))
Y_b, X_b = -V_b, -U_b
assert np.allclose(midpoint(V_b, Y_b), W_) and np.allclose(midpoint(U_b, X_b), W_)


@figure(f"{S}_bowtie")
def bowtie() -> Figure:
    f = Figure(width_in=3.0, height_in=1.3)
    f.seg(V_b, Y_b)
    f.seg(U_b, X_b)
    f.seg(V_b, U_b)
    f.seg(X_b, Y_b)
    f.dots([V_b, U_b, W_, X_b, Y_b])
    for p, n, d in [(V_b, "V", (-1, 1)), (U_b, "U", (-1, -1)), (X_b, "X", (1, 1)), (Y_b, "Y", (1, -1)),
                    (W_, "W", (0, -1))]:
        f.label(p, n, direction=d)
    mark_congruent(f, [((V_b, W_), (W_, Y_b)), ((U_b, W_), (W_, X_b))])
    f.arc(W_, V_b, U_b, n=2, r=0.7, gap=0.1, layer="answer")
    f.arc(W_, Y_b, X_b, n=2, r=0.7, gap=0.1, layer="answer")
    return f


# CYU (Act 1 #4): SSS from marks. TN = EL (3 ticks), AN = LF (2 ticks), TA = EF (1 tick); T -> E, N -> L, A -> F.
TAN = np.array([(0.0, 0.0), (0.85, -1.45), (3.0, 0.0)])
EFL = fit_rigid(TAN, np.array([(4.1, -1.5), (5.75, -1.5), (5.2, 1.3)]))
assert is_rigid_image(TAN, EFL)


@figure(f"{S}_sss_marks")
def sss_marks() -> Figure:
    f = Figure(width_in=2.9, height_in=1.5)
    T, A, N = TAN
    E, F, L = EFL
    f.poly(TAN)
    f.poly(EFL)
    f.label_poly(TAN, "TAN")
    f.label_poly(EFL, "EFL")
    mark_congruent(f, [((T, A), (E, F)), ((A, N), (F, L)), ((T, N), (E, L))])
    return f


# Exit (cool down): triangle ABC = triangle ADC. AD = 2y, AB = 16, DC = x + 4, CB = y, DB = 16.
# x = 4, y = 8 fits every label. (Source brace said 18, which no x and y fit.)
_x, _y = 4, 8
assert 2 * _y == 16 and _x + 4 == _y and (_x + 4) + _y == 16
Dc, Bc, Cc = np.array((0.0, 0.0)), np.array((4.0, 0.0)), np.array((2.0, 0.0))
Ac = np.array((2.0, np.sqrt(16 - 4)))


@figure(f"{S}_cooldown")
def cooldown() -> Figure:
    f = Figure(width_in=2.0, height_in=2.25)
    f.poly([Ac, Dc, Bc])
    f.seg(Ac, Cc)
    f.label(Ac, "A", direction=(0, 1))
    f.label(Dc, "D", direction=(-1, 0))
    f.label(Bc, "B", direction=(1, 0))
    f.label(Cc, "C", direction=(0, 1), offset_pt=8)
    f.side_label(Ac, Dc, '$2y$', Bc)
    f.side_label(Ac, Bc, '16', Dc)
    f.side_label(Dc, Cc, '$x + 4$', Ac)
    f.side_label(Cc, Bc, '$y$', Ac)
    yb = -0.75
    f.seg((0, yb), (4, yb), lw=0.8)
    f.seg((0, yb), (0, yb + 0.15), lw=0.8)
    f.seg((4, yb), (4, yb + 0.15), lw=0.8)
    f.text((2.0, yb - 0.42), '16', fixed=True)
    return f


# Practice 2 (redrawn from the source, letters were about 5 pt): circles centered at A and C, radii AB and CD.
Ac2, Cc2, R2 = np.array((0.0, 0.0)), np.array((4.6, 1.5)), 1.6
Bc2 = Ac2 + R2 * np.array((np.cos(np.radians(45)), np.sin(np.radians(45))))
Dc2 = Cc2 + R2 * np.array((np.cos(np.radians(135)), np.sin(np.radians(135))))
assert np.isclose(dist(Ac2, Bc2), dist(Cc2, Dc2))


@figure(f"{S}_pr_circles")
def pr_circles() -> Figure:
    f = Figure(width_in=2.5, height_in=1.75)
    t = np.linspace(0, 2 * np.pi, 120, endpoint=False)
    for c in (Ac2, Cc2):
        f.poly(np.c_[c[0] + R2 * np.cos(t), c[1] + R2 * np.sin(t)], lw=1.0)
    f.seg(Ac2, Bc2)
    f.seg(Cc2, Dc2)
    f.dots([Ac2, Bc2, Cc2, Dc2])
    f.label(Ac2, "A", direction=(-1, -0.6))
    f.label(Bc2, "B", direction=(1, 0.6))
    f.label(Cc2, "C", direction=(1, -0.6))
    f.label(Dc2, "D", direction=(-1, 0.6))
    mark_congruent(f, [((Ac2, Bc2), (Cc2, Dc2))])
    return f


# Practice 4 (redrawn; the source image was 274 px): triangle HEF is the reflection of HGF across line FH.
Fr, Hr, Er = np.array((0.0, 0.0)), np.array((0.0, -2.45)), np.array((-2.3, -0.38))
Gr = np.array((-Er[0], Er[1]))
assert is_rigid_image([Hr, Fr, Gr], [Hr, Fr, Er])


@figure(f"{S}_pr_reflect")
def pr_reflect() -> Figure:
    f = Figure(width_in=2.4, height_in=1.35)
    f.poly([Er, Fr, Gr, Hr])
    f.seg(Fr, Hr)
    f.dots([Er, Fr, Gr, Hr])
    f.label(Er, "E", direction=(-1, 0))
    f.label(Fr, "F", direction=(0, 1))
    f.label(Gr, "G", direction=(1, 0))
    f.label(Hr, "H", direction=(0, -1))
    return f

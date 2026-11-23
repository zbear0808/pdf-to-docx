"""Figures for assessment "Trig Word Problems Practice" (assessments/Trig Word Problems Practice.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Items 1-6 are key figures (students sketch in an empty box): black = what the problem gives, red = what students add.
Loop: uv run lesson-builder figs <unit> -l "Trig Word Problems Practice" (0 errors, no label warnings).
"""
import math

import numpy as np

from lesson_builder.figures import Figure, angle_deg, dist, figure, midpoint

S = 'Trig Word Problems Practice'
SZ = 10
R = "answer"


def tan(d):
    return math.tan(math.radians(d))


def sin(d):
    return math.sin(math.radians(d))


def pt(x, y):
    return np.array((float(x), float(y)))


def ctr(*pts):
    return np.mean(pts, axis=0)


def inside(f, a, b, text, c):
    """Red side role (opp/adj/hyp) on the inner side of a-b: push away from c mirrored across the side."""
    m = (np.asarray(a) + np.asarray(b)) / 2
    f.side_label(a, b, text, center=2 * m - c, size=SZ - 1, layer=R)


@figure(f"{S}_vocab")
def vocab() -> Figure:
    """Angle of elevation: you stand on the ground and look up at the top of a tree; the angle is at you,
    measured up from the ground. Nov 19: was a cliff picture with elevation and depression (no problem here,
    and no Unit 4 lesson, uses an angle of depression)."""
    h = 3.0
    you, foot, top = pt(0, 0), pt(h / tan(30), 0), pt(h / tan(30), h)
    assert abs(angle_deg(you, foot, top) - 30) < 1e-6 and abs(angle_deg(foot, you, top) - 90) < 1e-6
    f = Figure(width_in=2.6, height_in=1.35)
    f.seg(pt(-0.5, 0), pt(foot[0] + 0.7, 0))
    f.seg(foot, top, lw=2.0)
    f.seg(you, top)
    f.dots([you, top])
    f.arc(you, foot, top, r=0.9)
    f.angle_label(you, foot, top, "elevation", dist=1.3, size=9)
    f.label(you, "you", italic=False, direction=(0, -1), size=9)
    f.label(top, "top", italic=False, direction=(1, 0.3), size=9)
    f.side_label(foot, top, "tree", center=you, size=9)
    f.label(midpoint(you, foot), "ground", italic=False, direction=(0, -1), size=9)
    return f


@figure(f"{S}_1")
def q1() -> Figure:
    """Juan 25 ft from the tree, 51 deg up: h = 25 tan 51."""
    J, B = pt(0, 0), pt(25, 0)
    T = pt(25, 25 * tan(51))
    assert abs(angle_deg(J, B, T) - 51) < 1e-9 and abs(T[1] - 30.87) < 0.01
    c = ctr(J, B, T)
    f = Figure(width_in=2.4, height_in=2.0)
    f.poly([J, B, T])
    f.right_angle(B, J, T, size=2.2)
    f.arc(J, B, T, r=5)
    f.angle_label(J, B, T, "$51^\\circ$", size=SZ)
    f.label(J, "Juan", italic=False, direction=(-1, -0.4), size=SZ)
    f.label(T, "top of tree", italic=False, direction=(0, 1), size=SZ)
    f.side_label(J, B, "25 ft", center=c, size=SZ)
    inside(f, J, B, "adj", c)
    f.side_label(B, T, "$h\\approx30.9$ ft", center=c, size=SZ, layer=R, offset_pt=14)
    inside(f, B, T, "opp", c)
    f.side_label(J, T, "hyp", center=c, size=SZ - 1, layer=R)
    return f


@figure(f"{S}_2")
def q2() -> Figure:
    """Yasmin, 60 ft tree, 31 deg up: d = 60 / tan 31."""
    d = 60 / tan(31)
    Y, B, T = pt(0, 0), pt(d, 0), pt(d, 60)
    assert abs(angle_deg(Y, B, T) - 31) < 1e-9 and abs(d - 99.86) < 0.01
    c = ctr(Y, B, T)
    f = Figure(width_in=2.4, height_in=1.3)
    f.poly([Y, B, T])
    f.right_angle(B, Y, T, size=5)
    f.arc(Y, B, T, r=16)
    f.angle_label(Y, B, T, "$31^\\circ$", size=SZ)
    f.label(Y, "Yasmin", italic=False, direction=(-1, -0.4), size=SZ)
    f.side_label(B, T, "60 ft", center=c, size=SZ)
    inside(f, B, T, "opp", c)
    f.side_label(Y, B, "$d\\approx99.9$ ft", center=c, size=SZ, layer=R)
    inside(f, Y, B, "adj", c)
    inside(f, Y, T, "hyp", c)
    return f


@figure(f"{S}_3")
def q3() -> Figure:
    """Ladder at 60 deg reaching 8.5 ft up: L = 8.5 / sin 60."""
    base = 8.5 / tan(60)
    G, W, T = pt(0, 0), pt(base, 0), pt(base, 8.5)
    L = dist(G, T)
    assert abs(angle_deg(G, W, T) - 60) < 1e-9 and abs(L - 8.5 / sin(60)) < 1e-9 and abs(L - 9.815) < 0.001
    c = ctr(G, W, T)
    f = Figure(width_in=2.2, height_in=2.1)
    f.poly([G, W, T])
    f.seg(W, pt(base, 9.6), lw=2.0)
    f.right_angle(W, G, T, size=0.6)
    f.arc(G, W, T, r=1.3)
    f.angle_label(G, W, T, "$60^\\circ$", dist=2.0, size=SZ)
    f.side_label(W, T, "8.5 ft", center=c, size=SZ)
    inside(f, W, T, "opp", c)
    f.side_label(G, T, "$L\\approx9.8$ ft", center=c, size=SZ, layer=R, offset_pt=14)
    f.side_label(G, T, "hyp", center=c, size=SZ - 1, layer=R, offset_pt=30)
    f.side_label(G, W, "adj", center=c, size=SZ - 1, layer=R)
    f.label(pt(base, 9.6), "wall", italic=False, direction=(1, 0), size=SZ)
    return f


@figure(f"{S}_4")
def q4() -> Figure:
    """12 ft ladder, base 3 ft out: angle with the ground = acos(3/12)."""
    G, W = pt(0, 0), pt(3, 0)
    T = pt(3, math.sqrt(12 ** 2 - 3 ** 2))
    ang = angle_deg(G, W, T)
    assert abs(dist(G, T) - 12) < 1e-9 and abs(ang - math.degrees(math.acos(3 / 12))) < 1e-9
    assert abs(ang - 75.52) < 0.01
    c = ctr(G, W, T)
    f = Figure(width_in=2.0, height_in=2.2)
    f.poly([G, W, T])
    f.seg(W, pt(3, 13), lw=2.0)
    f.right_angle(W, G, T, size=0.6)
    f.side_label(G, W, "3 ft", center=c, size=SZ)
    f.side_label(G, T, "12 ft", center=c, size=SZ)
    f.side_label(G, W, "adj", center=c, size=SZ - 1, layer=R, offset_pt=24)
    f.side_label(G, T, "hyp", center=c, size=SZ - 1, layer=R, offset_pt=30)
    f.side_label(W, T, "opp", center=c, size=SZ - 1, layer=R)
    f.arc(G, W, T, r=1.6, layer=R)
    f.label(G, "$\\theta\\approx75.5^\\circ$", italic=False, direction=(-1, -0.2), size=SZ, layer=R, offset_pt=16)
    f.label(pt(3, 13), "wall", italic=False, direction=(1, 0), size=SZ)
    return f


@figure(f"{S}_5")
def q5() -> Figure:
    """Mohammad halfway between trees 200 ft apart: pine 100 tan 37, spruce 100 tan 26."""
    pine_h, spr_h = 100 * tan(37), 100 * tan(26)
    M, Pb, Sb = pt(0, 0), pt(-100, 0), pt(100, 0)
    Pt, St = pt(-100, pine_h), pt(100, spr_h)
    assert abs(angle_deg(M, Pb, Pt) - 37) < 1e-9 and abs(angle_deg(M, Sb, St) - 26) < 1e-9
    assert abs(pine_h - 75.36) < 0.01 and abs(spr_h - 48.77) < 0.01 and abs(pine_h - spr_h - 26.58) < 0.01
    cp, cs = ctr(M, Pb, Pt), ctr(M, Sb, St)
    f = Figure(width_in=3.2, height_in=1.8)
    f.poly([M, Pb, Pt])
    f.poly([M, Sb, St])
    f.right_angle(Pb, M, Pt, size=7)
    f.right_angle(Sb, M, St, size=7)
    f.arc(M, Pb, Pt, r=22)
    f.arc(M, Sb, St, r=22)
    f.angle_label(M, Pb, Pt, "$37^\\circ$", dist=40, size=SZ)
    f.angle_label(M, Sb, St, "$26^\\circ$", dist=42, size=SZ)
    f.dots([M])
    f.label(M, "Mohammad", italic=False, direction=(0, -1), size=SZ, offset_pt=24)
    f.side_label(Pb, M, "100 ft", center=cp, size=SZ)
    f.side_label(M, Sb, "100 ft", center=cs, size=SZ)
    f.label(Pt, "pine", italic=False, direction=(0, 1), size=SZ)
    f.label(St, "spruce", italic=False, direction=(0, 1), size=SZ)
    f.side_label(Pb, Pt, "$\\approx75.4$ ft", center=cp, size=SZ, layer=R, offset_pt=16)
    f.side_label(Sb, St, "$\\approx48.8$ ft", center=cs, size=SZ, layer=R, offset_pt=16)
    return f


@figure(f"{S}_6")
def q6() -> Figure:
    """Challenge: two side views share the tower height; the ground view is a right triangle at the tower.
    Side views: heights drawn x2 so the small angles are readable (not to scale). Ground view below, to scale."""
    h = 500 * tan(13)
    ct = h / tan(17)
    mc = math.hypot(500, ct)
    assert abs(h - 115.43) < 0.01 and abs(ct - 377.57) < 0.01 and abs(mc - 626.54) < 0.01
    v = 2.0
    # Mary's view (left): Mary, tower base, tower top
    M1, T1 = pt(0, 0), pt(500, 0)
    H1 = pt(500, v * h)
    # Christopher's view (right)
    x0 = 830
    C2, T2 = pt(x0, 0), pt(x0 + ct, 0)
    H2 = pt(x0 + ct, v * h)
    assert angle_deg(C2, T2, H2) > angle_deg(M1, T1, H1)
    # From above (below the side views): tower T, Mary 500 ft south, Christopher west
    tx, ty = (x0 + ct) / 2 + ct / 2, -300
    T3 = pt(tx, ty)
    M3, C3 = pt(tx, ty - 500), pt(tx - ct, ty)
    assert abs(dist(M3, C3) - mc) < 1e-9 and abs(angle_deg(T3, M3, C3) - 90) < 1e-9
    f = Figure(width_in=3.5, height_in=3.8)
    c1, c2, c3 = ctr(M1, T1, H1), ctr(C2, T2, H2), ctr(T3, M3, C3)
    f.poly([M1, T1, H1])
    f.right_angle(T1, M1, H1, size=16)
    f.arc(M1, T1, H1, r=110)
    f.angle_label(M1, T1, H1, "$13^\\circ$", dist=170, size=SZ - 1)
    f.label(M1, "Mary", italic=False, direction=(0, -1), size=SZ - 1)
    f.side_label(M1, T1, "500 ft", center=c1, size=SZ - 1)
    f.label(pt(500, v * h / 2), "$h\\approx115.4$", italic=False, direction=(1, 0), offset_pt=22, size=SZ - 1,
            layer=R, fixed=True)
    f.poly([C2, T2, H2])
    f.right_angle(T2, C2, H2, size=16)
    f.arc(C2, T2, H2, r=110)
    f.angle_label(C2, T2, H2, "$17^\\circ$", dist=170, size=SZ - 1)
    f.label(C2, "Christopher", italic=False, direction=(-1, 0), size=SZ - 1)
    f.side_label(T2, H2, "$h$", center=c2, size=SZ - 1, layer=R)
    f.side_label(C2, T2, "$\\approx377.6$ ft", center=c2, size=SZ - 1, layer=R)
    f.seg(T3, M3)
    f.seg(T3, C3)
    f.dots([T3, M3, C3])
    f.right_angle(T3, M3, C3, size=22)   # Nov 19: given in the stem now ("South and west make a right angle")
    f.seg(M3, C3, layer=R)
    f.label(T3, "tower", italic=False, direction=(1, 0), size=SZ - 1)
    f.label(M3, "Mary", italic=False, direction=(1, 0), size=SZ - 1)
    f.label(C3, "Christopher", italic=False, direction=(-1, 0), size=SZ - 1)
    f.side_label(T3, M3, "500 ft", center=c3, size=SZ - 1)
    f.side_label(C3, T3, "$\\approx377.6$ ft", center=pt(tx - ct / 2, ty + 200), size=SZ - 1, layer=R)
    f.label(midpoint(M3, C3), "$\\approx626.5$ ft", italic=False, direction=(-1, -0.7), offset_pt=34,
            size=SZ - 1, layer=R, fixed=True)
    f.text(pt(tx - ct, ty - 520), "view from above", size=SZ - 1, fixed=True)
    return f

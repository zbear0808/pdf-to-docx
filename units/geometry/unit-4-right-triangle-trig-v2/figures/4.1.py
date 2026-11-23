"""Figures for lesson "4.1" (lessons/4.1.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Ramp and flared-side figures stretch the height for readability and say "Not drawn to scale";
the given numbers carry the math.
"""
import math

import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, assert_lengths, assert_similar, collinear, dist, figure
from lesson_builder.figures.coordinate import axes, num_label, plot_line

S = '4.1'
NOTE = 9  # "Not drawn to scale" text size


def _right_tri(f, pts, names):
    """Triangle with dots, vertex names, and a right-angle mark at pts[0]."""
    f.poly(pts)
    f.dots(pts)
    f.label_poly(pts, names)
    f.right_angle(pts[0], pts[1], pts[2], size=0.045 * max(dist(pts[0], pts[1]), dist(pts[0], pts[2])))


# ---------------------------------------------------------------- warm-up, Together, partner

@figure(f"{S}_warmup")
def warmup() -> Figure:
    A, B, C = P((0, 0), (4, 0), (0, 3))
    D, E, F = P((5.5, 1.5), (7.5, 1.5), (5.5, 3))
    assert_similar([A, B, C], [D, E, F], k=0.5)
    assert np.isclose(angle_deg(A, B, C), 90) and np.isclose(angle_deg(D, E, F), 90)
    f = Figure(width_in=2.6, height_in=1.5)
    for tri, nm in (([A, B, C], "ABC"), ([D, E, F], "DEF")):
        f.poly(tri)
        f.dots(tri)
        f.label_poly(tri, nm)
    return f


@figure(f"{S}_together_a")
def together_a() -> Figure:
    A, B, C = P((0, 0), (5, 0), (0, 3))
    assert np.isclose(angle_deg(A, B, C), 90)
    x = dist(B, C)
    assert np.isclose(x, math.sqrt(34)) and f"{x:.2f}" == "5.83"
    f = Figure(width_in=2.2, height_in=1.4)
    _right_tri(f, [A, B, C], "ABC")
    f.side_label(A, C, "3", center=B)
    f.side_label(A, B, "5", center=C)
    f.side_label(B, C, "x", center=A, italic=True)
    f.side_label(B, C, r"$x \approx 5.83$", center=(4, 3), layer="answer", size=11)
    return f


GHJ = P((0, 0), (3, 0), (0, 4))     # Problem 2: right angle at G, 53° at H, z = JH
NOP = P((0, 0), (9, 0), (0, 12))    # Problem 3: right angle at N, 53° at O
assert_similar(GHJ, NOP, k=3)       # AA (right angle, 53°): z = OP / 3 = 5


@figure(f"{S}_together_b")
def together_b() -> Figure:
    G, H, J = GHJ
    assert np.isclose(angle_deg(G, H, J), 90)
    assert round(angle_deg(H, G, J)) == 53 and np.isclose(dist(J, H), 5)
    f = Figure(width_in=1.5, height_in=1.8)
    _right_tri(f, [G, H, J], "GHJ")
    f.side_label(G, H, "3", center=J)
    f.side_label(H, J, "z", center=G, italic=True)
    f.arc(H, G, J, r=0.45)
    f.angle_label(H, G, J, "53°", size=10)
    f.side_label(H, J, r"$z = 5$", center=(3, 4), layer="answer", size=11)
    return f


@figure(f"{S}_partner_pno")
def partner_pno() -> Figure:
    N, O, Pt = NOP
    assert np.isclose(dist(Pt, O), 15) and np.isclose(dist(Pt, N), 12)
    assert round(angle_deg(O, N, Pt)) == 53 and np.isclose(dist(Pt, O) / 3, dist(GHJ[2], GHJ[1]))
    f = Figure(width_in=1.5, height_in=1.8)
    _right_tri(f, [N, O, Pt], "NOP")
    f.side_label(N, O, "9", center=Pt)
    f.side_label(O, Pt, "15", center=N)
    f.arc(O, N, Pt, r=1.3)
    f.angle_label(O, N, Pt, "53°", size=10)
    f.side_label(N, Pt, "12", center=O, layer="answer", size=11)
    return f


# ---------------------------------------------------------------- ramp design (not to scale)

STEPS, STEP_IN = 4, 7
RISE_IN = STEPS * STEP_IN
RUN_IN = 12 * RISE_IN
assert RISE_IN == 28 and RUN_IN == 336 and RUN_IN / 12 == 28 and RUN_IN / 12 <= 30
assert round(math.degrees(math.atan(RISE_IN / RUN_IN)), 1) == 4.8
assert round(math.hypot(RISE_IN, RUN_IN), 1) == 337.2


@figure(f"{S}_ramp")
def ramp() -> Figure:
    sy = 6          # vertical stretch so the 7 in steps are readable
    tread = 24      # drawn tread width only; not a given
    land = 60       # 5 ft landing
    top = RISE_IN * sy
    x_stair = -land - (STEPS - 1) * tread
    prof = [(x_stair, 0)]
    for k in range(STEPS - 1):
        x = x_stair + k * tread
        prof += [(x, (k + 1) * STEP_IN * sy), (x + tread, (k + 1) * STEP_IN * sy)]
    prof += [(-land, top), (0, top), (0, 0)]
    foot = (-land - RUN_IN, 0)
    f = Figure(width_in=5.0, height_in=2.5)   # v2: printed stacked at full size, so pairs have room to sketch
    f.seg((foot[0] - land - 15, 0), (25, 0))
    f.poly(prof, closed=False)
    f.seg((0, top), (0, top + 70))
    f.text((38, top + 45), "door", size=10)
    f.side_label((x_stair, 0), (x_stair, STEP_IN * sy), "7 in", center=(0, 0), size=10)
    f.text((foot[0] - 10, top + 40), "Not drawn to scale", size=NOTE)
    # given: the total rise (printed in the prompt, so it is not student work)
    f.seg((14, 0), (14, top), dashed=True)
    f.side_label((14, 0), (14, top), f"rise\n{RISE_IN} in", center=(0, 0), size=10)
    # answer: the ramp and its labels
    f.seg(foot, (-land, top), layer="answer")
    f.arc(foot, (0, 0), (-land, top), r=55, layer="answer")
    f.angle_label(foot, (0, 0), (-land, top), "≈ 4.8°", dist=115, layer="answer", size=10)
    f.side_label(foot, (-land, 0), f"run {RUN_IN} in = {RUN_IN // 12} ft", center=(0, top), layer="answer", size=10)
    f.seg((foot[0] - land, 0), foot, layer="answer", lw=3)
    f.text((foot[0] - land / 2, 50), "5 ft × 5 ft\nlanding", layer="answer", size=9)
    f.text((-55, top + 30), "5 ft × 5 ft\nlanding", layer="answer", size=9)
    f.text((foot[0] + 110, 150), "ramp at least\n36 in wide", layer="answer", size=9)
    return f


def _slope_tri(run, rise, sy, angle_txt, ratio_txt, ans, rise_txt="4 in"):
    """Right triangle for a 1:n slope: foot at the origin, right angle under the top."""
    assert round(math.degrees(math.atan(rise / run)), 1) == float(angle_txt)
    A, B, C = np.array((0.0, 0.0)), np.array((run, 0.0)), np.array((run, rise * sy))
    f = Figure(width_in=2.6, height_in=1.8)
    f.poly([A, B, C])
    f.right_angle(B, A, C, size=2.2)
    f.side_label(B, C, rise_txt, center=A, size=11)
    f.arc(A, B, C, r=run * 0.22)
    f.angle_label(A, B, C, f"{angle_txt}°", dist=run * 0.42, size=10)
    f.side_label(A, B, "?", center=C, size=11)
    f.text((run * 0.2, rise * sy * 0.6), ratio_txt, size=10)
    f.text((run * 0.2, rise * sy * 1.05), "Not drawn to scale", size=NOTE)
    f.side_label(A, B, ans, center=C, layer="answer", size=11, offset_pt=24)
    return f


@figure(f"{S}_exit")
def exit_() -> Figure:
    assert 4 * 10 == 40
    return _slope_tri(40, 4, 5, "5.7", "1 : 10", "40 in")


# ---------------------------------------------------------------- practice

def _ramp_tri(run, rise, ok, hyp=None, w=2.0, h=0.6):
    """Practice 1 ramp: run along the bottom, rise on the right, true shape."""
    A, B, C = np.array((0.0, 0.0)), np.array((run, 0.0)), np.array((run, rise))
    ang = math.degrees(math.atan(rise / run))
    assert (ang <= 4.8) == ok, (run, rise, ang)
    f = Figure(width_in=w, height_in=h)
    f.poly([A, B, C])
    f.dots([A, B, C], size=8)
    s = 0.7 * rise if rise < run / 4 else 0.12 * min(run, rise)
    f.poly([B + (-s, 0), B + (-s, s), B + (0, s)], closed=False, lw=1.2)
    f.side_label(B, C, f"{rise:g}", center=A, size=11)
    if hyp is None:
        f.side_label(A, B, f"{run:g}", center=C, size=11)
    else:
        assert np.isclose(dist(A, C), hyp)
        f.side_label(A, C, f"{hyp:g}", center=B, size=11)
    return f


@figure(f"{S}_pr1_a")
def pr1_a() -> Figure:
    return _ramp_tri(12, 1, True)


@figure(f"{S}_pr1_b")
def pr1_b() -> Figure:
    return _ramp_tri(30, 40, False, w=1.3, h=1.6)


@figure(f"{S}_pr1_c")
def pr1_c() -> Figure:
    assert 10 / 120 == 1 / 12
    return _ramp_tri(120, 10, True)


@figure(f"{S}_pr1_d")
def pr1_d() -> Figure:
    return _ramp_tri(15, 1, True)


@figure(f"{S}_pr1_e")
def pr1_e() -> Figure:
    run = math.sqrt(15 ** 2 - 2 ** 2)
    assert round(math.degrees(math.asin(2 / 15)), 2) == 7.66
    return _ramp_tri(run, 2, False, hyp=15)


@figure(f"{S}_pr2")
def pr2() -> Figure:
    t = math.atan2(12, 5)
    A = np.array((0.0, 14.0))
    C = A + (13, 0)
    B = A + 5 * np.array((math.cos(t), -math.sin(t)))
    D, E, F = P((1, 0), (25, 0), (25, 10))
    assert_lengths([(A, B, 5), (B, C, 12), (A, C, 13), (D, E, 24), (E, F, 10), (D, F, 26)])
    assert np.isclose(angle_deg(A, B, C), angle_deg(F, D, E))
    assert_similar([A, B, C], [F, E, D], k=2)
    f = Figure(width_in=3.0, height_in=2.1)
    for tri, nm, rv in (([A, B, C], "ABC", B), ([D, E, F], "DEF", E)):
        f.poly(tri)
        f.dots(tri, size=8)
        f.label_poly(tri, nm)
    f.right_angle(B, A, C, size=0.8)
    f.right_angle(E, D, F, size=0.8)
    f.arc(A, B, C, r=1.2)
    f.arc(F, D, E, r=1.6)
    f.side_label(A, B, "5", center=C, size=11)
    f.side_label(B, C, "12", center=A, size=11)
    f.side_label(D, F, "26", center=E, size=11)
    f.side_label(E, F, "10", center=D, size=11)
    f.side_label(A, C, "13", center=B, layer="answer", size=11)
    f.side_label(D, E, "24", center=F, layer="answer", size=11)
    return f


@figure(f"{S}_pr3")
def pr3() -> Figure:
    A, B, C = P((-3, 0), (0, 4), (0, 0))
    D, E = np.array((0.0, 16 / 3)), np.array((1.0, 16 / 3))
    assert collinear(A, B, E) and np.isclose(dist(B, D), 4 / 3)
    assert_lengths([(A, B, 5), (B, C, 4), (A, C, 3), (D, E, 1)])
    assert_similar([A, B, C], [E, B, D], k=1 / 3)
    f = Figure(width_in=2.0, height_in=2.2)
    f.seg((-4, 0), (2, 0))
    f.seg((-4, 16 / 3), (2, 16 / 3))
    f.seg((0, -0.8), (0, 6.2))
    f.seg(A, E)
    f.dots([A, B, C, D, E], size=10)
    f.right_angle(C, A, B, size=0.3)
    f.right_angle(D, (2, 16 / 3), B, size=0.3)
    f.label(A, "A", direction=(-0.5, 1))
    f.label(B, "B", direction=(1, 0))
    f.label(C, "C", direction=(1, 1))
    f.label(D, "D", direction=(-1, 1))
    f.label(E, "E", direction=(0.5, 1))
    f.side_label(A, B, "5", center=C, size=11)
    f.side_label(B, C, "4", center=(1, 2), size=11)
    f.side_label(D, E, "1", center=B, layer="answer", size=11, offset_pt=18)
    return f


@figure(f"{S}_pr6")
def pr6() -> Figure:
    m1, b1, m2, b2 = -2 / 3, 1, 2 / 3, -3
    x = (b2 - b1) / (m1 - m2)
    assert np.isclose(x, 3) and np.isclose(m1 * x + b1, -1)
    assert 0 > m1 * 5 + b1 and 0 <= m2 * 5 + b2   # test point (5, 0) is in both
    f = Figure(width_in=2.8, height_in=2.8)
    axes(f, -5, 5, -5, 5, labels_every=100)   # numbers go along the bottom and left edges, clear of the lines
    for v in range(-5, 6):
        if v:
            num_label(f, (v, -5), v, (0, -11))
            num_label(f, (-5, v), v, (-11, 0))
    plot_line(f, m1, b1, layer="answer", dashed=True)
    plot_line(f, m2, b2, layer="answer")
    region = np.array([(3, -1), (5, m2 * 5 + b2), (5, m1 * 5 + b1)])
    f.custom(lambda ax, c: ax.fill(region[:, 0], region[:, 1], color=c, alpha=0.25, lw=0), layer="answer",
             extent=[(3, -7 / 3), (5, 1 / 3)])
    return f

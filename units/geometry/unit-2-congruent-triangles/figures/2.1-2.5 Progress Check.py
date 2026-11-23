"""Figures for assessment "2.1-2.5 Progress Check" (assessments/2.1-2.5 Progress Check.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Loop: uv run lesson-builder figs <unit> -l "2.1-2.5 Progress Check" (0 errors, no label warnings).
All four source images are redrawn: K was off line HF (q1), the marks were red (q4), EMF (q5), under 150 dpi (q6).
No drawing tasks, so no answer layers.
Names keep the source item numbers. Nov 19: old item 3 was cut, so _q4 is item 3, _q5 item 4, _q6 item 5.
Nov 20: _q5 (item 4) is a new SSA case that answers "no"; the source's SAA pair JAR/DIL is gone.
"""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, assert_distinct, collinear, dist, figure,
                                    is_rigid_image, mark_congruent, midpoint, reflect, rotate, ssa_triangles,
                                    translate)

S = '2.1-2.5 Progress Check'


def _polar(r, deg, origin=(0.0, 0.0)):
    a = np.radians(deg)
    return np.asarray(origin, float) + r * np.array((np.cos(a), np.sin(a)))


# q1: parallelogram HGFE, diagonal HF, K its midpoint. 180 deg about K: F -> H, G -> E, H -> F.
H1, G1, F1, E1 = P((0, 0), (3.4, 0), (5.4, 2), (2, 2))
K1 = midpoint(H1, F1)
assert np.allclose(rotate(np.array([F1, G1, H1]), 180, about=K1), [H1, E1, F1])
assert abs(dist(G1, H1) - dist(H1, K1)) > 0.4      # choice D (GH = HK) looks false
assert abs(dist(E1, F1) - dist(G1, F1)) > 0.4      # choice F (EFH = GFH) looks false


@figure(f"{S}_q1")
def q1() -> Figure:
    f = Figure(width_in=2.9, height_in=1.45)
    f.poly([H1, G1, F1, E1])
    f.seg(H1, F1)
    f.dots([H1, G1, F1, E1, K1])
    f.label(H1, "H", direction=(-1, -0.4))
    f.label(G1, "G", direction=(0.2, -1))
    f.label(F1, "F", direction=(1, 0.4))
    f.label(E1, "E", direction=(-0.2, 1))
    f.label(K1, "K", direction=(-0.3, 1))
    return f


# q4: L, N, D collinear; M, N, C collinear. LN = NC (1 tick), LM = CD (2), MN = ND (3).
# Angles: L, C (2 arcs); M, D (3 arcs); vertical angles LNM, DNC (1 arc). Triangle CND = triangle LNM.
N4 = np.array((0.0, 0.0))
L4, D4 = np.array((-2.4, 0.0)), np.array((3.1, 0.0))
M4, C4 = _polar(3.1, 118), _polar(2.4, -62)
assert collinear(L4, N4, D4) and collinear(M4, N4, C4)
assert is_rigid_image(np.array([L4, N4, M4]), np.array([C4, N4, D4]))
assert_distinct([angle_deg(L4, N4, M4), angle_deg(M4, L4, N4), angle_deg(N4, L4, M4)])


@figure(f"{S}_q4")
def q4() -> Figure:
    f = Figure(width_in=2.6, height_in=2.45)
    f.seg(L4, D4)
    f.seg(M4, C4)
    f.seg(L4, M4)
    f.seg(C4, D4)
    f.dots([L4, N4, D4, M4, C4])
    f.label(L4, "L", direction=(-1, -0.3))
    f.label(D4, "D", direction=(1, 0.3))
    f.label(M4, "M", direction=(0, 1))
    f.label(C4, "C", direction=(0, -1))
    f.label(N4, "N", direction=(-0.6, -1))
    mark_congruent(f, [((L4, N4), (N4, C4)), ((L4, M4), (C4, D4)), ((M4, N4), (N4, D4)),
                       ((N4, L4, M4), (N4, D4, C4)), ((L4, M4, N4), (C4, D4, N4)),
                       ((M4, N4, L4), (D4, N4, C4))], size=0.17, r=[0.45, 0.45, 0.42])
    return f


# q5 (item 4, Nov 20): SSA, answer "no". Both triangles have a 40 degree angle (A, S), the side next to it
# (AB = SP = 2.4, 1 tick), and the side across from it (BV = PW = 1.7, 2 ticks). The angle is not between the
# marked sides, and 2.4 sin 40 < 1.7 < 2.4, so two different triangles fit: ssa_triangles gives both
# (AV = 2.55 and SW = 1.12). The short one is turned 180 degrees. No numbers print (marks only, like 2.5 #4).
_LONG, _SHORT = ssa_triangles(2.4, 1.7, 40)
A5, B5, V5 = _LONG
S5, P5, W5 = translate(rotate(_SHORT, 180, about=(0, 0)), (5.6, 1.4))
for _v, _a, _o in ((A5, B5, V5), (S5, P5, W5)):
    assert np.isclose(angle_deg(_v, _a, _o), 40)                       # the marked angle
    assert np.isclose(dist(_v, _a), 2.4) and np.isclose(dist(_a, _o), 1.7)   # the two marked sides
assert not is_rigid_image(_LONG, np.array([S5, P5, W5]))               # SSA: the triangles are not congruent
assert dist(A5, V5) - dist(S5, W5) > 1.0                               # third sides clearly differ


@figure(f"{S}_q5")
def q5() -> Figure:
    f = Figure(width_in=2.9, height_in=1.3)
    f.poly([A5, B5, V5])
    f.poly([S5, P5, W5])
    f.dots([A5, B5, V5, S5, P5, W5])
    f.label(A5, "A", direction=(-1, -0.4))
    f.label(B5, "B", direction=(0.4, -1))
    f.label(V5, "V", direction=(0, 1))
    f.label(S5, "S", direction=(1, 0.4))
    f.label(P5, "P", direction=(-0.4, 1))
    f.label(W5, "W", direction=(0, -1))
    mark_congruent(f, [((A5, B5), (S5, P5)), ((B5, V5), (P5, W5)), ((A5, B5, V5), (S5, P5, W5))],
                   size=0.15, r=0.4)
    return f


# q6: X, M, Y collinear; triangle MTY is the mirror image of triangle MDX across x = 2.4.
# Marks: XM = MY (2 ticks), DM = TM (3 ticks), angle DMX = angle TMY (1 arc). SAS.
X6, M6, Y6 = P((0, 0), (2.4, 0), (4.8, 0))
D6 = _polar(2.6, 125, origin=M6)
T6 = reflect(np.array([D6]), M6, M6 + (0, 1))[0]
assert is_rigid_image(np.array([M6, D6, X6]), np.array([M6, T6, Y6]))
assert np.isclose(angle_deg(M6, D6, X6), angle_deg(M6, T6, Y6))


@figure(f"{S}_q6")
def q6() -> Figure:
    f = Figure(width_in=2.9, height_in=1.6)
    f.seg(X6, Y6)
    f.poly([X6, D6, M6], closed=False)
    f.poly([M6, T6, Y6], closed=False)
    f.dots([X6, M6, Y6, D6, T6])
    f.label(X6, "X", direction=(-1, -0.3))
    f.label(M6, "M", direction=(0, -1))
    f.label(Y6, "Y", direction=(1, -0.3))
    f.label(D6, "D", direction=(0, 1))
    f.label(T6, "T", direction=(0, 1))
    f.ticks(X6, M6, n=2, size=0.16)
    f.ticks(M6, Y6, n=2, size=0.16)
    f.ticks(D6, M6, n=3, size=0.16)
    f.ticks(M6, T6, n=3, size=0.16)
    f.arc(M6, X6, D6, r=0.45)
    f.arc(M6, T6, Y6, r=0.45)
    return f

"""Figures for lesson "2.8" (lessons/2.8.yaml): the Perpendicular Bisector Theorem.
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Shapes follow the teacher's source drawings (Lesson 2.8 Student Notes and Practice Problems; IM Geo.2 Lesson 8
Activity 3 and reference chart), redrawn because the source images are under 150 dpi at print size and the
activity diagrams use blue ink. Marks the handout prints as scaffolds are given ink; marks students add are answers.
Loop: uv run lesson-builder figs units/geometry/unit-2-congruent-triangles -l 2.8
"""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, collinear, dist, figure, foot, midpoint

S = '2.8'


def _past(a, b, t):
    """Point t units beyond b on ray ab."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return b + t * (b - a) / np.linalg.norm(b - a)


# ---------------------------------------------------------------- warm-up: triangle ACR (source image1)
_WA, _WR, _WC = P((0, 0), (4, 0), (2.69, 2.15))
_WF = midpoint(_WA, _WR)                                                        # median CF
_WE = _WA + dist(_WC, _WA) / (dist(_WC, _WA) + dist(_WC, _WR)) * (_WR - _WA)    # angle bisector CE
_WD = foot(_WC, _WA, _WR)                                                       # altitude CD
_WT = midpoint(_WF, _WR)                                                        # where the key's tick for FR goes
assert np.isclose(dist(_WA, _WF), dist(_WF, _WR))
assert np.isclose(angle_deg(_WC, _WA, _WE), angle_deg(_WC, _WE, _WR))           # 41.4 deg each
assert np.isclose(angle_deg(_WD, _WC, _WR), 90)
assert collinear(_WA, _WF, _WE, _WD, _WR)
# feet in the plan's order, then FR's midpoint: F < E < D < tick < R, each at least 0.3 units (0.2 in) apart, and the
# tick well off the middle of DR, so it reads as FR's tick (the source drew D at FR's midpoint, under the tick)
_xs = [p[0] for p in (_WF, _WE, _WD, _WT, _WR)]
assert all(b - a >= 0.3 for a, b in zip(_xs, _xs[1:])) and midpoint(_WD, _WR)[0] - _WT[0] >= 0.3
# not isosceles (the three segments are apart) and not right at C (82.7 deg), so no extra fact looks true
assert dist(_WC, _WA) / dist(_WC, _WR) > 1.3 and abs(angle_deg(_WC, _WA, _WR) - 90) > 5


@figure(f"{S}_warmup")
def warmup() -> Figure:
    """Triangle ACR with segments CF, CE, CD and no marks (given). Key: one tick on each half of AR, arcs for
    angle ACE and angle ECR, and the right angle at D."""
    A, R, C, F, E, D = _WA, _WR, _WC, _WF, _WE, _WD
    f = Figure(width_in=3.3, height_in=2.2)
    f.poly([A, R, C])
    for p in (F, E, D):
        f.seg(C, p)
    f.dots([A, F, E, D, R, C])
    f.label(A, "A", direction=(-1, -0.4))
    f.label(R, "R", direction=(1, -0.4))
    f.label(C, "C", direction=(0, 1))
    for p, name in ((F, "F"), (E, "E"), (D, "D")):
        f.label(p, name, direction=(0, -1))
    f.ticks(A, F, 1, layer="answer")
    f.ticks(F, R, 1, layer="answer")   # at FR's midpoint, right of D
    # one arc each; two radii, because rays CF and CD cross the marks and one radius would read as one arc
    # across all of angle ACR. Large radii: CF and CE are close together near C
    f.arc(C, A, E, r=0.85, layer="answer")
    f.arc(C, E, R, r=1.05, layer="answer")
    f.right_angle(D, C, A, size=0.15, layer="answer")   # on the E side, so FR's tick stands clear
    return f


# ---------------------------------------------------------------- Problems 1-2: isosceles ABC (source image4, image5)
_A, _B, _C = P((-1, 0), (1, 0), (0, 2.3))
_D = np.array((0.0, 0.0))
assert np.isclose(dist(_A, _C), dist(_B, _C))
assert np.isclose(angle_deg(_C, _A, _D), angle_deg(_C, _D, _B)) and collinear(_A, _D, _B)   # Noah: CD bisects C
assert np.allclose(_D, midpoint(_A, _B))                              # Problem 2: CD is a median
assert np.isclose(angle_deg(_A, _B, _C), angle_deg(_B, _C, _A))       # base angles, 66.5 deg (Problem 2 row 2)
assert np.isclose(angle_deg(_D, _A, _C), 90)                          # so the keys' right angle at D is true
_ISO_W = 1.85   # one canvas width, width-limited, so Noah's figure and the median figure print at one scale


@figure(f"{S}_noah")
def noah() -> Figure:
    """Problem 1, Noah's diagram: AC = BC and his angle bisector (dashed line through C and D) with its marks
    (given). Key: the right angle at D, which Noah still has to show."""
    A, B, C, D = _A, _B, _C, _D
    f = Figure(width_in=_ISO_W, height_in=2.7)
    f.poly([A, B, C])
    f.seg(_past(C, D, 0.35), _past(D, C, 0.35), dashed=True)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, -0.4))
    f.label(B, "B", direction=(1, -0.4))
    f.label(C, "C", direction=(1, 0.3))
    f.label(D, "D", direction=(-0.8, -1))
    f.ticks(A, C, 1)
    f.ticks(B, C, 1)
    f.arc(C, A, D, r=0.55, ticks=1)
    f.arc(C, D, B, r=0.55, ticks=1)
    f.right_angle(D, B, C, layer="answer")
    return f


@figure(f"{S}_median")
def median() -> Figure:
    """Problem 2: AC = BC, median CD (double ticks on AD and DB), and the base angles from row 2 (given).
    Key: the right angle at D, which the proof shows."""
    A, B, C, D = _A, _B, _C, _D
    f = Figure(width_in=_ISO_W, height_in=2.7)
    f.poly([A, B, C])
    f.seg(C, D)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, -0.4))
    f.label(B, "B", direction=(1, -0.4))
    f.label(C, "C", direction=(0, 1))
    f.label(D, "D", direction=(0, -1))
    f.ticks(A, C, 1)
    f.ticks(B, C, 1)
    f.ticks(A, D, 2)
    f.ticks(D, B, 2)
    f.arc(A, B, C)
    f.arc(B, A, C)
    f.right_angle(D, B, C, layer="answer")
    return f


# ---------------------------------------------------------------- Problem 4: P on the perpendicular bisector of AB
_PA, _PB = P((0, 0), (3, 0.6))
_PM = midpoint(_PA, _PB)
_PP = _PM + 0.325 * np.array((-1.0, 5.0))
_P_LO, _P_HI = _past(_PP, _PM, 0.45), _past(_PM, _PP, 0.4)   # line PM runs on past M and past P
assert np.isclose(angle_deg(_PM, _PB, _PP), 90)
assert np.isclose(dist(_PP, _PA), dist(_PP, _PB))                  # 2.255: what the proof shows
assert np.isclose((_PB - _PA)[1] / (_PB - _PA)[0], 0.2)            # AB is tilted, so it doesn't look like Problem 2
assert collinear(_P_LO, _PM, _PP, _P_HI)


@figure(f"{S}_converse")
def converse() -> Figure:
    """Problem 4 (source image6, IM Activity 3): triangle ABP, M the midpoint of AB, line PM perpendicular to AB
    (given ticks and right angle). Key: double ticks on PA and PB."""
    A, B, M, Pt = _PA, _PB, _PM, _PP
    f = Figure(width_in=2.4, height_in=2.2)
    f.poly([A, B, Pt])
    f.seg(Pt, M)
    f.seg(_P_LO, M, dashed=True)
    f.seg(Pt, _P_HI, dashed=True)
    f.dots([A, B, Pt, M])
    f.label(A, "A", direction=(-0.6, -1))
    f.label(B, "B", direction=(1, 0))
    f.label(Pt, "P", direction=(-1, 0.5))
    f.label(M, "M", direction=(1, -1))
    f.ticks(A, M, 1)
    f.ticks(M, B, 1)
    f.right_angle(M, B, Pt)
    f.ticks(Pt, A, 2, layer="answer")
    f.ticks(Pt, B, 2, layer="answer")
    return f


# ---------------------------------------------------------------- practice 2: Kiran (source image7, px / 100, y up)
_KA, _KC = P((2.08, -0.45), (1.78, -2.28))
_KD = _KA + dist(_KA, _KC) * (np.array((0.25, -0.77)) - _KA) / dist(_KA, (0.25, -0.77))   # source D's direction
_KB = midpoint(_KD, _KC)
assert np.isclose(dist(_KA, _KD), dist(_KA, _KC))                  # 1.854, the ticks
assert collinear(_KD, _KB, _KC)
assert np.isclose(angle_deg(_KB, _KA, _KD), 90)                    # true, but not marked: the item asks for it


@figure(f"{S}_pr_kiran")
def pr_kiran() -> Figure:
    """Practice 2: isosceles DAC with AD = AC and segment AB to B on DC (no other marks, as in the source)."""
    A, B, C, D = _KA, _KB, _KC, _KD
    f = Figure(width_in=1.95, height_in=1.95)
    f.poly([D, A, C])
    f.seg(A, B)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(0.4, 1))
    f.label(D, "D", direction=(-1, 0.5))
    f.label(B, "B", direction=(-1, -0.6))
    f.label(C, "C", direction=(0.6, -1))
    f.ticks(A, D, 1)
    f.ticks(A, C, 1)
    return f


# ---------------------------------------------------------------- practice 3-5: small isosceles ABC (source image10)
_TA, _TB, _TC = P((-1, 0), (1, 0), (0, 1.45))                     # practice 4-5: base angles 55.4
_TC3 = np.array((0.0, np.sqrt((2 * 22 / 16) ** 2 - 1)))           # practice 3: C(0, 2.56), so AC : AB = 22 : 16
_TD = np.array((0.0, 0.0))
assert np.allclose(_TD, midpoint(_TA, _TB))                        # median marks are true
for _c in (_TC, _TC3):
    assert np.isclose(dist(_TA, _c), dist(_TB, _c))                # the ticks
    assert np.isclose(angle_deg(_c, _TA, _TD), angle_deg(_c, _TD, _TB))   # bisector marks are true
    assert np.isclose(angle_deg(_TD, _TA, _c), 90)                 # altitude mark is true
# each figure fits its own item's numbers (practice 3 to scale; 4 and 5 within a few degrees)
assert np.isclose(dist(_TA, _TC3) / dist(_TA, _TB), 22 / 16)       # practice 3: AC = 22, AB = 60 - 44 = 16
assert abs(angle_deg(_TA, _TB, _TC) - 54) < 2                      # practice 4: angle A = 54 (drawn 55.4)
assert abs(angle_deg(_TB, _TA, _TC) - 52) < 4 and abs(angle_deg(_TC, _TA, _TD) - 38) < 4   # practice 5: B 52, ACD 38
assert abs(dist(_TB, _TC) / dist(_TA, _TB) - 13 / 16) < 0.1        # practice 5: CB = 13, AB = 16
# the items' numbers; each key uses AC = BC (the ticks) plus the variant's one mark
assert 60 - 2 * 22 == 16 < 2 * 22 and 16 / 2 == 8                  # practice 3: AB = 16, so AD = 8
assert (180 - 2 * 54) / 2 == 36                                    # practice 4: angle ACB = 72, so ACD = 36
_A5, _B5, _C5 = P((-8, 0), (8, 0), (0, np.sqrt(13 ** 2 - 8 ** 2)))   # practice 5 to scale: AD = DB = 8, CB = 13
assert np.isclose(dist(_A5, _B5) + 2 * dist(_B5, _C5), 42)
assert abs(angle_deg(_C5, _A5, (0, 0)) - 38) < 0.1 and abs(angle_deg(_B5, _A5, _C5) - 52) < 0.1   # the givens fit


def _small_iso(mark: str, C=_TC, height_in=1.3) -> Figure:
    """Isosceles ABC with CD and the ticks for AC = BC, plus the one mark the item's text names. The canvas is
    1.47 in wide and tall enough to stay width-limited, so the base prints at one length in every variant."""
    A, B, D = _TA, _TB, _TD
    f = Figure(width_in=1.47, height_in=height_in)
    f.poly([A, B, C])
    f.seg(C, D)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, -0.4))
    f.label(B, "B", direction=(1, -0.4))
    f.label(C, "C", direction=(0, 1))
    f.label(D, "D", direction=(0, -1))
    f.ticks(A, C, 1)
    f.ticks(B, C, 1)
    if mark == "median":
        f.ticks(A, D, 2)
        f.ticks(D, B, 2)
    elif mark == "bisector":
        f.arc(C, A, D, r=0.5, ticks=1)
        f.arc(C, D, B, r=0.5, ticks=1)
    elif mark == "altitude":
        f.right_angle(D, B, C)
    else:
        raise ValueError(mark)
    return f


@figure(f"{S}_pr_median")
def pr_median() -> Figure:
    """Practice 3: CD is a median (double ticks on AD and DB); C is higher, so AC looks 22/16 of AB."""
    return _small_iso("median", C=_TC3, height_in=1.75)


@figure(f"{S}_pr_bisector")
def pr_bisector() -> Figure:
    """Practice 4: CD bisects angle ACB (arcs with a tick, since the two angles share ray CD)."""
    return _small_iso("bisector")


@figure(f"{S}_pr_altitude")
def pr_altitude() -> Figure:
    """Practice 5: CD is an altitude (right angle at D)."""
    return _small_iso("altitude")


# ---------------------------------------------------------------- QuickNotes: C on the perpendicular bisector of AB
_NA, _NB = P((0, 0), (2.8, -0.5))
_NM = midpoint(_NA, _NB)
_NC = _NM + 0.75 * np.array((0.5, 2.8))
_N_LO, _N_HI = _past(_NC, _NM, 0.45), _past(_NM, _NC, 0.4)
assert np.isclose(angle_deg(_NM, _NC, _NB), 90)
assert np.isclose(dist(_NC, _NA), dist(_NC, _NB))                  # 2.564
assert collinear(_N_LO, _NM, _NC, _N_HI)


@figure(f"{S}_notes")
def notes() -> Figure:
    """QuickNotes (IM reference chart): C on the dashed perpendicular bisector of AB at M, with the marks for
    AM = MB, the right angle, and CA = CB (all given; QuickNotes print the same on both copies)."""
    A, B, M, C = _NA, _NB, _NM, _NC
    f = Figure(width_in=2.0, height_in=2.05)
    f.poly([A, B, C])
    f.seg(_N_LO, _N_HI, dashed=True)
    f.dots([A, B, M, C])
    f.label(A, "A", direction=(-1, 0.3))
    f.label(B, "B", direction=(1, 0.3))
    f.label(C, "C", direction=(1, 0.4))
    f.label(M, "M", direction=(-1, -0.6))
    f.ticks(C, A, 1)
    f.ticks(C, B, 1)
    f.ticks(A, M, 2)
    f.ticks(M, B, 2)
    f.right_angle(M, A, C)
    return f

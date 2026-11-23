"""Lesson 3.13 figures: the altitude to the hypotenuse. Given layer = student copy, answer layer (red) = key."""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_distinct, dilate, dist, figure, is_rigid_image, needs_reflection, similarity_ratio,
    translate,
)


def _close(a, b, tol=1e-6) -> bool:
    return abs(a - b) < tol


def _foot(p, a, b):
    """Foot of the perpendicular from p to line ab."""
    a, b, p = (np.asarray(x, float) for x in (a, b, p))
    u = (b - a) / np.linalg.norm(b - a)
    return a + np.dot(p - a, u) * u


def _sides(f, pts, labels, center, size=11, offset_pt=9):
    """labels[i] goes on side pts[i]-pts[i+1]; None skips."""
    n = len(pts)
    for i, t in enumerate(labels):
        if t is not None:
            f.side_label(pts[i], pts[(i + 1) % n], t, center, size=size, offset_pt=offset_pt)


# ---------------------------------------------------------------- warm-up: legs x and 12, hypotenuse 15
@figure("3.13_warmup")
def warmup() -> Figure:
    s = 0.2
    R, X, Y = P((0, 0), (12 * s, 0), (0, 9 * s))
    assert _close(dist(X, Y), 15 * s)
    f = Figure(width_in=1.7, height_in=1.3)
    f.poly([R, X, Y])
    f.right_angle(R, X, Y, size=0.18)
    c = (R + X + Y) / 3
    f.side_label(R, X, "12 in", c, size=11)
    f.side_label(X, Y, "15 in", c, size=11)
    f.side_label(R, Y, "x", c, italic=True, size=12)
    return f


# ---------------------------------------------------------------- Together: triangle ACB with altitude CD
TA, TB = P((0, 0), (15, 0))
TD = P(5.4, 0)
TC = P(5.4, -7.2)
assert _close(dist(TA, TC), 9) and _close(dist(TC, TB), 12) and _close(dist(TC, TD), 7.2)
assert _close(angle_deg(TA, TB, TC), 53.13010235415598) and _close(angle_deg(TA, TB, TC) + angle_deg(TB, TA, TC), 90)
# triangle ADC ~ triangle CDB (A->C, D->D, C->B), scale 4/3
assert _close(similarity_ratio([TA, TD, TC], [TC, TD, TB]), 4 / 3)


@figure("3.13_together")
def together() -> Figure:
    """Problem 1: only the two right angles are given; the class decides which one measurement to add."""
    k = 0.2
    A, B, D, C = (p * k for p in (TA, TB, TD, TC))
    f = Figure(width_in=3.0, height_in=1.75)
    f.poly([A, B, C])
    f.seg(C, D)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, 0.4))
    f.label(B, "B", direction=(1, 0.4))
    f.label(D, "D", direction=(0, 1))
    f.label(C, "C", direction=(0, -1))
    f.right_angle(D, A, C, size=0.13)
    f.right_angle(C, A, B, size=0.13)
    return f


# ---------------------------------------------------------------- Activity: right triangle HFE, altitude EG
H, F = P((0, 0), (20, 0))
E = H + 12 * np.array([np.cos(np.radians(-53.13010235415598)), np.sin(np.radians(-53.13010235415598))])
G = _foot(E, H, F)
assert _close(dist(H, E), 12) and _close(dist(E, F), 16) and _close(dist(H, F), 20)
assert _close(angle_deg(E, H, F), 90) and _close(angle_deg(G, H, E), 90)
assert _close(dist(H, G), 7.2) and _close(dist(G, E), 9.6) and _close(dist(G, F), 12.8)
# HFE ~ HEG ~ EFG (vertex order matters)
assert _close(similarity_ratio([H, F, E], [H, E, G]), 0.6)
assert _close(similarity_ratio([H, F, E], [E, F, G]), 0.8)
assert _close(dist(H, G) * dist(H, F), dist(H, E) ** 2) and _close(dist(G, E) ** 2, dist(H, G) * dist(G, F))


@figure("3.13_untangle")
def untangle() -> Figure:
    """Problem 2, at actual size so a patty-paper tracing fits an outline. Given: right triangle HFE with
    altitude EG, then two blank outlines turned like HFE (hypotenuse on top, right angle at the bottom),
    HFE dilated about H by 0.6 (fits HEG) and by 0.8 (fits EFG). Answer (red): the labels students add."""
    k = 0.1                                       # 1 unit = 0.1 in, so HF prints 2.0 in long
    h, fp, e, g = (p * k for p in (H, F, E, G))
    f = Figure(actual_size="in")
    f.poly([h, fp, e])
    f.seg(e, g)
    f.dots([h, fp, e, g])
    f.label(h, "H", direction=(-1, 0.4))
    f.label(fp, "F", direction=(1, 0.4))
    f.label(g, "G", direction=(0, 1))
    f.label(e, "E", direction=(0, -1))
    f.right_angle(g, fp, e, size=0.08)
    f.right_angle(e, h, fp, size=0.08)
    c = (h + fp) / 2 + P(0, 1)
    f.side_label(h, e, "12", c, size=10)
    f.side_label(e, fp, "16", c, size=10)
    f.angle_label(h, fp, e, "53°", dist=0.28, size=10)
    f.angle_label(fp, h, e, "37°", dist=0.41, size=10)

    base = np.array([h, fp, e])                   # 53° at the left end, 37° at the right end
    gap = 0.6
    small = translate(dilate(base, 0.6, h), (fp[0] + gap - h[0], 0))         # fits HEG as H, E, G
    big = translate(dilate(base, 0.8, h), (small[1][0] + gap - h[0], 0))     # fits EFG as E, F, G
    # each outline is a same-size copy of the triangle it fits, and both tracings need a flip
    assert is_rigid_image([h, e, g], small) and is_rigid_image([e, fp, g], big)
    assert needs_reflection([h, e, g], small) and needs_reflection([e, fp, g], big)
    # the key's angle labels: 53° at H in HEG and at E in EFG
    assert _close(angle_deg(H, E, G), angle_deg(H, F, E)) and _close(angle_deg(E, F, G), angle_deg(H, F, E))
    for pts, names, hyp in ((small, ["H", "E", "G"], "12"), (big, ["E", "F", "G"], "16")):
        a, b, r = pts
        assert _close(angle_deg(a, b, r), angle_deg(h, fp, e)) and _close(angle_deg(r, a, b), 90)
        f.poly(pts)
        f.dots(pts)
        f.right_angle(r, a, b, size=0.08)
        f.label(a, names[0], direction=(-1, 0.4), layer="answer")
        f.label(b, names[1], direction=(1, 0.4), layer="answer")
        f.label(r, names[2], direction=(0, -1), layer="answer")
        f.side_label(a, b, hyp, r, size=10, layer="answer")
        f.angle_label(a, b, r, "53°", dist=0.2, size=9, layer="answer")
        f.angle_label(b, a, r, "37°", dist=0.28, size=9, layer="answer")
    return f


# ---------------------------------------------------------------- in-class practice (v2): right angle at Q, altitude QS
# The Nov 19 exit ticket's triangle (3.13_exit), relettered P, Q, R, S for A, B, C, D (the QuickNotes use ABC with the
# right angle at C). Students find the leg PQ with similar triangles (PQ is a leg of PQR and the hypotenuse of PSQ),
# then check it with the Pythagorean theorem (QR = 3, PR = 5).
XP, XR, XS = P((0, 0), (5, 0), (3.2, 0))
XQ = P(3.2, 2.4)
assert _close(dist(XQ, XR), 3) and _close(dist(XP, XQ), 4) and _close(angle_deg(XQ, XP, XR), 90)
assert _close(angle_deg(XS, XR, XQ), 90) and _close(dist(XP, XR), 3.2 + 1.8)
assert _close(dist(XP, XQ) ** 2, dist(XP, XS) * dist(XP, XR))       # PQ^2 = PS * PR = 16
assert _close(similarity_ratio([XP, XQ, XR], [XP, XS, XQ]), 0.8)    # PQR ~ PSQ: P->P, Q->S, R->Q


@figure("3.13_apply")
def apply_fig() -> Figure:
    k = 0.5
    p, r, s, q = (x * k for x in (XP, XR, XS, XQ))
    f = Figure(width_in=2.4, height_in=1.35)
    f.poly([p, q, r])
    f.seg(q, s)
    f.dots([p, q, r, s])
    f.label(p, "P", direction=(-1, -0.3))
    f.label(r, "R", direction=(1, -0.3))
    f.label(s, "S", direction=(0, -1))
    f.label(q, "Q", direction=(0, 1))
    f.right_angle(q, p, r, size=0.12)
    f.right_angle(s, r, q, size=0.12)
    f.side_label(p, s, "3.2", q, size=10)
    f.side_label(s, r, "1.8", q, size=10)
    f.side_label(q, r, "3", s + P(-1, 0), size=10)
    return f


# ---------------------------------------------------------------- Practice 1: right triangle ABC (right angle C), altitude CD
@figure("3.13_p1")
def p1() -> Figure:
    A, B, D = P((0, 0), (5, 0), (1, 0))
    C = P(1, 2)
    assert _close(angle_deg(C, A, B), 90) and _close(dist(C, D) ** 2, 1 * 4)
    assert similarity_ratio([A, B, C], [A, C, D]) and similarity_ratio([A, B, C], [C, B, D])
    for wrong in ([B, C, D], [B, D, C], [C, A, D]):
        assert similarity_ratio([A, B, C], wrong) is None
    k = 0.42
    A, B, D, C = (x * k for x in (A, B, D, C))
    f = Figure(width_in=2.1, height_in=1.2)
    f.poly([A, B, C])
    f.seg(C, D)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, -0.3))
    f.label(B, "B", direction=(1, -0.3))
    f.label(D, "D", direction=(0, -1))
    f.label(C, "C", direction=(0, 1))
    f.right_angle(C, A, B, size=0.11)
    f.right_angle(D, B, C, size=0.11)
    return f


# ---------------------------------------------------------------- Practice 2: acute triangle ABC, altitude CD = h
@figure("3.13_p2")
def p2() -> Figure:
    h, db = 2.2, 0.4
    ad = h * np.tan(np.radians(75 - np.degrees(np.arctan(db / h))))
    A, D = P((0, 0), (ad, 0))
    B, C = P(ad + db, 0), P(ad, h)
    assert _close(angle_deg(C, A, B), 75)
    # choice A (m∠ACB = m∠B) is false, so the drawing must not make ∠B look like 75°
    assert_distinct([angle_deg(C, A, B), angle_deg(B, A, C), angle_deg(A, B, C)])
    f = Figure(width_in=2.5, height_in=1.55)
    f.poly([A, B, C])
    f.seg(C, D)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, -0.2))
    f.label(B, "B", direction=(1, -0.6))
    f.label(D, "D", direction=(-0.4, -1))
    f.label(C, "C", direction=(0, 1))
    f.right_angle(D, A, C, size=0.15)
    cen = (A + B + C) / 3
    f.side_label(A, C, "b", cen, italic=True, size=11)
    f.side_label(C, B, "a", cen, italic=True, size=11)
    f.text((A + D) / 2 + P(0, 0.2), "$e$", size=11)
    f.text((C + D) / 2 + P(-0.22, -0.4), "$h$", size=11)
    f.text(C + P(-0.4, -0.8), "75°", size=10)
    f.arc(C, A, B, r=0.3)
    y = -0.85
    f.arrow(P(ad / 2 + 0.3, y), P(0, y), layer="given", dashed=False)
    f.arrow(P(ad / 2 + 0.6, y), P(ad + db, y), layer="given", dashed=False)
    f.text(P(ad / 2 + 0.45, y), "$c$", size=11)
    return f


# ---------------------------------------------------------------- Practice 3: AD = 12, DB = 3, altitude h
@figure("3.13_p3")
def p3() -> Figure:
    A, D, B = P((0, 0), (12, 0), (15, 0))
    C = P(12, 6)
    assert _close(angle_deg(C, A, B), 90)
    k = 0.17
    A, D, B, C = (x * k for x in (A, D, B, C))
    f = Figure(width_in=2.6, height_in=1.2)
    f.poly([A, B, C])
    f.seg(C, D)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, -0.3))
    f.label(B, "B", direction=(1, -0.3))
    f.label(D, "D", direction=(-0.3, -1))
    f.label(C, "C", direction=(0, 1))
    f.right_angle(C, A, B, size=0.11)
    f.right_angle(D, A, C, size=0.11)
    f.side_label(A, D, "12", C, size=10)
    f.side_label(D, B, "3", C, size=10)
    f.text((C + D) / 2 + P(-0.14, 0), "$h$", size=11)
    return f


def _par_arrow(f, a, b, at=0.5, n=1, length=0.14):
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = (b - a) / np.linalg.norm(b - a)
    for i in range(n):
        m = a + (b - a) * at + u * i * 0.09
        f.arrow(m - u * length / 2, m + u * length / 2, layer="given", dashed=False)


# ---------------------------------------------------------------- Practice 4: side splitter, A'B' parallel to AB
@figure("3.13_p4")
def p4() -> Figure:
    th = np.arccos(116 / 144)               # angle C so that A'B' = 8 when CA' = 12, CB' = 6
    C = P(0, 0)
    u = np.array([np.cos(th), np.sin(th)])
    A2, B2 = C + 12 * u, P(6, 0)
    A, B = C + 30 * u, P(15, 0)
    assert _close(dist(A2, B2), 8) and _close(dist(A, B), 20)
    assert _close(similarity_ratio([C, A2, B2], [C, A, B]), 2.5)
    assert _close(dist(A2, A), 18) and _close(dist(B2, B), 9)
    k = 0.085
    C, A2, B2, A, B = (x * k for x in (C, A2, B2, A, B))
    f = Figure(width_in=2.2, height_in=1.8)
    f.poly([C, A, B])
    f.seg(A2, B2)
    f.dots([C, A2, B2, A, B])
    f.label(C, "C", direction=(-1, -0.4))
    f.label(A, "A", direction=(0, 1))
    f.label(B, "B", direction=(0.5, -1))
    f.label(A2, "A'", direction=(-0.6, 1))
    f.label(B2, "B'", direction=(0, -1))
    cen = (C + A + B) / 3
    f.side_label(C, A2, "12", cen + P(0, -5), size=10)
    f.side_label(C, B2, "6", cen, size=10)
    f.side_label(B2, A2, "8", C, size=10, offset_pt=8)
    f.side_label(B, A, "20", C, size=10)
    _par_arrow(f, B2, A2)
    _par_arrow(f, B, A)
    return f


# ---------------------------------------------------------------- Practice 7: solve y = x - 2, y = x^2 - x - 2 by graphing
@figure("3.13_p7")
def p7() -> Figure:
    n = 5
    f = Figure(width_in=2.3, height_in=2.3)
    for i in range(-n, n + 1):
        lw = 1.1 if i == 0 else 0.3
        f.seg(P(i, -n), P(i, n), lw=lw)
        f.seg(P(-n, i), P(n, i), lw=lw)
        if i and i % 2 == 0:
            f.text(P(i, -0.45), str(i).replace("-", "−"), size=7.5)
            f.text(P(-0.45, i), str(i).replace("-", "−"), size=7.5)
    f.text(P(n + 0.4, 0), "$x$", size=9)
    f.text(P(0, n + 0.45), "$y$", size=9)
    xs = np.linspace(-2.0, 3.0, 60)
    line = np.c_[np.array([-3, 5]), np.array([-3, 5]) - 2]
    par = np.c_[xs, xs ** 2 - xs - 2]
    assert np.all(np.abs(par[:, 1]) <= n + 1e-9)
    for x0 in (0, 2):
        assert _close(x0 - 2, x0 ** 2 - x0 - 2)
    f.poly(line, closed=False, layer="answer")
    f.poly(par, closed=False, layer="answer")
    f.dots([P(0, -2), P(2, 0)], layer="answer", size=18)
    f.text(P(3.1, -0.9), "(2, 0)", layer="answer", size=8)
    f.text(P(-1.9, -2.0), "(0, −2)", layer="answer", size=8)
    return f

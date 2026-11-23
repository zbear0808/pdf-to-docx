"""Lesson 3.7 figures: corresponding parts of similar triangles. Given layer = student, answer layer = key."""
import numpy as np

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_lengths, dilate, dist, figure, midpoint, needs_reflection, on_ray, reflect, rotate,
    similarity_ratio, translate, vertex_directions,
)


def _tri(f, pts, names, arcs=(1, 2, 3), r=0.22, gap=0.06, layer="given", dirs=None, r1=None):
    """Triangle with dots, vertex labels, and n arcs at each vertex (r1 = radius of single arcs)."""
    pts = np.asarray(pts, float)
    f.poly(pts, layer=layer)
    f.dots(pts, layer=layer)
    for i in range(3):
        if arcs[i]:
            ri = r1 if (r1 and arcs[i] == 1) else r
            f.arc(pts[i], pts[i - 1], pts[(i + 1) % 3], n=arcs[i], r=ri, gap=gap, layer=layer)
    for p, nm, d in zip(pts, names, dirs or vertex_directions(pts)):
        f.label(p, nm, direction=d, layer=layer)


# ---------------------------------------------------------------- warm-up: nested triangles (k = 4)
@figure("3.7_warmup")
def warmup() -> Figure:
    B, A, C = rotate(P((0, 0), (0, 12), (16, 0)), -18)
    D = A + (B - A) * 3 / 12
    E = A + (C - A) * 5 / 20
    assert np.isclose(dist(A, D), 3) and np.isclose(dist(D, B), 9)
    assert np.isclose(dist(A, E), 5) and np.isclose(dist(E, C), 15)
    assert np.isclose(dist(D, E), 4) and np.isclose(dist(B, C), 16)
    assert np.isclose(similarity_ratio([A, D, E], [A, B, C]), 4)
    f = Figure(width_in=2.4, height_in=2.3)
    f.poly([A, B, C])
    f.seg(D, E)
    f.dots([A, B, C, D, E])
    ctr = (A + B + C) / 3
    for p, nm in ((A, "A"), (B, "B"), (C, "C"), (D, "D"), (E, "E")):
        f.label(p, nm, direction=p - ctr if nm not in "DE" else {"D": (-1, -0.2), "E": (0.3, 1)}[nm])
    for a, b, t, c in ((A, D, "3", ctr), (D, B, "9", ctr), (A, E, "5", ctr), (E, C, "15", ctr), (B, C, "16", ctr),
                       (D, E, "4", A)):
        f.side_label(a, b, t, center=c if t != "4" else A, size=10, offset_pt=8)
    return f


# ---------------------------------------------------------------- Problem 1: ABC onto DEF
_ABC = P((0, 0), (1.1, 0.3), (-0.45, 1.6))
_ARCS = (3, 2, 1)                     # A triple, B double, C single (same marks on the image)


def _pair(img, names, dirs_img=None):
    f = Figure(width_in=2.9, height_in=1.9)
    _tri(f, _ABC, "ABC", _ARCS, dirs=[(0, -1), (1, -0.2), (-1, 0.3)], r1=0.32)
    _tri(f, img, names, _ARCS, dirs=dirs_img, r1=0.32)
    return f


def p1_image():
    # dilate from A by 1.5, rotate -25 deg around A, translate (the same map as Problem 1's printed steps)
    return translate(rotate(dilate(_ABC, 1.5, _ABC[0]), -25, _ABC[0]), (2.1, 0.1))


@figure("3.7_p1")
def p1() -> Figure:
    img = p1_image()                  # D, E, F  (A->D, B->E, C->F)
    assert np.isclose(similarity_ratio(_ABC, img), 1.5) and not needs_reflection(_ABC, img)
    D, E = img[0], img[1]
    step1 = translate(_ABC, D - _ABC[0])                 # Step 1: translate A to D
    step2 = rotate(step1, -25, D)                        # Step 2: rotate around D
    assert on_ray(D, E, step2[1])                        # ... until the image of B is on ray DE
    assert np.allclose(dilate(step2, 1.5, D), img)       # Step 3: dilate with center D, k = DE/AB = 1.5
    return _pair(img, "DEF")


def _from_sides(c, a, b):
    """Triangle [U, V, W] with UV = c on the x-axis, VW = a, UW = b."""
    x = (c ** 2 + b ** 2 - a ** 2) / (2 * c)
    return P((0, 0), (c, 0), (x, np.sqrt(b ** 2 - x ** 2)))


# ---------------------------------------------------------------- Problem 2: bowtie, BEC onto DEA
@figure("3.7_bowtie")
def bowtie() -> Figure:
    """Given: both triangles, the matching arcs, sides b, c, e of BEC, and kb on DEA (printed in Problem 2). Key: kc
    and ke on DEA (Problem 2's fills; faded version, Nov 23: DE = kc is a box, so kc is on the answer layer)."""
    E = P((0, 0))[0]
    C, B = P((0.7, 0.95), (0.95, -0.15))
    k = 2.0
    D, A = dilate(rotate([B, C], 180, E), k, E)          # Step 1 rotate 180 about E, Step 2 dilate by k: B->D, C->A
    assert np.allclose(D, -k * B) and np.allclose(A, -k * C)
    assert np.isclose(similarity_ratio([B, E, C], [D, E, A]), k)
    assert np.isclose(angle_deg(A, D, E), angle_deg(C, B, E))
    assert np.isclose(dist(E, A), k * dist(E, C))            # AE = kb
    assert np.isclose(dist(D, E), k * dist(E, B))            # DE = kc
    assert np.isclose(dist(A, D), k * dist(B, C))            # AD = ke
    f = Figure(width_in=2.5, height_in=1.95)
    f.poly([D, E, A])
    f.poly([B, E, C])
    f.dots([A, B, C, D, E])
    for p, nm, d in ((A, "A", (-0.3, -1)), (B, "B", (1, -0.3)), (C, "C", (0.4, 1)), (D, "D", (-1, 0.4)),
                     (E, "E", (0.35, -1))):
        f.label(p, nm, direction=d)
    f.arc(A, D, E, 1, r=0.3)
    f.arc(C, B, E, 1, r=0.2)
    f.arc(D, A, E, 2, r=0.3, gap=0.07)
    f.arc(B, C, E, 2, r=0.2, gap=0.06)
    f.arc(E, D, A, 3, r=0.2, gap=0.05)
    f.arc(E, B, C, 3, r=0.2, gap=0.05)
    cl, cs = (A + D + E) / 3, (B + C + E) / 3
    for a, b, t, c, layer in ((D, E, "kc", cl, "answer"), (E, A, "kb", cl, "given"), (A, D, "ke", cl, "answer"),
                              (E, C, "b", cs, "given"), (E, B, "c", cs, "given"), (C, B, "e", cs, "given")):
        f.side_label(a, b, t, center=c, italic=True, size=10, offset_pt=7, layer=layer)
    return f


# ---------------------------------------------------------------- Problem 3 (the exit ticket until Nov 19, round 2): Lin's triangles (not similar)
@figure("3.7_exit")
def exit_lin() -> Figure:
    B, C, A = _from_sides(7, 10, 4)                      # BC = 7, CA = 10, AB = 4
    D, E, F = translate(_from_sides(8, 13, 19), (14, -1))  # DE = 8, EF = 13, DF = 19
    assert np.isclose(dist(A, C), 10) and np.isclose(dist(D, F), 19) and np.isclose(dist(E, F), 13)
    ratios = [dist(D, E) / dist(A, B), dist(E, F) / dist(B, C), dist(D, F) / dist(A, C)]
    assert not np.allclose(ratios, ratios[0])            # 2, 1.857..., 1.9
    assert_lengths([(A, B, 4), (B, C, 7), (A, C, 10), (D, E, 8), (E, F, 13), (D, F, 19)])
    f = Figure(width_in=3.4, height_in=1.9)
    for tri, nm in (([A, B, C], "ABC"), ([D, E, F], "DEF")):
        _tri(f, tri, nm, (0, 0, 0))
    for a, b, t, c in ((A, B, "4", C), (B, C, "7", A), (A, C, "10", B), (D, E, "8", F), (E, F, "13", D),
                       (D, F, "19", E)):
        f.side_label(a, b, t, center=c, size=10)
    return f


# ---------------------------------------------------------------- practice
def _rhombus(s, acute, start=(0, 0)):
    """Vertices [U, V, W, X]: UV = s along +x, acute angle at U."""
    u = np.asarray(start, float)
    v = u + (s, 0)
    d = s * np.array([np.cos(np.radians(acute)), -np.sin(np.radians(acute))])
    return np.array([u, v, v + d, u + d])


def _para(a, b, acute, start=(0, 0), turn=0.0):
    """Parallelogram [U, V, W, X]: UV = a along +x (then turned), UX = b, acute angle at U."""
    u = np.asarray(start, float)
    pts = np.array([(0, 0), (a, 0), (a + b * np.cos(np.radians(acute)), -b * np.sin(np.radians(acute))),
                    (b * np.cos(np.radians(acute)), -b * np.sin(np.radians(acute)))])
    return rotate(pts, turn) + u


def _label_quad(f, q, sides, acute_txt, obtuse_txt, layer="given", size=9):
    c = q.mean(0)
    for i, t in enumerate(sides):
        if t:
            f.side_label(q[i], q[(i + 1) % 4], t, center=c, size=size, layer=layer, offset_pt=7)
    f.angle_label(q[0], q[1], q[3], acute_txt, layer=layer, size=size - 1)
    f.angle_label(q[1], q[0], q[2], obtuse_txt, layer=layer, size=size - 1)
    f.dots(q, layer=layer, size=8)


@figure("3.7_prac_rhombus")
def prac_rhombus() -> Figure:
    big = _rhombus(12, 30)
    small = _rhombus(9, 30, start=(24.5, 0))             # sample answer: k = 3/4
    assert np.isclose(similarity_ratio(big, small), 0.75)
    for q in (big, small):
        assert np.isclose(angle_deg(q[0], q[1], q[3]), 30) and np.isclose(angle_deg(q[1], q[0], q[2]), 150)
    assert_lengths([(big[0], big[1], 12), (big[1], big[2], 12), (small[0], small[1], 9), (small[1], small[2], 9)])
    f = Figure(width_in=3.2, height_in=1.0)
    f.poly(big)
    _label_quad(f, big, ("12", "12", "12", "12"), r"30$^\circ$", r"150$^\circ$")
    f.poly(small, layer="answer")
    _label_quad(f, small, ("9", "9", "9", "9"), r"30$^\circ$", r"150$^\circ$", layer="answer")
    return f


@figure("3.7_prac_aed")
def prac_aed() -> Figure:
    A, C, B = _from_sides(6, 4, 8)                       # AC = 6, CB = 4, AB = 8
    A, C, B = rotate([A, C, B], 38)
    D = dilate(C, 0.5, A)[0]
    E = reflect(dilate(B, 0.5, A), A, C)[0]              # dilate from A by 1/2, reflect across line AC
    assert np.isclose(similarity_ratio([A, B, C], [A, E, D]), 0.5) and needs_reflection([A, B, C], [A, E, D])
    assert np.isclose(dist(A, E), 4) and np.isclose(dist(E, D), 2) and np.isclose(dist(A, D), 3)
    f = Figure(width_in=1.7, height_in=2.2)
    f.poly([A, B, C])
    f.poly([A, D, E])
    f.dots([A, B, C, D, E], size=10)
    for p, nm, d in ((A, "A", (-1, -0.5)), (B, "B", (0, 1)), (C, "C", (1, 0.3)), (D, "D", (-0.6, 1)),
                     (E, "E", (1, -0.3))):
        f.label(p, nm, direction=d)
    for a, b, t, c in ((A, B, "8", C), (B, C, "4", A), (D, E, "2", A), (A, E, "4", D), (A, D, "3", B)):
        f.side_label(a, b, t, center=c, size=9, offset_pt=7)
    return f


@figure("3.7_prac_paras")
def prac_paras() -> Figure:
    shapes = {
        "P": (_para(5, 5, 50, start=(6, 7.5)), ("5", "5", "5", "5")),
        "A": (_para(5, 5, 50, start=(0, 0)), ("5", "5", "5", "5")),
        "B": (_para(4, 4, 50, start=(13, -1.2), turn=20), ("4", "4", "4", "4")),
        "C": (_para(5, 5, 45, start=(0, -7.5)), ("5", "5", "5", "5")),
        "D": (_para(4, 6, 50, start=(12, -7.5)), ("4", "6", "4", "6")),
    }
    P0 = shapes["P"][0]
    similar = {k: similarity_ratio(P0, q) is not None for k, (q, _) in shapes.items()}
    assert similar == {"P": True, "A": True, "B": True, "C": False, "D": False}
    assert np.isclose(similarity_ratio(P0, shapes["B"][0]), 0.8)
    assert_lengths([(q[i], q[(i + 1) % 4], float(s[i])) for q, s in shapes.values() for i in range(4)])
    f = Figure(width_in=3.0, height_in=3.1)
    for k, (q, sides) in shapes.items():
        acute = angle_deg(q[0], q[1], q[3])
        f.poly(q)
        _label_quad(f, q, sides, f"{acute:.0f}" + r"$^\circ$", f"{180 - acute:.0f}" + r"$^\circ$")
        if k == "P":
            f.text(q.mean(0) + (0, 3.9), "Parallelogram P", size=10)
        else:
            f.text((q[:, 0].min() - 1.3, q[:, 1].max()), f"{k}.", size=10)
    return f


@figure("3.7_prac_midseg")
def prac_midseg() -> Figure:
    A, C, B = rotate(_from_sides(4, 8, 6), 30)           # AC = 4, CB = 8, BA = 6
    D, E, F = midpoint(A, B), midpoint(B, C), midpoint(A, C)
    assert np.isclose(dist(D, E), 2) and np.isclose(dist(E, F), 3) and np.isclose(dist(D, F), 4)
    assert np.isclose(dist(A, B) + dist(B, C) + dist(A, C), 18)
    f = Figure(width_in=2.0, height_in=1.9)
    f.poly([A, B, C])
    f.poly([D, E, F])
    f.dots([A, B, C, D, E, F], size=10)
    ctr = (A + B + C) / 3
    for p, nm in ((A, "A"), (B, "B"), (C, "C"), (D, "D"), (E, "E"), (F, "F")):
        f.label(p, nm, direction=p - ctr)
    m = (D + E + F) / 3
    for a, b, t in ((D, E, "2"), (E, F, "3"), (D, F, "4")):
        f.side_label(a, b, t, center=m, size=9, offset_pt=7)
    return f

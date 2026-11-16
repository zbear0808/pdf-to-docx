"""Figures for lesson "2.9" (lessons/2.9.yaml): Side-Side-Side triangle congruence.
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Coordinates come from the source page renders (pixels / 50, y flipped) so the shapes match the teacher's notes.
"""
import numpy as np
from matplotlib.patches import Circle

from lesson_builder.figures import (
    Figure, P, angle_deg, dist, figure, fit_rigid, is_rigid_image, midpoint, needs_reflection, reflect, rotate,
    translate,
)
from lesson_builder.figures.coordinate import axes, plot_line

S = '2.9'


def _px(*pts):
    """Source pixel coordinates (y down) to data units (y up)."""
    return np.array([(x / 50.0, -y / 50.0) for x, y in pts])


def _kite(W, Y, X):
    """Kite with diagonal WY as its line of symmetry: Z is the reflection of X across WY."""
    Z = reflect([X], W, Y)[0]
    assert np.isclose(dist(W, X), dist(W, Z)) and np.isclose(dist(Y, X), dist(Y, Z))
    return W, X, Y, Z


def _circle(f, center, r):
    c = np.asarray(center, float)
    f.custom(lambda ax, col: ax.add_patch(Circle(tuple(c), r, fill=False, color=col, lw=1.1)),
             extent=[tuple(c - r), tuple(c + r)])


def _ray(a, b, past):
    """Point `past` units beyond b on ray ab."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    return b + past * (b - a) / np.linalg.norm(b - a)


# ------------------------------------------------------------------ warm-up: practice #1 kite
W1, X1, Y1, Z1 = _kite(*_px((97, 284), (205, 250), (110, 222)))


@figure(f"{S}_warmup")
def warmup() -> Figure:
    """Kite WXYZ; the key draws diagonal WY (it splits the kite into two congruent triangles, SSS)."""
    f = Figure(width_in=1.9, height_in=1.9)
    f.poly([W1, X1, Y1, Z1])
    f.dots([W1, X1, Y1, Z1])
    f.label_poly([W1, X1, Y1, Z1], "WXYZ")
    f.ticks(W1, X1, 1)
    f.ticks(W1, Z1, 1)
    f.ticks(X1, Y1, 2)
    f.ticks(Z1, Y1, 2)
    f.seg(W1, Y1, layer="answer")
    return f


# ------------------------------------------------------------------ Activity 2.9.2: STU and GHJ
STU = _px((60, 293), (157, 180), (87, 183))
GHJ = fit_rigid(STU, _px((199, 256), (338, 206), (309, 268)))
assert is_rigid_image(STU, GHJ)
assert needs_reflection(STU, GHJ), "the source pair has opposite orientation, so Step 3 (reflect) is needed"
S_, T_, U_ = STU
G, H, J = GHJ

# Steps 1-2: translate S to G, rotate around G until T' is on ray GH. ST = GH, so T' lands on H.
_img = translate(STU, G - S_)
_turn = np.degrees(np.arctan2(*(H - G)[::-1]) - np.arctan2(*(_img[1] - G)[::-1]))
_img = rotate(_img, _turn, about=G)
assert np.allclose(_img[0], G) and np.allclose(_img[1], H)
U2 = _img[2]
assert np.allclose(U2, reflect([J], G, H)[0]), "after Steps 1-2, U'' is the mirror image of J across GH"


@figure(f"{S}_label")
def label_pair() -> Figure:
    """Two triangles as in the notes; the key adds the tick marks for ST = GH, TU = HJ, SU = GJ."""
    f = Figure(width_in=3.0, height_in=1.55)
    for tri, names in ((STU, "STU"), (GHJ, "GHJ")):
        f.poly(tri)
        f.dots(tri)
        f.label_poly(tri, names)
    for n, (a, b, c, d) in enumerate(((S_, T_, G, H), (T_, U_, H, J), (S_, U_, G, J)), start=1):
        f.ticks(a, b, n, layer="answer")
        f.ticks(c, d, n, layer="answer")
    return f


@figure(f"{S}_proof")
def proof() -> Figure:
    """After Steps 1-2: G, H, J and the image U'' of U on the other side of GH (source image4)."""
    f = Figure(width_in=2.2, height_in=1.9)
    f.poly([G, U2, H, J])
    f.seg(G, H)
    f.seg(U2, J, dashed=True, lw=0.9)
    f.dots([G, U2, H, J])
    f.label(G, "G", direction=(-1, -0.3))
    f.label(U2, "U''", direction=(0, 1))
    f.label(H, "H", direction=(1, 0.3))
    f.label(J, "J", direction=(0.3, -1))
    f.ticks(G, U2, 1)
    f.ticks(G, J, 1)
    f.ticks(H, U2, 2)
    f.ticks(H, J, 2)
    return f


# ------------------------------------------------------------------ Cool-down 2: SSS, SAS, ASA, or none
def _panel_a(f, o):
    A = o + np.array((0.0, 0.0))
    C = A + np.array((1.0, 0.0))
    B = A + np.array((np.cos(np.radians(62)), np.sin(np.radians(62))))
    D = midpoint(B, C)
    assert np.isclose(dist(A, B), dist(A, C))
    _circle(f, A, 1.0)
    f.seg(A, _ray(A, B, 0.35))
    f.seg(A, _ray(A, C, 0.35))
    f.seg(A, _ray(A, D, 0.55))
    f.seg(B, C)
    f.ticks(B, D, 1, size=0.09)
    f.ticks(D, C, 1, size=0.09)
    f.dots([A, B, C, D])
    f.label(A, "A", direction=(-1, 0))
    f.label(B, "B", direction=(-1, 0.6))
    f.label(C, "C", direction=(0.4, -1))
    f.label(D, "D", direction=(-1, 0.2))
    f.text(o + np.array((0.1, 1.45)), r"a.  $\Delta ABD \cong \Delta ACD$")


def _panel_b(f, o):
    E = o + np.array((-1.0, -0.75))
    H = E + np.array((1.9, 1.0))
    jh = 0.68
    ej = np.sqrt(dist(E, H) ** 2 - jh ** 2)
    u = (H - E) / dist(E, H)
    nrm = np.array((-u[1], u[0]))
    t = np.arcsin(jh / dist(E, H))
    J = E + ej * (np.cos(t) * u + np.sin(t) * nrm)
    I = reflect([J], E, H)[0]
    assert np.isclose(angle_deg(J, E, H), 90) and np.isclose(angle_deg(I, E, H), 90)
    assert np.isclose(dist(J, H), dist(I, H))
    f.poly([E, J, H, I])
    f.seg(_ray(H, E, 0.45), _ray(E, H, 0.5))
    f.right_angle(J, E, H, size=0.12)
    f.right_angle(I, E, H, size=0.12)
    f.ticks(J, H, 1, size=0.09)
    f.ticks(I, H, 1, size=0.09)
    f.dots([E, J, H, I])
    f.label(E, "E", direction=(-0.4, 1))
    f.label(J, "J", direction=(0, 1))
    f.label(H, "H", direction=(0.3, 1))
    f.label(I, "I", direction=(0.4, -1))
    f.text(o + np.array((0.0, 1.45)), r"b.  $\Delta EJH \cong \Delta EIH$")


def _panel_c(f, o):
    K = o + np.array((0.3, 0.1))
    M = K + np.array((-1.0, 0.0))
    L = K + np.array((np.cos(np.radians(-118)), np.sin(np.radians(-118))))
    N = midpoint(M, L)
    assert np.isclose(angle_deg(K, M, N), angle_deg(K, N, L))
    _circle(f, K, 1.0)
    f.seg(K, _ray(K, M, 0.3))
    f.seg(K, _ray(K, L, 0.3))
    f.seg(K, _ray(K, N, 0.75))
    f.seg(M, L)
    f.arc(K, M, N, 1, r=0.36, ticks=1)
    f.arc(K, N, L, 1, r=0.36, ticks=1)
    f.dots([K, M, L, N])
    f.label(K, "K", direction=(1, 0.4))
    f.label(M, "M", direction=(-0.5, 1))
    f.label(L, "L", direction=(1, -0.4))
    f.label(N, "N", direction=(1, -0.2))
    f.text(o + np.array((0.3, 1.45)), r"c.  $\Delta LKN \cong \Delta MKN$")


@figure(f"{S}_sort")
def sort() -> Figure:
    """Three panels redrawn from the notes' Cool-down 2 (a. SSS, b. none, c. SAS)."""
    f = Figure(width_in=6.6, height_in=2.5)
    _panel_a(f, np.array((0.0, 0.0)))
    _panel_b(f, np.array((3.0, 0.0)))
    _panel_c(f, np.array((6.0, 0.0)))
    return f


# ------------------------------------------------------------------ exit ticket: practice #2 (Mai)
W2, X2, Y2, Z2 = _kite(*_px((800, 180), (862, 352), (857, 228)))


@figure(f"{S}_mai")
def mai() -> Figure:
    """Kite WXYZ with diagonal WY, as in practice #2."""
    f = Figure(width_in=1.3, height_in=2.0)
    f.poly([W2, X2, Y2, Z2])
    f.seg(W2, Y2)
    f.dots([W2, X2, Y2, Z2])
    f.label_poly([W2, X2, Y2, Z2], "WXYZ")
    f.ticks(W2, Z2, 1)
    f.ticks(W2, X2, 1)
    f.ticks(Z2, Y2, 2)
    f.ticks(X2, Y2, 2)
    return f


# ------------------------------------------------------------------ practice: graph 3x + 2y = 6
@figure(f"{S}_pr_graph")
def pr_graph() -> Figure:
    """Grid from -5 to 5; the key draws y = -1.5x + 3 through (0, 3) and (2, 0)."""
    m, b = -1.5, 3.0
    assert np.isclose(3 * 0 + 2 * b, 6) and np.isclose(3 * 2 + 2 * (m * 2 + b), 6)
    f = Figure(width_in=3.0, height_in=3.0)
    axes(f, -5, 5, -5, 5)
    # starts at x = -0.5 so the red arrow stays clear of the y-axis number 4 (the arrowheads mean the line goes on)
    plot_line(f, m, b, x0=-0.5, layer="answer")
    f.dots([(0, 3), (2, 0)], layer="answer")
    return f


# ------------------------------------------------------------------ practice proofs (diagrams from the source)
@figure(f"{S}_pr_sas")
def pr_sas() -> Figure:
    """Practice 4: triangles ABC and DEF (DEF is a translation of ABC), marks for AB = DE, angle A = D, AC = DF."""
    abc = _px((290, 57), (357, 32), (357, 180))
    def_ = translate(abc, _px((400, 56))[0] - abc[0])
    assert is_rigid_image(abc, def_)
    f = Figure(width_in=1.9, height_in=1.7)
    for tri, names in ((abc, "ABC"), (def_, "DEF")):
        a, b, c = tri
        f.poly(tri)
        f.label_poly(tri, names)
        f.ticks(a, b, 1)
        f.ticks(a, c, 2)
        f.arc(a, b, c, 1, r=0.3)
    return f


@figure(f"{S}_pr_bisect")
def pr_bisect() -> Figure:
    """Practice 5: quadrilateral KQAB with diagonal QB; K is the mirror image of A across QB, so QK = QA."""
    Q, B, A = _px((405, 52), (347, 190), (455, 128))
    K = reflect([A], Q, B)[0]
    assert np.isclose(dist(Q, K), dist(Q, A)) and np.isclose(angle_deg(Q, K, B), angle_deg(Q, A, B))
    f = Figure(width_in=1.5, height_in=1.6)
    f.poly([K, Q, A, B])
    f.seg(Q, B)
    f.dots([K, Q, A, B])
    f.label_poly([K, Q, A, B], "KQAB")
    return f

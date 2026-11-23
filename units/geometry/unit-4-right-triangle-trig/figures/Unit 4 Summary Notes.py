"""Figures for reference "Unit 4 Summary Notes" (assessments/Unit 4 Summary Notes.yaml).
Completed reference: every figure is black (given layer only), all values printed.
Loop: uv run lesson-builder figs <unit> -l "Unit 4 Summary Notes" (0 errors, no label warnings).
"""
import math

from lesson_builder.figures import Figure, P, angle_deg, dist, figure

S = 'Unit 4 Summary Notes'


def _close(a, b, tol):
    assert abs(a - b) < tol, (a, b)


@figure(f"{S}_pythag")
def pythag() -> Figure:
    R, X, Y = P((0, 0), (4, 0), (0, 3))
    _close(angle_deg(R, X, Y), 90, 1e-9)
    _close(dist(X, Y), 5, 1e-9)
    f = Figure(width_in=2.8, height_in=2.1)
    f.poly([R, X, Y])
    f.right_angle(R, X, Y, size=0.35)
    f.side_label(R, X, "leg $a$", center=Y, size=11)
    f.side_label(R, Y, "leg\n$b$", center=X, size=11)
    f.side_label(X, Y, "hypotenuse $c$", center=R, size=11, offset_pt=24)
    return f


@figure(f"{S}_4.1")
def ramp() -> Figure:
    rise, run = 4 * 8, 12 * 4 * 8
    _close(rise, 32, 1e-9)
    _close(run, 384, 1e-9)
    hyp = math.hypot(rise, run)
    _close(hyp, 385.33, 0.01)
    k = 5  # vertical stretch only
    A, C, B = P((0, 0), (run, 0), (run, rise * k))
    f = Figure(width_in=4.4, height_in=2.2)
    f.poly([A, C, B])
    f.right_angle(C, A, B, size=14)
    step_w = 16
    pts = [B]
    for i in range(4):
        y = rise * k - (i + 1) * 8 * k
        x = run + i * step_w
        pts += [(x + step_w, (rise - i * 8) * k), (x + step_w, y)]
    f.poly(P(*pts), closed=False)
    f.side_label(A, C, "run = 384 in", center=B, size=11)
    f.side_label(C, B, "rise\n32 in", center=(run + 200, rise * k / 2), size=11)
    f.side_label(A, B, "ramp ≈ 385.3 in", center=C, size=11, offset_pt=20)
    f.angle_label(A, C, B, r"$\approx 4.8^\circ$", dist=110, size=11)
    f.text((run + 40, rise * k + 30), "4 steps, 8 in each", size=10)
    f.text((run / 2, -80), "(not drawn to scale)", size=10)
    return f


@figure(f"{S}_4.4")
def sides() -> Figure:
    Z, X, Y = P((0, 0), (5, 0), (0, 3.5))
    _close(angle_deg(Z, X, Y), 90, 1e-9)
    f = Figure(width_in=3.6, height_in=2.4)
    f.poly([Z, X, Y])
    f.right_angle(Z, X, Y, size=0.35)
    f.label_poly([Z, X, Y], "ZXY")
    f.side_label(X, Y, "hypotenuse", center=Z, size=11, offset_pt=14)
    f.side_label(Z, Y, "opposite ∠X\nadjacent ∠Y", center=X, size=11, offset_pt=36)
    f.side_label(Z, X, "adjacent ∠X, opposite ∠Y", center=Y, size=11)
    return f


@figure(f"{S}_4.5")
def triple() -> Figure:
    R, X, Y = P((0, 0), (56, 0), (0, 33))
    _close(dist(X, Y), 65, 0.01)
    _close(angle_deg(X, R, Y), 30.51, 0.05)
    f = Figure(width_in=2.6, height_in=1.6)
    f.poly([R, X, Y])
    f.right_angle(R, X, Y, size=4)
    f.side_label(R, X, "56", center=Y)
    f.side_label(R, Y, "33", center=X)
    f.side_label(X, Y, "65", center=R)
    f.angle_label(X, R, Y, r"$\approx 30.5^\circ$", dist=14)
    f.angle_label(Y, R, X, r"$\approx 59.5^\circ$", dist=9)
    return f


@figure(f"{S}_4.6")
def ratios() -> Figure:
    """Right angle at C; a = BC = 10 is opposite the 41 degree angle at A; c = AB = x = 10 / sin 41 (divide).
    Nov 19: was c = 18 given and a = x = 18 sin 41 (multiply); 4.6's framing question is the unknown on the bottom."""
    run = 10 / math.tan(math.radians(41))
    A, C, B = P((0, 0), (run, 0), (run, 10))
    _close(dist(C, B), 10, 1e-9)
    _close(angle_deg(A, C, B), 41, 1e-6)
    _close(angle_deg(C, A, B), 90, 1e-6)
    _close(dist(A, B), 10 / math.sin(math.radians(41)), 1e-9)
    _close(dist(A, B), 15.24, 0.01)
    f = Figure(width_in=2.4, height_in=2.0)
    f.poly([A, C, B])
    f.right_angle(C, A, B, size=0.85)
    f.label_poly([A, C, B], "ACB")
    f.side_label(A, B, "$c$ = $x$", center=C)
    f.side_label(C, B, "$a$ = 10", center=A, offset_pt=20)
    f.side_label(A, C, "$b$", center=B)
    f.angle_label(A, C, B, r"$41^\circ$", dist=2.8)
    return f


@figure(f"{S}_4.7")
def statue() -> Figure:
    boat, base = P((0, 0), (82, 0))
    top = (82, 82 * math.tan(math.radians(75)))
    _close(top[1], 306.03, 0.01)
    _close(angle_deg(boat, base, top), 75, 0.1)
    f = Figure(width_in=1.6, height_in=3.8)
    f.poly(P(boat, base, top))
    f.right_angle(base, boat, top, size=10)
    f.side_label(boat, base, "82 ft", center=top, offset_pt=22)
    f.side_label(base, top, "$h$", center=boat, italic=False)
    f.angle_label(boat, base, top, r"$75^\circ$", dist=30)
    f.label(boat, "boat", direction=(-1, 0.3), italic=False)
    f.label(top, "statue top", direction=(1, 0), italic=False)
    return f


@figure(f"{S}_4.10")
def inverse() -> Figure:
    A, C, B = P((0, 0), (13, 0), (0, 10))
    _close(dist(B, C), 16.401, 0.01)
    _close(angle_deg(C, A, B), 37.57, 0.05)
    f = Figure(width_in=2.5, height_in=1.9)
    f.poly([A, C, B])
    f.right_angle(A, C, B, size=0.9)
    f.label_poly([A, C, B], "ACB")
    f.side_label(A, C, "13", center=B)
    f.side_label(A, B, "10", center=C)
    f.side_label(B, C, "?", center=A)
    return f

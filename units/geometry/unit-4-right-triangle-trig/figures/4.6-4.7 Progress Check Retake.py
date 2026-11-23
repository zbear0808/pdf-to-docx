"""Figures for assessment "4.6-4.7 Progress Check Retake" (assessments/4.6-4.7 Progress Check Retake.yaml). Name each figure f"{S}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Loop: uv run lesson-builder figs <unit> -l "4.6-4.7 Progress Check Retake" (0 errors, no label warnings).
"""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, dist, figure

S = '4.6-4.7 Progress Check Retake'


@figure(f"{S}_1")
def q1() -> Figure:
    """Key only: triangle XYZ with the right angle at X; XZ is opposite angle Y."""
    X, Y, Z = P((0, 0), (4, 0), (0, 3))
    assert np.isclose(angle_deg(X, Y, Z), 90)
    f = Figure(width_in=2.2, height_in=1.8)

    def border(ax, color):
        import matplotlib.patches as mp
        ax.add_patch(mp.Rectangle((-3.8, -0.7), 8.6, 4.4, fill=False, ec="0.6", lw=0.5))

    f.custom(border, extent=[(-3.8, -0.7), (4.8, 3.7)])
    f.poly([X, Y, Z], layer="answer")
    f.seg(X, Z, layer="answer", lw=3)
    f.right_angle(X, Y, Z, size=0.35, layer="answer")
    f.label_poly([X, Y, Z], "XYZ", layer="answer")
    f.text((-1.8, 1.5), r"opposite $\angle Y$", layer="answer", size=9)
    return f


@figure(f"{S}_2")
def q2() -> Figure:
    """Triangle MNP, right angle at P (bottom left), hypotenuse MN = 9.5, 51 deg marked at M (the top vertex),
    x = PN (the bottom leg). x is opposite M, so the key is sin(51) = x / 9.5. Nov 20 audit fix: the angle moved
    from N (39 deg, with x on the vertical leg MP) to M, so "the vertical side is opposite" picks a distractor here
    as it does on form A. Nov 19: replaced triangle GHJ (32 deg, HJ = 8.5, x = GH), the 4.7 practice 4 triangle."""
    th = np.radians(39)                       # angle at N; the marked angle at M is 90 - 39 = 51
    P_, N, M = P((0, 0), (9.5 * np.cos(th), 0), (0, 9.5 * np.sin(th)))
    assert np.isclose(dist(N, M), 9.5)
    assert np.isclose(angle_deg(P_, N, M), 90)
    assert abs(angle_deg(M, N, P_) - 51) < 1e-6
    assert np.isclose(dist(P_, N) / dist(N, M), np.sin(np.radians(51)))   # x / 9.5 = sin 51 (x opposite M)
    assert np.isclose(dist(P_, M) / dist(N, M), np.cos(np.radians(51)))   # the vertical leg MP is adjacent to M
    f = Figure(width_in=2.4, height_in=1.9)
    f.poly([P_, N, M])
    f.right_angle(P_, N, M, size=0.5)
    f.label_poly([P_, N, M], "PNM")
    f.side_label(N, M, "9.5", center=P_)
    f.side_label(P_, N, "$x$", center=M)
    f.angle_label(M, N, P_, r"$51^\circ$", dist=1.5)
    return f


@figure(f"{S}_3")
def q3() -> Figure:
    """Triangle JKL, right angle at L, 67 deg at K, hypotenuse KJ = 15."""
    L, K, J = P((0, 0), (0, 5.861), (13.808, 0))
    assert abs(dist(K, J) - 15) < 0.01
    assert abs(angle_deg(K, L, J) - 67) < 0.1
    assert np.isclose(angle_deg(L, K, J), 90)
    f = Figure(width_in=2.6, height_in=1.5)
    f.poly([L, K, J])
    f.right_angle(L, K, J, size=0.7)
    f.label_poly([L, K, J], "LKJ")
    f.side_label(K, J, "15", center=L)
    f.angle_label(K, L, J, r"$67^\circ$", dist=1.6)
    f.angle_label(J, K, L, r"$23^\circ$", dist=3.4, layer="answer")
    f.side_label(L, J, r"$\approx 13.8$", center=K, layer="answer")
    f.side_label(K, L, r"$\approx 5.9$", center=J, layer="answer")
    return f


@figure(f"{S}_4")
def q4() -> Figure:
    """Tree ST, Kiran at U, TU = 30 ft, angle of elevation 63 deg at U, ST = h."""
    T, U, S_ = P((0, 0), (30, 0), (0, 58.88))
    assert np.isclose(dist(T, U), 30)
    assert abs(angle_deg(U, S_, T) - 63) < 0.1
    assert np.isclose(angle_deg(T, S_, U), 90)
    f = Figure(width_in=1.9, height_in=2.4)

    def tree(ax, color):
        import matplotlib.patches as mp
        ax.add_patch(mp.Rectangle((-1.2, 0), 2.4, 44, fill=False, ec=color, lw=1))
        ax.add_patch(mp.Ellipse((0, 49), 16, 20, fill=False, ec=color, lw=1))

    f.custom(tree, extent=[(-26, -8), (0, 59)])
    f.seg(T, U, lw=1.5)
    f.seg(U, S_, dashed=True)
    f.right_angle(T, U, S_, size=3)
    f.dots([S_, T, U])
    f.label(S_, "S", direction=(-1, 0.3))
    f.label(T, "T", direction=(-1, -1))
    f.label(U, "U", direction=(1, -1))
    f.text((30, -13), "Kiran", size=10)
    f.side_label(T, U, "30 ft", center=S_)
    f.side_label(S_, T, "$h$", center=(-20, 30))
    f.angle_label(U, T, S_, r"$63^\circ$", dist=8)
    f.text((-15, 22), r"$h \approx 59$ ft", layer="answer", size=10)
    return f

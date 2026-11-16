"""Progress Check A. Shared templates; item q3's givens live in its assessment YAML."""
import numpy as np

from lesson_builder.figures import Figure, P, angle_deg, dilate, dilation_task, dist, figure, similarity_ratio
from lesson_builder.figures.comparison import line_family, parallel_names, scaled_rectangles, split_triangle
from lesson_builder.resolve import model_for_figure

S = "3.1-3.5 Progress Check A"


@figure(f"{S}_q1")
def q1() -> Figure:
    f, _ = dilation_task(P((2, 5), (4, 4), (3, 1)), 2, (0, 2), "ABC", grid=(0, 9, 0, 8),
                         width_in=2.6, height_in=2.3, center_dir=(-1, 0.6), overrides={"B": (0.2, 1)})
    return f


@figure(f"{S}_q3")
def q3() -> Figure:
    return scaled_rectangles(model_for_figure(__file__, "q3"))


@figure(f"{S}_q4")
def q4() -> Figure:
    B = P(0, 0)
    bc = np.radians(-22)
    C = 9 * np.array([np.cos(bc), np.sin(bc)])
    c = (18 * np.cos(np.radians(40)) + np.sqrt((18 * np.cos(np.radians(40))) ** 2 - 4 * 45)) / 2
    A = c * np.array([np.cos(bc - np.radians(40)), np.sin(bc - np.radians(40))])
    assert np.isclose(dist(C, A), 6) and np.isclose(angle_deg(B, C, A), 40)
    f, B2, A2 = split_triangle(C, B, A, 2 / 3, ("C", "B", "A", "B'", "A'"),
                               (("6", "3"), ("4", "2")), angle_at=(B, C, A), angle_text=r"$40^\circ$",
                               inside=("W",), angle_dist=1.5)
    assert np.isclose(angle_deg(B2, C, A2), 40)
    return f


@figure(f"{S}_q5")
def q5() -> Figure:
    lines = [("o", (5, 3), -30, 1), (r"\ell", (3.6, 3), 80, 1), ("m", (4.4, 3.6), 38, 1),
             ("n", (6.0, 3.4), 38, 1), ("p", (8.2, 3.2), 38, 1)]
    assert parallel_names(lines, "p") == {"m", "n", "p"}
    return line_family(lines)


@figure(f"{S}_q6")
def q6() -> Figure:
    pts = P((0, 0), (2.2, 0.3), (1.9, 2.0), (0.1, 1.7))
    img = dilate(pts, 2, (-3.5, 1.0))
    assert np.isclose(similarity_ratio(pts, img), 2)
    f = Figure(width_in=2.6, height_in=1.6)
    f.poly(img, fill="#e6e6e6")
    f.poly(pts, fill="#b5b5b5")
    f.dots(np.vstack([pts, img]))
    f.label_poly(pts, "ABCD")
    f.label_poly(img, ["A'", "B'", "C'", "D'"])
    return f

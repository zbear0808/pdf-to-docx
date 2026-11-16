"""Progress Check Retake B. Item q3 uses the same checked data as its prompt and key."""
import numpy as np

from lesson_builder.figures import Figure, P, assert_lengths, dilate, dilation_task, dist, figure, similarity_ratio
from lesson_builder.figures.comparison import line_family, parallel_names, scaled_rectangles, split_triangle
from lesson_builder.resolve import model_for_figure

S = "3.1-3.5 Progress Check Retake B"


@figure(f"{S}_q1")
def q1() -> Figure:
    f, _ = dilation_task(P((3, 9), (9, 6), (6, 3)), 1 / 3, (0, 0), "JKL", grid=(0, 10, 0, 9),
                         width_in=2.6, height_in=2.3, center_name="O", center_dir=(-1, -0.6))
    return f


@figure(f"{S}_q3")
def q3() -> Figure:
    return scaled_rectangles(model_for_figure(__file__, "q3"))


@figure(f"{S}_q4")
def q4() -> Figure:
    Q, R = P(0, 0), P(16, 0)
    x = (144 - 64 + 256) / 32
    P0 = np.array([x, -np.sqrt(144 - x ** 2)])
    assert np.isclose(dist(P0, Q), 12) and np.isclose(dist(P0, R), 8)
    f, Q2, R2 = split_triangle(P0, Q, R, 3 / 4, ("P", "Q", "R", "Q'", "R'"),
                               (("9", "3"), ("6", "2")), size=(2.6, 1.6))
    f.side_label(Q, R, "16", P(P0, Q, R).mean(0))
    assert_lengths([(P0, Q2, 9), (P0, R2, 6), (Q, R, 16)])
    assert np.isclose(dist(Q2, R2), 12)
    return f


@figure(f"{S}_q5")
def q5() -> Figure:
    lines = [("q", (3.0, 6), 115, 1), ("t", (5.5, 6), 115, 1), ("u", (8.0, 6), 115, 1),
             ("r", (5.0, 1.2), 18, -1), ("s", (5.0, 5.0), -10, 1)]
    assert parallel_names(lines, "q") == {"q", "t", "u"}
    return line_family(lines)


@figure(f"{S}_q6")
def q6() -> Figure:
    pts = P((0, 0), (1.4, 0.3), (0.4, 1.1))
    img = dilate(pts, 2, (2.6, 1.6))
    assert np.isclose(similarity_ratio(pts, img), 2)
    f = Figure(width_in=2.0, height_in=1.6)
    f.poly(img, fill="#e6e6e6")
    f.poly(pts, fill="#b5b5b5")
    f.dots(np.vstack([pts, img]))
    f.label_poly(pts, "RST", overrides={"R": (-0.6, 0.8)})
    f.label_poly(img, "XYZ")
    return f

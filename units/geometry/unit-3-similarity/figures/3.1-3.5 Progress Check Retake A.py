"""Progress Check Retake A. Item q3 uses the same checked data as its prompt and key."""
import numpy as np

from lesson_builder.figures import Figure, P, dilate, dilation_task, dist, figure, similarity_ratio
from lesson_builder.figures.comparison import line_family, parallel_names, scaled_rectangles
from lesson_builder.resolve import model_for_figure

S = "3.1-3.5 Progress Check Retake A"


@figure(f"{S}_q1")
def q1() -> Figure:
    f, _ = dilation_task(P((0, 8), (6, 8), (2, 2)), 0.5, (10, 2), "GHK", grid=(0, 10, 1, 9),
                         width_in=2.7, height_in=2.2, center_name="C", center_dir=(1, 0.6))
    return f


@figure(f"{S}_q3")
def q3() -> Figure:
    return scaled_rectangles(model_for_figure(__file__, "q3"))


@figure(f"{S}_q5")
def q5() -> Figure:
    lines = [("j", (1.2, 6), -50, 1), ("k", (3.6, 6), -50, 1), ("m", (6.0, 6), -50, 1),
             (r"\ell", (8.6, 3), 78, 1, (1, 0)), ("n", (5.0, 4.0), 8, -1)]
    assert parallel_names(lines, "m") == {"j", "k", "m"}
    return line_family(lines)


@figure(f"{S}_q6")
def q6() -> Figure:
    pts = P((0, 1.8), (0, 0), (1.5, 0))
    img = dilate(pts, 3, (-2.0, -0.3))
    assert np.isclose(similarity_ratio(pts, img), 3)
    assert dist(img[1], pts[2]) > 2   # E sits clear of C, so their labels can't swap
    f = Figure(width_in=2.6, height_in=2.2)
    for tri, names in ((pts, "ABC"), (img, "DEF")):
        f.poly(tri)
        f.dots(tri)
        f.right_angle(tri[1], tri[0], tri[2], size=0.22 if tri is pts else 0.5)
        f.label_poly(tri, names)
    return f

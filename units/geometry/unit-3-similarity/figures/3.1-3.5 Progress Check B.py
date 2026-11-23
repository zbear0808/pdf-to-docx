"""Progress Check B. Shared templates; item q3's givens live in its assessment YAML."""
import numpy as np

from lesson_builder.figures import Figure, P, dilate, dilation_task, figure, similarity_ratio
from lesson_builder.figures.comparison import line_family, parallel_names, scaled_rectangles
from lesson_builder.resolve import model_for_figure

S = "3.1-3.5 Progress Check B"


@figure(f"{S}_q1")
def q1() -> Figure:
    f, _ = dilation_task(P((10, 4), (6, 2), (6, 4)), 2, (11, 1), "RST", grid=(0, 11, 0, 8),
                         width_in=2.7, height_in=2.0, center_name="Q", center_dir=(1, 0.6))
    return f


@figure(f"{S}_q3")
def q3() -> Figure:
    return scaled_rectangles(model_for_figure(__file__, "q3"))


@figure(f"{S}_q5")
def q5() -> Figure:
    lines = [("a", (1.0, 6), -40, 1), ("c", (3.3, 6), -40, 1), ("d", (5.6, 6), -40, 1),
             ("b", (6.5, 2.5), 64, 1, (1, 0)), ("e", (5.0, 0.6), 8, -1)]
    assert parallel_names(lines, "d") == {"a", "c", "d"}
    return line_family(lines)


@figure(f"{S}_q6")
def q6() -> Figure:
    pts = P((0, 0), (1.6, -0.3), (1.9, 1.2), (0.3, 1.4))
    img = dilate(pts, 3, (3.4, 0.2))
    assert np.isclose(similarity_ratio(pts, img), 3)
    f = Figure(width_in=2.1, height_in=1.8)
    f.poly(img, fill="#e6e6e6")
    f.poly(pts, fill="#b5b5b5")
    f.dots(np.vstack([pts, img]))
    f.label_poly(pts, "EFGH", overrides={"H": (0.4, 1)})
    f.label_poly(img, ["E'", "F'", "G'", "H'"])
    return f

"""Progress Check A. Shared templates; item q3's givens live in its assessment YAML."""
import numpy as np

from lesson_builder.figures import Figure, P, dilate, dilation_task, figure, similarity_ratio
from lesson_builder.figures.comparison import line_family, parallel_names, scaled_rectangles
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


@figure(f"{S}_q5")
def q5() -> Figure:
    lines = [("h", (5, 1.6), 15, -1), ("v", (5, 3.9), 15, -1), ("w", (5, 6.2), 15, -1),
             ("f", (3.0, 3.75), 72, 1), ("z", (7.4, 3.75), -62, 1)]
    assert parallel_names(lines, "w") == {"h", "v", "w"}
    return line_family(lines, box=(10, 7.5), size=(2.6, 1.95))


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

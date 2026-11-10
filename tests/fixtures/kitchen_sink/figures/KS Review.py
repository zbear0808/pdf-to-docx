"""Figures for assessments/KS Review.yaml: one built on the shared helper, one with Figure.custom."""
import numpy as np
from _helpers import labeled_triangle
from matplotlib.patches import Circle

from lesson_builder.figures import Figure, P, angle_deg, figure, triangle_from_angles

S = "KS Review"


@figure("ksr_tri")
def ksr_tri() -> Figure:
    """Item 2: triangle WXZ with angles W = 64 and X = 71 marked, so Z = 45."""
    tri = triangle_from_angles((0, 0), (3, 0), 64, 71)
    assert np.isclose(angle_deg(tri[2], tri[0], tri[1]), 45)
    f = Figure(2.2, 1.8)
    labeled_triangle(f, tri, "WXZ")
    f.angle_label(tri[0], tri[1], tri[2], r"$64^\circ$")
    f.angle_label(tri[1], tri[0], tri[2], r"$71^\circ$")
    return f


@figure("ksr_circle")
def ksr_circle() -> Figure:
    """Item 3: circle O with radius 7 (given) and its image under a dilation by 3 (answer, dashed)."""
    f = Figure(1.2, 1.2, key_frame="union")
    f.custom(lambda ax, c: ax.add_patch(Circle((0, 0), 1, fill=False, edgecolor=c, lw=1.3)),
             extent=[(-1, -1), (1, 1)])
    f.dots(P((0, 0)))
    f.label((0, 0), "O", direction=(-1, -1))
    f.seg((0, 0), (1, 0))
    f.side_label((0, 0), (1, 0), "7", center=(0, -1))
    f.custom(lambda ax, c: ax.add_patch(Circle((0, 0), 3, fill=False, edgecolor=c, lw=1.0, ls="--")),
             layer="answer", extent=[(-3, -3), (3, 3)])
    f.text((0, 2.5), "21", layer="answer")
    return f

"""Figures for lessons/ks.yaml (kitchen-sink fixture). One figure per helper or template the builder has."""
import numpy as np
from _helpers import labeled_triangle
from matplotlib.patches import Circle

from lesson_builder.figures import (
    Figure, P, congruent_pair, dilation_task, figure, rect_pair, reflect, reflection_build, rotation_build,
    side_splitter,
)
from lesson_builder.figures import coordinate as co
from lesson_builder.figures import cs, numberline as nl, stats

S = "ks"


@figure("ks_reflect")
def ks_reflect() -> Figure:
    """Together 1: reflect ABC across line m (image on the answer layer)."""
    f, info = reflection_build(P((0.4, 0.2), (2.0, 0.6), (0.9, 2.0)), (3, -0.4), (3, 2.6), names="ABC",
                               line_name="m", width_in=2.6)
    assert np.allclose(info["image_pts"][0], (5.6, 0.2))
    return f


@figure("ks_rotation")
def ks_rotation() -> Figure:
    """Partner build: rotate ABC 180 degrees around M, the midpoint of AC (key drawing)."""
    return rotation_build(P((0, 0), (1.2, 1.7), (3, 0)), names="ABC", image_name="D", width_in=2.4)


@figure("ks_congruent")
def ks_congruent() -> Figure:
    """Partner 5: ABC and its mirror image DEF, every pair of parts marked."""
    f, info = congruent_pair(P((0, 0), (2, 0), (0.6, 1.4)), "ABC", lambda p: reflect(p, (0, 0), (0, 1)), "DEF",
                             offset=(5.6, 0), width_in=3.0, height_in=1.3)
    assert info["correspondence"] == {"A": "D", "B": "E", "C": "F"} and info["needs_reflection"]
    return f


@figure("ks_coord")
def ks_coord() -> Figure:
    """CYU 1: A(2, 1) and its reflection across the y-axis (answer)."""
    f = Figure(2.2, 2.2)
    co.axes(f, -3, 3, -3, 3)
    co.plot_points(f, [(2, 1)], names=["A"])
    co.plot_points(f, [(-2, 1)], names=["A'"], layer="answer", directions=[(-0.7, 1)])
    return f


@figure("ks_numberline")
def ks_numberline() -> Figure:
    """Extension: x > 1 (open dot and ray on the answer layer)."""
    f = Figure(2.8, 0.6)
    nl.number_line(f, -3, 4)
    nl.ray(f, 1, "right", open=True, layer="answer")
    return f


@figure("ks_dilate")
def ks_dilate() -> Figure:
    """Practice 1: dilate ABC from the origin by 2 on a grid."""
    f, info = dilation_task(P((1, 1), (2, 1), (1, 2)), 2, (0, 0), names="ABC", grid=(0, 5, 0, 5), width_in=1.9,
                            center_name="O", center_dir=(-1, -1))
    assert np.allclose(info["image_pts"], P((2, 2), (4, 2), (2, 4)))
    return f


@figure("ks_split")
def ks_split() -> Figure:
    """Practice 2: DE parallel to BC with AD = 3, DB = 3, AE = 4."""
    f, info = side_splitter(P((0, 2.2), (-1.4, 0), (2.4, 0)), 0.5, names="ABC", split_names="DE",
                            seg_labels=("3", "3", "4", None), marks=True, width_in=2.0)
    assert info["k"] == 2
    return f


@figure("ks_rects")
def ks_rects() -> Figure:
    """Practice 3: rectangle M and its dilation N by 1.5."""
    f, info = rect_pair(2, 1, 1.5, names=("M", "N"), width_in=2.4)
    assert info["k"] == 1.5
    return f


@figure("ks_dotplot")
def ks_dotplot() -> Figure:
    """Practice 4: quiz scores dot plot."""
    f = Figure(2.6, 1.3)
    counts = stats.dotplot(f, [2, 3, 3, 4, 4, 4, 5, 6], 0, 6)
    assert counts[4] == 3
    return f


@figure("ks_array")
def ks_array() -> Figure:
    """Practice 5: int array with index 2 filled in on the key."""
    f = Figure(2.0, 0.8)
    cs.array_boxes(f, [4, 7, None, 9], name="nums", answer={2: 5})
    return f


@figure("ks_union")
def ks_union() -> Figure:
    """Practice 6: translate ABC 3 units right. key_frame="union": the image reaches past the given frame."""
    f = Figure(1.4, 1.2, key_frame="union")
    tri = P((0, 0), (1.2, 0), (0.3, 1))
    labeled_triangle(f, tri, "ABC")
    labeled_triangle(f, tri + (3, 0), ["A'", "B'", "C'"], layer="answer")
    return f


@figure("ks_custom")
def ks_custom() -> Figure:
    """Practice 7: circle with center O (custom given drawing) and a radius on the answer layer."""
    f = Figure(2.0, 2.0)
    f.custom(lambda ax, c: ax.add_patch(Circle((0, 0), 1, fill=False, edgecolor=c, lw=1.3)),
             extent=[(-1, -1), (1, 1)])
    f.dots([(0, 0)])
    f.label((0, 0), "O", direction=(-1, -1))
    f.custom(lambda ax, c: ax.plot([0, 0.6], [0, 0.8], color=c, lw=1.3), layer="answer")
    return f

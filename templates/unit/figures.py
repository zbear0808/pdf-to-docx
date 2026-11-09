"""Template figures. Each @figure function draws the given layer (student copy) and, optionally, an answer
layer (red, key only) on the same Figure, so the two images always line up."""
from lesson_builder.figures import Figure, P, congruent_pair, figure, reflect, rotate, rotation_build


@figure("warmup_fig")
def warmup_fig() -> Figure:
    A, B, C = P((0, 0), (2.4, 0.4), (0.8, 1.8))
    f = Figure(width_in=2.4, height_in=1.8)
    f.poly([A, B, C])
    f.dots([A, B, C])
    f.label_poly([A, B, C], "ABC")
    return f


@figure("pair_fig")
def pair_fig() -> Figure:
    abc = P((0, 0), (2.6, 0.5), (0.7, 1.9))
    fig, _info = congruent_pair(abc, "ABC", lambda p: rotate(reflect(p, (0, 0), (0, 1)), 75), "DEF",
                                offset=(6.4, -0.9), marks=True)
    return fig


@figure("build_fig")
def build_fig() -> Figure:
    return rotation_build(P((0, 0), (1.1, 1.7), (4.0, 0)), names="ABC", image_name="D", width_in=2.8)

"""Figures for assessments/KS Test A.yaml."""
import numpy as np

from lesson_builder.figures import Figure, P, assert_lengths, dilation_task, figure, side_splitter

S = "KS Test A"


@figure("ksa_dilate")
def ksa_dilate() -> Figure:
    """Item 5: dilate JKL from P by 2 (image on the answer layer)."""
    f, info = dilation_task(P((1, 1), (2, 1), (2, 2)), 2, (0, 0), names="JKL", grid=(0, 4, 0, 4), width_in=1.8,
                            center_name="P", center_dir=(-1, -1))
    assert np.allclose(info["image_pts"], P((2, 2), (4, 2), (4, 4)))
    return f


@figure("ksa_split")
def ksa_split() -> Figure:
    """Item 6: XY parallel to GH with FX = 8, XG = 4, FY = 10, so YH = 5."""
    tri = P((0.4, 2.4), (-1.5, 0), (2.4, 0))
    f, info = side_splitter(tri, 8 / 12, names="FGH", split_names="XY", seg_labels=("8", "4", "10", None),
                            marks=True, width_in=2.0)
    F, (X, Y) = tri[0], info["split_pts"]
    assert_lengths([(F, X, 8), (X, tri[1], 4)])
    assert np.isclose(10 * 4 / 8, 5)
    return f

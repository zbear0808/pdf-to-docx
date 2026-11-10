"""Figures for assessments/KS Test B.yaml (parallel to Form A: new letters, numbers, and keys)."""
import numpy as np

from lesson_builder.figures import Figure, P, assert_lengths, dilation_task, figure, side_splitter

S = "KS Test B"


@figure("ksb_dilate")
def ksb_dilate() -> Figure:
    """Item 5: dilate TUV from Q by 1/2 (image on the answer layer)."""
    f, info = dilation_task(P((4, 2), (4, 4), (2, 4)), 0.5, (0, 0), names="TUV", grid=(0, 4, 0, 4), width_in=1.8,
                            center_name="Q", center_dir=(-1, -1))
    assert np.allclose(info["image_pts"], P((2, 1), (2, 2), (1, 2)))
    return f


@figure("ksb_split")
def ksb_split() -> Figure:
    """Item 6: MN parallel to ST with RM = 9, MS = 6, RN = 12, so NT = 8."""
    tri = P((0.2, 2.4), (-1.6, 0), (2.3, 0))
    f, info = side_splitter(tri, 9 / 15, names="RST", split_names="MN", seg_labels=("9", "6", "12", None),
                            marks=True, width_in=2.0)
    R, (M, N) = tri[0], info["split_pts"]
    assert_lengths([(R, M, 9), (M, tri[1], 6)])
    assert np.isclose(12 * 6 / 9, 8)
    return f

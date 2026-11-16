"""3.6 Progress Check A: right triangles FED (small) and CBA (large). FED onto CBA is reflect, translate, dilate by 2."""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, assert_lengths, dilate, dist, figure, needs_reflection,
                                    reflect, similarity_ratio, translate)

_F, _E, _D = P((-1.5, 0), (0, 0), (0, np.sqrt(3 ** 2 - 1.5 ** 2)))
_C, _B, _A = P((5.5, 0), (2.5, 0), (2.5, 2 * np.sqrt(3 ** 2 - 1.5 ** 2)))


@figure("3.6 Progress Check A_triangles")
def triangles() -> Figure:
    FED, CBA = np.array([_F, _E, _D]), np.array([_C, _B, _A])
    assert np.isclose(similarity_ratio(FED, CBA), 2) and needs_reflection(FED, CBA)
    assert np.isclose(dist(_F, _D), 3) and np.isclose(dist(_A, _C), 6) and np.isclose(dist(_F, _E), 1.5)
    assert_lengths([(_F, _D, 3), (_A, _C, 6), (_F, _E, 1.5)])
    assert np.isclose(angle_deg(_E, _F, _D), 90) and np.isclose(angle_deg(_B, _C, _A), 90)
    # key sequence: reflect across line DE, translate E to B, dilate center B by 2
    step = dilate(translate(reflect(FED, _D, _E), _B - _E), 2, _B)
    assert np.allclose(step, CBA)
    f = Figure(width_in=2.4, height_in=2.0)
    for tri in (FED, CBA):
        f.poly(tri)
        f.dots(tri)
    f.right_angle(_E, _F, _D, size=0.3)
    f.right_angle(_B, _C, _A, size=0.4)
    for pt, nm, d in ((_F, "F", (-0.6, -1)), (_E, "E", (0.4, -1)), (_D, "D", (0, 1)),
                      (_B, "B", (-0.4, -1)), (_C, "C", (0.6, -1)), (_A, "A", (0, 1))):
        f.label(pt, nm, direction=d, size=11)
    f.side_label(_F, _D, "3", FED.mean(0), size=11)
    f.side_label(_F, _E, "1.5", FED.mean(0), size=11)
    f.side_label(_A, _C, "6", CBA.mean(0), size=11)
    return f

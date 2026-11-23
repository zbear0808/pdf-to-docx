"""3.6 Progress Check A: right triangles FED (small) and BAC (large). FED onto BAC is reflect, translate, dilate by 2.
Large-triangle letters: right angle A, top C, bottom right B, so the matching (F->B, E->A, D->C) is not
alphabetical (DEF ~ ABC is wrong) and is not Lesson 3.6's ABC ~ DEF."""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, assert_lengths, dilate, dist, figure, needs_reflection,
                                    reflect, similarity_ratio, translate)

_F, _E, _D = P((-1.5, 0), (0, 0), (0, np.sqrt(3 ** 2 - 1.5 ** 2)))
_B, _A, _C = P((5.5, 0), (2.5, 0), (2.5, 2 * np.sqrt(3 ** 2 - 1.5 ** 2)))


@figure("3.6 Progress Check A_triangles")
def triangles() -> Figure:
    FED, BAC = np.array([_F, _E, _D]), np.array([_B, _A, _C])
    assert np.isclose(similarity_ratio(FED, BAC), 2) and needs_reflection(FED, BAC)
    assert_lengths([(_F, _D, 3), (_C, _B, 6), (_F, _E, 1.5), (_A, _B, 3)])
    assert np.isclose(angle_deg(_E, _F, _D), 90) and np.isclose(angle_deg(_A, _B, _C), 90)
    # key sequence: reflect across line DE, translate E to A, dilate center A by 2
    step = dilate(translate(reflect(FED, _D, _E), _A - _E), 2, _A)
    assert np.allclose(step, BAC)
    # the guide's other order: translate E to A, reflect across line AC, dilate center A by 2
    assert np.allclose(dilate(reflect(translate(FED, _A - _E), _A, _C), 2, _A), BAC)
    f = Figure(width_in=2.4, height_in=2.0)
    for tri in (FED, BAC):
        f.poly(tri)
        f.dots(tri)
    f.right_angle(_E, _F, _D, size=0.3)
    f.right_angle(_A, _B, _C, size=0.4)
    for pt, nm, d in ((_F, "F", (-0.6, -1)), (_E, "E", (0.4, -1)), (_D, "D", (0, 1)),
                      (_A, "A", (-0.4, -1)), (_B, "B", (0.6, -1)), (_C, "C", (0, 1))):
        f.label(pt, nm, direction=d, size=11)
    f.side_label(_F, _D, "3", FED.mean(0), size=11)
    f.side_label(_F, _E, "1.5", FED.mean(0), size=11)
    f.side_label(_C, _B, "6", BAC.mean(0), size=11)
    return f

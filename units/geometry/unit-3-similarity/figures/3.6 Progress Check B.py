"""3.6 Progress Check B: right triangles MKL (large) and RPQ (small). MKL onto RPQ is reflect across LK, translate L to Q, dilate by 1/2."""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, assert_lengths, dilate, dist, figure, needs_reflection,
                                    reflect, similarity_ratio, translate)

_LEG = np.sqrt(9 ** 2 - 5 ** 2)                      # long leg LK
_L, _K, _M = P((0, 0), (_LEG, 0), (0, 5))
_Q = P((11, 5))[0]
_P, _R = _Q + np.array([_LEG / 2, 0]), _Q + np.array([0, -2.5])


@figure("3.6 Progress Check B_triangles")
def triangles() -> Figure:
    MKL, RPQ = np.array([_M, _K, _L]), np.array([_R, _P, _Q])
    assert np.isclose(similarity_ratio(MKL, RPQ), 0.5) and needs_reflection(MKL, RPQ)
    assert np.isclose(dist(_K, _M), 9) and np.isclose(dist(_P, _R), 4.5) and np.isclose(dist(_L, _M), 5)
    assert_lengths([(_K, _M, 9), (_P, _R, 4.5), (_L, _M, 5)])
    assert np.isclose(angle_deg(_L, _K, _M), 90) and np.isclose(angle_deg(_Q, _P, _R), 90)
    # key sequence: reflect across line LK, translate L to Q, dilate center Q by 1/2
    step = dilate(translate(reflect(MKL, _L, _K), _Q - _L), 0.5, _Q)
    assert np.allclose(step, RPQ)
    f = Figure(width_in=2.8, height_in=1.5)
    for tri in (MKL, RPQ):
        f.poly(tri)
        f.dots(tri)
    f.right_angle(_L, _K, _M, size=0.55)
    f.right_angle(_Q, _P, _R, size=0.35)
    for pt, nm, d in ((_L, "L", (-0.6, -1)), (_K, "K", (0.4, -1)), (_M, "M", (-0.4, 1)),
                      (_Q, "Q", (-0.6, 1)), (_R, "R", (-0.4, -1)), (_P, "P", (0.6, 1))):
        f.label(pt, nm, direction=d, size=11)
    f.side_label(_K, _M, "9", MKL.mean(0), size=11)
    f.side_label(_L, _M, "5", MKL.mean(0), size=11)
    f.side_label(_P, _R, "4.5", RPQ.mean(0), size=11)
    return f

"""3.6 Progress Check B: right triangles MKL (large) and QRP (small). MKL onto QRP is reflect across LK, translate L to P,
dilate by 1/2. Small-triangle letters: right angle P, top right R, bottom Q, so the matching (M->Q, K->R, L->P) is not
alphabetical (KLM ~ PQR is wrong)."""
import numpy as np

from lesson_builder.figures import (Figure, P, angle_deg, assert_lengths, dilate, dist, figure, needs_reflection,
                                    reflect, similarity_ratio, translate)

_LEG = np.sqrt(9 ** 2 - 5 ** 2)                      # long leg LK
_L, _K, _M = P((0, 0), (_LEG, 0), (0, 5))
_P = P((11, 5))[0]                                    # right angle of the small triangle
_R, _Q = _P + np.array([_LEG / 2, 0]), _P + np.array([0, -2.5])


@figure("3.6 Progress Check B_triangles")
def triangles() -> Figure:
    MKL, QRP = np.array([_M, _K, _L]), np.array([_Q, _R, _P])
    assert np.isclose(similarity_ratio(MKL, QRP), 0.5) and needs_reflection(MKL, QRP)
    assert_lengths([(_K, _M, 9), (_R, _Q, 4.5), (_L, _M, 5), (_P, _Q, 2.5)])
    assert np.isclose(angle_deg(_L, _K, _M), 90) and np.isclose(angle_deg(_P, _R, _Q), 90)
    # key sequence: reflect across line LK, translate L to P, dilate center P by 1/2
    step = dilate(translate(reflect(MKL, _L, _K), _P - _L), 0.5, _P)
    assert np.allclose(step, QRP)
    # the guide's other order: translate L to P, reflect across line PR, dilate center P by 1/2
    assert np.allclose(dilate(reflect(translate(MKL, _P - _L), _P, _R), 0.5, _P), QRP)
    f = Figure(width_in=2.8, height_in=1.5)
    for tri in (MKL, QRP):
        f.poly(tri)
        f.dots(tri)
    f.right_angle(_L, _K, _M, size=0.55)
    f.right_angle(_P, _R, _Q, size=0.35)
    for pt, nm, d in ((_L, "L", (-0.6, -1)), (_K, "K", (0.4, -1)), (_M, "M", (-0.4, 1)),
                      (_P, "P", (-0.6, 1)), (_Q, "Q", (-0.4, -1)), (_R, "R", (0.6, 1))):
        f.label(pt, nm, direction=d, size=11)
    f.side_label(_K, _M, "9", MKL.mean(0), size=11)
    f.side_label(_L, _M, "5", MKL.mean(0), size=11)
    f.side_label(_R, _Q, "4.5", QRP.mean(0), size=11)
    return f

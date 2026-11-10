import numpy as np
import pytest
from PIL import Image

from lesson_builder.figures import (
    Figure, P, angle_deg, assert_dilation, assert_distinct, assert_lengths, assert_similar, collinear, cross2,
    dilate, dilation_task, dist, extend, foot, is_parallel, is_rigid_image, law_of_sines_side, mark_congruent,
    mark_parallel, needs_reflection, on_ray, rect_pair, reflection_build, rotate, side_splitter, signed_area,
    similarity_ratio, triangle_from_angles, triangle_sas,
)


def _red(img):
    a = np.asarray(img.convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return int(((r - g > 80) & (r - b > 80)).sum())


def _layers_ok(f):
    """Key (both layers) has red ink; the student copy has none."""
    assert f.has_answer()
    assert _red(f.render(("given", "answer"))) > 50
    assert _red(f.render(("given",))) == 0


def test_cross2_and_exports():
    assert cross2((1, 0), (0, 1)) == 1.0 and cross2((2, 3), (4, 6)) == 0.0
    assert signed_area(P((0, 0), (2, 0), (0, 2))) == pytest.approx(2.0)
    assert similarity_ratio(P((0, 0), (1, 0), (0, 1)), dilate(P((0, 0), (1, 0), (0, 1)), 3)) == pytest.approx(3)


def test_is_parallel_scale_aware():
    assert is_parallel((0, 0), (1, 1), (5, 0), (7, 2))
    assert is_parallel((0, 0), (1000, 1000), (0, 1), (2000, 2001)) and not is_parallel((0, 0), (1, 0), (0, 0), (1, 0.01))
    big, tiny = 1e4, 1e-4
    assert is_parallel((0, 0), (big, big), (1, 0), (1 + tiny, tiny))
    assert not is_parallel((0, 0), (big, 0), (0, 1), (big, 1 + 0.001 * big))
    with pytest.raises(ValueError):
        is_parallel((0, 0), (0, 0), (1, 1), (2, 2))


def test_collinear_and_on_ray():
    assert collinear((0, 0), (1, 1), (5, 5), (-2, -2)) and collinear((0, 0), (1, 1))
    assert not collinear((0, 0), (1, 1), (2, 2.1))
    assert collinear(P(0, 0), P(100, 0), P(50, 1e-5))
    assert on_ray((0, 0), (1, 2), (3, 6)) and on_ray((0, 0), (1, 2), (0, 0))
    assert not on_ray((0, 0), (1, 2), (-1, -2)) and not on_ray((0, 0), (1, 2), (3, 6.1))
    assert on_ray(P(1, 1), P(2, 1), np.array([[9.0, 1.0]]))


def test_foot_and_extend():
    assert np.allclose(foot((2, 3), (0, 0), (4, 0)), (2, 0))
    assert np.allclose(foot((0, 2), (0, 0), (2, 2)), (1, 1))
    box = (0, 10, 0, 6)
    assert np.allclose(extend((1, 1), (2, 2), box), [(1, 1), (6, 6)])
    assert np.allclose(extend((1, 1), (2, 2), box, ray=False), [(0, 0), (6, 6)])
    assert np.allclose(extend((2, 3), (5, 3), box, ray=False), [(0, 3), (10, 3)])
    assert np.allclose(extend((4, 1), (4, 2), box, ray=False), [(4, 0), (4, 6)])
    with pytest.raises(ValueError):
        extend((20, 20), (21, 21), box)


def test_law_of_sines_and_triangles():
    assert law_of_sines_side(10, 30, 90) == pytest.approx(20)
    A, B, C = triangle_from_angles((0, 0), (5, 0), 40, 65)
    assert angle_deg(A, B, C) == pytest.approx(40) and angle_deg(B, A, C) == pytest.approx(65)
    assert C[1] > 0 and triangle_from_angles((0, 0), (5, 0), 40, 65, above=False)[2][1] < 0
    t = triangle_from_angles((1, 2), (3, 5), 50, 70)
    assert angle_deg(*t) == pytest.approx(50) and signed_area(t) > 0
    with pytest.raises(ValueError):
        triangle_from_angles((0, 0), (1, 0), 100, 90)
    A, B, C = triangle_sas((0, 0), (4, 0), 60, 3)
    assert dist(A, C) == pytest.approx(3) and angle_deg(A, B, C) == pytest.approx(60) and C[1] > 0
    assert triangle_sas((0, 0), (4, 0), 60, 3, above=False)[2][1] < 0


def test_assert_dilation():
    src, c = P((2, 5), (4, 4), (3, 1)), P(0, 2)
    assert_dilation(c, src, dilate(src, 2, c), 2)
    assert_dilation(c, src, dilate(src, -0.5, c), -0.5)
    assert_dilation(c, np.vstack([src, [c]]), dilate(np.vstack([src, [c]]), 3, c), 3)
    with pytest.raises(AssertionError, match="ray"):
        assert_dilation(c, src, dilate(src, 2, (0, 0)), 2)
    with pytest.raises(AssertionError, match="ratio"):
        assert_dilation(c, src, dilate(src, 2.5, c), 2)


def test_assert_lengths():
    A, B, C = P((0, 0), (4, 0), (0, 3))
    assert assert_lengths([(A, B, 8), (A, C, 6), (B, C, 10)]) == pytest.approx(0.5)
    assert_lengths([(A, B, 8), (A, C, 6.1)])  # 1.6% off is fine
    with pytest.raises(AssertionError, match="pair 1"):
        assert_lengths([(A, B, 8), (A, C, 7)])


def test_assert_distinct_and_similar():
    assert_distinct([30, 35, 70])
    with pytest.raises(AssertionError, match="35 and 37"):
        assert_distinct([35, 37, 90])
    tri = P((0, 0), (3, 0), (1, 2))
    assert assert_similar(tri, rotate(dilate(tri, 1.5), 30), 1.5) == pytest.approx(1.5)
    with pytest.raises(AssertionError, match="not 2"):
        assert_similar(tri, dilate(tri, 1.5), 2)
    with pytest.raises(AssertionError, match="not a similar"):
        assert_similar(tri, P((0, 0), (3, 0), (1, 3)))


def _ops(f, layer):
    return sum(op.layer == layer for op in f._ops)


def test_mark_congruent_counts():
    A, B, C, D = P((0, 0), (3, 0), (3, 2), (0, 2))
    calls = []
    f = Figure(2, 2)
    f.ticks = lambda a, b, n=1, layer="given", size=0.12: calls.append(("t", n, layer, size))
    f.arc = lambda v, p1, p2, n=1, r=0.35, layer="given", gap=0.07: calls.append(("a", n, layer, r))
    mark_congruent(f, [((A, B), (C, D)), ((B, A, C), (D, C, A)), ((B, C), (D, A)), ((A, B, D), (C, D, B))],
                   layer="answer", size=0.1, r=[0.3, 0.5])
    assert calls == [("t", 1, "answer", 0.1)] * 2 + [("a", 1, "answer", 0.3)] * 2 + \
        [("t", 2, "answer", 0.1)] * 2 + [("a", 2, "answer", 0.5)] * 2
    with pytest.raises(AssertionError, match="mix"):
        mark_congruent(Figure(2, 2), [((A, B), (B, A, C))])


def test_mark_parallel_draws():
    f = Figure(2, 2)
    f.poly(P((0, 0), (3, 0), (1, 2)))
    mark_parallel(f, [((0, 0), (3, 0)), ((0.5, 1), (2, 1))], n=2, layer="answer")
    assert _ops(f, "answer") == 2
    _layers_ok(f)


def test_reflection_build(tmp_path):
    tri = P((0, 0), (1.3, 0), (0, 2.2))       # B, A, C as in Unit 2: reflect across BC
    f, info = reflection_build(tri, tri[0], tri[2], names="BAC")
    img = info["image_pts"]
    assert np.allclose(img[0], tri[0]) and np.allclose(img[2], tri[2]) and np.allclose(img[1], (-1.3, 0))
    assert info["correspondence"] == {"B": "B'", "A": "A'", "C": "C'"}
    _layers_ok(f)
    assert _ops(f, "answer") == 7       # image, dot, A' label, 4 ticks; no connector through B
    f2, info2 = reflection_build(P((1, 1), (3, 1), (2, 3)), (0, 0), (1, -1), line_name="m")
    assert is_rigid_image(P((1, 1), (3, 1), (2, 3)), info2["image_pts"])
    assert needs_reflection(P((1, 1), (3, 1), (2, 3)), info2["image_pts"])
    _layers_ok(f2)
    p = f2.save(tmp_path / "s.png")
    q = f2.save(tmp_path / "k.png", layers=("given", "answer"))
    assert Image.open(p).size == Image.open(q).size
    f3, _ = reflection_build(P((1, 1), (3, 1), (2, 3)), (0, 0), (0, 1), answer=False, marks=False)
    assert not f3.has_answer()


def test_dilation_task():
    pts, c = P((2, 5), (4, 4), (3, 1)), P(0, 2)
    f, info = dilation_task(pts, 2, c, grid=(0, 8, 0, 8))
    assert np.allclose(info["image_pts"], [(4, 8), (8, 6), (6, 0)])
    _layers_ok(f)
    f2, info2 = dilation_task(P((6, 6), (10, 4), (8, 0)), 0.5, (0, 2), names="XYZ", grid=(0, 10, 0, 6),
                              ray_past=0.4, overrides={"X": (0, 1)})
    assert np.allclose(info2["image_pts"], [(3, 4), (5, 3), (4, 1)])
    _layers_ok(f2)
    f3, _ = dilation_task(P((2, 1)), 3, (0, 0), names="H", center_name="C")   # one point, no grid
    _layers_ok(f3)
    with pytest.raises(AssertionError, match="grid points"):
        dilation_task(pts, 1.5, c, grid=(0, 8, 0, 8))
    with pytest.raises(AssertionError, match="outside"):
        dilation_task(pts, 2, c, grid=(0, 5, 0, 5))


def test_side_splitter():
    tri = P((1.5, 3), (0, 0), (4, 0))
    f, info = side_splitter(tri, 0.4, seg_labels=("4", "6", None, "x"), marks=True)
    D, E = info["split_pts"]
    assert is_parallel(D, E, tri[1], tri[2]) and info["k"] == pytest.approx(2.5)
    assert dist(tri[0], D) / dist(D, tri[1]) == pytest.approx(4 / 6)
    assert not f.has_answer()
    with pytest.raises(AssertionError):
        side_splitter(tri, 1.2)


def test_rect_pair():
    f, info = rect_pair(3, 2, 1.5)
    a, b = info["rects"]
    assert similarity_ratio(a, b) == pytest.approx(1.5) and b[:, 0].min() > a[:, 0].max()
    texts = [lab.s for lab in f.labels]
    assert {"3", "2", "4.5"} <= set(texts) and "$M$" in texts
    f2, _ = rect_pair(4, 2, 0.5, names=("A", "B"), labels=("x", None, "2", "1"))
    assert "x" in [lab.s for lab in f2.labels]

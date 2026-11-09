import textwrap

import numpy as np
import pytest
from PIL import Image

from lesson_builder.figures import (
    P, angle_deg, congruence_statement, congruent_pair, correspondence, dist, fit_rigid, is_rigid_image,
    load_module, needs_reflection, orientation, reflect, render_all, rotate, rotation_build, ssa_triangles,
)
from lesson_builder.figures import core


def test_rotate_reflect_translate():
    assert np.allclose(rotate(P((1, 0)), 90), [[0, 1]])
    assert np.allclose(rotate(P((2, 1)), 180, about=(1, 1)), [[0, 1]])
    assert np.allclose(reflect(P((1, 2)), (0, 0), (1, 1)), [[2, 1]])
    assert np.allclose(reflect(P((3, 5)), (0, 0), (1, 0)), [[3, -5]])


def test_orientation_and_needs_reflection():
    tri = P((0, 0), (3, 0), (1, 2))
    assert orientation(tri) == 1 and orientation(tri[::-1]) == -1
    assert not needs_reflection(tri, rotate(tri, 37, about=(5, 1)))
    assert needs_reflection(tri, reflect(tri, (0, 0), (0, 1)))


def test_fit_rigid_is_exact():
    src = P((0, 0), (2.6, 0.5), (0.7, 1.9))
    target = rotate(reflect(src, (0, 0), (0, 1)), 75) + (6.4, -0.9)
    noisy = target + np.array([[0.05, -0.03], [-0.04, 0.02], [0.01, 0.06]])
    img = fit_rigid(src, noisy)
    assert is_rigid_image(src, img, tol=1e-9)
    assert needs_reflection(src, img)
    assert np.abs(img - target).max() < 0.1
    proper = fit_rigid(src, noisy, allow_reflection=False)
    assert is_rigid_image(src, proper) and not needs_reflection(src, proper)
    assert not is_rigid_image(src, src * 1.1)


def test_correspondence_and_statement():
    assert correspondence("ABC", "DEF") == {"A": "D", "B": "E", "C": "F"}
    assert congruence_statement("ABC", "DEF", "BAC") == "EDF"
    assert congruence_statement("PONML", "AYSFH", "NMLPO") == "SFHAY"
    with pytest.raises(ValueError):
        correspondence("ABC", "DE")


def test_ssa_triangles():
    long, short = ssa_triangles(5.9, 4.3, 46.6)
    for t in (long, short):
        V, W, U = t
        assert np.isclose(dist(V, W), 5.9) and np.isclose(dist(W, U), 4.3)
        assert np.isclose(angle_deg(V, W, U), 46.6)
    assert dist(long[0], long[2]) == pytest.approx(4.39, abs=0.01)
    assert dist(short[0], short[2]) == pytest.approx(3.72, abs=0.01)
    assert not is_rigid_image(long, short)


def test_rotation_build_is_parallelogram():
    f = rotation_build(P((0, 0), (1.2, 1.6), (4.0, 0.3)))  # asserts inside check the parallelogram
    assert f.has_answer()
    with pytest.raises(AssertionError):
        rotation_build(P((0, 0), (1, 1)))


def test_congruent_pair_info():
    src = P((0, 0), (2.6, 0.5), (0.7, 1.9))
    f, info = congruent_pair(src, "ABC", lambda p: rotate(reflect(p, (0, 0), (0, 1)), 75), "DEF", offset=(6.4, -0.9))
    assert info["correspondence"] == {"A": "D", "B": "E", "C": "F"}
    assert info["needs_reflection"] and is_rigid_image(src, info["image_pts"])
    assert not f.has_answer()
    f2, _ = congruent_pair(src, "ABC", lambda p: rotate(p, 90), "DEF", offset=(5, 0), marks="answer")
    assert f2.has_answer()


def _red_pixels(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return int(((r - g > 80) & (r - b > 80)).sum())


def test_registry_and_render_all(tmp_path):
    mod_path = tmp_path / "figures.py"
    mod_path.write_text(textwrap.dedent("""
        from lesson_builder.figures import Figure, figure, P

        @figure("tri_key")
        def tri_key():
            A, B, C = P((0, 0), (3, 0), (1, 2))
            f = Figure(2.4, 1.8)
            f.poly([A, B, C])
            f.label_poly([A, B, C], "ABC")
            f.seg(C, (1, -1.5), layer="answer", dashed=True)
            f.label((1, -1.5), "D", layer="answer", direction=(0, -1))
            return f

        @figure("plain")
        def plain():
            f = Figure(1.5, 1.5)
            f.poly(P((0, 0), (1, 0), (0, 1)))
            return f
    """))
    mod = load_module(mod_path)
    assert set(core.registered(mod)) == {"tri_key", "plain"}
    out = tmp_path / "out"
    res = render_all(mod_path, out)
    assert res["plain"]["key"] is None and res["plain"]["student"].exists()
    s, k = res["tri_key"]["student"], res["tri_key"]["key"]
    assert s.exists() and k.exists()
    assert Image.open(s).size == Image.open(k).size
    assert _red_pixels(k) > 100 and _red_pixels(s) == 0

    # cache: a second run doesn't rewrite; force does
    mtime = k.stat().st_mtime_ns
    render_all(mod_path, out)
    assert k.stat().st_mtime_ns == mtime
    render_all(mod_path, out, names=["tri_key"], force=True)
    assert k.stat().st_mtime_ns != mtime
    with pytest.raises(KeyError):
        render_all(mod_path, out, names=["nope"])

    # fresh import each call: registry follows the file contents
    mod_path.write_text(mod_path.read_text().replace('"plain"', '"plain2"'))
    mod = load_module(mod_path)
    assert set(core.registered(mod)) == {"tri_key", "plain2"}


def test_given_frame_unchanged_by_answer(tmp_path):
    f = core.Figure(2.0, 2.0)
    f.poly(P((0, 0), (1, 0), (0, 1)))
    xl0, yl0 = f._limits()
    f.dots([(0.5, 0.5)], layer="answer")
    assert f._limits() == (xl0, yl0)  # answer inside the given extents doesn't rescale
    p = f.save(tmp_path / "s.png")
    q = f.save(tmp_path / "k.png", layers=("given", "answer"))
    assert Image.open(p).size == Image.open(q).size

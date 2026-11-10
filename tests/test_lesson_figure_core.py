import json
import os
import textwrap
import time

import numpy as np
import pytest
from PIL import Image

from lesson_builder.figures import P, load_module, render_all
from lesson_builder.figures.core import Figure
from lesson_builder.figures.layout import prime_styles


def _red(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    return (a[..., 0] - a[..., 1] > 80) & (a[..., 0] - a[..., 2] > 80)


def _write(tmp_path, body, name="figures.py"):
    p = tmp_path / name
    p.write_text(textwrap.dedent(body), encoding="utf-8")
    return p


def test_custom_layers_extent_and_colour(tmp_path):
    mod = _write(tmp_path, """
        from lesson_builder.figures import Figure, figure

        @figure("bars")
        def bars():
            f = Figure(2.0, 1.5)
            f.custom(lambda ax, c: ax.bar([0, 1, 2], [1, 3, 2], color="0.8", edgecolor=c))
            f.custom(lambda ax, c: ax.plot([0, 2], [3.5, 3.5], color=c, lw=1.5), layer="answer")
            f.label((1, 3), "M", layer="answer")
            return f

        @figure("leak")
        def leak():
            f = Figure(1.5, 1.0)
            f.custom(lambda ax, c: ax.plot([0, 1], [0, 1], color="tab:blue", lw=3))
            return f

        @figure("cycle")
        def cycle():
            f = Figure(1.5, 1.0)
            f.custom(lambda ax, c: [ax.plot([0, 1], [k, k + 1], lw=3) for k in range(3)])
            return f
    """)
    res = render_all(mod, tmp_path / "out")
    b = res["bars"]
    assert not _red(b["student"]).any() and _red(b["key"]).sum() > 50
    assert Image.open(b["student"]).size == Image.open(b["key"]).size
    assert any("colour" in m for m in res["leak"]["meta"]["lint"])
    assert not res["cycle"]["meta"]["lint"]  # the default colour cycle is black on the given layer


def test_custom_needs_an_extent():
    f = Figure(1.0, 1.0)
    with pytest.raises(ValueError, match="extent"):
        f.custom(lambda ax, c: ax.text(0, 0, "hi", color=c))
    f.custom(lambda ax, c: ax.text(0, 0, "hi", color=c), extent=[(-1, -1), (1, 1)])
    assert len(f._ops) == 1


def test_custom_text_and_patches_are_obstacles():
    f = Figure(2.0, 2.0)
    f.custom(lambda ax, c: ax.text(0, 0.35, "WORD", color=c, ha="center", va="center", fontsize=13),
             extent=[(-1, -1), (1, 1)])
    f.dots([(0, 0)])
    f.label((0, 0), "A", direction=(0, 1))
    assert not f.place() and f.labels[0].choice != 0  # moved off the custom text, no lint left


def test_key_frame_union_keeps_answer_and_student_scale(tmp_path):
    mod = _write(tmp_path, """
        from lesson_builder.figures import Figure, figure, P

        def base(**kw):
            f = Figure(1.5, 1.5, **kw)
            f.poly(P((0, 0), (1, 0), (1, 1), (0, 1)))
            return f

        @figure("given_only")
        def given_only():
            return base()

        @figure("union")
        def union():
            f = base(key_frame="union")
            f.seg((1, 0.5), (4, 0.5), layer="answer")
            return f

        @figure("same")
        def same():
            f = base()
            f.seg((1, 0.5), (4, 0.5), layer="answer")
            return f
    """)
    res = render_all(mod, tmp_path / "out")
    g = Image.open(res["given_only"]["student"]).size
    us, uk = Image.open(res["union"]["student"]).size, Image.open(res["union"]["key"]).size
    assert abs(us[0] - g[0]) <= 2 and abs(us[1] - g[1]) <= 2  # student copy drawn as if no answer
    assert uk[0] > 2.5 * us[0]                                # key grew to hold the answer at the same scale
    red = _red(res["union"]["key"])
    cols = np.nonzero(red.any(0))[0]
    assert cols.max() > 0.9 * uk[0]                           # answer ink reaches the key's right edge
    ss, sk = Image.open(res["same"]["student"]).size, Image.open(res["same"]["key"]).size
    assert ss == sk and ss[0] < 1.5 * g[0]                    # "same": one frame, shrunk to fit the answer
    meta = res["union"]["meta"]
    assert meta["key_frame"] == "union" and meta["key_width_in"] > meta["width_in"]
    with pytest.raises(ValueError):
        Figure(1, 1, key_frame="wide")


def test_sidecar_labels(tmp_path):
    mod = _write(tmp_path, """
        from lesson_builder.figures import Figure, figure, P

        @figure("tri")
        def tri():
            A, B, C = P((0, 0), (3, 0), (1, 2))
            f = Figure(2.4, 1.8)
            f.poly([A, B, C])
            f.label_poly([A, B, C], "ABC")
            f.side_label(A, B, "6", C)
            f.label((1, -1), "D'", layer="answer")
            return f
    """)
    meta = render_all(mod, tmp_path / "out")["tri"]["meta"]
    on_disk = json.loads((tmp_path / "out" / "tri.json").read_text("utf-8"))
    assert on_disk == meta
    texts = {(d["text"], d["layer"]) for d in meta["labels"]}
    assert {("A", "given"), ("B", "given"), ("C", "given"), ("6", "given"), ("D\u2032", "answer")} <= texts
    assert [d["text"] for d in meta["key_labels"]] == ["D\u2032"] and meta["key_labels"][0]["raw"] == "$D'$"
    assert {"width_in", "min_text_pt", "lint"} <= set(meta)


def test_prime_styles_lint():
    assert prime_styles("$A'$") == {"'"} and prime_styles("A\u2032") == {"\u2032"}
    assert prime_styles(r"$A^{\prime}$") == {r"^{\prime}"} and prime_styles(r"$A\prime$") == {r"\prime"}
    assert prime_styles("don't") == set()  # an apostrophe outside math is not a prime
    pts = P((0, 0), (2, 0), (0, 2))
    f = Figure(2, 2)
    f.poly(pts)
    f.label_poly(pts, ["A'", "B'", "C''"])
    assert not any("prime" in m for m in f.place())
    f.label((1, 1), "D\u2032")
    f.text((1.6, 1.6), r"$E^{\prime}$")
    msgs = [m for m in f.place() if "mixed prime styles" in m]
    assert len(msgs) == 1 and "'" in msgs[0] and "\u2032" in msgs[0]


def test_cache_follows_helpers(tmp_path):
    folder = tmp_path / "figures"
    folder.mkdir()
    _write(folder, "SIZE = 1.0\n", "_helpers.py")
    mod = _write(folder, """
        from _helpers import SIZE
        from lesson_builder.figures import Figure, figure, P

        @figure("sq")
        def sq():
            f = Figure(1.0, 1.0)
            f.poly(P((0, 0), (SIZE, 0), (SIZE, SIZE)))
            return f
    """, "doc.py")
    out = tmp_path / "out"
    png = render_all(mod, out)["sq"]["student"]
    future = time.time() + 100
    png.write_bytes(b"cached")
    for p in (png, out / "sq.json"):
        os.utime(p, (future, future))
    render_all(mod, out)
    assert png.read_bytes() == b"cached"          # nothing changed: cache hit
    os.utime(folder / "_helpers.py", (future + 50, future + 50))
    render_all(mod, out)
    assert png.read_bytes()[:4] == b"\x89PNG"     # helper edited: re-rendered


def test_load_module_registry_still_isolated(tmp_path):
    mod = load_module(_write(tmp_path, """
        from lesson_builder.figures import Figure, figure
        @figure("one")
        def one():
            f = Figure(1, 1)
            f.dots([(0, 0)])
            return f
    """))
    assert "one" in render_all(mod, tmp_path / "o")


def test_actual_size_prints_one_unit_per_cm(tmp_path):
    mod = _write(tmp_path, """
        from lesson_builder.figures import Figure, figure

        @figure("ruler")
        def ruler():
            f = Figure(actual_size="cm")
            f.dots([(0, 0), (4, 0)])
            return f
        """)
    out = render_all(mod, tmp_path / "out")["ruler"]
    ink = np.asarray(Image.open(out["student"]).convert("L")) < 128
    cols = np.flatnonzero(ink.any(0))
    left, right = cols[cols < cols.mean()], cols[cols > cols.mean()]
    gap_cm = (right.mean() - left.mean()) / 300 * 2.54
    assert abs(gap_cm - 4) < 0.02
    assert out["meta"]["actual_size"] == "cm"
    with pytest.raises(ValueError):
        Figure(3, 2, actual_size="cm")
    with pytest.raises(ValueError):
        Figure()

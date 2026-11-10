import textwrap

import numpy as np
import pytest
from PIL import Image

from lesson_builder.figures import Figure, render_all
from lesson_builder.figures import coordinate as co
from lesson_builder.figures import cs, numberline as nl, stats as st

FIGS = '''
import numpy as np
from lesson_builder.figures import Figure, figure
from lesson_builder.figures import coordinate as co, cs, numberline as nl, stats as st

@figure("coord")
def coord():
    f = Figure(3.0, 3.0)
    co.axes(f, -4, 4, -4, 4)
    co.plot_points(f, [(1, 2), (-3, -1)], names="AB")
    co.plot_line(f, 0.75, 1.25, layer="answer")
    co.slope_triangle(f, (-3, -1), (1, 2), layer="answer")
    return f

@figure("parabola")
def parabola():
    f = Figure(2.5, 2.5)
    co.axes(f, -3, 3, -3, 3, grid=False, arrows=False, labels_every=2)
    co.plot_fn(f, lambda x: x * x / 2 + 0.5)
    return f

@figure("numline")
def numline():
    f = Figure(3.5, 0.8)
    nl.number_line(f, -5, 5, 1)
    nl.ray(f, 2, "right", open=True, layer="answer")
    nl.segment_interval(f, -4, -1, open_b=True, layer="answer")
    nl.point(f, 0)
    return f

@figure("dot")
def dot():
    f = Figure(3.0, 1.8)
    st.dotplot(f, [1, 2, 2, 3, 3, 3, 4, 7], 0, 8)
    st.boxplot(f, [1, 2, 2, 3, 3, 3, 4, 7], y=3.5, layer="answer")
    return f

@figure("hist")
def hist():
    f = Figure(3.0, 2.2)
    st.histogram(f, [12, 15, 18, 22, 25, 25, 31, 35, 38, 41, 44, 47], [10, 20, 30, 40, 50], xlabel="Minutes",
                 layer="answer")
    return f

@figure("scatter")
def scatter():
    f = Figure(3.0, 2.2)
    xs = np.arange(1, 9)
    st.scatter(f, xs, 3 * xs + 4, line=(3, 4), line_layer="answer", xlabel="Hours", ylabel="Score")
    return f

@figure("normal")
def normal():
    f = Figure(3.2, 1.5)
    st.normal_curve(f, 100, 15, shade=(115, None), layer="answer")
    return f

@figure("normal_given")
def normal_given():
    f = Figure(3.2, 1.5)
    st.normal_curve(f, 0, 1, shade=(-1, 1), ticks="z")
    return f

@figure("array")
def array():
    f = Figure(3.0, 0.9)
    cs.array_boxes(f, [3, 8, None, 1, 6], answer={2: 5}, name="nums")
    return f

@figure("refs")
def refs():
    f = Figure(3.2, 2.4)
    cs.reference_diagram(f, {"a": cs.Ref("d1"), "b": cs.Ref("d1"), "n": 4, "c": None},
                         {"d1": {"_type": "Dog", "name": '"Rex"', "age": 3}, "arr": [1, 2, 3]},
                         answer={"b", ("d1", "age")})
    return f
'''

ANSWER = {"coord", "numline", "dot", "hist", "scatter", "normal", "array", "refs"}


def _red(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    return int(((a[..., 0] - a[..., 1] > 80) & (a[..., 0] - a[..., 2] > 80)).sum())


def _colour(path):
    a = np.asarray(Image.open(path).convert("RGB")).astype(int)
    return int(((a.max(-1) - a.min(-1)) > 60).sum())


@pytest.fixture(scope="module")
def rendered(tmp_path_factory):
    d = tmp_path_factory.mktemp("subject")
    p = d / "figures.py"
    p.write_text(textwrap.dedent(FIGS), encoding="utf-8")
    return render_all(p, d / "out")


def test_every_figure_renders_black_and_white(rendered):
    assert set(rendered) == ANSWER | {"parabola", "normal_given"}
    for name, r in rendered.items():
        assert _colour(r["student"]) == 0, name
        assert (r["key"] is not None) == (name in ANSWER), name
        if r["key"]:
            assert _red(r["key"]) > 30, name
        assert r["meta"]["labels"], name
        assert not any("colour" in m for m in r["meta"]["lint"]), name


def test_sidecar_label_texts(rendered):
    texts = lambda n: [d["text"] for d in rendered[n]["meta"]["labels"]]  # noqa: E731
    assert {"A", "B", "x", "y", "-4", "4"} <= set(texts("coord"))
    assert {"4", "3"} <= {d["text"] for d in rendered["coord"]["meta"]["key_labels"]}  # run 4, rise 3
    assert [d["text"] for d in rendered["array"]["meta"]["key_labels"]] == ["5"]
    assert "null" in texts("refs") and "Dog" in texts("refs")
    assert {"55", "100", "145"} <= set(texts("normal"))


def test_simple_figures_have_no_lint(rendered):
    for name in ("numline", "dot", "hist", "scatter", "normal", "normal_given", "array", "refs", "parabola"):
        assert rendered[name]["meta"]["lint"] == [], (name, rendered[name]["meta"]["lint"])


def test_coordinate_asserts_and_slope():
    f = Figure(2, 2)
    with pytest.raises(AssertionError):
        co.plot_points(f, [(0, 0)])           # axes() first
    co.axes(f, -3, 3, -3, 3)
    with pytest.raises(AssertionError):
        co.plot_points(f, [(5, 0)])
    with pytest.raises(AssertionError):
        co.plot_line(f, 0, 10)                # y = 10 misses the window
    assert co.slope_triangle(f, (0, 0), (2, 3)) == pytest.approx(1.5)
    with pytest.raises(AssertionError):
        co.slope_triangle(f, (1, 0), (1, 2))
    assert co.fmt(-3) == "$-3$" and co.fmt(2.5) == "$2.5$" and co.fmt(4.0) == "$4$"


def test_numberline_asserts():
    f = Figure(3, 0.8)
    with pytest.raises(AssertionError):
        nl.point(f, 0)
    nl.number_line(f, 0, 10, 2)
    with pytest.raises(AssertionError):
        nl.point(f, 12)
    with pytest.raises(AssertionError):
        nl.ray(f, 3, "up")
    with pytest.raises(AssertionError):
        nl.segment_interval(f, 5, 2)


def test_stats_math():
    assert st.five_number([1, 2, 3, 4, 5, 6, 7]) == (1, 2, 4, 6, 7)       # odd n: median left out of halves
    assert st.five_number([1, 2, 3, 4, 5, 6, 7, 8]) == (1, 2.5, 4.5, 6.5, 8)
    f = Figure(3, 1)
    s = st.boxplot(f, [1, 2, 2, 3, 3, 3, 4, 20])
    assert s["outliers"] == [20] and s["max"] == 4
    assert st.boxplot(Figure(3, 1), [0, 1, 2, 3, 9], five=True)["max"] == 9
    assert st.nice_axis(3, 47) == (0, 50, 10)
    counts, scale = st.histogram(Figure(3, 2), [1, 2, 11, 12, 13, 25], [0, 10, 20, 30])
    assert counts == [2, 3, 1] and np.allclose(scale.pt(30, 0), (6, 0))
    assert st.dotplot(Figure(3, 1), [1, 1, 2], 0, 4) == {1.0: 2, 2.0: 1}
    with pytest.raises(AssertionError):
        st.dotplot(Figure(3, 1), [9], 0, 4)


def test_cs_asserts():
    with pytest.raises(AssertionError):
        cs.reference_diagram(Figure(2, 2), {"a": cs.Ref("missing")})
    with pytest.raises(AssertionError):
        cs.array_boxes(Figure(2, 1), [1, 2], answer={5: 0})
    c = cs.array_boxes(Figure(2, 1), [1, 2, 3], start=(1, 1), cell=2)
    assert np.allclose(c[0], (2, 2)) and np.allclose(c[-1], (6, 2))

import pytest
from docx import Document

from lesson_builder.docbuilder import add_math, latex_to_omml_inner


@pytest.mark.parametrize("latex, tag", [
    (r"\frac{A'B'}{AB} = \frac{3}{2}", "<m:f>"),
    (r"\sqrt{x^2 + 9}", "<m:rad>"),
    (r"\triangle ABC \sim \triangle DEF", "∼"),
    (r"\overline{AB} \parallel \overline{CD}", "<m:bar>"),
    (r"m\angle A = 40^\circ", "°"),
    (r"B_1 B_{12}", "<m:sSub>"),
])
def test_latex_subset_converts(latex, tag):
    assert tag in latex_to_omml_inner(latex, 11)
    p = Document().add_paragraph()
    add_math(p, latex, 11)  # parses as valid OMML


def test_unknown_command_is_reported():
    with pytest.raises(ValueError, match="unknown latex command"):
        latex_to_omml_inner(r"\notacommand{x}", 11)


def test_trig_functions_print_upright():
    r"""Regression (Unit 4): \sin, \cos, \tan printed in italics like variables."""
    from lesson_builder.docbuilder import latex_to_omml_inner
    xml = latex_to_omml_inner(r"\sin(43^\circ)=\frac{a}{c}", 11)
    assert '<m:sty m:val="p"/></m:rPr><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/>' in xml
    assert ">sin</m:t>" in xml
    inv = latex_to_omml_inner(r"\tan^{-1}(0.5)", 11)
    assert inv.startswith("<m:sSup><m:e><m:r><m:rPr><m:sty") and ">tan</m:t>" in inv and "−1" in inv
    assert ">\u2006</m:t>" in latex_to_omml_inner(r"\cos\theta", 11)
    assert ">arcsin</m:t>" in latex_to_omml_inner(r"\arcsin(0.6)", 11)


def test_greek_and_nth_root():
    from lesson_builder.docbuilder import latex_to_omml_inner
    assert ">β=40°</m:t>" in latex_to_omml_inner(r"\beta=40^\circ", 11)
    root = latex_to_omml_inner(r"\sqrt[3]{27}", 11)
    assert "<m:deg><m:r>" in root and ">3</m:t>" in root and "degHide" not in root


def test_space_between_coefficient_and_function():
    from lesson_builder.docbuilder import latex_to_omml_inner
    xml = latex_to_omml_inner(r"18\sin 41^\circ", 11)
    assert xml.index(">18</m:t>") < xml.index(">\u2006</m:t>") < xml.index(">sin</m:t>")
    assert ">\u2006</m:t>" not in latex_to_omml_inner(r"\sin(30^\circ)", 11).split(">sin</m:t>")[0]

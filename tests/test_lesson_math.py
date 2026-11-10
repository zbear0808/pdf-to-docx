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

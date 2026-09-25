import json
from pathlib import Path

from pdf_to_docx.ir_schema import (
    Alignment,
    BoundingBox,
    BoxBlock,
    ChartBlock,
    ChartSeries,
    ChartType,
    DocumentClass,
    DocumentSpec,
    EquationBlock,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageSpec,
    ParagraphBlock,
    QuestionBlock,
    QuestionChoice,
    TableBlock,
    TableCell,
    TextRun,
)
from pdf_to_latex.latex_compiler import LatexCompiler, escape_latex_text


def test_escape_latex_text():
    # Plain text special characters
    assert escape_latex_text("Revenue & Growth (50% increase)") == r"Revenue \& Growth (50\% increase)"
    assert escape_latex_text("Item #1 _test_ {foo}") == r"Item \#1 \_test\_ \{foo\}"

    # Embedded math should be preserved intact
    math_text = r"Given $z = \frac{x - \mu}{\sigma}$ and 20% margin"
    escaped = escape_latex_text(math_text)
    assert r"$z = \frac{x - \mu}{\sigma}$" in escaped
    assert r"20\%" in escaped


def test_article_compilation():
    doc_spec = DocumentSpec(
        title="Statistical Inference and Hypothesis Testing",
        author="Research Team",
        document_class=DocumentClass.ARTICLE,
        theme_hex="#1F4E79",
        pages=[
            PageSpec(
                page_number=1,
                blocks=[
                    HeadingBlock(level=1, text="Introduction to Significance Tests"),
                    ParagraphBlock(
                        runs=[
                            TextRun(text="In this paper we evaluate the test statistic "),
                            TextRun(text="z", is_math=True),
                            TextRun(text=" under the null hypothesis "),
                            TextRun(text=r"H_0: \mu = \mu_0", is_math=True),
                            TextRun(text="."),
                        ]
                    ),
                    EquationBlock(
                        latex_code=r"z = \frac{\bar{x} - \mu_0}{\sigma / \sqrt{n}}",
                        numbered=True,
                        label="eq:z_stat",
                    ),
                    TableBlock(
                        caption="Sample Statistics",
                        headers=["Condition", "Sample Size (n)", "Mean (\\bar{x})"],
                        rows=[
                            ["Control", "100", "50.2"],
                            ["Treatment", "105", "54.8"],
                        ],
                        booktabs=True,
                    ),
                    BoxBlock(
                        title="Theorem 1 (Central Limit Theorem)",
                        content=[
                            ParagraphBlock(
                                runs=[
                                    TextRun(text="As the sample size approaches infinity, the sampling distribution of "),
                                    TextRun(text=r"\bar{x}", is_math=True),
                                    TextRun(text=" approaches a normal distribution."),
                                ]
                            )
                        ],
                    ),
                ],
            )
        ],
    )

    compiler = LatexCompiler(doc_spec)
    tex_code = compiler.generate_latex_code()

    # Assertions
    assert r"\documentclass[11pt,letterpaper]{article}" in tex_code
    assert r"\usepackage{amsmath,amssymb,amsfonts,mathtools}" in tex_code
    assert r"\usepackage{booktabs}" in tex_code
    assert r"\usepackage[most]{tcolorbox}" in tex_code
    assert r"\section{Introduction to Significance Tests}" in tex_code
    assert r"\begin{equation}" in tex_code
    assert r"z = \frac{\bar{x} - \mu_0}{\sigma / \sqrt{n}}" in tex_code
    assert r"\label{eq:z_stat}" in tex_code
    assert r"\begin{tabular}" in tex_code
    assert r"\toprule" in tex_code
    assert r"\bottomrule" in tex_code
    assert r"\begin{tcolorbox}" in tex_code
    assert r"Theorem 1 (Central Limit Theorem)" in tex_code


def test_exam_quiz_compilation():
    doc_spec = DocumentSpec(
        title="AP Statistics Unit 1 Quiz",
        document_class=DocumentClass.EXAM,
        pages=[
            PageSpec(
                page_number=1,
                blocks=[
                    HeadingBlock(level=1, text="Section I: Free Response"),
                    QuestionBlock(
                        number=1,
                        points=4,
                        prompt=[
                            ParagraphBlock(
                                runs=[
                                    TextRun(text="A researcher records the weights (in grams) of a sample of 30 apples."),
                                ]
                            )
                        ],
                        response_box_height_pt=150.0,
                    ),
                    QuestionBlock(
                        number=2,
                        points=2,
                        prompt=[
                            ParagraphBlock(
                                runs=[
                                    TextRun(text="Which measure of center is most resistant to extreme outliers?"),
                                ]
                            )
                        ],
                        choices=[
                            QuestionChoice(label="(A)", text="Mean"),
                            QuestionChoice(label="(B)", text="Median"),
                            QuestionChoice(label="(C)", text="Standard Deviation"),
                            QuestionChoice(label="(D)", text="Range"),
                        ],
                    ),
                ],
            )
        ],
    )

    compiler = LatexCompiler(doc_spec)
    tex_code = compiler.generate_latex_code()

    assert r"\documentclass[11pt,addpoints]{exam}" in tex_code
    assert r"\firstpageheader{}{}{\textbf{Name:} \underline{\hspace{2.5in}}}" in tex_code
    assert r"\begin{questions}" in tex_code
    assert r"\question[4]" in tex_code
    assert r"\makeemptybox{150.0pt}" in tex_code
    assert r"\question[2]" in tex_code
    assert r"\begin{choices}" in tex_code
    assert r"\choice Median" in tex_code
    assert r"\end{questions}" in tex_code


def test_subagent_workspace_merge_and_compile():
    workspace = Path("test_output/latex_workspace")
    workspace.mkdir(parents=True, exist_ok=True)

    # Page 1 spec (simulated subagent output)
    p1 = PageSpec(
        page_number=1,
        blocks=[
            HeadingBlock(level=1, text="Page 1: Introduction"),
            ParagraphBlock(
                runs=[
                    TextRun(text="Independent subagent extraction for page 1."),
                ]
            ),
            EquationBlock(latex_code=r"e^{i\pi} + 1 = 0"),
        ],
    )
    p1_file = workspace / "page_1_spec.json"
    p1_file.write_text(p1.model_dump_json(indent=2), encoding="utf-8")

    # Page 2 spec (simulated subagent output)
    p2 = PageSpec(
        page_number=2,
        blocks=[
            HeadingBlock(level=1, text="Page 2: Tabular Analysis"),
            TableBlock(
                headers=["Metric", "Q1", "Q2"],
                rows=[["Accuracy", "94%", "97%"]],
            ),
        ],
    )
    p2_file = workspace / "page_2_spec.json"
    p2_file.write_text(p2.model_dump_json(indent=2), encoding="utf-8")

    # Load and compile
    loaded_pages = [
        PageSpec.model_validate(json.loads(p1_file.read_text(encoding="utf-8"))),
        PageSpec.model_validate(json.loads(p2_file.read_text(encoding="utf-8"))),
    ]
    doc_spec = DocumentSpec(title="Assembled Subagent Report", pages=loaded_pages)

    out_tex = Path("test_output/compiled_subagent_latex.tex")
    compiler = LatexCompiler(doc_spec)
    compiled = compiler.compile(out_tex)

    assert compiled.exists()
    content = compiled.read_text(encoding="utf-8")
    assert "Page 1: Introduction" in content
    assert r"e^{i\pi} + 1 = 0" in content
    assert "Page 2: Tabular Analysis" in content
    assert r"97\%" in content  # Escaped percent in table


if __name__ == "__main__":
    test_escape_latex_text()
    test_article_compilation()
    test_exam_quiz_compilation()
    test_subagent_workspace_merge_and_compile()
    print("All LaTeX tests passed successfully!")

"""Verification test for the intermediate representation and docx compiler."""

from pathlib import Path
from pdf_to_docx.ir_schema import (
    Alignment,
    ChartBlock,
    ChartSeries,
    ChartType,
    DocumentSpec,
    HeadingBlock,
    ListType,
    PageSpec,
    ParagraphBlock,
    TableBlock,
    TextRun,
)
from pdf_to_docx.docx_compiler import DocxCompiler


def test_compiler():
    spec = DocumentSpec(
        title="Quarterly Business Review",
        theme_hex="#1F4E79",
        pages=[
            PageSpec(
                page_number=1,
                blocks=[
                    HeadingBlock(level=1, text="Executive Summary", alignment=Alignment.LEFT),
                    ParagraphBlock(
                        runs=[
                            TextRun(text="This report outlines "),
                            TextRun(text="key performance indicators", bold=True),
                            TextRun(text=" for the second fiscal quarter."),
                        ],
                        alignment=Alignment.LEFT,
                    ),
                    ParagraphBlock(
                        runs=[TextRun(text="Notice: Projections are subject to quarterly audit.", italic=True)],
                        is_callout=True,
                    ),
                    HeadingBlock(level=2, text="Financial Highlights", alignment=Alignment.LEFT),
                    TableBlock(
                        headers=["Metric", "Q1 Actual", "Q2 Actual", "YoY Growth"],
                        rows=[
                            ["Revenue", "$1.2M", "$1.5M", "+25%"],
                            ["Net Margin", "22%", "27%", "+500 bps"],
                            ["Customer Retention", "94.2%", "96.1%", "+1.9%"],
                        ],
                        col_widths_pct=[30.0, 23.0, 23.0, 24.0],
                        cant_split=True,
                        repeat_header=True,
                    ),
                    ChartBlock(
                        title="Quarterly Revenue Trend ($M)",
                        chart_type=ChartType.BAR,
                        categories=["Q1", "Q2", "Q3 (Est)", "Q4 (Est)"],
                        series=[
                            ChartSeries(name="2025", values=[1.0, 1.2, 1.3, 1.5]),
                            ChartSeries(name="2026", values=[1.2, 1.5, 1.7, 2.0]),
                        ],
                    ),
                    ParagraphBlock(
                        runs=[TextRun(text="Key Strategic Priorities:", bold=True)],
                    ),
                    ParagraphBlock(
                        runs=[TextRun(text="Expand enterprise sales channel")],
                        list_type=ListType.BULLET,
                    ),
                    ParagraphBlock(
                        runs=[TextRun(text="Optimize cloud compute expenditures")],
                        list_type=ListType.BULLET,
                    ),
                ],
            )
        ],
    )

    test_dir = Path("test_output/sample_report")
    test_dir.mkdir(parents=True, exist_ok=True)
    test_out = test_dir / "sample_report.docx"
    compiler = DocxCompiler(spec)
    out_file = compiler.compile(test_out, assets_dir=test_dir / "assets")
    assert out_file.exists(), f"Output file does not exist: {out_file}"
    print(f"Compilation succeeded! Created: {out_file} ({out_file.stat().st_size} bytes)")


if __name__ == "__main__":
    test_compiler()

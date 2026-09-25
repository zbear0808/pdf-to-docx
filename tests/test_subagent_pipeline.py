"""Tests for the page-parallel subagent pipeline and CLI commands."""

import json
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


def test_page_specs_merge_and_compile():
    workspace = Path("test_output/subagent_workspace")
    workspace.mkdir(parents=True, exist_ok=True)

    # Page 1 spec (produced by Page 1 Subagent)
    p1 = PageSpec(
        page_number=1,
        blocks=[
            HeadingBlock(level=1, text="Page 1: Executive Overview", alignment=Alignment.LEFT),
            ParagraphBlock(
                runs=[
                    TextRun(text="This is page 1 extracted by an "),
                    TextRun(text="independent subagent", bold=True),
                    TextRun(text=" to isolate LLM context."),
                ]
            ),
            TableBlock(
                headers=["Metric", "2025", "2026"],
                rows=[["ARR", "$10M", "$18M"], ["EBITDA", "$2M", "$5M"]],
            ),
        ],
    )
    p1_file = workspace / "page_1_spec.json"
    p1_file.write_text(p1.model_dump_json(indent=2), encoding="utf-8")

    # Page 2 spec (produced by Page 2 Subagent)
    p2 = PageSpec(
        page_number=2,
        blocks=[
            HeadingBlock(level=1, text="Page 2: Regional Performance", alignment=Alignment.LEFT),
            ParagraphBlock(
                runs=[
                    TextRun(text="Extracted independently by the Page 2 subagent.", italic=True),
                ]
            ),
            ChartBlock(
                title="Regional Revenue Share",
                chart_type=ChartType.BAR,
                categories=["Americas", "EMEA", "APAC"],
                series=[ChartSeries(name="Share (%)", values=[55.0, 30.0, 15.0])],
            ),
        ],
    )
    p2_file = workspace / "page_2_spec.json"
    p2_file.write_text(p2.model_dump_json(indent=2), encoding="utf-8")

    # Verify both specs can be re-loaded and merged into DocumentSpec
    loaded_pages = [
        PageSpec.model_validate(json.loads(p1_file.read_text(encoding="utf-8"))),
        PageSpec.model_validate(json.loads(p2_file.read_text(encoding="utf-8"))),
    ]

    assert len(loaded_pages) == 2
    assert loaded_pages[0].page_number == 1
    assert loaded_pages[1].page_number == 2

    doc_spec = DocumentSpec(
        title="Multi-Page Subagent Report",
        theme_hex="#1F4E79",
        pages=loaded_pages,
    )

    out_docx = Path("test_output/subagent_merged_report.docx")
    compiler = DocxCompiler(doc_spec)
    compiled = compiler.compile(out_docx)

    assert compiled.exists()
    assert compiled.stat().st_size > 0
    print(f"Subagent pipeline test passed! Output: {compiled} ({compiled.stat().st_size} bytes)")


if __name__ == "__main__":
    test_page_specs_merge_and_compile()

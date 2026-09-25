"""Tests for CLI options: independent workspace directories and --save-ast."""

import json
from pathlib import Path
from unittest.mock import patch
from typer.testing import CliRunner

from pdf_to_docx.cli import app as docx_app
from pdf_to_latex.cli import app as latex_app
from pdf_to_docx.ir_schema import (
    Alignment,
    DocumentSpec,
    HeadingBlock,
    PageSpec,
    ParagraphBlock,
    TextRun,
)

runner = CliRunner()


def test_docx_compile_pages_save_ast_options():
    test_dir = Path("test_output/test_cli_docx")
    workspace = test_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # Create dummy page spec
    p1 = PageSpec(
        page_number=1,
        blocks=[
            HeadingBlock(level=1, text="Test Title", alignment=Alignment.CENTER),
            ParagraphBlock(runs=[TextRun(text="Test paragraph content.")]),
        ],
    )
    spec_path = workspace / "page_1_spec.json"
    spec_path.write_text(p1.model_dump_json(indent=2), encoding="utf-8")

    out_docx_no_ast = test_dir / "doc_no_ast.docx"
    default_ast_file = test_dir / "doc_no_ast_ast.json"
    if default_ast_file.exists():
        default_ast_file.unlink()

    # 1. Compile WITHOUT --save-ast -> should NOT produce AST file
    result = runner.invoke(docx_app, ["compile-pages", str(workspace), "-o", str(out_docx_no_ast)])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert out_docx_no_ast.exists()
    assert not default_ast_file.exists(), "AST file should not exist when --save-ast is not passed"

    # 2. Compile WITH --save-ast -> should produce AST file at default path
    out_docx_with_ast = test_dir / "doc_with_ast.docx"
    expected_ast_file = test_dir / "doc_with_ast_ast.json"
    result = runner.invoke(
        docx_app,
        ["compile-pages", str(workspace), "-o", str(out_docx_with_ast), "--save-ast"],
    )
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert out_docx_with_ast.exists()
    assert expected_ast_file.exists(), "AST file should exist when --save-ast is passed"
    ast_data = json.loads(expected_ast_file.read_text(encoding="utf-8"))
    assert len(ast_data["pages"]) == 1
    assert ast_data["pages"][0]["blocks"][0]["text"] == "Test Title"

    # 3. Compile WITH custom --ast-path
    custom_ast = test_dir / "custom_named_ast.json"
    if custom_ast.exists():
        custom_ast.unlink()
    out_docx_custom = test_dir / "doc_custom.docx"
    result = runner.invoke(
        docx_app,
        ["compile-pages", str(workspace), "-o", str(out_docx_custom), "--ast-path", str(custom_ast)],
    )
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert out_docx_custom.exists()
    assert custom_ast.exists(), "Custom AST file should exist when --ast-path is specified"


def test_latex_compile_pages_save_ast_options():
    test_dir = Path("test_output/test_cli_latex")
    workspace = test_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)

    # Create dummy page spec
    p1 = PageSpec(
        page_number=1,
        blocks=[
            HeadingBlock(level=1, text="LaTeX Title", alignment=Alignment.CENTER),
            ParagraphBlock(runs=[TextRun(text="LaTeX test content.")]),
        ],
    )
    spec_path = workspace / "page_1_spec.json"
    spec_path.write_text(p1.model_dump_json(indent=2), encoding="utf-8")

    out_tex_no_ast = test_dir / "doc_no_ast.tex"
    default_ast_file = test_dir / "doc_no_ast_ast.json"
    if default_ast_file.exists():
        default_ast_file.unlink()

    # 1. Compile WITHOUT --save-ast -> should NOT produce AST file
    result = runner.invoke(latex_app, ["compile-pages", str(workspace), "-o", str(out_tex_no_ast)])
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert out_tex_no_ast.exists()
    assert not default_ast_file.exists(), "AST file should not exist when --save-ast is not passed"

    # 2. Compile WITH --save-ast -> should produce AST file at default path
    out_tex_with_ast = test_dir / "doc_with_ast.tex"
    expected_ast_file = test_dir / "doc_with_ast_ast.json"
    result = runner.invoke(
        latex_app,
        ["compile-pages", str(workspace), "-o", str(out_tex_with_ast), "--save-ast"],
    )
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert out_tex_with_ast.exists()
    assert expected_ast_file.exists(), "AST file should exist when --save-ast is passed"

    # 3. Compile WITH custom --ast-path
    custom_ast = test_dir / "custom_latex_ast.json"
    if custom_ast.exists():
        custom_ast.unlink()
    out_tex_custom = test_dir / "doc_custom.tex"
    result = runner.invoke(
        latex_app,
        ["compile-pages", str(workspace), "-o", str(out_tex_custom), "--ast-path", str(custom_ast)],
    )
    assert result.exit_code == 0, f"Command failed: {result.stdout}"
    assert out_tex_custom.exists()
    assert custom_ast.exists(), "Custom AST file should exist when --ast-path is specified"


def test_independent_workspace_directory_resolution():
    sample_pdf = Path("tests/sample.pdf")
    if not sample_pdf.exists():
        return

    test_dir = Path("test_output/test_independent_workspace")
    test_dir.mkdir(parents=True, exist_ok=True)
    out_docx = test_dir / "custom_sample.docx"
    custom_workspace = test_dir / "my_custom_workspace"

    dummy_page_spec = PageSpec(
        page_number=1,
        blocks=[
            HeadingBlock(level=1, text="Sample Title", alignment=Alignment.CENTER),
            ParagraphBlock(runs=[TextRun(text="Mocked paragraph text.")]),
        ],
    )

    # 1. Convert with explicit --workspace-dir and --save-ast
    with patch("pdf_to_docx.cli.LayoutParser.parse_page_image", return_value=dummy_page_spec):
        result = runner.invoke(
            docx_app,
            [
                "convert",
                str(sample_pdf),
                "-o",
                str(out_docx),
                "--workspace-dir",
                str(custom_workspace),
                "--save-ast",
            ],
        )
    assert result.exit_code == 0, f"Convert failed: {result.stdout}"
    assert out_docx.exists()
    assert custom_workspace.exists(), f"Custom workspace directory {custom_workspace} was not created"
    assert (test_dir / "custom_sample_ast.json").exists(), "AST file was not saved"

    # 2. Convert with default independent workspace directory (no --workspace-dir, no --save-ast)
    out_docx_default = test_dir / "default_sample.docx"
    with patch("pdf_to_docx.cli.LayoutParser.parse_page_image", return_value=dummy_page_spec):
        result2 = runner.invoke(
            docx_app,
            [
                "convert",
                str(sample_pdf),
                "-o",
                str(out_docx_default),
            ],
        )
    assert result2.exit_code == 0, f"Convert failed: {result2.stdout}"
    assert out_docx_default.exists()
    assert (test_dir / ".workspace_default_sample").exists(), "Default independent workspace folder was not created"
    assert not (test_dir / "default_sample_ast.json").exists(), "AST should not be saved by default without --save-ast"

    # 3. LaTeX convert with default independent workspace and --save-ast
    out_tex_default = test_dir / "default_latex.tex"
    with patch("pdf_to_latex.cli.LayoutParser.parse_page_image", return_value=dummy_page_spec):
        result3 = runner.invoke(
            latex_app,
            [
                "convert",
                str(sample_pdf),
                "-o",
                str(out_tex_default),
                "--save-ast",
            ],
        )
    assert result3.exit_code == 0, f"LaTeX convert failed: {result3.stdout}"
    assert out_tex_default.exists()
    assert (test_dir / ".workspace_default_latex").exists(), "Default independent LaTeX workspace folder was not created"
    assert (test_dir / "default_latex_ast.json").exists(), "LaTeX AST was not saved with --save-ast"


if __name__ == "__main__":
    test_docx_compile_pages_save_ast_options()
    test_latex_compile_pages_save_ast_options()
    test_independent_workspace_directory_resolution()
    print("All CLI option tests passed successfully!")


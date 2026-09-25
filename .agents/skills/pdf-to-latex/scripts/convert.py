#!/usr/bin/env python3
"""Autonomous end-to-end converter from PDF to LaTeX."""

from pathlib import Path
from typing import Optional
import typer
from pdf_to_docx.ir_schema import DocumentClass
from pdf_to_latex.cli import convert as cli_convert


def main(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output: Path = typer.Option(Path("document.tex"), "--output", "-o", help="Output LaTeX file (.tex)"),
    workspace_dir: Optional[Path] = typer.Option(None, "--workspace-dir", "-w", help="Independent temp workspace directory"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
    doc_class: DocumentClass = typer.Option(DocumentClass.ARTICLE, "--doc-class", "-c", help="Document class (article, report, exam, scrartcl)"),
    title: Optional[str] = typer.Option(None, "--title", "-t", help="Document title"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution"),
    compile_pdf: bool = typer.Option(False, "--pdf", help="Also compile generated .tex into .pdf"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save DocumentSpec AST JSON alongside exported LaTeX"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path for DocumentSpec AST JSON"),
):
    cli_convert(
        pdf_path,
        output_tex=output,
        workspace_dir=workspace_dir,
        assets_dir=assets_dir,
        doc_class=doc_class,
        title=title,
        dpi=dpi,
        compile_pdf=compile_pdf,
        save_ast=save_ast,
        ast_path=ast_path,
    )


if __name__ == "__main__":
    typer.run(main)


#!/usr/bin/env python3
"""Convenience runner script for compiling individual page specs into LaTeX."""

from pathlib import Path
from typing import Optional
import typer
from pdf_to_docx.ir_schema import DocumentClass
from pdf_to_latex.cli import compile_pages as cli_compile_pages


def main(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*_spec.json files"),
    output: Path = typer.Option(Path("document.tex"), "--output", "-o", help="Output LaTeX file (.tex)"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    author: Optional[str] = typer.Option(None, "--author"),
    doc_class: DocumentClass = typer.Option(DocumentClass.ARTICLE, "--doc-class", "-c", help="Document class (article, report, exam, scrartcl)"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex", help="Primary theme color hex"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
    compile_pdf: bool = typer.Option(False, "--pdf", help="Also compile generated .tex into .pdf"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save merged DocumentSpec AST JSON alongside exported LaTeX"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path for DocumentSpec AST JSON"),
):
    cli_compile_pages(
        pages_dir,
        output_tex=output,
        title=title,
        author=author,
        doc_class=doc_class,
        theme_hex=theme_hex,
        assets_dir=assets_dir,
        compile_pdf=compile_pdf,
        save_ast=save_ast,
        ast_path=ast_path,
    )


if __name__ == "__main__":
    typer.run(main)


#!/usr/bin/env python3
"""Convenience runner script for compiling individual page specs into DOCX."""

from pathlib import Path
from typing import Optional
import typer
from pdf_to_docx.cli import compile_pages as cli_compile_pages

def main(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*_spec.json files"),
    output: Path = typer.Option(Path("output.docx"), "--output", "-o", help="Output DOCX path"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex", help="Corporate theme color hex"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save merged DocumentSpec AST JSON alongside exported DOCX"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path for DocumentSpec AST JSON"),
):
    cli_compile_pages(
        pages_dir,
        output_docx=output,
        title=title,
        theme_hex=theme_hex,
        assets_dir=assets_dir,
        save_ast=save_ast,
        ast_path=ast_path,
    )

if __name__ == "__main__":
    typer.run(main)


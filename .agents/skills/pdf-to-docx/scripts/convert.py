#!/usr/bin/env python3
"""Convenience runner script for full PDF to DOCX conversion."""

from pathlib import Path
from typing import Optional
import typer
from pdf_to_docx.cli import convert as cli_convert

def main(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF file"),
    output: Path = typer.Option(Path("output.docx"), "--output", "-o", help="Output DOCX path"),
    workspace_dir: Optional[Path] = typer.Option(None, "--workspace-dir", "-w", help="Independent temp workspace directory"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution for page analysis"),
    diff: bool = typer.Option(False, "--diff", help="Run visual diff critique if renderer available"),
    save_ast: bool = typer.Option(False, "--save-ast", help="Save DocumentSpec AST JSON alongside exported DOCX"),
    ast_path: Optional[Path] = typer.Option(None, "--ast-path", help="Custom path for DocumentSpec AST JSON"),
):
    cli_convert(
        pdf_path,
        output_docx=output,
        workspace_dir=workspace_dir,
        assets_dir=assets_dir,
        dpi=dpi,
        diff=diff,
        save_ast=save_ast,
        ast_path=ast_path,
    )

if __name__ == "__main__":
    typer.run(main)


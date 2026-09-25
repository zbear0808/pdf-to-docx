#!/usr/bin/env python3
"""Convenience runner script for full PDF to DOCX conversion."""

from pathlib import Path
import typer
from pdf_to_docx.cli import convert as cli_convert

def main(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF file"),
    output: Path = typer.Option(Path("output.docx"), "--output", "-o", help="Output DOCX path"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution for page analysis"),
    diff: bool = typer.Option(False, "--diff", help="Run visual diff critique if renderer available"),
):
    cli_convert(pdf_path, output, dpi=dpi, diff=diff)

if __name__ == "__main__":
    typer.run(main)

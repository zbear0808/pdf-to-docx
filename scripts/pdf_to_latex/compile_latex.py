#!/usr/bin/env python3
"""Compiles a .tex LaTeX document into a PDF using local LaTeX engines."""

from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from pdf_to_latex.latex_compiler import compile_tex_to_pdf, find_latex_compiler

console = Console()


def compile_doc(
    tex_path: Path = typer.Argument(..., help="Path to input .tex file"),
    output_pdf: Optional[Path] = typer.Option(None, "--output", "-o", help="Destination path for PDF"),
):
    engine = find_latex_compiler()
    if not engine:
        console.print("[bold red]Error:[/] No LaTeX compiler found on your system PATH.")
        console.print("Available options to compile this file:")
        console.print("  1. Install MiKTeX on Windows: [cyan]winget install MiKTeX.MiKTeX[/]")
        console.print("  2. Install Tectonic: [cyan]winget install tectonic[/]")
        console.print("  3. Upload the .tex file and assets/ folder directly to [cyan]Overleaf.com[/]")
        raise typer.Exit(code=1)

    console.print(f"[cyan]Compiling with {engine}...[/]")
    success, msg = compile_tex_to_pdf(tex_path, output_pdf=output_pdf)
    if success:
        console.print(f"[bold green]{msg}[/]")
    else:
        console.print(f"[bold red]{msg}[/]")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    typer.run(compile_doc)

#!/usr/bin/env python3
"""Helper script to inspect PDF structure and render pages for LaTeX conversion."""

from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table

from pdf_to_docx.pdf_extractor import PDFExtractor
from pdf_to_latex.latex_compiler import find_latex_compiler

console = Console()


def inspect(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    render_dpi: int = typer.Option(200, "--dpi", help="DPI for page rendering"),
    output_dir: Path = typer.Option(Path("./rendered_pages"), "--output-dir", "-o", help="Directory for rendered PNG pages"),
):
    with PDFExtractor(pdf_path) as ext:
        info = ext.get_document_info()
        console.print(f"[bold cyan]Document:[/] {info['title']} ({info['page_count']} pages)")

        table = Table(title="PDF Pages Breakdown")
        table.add_column("Page", justify="center")
        table.add_column("Dimensions (pt)")
        table.add_column("Orientation")
        table.add_column("Images", justify="right")
        table.add_column("Drawings", justify="right")

        for p in info["pages"]:
            table.add_row(
                str(p["page_number"]),
                f"{p['width_pt']:.1f} x {p['height_pt']:.1f}",
                p["orientation"],
                str(p["image_count"]),
                str(p["drawings_count"]),
            )
        console.print(table)

        paths = ext.render_all_pages(output_dir, dpi=render_dpi)
        console.print(f"[green]Rendered {len(paths)} pages at {render_dpi} DPI to {output_dir}[/]")

    compiler = find_latex_compiler()
    if compiler:
        console.print(f"[green]Detected local LaTeX compiler:[/] [bold]{compiler}[/]")
    else:
        console.print("[dim yellow]Note: No local LaTeX compiler found in PATH. You can compile the generated .tex in Overleaf or install MiKTeX/TeX Live/Tectonic.[/]")


if __name__ == "__main__":
    typer.run(inspect)

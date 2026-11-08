#!/usr/bin/env python3
"""Helper script to inspect PDF structure and render pages."""

import sys
from pathlib import Path
import typer
from pdf_to_docx.pdf_extractor import PDFExtractor
from rich.console import Console
from rich.table import Table

console = Console()

def inspect(pdf_path: Path, render_dpi: int = 200, output_dir: Path = Path("./rendered_pages")):
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

        # Render all pages
        paths = ext.render_all_pages(output_dir, dpi=render_dpi)
        console.print(f"[green]Rendered {len(paths)} pages at {render_dpi} DPI to {output_dir}[/]")

if __name__ == "__main__":
    typer.run(inspect)

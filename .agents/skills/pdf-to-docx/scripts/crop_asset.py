#!/usr/bin/env python3
"""Helper script to crop non-text assets (figures, drawings, signatures) from PDF."""

from pathlib import Path
import typer
from pdf_to_docx.pdf_extractor import PDFExtractor
from rich.console import Console

console = Console()

def crop_asset(
    pdf_path: Path = typer.Argument(..., help="Path to PDF"),
    page: int = typer.Option(1, "--page", "-p", help="1-indexed page number"),
    bbox: str = typer.Option(..., "--bbox", "-b", help="Bounding box as 'ymin,xmin,ymax,xmax' (0-1000)"),
    output: Path = typer.Option(Path("./assets/cropped_asset.png"), "--output", "-o"),
    dpi: int = typer.Option(300, "--dpi"),
    format: str = typer.Option("png", "--format", help="png or svg"),
):
    coords = [int(x.strip()) for x in bbox.split(",")]
    if len(coords) != 4:
        raise typer.BadParameter("BBox must be 4 comma-separated integers (0-1000)")

    with PDFExtractor(pdf_path) as ext:
        res = ext.extract_region(page, coords, output_path=output, dpi=dpi, format=format)
    console.print(f"[bold green]Asset saved to:[/] {res}")

if __name__ == "__main__":
    typer.run(crop_asset)

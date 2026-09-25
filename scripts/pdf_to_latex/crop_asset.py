#!/usr/bin/env python3
"""Crops high-resolution visual assets (charts, diagrams, logos) from PDF for LaTeX inclusion."""

from pathlib import Path
import typer
from rich.console import Console
from pdf_to_docx.pdf_extractor import PDFExtractor

console = Console()


def crop(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(1, "--page", "-p", help="Page number (1-indexed)"),
    bbox: str = typer.Option(..., "--bbox", "-b", help="Bounding box as 'ymin,xmin,ymax,xmax' on 0-1000 scale"),
    output: Path = typer.Option(Path("assets/cropped_asset.png"), "--output", "-o", help="Output path for asset"),
    dpi: int = typer.Option(300, "--dpi", help="DPI resolution for cropped asset"),
):
    coords = [int(x.strip()) for x in bbox.split(",")]
    if len(coords) != 4:
        raise typer.BadParameter("BBox must be 4 comma-separated integers: ymin,xmin,ymax,xmax")

    output.parent.mkdir(parents=True, exist_ok=True)
    with PDFExtractor(pdf_path) as ext:
        out = ext.extract_region(page, coords, output_path=output, dpi=dpi)
    console.print(f"[bold green]Asset saved to:[/] {out}")


if __name__ == "__main__":
    typer.run(crop)

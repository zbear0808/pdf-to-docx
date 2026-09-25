#!/usr/bin/env python3
"""Visual layout validation comparing original PDF rendering with compiled LaTeX PDF."""

from pathlib import Path
import typer
from rich.console import Console
from PIL import Image
from pdf_to_docx.pdf_extractor import PDFExtractor

console = Console()


def diff(
    original_png: Path = typer.Argument(..., help="Path to original rendered page PNG"),
    compiled_pdf: Path = typer.Argument(..., help="Path to compiled LaTeX PDF"),
    page: int = typer.Option(1, "--page", "-p", help="Page number (1-indexed)"),
    output_diff: Path = typer.Option(Path("visual_diff.png"), "--output", "-o", help="Output comparison PNG"),
    dpi: int = typer.Option(200, "--dpi"),
):
    if not original_png.exists():
        console.print(f"[bold red]Original image not found:[/] {original_png}")
        raise typer.Exit(code=1)

    if not compiled_pdf.exists():
        console.print(f"[bold red]Compiled PDF not found:[/] {compiled_pdf}")
        raise typer.Exit(code=1)

    temp_render = output_diff.parent / f".temp_compiled_p{page}.png"
    with PDFExtractor(compiled_pdf) as ext:
        if page > ext.page_count:
            console.print(f"[bold red]Page {page} exceeds compiled document page count ({ext.page_count})[/]")
            raise typer.Exit(code=1)
        ext.render_page_to_png(page, temp_render, dpi=dpi)

    img_orig = Image.open(original_png).convert("RGB")
    img_comp = Image.open(temp_render).convert("RGB")

    # Match heights
    target_h = max(img_orig.height, img_comp.height)
    orig_w = int(img_orig.width * (target_h / img_orig.height))
    comp_w = int(img_comp.width * (target_h / img_comp.height))

    img_orig_resized = img_orig.resize((orig_w, target_h), Image.Resampling.LANCZOS)
    img_comp_resized = img_comp.resize((comp_w, target_h), Image.Resampling.LANCZOS)

    # Side by side canvas with separator
    gap = 20
    combined = Image.new("RGB", (orig_w + comp_w + gap, target_h), color=(240, 240, 240))
    combined.paste(img_orig_resized, (0, 0))
    combined.paste(img_comp_resized, (orig_w + gap, 0))

    output_diff.parent.mkdir(parents=True, exist_ok=True)
    combined.save(str(output_diff))
    console.print(f"[bold green]Side-by-side visual comparison saved to:[/] {output_diff}")

    if temp_render.exists():
        temp_render.unlink()


if __name__ == "__main__":
    typer.run(diff)

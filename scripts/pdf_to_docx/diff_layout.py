#!/usr/bin/env python3
"""Helper script to run visual layout diff between original PDF page and generated DOCX."""

from pathlib import Path
import typer
from pdf_to_docx.visual_diff import VisualDiffInspector, render_docx_to_png
from rich.console import Console

console = Console()

def run_diff(
    original_png: Path = typer.Argument(..., help="Path to original rendered page PNG"),
    docx_path: Path = typer.Argument(..., help="Path to generated DOCX file"),
    page: int = typer.Option(1, "--page", "-p", help="Page number to compare"),
):
    temp_render = docx_path.parent / ".temp_render" / f"rendered_p{page}.png"
    rendered = render_docx_to_png(docx_path, temp_render, page_number=page)

    if not rendered or not rendered.exists():
        console.print("[yellow]Could not render DOCX headlessly. Ensure LibreOffice (soffice) is installed.[/]")
        return

    inspector = VisualDiffInspector()
    console.print(f"[cyan]Comparing {original_png} vs {rendered}...[/]")
    critique = inspector.inspect_and_critique(original_png, rendered, page_number=page)

    console.print(f"\n[bold yellow]Layout Fidelity Score:[/] {critique.fidelity_score}/100")
    if critique.matches_well:
        console.print("[bold green]Matches Well:[/]")
        for m in critique.matches_well:
            console.print(f"  + {m}")

    if critique.discrepancies:
        console.print("\n[bold red]Discrepancies & Recommendations:[/]")
        for d in critique.discrepancies:
            console.print(f"  - [{d.severity.upper()}] ({d.category}): {d.description}")
            console.print(f"    Fix: [italic]{d.suggested_fix}[/]")

if __name__ == "__main__":
    typer.run(run_diff)

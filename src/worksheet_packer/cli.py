"""Command Line Interface for Worksheet Packer.

Provides commands to inspect, parse, pack, and render space-efficient worksheets
into beautifully formatted Word (.docx) and LaTeX (.tex / .pdf) documents.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from .worksheet_ast import (
    RenderPlan,
    SectionOrdering,
    WorksheetSpec,
)
from .layout_engine import LayoutEngine
from .docx_renderer import DocxWorksheetRenderer
from .latex_renderer import LatexWorksheetRenderer
from .worksheet_parser import WorksheetParser

app = typer.Typer(
    name="worksheet-packer",
    help="Space-efficient PDF worksheet parser, 2D bin-packer, and DOCX/LaTeX renderer.",
    add_completion=False,
)
console = Console()


@app.command()
def info(
    file_path: Path = typer.Argument(..., help="Path to PDF, WorksheetSpec JSON, or RenderPlan JSON")
):
    """Inspects a PDF document or existing AST/Plan JSON file."""
    if not file_path.exists():
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        raise typer.Exit(1)

    if file_path.suffix.lower() == ".pdf":
        from pdf_to_docx.pdf_extractor import PDFExtractor
        with PDFExtractor(file_path) as ext:
            doc_info = ext.get_document_info()
            console.print(f"[bold cyan]PDF Document:[/bold cyan] {doc_info['title']}")
            console.print(f"Total Pages: {doc_info['page_count']}")
            table = Table(title="Pages Summary")
            table.add_column("Page", justify="right")
            table.add_column("Dimensions (pt)")
            table.add_column("Orientation")
            table.add_column("Images", justify="right")
            table.add_column("Drawings", justify="right")
            for p in doc_info["pages"]:
                table.add_row(
                    str(p["page_number"]),
                    f"{p['width_pt']:.1f} x {p['height_pt']:.1f}",
                    p["orientation"],
                    str(p["image_count"]),
                    str(p["drawings_count"]),
                )
            console.print(table)
    elif file_path.suffix.lower() == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if "pages" in data and "stats" in data:
            console.print(f"[bold green]RenderPlan JSON[/bold green]: {file_path.name}")
            console.print(f"Total Pages: {data.get('total_pages')}")
            stats = data.get("stats", {})
            console.print(f"Problems: {stats.get('total_problems')}")
            console.print(f"Side-by-side layouts: {stats.get('side_by_side_count')}")
            console.print(f"Stacked layouts: {stats.get('stacked_count')}")
            console.print(f"Text-only layouts: {stats.get('text_only_count')}")
        elif "sections" in data:
            console.print(f"[bold green]WorksheetSpec JSON[/bold green]: {data.get('title')}")
            console.print(f"Default Columns: {data.get('default_columns')}")
            total_probs = sum(len(s.get("problems", [])) for s in data.get("sections", []))
            console.print(f"Sections: {len(data.get('sections', []))}")
            console.print(f"Total Problems: {total_probs}")


@app.command()
def parse(
    pdf_path: Path = typer.Argument(..., help="Path to input worksheet PDF"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to output WorksheetSpec JSON"),
    workspace_dir: Optional[Path] = typer.Option(None, "--workspace-dir", "-w", help="Cache directory for media assets"),
    ordering: str = typer.Option("strict", "--ordering", help="Section ordering: 'strict' or 'flexible'"),
    columns: int = typer.Option(2, "--columns", "-c", help="Default column count: 1 or 2"),
):
    """Parses a worksheet PDF into a WorksheetSpec AST JSON with harvested diagrams."""
    sec_ordering = SectionOrdering.FLEXIBLE if ordering.lower() == "flexible" else SectionOrdering.STRICT
    out_json = output or pdf_path.with_name(f"{pdf_path.stem}_spec.json")

    console.print(f"[cyan]Parsing worksheet PDF:[/cyan] {pdf_path}")
    with WorksheetParser(pdf_path) as parser:
        spec = parser.parse_worksheet(
            workspace_dir=workspace_dir,
            ordering=sec_ordering,
            default_columns=columns,
        )

    out_json.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    total_probs = sum(len(s.problems) for s in spec.sections)
    console.print(f"[bold green]Extracted {total_probs} problems into:[/bold green] {out_json}")


@app.command()
def pack(
    spec_path: Path = typer.Argument(..., help="Path to WorksheetSpec JSON"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to output RenderPlan JSON"),
    columns: Optional[int] = typer.Option(None, "--columns", "-c", help="Override default columns (1 or 2)"),
    ordering: Optional[str] = typer.Option(None, "--ordering", help="Override ordering: 'strict' or 'flexible'"),
):
    """Executes 2D layout packing on a WorksheetSpec AST to generate a RenderPlan."""
    spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = WorksheetSpec.model_validate(spec_data)

    if columns is not None:
        spec.default_columns = columns
    if ordering:
        sec_ord = SectionOrdering.FLEXIBLE if ordering.lower() == "flexible" else SectionOrdering.STRICT
        for s in spec.sections:
            s.ordering = sec_ord

    engine = LayoutEngine(spec)
    plan = engine.pack()

    out_plan = output or spec_path.with_name(f"{spec_path.stem}_plan.json")
    out_plan.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    stats = plan.stats
    console.print(f"[bold green]Layout Plan Generated:[/bold green] {out_plan}")
    console.print(f"Total Pages: {plan.total_pages}")
    console.print(f"Side-by-side: {stats.get('side_by_side_count')} | Stacked: {stats.get('stacked_count')} | Text-only: {stats.get('text_only_count')}")


@app.command()
def render(
    plan_or_spec: Path = typer.Argument(..., help="Path to RenderPlan JSON or WorksheetSpec JSON"),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path (.docx or .tex)"),
    fmt: str = typer.Option("docx", "--format", "-f", help="Output format: 'docx', 'latex', or 'pdf'"),
):
    """Renders a RenderPlan or WorksheetSpec to DOCX, LaTeX, or PDF."""
    data = json.loads(plan_or_spec.read_text(encoding="utf-8"))

    if "pages" in data and "stats" in data:
        plan = RenderPlan.model_validate(data)
    else:
        spec = WorksheetSpec.model_validate(data)
        plan = LayoutEngine(spec).pack()

    fmt_clean = fmt.lower()
    if fmt_clean == "docx" or output.suffix.lower() == ".docx":
        renderer = DocxWorksheetRenderer(plan)
        saved = renderer.render(output)
        console.print(f"[bold green]Successfully compiled DOCX:[/bold green] {saved}")
    elif fmt_clean in ("latex", "tex", "pdf") or output.suffix.lower() in (".tex", ".pdf"):
        renderer = LatexWorksheetRenderer(plan)
        compile_pdf = (fmt_clean == "pdf" or output.suffix.lower() == ".pdf")
        tex_path = output if output.suffix.lower() == ".tex" else output.with_suffix(".tex")
        saved = renderer.render(tex_path, compile_pdf=compile_pdf)
        console.print(f"[bold green]Successfully generated LaTeX:[/bold green] {saved}")


@app.command()
def convert(
    pdf_path: Path = typer.Argument(..., help="Path to input worksheet PDF"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Destination path (.docx or .tex)"),
    fmt: str = typer.Option("docx", "--format", "-f", help="Format: 'docx', 'latex', or 'both'"),
    columns: int = typer.Option(2, "--columns", "-c", help="Number of columns (1 or 2)"),
    ordering: str = typer.Option("strict", "--ordering", help="Ordering: 'strict' or 'flexible'"),
    save_ast: bool = typer.Option(True, "--save-ast/--no-save-ast", help="Save intermediate spec and plan JSON"),
):
    """Autonomous end-to-end pipeline: PDF -> Parsing -> 2D Packing -> DOCX / LaTeX."""
    sec_ordering = SectionOrdering.FLEXIBLE if ordering.lower() == "flexible" else SectionOrdering.STRICT

    console.print(f"[bold cyan]Starting end-to-end worksheet conversion:[/bold cyan] {pdf_path}")
    with WorksheetParser(pdf_path) as parser:
        spec = parser.parse_worksheet(ordering=sec_ordering, default_columns=columns)

    if save_ast:
        spec_file = pdf_path.with_name(f"{pdf_path.stem}_spec.json")
        spec_file.write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    engine = LayoutEngine(spec)
    plan = engine.pack()

    if save_ast:
        plan_file = pdf_path.with_name(f"{pdf_path.stem}_plan.json")
        plan_file.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    fmt_lower = fmt.lower()
    if fmt_lower in ("docx", "both"):
        docx_out = output if (output and output.suffix.lower() == ".docx") else pdf_path.with_suffix(".docx")
        DocxWorksheetRenderer(plan).render(docx_out)
        console.print(f"[bold green]Rendered Word Document:[/bold green] {docx_out}")

    if fmt_lower in ("latex", "tex", "both", "pdf"):
        tex_out = output if (output and output.suffix.lower() == ".tex") else pdf_path.with_suffix(".tex")
        LatexWorksheetRenderer(plan).render(tex_out, compile_pdf=(fmt_lower == "pdf"))
        console.print(f"[bold green]Rendered LaTeX Document:[/bold green] {tex_out}")


def main():
    app()


if __name__ == "__main__":
    main()


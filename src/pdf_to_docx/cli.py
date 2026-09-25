"""Command-line interface for PDF to DOCX conversion."""

from __future__ import annotations
import json
from pathlib import Path
import re
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table

from .ir_schema import DocumentSpec, PageSpec
from .pdf_extractor import PDFExtractor
from .layout_parser import LayoutParser
from .docx_compiler import DocxCompiler
from .visual_diff import VisualDiffInspector, render_docx_to_png

app = typer.Typer(help="Autonomous, high-fidelity PDF to editable Word (.docx) converter.")
console = Console()


@app.command()
def info(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
):
    """Inspects PDF structure, dimensions, and visual elements."""
    with PDFExtractor(pdf_path) as extractor:
        doc_info = extractor.get_document_info()

    console.print(f"[bold cyan]Document:[/] {doc_info['title']} ({doc_info['page_count']} pages)")
    table = Table(title="Pages Overview")
    table.add_column("Page #", justify="center")
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


@app.command()
def render_pages(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_dir: Path = typer.Option(Path("./rendered_pages"), "--output-dir", "-o"),
    dpi: int = typer.Option(200, "--dpi", help="Rendering resolution"),
):
    """Renders all PDF pages to high-resolution PNG images."""
    with PDFExtractor(pdf_path) as extractor:
        paths = extractor.render_all_pages(output_dir, dpi=dpi)
    console.print(f"[green]Successfully rendered {len(paths)} pages to {output_dir}[/]")


@app.command()
def crop(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(1, "--page", "-p", help="Page number (1-indexed)"),
    bbox: str = typer.Option(..., "--bbox", help="Normalized bbox as 'ymin,xmin,ymax,xmax' (0-1000)"),
    output_path: Path = typer.Option(Path("cropped_asset.png"), "--output", "-o"),
    dpi: int = typer.Option(300, "--dpi"),
):
    """Crops a specific bounding box region from a PDF page."""
    coords = [int(x.strip()) for x in bbox.split(",")]
    if len(coords) != 4:
        raise typer.BadParameter("BBox must have 4 comma-separated integers: ymin,xmin,ymax,xmax")

    with PDFExtractor(pdf_path) as extractor:
        out = extractor.extract_region(page, coords, output_path=output_path, dpi=dpi)
    console.print(f"[green]Cropped region saved to {out}[/]")


@app.command()
def parse_page(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(..., "--page", "-p", help="Page number (1-indexed)"),
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="Path to pre-rendered page PNG"),
    output_spec: Path = typer.Option(..., "--output", "-o", help="Output PageSpec JSON path"),
    assets_dir: Path = typer.Option(Path("./assets"), "--assets-dir", "-a", help="Directory for cropped assets"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution if rendering"),
):
    """Parses a single PDF page into a PageSpec JSON and crops assets (designed for page subagents)."""
    assets_dir.mkdir(parents=True, exist_ok=True)
    output_spec.parent.mkdir(parents=True, exist_ok=True)

    with PDFExtractor(pdf_path) as extractor:
        if image and image.exists():
            page_png = image
        else:
            temp_dir = output_spec.parent / ".temp_renders"
            temp_dir.mkdir(parents=True, exist_ok=True)
            page_png = extractor.render_page_to_png(page, temp_dir / f"orig_p{page}.png", dpi=dpi)

        console.print(f"[cyan]Parsing layout structure for page {page}...[/]")
        parser = LayoutParser()
        page_spec = parser.parse_page_image(page_png, page_number=page)

        # Crop any image/figure blocks flagged with bbox
        for b_idx, block in enumerate(page_spec.blocks):
            if getattr(block, "type", "") == "image" and block.bbox:  # type: ignore
                crop_dest = assets_dir / f"p{page}_img{b_idx}.png"
                extractor.extract_region(
                    page,
                    [block.bbox.ymin, block.bbox.xmin, block.bbox.ymax, block.bbox.xmax],  # type: ignore
                    output_path=crop_dest,
                    dpi=300,
                )
                block.image_path = str(crop_dest)  # type: ignore

    output_spec.write_text(page_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]Page {page} AST saved to:[/] {output_spec}")


@app.command()
def compile_pages(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*_spec.json files"),
    output_docx: Path = typer.Option(Path("output.docx"), "--output", "-o", help="Output DOCX path"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex", help="Corporate theme color hex"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
):
    """Compiles multiple PageSpec JSON files from a workspace directory into a single Word (.docx) file."""
    if pages_dir.is_dir():
        spec_files = sorted(
            [f for f in pages_dir.glob("page_*_spec.json") if not f.name.endswith("_merged_ast.json")],
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
        if not spec_files:
            spec_files = sorted(
                [f for f in pages_dir.glob("*.json") if not f.name.endswith("_merged_ast.json") and not f.name.endswith("_ast.json")],
                key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
            )
    elif pages_dir.is_file():
        spec_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not spec_files:
        raise typer.BadParameter(f"No PageSpec JSON files found in {pages_dir}")

    console.print(f"[cyan]Found {len(spec_files)} page spec(s) to compile in order:[/]")
    for sf in spec_files:
        console.print(f"  - {sf.name}")

    pages = []
    for f in spec_files:
        data = json.loads(f.read_text(encoding="utf-8"))
        pages.append(PageSpec.model_validate(data))

    doc_spec = DocumentSpec(title=title, theme_hex=theme_hex, pages=pages)

    # Save merged AST for inspection
    merged_ast_path = output_docx.parent / f"{output_docx.stem}_merged_ast.json"
    merged_ast_path.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[dim]Merged DocumentSpec AST saved to: {merged_ast_path}[/]")

    compiler = DocxCompiler(doc_spec)
    out = compiler.compile(output_docx, assets_dir=assets_dir)
    console.print(f"[bold green]Successfully compiled {len(pages)} pages to:[/] {out}")


@app.command()
def merge_specs(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*_spec.json files"),
    output_spec: Path = typer.Option(Path("merged_spec.json"), "--output", "-o", help="Output merged DocumentSpec JSON path"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex", help="Corporate theme color hex"),
):
    """Merges individual PageSpec JSON files into a single DocumentSpec AST JSON."""
    if pages_dir.is_dir():
        spec_files = sorted(
            [f for f in pages_dir.glob("page_*_spec.json") if not f.name.endswith("_merged_ast.json")],
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
        if not spec_files:
            spec_files = sorted(
                [f for f in pages_dir.glob("*.json") if not f.name.endswith("_merged_ast.json") and not f.name.endswith("_ast.json")],
                key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
            )
    elif pages_dir.is_file():
        spec_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not spec_files:
        raise typer.BadParameter(f"No PageSpec JSON files found in {pages_dir}")

    pages = [PageSpec.model_validate(json.loads(f.read_text(encoding="utf-8"))) for f in spec_files]
    doc_spec = DocumentSpec(title=title, theme_hex=theme_hex, pages=pages)
    output_spec.parent.mkdir(parents=True, exist_ok=True)
    output_spec.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[bold green]Successfully merged {len(pages)} pages into:[/] {output_spec}")


@app.command()
def to_markdown_page(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(..., "--page", "-p", help="Page number (1-indexed)"),
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="Path to pre-rendered page PNG"),
    output_md: Path = typer.Option(..., "--output", "-o", help="Output Markdown path"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution if rendering"),
):
    """Fast-track: Converts a single page to clean GFM Markdown (designed for page subagents)."""
    output_md.parent.mkdir(parents=True, exist_ok=True)
    with PDFExtractor(pdf_path) as extractor:
        if image and image.exists():
            page_png = image
        else:
            temp_dir = output_md.parent / ".temp_renders"
            temp_dir.mkdir(parents=True, exist_ok=True)
            page_png = extractor.render_page_to_png(page, temp_dir / f"p{page}.png", dpi=dpi)

        console.print(f"Parsing page {page} into Markdown...")
        parser = LayoutParser()
        md = parser.parse_markdown_fast_path(page_png)
        output_md.write_text(f"<!-- Page {page} -->\n{md}\n", encoding="utf-8")
    console.print(f"[bold green]Page {page} Markdown saved to:[/] {output_md}")


@app.command()
def merge_markdown(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*.md files"),
    output_md: Path = typer.Option(Path("document.md"), "--output", "-o", help="Output merged Markdown path"),
):
    """Merges individual page Markdown files into a single unified Markdown document."""
    if pages_dir.is_dir():
        md_files = sorted(
            pages_dir.glob("page_*.md"),
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
    elif pages_dir.is_file():
        md_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not md_files:
        raise typer.BadParameter(f"No Markdown files found in {pages_dir}")

    full_md = [f.read_text(encoding="utf-8").strip() for f in md_files]
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n\n---\n\n".join(full_md), encoding="utf-8")
    console.print(f"[bold green]Merged {len(md_files)} pages into:[/] {output_md}")


@app.command()
def compile(
    spec_path: Path = typer.Argument(..., help="Path to AST DocumentSpec JSON file"),
    output_docx: Path = typer.Option(Path("output.docx"), "--output", "-o"),
):
    """Compiles a canonical DocumentSpec AST JSON into a formatted Word (.docx) file."""
    raw_data = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = DocumentSpec.model_validate(raw_data)
    compiler = DocxCompiler(spec)
    out = compiler.compile(output_docx)
    console.print(f"[bold green]Successfully compiled document to:[/] {out}")


@app.command()
def to_markdown(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_md: Path = typer.Option(Path("document.md"), "--output", "-o"),
    page: Optional[int] = typer.Option(None, "--page", "-p", help="Specific page (default: all)"),
):
    """Fast-track: Converts PDF pages to clean Markdown for direct docx-mcp generation."""
    temp_dir = Path("./.temp_pages")
    with PDFExtractor(pdf_path) as extractor:
        pages = [page] if page else list(range(1, extractor.page_count + 1))
        parser = LayoutParser()
        full_md = []

        for p_num in pages:
            img = extractor.render_page_to_png(p_num, temp_dir / f"p{p_num}.png")
            console.print(f"Parsing page {p_num} into Markdown...")
            md = parser.parse_markdown_fast_path(img)
            full_md.append(f"<!-- Page {p_num} -->\n{md}")

    output_md.write_text("\n\n---\n\n".join(full_md), encoding="utf-8")
    console.print(f"[bold green]Markdown exported to:[/] {output_md}")


@app.command()
def convert(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_docx: Path = typer.Option(Path("output.docx"), "--output", "-o"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution"),
    diff: bool = typer.Option(False, "--diff", help="Perform visual diff critique"),
):
    """Executes full autonomous conversion pipeline from PDF to DOCX."""
    console.print(f"[bold cyan]Starting conversion:[/] {pdf_path}")
    temp_dir = output_docx.parent / ".conversion_workspace"
    assets_dir = output_docx.parent / "assets"
    temp_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    with PDFExtractor(pdf_path) as extractor:
        doc_info = extractor.get_document_info()
        doc_spec = DocumentSpec(title=doc_info["title"])
        parser = LayoutParser()

        for p_info in doc_info["pages"]:
            p_num = p_info["page_number"]
            console.print(f"[cyan]Rendering page {p_num}/{doc_info['page_count']}...[/]")
            page_png = extractor.render_page_to_png(p_num, temp_dir / f"orig_p{p_num}.png", dpi=dpi)

            console.print(f"[cyan]Parsing layout structure for page {p_num}...[/]")
            page_spec = parser.parse_page_image(page_png, page_number=p_num)

            # Crop any image/figure blocks flagged with bbox
            for b_idx, block in enumerate(page_spec.blocks):
                if getattr(block, "type", "") == "image" and block.bbox:  # type: ignore
                    crop_dest = assets_dir / f"p{p_num}_img{b_idx}.png"
                    extractor.extract_region(
                        p_num,
                        [block.bbox.ymin, block.bbox.xmin, block.bbox.ymax, block.bbox.xmax],  # type: ignore
                        output_path=crop_dest,
                        dpi=300,
                    )
                    block.image_path = str(crop_dest)  # type: ignore

            doc_spec.pages.append(page_spec)

    # Save AST JSON for debugging or reproducible editing
    ast_json_path = output_docx.parent / f"{output_docx.stem}_ast.json"
    ast_json_path.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[dim]Intermediate Representation AST saved to: {ast_json_path}[/]")

    # Compile to DOCX
    console.print("[cyan]Compiling AST into Word document (.docx)...[/]")
    compiler = DocxCompiler(doc_spec)
    compiler.compile(output_docx, assets_dir=assets_dir)
    console.print(f"[bold green]Successfully created Word document:[/] {output_docx}")

    # Optional Visual Diff
    if diff:
        console.print("[cyan]Rendering DOCX headlessly for visual validation...[/]")
        rendered_docx_png = temp_dir / "rendered_docx_p1.png"
        res = render_docx_to_png(output_docx, rendered_docx_png, page_number=1)
        if res and res.exists():
            orig_p1 = temp_dir / "orig_p1.png"
            inspector = VisualDiffInspector()
            critique = inspector.inspect_and_critique(orig_p1, rendered_docx_png, page_number=1)
            console.print(f"[bold yellow]Layout Fidelity Score:[/] {critique.fidelity_score}/100")
            for d in critique.discrepancies:
                console.print(f"  - [{d.severity.upper()}] ({d.category}): {d.description} -> [italic]{d.suggested_fix}[/]")
        else:
            console.print("[dim yellow]Headless DOCX renderer (LibreOffice) not detected; skipped visual diff.[/]")


def main():
    app()


if __name__ == "__main__":
    main()

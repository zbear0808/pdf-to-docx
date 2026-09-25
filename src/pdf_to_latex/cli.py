"""Command-line interface for PDF to LaTeX conversion."""

from __future__ import annotations
import json
from pathlib import Path
import re
from typing import List, Optional
import typer
from rich.console import Console
from rich.table import Table

from pdf_to_docx.ir_schema import DocumentClass, DocumentSpec, PageSpec
from pdf_to_docx.pdf_extractor import PDFExtractor
from pdf_to_docx.layout_parser import LayoutParser
from .latex_compiler import LatexCompiler, compile_tex_to_pdf, find_latex_compiler

app = typer.Typer(help="Autonomous, high-fidelity PDF to LaTeX (.tex) and PDF converter.")
console = Console()


@app.command()
def info(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
):
    """Inspects PDF structure, dimensions, fonts, and visual elements."""
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

    compiler = find_latex_compiler()
    if compiler:
        console.print(f"[green]Detected local LaTeX compiler:[/] [bold]{compiler}[/]")
    else:
        console.print("[dim yellow]No local LaTeX compiler detected (pdflatex, xelatex, tectonic). Generated .tex files will be ready for Overleaf or remote compilation.[/]")


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
    """Crops a specific bounding box region from a PDF page for \\includegraphics."""
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
def to_latex_page(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    page: int = typer.Option(..., "--page", "-p", help="Page number (1-indexed)"),
    image: Optional[Path] = typer.Option(None, "--image", "-i", help="Path to pre-rendered page PNG"),
    output_tex: Path = typer.Option(..., "--output", "-o", help="Output LaTeX fragment path"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution if rendering"),
):
    """Fast-track: Converts a single page directly into a LaTeX fragment (.tex) (designed for page subagents)."""
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    with PDFExtractor(pdf_path) as extractor:
        if image and image.exists():
            page_png = image
        else:
            temp_dir = output_tex.parent / ".temp_renders"
            temp_dir.mkdir(parents=True, exist_ok=True)
            page_png = extractor.render_page_to_png(page, temp_dir / f"p{page}.png", dpi=dpi)

        console.print(f"Parsing page {page} directly into LaTeX fragment...")
        parser = LayoutParser()
        tex_fragment = parser.parse_latex_fast_path(page_png, page_number=page)
        output_tex.write_text(f"% --- Page {page} ---\n{tex_fragment}\n", encoding="utf-8")
    console.print(f"[bold green]Page {page} LaTeX fragment saved to:[/] {output_tex}")


@app.command()
def compile_pages(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*_spec.json files"),
    output_tex: Path = typer.Option(Path("document.tex"), "--output", "-o", help="Output LaTeX file (.tex)"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    author: Optional[str] = typer.Option(None, "--author"),
    doc_class: DocumentClass = typer.Option(DocumentClass.ARTICLE, "--doc-class", "-c", help="Document class (article, report, exam, scrartcl)"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex", help="Primary theme color hex"),
    assets_dir: Optional[Path] = typer.Option(None, "--assets-dir", "-a", help="Assets directory"),
    compile_pdf: bool = typer.Option(False, "--pdf", help="Also compile generated .tex into .pdf"),
):
    """Compiles multiple PageSpec JSON files from a workspace into a production-grade LaTeX file and PDF."""
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

    doc_spec = DocumentSpec(
        title=title,
        author=author,
        document_class=doc_class,
        theme_hex=theme_hex,
        pages=pages,
    )

    # Save merged AST for inspection
    merged_ast_path = output_tex.parent / f"{output_tex.stem}_merged_ast.json"
    merged_ast_path.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[dim]Merged DocumentSpec AST saved to: {merged_ast_path}[/]")

    compiler = LatexCompiler(doc_spec)
    out = compiler.compile(output_tex, assets_dir=assets_dir)
    console.print(f"[bold green]Successfully compiled {len(pages)} pages to LaTeX:[/] {out}")

    if compile_pdf:
        console.print("[cyan]Attempting to compile LaTeX to PDF...[/]")
        pdf_target = output_tex.with_suffix(".pdf")
        success, msg = compile_tex_to_pdf(out, pdf_target)
        if success:
            console.print(f"[bold green]{msg}[/]")
        else:
            console.print(f"[yellow]{msg}[/]")


@app.command()
def merge_latex(
    pages_dir: Path = typer.Argument(Path(".conversion_workspace"), help="Directory containing page_*.tex fragment files"),
    output_tex: Path = typer.Option(Path("document.tex"), "--output", "-o", help="Output merged LaTeX document"),
    title: str = typer.Option("Converted Document", "--title", "-t", help="Document title"),
    author: Optional[str] = typer.Option(None, "--author"),
    doc_class: DocumentClass = typer.Option(DocumentClass.ARTICLE, "--doc-class", "-c"),
    theme_hex: str = typer.Option("#1F4E79", "--theme-hex"),
    compile_pdf: bool = typer.Option(False, "--pdf", help="Also compile generated .tex into .pdf"),
):
    """Merges individual page_*.tex fragment files into a master compilable LaTeX document with preamble."""
    if pages_dir.is_dir():
        tex_files = sorted(
            pages_dir.glob("page_*.tex"),
            key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)) if re.search(r"(\d+)", p.stem) else 0,
        )
    elif pages_dir.is_file():
        tex_files = [pages_dir]
    else:
        raise typer.BadParameter(f"Directory or file not found: {pages_dir}")

    if not tex_files:
        raise typer.BadParameter(f"No LaTeX fragment files found in {pages_dir}")

    dummy_spec = DocumentSpec(
        title=title,
        author=author,
        document_class=doc_class,
        theme_hex=theme_hex,
        pages=[],
    )
    compiler = LatexCompiler(dummy_spec)
    preamble = compiler._render_preamble()

    body_lines = ["\\begin{document}"]
    if doc_class != DocumentClass.EXAM:
        body_lines.append("\\maketitle\n")

    for idx, tf in enumerate(tex_files):
        if idx > 0:
            body_lines.append("\\newpage")
        body_lines.append(tf.read_text(encoding="utf-8").strip())
        body_lines.append("")

    body_lines.append("\\end{document}")

    full_tex = preamble + "\n\n" + "\n".join(body_lines) + "\n"
    output_tex.parent.mkdir(parents=True, exist_ok=True)
    output_tex.write_text(full_tex, encoding="utf-8")
    console.print(f"[bold green]Successfully assembled {len(tex_files)} pages into:[/] {output_tex}")

    if compile_pdf:
        console.print("[cyan]Attempting to compile LaTeX to PDF...[/]")
        pdf_target = output_tex.with_suffix(".pdf")
        success, msg = compile_tex_to_pdf(output_tex, pdf_target)
        if success:
            console.print(f"[bold green]{msg}[/]")
        else:
            console.print(f"[yellow]{msg}[/]")


@app.command()
def compile_pdf(
    tex_path: Path = typer.Argument(..., help="Path to input .tex file"),
    output_pdf: Optional[Path] = typer.Option(None, "--output", "-o", help="Output PDF destination"),
):
    """Compiles an existing .tex file to PDF using local LaTeX engine (pdflatex, xelatex, tectonic, latexmk)."""
    success, msg = compile_tex_to_pdf(tex_path, output_pdf)
    if success:
        console.print(f"[bold green]{msg}[/]")
    else:
        console.print(f"[bold red]{msg}[/]")
        raise typer.Exit(code=1)


@app.command()
def convert(
    pdf_path: Path = typer.Argument(..., help="Path to input PDF"),
    output_tex: Path = typer.Option(Path("document.tex"), "--output", "-o"),
    doc_class: DocumentClass = typer.Option(DocumentClass.ARTICLE, "--doc-class", "-c"),
    title: Optional[str] = typer.Option(None, "--title", "-t"),
    dpi: int = typer.Option(200, "--dpi", help="Vision resolution"),
    compile_pdf: bool = typer.Option(False, "--pdf", help="Also compile generated .tex into .pdf"),
):
    """Executes full autonomous conversion pipeline from PDF to LaTeX."""
    console.print(f"[bold cyan]Starting LaTeX conversion:[/] {pdf_path}")
    temp_dir = output_tex.parent / ".conversion_workspace"
    assets_dir = output_tex.parent / "assets"
    temp_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    with PDFExtractor(pdf_path) as extractor:
        doc_info = extractor.get_document_info()
        doc_title = title or doc_info["title"]
        doc_spec = DocumentSpec(title=doc_title, document_class=doc_class)
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

    # Save AST JSON
    ast_json_path = output_tex.parent / f"{output_tex.stem}_ast.json"
    ast_json_path.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
    console.print(f"[dim]Intermediate Representation AST saved to: {ast_json_path}[/]")

    # Compile to LaTeX
    console.print("[cyan]Compiling AST into LaTeX (.tex)...[/]")
    compiler = LatexCompiler(doc_spec)
    compiler.compile(output_tex, assets_dir=assets_dir)
    console.print(f"[bold green]Successfully created LaTeX document:[/] {output_tex}")

    if compile_pdf:
        console.print("[cyan]Attempting to compile LaTeX to PDF...[/]")
        pdf_target = output_tex.with_suffix(".pdf")
        success, msg = compile_tex_to_pdf(output_tex, pdf_target)
        if success:
            console.print(f"[bold green]{msg}[/]")
        else:
            console.print(f"[yellow]{msg}[/]")


def main():
    app()


if __name__ == "__main__":
    main()

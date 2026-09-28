"""Standalone PDF-to-DOCX Converter Pipeline.

Replaces the agentic subagent orchestration with a simple
ThreadPoolExecutor-based pipeline. One function call does everything:

    from standalone_converter import convert_pdf_to_docx
    output = convert_pdf_to_docx("input.pdf", "output.docx")

Pipeline steps:
    1. PDFExtractor: inspect PDF, render all pages to PNGs
    2. ThreadPoolExecutor: parse each page image via Gemini Flash Lite → PageSpec
    3. Crop image/figure assets from bounding boxes
    4. Assemble DocumentSpec from all PageSpecs
    5. DocxCompiler: compile to .docx
"""

from __future__ import annotations
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

from .ir_schema import DocumentSpec, PageSpec
from .pdf_extractor import PDFExtractor
from .page_parser import PageParser
from .docx_compiler import DocxCompiler

logger = logging.getLogger(__name__)


def _process_single_page(
    parser: PageParser,
    extractor: PDFExtractor,
    page_number: int,
    page_png: Path,
    assets_dir: Path,
) -> PageSpec:
    """Processes a single page: parse layout via Gemini, crop assets.

    This function runs in a thread pool worker. It is self-contained:
    one page image in, one PageSpec out. Errors are caught and result
    in an empty PageSpec with a warning.
    """
    try:
        logger.info(f"Parsing page {page_number}...")
        page_spec = parser.parse_page(page_png, page_number=page_number)

        # Crop any image/figure blocks that have bounding boxes
        for block_idx, block in enumerate(page_spec.blocks):
            if getattr(block, "type", "") == "image" and getattr(block, "bbox", None):
                bbox = block.bbox  # type: ignore
                crop_dest = assets_dir / f"p{page_number}_img{block_idx}.png"
                try:
                    extractor.extract_region(
                        page_number,
                        [bbox.ymin, bbox.xmin, bbox.ymax, bbox.xmax],
                        output_path=crop_dest,
                        dpi=300,
                    )
                    block.image_path = str(crop_dest)  # type: ignore
                    logger.info(f"  Cropped asset: {crop_dest}")
                except Exception as crop_err:
                    logger.warning(f"  Failed to crop asset on page {page_number}, block {block_idx}: {crop_err}")

        block_count = len(page_spec.blocks)
        table_count = sum(1 for b in page_spec.blocks if getattr(b, "type", "") == "table")
        chart_count = sum(1 for b in page_spec.blocks if getattr(b, "type", "") == "chart")
        image_count = sum(1 for b in page_spec.blocks if getattr(b, "type", "") == "image")
        logger.info(
            f"Page {page_number} done: {block_count} blocks "
            f"({table_count} tables, {chart_count} charts, {image_count} images)"
        )
        return page_spec

    except Exception as e:
        logger.error(f"Page {page_number} failed completely: {e}. Using empty page.")
        return PageSpec(page_number=page_number)


def convert_pdf_to_docx(
    pdf_path: str | Path,
    output_path: str | Path = "output.docx",
    *,
    api_key: Optional[str] = None,
    model_name: str = "gemini-3.5-flash-lite",

    max_workers: int = 4,
    dpi: int = 200,
    title: Optional[str] = None,
    theme_hex: str = "#1F4E79",
    workspace_dir: Optional[str | Path] = None,
    save_ast: bool = False,
    ast_path: Optional[str | Path] = None,
) -> Path:
    """Convert a PDF file to a Word (.docx) document.

    This is the main entry point. It runs the full pipeline:
    render pages → parse with Gemini Flash Lite → crop assets → compile DOCX.

    Args:
        pdf_path: Path to the input PDF file.
        output_path: Path for the output .docx file.
        api_key: Gemini API key. Falls back to GEMINI_API_KEY env var.
        model_name: Gemini model to use. Default is gemini-2.0-flash-lite.
        max_workers: Max concurrent page parsing threads. Default 4.
        dpi: Resolution for page rendering. Default 200.
        title: Document title. Defaults to the PDF filename stem.
        theme_hex: Corporate theme color hex. Default "#1F4E79".
        workspace_dir: Directory for intermediate files. Auto-created if None.
        save_ast: If True, save the merged DocumentSpec AST JSON.
        ast_path: Custom path for the AST JSON (implies save_ast=True).

    Returns:
        Path to the created .docx file.
    """
    pdf_path = Path(pdf_path)
    output_path = Path(output_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Set up workspace
    if workspace_dir:
        work_dir = Path(workspace_dir)
    else:
        work_dir = output_path.parent / f".workspace_{pdf_path.stem}"
    work_dir.mkdir(parents=True, exist_ok=True)

    renders_dir = work_dir / "rendered_pages"
    assets_dir = work_dir / "assets"
    renders_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    # ── Step 1: Inspect PDF and render all pages ──
    logger.info(f"Opening PDF: {pdf_path}")
    with PDFExtractor(pdf_path) as extractor:
        doc_info = extractor.get_document_info()
        page_count = doc_info["page_count"]
        doc_title = title or doc_info.get("title", pdf_path.stem)

        logger.info(f"Document: '{doc_title}', {page_count} pages")

        # Render all pages to PNGs
        logger.info(f"Rendering {page_count} pages at {dpi} DPI...")
        page_pngs: List[Path] = []
        for p_num in range(1, page_count + 1):
            png_path = renders_dir / f"page_{p_num}.png"
            extractor.render_page_to_png(p_num, png_path, dpi=dpi)
            page_pngs.append(png_path)
        logger.info(f"All {page_count} pages rendered to {renders_dir}")

        # ── Step 2: Parse all pages in parallel via Gemini Flash Lite ──
        parser = PageParser(api_key=api_key, model_name=model_name)
        page_specs: List[Optional[PageSpec]] = [None] * page_count

        logger.info(f"Parsing {page_count} pages with {max_workers} workers using {model_name}...")

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_page = {
                executor.submit(
                    _process_single_page,
                    parser, extractor, p_num, page_pngs[p_num - 1], assets_dir,
                ): p_num
                for p_num in range(1, page_count + 1)
            }
            for future in as_completed(future_to_page):
                p_num = future_to_page[future]
                try:
                    page_specs[p_num - 1] = future.result()
                except Exception as e:
                    logger.error(f"Unexpected error on page {p_num}: {e}")
                    page_specs[p_num - 1] = PageSpec(page_number=p_num)

    # ── Step 3: Assemble DocumentSpec ──
    assembled_pages = [ps for ps in page_specs if ps is not None]
    doc_spec = DocumentSpec(
        title=doc_title,
        theme_hex=theme_hex,
        pages=assembled_pages,
    )

    # Save AST if requested
    if save_ast or ast_path is not None:
        target_ast = Path(ast_path) if ast_path else (output_path.parent / f"{output_path.stem}_ast.json")
        target_ast.parent.mkdir(parents=True, exist_ok=True)
        target_ast.write_text(doc_spec.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"AST saved to: {target_ast}")

    # ── Step 4: Compile to DOCX ──
    logger.info("Compiling DOCX...")
    compiler = DocxCompiler(doc_spec)
    result = compiler.compile(output_path, assets_dir=assets_dir)
    logger.info(f"Created: {result}")

    return result

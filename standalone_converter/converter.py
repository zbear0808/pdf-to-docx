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

from .ir_schema import DocumentSpec, PageSpec, ImageBlock
from .pdf_extractor import PDFExtractor
from .page_parser import PageParser
from .docx_compiler import DocxCompiler

logger = logging.getLogger(__name__)


def _backfill_page_typography(page_spec: PageSpec, typo: Dict[str, Any]):
    """Enriches PageSpec with exact PDF geometry and text span typography."""
    page_spec.width_pt = typo.get("width_pt", page_spec.width_pt)
    page_spec.height_pt = typo.get("height_pt", page_spec.height_pt)
    page_spec.margin_top_pt = typo.get("margin_top_pt")
    page_spec.margin_bottom_pt = typo.get("margin_bottom_pt")
    page_spec.margin_left_pt = typo.get("margin_left_pt")
    page_spec.margin_right_pt = typo.get("margin_right_pt")

    pdf_spans = typo.get("spans", [])
    if not pdf_spans:
        return

    span_lookup = {}
    for s in pdf_spans:
        k = s["text"].strip().lower()[:15]
        if k and k not in span_lookup:
            span_lookup[k] = s

    for block in page_spec.blocks:
        b_type = getattr(block, "type", "")
        if b_type == "paragraph":
            if getattr(block, "space_after_pt", None) is None:
                block.space_after_pt = 2.0
            if getattr(block, "line_spacing", None) is None:
                block.line_spacing = 1.05

        runs = getattr(block, "runs", None) or []
        for run in runs:
            r_text = getattr(run, "text", "").strip()
            if not r_text:
                continue
            k = r_text.lower()[:15]
            matched_span = span_lookup.get(k)
            if not matched_span:
                for s in pdf_spans:
                    if s["text"] in r_text or r_text in s["text"]:
                        matched_span = s
                        break
            if matched_span:
                if getattr(run, "font_size_pt", None) is None:
                    run.font_size_pt = matched_span["size"]
                if not getattr(run, "font_name", None):
                    run.font_name = matched_span["font"]
                if matched_span.get("flags", 0) & 2:
                    run.bold = True
                if matched_span.get("flags", 0) & 1:
                    run.italic = True


def _process_single_page(
    parser: PageParser,
    extractor: PDFExtractor,
    page_number: int,
    page_png: Path,
    assets_dir: Path,
) -> PageSpec:
    """Processes a single page: parse layout via Gemini, crop assets, and backfill typography."""
    try:
        logger.info(f"Parsing page {page_number}...")
        page_spec = parser.parse_page(page_png, page_number=page_number)

        # Backfill exact typography and page margins from PDF content stream
        try:
            typo = extractor.get_page_typography(page_number)
            _backfill_page_typography(page_spec, typo)
        except Exception as typo_err:
            logger.debug(f"Typography extraction skipped for page {page_number}: {typo_err}")

        # Resolve image and figure blocks using multi-modal asset harvester
        for block_idx, block in enumerate(page_spec.blocks):
            b_type = getattr(block, "type", "")
            bbox = getattr(block, "bbox", None)

            if b_type == "image" and bbox:
                crop_dest = assets_dir / f"p{page_number}_img{block_idx}.png"
                try:
                    res = extractor.resolve_asset(
                        page_number,
                        [bbox.ymin, bbox.xmin, bbox.ymax, bbox.xmax],
                        output_path=crop_dest,
                        dpi=300,
                    )
                    block.image_path = res["image_path"]
                    block.width_inches = res["width_inches"]
                    block.height_inches = res["height_inches"]
                    logger.info(
                        f"  Resolved visual asset ({res['source']}): {block.image_path} "
                        f"({block.width_inches}x{block.height_inches} in)"
                    )
                except Exception as crop_err:
                    logger.warning(f"  Failed to resolve asset on page {page_number}, block {block_idx}: {crop_err}")

            elif b_type == "chart" and bbox:
                crop_dest = assets_dir / f"p{page_number}_chart_asset{block_idx}.png"
                try:
                    res = extractor.resolve_asset(
                        page_number,
                        [bbox.ymin, bbox.xmin, bbox.ymax, bbox.xmax],
                        output_path=crop_dest,
                        dpi=300,
                    )
                    if res["source"] in ("native_image", "vector_cluster"):
                        logger.info(
                            f"  Preserving native chart graphic ({res['source']}) on page {page_number} "
                            f"instead of synthesizing: {res['image_path']}"
                        )
                        page_spec.blocks[block_idx] = ImageBlock(
                            type="image",
                            image_path=res["image_path"],
                            caption=getattr(block, "title", None),
                            width_inches=res["width_inches"],
                            height_inches=res["height_inches"],
                            bbox=bbox,
                        )
                except Exception as chart_err:
                    logger.debug(f"  Chart resolution check skipped: {chart_err}")

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
        logger.error(f"Page {page_number} parsing failed: {e}. Falling back to PDF text streams.")
        blocks = []
        try:
            page = extractor.doc[page_number - 1]
            raw_blocks = page.get_text("blocks")
            for b in raw_blocks:
                if b[6] == 0:  # text
                    txt = b[4].strip()
                    if txt:
                        from .ir_schema import ParagraphBlock, TextRun
                        blocks.append(ParagraphBlock(
                            type="paragraph",
                            runs=[TextRun(text=txt)],
                            space_after_pt=2.0,
                        ))
        except Exception as fb_err:
            logger.error(f"Fallback extraction failed on page {page_number}: {fb_err}")
        return PageSpec(page_number=page_number, blocks=blocks)


def convert_pdf_to_docx(
    pdf_path: str | Path,
    output_path: str | Path = "output.docx",
    *,
    api_key: Optional[str] = None,
    model_name: str = "gemini--flash-lite-latest",
    request_delay: float = 0.0,
    max_workers: int = 4,
    dpi: int = 200,
    title: Optional[str] = None,
    theme_hex: str = "#000000",
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
        model_name: Gemini model to use. Default is gemini--flash-lite-latest.
        max_workers: Max concurrent page parsing threads. Default 4.
        dpi: Resolution for page rendering. Default 200.
        title: Document title. Defaults to the PDF filename stem.
        theme_hex: Theme color hex (default "#000000" for neutral/source-faithful typography).
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
        parser = PageParser(api_key=api_key, model_name=model_name, delay_between_requests=request_delay)
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

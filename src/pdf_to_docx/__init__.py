"""PDF to DOCX Conversion Package."""

from .ir_schema import (
    Alignment,
    BoundingBox,
    ChartBlock,
    ChartSeries,
    ChartType,
    DocumentBlock,
    DocumentSpec,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageBreakBlock,
    PageSpec,
    ParagraphBlock,
    TableBlock,
    TableCell,
    TextRun,
)
from .pdf_extractor import PDFExtractor
from .layout_parser import LayoutParser
from .docx_compiler import DocxCompiler
from .chart_generator import render_chart_image, to_docx_mcp_chart_args
from .visual_diff import VisualDiffInspector, render_docx_to_png
from .cli import app, main

__all__ = [
    "Alignment",
    "BoundingBox",
    "ChartBlock",
    "ChartSeries",
    "ChartType",
    "DocumentBlock",
    "DocumentSpec",
    "HeadingBlock",
    "ImageBlock",
    "ListType",
    "PageBreakBlock",
    "PageSpec",
    "ParagraphBlock",
    "TableBlock",
    "TableCell",
    "TextRun",
    "PDFExtractor",
    "LayoutParser",
    "DocxCompiler",
    "render_chart_image",
    "to_docx_mcp_chart_args",
    "VisualDiffInspector",
    "render_docx_to_png",
    "app",
    "main",
]

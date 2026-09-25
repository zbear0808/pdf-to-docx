"""PDF to LaTeX conversion package.

Reuses the unified document extraction pipeline from pdf_to_docx and compiles
canonical AST specs into publication-grade LaTeX (.tex) and PDFs.
"""

from pdf_to_docx.ir_schema import (
    Alignment,
    BoundingBox,
    BoxBlock,
    ChartBlock,
    ChartSeries,
    ChartType,
    CodeBlock,
    DocumentBlock,
    DocumentClass,
    DocumentSpec,
    EquationBlock,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageBreakBlock,
    PageSpec,
    ParagraphBlock,
    QuestionBlock,
    QuestionChoice,
    TableBlock,
    TableCell,
    TextRun,
)
from pdf_to_docx.pdf_extractor import PDFExtractor
from pdf_to_docx.layout_parser import LayoutParser
from pdf_to_docx.chart_generator import render_chart_image

from .latex_compiler import LatexCompiler, compile_tex_to_pdf, escape_latex_text, find_latex_compiler
from .cli import main

__all__ = [
    "Alignment",
    "BoundingBox",
    "BoxBlock",
    "ChartBlock",
    "ChartSeries",
    "ChartType",
    "CodeBlock",
    "DocumentBlock",
    "DocumentClass",
    "DocumentSpec",
    "EquationBlock",
    "HeadingBlock",
    "ImageBlock",
    "LatexCompiler",
    "LayoutParser",
    "ListType",
    "PDFExtractor",
    "PageBreakBlock",
    "PageSpec",
    "ParagraphBlock",
    "QuestionBlock",
    "QuestionChoice",
    "TableBlock",
    "TableCell",
    "TextRun",
    "compile_tex_to_pdf",
    "escape_latex_text",
    "find_latex_compiler",
    "main",
    "render_chart_image",
]


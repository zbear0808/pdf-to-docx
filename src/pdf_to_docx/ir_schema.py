"""Unified Intermediate Representation (IR) Schema for Document Conversion.

Defines the strongly-typed Abstract Syntax Tree (AST) representing a document.
Extracted once from the input PDF by multimodal page subagents, this canonical
format is deterministically compiled into either:
  1. Professional Word documents (.docx) via DocxCompiler
  2. Publication-grade LaTeX documents (.tex / .pdf) via LatexCompiler
"""

from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class DocumentClass(str, Enum):
    ARTICLE = "article"
    REPORT = "report"
    EXAM = "exam"
    SCRARTCL = "scrartcl"


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class ListType(str, Enum):
    BULLET = "bullet"
    NUMBERED = "numbered"
    DESCRIPTION = "description"
    NONE = "none"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    AREA = "area"


class TextRun(BaseModel):
    """A styled fragment of text within a paragraph, table cell, or callout box."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    color_hex: Optional[str] = None  # e.g., "#1F4E79"
    font_size_pt: Optional[float] = None
    font_name: Optional[str] = None
    superscript: bool = False
    subscript: bool = False
    code: bool = False
    is_math: bool = False  # True for raw mathematical formulas (e.g. \frac{a}{b}, x_i)


class BoundingBox(BaseModel):
    """Normalized bounding box coordinates on a 0-1000 scale [ymin, xmin, ymax, xmax]."""
    ymin: int = Field(..., ge=0, le=1000)
    xmin: int = Field(..., ge=0, le=1000)
    ymax: int = Field(..., ge=0, le=1000)
    xmax: int = Field(..., ge=0, le=1000)

    @property
    def height_ratio(self) -> float:
        return (self.ymax - self.ymin) / 1000.0

    @property
    def width_ratio(self) -> float:
        return (self.xmax - self.xmin) / 1000.0


class HeadingBlock(BaseModel):
    """Section heading with hierarchical level."""
    type: str = "heading"
    level: int = Field(1, ge=1, le=4)
    text: str
    runs: Optional[List[TextRun]] = None
    alignment: Alignment = Alignment.LEFT
    numbered: bool = True
    bbox: Optional[BoundingBox] = None


class ParagraphBlock(BaseModel):
    """Narrative text block with optional runs, list formatting, and callout styling."""
    type: str = "paragraph"
    runs: List[TextRun] = Field(default_factory=list)
    alignment: Alignment = Alignment.LEFT
    list_type: ListType = ListType.NONE
    list_level: int = 0
    is_callout: bool = False
    callout_color_hex: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class EquationBlock(BaseModel):
    """Dedicated mathematical display equation block."""
    type: str = "equation"
    latex_code: str  # Raw LaTeX math without outer delimiters, e.g. "z = \frac{x - \mu}{\sigma}"
    numbered: bool = False
    label: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class TableCell(BaseModel):
    """A single cell inside a table."""
    text: str = ""
    runs: Optional[List[TextRun]] = None
    bg_color_hex: Optional[str] = None
    bold: bool = False
    italic: bool = False
    alignment: Alignment = Alignment.LEFT
    col_span: int = 1
    row_span: int = 1


class TableBlock(BaseModel):
    """Structured table block."""
    type: str = "table"
    caption: Optional[str] = None
    headers: List[str] = Field(default_factory=list)
    header_cells: Optional[List[TableCell]] = None
    rows: List[List[str]] = Field(default_factory=list)
    row_cells: Optional[List[List[TableCell]]] = None
    col_alignments: Optional[List[Alignment]] = None
    col_widths_pct: Optional[List[float]] = None  # e.g. [30.0, 35.0, 35.0]
    cant_split: bool = True  # Prevent row break across page boundaries (Word)
    repeat_header: bool = True  # Repeat header row if table crosses page
    style_name: Optional[str] = "Table Grid"
    booktabs: bool = True  # Professional table styling (LaTeX)
    full_width: bool = False
    bbox: Optional[BoundingBox] = None


class ChartSeries(BaseModel):
    name: str
    values: List[float]


class ChartBlock(BaseModel):
    """Chart or data visualization."""
    type: str = "chart"
    title: str
    chart_type: ChartType = ChartType.BAR
    categories: List[str] = Field(default_factory=list)
    series: List[ChartSeries] = Field(default_factory=list)
    reproduce_programmatically: bool = True
    generated_image_path: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    width_inches: float = 5.5
    height_inches: float = 3.5
    caption: Optional[str] = None


class ImageBlock(BaseModel):
    """Raster image or vector drawing extracted from PDF."""
    type: str = "image"
    image_path: str = ""
    caption: Optional[str] = None
    label: Optional[str] = None
    alt_text: Optional[str] = None
    width_inches: float = 5.5
    height_inches: Optional[float] = None
    width_ratio: float = 0.8
    alignment: Alignment = Alignment.CENTER
    bbox: Optional[BoundingBox] = None
    is_vector: bool = False


class BoxBlock(BaseModel):
    """Framed callout or response box (tcolorbox in LaTeX / shaded frame in Word)."""
    type: str = "box"
    title: Optional[str] = None
    content: List[ParagraphBlock] = Field(default_factory=list)
    color_hex: str = "#1F4E79"
    height_pt: Optional[float] = None
    empty_for_response: bool = False
    bbox: Optional[BoundingBox] = None


class QuestionChoice(BaseModel):
    """Multiple choice option."""
    label: str  # "(A)", "(B)", "(C)", etc.
    text: str
    runs: Optional[List[TextRun]] = None


class QuestionBlock(BaseModel):
    """Specialized block for exam / quiz problems."""
    type: str = "question"
    number: Optional[int] = None
    part: Optional[str] = None  # "a", "b", "c", etc.
    points: Optional[int] = None
    prompt: List[ParagraphBlock] = Field(default_factory=list)
    choices: Optional[List[QuestionChoice]] = None
    response_box_height_pt: Optional[float] = None
    solution: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class CodeBlock(BaseModel):
    """Verbatim or syntax-highlighted code block."""
    type: str = "code"
    language: Optional[str] = None
    code: str
    caption: Optional[str] = None


class PageBreakBlock(BaseModel):
    """Explicit page break."""
    type: str = "page_break"


DocumentBlock = Union[
    HeadingBlock,
    ParagraphBlock,
    EquationBlock,
    TableBlock,
    ChartBlock,
    ImageBlock,
    BoxBlock,
    QuestionBlock,
    CodeBlock,
    PageBreakBlock,
]


class PageSpec(BaseModel):
    """Specification for a single document page."""
    page_number: int
    width_pt: float = 612.0  # Standard letter (8.5 x 11 in points)
    height_pt: float = 792.0
    orientation: str = "portrait"  # portrait | landscape
    blocks: List[DocumentBlock] = Field(default_factory=list)


class DocumentSpec(BaseModel):
    """Root canonical representation of the entire document."""
    title: str = "Converted Document"
    author: Optional[str] = None
    company: Optional[str] = None
    date: Optional[str] = None
    document_class: DocumentClass = DocumentClass.ARTICLE
    font_size: str = "11pt"
    paper_size: str = "letterpaper"
    margins_in: float = 1.0
    theme_hex: str = "#1F4E79"
    default_font: str = "Calibri"
    default_font_size_pt: float = 11.0
    custom_preamble: Optional[str] = None
    pages: List[PageSpec] = Field(default_factory=list)


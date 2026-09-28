"""Intermediate Representation (IR) Schema for Document Conversion.

Defines the strongly-typed AST representing a document.
Extracted once from input PDF pages via Gemini Flash Lite,
then deterministically compiled into Word (.docx).
"""

from __future__ import annotations
from enum import Enum
from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field


class Alignment(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    JUSTIFY = "justify"


class ListType(str, Enum):
    BULLET = "bullet"
    NUMBERED = "numbered"
    NONE = "none"


class ChartType(str, Enum):
    BAR = "bar"
    LINE = "line"
    PIE = "pie"


class TextRun(BaseModel):
    """A styled fragment of text within a paragraph or table cell."""
    text: str
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strike: bool = False
    color_hex: Optional[str] = None
    font_size_pt: Optional[float] = None
    font_name: Optional[str] = None
    superscript: bool = False
    subscript: bool = False


class BoundingBox(BaseModel):
    """Normalized bounding box on 0-1000 scale [ymin, xmin, ymax, xmax]."""
    ymin: int = Field(..., ge=0, le=1000)
    xmin: int = Field(..., ge=0, le=1000)
    ymax: int = Field(..., ge=0, le=1000)
    xmax: int = Field(..., ge=0, le=1000)


class HeadingBlock(BaseModel):
    """Section heading with hierarchical level."""
    type: str = "heading"
    level: int = Field(1, ge=1, le=4)
    text: str
    runs: Optional[List[TextRun]] = None
    alignment: Alignment = Alignment.LEFT
    bbox: Optional[BoundingBox] = None


class ParagraphBlock(BaseModel):
    """Text block with optional runs, list formatting, and callout styling."""
    type: str = "paragraph"
    runs: List[TextRun] = Field(default_factory=list)
    alignment: Alignment = Alignment.LEFT
    list_type: ListType = ListType.NONE
    list_level: int = 0
    is_callout: bool = False
    callout_color_hex: Optional[str] = None
    line_spacing: Optional[float] = None
    space_before_pt: Optional[float] = None
    space_after_pt: Optional[float] = None
    bbox: Optional[BoundingBox] = None


class TableBlock(BaseModel):
    """Structured table block."""
    type: str = "table"
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    col_widths_pct: Optional[List[float]] = None
    col_alignments: Optional[List[Alignment]] = None
    cant_split: bool = True
    repeat_header: bool = True
    style_name: Optional[str] = "Table Grid"
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
    generated_image_path: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    width_inches: float = 5.5
    height_inches: float = 3.5


class ImageBlock(BaseModel):
    """Raster image or vector drawing extracted from PDF."""
    type: str = "image"
    image_path: str = ""
    caption: Optional[str] = None
    width_inches: Optional[float] = None
    height_inches: Optional[float] = None
    alignment: Alignment = Alignment.CENTER
    bbox: Optional[BoundingBox] = None


class EquationBlock(BaseModel):
    """Dedicated mathematical display equation block."""
    type: str = "equation"
    latex_code: str
    numbered: bool = False
    label: Optional[str] = None
    bbox: Optional[BoundingBox] = None


class BoxBlock(BaseModel):
    """Framed callout or response box."""
    type: str = "box"
    title: Optional[str] = None
    content: List[ParagraphBlock] = Field(default_factory=list)
    color_hex: str = "#000000"
    height_pt: Optional[float] = None
    empty_for_response: bool = False
    bbox: Optional[BoundingBox] = None


class QuestionChoice(BaseModel):
    """Multiple choice option."""
    label: str
    text: str
    runs: Optional[List[TextRun]] = None


class QuestionBlock(BaseModel):
    """Specialized block for exam / quiz problems."""
    type: str = "question"
    number: Optional[int] = None
    part: Optional[str] = None
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
    TableBlock,
    ChartBlock,
    ImageBlock,
    EquationBlock,
    BoxBlock,
    QuestionBlock,
    CodeBlock,
    PageBreakBlock,
]


class PageSpec(BaseModel):
    """Specification for a single document page."""
    page_number: int = 1
    width_pt: float = 612.0
    height_pt: float = 792.0
    orientation: str = "portrait"
    margin_top_pt: Optional[float] = None
    margin_bottom_pt: Optional[float] = None
    margin_left_pt: Optional[float] = None
    margin_right_pt: Optional[float] = None
    blocks: List[DocumentBlock] = Field(default_factory=list)


class DocumentSpec(BaseModel):
    """Root canonical representation of the entire document."""
    title: str = "Converted Document"
    theme_hex: str = "#000000"
    default_font: str = "Calibri"
    default_font_size_pt: float = 11.0
    margins_in: Optional[float] = None
    pages: List[PageSpec] = Field(default_factory=list)

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
    bbox: Optional[BoundingBox] = None


class TableBlock(BaseModel):
    """Structured table block."""
    type: str = "table"
    headers: List[str] = Field(default_factory=list)
    rows: List[List[str]] = Field(default_factory=list)
    col_widths_pct: Optional[List[float]] = None
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
    width_inches: float = 5.5
    height_inches: Optional[float] = None
    alignment: Alignment = Alignment.CENTER
    bbox: Optional[BoundingBox] = None


class PageBreakBlock(BaseModel):
    """Explicit page break."""
    type: str = "page_break"


DocumentBlock = Union[
    HeadingBlock,
    ParagraphBlock,
    TableBlock,
    ChartBlock,
    ImageBlock,
    PageBreakBlock,
]


class PageSpec(BaseModel):
    """Specification for a single document page."""
    page_number: int = 1
    width_pt: float = 612.0
    height_pt: float = 792.0
    orientation: str = "portrait"
    blocks: List[DocumentBlock] = Field(default_factory=list)


class DocumentSpec(BaseModel):
    """Root canonical representation of the entire document."""
    title: str = "Converted Document"
    theme_hex: str = "#000000"
    default_font: str = "Calibri"
    default_font_size_pt: float = 11.0
    pages: List[PageSpec] = Field(default_factory=list)

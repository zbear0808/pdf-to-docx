"""Intermediate Representation (IR) Schema for PDF to DOCX compilation.

Defines the strongly-typed Abstract Syntax Tree (AST) representing a document.
The LLM extracts PDF pages into this canonical format, which is then deterministically
compiled into a professional Word document.
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
    SCATTER = "scatter"
    AREA = "area"


class TextRun(BaseModel):
    """A styled fragment of text within a paragraph or cell."""
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
    level: int = Field(1, ge=1, le=6)
    text: str
    runs: Optional[List[TextRun]] = None
    alignment: Alignment = Alignment.LEFT
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


class TableCell(BaseModel):
    """A single cell inside a table."""
    text: str = ""
    runs: Optional[List[TextRun]] = None
    bg_color_hex: Optional[str] = None
    bold: bool = False
    alignment: Alignment = Alignment.LEFT
    col_span: int = 1
    row_span: int = 1


class TableBlock(BaseModel):
    """Structured table block."""
    type: str = "table"
    headers: List[str] = Field(default_factory=list)
    header_cells: Optional[List[TableCell]] = None
    rows: List[List[str]] = Field(default_factory=list)
    row_cells: Optional[List[List[TableCell]]] = None
    col_widths_pct: Optional[List[float]] = None  # e.g. [30.0, 35.0, 35.0]
    cant_split: bool = True  # Prevent row break across page boundaries
    repeat_header: bool = True  # Repeat header row if table crosses page
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
    reproduce_programmatically: bool = True
    generated_image_path: Optional[str] = None
    bbox: Optional[BoundingBox] = None
    width_inches: float = 6.0
    height_inches: float = 3.5


class ImageBlock(BaseModel):
    """Raster image or vector drawing extracted from PDF."""
    type: str = "image"
    image_path: str = ""
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    width_inches: float = 5.5
    height_inches: Optional[float] = None
    bbox: Optional[BoundingBox] = None
    is_vector: bool = False


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
    theme_hex: str = "#1F4E79"  # Default corporate navy
    default_font: str = "Calibri"
    default_font_size_pt: float = 11.0
    pages: List[PageSpec] = Field(default_factory=list)

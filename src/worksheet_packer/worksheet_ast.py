"""Worksheet AST Schema.

Defines the strongly-typed Abstract Syntax Tree (AST) representing a worksheet.
Provides problem-oriented semantics with ordering constraints (strict vs flexible),
image attachments, workspace budgeting, and layout decisions for space-efficient 2D packing.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

# Re-use foundational typography types from the core IR schema
from pdf_to_docx.ir_schema import TextRun, QuestionChoice


class SectionOrdering(str, Enum):
    """Ordering constraint within a worksheet section."""
    STRICT = "strict"        # Problems must be rendered in their exact given sequence
    FLEXIBLE = "flexible"    # Problems can be reordered/packed to optimize space utilization


class LayoutHint(str, Enum):
    """User or heuristic hint for problem layout."""
    AUTO = "auto"
    SIDE_BY_SIDE = "side_by_side"   # Force question text and diagram side-by-side
    STACKED = "stacked"             # Force question text above diagram
    FULL_WIDTH = "full_width"       # Force spanning across all columns in multi-column mode


class LayoutDecision(str, Enum):
    """Actual layout chosen by the packing engine."""
    SIDE_BY_SIDE = "side_by_side"
    STACKED = "stacked"
    TEXT_ONLY = "text_only"
    IMAGE_ONLY = "image_only"


class WorkspaceType(str, Enum):
    """Type of student work area under a problem."""
    LINES = "lines"          # Blank answer/work lines (underline style)
    GRID = "grid"            # Coordinate or graph grid
    BOX = "box"              # Framed empty response rectangle
    BLANK = "blank"          # Pure whitespace gap
    NONE = "none"            # Multiple choice or inline question with no extra work space


class WorkspaceConfig(BaseModel):
    """Configuration for problem workspace / student answer area."""
    type: WorkspaceType = WorkspaceType.LINES
    lines: int = 3
    height_pt: Optional[float] = None
    fill_remaining: bool = False   # True if this problem should expand to fill trailing whitespace


class ProblemImage(BaseModel):
    """Raster image or diagram attached to a problem."""
    media_path: str
    native_width_px: int = 0
    native_height_px: int = 0
    aspect_ratio: float = 1.0       # Height / Width (H / W)
    auto_cropped: bool = False
    caption: Optional[str] = None
    alt_text: Optional[str] = None
    bbox: Optional[List[int]] = None  # Normalized [ymin, xmin, ymax, xmax] 0-1000 in original PDF

    # Dynamic scale bounds and content classification
    source_width_in: Optional[float] = None
    source_height_in: Optional[float] = None
    min_width_in: float = 1.0          # Hard legibility floor in inches
    max_width_in: float = 3.5          # Hard aesthetic ceiling in inches
    preferred_width_in: float = 2.0    # Target aesthetic width in inches
    has_fine_text: bool = True         # True if diagram contains fine labels, angles, equations
    category: str = "detailed_diagram" # "formula_icon", "compact_shape", "detailed_diagram", "wide_grid"
    elasticity: float = 1.0            # Compressibility factor: 0.0 (rigid) to 1.0 (fully compressible)


class Problem(BaseModel):
    """Individual question or problem on a worksheet."""
    id: str
    number: Optional[int] = None
    part: Optional[str] = None          # "a", "b", "i", "ii", etc.
    points: Optional[int] = None
    prompt_text: str = ""
    prompt_runs: List[TextRun] = Field(default_factory=list)
    image: Optional[ProblemImage] = None
    choices: Optional[List[QuestionChoice]] = None
    workspace: WorkspaceConfig = Field(default_factory=WorkspaceConfig)
    layout_hint: LayoutHint = LayoutHint.AUTO
    min_rendered_width_in: float = 1.5  # Diagram won't be shrunk below this width
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

    @property
    def effective_min_image_width_in(self) -> float:
        """Returns the lower legibility bound for image width in inches."""
        if self.image and self.image.min_width_in is not None:
            return self.image.min_width_in
        return self.min_rendered_width_in

    @property
    def full_label(self) -> str:
        """Returns formatted question prefix, e.g. '1.', '2.(a)', or '(b)'."""
        prefix = ""
        if self.number is not None:
            prefix += f"{self.number}."
        if self.part:
            prefix += f"({self.part})" if prefix else f"({self.part})"
        if self.points:
            prefix += f" [{self.points} pts]"
        return prefix.strip()


class WorksheetSection(BaseModel):
    """Named grouping of problems with distinct layout or ordering rules."""
    id: str
    title: Optional[str] = None
    instructions: Optional[str] = None
    ordering: SectionOrdering = SectionOrdering.STRICT
    column_mode: Optional[str] = None   # "single", "double", or None (inherits from worksheet)
    problems: List[Problem] = Field(default_factory=list)


class PageMargins(BaseModel):
    """Page margins in inches."""
    top_in: float = 0.5
    bottom_in: float = 0.5
    left_in: float = 0.5
    right_in: float = 0.5


class WorksheetSpec(BaseModel):
    """Root canonical representation of a worksheet before layout packing."""
    title: str = "Worksheet"
    subtitle: Optional[str] = None
    header_left: Optional[str] = None
    header_center: Optional[str] = None
    header_right: Optional[str] = "Name: ______________________ Date: ________ Period: ____"
    page_width_in: float = 8.5
    page_height_in: float = 11.0
    margins: PageMargins = Field(default_factory=PageMargins)
    default_columns: int = 2            # 1 or 2
    column_gap_in: float = 0.3          # Gap between columns in multi-column mode
    theme_hex: str = "#1F4E79"
    default_font: str = "Calibri"
    default_font_size_pt: float = 10.5
    sections: List[WorksheetSection] = Field(default_factory=list)

    @property
    def printable_width_in(self) -> float:
        return self.page_width_in - (self.margins.left_in + self.margins.right_in)

    @property
    def printable_height_in(self) -> float:
        return self.page_height_in - (self.margins.top_in + self.margins.bottom_in)


class PlacedProblem(BaseModel):
    """A problem assigned to a specific page, column, and geometry footprint."""
    problem: Problem
    layout: LayoutDecision
    page_index: int                     # 1-indexed page
    col_index: int                      # 0 (left/single), 1 (right)
    x_in: float
    y_in: float
    width_in: float
    height_in: float
    image_render_width_in: float = 0.0
    image_render_height_in: float = 0.0
    text_render_width_in: float = 0.0
    text_render_height_in: float = 0.0
    workspace_height_in: float = 0.0


class PlacedSectionHeader(BaseModel):
    """Section title / instructions placed on a page."""
    section_id: str
    title: Optional[str] = None
    instructions: Optional[str] = None
    page_index: int = 1
    y_in: float = 0.0
    height_in: float = 0.0
    span_all_columns: bool = True


PlacedItem = Union[PlacedProblem, PlacedSectionHeader]


class PlacedPage(BaseModel):
    """A single page containing positioned items."""
    page_index: int
    items: List[PlacedItem] = Field(default_factory=list)


class RenderPlan(BaseModel):
    """Complete layout plan ready for deterministic DOCX or LaTeX rendering."""
    worksheet: WorksheetSpec
    pages: List[PlacedPage] = Field(default_factory=list)
    total_pages: int = 0
    stats: Dict[str, Any] = Field(default_factory=dict)


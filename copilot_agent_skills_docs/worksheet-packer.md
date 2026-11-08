# Skill: worksheet-packer

## Description

_Source: `C:\Users\zubair\Documents\GitHub\pdf-to-docx\.agents\skills\worksheet-packer\SKILL.md`

```markdown
---
name: worksheet-packer
description: >-
  Parses, reorganizes, and packs worksheet and exam documents (PDF or Word .docx) into space-efficient,
  beautifully formatted Word (.docx) and LaTeX (.tex / .pdf) files using 2D bin packing,
  whitespace auto-cropping, and side-by-side minipage/table layouts. Use when converting, compacting, or
  re-formatting worksheets, problem sets, quizzes, or exams with excessive whitespace.
---

# Worksheet Packer Skill

This skill provides autonomous and surgical workflows for parsing, restructuring, and re-packing problem sets, worksheets, quizzes, and exams into dense, space-efficient Microsoft Word (`.docx`) and LaTeX (`.tex` / `.pdf`) documents.

---

## The Whitespace Problem & Solution

Standard worksheets often waste massive horizontal whitespace—for example, placing a 2-inch geometric diagram on its own vertical row with 4.5 inches of blank space next to it. 

**Worksheet Packer** eliminates this by:
1. **Perception**: Extracting problem prompts, multiple-choice choices, student answer areas, and attached diagrams from PDF or existing Word (`.docx`) documents.
2. **Auto-Cropping**: Trimming white and transparent borders from diagram images so footprint calculations reflect the true visual drawing rather than margin padding.
3. **Empty Space Workspaces**:
   - **No Blank Underlines**: Never generate blank underlines (`_______` or `\hrule`) for student work areas. Blank underlines constrain handwriting, look dated, and waste vertical space.
   - **Clean Whitespace Budgeting**: Use `WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=...)` or `approx_workspace_in=...` on `Problem`.
   - **2D Area Budgeting**: Use `approx_area_sq_in` so student work space automatically adapts its height when toggling between 1-column and 2-column layouts.
4. **2D Bin-Packing & Column Balancing Layout Engine**:
   - **Balanced Multi-Column Splits**: Automatically splits problems evenly across columns on each page (e.g. 3 questions in Column 0 and 3 questions in Column 1, instead of greedy 5-and-1 or 4-and-2 imbalances).
   - **Even Vertical Spacing Distribution**: Calculates vertical slack in each column and distributes it into inter-problem spacing (`spacing_after_in` up to 0.45 in / ~32 pt) so questions comfortably fill the page without awkward voids.
   - **Side-by-Side vs Stacked**: Heuristically routing square-ish or portrait diagrams ($0.55 \le AR \le 1.50$) into **Side-by-Side** (65% text / 35% diagram) containers, and wide diagrams into **Stacked** containers.
5. **Deterministic Structural Rendering**:
   - **DOCX**: Invisible borderless tables with OpenXML `w:cantSplit` on every row guarantee that diagrams, text, and workspaces stay strictly locked together without mid-problem page breaks or jumping floating anchors. Explicit `WD_BREAK.COLUMN` breaks guarantee balanced column transitions.
   - **LaTeX**: `minipage` environments with `multicol` and `tcolorbox`, inserting explicit `\columnbreak` to preserve balanced multi-column splits.

---

## When to Use This Skill

- When a user asks to convert an exam, quiz, or worksheet PDF into Word or LaTeX with optimal use of whitespace.
- When an existing Word document (`.docx`) has excessive whitespace, sprawling pages, or disorganized floating images that need to be re-packed into a compact 1- or 2-column format.
- When grouping problems where order does not matter (`SectionOrdering.FLEXIBLE`) to pack problems into the minimum possible page count.
- When preserving exact problem sequence (`SectionOrdering.STRICT`) while still compacting diagrams side-by-side with question text.

---

## Directory Layout & Workspace Hygiene

All worksheet packing workflows must store deliverables in `output/` and all intermediate diagrams, page renderings, and specs in `_temp/`:
```text
<document_workspace>/
├── output/                 # Final packed deliverables (.docx, .pdf, .tex)
└── _temp/                  # ALL temporary & intermediate working files
    ├── assets/             # Extracted & auto-cropped diagrams/figures
    ├── renders/            # Page preview images (orig_p*.png, docx_p*.png)
    ├── specs/              # Intermediate specs & plans (spec.json, plan.json)
    └── build/              # LaTeX compile logs (.aux, .log, .fls), temp runner scripts
```

---

## Workflow 1: End-to-End PDF Worksheet Conversion

Run the autonomous CLI pipeline:

```bash
# Convert PDF to space-optimized 2-column Word document in output/
uv run worksheet-packer convert "path/to/worksheet.pdf" --columns 2 --format docx -o output/optimized_worksheet.docx

# Convert PDF to LaTeX and compile PDF in output/
uv run worksheet-packer convert "path/to/worksheet.pdf" --columns 2 --format pdf -o output/optimized_worksheet.pdf

# Save intermediate AST (spec.json) and layout plan (plan.json) into _temp/specs/
uv run worksheet-packer convert "path/to/worksheet.pdf" --columns 2 --save-ast -o output/optimized_worksheet.docx --workspace-dir _temp/
```

---

## Workflow 2: Re-Packing an Existing Word Document (.docx)

When an existing `.docx` worksheet needs to be compacted or reformatted:

### Phase A: Direct Autonomous Ingestion
`worksheet-packer` natively ingests `.docx` files:
1. Headlessly renders `.docx` pages to high-resolution PNGs via LibreOffice or Windows Word COM.
2. Extracts original native uncompressed assets from `word/media/` inside the `.docx` archive into `_temp/assets/`.
3. Uses Gemini multimodal vision to understand question boundaries, choices, and diagrams.
4. Packs and outputs a new compacted `.docx` (or `.tex`) into `output/`:

```bash
uv run worksheet-packer convert "path/to/messy_worksheet.docx" --columns 2 --format docx -o output/optimized_worksheet.docx
```

### Phase B: Visual-Inspection First Workflow
If the agent needs to inspect or critique the existing Word document before deciding on layout changes:
1. Prepare directories:
   ```bash
   mkdir -p output _temp/renders _temp/assets _temp/specs _temp/build
   ```
2. Render all pages of the Word doc to PNGs in `_temp/renders`:
   ```bash
   uv run worksheet-packer render-docx-pages "path/to/messy_worksheet.docx" -o _temp/renders
   ```
3. Inspect the rendered page images with multimodal vision to check question density.
4. Parse and generate the editable `WorksheetSpec` JSON:
   ```bash
   uv run worksheet-packer parse "path/to/messy_worksheet.docx" -o _temp/specs/spec.json --columns 2 --workspace-dir _temp/assets
   ```
5. Customize section ordering or hints in `_temp/specs/spec.json`:
   - Set `"ordering": "flexible"` on sections where problem order can be rearranged to fill columns.
   - Set `"ordering": "strict"` on sections where sequence must be preserved.
6. Pack and compile:
   ```bash
   uv run worksheet-packer pack _temp/specs/spec.json -o _temp/specs/plan.json
   uv run worksheet-packer render _temp/specs/plan.json -o output/optimized_worksheet.docx --format docx
   ```

---

## CLI Command Reference

| Command | Purpose | Key Flags |
| :--- | :--- | :--- |
| `info` | Inspect PDF, DOCX, or AST JSON | `<file_path>` |
| `parse` | Parse PDF or DOCX into `WorksheetSpec` JSON | `-o spec.json`, `-c 2`, `--ordering strict\|flexible` |
| `pack` | Run 2D bin packer on AST to create `RenderPlan` | `-o plan.json`, `-c 1\|2`, `--ordering strict\|flexible` |
| `render` | Compile `RenderPlan` or AST into DOCX/LaTeX | `-o output.docx`, `-f docx\|latex\|pdf` |
| `render-docx-pages` | Render all pages of a DOCX to PNG images | `<doc.docx> -o ./pages --dpi 200` |
| `convert` | Full autonomous pipeline (PDF/DOCX -> DOCX/LaTeX) | `--columns 2`, `--format docx\|latex\|both`, `--save-ast` |

---

## Python API Usage

```python
from worksheet_packer import (
    WorksheetSpec,
    WorksheetSection,
    Problem,
    ProblemImage,
    WorkspaceConfig,
    WorkspaceType,
    SectionOrdering,
    LayoutEngine,
    DocxWorksheetRenderer,
    LatexWorksheetRenderer,
    auto_crop_image,
)

# 1. Clean diagram whitespace
clean_path, w, h, ar = auto_crop_image("raw_diagram.png")

# 2. Build WorksheetSpec
spec = WorksheetSpec(
    title="AP Calculus Quiz",
    default_columns=2,
    sections=[
        WorksheetSection(
            id="s1",
            title="Part I: Related Rates",
            ordering=SectionOrdering.STRICT,  # or FLEXIBLE
            problems=[
                Problem(
                    id="q1",
                    number=1,
                    prompt_text="Find the rate of change of angle θ.",
                    image=ProblemImage(media_path=str(clean_path), native_width_px=w, native_height_px=h, aspect_ratio=ar),
                    workspace=WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=1.0),
                )
            ]
        )
    ]
)

# 3. 2D Bin-Packing Layout
engine = LayoutEngine(spec)
plan = engine.pack()

# 4. Render to DOCX (invisible tables w:cantSplit) or LaTeX (minipage)
DocxWorksheetRenderer(plan).render("quiz.docx")
LatexWorksheetRenderer(plan).render("quiz.tex", compile_pdf=True)
```


```

## Relevant Python Code


### src\worksheet_packer\__init__.py

```python
"""Worksheet Packer Package.

Parses worksheet PDFs, extracts problems and diagrams, and deterministically
compiles them into space-optimized DOCX and LaTeX documents using 2D bin packing.
"""

from .worksheet_ast import (
    LayoutDecision,
    LayoutHint,
    PlacedPage,
    PlacedProblem,
    PlacedSectionHeader,
    Problem,
    ProblemImage,
    RenderPlan,
    SectionOrdering,
    WorkspaceConfig,
    WorkspaceType,
    WorksheetSection,
    WorksheetSpec,
)
from .image_utils import auto_crop_image, inspect_diagram_dimensions, audit_image_boundaries, ImageBoundaryAuditor
from .layout_engine import LayoutEngine
from .docx_renderer import DocxWorksheetRenderer
from .latex_renderer import LatexWorksheetRenderer
from .worksheet_parser import WorksheetParser
from .docx_extractor import convert_docx_to_pdf, extract_docx_media, render_docx_pages
from .cli import app, main

__all__ = [
    "WorksheetSpec",
    "WorksheetSection",
    "Problem",
    "ProblemImage",
    "WorkspaceConfig",
    "WorkspaceType",
    "SectionOrdering",
    "LayoutHint",
    "LayoutDecision",
    "PlacedProblem",
    "PlacedSectionHeader",
    "PlacedPage",
    "RenderPlan",
    "auto_crop_image",
    "inspect_diagram_dimensions",
    "audit_image_boundaries",
    "ImageBoundaryAuditor",
    "convert_docx_to_pdf",
    "extract_docx_media",
    "render_docx_pages",
    "LayoutEngine",
    "DocxWorksheetRenderer",
    "LatexWorksheetRenderer",
    "WorksheetParser",
    "app",
    "main",
]


```

### src\worksheet_packer\worksheet_ast.py

```python
"""Worksheet AST Schema.

Defines the strongly-typed Abstract Syntax Tree (AST) representing a worksheet.
Provides problem-oriented semantics with ordering constraints (strict vs flexible),
image attachments, workspace budgeting, and layout decisions for space-efficient 2D packing.
"""

from __future__ import annotations
from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field, model_validator

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
    BLANK = "blank"          # Pure whitespace gap (recommended default - no underlines)
    LINES = "lines"          # Blank answer/work lines (deprecated in favor of pure whitespace)
    GRID = "grid"            # Coordinate or graph grid
    BOX = "box"              # Framed empty response rectangle
    NONE = "none"            # Multiple choice or inline question with no extra work space


class WorkspaceConfig(BaseModel):
    """Configuration for problem workspace / student answer area.
    
    Prefers clean empty whitespace over underlines. Can specify an exact height in inches
    (approx_height_in), a 2D area (approx_area_sq_in) that scales with column width,
    or a number of lines (approx 22pt / 0.3in each).
    """
    type: WorkspaceType = WorkspaceType.BLANK
    lines: int = 2
    height_pt: Optional[float] = None
    approx_height_in: Optional[float] = None   # Approximate vertical workspace height required in inches
    approx_area_sq_in: Optional[float] = None  # Approximate workspace area in square inches (scales by column width)
    fill_remaining: bool = False               # True if this problem should expand to fill trailing whitespace

    def effective_height_in(self, col_width_in: float = 3.5) -> float:
        """Calculates effective workspace height in inches given column width."""
        if self.type == WorkspaceType.NONE:
            return 0.0
        if self.approx_height_in is not None and self.approx_height_in > 0:
            return float(self.approx_height_in)
        if self.approx_area_sq_in is not None and self.approx_area_sq_in > 0:
            cw = max(0.5, col_width_in)
            return float(self.approx_area_sq_in / cw)
        if self.height_pt is not None and self.height_pt > 0:
            return float(self.height_pt / 72.0)
        if self.type == WorkspaceType.GRID:
            return 2.0  # Default 2 inches for coordinate planes
        if self.type == WorkspaceType.BOX:
            return max(1.0, (self.lines * 24.0) / 72.0)
        # BLANK (and legacy LINES): standard ~22 pt (approx 0.30 in) per line of writing whitespace
        return (max(1, self.lines) * 22.0) / 72.0


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
    approx_workspace_in: Optional[float] = None       # Top-level shortcut for workspace height in inches
    approx_workspace_area_sq_in: Optional[float] = None # Top-level shortcut for workspace area in sq inches
    layout_hint: LayoutHint = LayoutHint.AUTO
    min_rendered_width_in: float = 1.5  # Diagram won't be shrunk below this width
    extra_metadata: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _sync_workspace_dimensions(self) -> Problem:
        if self.approx_workspace_in is not None and self.approx_workspace_in > 0:
            if self.workspace.approx_height_in is None:
                self.workspace.approx_height_in = self.approx_workspace_in
        if self.approx_workspace_area_sq_in is not None and self.approx_workspace_area_sq_in > 0:
            if self.workspace.approx_area_sq_in is None:
                self.workspace.approx_area_sq_in = self.approx_workspace_area_sq_in
        return self

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


PART_PREFIX_RE = re.compile(
    r"^([a-zA-Z][\.\)]|\([a-zA-Z]\)|(?:i{1,3}|iv|v|vi{0,3}|ix|x)[\.\)]|\((?:i{1,3}|iv|v|vi{0,3}|ix|x)\))\s+(.*)$"
)


def parse_prompt_parts(text: str) -> List[Tuple[Optional[str], str]]:
    """Splits a question prompt into logical paragraphs and extracts sub-part labels.
    
    Returns:
        List of (part_label, text_content).
        part_label is non-empty (e.g. 'a.', '(b)') if this line starts a sub-part,
        or None for intro/general prompt text.
    """
    if not text:
        return []

    # Normalize inline sub-part breaks if not already newline-separated
    normalized = re.sub(r'(?<=[.!?])\s+([a-zA-Z][\.\)]\s+)', r'\n\1', text)
    lines = normalized.split("\n")
    results = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        m = PART_PREFIX_RE.match(stripped)
        if m:
            label = m.group(1).strip()
            content = m.group(2).strip()
            results.append((label, content))
        else:
            results.append((None, stripped))

    return results


class WorksheetSection(BaseModel):
    """Named grouping of problems with distinct layout or ordering rules."""
    id: str
    title: Optional[str] = None
    instructions: Optional[str] = None
    ordering: SectionOrdering = SectionOrdering.STRICT
    column_mode: Optional[str] = None   # "single", "double", or None (inherits from worksheet)
    page_break_before: bool = False     # Forces this section to start on a new page
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
    max_font_size_pt: float = 14.0
    auto_scale_font: bool = True
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
    spacing_after_in: float = 0.10
    font_size_pt: Optional[float] = None


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
    font_size_pt: Optional[float] = None


class RenderPlan(BaseModel):
    """Complete layout plan ready for deterministic DOCX or LaTeX rendering."""
    worksheet: WorksheetSpec
    pages: List[PlacedPage] = Field(default_factory=list)
    total_pages: int = 0
    stats: Dict[str, Any] = Field(default_factory=dict)


```

### src\worksheet_packer\layout_engine.py

```python
"""2D Bin Packing and Whitespace Optimization Engine for Worksheets.

Computes exact geometric footprints for problems with attached diagrams, chooses
side-by-side vs stacked layouts, respects strict vs flexible ordering constraints,
and packs items across pages and columns to minimize wasted whitespace.
"""

from __future__ import annotations
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from .worksheet_ast import (
    LayoutDecision,
    LayoutHint,
    PlacedPage,
    PlacedProblem,
    PlacedSectionHeader,
    Problem,
    RenderPlan,
    SectionOrdering,
    WorkspaceType,
    WorksheetSection,
    WorksheetSpec,
)


class LayoutEngine:
    """Calculates spatial footprints and executes 2D bin packing for worksheets."""

    def __init__(self, worksheet: WorksheetSpec):
        self.ws = worksheet

    def estimate_text_height(
        self,
        problem: Problem,
        target_width_in: float,
        font_size_pt: Optional[float] = None,
    ) -> float:
        """Estimates vertical text height in inches for question prompt and multiple-choice options."""
        fs = font_size_pt or self.ws.default_font_size_pt
        line_height_in = (fs * 1.30) / 72.0  # Approx line pitch
        padding_in = 0.06

        # Average char width in inches for proportional fonts like Calibri/Arial
        char_width_in = (fs * 0.48) / 72.0
        chars_per_line = max(15, int(target_width_in / char_width_in))

        # 1. Main question prompt
        full_text = problem.prompt_text or ""
        if not full_text and problem.prompt_runs:
            full_text = "".join(r.text for r in problem.prompt_runs)

        label_prefix = problem.full_label
        if label_prefix and not full_text.startswith(label_prefix):
            full_text = f"{label_prefix} {full_text}"

        # Clean common markup delimiters from full_text so line counting reflects actual visible text
        cleaned_text = re.sub(r"%.*", "", full_text)
        cleaned_text = re.sub(r"\\begin\{(?:lstlisting|enumerate|itemize)\}(?:\[.*?\])?", "", cleaned_text)
        cleaned_text = re.sub(r"\\end\{(?:lstlisting|enumerate|itemize)\}", "", cleaned_text)
        cleaned_text = re.sub(r"\\item\s*", "", cleaned_text)
        cleaned_text = re.sub(r"\\qnum\{\d+\}", "", cleaned_text)
        cleaned_text = re.sub(r"\\scriptsize", "", cleaned_text)
        cleaned_text = re.sub(r"\\(?:textbf|texttt|textit|color)\{([^}]*)\}", r"\1", cleaned_text)

        lines = 0
        paragraphs = cleaned_text.split("\n")
        for p in paragraphs:
            p_str = p.strip()
            if not p_str:
                lines += 0.3
            else:
                lines += max(1, math.ceil(len(p_str) / chars_per_line))

        # 2. Multiple choice options
        if problem.choices:
            all_short = all(len(ch.text.strip()) <= 15 for ch in problem.choices)
            if all_short and len(problem.choices) <= 4:
                lines += 1.5
            else:
                for ch in problem.choices:
                    c_text = ch.text.strip()
                    c_text = re.sub(r"%.*", "", c_text)
                    c_text = re.sub(r"\\[a-zA-Z]+(?:\{.*?\})?", "", c_text)
                    ch_line_chars = max(10, chars_per_line - 5)
                    lines += max(1, math.ceil(len(c_text) / ch_line_chars))

        return max(line_height_in, lines * line_height_in + padding_in)

    def estimate_workspace_height(
        self,
        problem: Problem,
        col_width_in: Optional[float] = None,
    ) -> float:
        """Estimates vertical height in inches for the student work area.
        
        Prioritizes explicit approximate workspace heights/areas (approx_workspace_in,
        approx_height_in, approx_area_sq_in) or lines of empty whitespace.
        """
        ws_cfg = problem.workspace
        if ws_cfg.type == WorkspaceType.NONE:
            return 0.0

        cw = col_width_in
        if cw is None:
            cw = self.ws.printable_width_in / max(1, self.ws.default_columns)

        if problem.approx_workspace_in is not None and problem.approx_workspace_in > 0:
            return float(problem.approx_workspace_in)
        if problem.approx_workspace_area_sq_in is not None and problem.approx_workspace_area_sq_in > 0:
            return float(problem.approx_workspace_area_sq_in / max(0.5, cw))

        return ws_cfg.effective_height_in(cw)

    def calculate_problem_footprint(
        self,
        problem: Problem,
        col_width_in: float,
        target_img_width_in: Optional[float] = None,
        font_size_pt: Optional[float] = None,
    ) -> Tuple[LayoutDecision, float, float, float, float, float, float]:
        """Calculates layout decision and exact dimensions for a problem.

        Args:
            problem: The problem to evaluate.
            col_width_in: Target column width in inches.
            target_img_width_in: Explicit image width override (for elastic squeeze or slack expansion).
            font_size_pt: Optional font size override in points.

        Returns:
            Tuple of:
              - decision (LayoutDecision)
              - total_height_in
              - text_render_width_in
              - text_render_height_in
              - image_render_width_in
              - image_render_height_in
              - workspace_height_in
        """
        ws_height = self.estimate_workspace_height(problem, col_width_in)

        # Case 1: No image attached
        if not problem.image:
            text_w = col_width_in
            text_h = self.estimate_text_height(problem, text_w, font_size_pt=font_size_pt)
            total_h = text_h + ws_height + 0.08
            return (
                LayoutDecision.TEXT_ONLY,
                total_h,
                text_w,
                text_h,
                0.0,
                0.0,
                ws_height,
            )

        # Case 2: Image attached
        img = problem.image
        ar = img.aspect_ratio or 1.0
        prompt_len = len(problem.prompt_text or "")
        min_img_w = problem.effective_min_image_width_in
        pref_img_w = getattr(img, "preferred_width_in", 2.0)
        max_img_w = getattr(img, "max_width_in", 3.5)
        category = getattr(img, "category", "detailed_diagram")

        # Determine Layout Decision based on hints, category, & aspect ratio
        decision = LayoutDecision.STACKED
        if problem.layout_hint == LayoutHint.SIDE_BY_SIDE:
            decision = LayoutDecision.SIDE_BY_SIDE
        elif problem.layout_hint == LayoutHint.STACKED:
            decision = LayoutDecision.STACKED
        else:
            # Auto heuristic:
            # Wide grids and wide aspect ratios must be stacked
            # Formula icons (isolated radical/expression) are best centered stacked
            if category == "wide_grid" or ar < 0.52 or category == "formula_icon":
                decision = LayoutDecision.STACKED
            elif 0.55 <= ar <= 1.55 and prompt_len < 450:
                # Check if side-by-side fits legibility floor comfortably in column
                if min_img_w <= col_width_in * 0.46:
                    decision = LayoutDecision.SIDE_BY_SIDE
                else:
                    decision = LayoutDecision.STACKED
            else:
                decision = LayoutDecision.STACKED

        if decision == LayoutDecision.SIDE_BY_SIDE:
            if target_img_width_in is not None:
                img_w = max(min_img_w, min(target_img_width_in, col_width_in * 0.50))
            else:
                # Ideal width within side-by-side share (35% to 42% of column)
                ideal_w = min(pref_img_w, col_width_in * 0.40)
                img_w = max(min_img_w, min(ideal_w, max_img_w))

            text_w = col_width_in - img_w - 0.08
            img_h = img_w * ar
            text_h = self.estimate_text_height(problem, text_w, font_size_pt=font_size_pt)
            top_h = max(text_h, img_h)
            total_h = top_h + ws_height + 0.12
            return (
                LayoutDecision.SIDE_BY_SIDE,
                total_h,
                text_w,
                text_h,
                img_w,
                img_h,
                ws_height,
            )
        else:
            # STACKED
            text_w = col_width_in
            text_h = self.estimate_text_height(problem, text_w, font_size_pt=font_size_pt)

            if target_img_width_in is not None:
                img_w = max(min_img_w, min(target_img_width_in, col_width_in * 0.95))
            else:
                # Bound by pref_img_w and max_img_w (prevents formula icons from ballooning)
                cand_w = min(col_width_in * 0.90, pref_img_w)
                img_w = max(min_img_w, min(cand_w, max_img_w))

            max_stacked_h = 3.4
            img_h = img_w * ar
            if img_h > max_stacked_h:
                img_h = max_stacked_h
                img_w = img_h / ar if ar > 0 else img_w

            total_h = text_h + img_h + ws_height + 0.16
            return (
                LayoutDecision.STACKED,
                total_h,
                text_w,
                text_h,
                img_w,
                img_h,
                ws_height,
            )

    def _attempt_elastic_squeeze(
        self,
        placed_col_items: List[PlacedProblem],
        new_prob: Problem,
        new_fp: Tuple[LayoutDecision, float, float, float, float, float, float],
        overflow_in: float,
        col_width_in: float,
    ) -> Optional[Tuple[List[Tuple[float, float, float, float, float]], Tuple[LayoutDecision, float, float, float, float, float, float]]]:
        """Attempts to elastically compress images in this column to eliminate overflow_in.

        Returns:
            Tuple of (updated_placed_dimensions [(height, img_w, img_h, text_w, text_h)...], new_prob_updated_fp) or None.
        """
        all_candidates = placed_col_items + [PlacedProblem(
            problem=new_prob,
            layout=new_fp[0],
            page_index=0,
            col_index=0,
            x_in=0,
            y_in=0,
            width_in=col_width_in,
            height_in=new_fp[1],
            text_render_width_in=new_fp[2],
            text_render_height_in=new_fp[3],
            image_render_width_in=new_fp[4],
            image_render_height_in=new_fp[5],
            workspace_height_in=new_fp[6],
        )]

        shrink_capacities: List[float] = []
        for cand in all_candidates:
            if not cand.problem.image or cand.image_render_width_in <= 0:
                shrink_capacities.append(0.0)
                continue
            min_w = cand.problem.effective_min_image_width_in
            curr_w = cand.image_render_width_in
            if curr_w <= min_w:
                shrink_capacities.append(0.0)
                continue

            # Footprint at absolute minimum legible width
            _, min_h, _, _, _, _, _ = self.calculate_problem_footprint(
                cand.problem, col_width_in, target_img_width_in=min_w
            )
            elasticity = getattr(cand.problem.image, "elasticity", 1.0)
            cap = max(0.0, (cand.height_in - min_h) * elasticity)
            shrink_capacities.append(cap)

        total_capacity = sum(shrink_capacities)
        if total_capacity < overflow_in:
            return None  # Cannot squeeze enough to absorb the overflow

        squeeze_factor = min(1.0, overflow_in / total_capacity)

        # Apply compression to previously placed items
        updated_placed = []
        for i, cand in enumerate(placed_col_items):
            if shrink_capacities[i] > 0:
                min_w = cand.problem.effective_min_image_width_in
                curr_w = cand.image_render_width_in
                target_w = curr_w - squeeze_factor * (curr_w - min_w)
                fp = self.calculate_problem_footprint(cand.problem, col_width_in, target_img_width_in=target_w)
                updated_placed.append((fp[1], fp[4], fp[5], fp[2], fp[3]))
            else:
                updated_placed.append((cand.height_in, cand.image_render_width_in, cand.image_render_height_in, cand.text_render_width_in, cand.text_render_height_in))

        # Apply compression to the newly placed problem
        last_idx = len(all_candidates) - 1
        if shrink_capacities[last_idx] > 0:
            min_w = new_prob.effective_min_image_width_in
            curr_w = new_fp[4]
            target_w = curr_w - squeeze_factor * (curr_w - min_w)
            new_prob_fp = self.calculate_problem_footprint(new_prob, col_width_in, target_img_width_in=target_w)
        else:
            new_prob_fp = new_fp

        return updated_placed, new_prob_fp

    def _absorb_slack_expansion(
        self,
        page: PlacedPage,
        col_idx: int,
        printable_h: float,
        col_w: float,
    ) -> None:
        """Expands images up to max_width_in when there is excessive trailing whitespace."""
        col_problems = [
            item for item in page.items
            if isinstance(item, PlacedProblem) and item.col_index == col_idx
        ]
        if not col_problems:
            return

        last_prob = col_problems[-1]
        slack = printable_h - (last_prob.y_in + last_prob.height_in)
        if slack < 1.0:
            return

        exp_capacities = []
        for p in col_problems:
            if not p.problem.image or p.image_render_width_in <= 0:
                exp_capacities.append(0.0)
                continue
            max_w = getattr(p.problem.image, "max_width_in", 3.5)
            curr_w = p.image_render_width_in
            if curr_w >= max_w:
                exp_capacities.append(0.0)
                continue
            _, exp_h, _, _, _, _, _ = self.calculate_problem_footprint(
                p.problem, col_w, target_img_width_in=max_w, font_size_pt=p.font_size_pt
            )
            cap = max(0.0, exp_h - p.height_in)
            exp_capacities.append(cap)

        total_exp_cap = sum(exp_capacities)
        if total_exp_cap <= 0:
            return

        usable_slack = min(total_exp_cap, slack * 0.60)
        exp_factor = usable_slack / total_exp_cap

        curr_y = col_problems[0].y_in
        for i, p in enumerate(col_problems):
            if exp_capacities[i] > 0:
                max_w = getattr(p.problem.image, "max_width_in", 3.5)
                target_w = p.image_render_width_in + exp_factor * (max_w - p.image_render_width_in)
                fp = self.calculate_problem_footprint(p.problem, col_w, target_img_width_in=target_w, font_size_pt=p.font_size_pt)
                p.height_in = fp[1]
                p.text_render_width_in = fp[2]
                p.text_render_height_in = fp[3]
                p.image_render_width_in = fp[4]
                p.image_render_height_in = fp[5]
            p.y_in = curr_y
            curr_y += p.height_in + getattr(p, "spacing_after_in", 0.10)

    def _attempt_squeeze_batch(
        self,
        batch: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        avail_h: float,
        col_w: float,
        base_gap: float = 0.10,
        font_size_pt: Optional[float] = None,
    ) -> Optional[List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]]]:
        """Attempts to elastically compress diagrams in batch so total height + gaps <= avail_h."""
        total_curr_h = sum(fp[1] for _, fp in batch) + max(0, len(batch) - 1) * base_gap
        overflow_in = total_curr_h - avail_h
        if overflow_in <= 0.001:
            return batch
        if overflow_in > 1.80:
            return None

        shrink_capacities: List[float] = []
        min_fps = []
        for prob, fp in batch:
            if not prob.image or fp[4] <= 0:
                shrink_capacities.append(0.0)
                min_fps.append(fp)
                continue
            min_w = prob.effective_min_image_width_in
            curr_w = fp[4]
            if curr_w <= min_w:
                shrink_capacities.append(0.0)
                min_fps.append(fp)
                continue
            min_fp = self.calculate_problem_footprint(prob, col_w, target_img_width_in=min_w, font_size_pt=font_size_pt)
            min_fps.append(min_fp)
            elasticity = getattr(prob.image, "elasticity", 1.0)
            cap = max(0.0, (fp[1] - min_fp[1]) * elasticity)
            shrink_capacities.append(cap)

        total_cap = sum(shrink_capacities)
        if total_cap < overflow_in:
            return None

        squeeze_factor = min(1.0, overflow_in / total_cap)
        squeezed_batch = []
        for i, (prob, fp) in enumerate(batch):
            if shrink_capacities[i] > 0:
                min_w = prob.effective_min_image_width_in
                curr_w = fp[4]
                target_w = curr_w - squeeze_factor * (curr_w - min_w)
                new_fp = self.calculate_problem_footprint(prob, col_w, target_img_width_in=target_w, font_size_pt=font_size_pt)
                squeezed_batch.append((prob, new_fp))
            else:
                squeezed_batch.append((prob, fp))

        return squeezed_batch

    def _find_valid_splits_strict(
        self,
        batch: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        avail_0: float,
        avail_1: float,
        col_w: float,
        base_gap: float,
        cursor_0: float,
        cursor_1: float,
        font_size_pt: Optional[float] = None,
    ) -> List[Tuple[float, int, List[Tuple[Any, Any]], List[Tuple[Any, Any]]]]:
        """Evaluates all possible split points k in strict sequence for a subset of problems.
        
        Returns:
            List of (score, k, b0_sq, b1_sq) for splits that fit within (avail_0, avail_1).
        """
        m = len(batch)
        if m == 0:
            return []

        valid_splits = []
        for k in range(1, m + 1):
            b0 = batch[:k]
            b1 = batch[k:]

            h0 = sum(fp[1] for _, fp in b0) + max(0, len(b0) - 1) * base_gap
            h1 = sum(fp[1] for _, fp in b1) + max(0, len(b1) - 1) * base_gap if b1 else 0.0

            b0_sq = b0
            b1_sq = b1
            if h0 > avail_0 + 0.01:
                res0 = self._attempt_squeeze_batch(b0, avail_0, col_w, base_gap, font_size_pt=font_size_pt)
                if res0 is not None:
                    b0_sq = res0
                    h0 = sum(fp[1] for _, fp in b0_sq) + max(0, len(b0_sq) - 1) * base_gap
                else:
                    continue

            if h1 > avail_1 + 0.01:
                res1 = self._attempt_squeeze_batch(b1, avail_1, col_w, base_gap, font_size_pt=font_size_pt)
                if res1 is not None:
                    b1_sq = res1
                    h1 = sum(fp[1] for _, fp in b1_sq) + max(0, len(b1_sq) - 1) * base_gap
                else:
                    continue

            if h0 <= avail_0 + 0.01 and h1 <= avail_1 + 0.01:
                end0 = cursor_0 + h0
                end1 = cursor_1 + h1
                h_diff = abs(end0 - end1)
                count_diff = abs(len(b0) - len(b1))
                score = h_diff + 1.25 * count_diff
                if m % 2 == 1 and k == (m + 1) // 2:
                    score -= 0.05
                valid_splits.append((score, k, b0_sq, b1_sq))

        valid_splits.sort(key=lambda x: x[0])
        return valid_splits

    def _find_valid_flex(
        self,
        batch: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        avail_0: float,
        avail_1: float,
        col_w: float,
        base_gap: float,
        cursor_0: float,
        cursor_1: float,
    ) -> Optional[Tuple[float, List[Tuple[Any, Any]], List[Tuple[Any, Any]]]]:
        """Partitions batch items into two balanced columns in flexible order."""
        sorted_cand = sorted(batch, key=lambda x: x[1][1], reverse=True)
        c0 = []
        c1 = []
        h0 = 0.0
        h1 = 0.0

        for prob, fp in sorted_cand:
            h = fp[1]
            needed_0 = h if not c0 else (h + base_gap)
            needed_1 = h if not c1 else (h + base_gap)

            if cursor_0 + h0 + needed_0 <= avail_0 + 0.01 and (
                cursor_0 + h0 <= cursor_1 + h1 or cursor_1 + h1 + needed_1 > avail_1 + 0.01
            ):
                c0.append((prob, fp))
                h0 += needed_0
            elif cursor_1 + h1 + needed_1 <= avail_1 + 0.01:
                c1.append((prob, fp))
                h1 += needed_1
            elif cursor_0 + h0 + needed_0 <= avail_0 + 0.01:
                c0.append((prob, fp))
                h0 += needed_0
            else:
                return None

        # Rebalance counts if one column has significantly more items and heights allow
        if len(c0) >= len(c1) + 2:
            for i in reversed(range(len(c0))):
                p, fp = c0[i]
                needed_1 = fp[1] if not c1 else (fp[1] + base_gap)
                if cursor_1 + h1 + needed_1 <= avail_1 + 0.01:
                    c1.append(c0.pop(i))
                    h1 += needed_1
                    h0 -= (fp[1] + (base_gap if c0 else 0.0))
                    break
        elif len(c1) >= len(c0) + 2:
            for i in reversed(range(len(c1))):
                p, fp = c1[i]
                needed_0 = fp[1] if not c0 else (fp[1] + base_gap)
                if cursor_0 + h0 + needed_0 <= avail_0 + 0.01:
                    c0.append(c1.pop(i))
                    h0 += needed_0
                    h1 -= (fp[1] + (base_gap if c1 else 0.0))
                    break

        end0 = cursor_0 + h0
        end1 = cursor_1 + h1
        score = abs(end0 - end1) + 1.25 * abs(len(c0) - len(c1))
        return (score, c0, c1)

    def _estimate_pages_needed_strict(
        self,
        remaining_items: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        avail_0: float,
        avail_1: float,
        printable_h: float,
        col_w: float,
        base_gap: float,
        font_size_pt: Optional[float] = None,
    ) -> int:
        """Simulates strict forward packing to estimate minimum pages needed for remaining items."""
        pages = 0
        cur = list(remaining_items)
        first_page = True
        while cur:
            pages += 1
            cur_a0 = avail_0 if first_page else printable_h
            cur_a1 = avail_1 if first_page else printable_h
            first_page = False
            m_fit = 0
            for m in range(1, len(cur) + 1):
                s = self._find_valid_splits_strict(cur[:m], cur_a0, cur_a1, col_w, base_gap, 0.0, 0.0, font_size_pt=font_size_pt)
                if s:
                    m_fit = m
                else:
                    break
            if m_fit == 0:
                m_fit = 1
            cur = cur[m_fit:]
        return max(1, pages)

    def _distribute_column_spacing(
        self,
        batch_items: List[Tuple[Problem, Tuple[LayoutDecision, float, float, float, float, float, float]]],
        col_idx: int,
        avail_h: float,
        cursor_y: float,
        base_gap: float,
        col_w: float,
        col_gap: float,
        page_idx: int,
        font_size_pt: Optional[float] = None,
    ) -> Tuple[float, List[PlacedProblem]]:
        """Positions problems in a column, distributing vertical slack into gaps and workspaces."""
        n = len(batch_items)
        if n == 0:
            return cursor_y, []

        h_total = sum(fp[1] for _, fp in batch_items)
        slack = max(0.0, avail_h - h_total)

        if n > 1:
            base_gaps_total = (n - 1) * base_gap
            extra_slack = max(0.0, slack - base_gaps_total)
            extra_gap = extra_slack / (n - 1)
            gap = min(0.45, base_gap + extra_gap)
            gaps_total = (n - 1) * gap
        else:
            gap = base_gap
            gaps_total = 0.0

        # Space out problems evenly down the column
        x_pos = 0.0 if col_idx == 0 else (col_w + col_gap)
        curr_y = cursor_y
        placed_items = []
        fs = font_size_pt or self.ws.default_font_size_pt

        for i, (prob, (decision, total_h, text_w, text_h, img_w, img_h, ws_h)) in enumerate(batch_items):
            placed = PlacedProblem(
                problem=prob,
                layout=decision,
                page_index=page_idx,
                col_index=col_idx,
                x_in=x_pos,
                y_in=curr_y,
                width_in=col_w,
                height_in=total_h,
                image_render_width_in=img_w,
                image_render_height_in=img_h,
                text_render_width_in=text_w,
                text_render_height_in=text_h,
                workspace_height_in=ws_h,
                spacing_after_in=gap,
                font_size_pt=fs,
            )
            placed_items.append(placed)
            curr_y += total_h + gap

        return curr_y, placed_items

    def _pack_page_layout(self, font_size_pt: Optional[float] = None) -> RenderPlan:
        """Executes 2D layout bin-packing across all worksheet sections at a specific font size."""
        printable_w = self.ws.printable_width_in
        printable_h = self.ws.printable_height_in
        active_fs = font_size_pt or self.ws.default_font_size_pt

        # Page 1 header reserve (title, student info line, etc.)
        p1_header_h = 0.75 if (self.ws.title or self.ws.header_right) else 0.0

        current_page_idx = 1
        pages: List[PlacedPage] = [PlacedPage(page_index=1, font_size_pt=active_fs)]
        default_col_count = max(1, min(2, int(self.ws.default_columns)))
        col_cursors = [p1_header_h] * default_col_count

        # Global statistics
        total_problems = 0
        side_by_side_count = 0
        stacked_count = 0
        text_only_count = 0

        for section in self.ws.sections:
            if section.column_mode:
                if str(section.column_mode).lower() in ("single", "1"):
                    col_count = 1
                elif str(section.column_mode).lower() in ("double", "2"):
                    col_count = 2
                else:
                    try:
                        col_count = int(section.column_mode)
                    except ValueError:
                        col_count = int(self.ws.default_columns)
            else:
                col_count = int(self.ws.default_columns)
            col_count = max(1, min(2, col_count))  # Support 1 or 2 columns

            if section.page_break_before or (col_count != len(col_cursors) and max(col_cursors) > 0.05):
                if max(col_cursors) > 0.05:
                    current_page_idx = len(pages) + 1
                    pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                    col_cursors = [0.0] * col_count
            elif len(col_cursors) != col_count:
                curr_max = max(col_cursors) if col_cursors else 0.0
                col_cursors = [curr_max] * col_count

            col_gap = self.ws.column_gap_in if col_count > 1 else 0.0
            col_w = (printable_w - (col_count - 1) * col_gap) / col_count

            # Section Header footprint
            sec_header_h = 0.0
            if section.title or section.instructions:
                sec_header_h = 0.35 + (0.20 if section.instructions else 0.0)

            # Problems to pack in this section
            prob_list = list(section.problems)
            if not prob_list:
                continue

            # Calculate footprints
            problem_footprints = []
            for prob in prob_list:
                fp = self.calculate_problem_footprint(prob, col_w, font_size_pt=active_fs)
                problem_footprints.append((prob, fp))

            # Ordering strategy:
            # If FLEXIBLE: sort by height descending (First-Fit Decreasing) for tightest 2D packing
            if section.ordering == SectionOrdering.FLEXIBLE:
                problem_footprints.sort(key=lambda item: item[1][1], reverse=True)

            # Insert section header if present
            if sec_header_h > 0:
                # Align both columns to the lowest available point for a cross-column section header
                curr_max_y = max(col_cursors)
                if curr_max_y + sec_header_h > printable_h - 1.2:
                    # Header doesn't fit with room for problems; start new page
                    current_page_idx = len(pages) + 1
                    pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                    col_cursors = [0.0] * col_count
                    curr_max_y = 0.0

                header_item = PlacedSectionHeader(
                    section_id=section.id,
                    title=section.title,
                    instructions=section.instructions,
                    page_index=pages[-1].page_index,
                    y_in=curr_max_y,
                    height_in=sec_header_h,
                    span_all_columns=True,
                )
                pages[-1].items.append(header_item)
                for c in range(col_count):
                    col_cursors[c] = curr_max_y + sec_header_h + 0.08

            base_gap = 0.10
            remaining = list(problem_footprints)

            if col_count == 1:
                while remaining:
                    avail_h = printable_h - col_cursors[0]
                    if avail_h < 1.0:
                        current_page_idx = len(pages) + 1
                        pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                        col_cursors = [0.0]
                        avail_h = printable_h

                    count = 0
                    curr_h = 0.0
                    for prob, fp in remaining:
                        needed = fp[1] if count == 0 else (fp[1] + base_gap)
                        if curr_h + needed <= avail_h + 0.01:
                            curr_h += needed
                            count += 1
                        else:
                            break

                    if count < len(remaining):
                        cand_squeeze = remaining[:count + 1]
                        sq_res = self._attempt_squeeze_batch(cand_squeeze, avail_h, col_w, base_gap, font_size_pt=active_fs)
                        if sq_res is not None:
                            count += 1
                            placed_batch = sq_res
                        else:
                            placed_batch = remaining[:count]
                    else:
                        placed_batch = remaining[:count]

                    if count == 0:
                        if col_cursors[0] > 0.05:
                            current_page_idx = len(pages) + 1
                            pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                            col_cursors = [0.0]
                            continue
                        else:
                            count = 1
                            placed_batch = remaining[:1]

                    remaining = remaining[count:]
                    col_cursors[0], placed = self._distribute_column_spacing(
                        placed_batch, 0, avail_h, col_cursors[0], base_gap, col_w, col_gap, pages[-1].page_index, font_size_pt=active_fs
                    )
                    pages[-1].items.extend(placed)

                    for p in placed:
                        total_problems += 1
                        if p.layout == LayoutDecision.SIDE_BY_SIDE:
                            side_by_side_count += 1
                        elif p.layout == LayoutDecision.STACKED:
                            stacked_count += 1
                        elif p.layout == LayoutDecision.TEXT_ONLY:
                            text_only_count += 1

                    if remaining:
                        current_page_idx = len(pages) + 1
                        pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                        col_cursors = [0.0]

            elif col_count == 2:
                while remaining:
                    avail_0 = printable_h - col_cursors[0]
                    avail_1 = printable_h - col_cursors[1]

                    if max(avail_0, avail_1) < 1.0:
                        current_page_idx = len(pages) + 1
                        pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                        col_cursors = [0.0, 0.0]
                        avail_0 = printable_h
                        avail_1 = printable_h

                    if section.ordering == SectionOrdering.STRICT:
                        valid_m_splits = {}
                        for m_cand in range(1, len(remaining) + 1):
                            splits = self._find_valid_splits_strict(
                                remaining[:m_cand], avail_0, avail_1, col_w, base_gap, col_cursors[0], col_cursors[1], font_size_pt=active_fs
                            )
                            if splits:
                                valid_m_splits[m_cand] = splits[0]
                            else:
                                break

                        if not valid_m_splits:
                            if col_cursors[0] > 0.05 or col_cursors[1] > 0.05:
                                current_page_idx = len(pages) + 1
                                pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                                col_cursors = [0.0, 0.0]
                                continue
                            else:
                                col_0_items = [remaining[0]]
                                col_1_items = []
                                remaining = remaining[1:]
                        else:
                            max_m = max(valid_m_splits.keys())
                            if max_m == len(remaining):
                                best_m = max_m
                            else:
                                p_needed = self._estimate_pages_needed_strict(
                                    remaining, avail_0, avail_1, printable_h, col_w, base_gap, font_size_pt=active_fs
                                )
                                target_m = math.ceil(len(remaining) / max(1, p_needed))
                                candidate_ms = [m for m in valid_m_splits.keys() if m <= max_m]
                                best_m = min(candidate_ms, key=lambda m: (abs(m - target_m), valid_m_splits[m][0]))

                            best_split = valid_m_splits[best_m]
                            _, k_star, col_0_items, col_1_items = best_split
                            remaining = remaining[best_m:]

                    else:
                        best_m = 0
                        best_c0, best_c1 = [], []
                        for m_cand in range(1, len(remaining) + 1):
                            res = self._find_valid_flex(
                                remaining[:m_cand], avail_0, avail_1, col_w, base_gap, col_cursors[0], col_cursors[1]
                            )
                            if res is not None:
                                best_m = m_cand
                                _, best_c0, best_c1 = res
                            else:
                                break

                        if best_m == 0:
                            if col_cursors[0] > 0.05 or col_cursors[1] > 0.05:
                                current_page_idx = len(pages) + 1
                                pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                                col_cursors = [0.0, 0.0]
                                continue
                            else:
                                col_0_items = [remaining[0]]
                                col_1_items = []
                                remaining = remaining[1:]
                        else:
                            col_0_items = best_c0
                            col_1_items = best_c1
                            remaining = remaining[best_m:]

                    col_cursors[0], placed_0 = self._distribute_column_spacing(
                        col_0_items, 0, avail_0, col_cursors[0], base_gap, col_w, col_gap, pages[-1].page_index, font_size_pt=active_fs
                    )
                    pages[-1].items.extend(placed_0)

                    col_cursors[1], placed_1 = self._distribute_column_spacing(
                        col_1_items, 1, avail_1, col_cursors[1], base_gap, col_w, col_gap, pages[-1].page_index, font_size_pt=active_fs
                    )
                    pages[-1].items.extend(placed_1)

                    for p in placed_0 + placed_1:
                        total_problems += 1
                        if p.layout == LayoutDecision.SIDE_BY_SIDE:
                            side_by_side_count += 1
                        elif p.layout == LayoutDecision.STACKED:
                            stacked_count += 1
                        elif p.layout == LayoutDecision.TEXT_ONLY:
                            text_only_count += 1

                    if remaining:
                        current_page_idx = len(pages) + 1
                        pages.append(PlacedPage(page_index=current_page_idx, font_size_pt=active_fs))
                        col_cursors = [0.0, 0.0]

        # Pass 3: Slack Absorption (Whitespace Filling across pages)
        default_gap = self.ws.column_gap_in if self.ws.default_columns > 1 else 0.0
        default_col_w = (printable_w - (self.ws.default_columns - 1) * default_gap) / max(1, self.ws.default_columns)
        for page in pages:
            for col_idx in range(self.ws.default_columns):
                self._absorb_slack_expansion(page, col_idx, printable_h, default_col_w)

        # Post-processing: Handle fill_remaining workspace
        for page in pages:
            # Find the bottom-most problem in each column
            for col_idx in range(self.ws.default_columns):
                col_problems = [
                    item for item in page.items
                    if isinstance(item, PlacedProblem) and item.col_index == col_idx
                ]
                if col_problems:
                    last_prob = col_problems[-1]
                    if last_prob.problem.workspace.fill_remaining:
                        remain_h = printable_h - (last_prob.y_in + last_prob.height_in)
                        if remain_h > 0.3:
                            last_prob.workspace_height_in += remain_h
                            last_prob.height_in += remain_h

        stats = {
            "total_problems": total_problems,
            "total_pages": len(pages),
            "side_by_side_count": side_by_side_count,
            "stacked_count": stacked_count,
            "text_only_count": text_only_count,
            "density_ratio": (
                float(side_by_side_count) / float(total_problems)
                if total_problems > 0 else 0.0
            ),
        }

        return RenderPlan(
            worksheet=self.ws,
            pages=pages,
            total_pages=len(pages),
            stats=stats,
        )

    def _scale_page_fonts_to_fill_slack(self, plan: RenderPlan, max_fs: float) -> None:
        """Increases font size on individual pages that have significant unused vertical space."""
        printable_h = self.ws.printable_height_in
        printable_w = self.ws.printable_width_in
        col_gap = self.ws.column_gap_in if self.ws.default_columns > 1 else 0.0
        base_gap = 0.10

        for page in plan.pages:
            prob_items = [it for it in page.items if isinstance(it, PlacedProblem)]
            if not prob_items:
                continue

            current_page_fs = page.font_size_pt or prob_items[0].font_size_pt or self.ws.default_font_size_pt
            if current_page_fs >= max_fs:
                continue

            # Determine column count on this page
            max_col_idx = max(p.col_index for p in prob_items)
            col_count = max(1, max_col_idx + 1)
            col_w = (printable_w - (col_count - 1) * col_gap) / col_count

            # Measure trailing slack across active columns
            col_slacks = []
            for c in range(col_count):
                col_probs = [p for p in prob_items if p.col_index == c]
                if not col_probs:
                    continue
                bottom_y = max(p.y_in + p.height_in for p in col_probs)
                col_slacks.append(printable_h - bottom_y)

            if not col_slacks:
                continue

            min_slack = min(col_slacks)
            # If the page already uses almost the whole page (slack < 0.60 in), don't scale further
            if min_slack < 0.60:
                continue

            # Test higher font sizes for this page in 0.5pt steps
            best_fs = current_page_fs
            step = 0.5
            cand_fs = round(current_page_fs + step, 1)

            while cand_fs <= max_fs:
                all_fit = True
                for c in range(col_count):
                    col_probs = [p for p in prob_items if p.col_index == c]
                    if not col_probs:
                        continue
                    initial_y = col_probs[0].y_in
                    total_h = 0.0
                    for p in col_probs:
                        fp = self.calculate_problem_footprint(
                            p.problem,
                            col_w,
                            target_img_width_in=p.image_render_width_in if p.image_render_width_in > 0 else None,
                            font_size_pt=cand_fs,
                        )
                        total_h += fp[1]
                    # Ensure at least 0.18 in padding between problems in multi-item columns
                    needed_total = initial_y + total_h + max(0, len(col_probs) - 1) * 0.18
                    if needed_total > printable_h:
                        all_fit = False
                        break

                if all_fit:
                    best_fs = cand_fs
                    cand_fs = round(cand_fs + step, 1)
                else:
                    break

            if best_fs > current_page_fs:
                page.font_size_pt = best_fs
                new_placed_by_col = {}
                for c in range(col_count):
                    col_probs = [p for p in prob_items if p.col_index == c]
                    if not col_probs:
                        continue
                    initial_y = col_probs[0].y_in
                    avail_h = printable_h - initial_y

                    batch = []
                    for p in col_probs:
                        fp = self.calculate_problem_footprint(
                            p.problem,
                            col_w,
                            target_img_width_in=p.image_render_width_in if p.image_render_width_in > 0 else None,
                            font_size_pt=best_fs,
                        )
                        batch.append((p.problem, fp))

                    _, new_placed = self._distribute_column_spacing(
                        batch,
                        c,
                        avail_h,
                        initial_y,
                        base_gap,
                        col_w,
                        col_gap,
                        page.page_index,
                        font_size_pt=best_fs,
                    )
                    new_placed_by_col[c] = list(new_placed)

                # Reconstruct page.items preserving section headers and updated problems
                new_items = []
                col_pointers = {c: 0 for c in range(col_count)}
                for item in page.items:
                    if isinstance(item, PlacedProblem):
                        c = item.col_index
                        if c in new_placed_by_col and col_pointers[c] < len(new_placed_by_col[c]):
                            new_items.append(new_placed_by_col[c][col_pointers[c]])
                            col_pointers[c] += 1
                        else:
                            new_items.append(item)
                    else:
                        new_items.append(item)
                page.items = new_items

    def pack(self) -> RenderPlan:
        """Executes full 2D layout bin-packing with adaptive font scaling to maximize page utilization."""
        base_fs = self.ws.default_font_size_pt
        auto_scale = getattr(self.ws, "auto_scale_font", True)
        max_fs = getattr(self.ws, "max_font_size_pt", 14.0) or 14.0

        # Baseline pack at default font size
        plan = self._pack_page_layout(font_size_pt=base_fs)

        if not auto_scale or max_fs <= base_fs:
            return plan

        # When content on any specific page doesn't use the whole page (remaining slack >= 0.60 in),
        # try to increase font size on that page's problems to use up more of the page.
        self._scale_page_fonts_to_fill_slack(plan, max_fs=max_fs)

        # Final Slack Absorption (Expand images / fill workspace if any slack remains)
        printable_h = self.ws.printable_height_in
        printable_w = self.ws.printable_width_in
        default_gap = self.ws.column_gap_in if self.ws.default_columns > 1 else 0.0
        default_col_w = (printable_w - (self.ws.default_columns - 1) * default_gap) / max(1, self.ws.default_columns)
        for page in plan.pages:
            for col_idx in range(self.ws.default_columns):
                self._absorb_slack_expansion(page, col_idx, printable_h, default_col_w)

        return plan


```

### src\worksheet_packer\worksheet_parser.py

```python
"""Worksheet PDF Parser.

Reuses the project's PDFExtractor and multimodal vision to parse worksheet PDFs,
identify problems, detect diagram bounding boxes, crop and auto-trim whitespace,
and produce strongly-typed WorksheetSpec AST instances.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from pdf_to_docx.ir_schema import QuestionChoice, TextRun
from pdf_to_docx.pdf_extractor import PDFExtractor
from .image_utils import auto_crop_image, inspect_diagram_dimensions, estimate_image_scale_bounds
from .docx_extractor import convert_docx_to_pdf, extract_docx_media
from .worksheet_ast import (
    LayoutHint,
    Problem,
    ProblemImage,
    SectionOrdering,
    WorkspaceConfig,
    WorkspaceType,
    WorksheetSection,
    WorksheetSpec,
)


class RawProblemExtraction(BaseModel):
    """Raw problem representation output by multimodal LLM vision analysis."""
    id: str
    number: Optional[int] = None
    part: Optional[str] = None
    points: Optional[int] = None
    prompt: str
    choices: Optional[List[QuestionChoice]] = None
    has_diagram: bool = False
    diagram_bbox: Optional[List[int]] = Field(
        None,
        description="Normalized bounding box [ymin, xmin, ymax, xmax] on a 0-1000 scale"
    )
    diagram_caption: Optional[str] = None
    diagram_category: Optional[str] = Field(
        None,
        description="'formula_icon' (small math symbol), 'compact_shape' (simple shape), 'detailed_diagram' (angles/labels), or 'wide_grid'"
    )
    diagram_min_width_in: Optional[float] = Field(
        None,
        description="Minimum legible diagram width in inches before angle labels/numbers become unreadable"
    )
    diagram_max_width_in: Optional[float] = Field(
        None,
        description="Maximum sensible diagram width in inches before looking comically oversized"
    )
    workspace_type: str = "blank"  # "blank" (default whitespace), "box", "grid", "lines", "none"
    workspace_lines: int = 2
    workspace_height_pt: Optional[float] = None
    approx_workspace_height_in: Optional[float] = Field(
        None,
        description="Approximate vertical workspace height in inches required for students to show work"
    )
    approx_workspace_area_sq_in: Optional[float] = Field(
        None,
        description="Approximate workspace area in square inches required for student work"
    )
    layout_hint: str = "auto"      # "auto", "side_by_side", "stacked", "full_width"


class RawPageExtraction(BaseModel):
    """Extraction result for a single worksheet page."""
    page_number: int
    page_title: Optional[str] = None
    section_title: Optional[str] = None
    section_instructions: Optional[str] = None
    problems: List[RawProblemExtraction] = Field(default_factory=list)


WORKSHEET_VISION_PROMPT = """Analyze this worksheet/exam page image and extract every problem into the structured JSON schema.

Extraction Rules:
1. Identify all questions and problems on this page in sequential order.
2. For each question:
   - Extract the problem number (e.g. 1, 2) and part (e.g. "a", "b", "i").
   - Extract the full prompt text. Preserve mathematical symbols and equations in standard LaTeX notation ($...$ or \\(...\\)).
   - If multiple-choice, extract each option with label "(A)", "(B)", etc. and text.
3. DIAGRAMS & FIGURES:
   - If the problem refers to or contains a geometric figure, coordinate grid, graph, data table, or illustration, set has_diagram = true.
   - Provide the exact bounding box [ymin, xmin, ymax, xmax] on a 0-1000 normalized scale covering the diagram.
   - Identify diagram_category: "formula_icon" (isolated radical/expression), "compact_shape" (small polygon/circle), "detailed_diagram" (geometry figure with angle numbers and letters), or "wide_grid" (coordinate plane/table).
   - Estimate diagram_min_width_in (minimum width in inches to keep text legible) and diagram_max_width_in (maximum width before it looks cartoonishly blown up).
   - If the diagram is square-ish or portrait, note layout_hint = "side_by_side". If it is wide or full-width, note layout_hint = "stacked".
4. WORKSPACE & STUDENT ANSWER AREA:
   - Students need clean empty whitespace to write their answers. DO NOT extract or generate blank underline rules for student work areas.
   - Default to workspace_type = "blank" (clean whitespace gap).
   - Estimate approx_workspace_height_in (approximate vertical height in inches needed for work, e.g. 0.5 to 2.0 inches) or workspace_lines (approx 0.3 in each).
   - Only use "box" if the original document explicitly drew a framed response rectangle, "grid" for coordinate graphs, or "none" if multiple-choice with no extra work area needed.
5. If there is a section header (e.g. "Part I: Multiple Choice" or "Free Response"), record section_title.
"""


def _load_env_api_key() -> Optional[str]:
    """Finds and loads GEMINI_API_KEY from environment or .env file."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    for p in [Path.cwd() / ".env", Path(__file__).resolve().parents[2] / ".env"]:
        if p.exists():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    clean = line.strip()
                    if clean.startswith("GEMINI_API_KEY="):
                        val = clean.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            os.environ["GEMINI_API_KEY"] = val
                            return val
            except Exception:
                pass
    return None


class WorksheetParser:
    """Parses worksheet PDFs into canonical WorksheetSpec AST."""

    def __init__(
        self,
        doc_path: str | Path,
        api_key: Optional[str] = None,
        model_name: str = "gemini-flash-lite-latest",
    ):
        self.doc_path = Path(doc_path)
        if not self.doc_path.exists():
            raise FileNotFoundError(f"Document file not found: {self.doc_path}")

        self.api_key = api_key or _load_env_api_key()
        self.model_name = model_name
        self.is_docx = self.doc_path.suffix.lower() == ".docx"
        self._temp_pdf: Optional[Path] = None

        if self.is_docx:
            # Headless conversion of existing Word doc to PDF for page rendering
            self._temp_pdf = self.doc_path.parent / f".temp_{self.doc_path.stem}.pdf"
            self.pdf_path = convert_docx_to_pdf(self.doc_path, self._temp_pdf)
        else:
            self.pdf_path = self.doc_path

        self.extractor = PDFExtractor(self.pdf_path)
        self._client = None

    def close(self):
        if hasattr(self, "extractor") and self.extractor:
            self.extractor.close()
        if self._temp_pdf and self._temp_pdf.exists():
            try:
                self._temp_pdf.unlink(missing_ok=True)
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def client(self):
        if self._client is None:
            from google import genai
            import logging
            logging.getLogger("google_genai.models").addFilter(
                lambda record: "automatic function calling (AFC)" not in record.getMessage()
            )
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            else:
                self._client = genai.Client()
        return self._client

    def parse_page_vision(self, page_image_path: str | Path, page_number: int) -> RawPageExtraction:
        """Sends a rendered page image to Gemini Flash to extract problems and diagram locations."""
        img_p = Path(page_image_path)
        img_bytes = img_p.read_bytes()

        import time
        from google.genai import types

        response = None
        for attempt in range(4):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=[
                        types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                        WORKSHEET_VISION_PROMPT,
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=RawPageExtraction,
                        temperature=0.1,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                    ),
                )
                break
            except Exception as e:
                err_str = str(e)
                if ("503" in err_str or "429" in err_str or "UNAVAILABLE" in err_str or "RESOURCE_EXHAUSTED" in err_str) and attempt < 3:
                    wait_sec = 2.0 * (attempt + 1)
                    time.sleep(wait_sec)
                else:
                    raise

        try:
            parsed = json.loads(response.text)
            return RawPageExtraction.model_validate(parsed)
        except Exception:
            raw = response.text.strip()
            if raw.startswith("```json"):
                raw = raw.split("```json", 1)[1].split("```", 1)[0].strip()
            elif raw.startswith("```"):
                raw = raw.split("```", 1)[1].split("```", 1)[0].strip()
            parsed = json.loads(raw)
            return RawPageExtraction.model_validate(parsed)

    def parse_worksheet(
        self,
        workspace_dir: Optional[str | Path] = None,
        ordering: SectionOrdering = SectionOrdering.STRICT,
        default_columns: int = 2,
    ) -> WorksheetSpec:
        """Executes end-to-end document parsing and diagram harvesting."""
        ws_dir = Path(workspace_dir) if workspace_dir else self.doc_path.parent / f".ws_{self.doc_path.stem}"
        ws_dir.mkdir(parents=True, exist_ok=True)
        media_dir = ws_dir / "media"
        media_dir.mkdir(parents=True, exist_ok=True)
        rendered_dir = ws_dir / "rendered_pages"
        rendered_dir.mkdir(parents=True, exist_ok=True)

        if self.is_docx:
            extract_docx_media(self.doc_path, media_dir)

        doc_info = self.extractor.get_document_info()
        raw_title = doc_info.get("title") or ""
        if not raw_title or raw_title.startswith(".temp_") or self.is_docx:
            title = self.doc_path.stem.replace("_", " ").title()
        else:
            title = raw_title

        spec = WorksheetSpec(
            title=title,
            default_columns=default_columns,
            sections=[],
        )

        current_section = WorksheetSection(
            id="section_1",
            title=None,
            ordering=ordering,
            problems=[],
        )

        for page_idx in range(1, self.extractor.page_count + 1):
            page_png = rendered_dir / f"page_{page_idx}.png"
            if not page_png.exists():
                self.extractor.render_page_to_png(page_idx, page_png, dpi=200)

            # Vision extraction
            raw_page = self.parse_page_vision(page_png, page_idx)

            if raw_page.section_title and raw_page.section_title != current_section.title:
                if current_section.problems:
                    spec.sections.append(current_section)
                current_section = WorksheetSection(
                    id=f"section_{len(spec.sections) + 1}",
                    title=raw_page.section_title,
                    instructions=raw_page.section_instructions,
                    ordering=ordering,
                    problems=[],
                )

            # Process problems on this page
            for raw_p in raw_page.problems:
                prob_image: Optional[ProblemImage] = None

                # Extract diagram asset if present
                if raw_p.has_diagram and raw_p.diagram_bbox and len(raw_p.diagram_bbox) == 4:
                    raw_crop_path = media_dir / f"p{page_idx}_{raw_p.id}_raw.png"
                    self.extractor.extract_region(
                        page_number=page_idx,
                        bbox=raw_p.diagram_bbox,
                        output_path=raw_crop_path,
                        dpi=300,
                    )

                    # Auto-crop empty margins & determine true aspect ratio
                    clean_crop_path = media_dir / f"p{page_idx}_{raw_p.id}.png"
                    cropped_p, w_px, h_px, ar = auto_crop_image(
                        raw_crop_path,
                        clean_crop_path,
                        tolerance=15,
                        padding_px=4,
                    )

                    # Calculate dynamic scale bounds
                    col_width_est = (spec.printable_width_in - (default_columns - 1) * spec.column_gap_in) / max(1, default_columns)
                    scale_bounds = estimate_image_scale_bounds(
                        image_path=clean_crop_path,
                        native_width_px=w_px,
                        native_height_px=h_px,
                        aspect_ratio=ar,
                        bbox=raw_p.diagram_bbox,
                        page_width_in=spec.page_width_in,
                        col_width_in=col_width_est,
                    )

                    # Blend with LLM vision verification if provided
                    min_w = scale_bounds.min_width_in
                    if raw_p.diagram_min_width_in and raw_p.diagram_min_width_in > 0:
                        min_w = max(min_w, raw_p.diagram_min_width_in)
                    max_w = scale_bounds.max_width_in
                    if raw_p.diagram_max_width_in and raw_p.diagram_max_width_in > 0:
                        max_w = min(max_w, raw_p.diagram_max_width_in)
                    max_w = max(min_w, max_w)

                    category = raw_p.diagram_category or scale_bounds.category

                    prob_image = ProblemImage(
                        media_path=str(clean_crop_path.resolve()),
                        native_width_px=w_px,
                        native_height_px=h_px,
                        aspect_ratio=ar,
                        auto_cropped=True,
                        caption=raw_p.diagram_caption,
                        bbox=raw_p.diagram_bbox,
                        source_width_in=scale_bounds.source_width_in,
                        source_height_in=scale_bounds.source_height_in,
                        min_width_in=min_w,
                        preferred_width_in=scale_bounds.preferred_width_in,
                        max_width_in=max_w,
                        has_fine_text=scale_bounds.has_fine_text,
                        category=category,
                        elasticity=scale_bounds.elasticity,
                    )

                # Workspace config
                ws_type_str = raw_p.workspace_type.lower()
                ws_type = WorkspaceType.BLANK
                if "box" in ws_type_str:
                    ws_type = WorkspaceType.BOX
                elif "grid" in ws_type_str:
                    ws_type = WorkspaceType.GRID
                elif "none" in ws_type_str or (raw_p.choices and raw_p.workspace_lines <= 0 and not raw_p.approx_workspace_height_in):
                    ws_type = WorkspaceType.NONE
                else:
                    ws_type = WorkspaceType.BLANK

                ws_cfg = WorkspaceConfig(
                    type=ws_type,
                    lines=max(0, raw_p.workspace_lines),
                    height_pt=raw_p.workspace_height_pt,
                    approx_height_in=raw_p.approx_workspace_height_in,
                    approx_area_sq_in=raw_p.approx_workspace_area_sq_in,
                )

                # Layout hint
                hint_str = raw_p.layout_hint.lower()
                layout_hint = LayoutHint.AUTO
                if "side" in hint_str:
                    layout_hint = LayoutHint.SIDE_BY_SIDE
                elif "stack" in hint_str:
                    layout_hint = LayoutHint.STACKED
                elif "full" in hint_str:
                    layout_hint = LayoutHint.FULL_WIDTH

                problem = Problem(
                    id=raw_p.id,
                    number=raw_p.number,
                    part=raw_p.part,
                    points=raw_p.points,
                    prompt_text=raw_p.prompt,
                    image=prob_image,
                    choices=raw_p.choices,
                    workspace=ws_cfg,
                    layout_hint=layout_hint,
                )
                current_section.problems.append(problem)

        if current_section.problems:
            spec.sections.append(current_section)

        return spec


```

### src\worksheet_packer\image_utils.py

```python
"""Image pre-processing and whitespace trimming utilities for worksheet diagrams.

Extracts bounding boxes of actual visual drawings, trims empty white/transparent margins,
computes true aspect ratios, and validates minimum scale thresholds for legibility.
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageChops, ImageFilter, ImageOps


@dataclass
class ScaleBoundsResult:
    """Scale bounds and classification for an image asset."""
    source_width_in: float
    source_height_in: float
    min_width_in: float
    preferred_width_in: float
    max_width_in: float
    category: str        # "formula_icon", "compact_shape", "detailed_diagram", "wide_grid"
    has_fine_text: bool
    elasticity: float


def auto_crop_image(
    image_path: str | Path,
    output_path: Optional[str | Path] = None,
    tolerance: int = 15,
    padding_px: int = 4,
) -> Tuple[Path, int, int, float]:
    """Trims solid white and transparent borders from an extracted diagram.

    Args:
        image_path: Path to original raster image.
        output_path: Optional path to save cropped result. If omitted, appends '_cropped'.
        tolerance: Color variance from pure white (0-255) to consider as background margin.
        padding_px: Safe perimeter padding in pixels to prevent clipping edge strokes.

    Returns:
        Tuple of (saved_cropped_path, width_px, height_px, aspect_ratio).
    """
    src = Path(image_path)
    if not src.exists():
        raise FileNotFoundError(f"Image not found for cropping: {src}")

    with Image.open(src) as img:
        # Convert to RGBA for consistent border detection
        rgba = img.convert("RGBA")
        width, height = rgba.size

        # Split channels
        r, g, b, a = rgba.split()

        # Step 1: Detect non-transparent pixels
        # Pixels with alpha > 15 are potential content
        alpha_mask = a.point(lambda p: 255 if p > 15 else 0)

        # Step 2: Detect non-white pixels
        # An RGB pixel is "white background" if R > 255 - tol and G > 255 - tol and B > 255 - tol
        threshold = max(0, 255 - tolerance)
        r_dark = r.point(lambda p: 255 if p < threshold else 0)
        g_dark = g.point(lambda p: 255 if p < threshold else 0)
        b_dark = b.point(lambda p: 255 if p < threshold else 0)

        # Combined color mask: any channel significantly below 255
        color_mask = ImageChops.lighter(r_dark, ImageChops.lighter(g_dark, b_dark))

        # Content is where it's not transparent AND not white
        content_mask = ImageChops.darker(alpha_mask, color_mask)

        bbox = content_mask.getbbox()

        if bbox is None:
            # Image is entirely blank or white; keep original
            crop_box = (0, 0, width, height)
        else:
            x0, y0, x1, y1 = bbox
            # Apply safety padding
            x0 = max(0, x0 - padding_px)
            y0 = max(0, y0 - padding_px)
            x1 = min(width, x1 + padding_px)
            y1 = min(height, y1 + padding_px)
            crop_box = (x0, y0, x1, y1)

        cropped_img = img.crop(crop_box)
        crop_w, crop_h = cropped_img.size
        aspect_ratio = float(crop_h) / float(crop_w) if crop_w > 0 else 1.0

        if output_path is None:
            out_p = src.parent / f"{src.stem}_cropped{src.suffix}"
        else:
            out_p = Path(output_path)

        out_p.parent.mkdir(parents=True, exist_ok=True)
        # Preserve format or default to PNG
        fmt = img.format if img.format else "PNG"
        cropped_img.save(str(out_p), format=fmt)

        return out_p, crop_w, crop_h, aspect_ratio


def inspect_diagram_dimensions(image_path: str | Path) -> Tuple[int, int, float]:
    """Inspects native dimensions and aspect ratio (H / W) of an image without modifying it."""
    p = Path(image_path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")
    with Image.open(p) as img:
        w, h = img.size
        ar = float(h) / float(w) if w > 0 else 1.0
        return w, h, ar


def estimate_image_scale_bounds(
    image_path: str | Path,
    native_width_px: int,
    native_height_px: int,
    aspect_ratio: float,
    bbox: Optional[List[int]] = None,
    page_width_in: float = 8.5,
    col_width_in: float = 3.5,
) -> ScaleBoundsResult:
    """Estimates content-aware scale bounds [min_w, pref_w, max_w] and classification for an image.

    Prevents formula icons (e.g. radical signs) from exploding into huge diagrams, while
    enforcing a strict legibility floor for detailed geometry figures with fine angle text.

    Args:
        image_path: File path of the image.
        native_width_px: Native cropped width in pixels.
        native_height_px: Native cropped height in pixels.
        aspect_ratio: True height-to-width ratio (H / W).
        bbox: Optional normalized bounding box [ymin, xmin, ymax, xmax] (0-1000 scale).
        page_width_in: Page width in inches (default 8.5).
        col_width_in: Target column width in inches (default 3.5).

    Returns:
        ScaleBoundsResult with source dimensions, bounds, category, fine_text flag, and elasticity.
    """
    # 1. Physical source width anchor
    if bbox and len(bbox) == 4 and (bbox[3] > bbox[1]):
        w_ratio = (bbox[3] - bbox[1]) / 1000.0
        h_ratio = (bbox[2] - bbox[0]) / 1000.0
        source_w = round(w_ratio * page_width_in, 2)
        source_h = round(h_ratio * 11.0, 2)
    else:
        # Fallback to ~180 DPI estimation
        source_w = round(native_width_px / 180.0, 2)
        source_h = round(native_height_px / 180.0, 2)

    # 2. Check for fine line / text density
    has_fine_text = True
    p = Path(image_path)
    if p.exists():
        try:
            with Image.open(p) as img:
                small = img.convert("L").resize((120, 120))
                edges = small.filter(ImageFilter.FIND_EDGES)
                px_data = edges.get_flattened_data() if hasattr(edges, "get_flattened_data") else edges.getdata()
                edge_pixels = sum(1 for px in px_data if px > 64)
                has_fine_text = (edge_pixels / 14400.0) > 0.05
        except Exception:
            has_fine_text = True

    # 3. Content classification & scale bounds derivation
    # Category A: Formula / Math Symbol Icon (e.g. radical expression, fraction, small symbol)
    if source_w <= 1.10 or (native_width_px < 220 and native_height_px < 150):
        category = "formula_icon"
        # Never let a formula icon balloon to fill the column!
        min_w = max(0.40, round(source_w * 0.85, 2))
        pref_w = min(1.25, max(0.65, round(source_w * 1.05, 2)))
        max_w = min(1.40, max(0.95, round(source_w * 1.30, 2)))
        elasticity = 0.5  # Modest compression

    # Category B: Wide Grid, Coordinate Plane, or Data Table
    elif aspect_ratio < 0.52 or source_w >= 3.20:
        category = "wide_grid"
        min_w = min(col_width_in * 0.70, max(2.20, round(col_width_in * 0.65, 2)))
        pref_w = min(col_width_in * 0.95, max(2.80, round(source_w, 2)))
        max_w = col_width_in
        elasticity = 0.8

    # Category C: Compact Shape / Diagram (simple geometric figure, single polygon)
    elif source_w <= 2.20 and not (aspect_ratio > 1.6 or aspect_ratio < 0.6):
        category = "compact_shape"
        min_w = 1.10
        pref_w = min(col_width_in * 0.85, max(1.50, round(source_w, 2)))
        max_w = min(col_width_in * 0.95, max(2.40, round(source_w * 1.25, 2)))
        elasticity = 1.0

    # Category D: Detailed Geometry Diagram (angles, line labels, complex markings)
    else:
        category = "detailed_diagram"
        # High legibility floor: below ~1.45 in, angle markings like 30° become illegible
        min_w = 1.45
        pref_w = min(col_width_in * 0.90, max(1.90, round(source_w, 2)))
        max_w = min(col_width_in, max(3.00, round(source_w * 1.20, 2)))
        elasticity = 1.0

    # Safety clamps
    min_w = min(min_w, col_width_in)
    pref_w = max(min_w, min(pref_w, col_width_in))
    max_w = max(pref_w, min(max_w, col_width_in))

    return ScaleBoundsResult(
        source_width_in=source_w,
        source_height_in=source_h,
        min_width_in=min_w,
        preferred_width_in=pref_w,
        max_width_in=max_w,
        category=category,
        has_fine_text=has_fine_text,
        elasticity=elasticity,
    )


def audit_image_boundaries(
    image_path: str | Path,
    bg_threshold: int = 240,
    edge_density_tolerance: float = 0.015,
) -> Dict[str, Any]:
    """Audits image edge perimeters for non-background pixels indicative of cutoffs.

    Scans the outer 2 rows and columns of an image asset to detect whether visual content
    (e.g., axes, formulas, exponent text, or diagram strokes) was truncated by a tight crop.

    Args:
        image_path: Path to the image file to audit.
        bg_threshold: RGB channel value above which a pixel is considered white background (0-255).
        edge_density_tolerance: Max allowed proportion of content pixels along any edge before flagging.

    Returns:
        Dict with status ("PASS" | "FAIL"), filename, cutoffs list, and per-edge density metrics.
    """
    img_p = Path(image_path)
    if not img_p.exists():
        raise FileNotFoundError(f"Image not found: {img_p}")

    with Image.open(img_p) as raw_img:
        img = raw_img.convert("RGBA")
        w, h = img.size
        if w == 0 or h == 0:
            return {
                "status": "FAIL",
                "name": img_p.name,
                "error": "Empty image",
                "cutoffs": [],
                "densities": {"top": 0.0, "bottom": 0.0, "left": 0.0, "right": 0.0},
            }

        pixels = img.load()

        def is_content(x: int, y: int) -> bool:
            r, g, b, a = pixels[x, y]
            if a < 30:  # transparent
                return False
            return r < bg_threshold or g < bg_threshold or b < bg_threshold

        def scan_edge(coords: List[Tuple[int, int]]) -> float:
            content_count = sum(1 for (x, y) in coords if is_content(x, y))
            return content_count / max(1, len(coords))

        top_density = scan_edge([(x, y) for y in range(min(2, h)) for x in range(w)])
        bottom_density = scan_edge([(x, y) for y in range(max(0, h - 2), h) for x in range(w)])
        left_density = scan_edge([(x, y) for x in range(min(2, w)) for y in range(h)])
        right_density = scan_edge([(x, y) for x in range(max(0, w - 2), w) for y in range(h)])

        cutoffs: List[Tuple[str, float]] = []
        if top_density > edge_density_tolerance:
            cutoffs.append(("TOP", top_density))
        if bottom_density > edge_density_tolerance:
            cutoffs.append(("BOTTOM", bottom_density))
        if left_density > edge_density_tolerance:
            cutoffs.append(("LEFT", left_density))
        if right_density > edge_density_tolerance:
            cutoffs.append(("RIGHT", right_density))

        return {
            "status": "FAIL" if cutoffs else "PASS",
            "name": img_p.name,
            "cutoffs": cutoffs,
            "densities": {
                "top": top_density,
                "bottom": bottom_density,
                "left": left_density,
                "right": right_density,
            },
        }


class ImageBoundaryAuditor:
    """Audits image edge perimeters for non-background pixels indicative of cutoffs."""

    def __init__(self, bg_threshold: int = 240, edge_density_tolerance: float = 0.015):
        self.bg_threshold = bg_threshold
        self.edge_density_tolerance = edge_density_tolerance

    def audit_image_file(self, image_path: str | Path) -> Dict[str, Any]:
        return audit_image_boundaries(
            image_path=image_path,
            bg_threshold=self.bg_threshold,
            edge_density_tolerance=self.edge_density_tolerance,
        )




```

### src\worksheet_packer\docx_renderer.py

```python
"""Deterministic DOCX Renderer for Worksheets.

Transforms a RenderPlan AST into a high-density, professional Word document (.docx).
Enforces invisible structural tables with OpenXML w:cantSplit on all problem containers
so diagrams, text, and workspaces stay strictly bound together without page-boundary splits.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

from .worksheet_ast import (
    LayoutDecision,
    PlacedProblem,
    PlacedSectionHeader,
    Problem,
    RenderPlan,
    WorkspaceType,
    parse_prompt_parts,
)
from pdf_to_docx.docx_compiler import hex_to_rgb


def clear_table_borders(table) -> None:
    """Removes all borders from a table to make it an invisible layout frame."""
    tblPr = table._tbl.tblPr
    old = tblPr.find(qn("w:tblBorders"))
    if old is not None:
        tblPr.remove(old)
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:left w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:bottom w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:right w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:insideH w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'  <w:insideV w:val="none" w:sz="0" w:space="0" w:color="auto"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


def make_row_cant_split(row) -> None:
    """Prevents a table row from breaking mid-cell across a page boundary (w:cantSplit)."""
    trPr = row._tr.get_or_add_trPr()
    if trPr.find(qn("w:cantSplit")) is None:
        trPr.append(OxmlElement("w:cantSplit"))


def set_cell_width(cell, width_in: float) -> None:
    """Sets explicit cell width in twips (1/1440 of an inch)."""
    twips = max(100, int(width_in * 1440))
    tcPr = cell._tc.get_or_add_tcPr()
    # Remove existing tcW if present
    old_w = tcPr.find(qn("w:tcW"))
    if old_w is not None:
        tcPr.remove(old_w)
    tcW = parse_xml(f'<w:tcW {nsdecls("w")} w:w="{twips}" w:type="dxa"/>')
    tcPr.append(tcW)


def set_cell_padding(cell, top: int = 40, bottom: int = 40, left: int = 40, right: int = 40) -> None:
    """Sets cell padding in twips."""
    tcPr = cell._tc.get_or_add_tcPr()
    old_mar = tcPr.find(qn("w:tcMar"))
    if old_mar is not None:
        tcPr.remove(old_mar)
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>\n'
        f'  <w:top w:w="{top}" w:type="dxa"/>\n'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>\n'
        f'  <w:left w:w="{left}" w:type="dxa"/>\n'
        f'  <w:right w:w="{right}" w:type="dxa"/>\n'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def clean_math_text_for_docx(text: str) -> str:
    """Replaces common LaTeX math escape sequences with clean Unicode symbols for Word."""
    if not text:
        return ""
    import re

    out = text
    # Fix potential double-encoded UTF-8 artifacts (e.g. 180Â° -> 180°)
    out = out.replace("Â°", "°").replace("Â", "")

    # Superscript map for roots and powers
    sup_map = {
        "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴",
        "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹",
        "+": "⁺", "-": "⁻", "=": "⁼", "(": "⁽", ")": "⁾",
        "n": "ⁿ", "x": "ˣ", "y": "ʸ",
    }

    # Translate \sqrt[n]{x} -> ⁿ√(x)
    def _repl_root(m):
        idx = "".join(sup_map.get(ch, ch) for ch in m.group(1))
        content = m.group(2)
        return f"{idx}√({content})"
    out = re.sub(r"\\sqrt\[([^\]]+)\]\{([^\}]+)\}", _repl_root, out)

    # Translate \sqrt{x} -> √(x)
    out = re.sub(r"\\sqrt\{([^\}]+)\}", r"√(\1)", out)

    # Translate x^{n} or x^n -> xⁿ
    def _repl_sup(m):
        base = m.group(1)
        exp = m.group(2)
        sup = "".join(sup_map.get(ch, ch) for ch in exp)
        return f"{base}{sup}"
    out = re.sub(r"([A-Za-z0-9\)])\^\{([^\}]+)\}", _repl_sup, out)
    out = re.sub(r"([A-Za-z0-9\)])\^([0-9a-zA-Z\+\-])", _repl_sup, out)

    replacements = [
        (r"\ell", "ℓ"),
        (r"^{\circ}", "°"),
        (r"^\circ", "°"),
        (r"\circ", "°"),
        (r"\theta", "θ"),
        (r"\alpha", "α"),
        (r"\beta", "β"),
        (r"\pi", "π"),
        (r"\le", "≤"),
        (r"\ge", "≥"),
        (r"\neq", "≠"),
        (r"\approx", "≈"),
        (r"\times", "×"),
        (r"\div", "÷"),
        (r"\pm", "±"),
        (r"\parallel", "∥"),
        (r"\perp", "⊥"),
        (r"\angle", "∠"),
        (r"\cong", "≅"),
        (r"\sim", "∼"),
        (r"\Delta", "Δ"),
        (r"\triangle", "△"),
        (r"\(", ""),
        (r"\)", ""),
        (r"\[", ""),
        (r"\]", ""),
    ]
    for old, new in replacements:
        out = out.replace(old, new)
    out = out.replace("\\n", " ")
    out = re.sub(r"\$([^\$]+)\$", r"\1", out)
    # Clean up double-encoded or mangled characters (e.g. â„“, â€, Â)
    out = out.replace("Â°", "°").replace("Â", "").replace("â„“", "ℓ").replace("â€“", "–").replace("â€”", "—")
    return out


class DocxWorksheetRenderer:
    """Compiles a RenderPlan into an editable, space-optimized Word (.docx) document."""

    def __init__(self, plan: RenderPlan):
        self.plan = plan
        self.ws = plan.worksheet
        self.doc = Document()
        self._configure_document()

    def _configure_document(self) -> None:
        """Sets page dimensions, margins, and standard typography styles."""
        normal = self.doc.styles["Normal"]
        normal.font.name = self.ws.default_font
        normal.font.size = Pt(self.ws.default_font_size_pt)
        normal.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        normal.paragraph_format.line_spacing = 1.05
        normal.paragraph_format.space_after = Pt(2)

        section = self.doc.sections[0]
        section.page_width = Inches(self.ws.page_width_in)
        section.page_height = Inches(self.ws.page_height_in)
        section.top_margin = Inches(self.ws.margins.top_in)
        section.bottom_margin = Inches(self.ws.margins.bottom_in)
        section.left_margin = Inches(self.ws.margins.left_in)
        section.right_margin = Inches(self.ws.margins.right_in)

        # Configure columns on the section
        if self.ws.default_columns > 1:
            sectPr = section._sectPr
            cols = sectPr.xpath("./w:cols")
            gap_twips = int(self.ws.column_gap_in * 1440)
            if cols:
                cols[0].set(qn("w:num"), str(self.ws.default_columns))
                cols[0].set(qn("w:space"), str(gap_twips))
            else:
                col_elem = parse_xml(
                    f'<w:cols {nsdecls("w")} w:num="{self.ws.default_columns}" w:space="{gap_twips}"/>'
                )
                sectPr.append(col_elem)

    def _render_header_block(self) -> None:
        """Renders title and student name/date header at top of first page."""
        # Top title & student info table
        table = self.doc.add_table(rows=1, cols=2)
        clear_table_borders(table)
        make_row_cant_split(table.rows[0])
        table.alignment = WD_TABLE_ALIGNMENT.CENTER

        col_w = self.ws.printable_width_in / 2.0
        set_cell_width(table.cell(0, 0), col_w)
        set_cell_width(table.cell(0, 1), col_w)
        set_cell_padding(table.cell(0, 0), top=0, bottom=60, left=0, right=40)
        set_cell_padding(table.cell(0, 1), top=0, bottom=60, left=40, right=0)

        # Left cell: Title & Subtitle
        c_left = table.cell(0, 0)
        p_title = c_left.paragraphs[0]
        p_title.paragraph_format.space_after = Pt(2)
        r_title = p_title.add_run(self.ws.title)
        r_title.bold = True
        r_title.font.size = Pt(14)
        r_title.font.color.rgb = hex_to_rgb(self.ws.theme_hex)

        if self.ws.subtitle:
            p_sub = c_left.add_paragraph()
            p_sub.paragraph_format.space_after = Pt(2)
            r_sub = p_sub.add_run(self.ws.subtitle)
            r_sub.italic = True
            r_sub.font.size = Pt(10)
            r_sub.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

        # Right cell: Name / Date / Period line
        c_right = table.cell(0, 1)
        p_hdr = c_right.paragraphs[0]
        p_hdr.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_hdr.paragraph_format.space_after = Pt(2)
        if self.ws.header_right:
            r_hdr = p_hdr.add_run(self.ws.header_right)
            r_hdr.font.size = Pt(9.5)
            r_hdr.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

        # Subtle separator
        p_sep = self.doc.add_paragraph()
        p_sep.paragraph_format.space_before = Pt(2)
        p_sep.paragraph_format.space_after = Pt(8)
        p_sep_run = p_sep.add_run("―" * 55)
        p_sep_run.font.size = Pt(8)
        p_sep_run.font.color.rgb = RGBColor(0xCC, 0xCC, 0xCC)

    def _apply_prompt_text(
        self,
        container_or_paragraph,
        problem: Problem,
        placed: Optional[PlacedProblem] = None,
        font_size_pt: Optional[float] = None,
    ) -> None:
        """Adds question number prefix, bold sub-part letters, and styled prompt runs to cell or paragraph."""
        fs = font_size_pt or self.ws.default_font_size_pt
        theme_rgb = hex_to_rgb(self.ws.theme_hex)

        is_cell = hasattr(container_or_paragraph, "paragraphs")
        first_p = container_or_paragraph.paragraphs[0] if is_cell else container_or_paragraph
        cell = container_or_paragraph if is_cell else None

        label = problem.full_label

        if problem.prompt_runs and not problem.prompt_text:
            if label:
                r_lbl = first_p.add_run(f"{label} ")
                r_lbl.bold = True
                r_lbl.font.color.rgb = theme_rgb
                r_lbl.font.size = Pt(fs)

            for r_spec in problem.prompt_runs:
                clean_txt = clean_math_text_for_docx(r_spec.text)
                r = first_p.add_run(clean_txt)
                r.bold = r_spec.bold
                r.italic = r_spec.italic
                r.underline = r_spec.underline
                if r_spec.is_math:
                    r.font.name = "Cambria Math"
                    r.italic = True
                if r_spec.color_hex:
                    r.font.color.rgb = hex_to_rgb(r_spec.color_hex)
                r_fs = r_spec.font_size_pt or fs
                r.font.size = Pt(r_fs)
            return

        raw_text = problem.prompt_text or ""
        if label and raw_text.startswith(label):
            raw_text = raw_text[len(label):].strip()

        segments = parse_prompt_parts(raw_text)
        if not segments:
            segments = [(None, "")]

        sub_parts = [(lbl, txt) for lbl, txt in segments if lbl is not None]
        num_sub_parts = len(sub_parts)

        # Detect available space to include open space between parts
        ws_h = placed.workspace_height_in if placed else 0.0
        spacing_after = getattr(placed, "spacing_after_in", 0.10) if placed else 0.10

        inter_part_space_pt = 3.0
        if num_sub_parts >= 2 and cell is not None and not getattr(placed, "_sub_parts_spaced", False):
            if ws_h >= 0.35 and placed and placed.problem.workspace.type in (WorkspaceType.BLANK, WorkspaceType.LINES):
                # Distribute part of the student workspace between sub-parts
                inter_space_in = min(0.40, max(0.12, (ws_h * 0.65) / num_sub_parts))
                inter_part_space_pt = inter_space_in * 72.0
                distributed_in = (num_sub_parts - 1) * inter_space_in
                placed.workspace_height_in = max(0.15, ws_h - distributed_in)
                placed._sub_parts_spaced = True
                placed._inter_part_space_pt = inter_part_space_pt
            elif spacing_after >= 0.30:
                inter_part_space_pt = min(14.0, max(6.0, spacing_after * 24.0))
                placed._sub_parts_spaced = True
                placed._inter_part_space_pt = inter_part_space_pt
        elif getattr(placed, "_sub_parts_spaced", False):
            inter_part_space_pt = getattr(placed, "_inter_part_space_pt", 3.0)

        for idx, (part_lbl, content) in enumerate(segments):
            if idx == 0:
                p = first_p
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2 if part_lbl is None else inter_part_space_pt)

                if label:
                    r_lbl = p.add_run(f"{label} ")
                    r_lbl.bold = True
                    r_lbl.font.color.rgb = theme_rgb
                    r_lbl.font.size = Pt(fs)

                if part_lbl:
                    r_part = p.add_run(f"{part_lbl} ")
                    r_part.bold = True
                    r_part.font.color.rgb = theme_rgb
                    r_part.font.size = Pt(fs)

                if content:
                    clean_c = clean_math_text_for_docx(content)
                    r_txt = p.add_run(clean_c)
                    r_txt.font.size = Pt(fs)
            else:
                if cell is not None:
                    p = cell.add_paragraph()
                else:
                    first_p.add_run("\n")
                    p = first_p

                if part_lbl:
                    if cell is not None:
                        p.paragraph_format.left_indent = Inches(0.15)
                        p.paragraph_format.space_before = Pt(2)
                        p.paragraph_format.space_after = Pt(inter_part_space_pt if idx < len(segments) - 1 else 2)
                    r_part = p.add_run(f"{part_lbl} ")
                    r_part.bold = True
                    r_part.font.color.rgb = theme_rgb
                    r_part.font.size = Pt(fs)
                else:
                    if cell is not None:
                        p.paragraph_format.space_before = Pt(1)
                        p.paragraph_format.space_after = Pt(2)

                if content:
                    clean_c = clean_math_text_for_docx(content)
                    r_txt = p.add_run(clean_c)
                    r_txt.font.size = Pt(fs)

    def _apply_choices(self, container_cell, problem: Problem, font_size_pt: Optional[float] = None) -> None:
        """Appends multiple choice options to a cell."""
        if not problem.choices:
            return
        for ch in problem.choices:
            p = container_cell.add_paragraph()
            p.paragraph_format.left_indent = Inches(0.15)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(1)
            r_lbl = p.add_run(f"{ch.label} ")
            r_lbl.bold = True
            if font_size_pt:
                r_lbl.font.size = Pt(font_size_pt)
            if ch.runs:
                for r_spec in ch.runs:
                    clean_c = clean_math_text_for_docx(r_spec.text)
                    r = p.add_run(clean_c)
                    r.bold = r_spec.bold
                    r.italic = r_spec.italic
                    r_fs = r_spec.font_size_pt or font_size_pt
                    if r_fs:
                        r.font.size = Pt(r_fs)
            else:
                clean_c = clean_math_text_for_docx(ch.text)
                r = p.add_run(clean_c)
                if font_size_pt:
                    r.font.size = Pt(font_size_pt)

    def _render_workspace_in_cell(self, cell, placed: PlacedProblem) -> None:
        """Renders answer lines or response box in designated cell."""
        ws_cfg = placed.problem.workspace
        if ws_cfg.type == WorkspaceType.NONE:
            return

        p = cell.paragraphs[0]
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(2)

        if ws_cfg.type == WorkspaceType.BOX or ws_cfg.type == WorkspaceType.GRID:
            # Render a framed response box
            sub_tbl = cell.add_table(rows=1, cols=1)
            sub_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            box_cell = sub_tbl.cell(0, 0)
            h_pt = max(40.0, placed.workspace_height_in * 72.0)
            sub_tbl.rows[0].height = Pt(h_pt)
            make_row_cant_split(sub_tbl.rows[0])
            set_cell_width(box_cell, placed.width_in * 0.95)
            # Add light border
            tcPr = box_cell._tc.get_or_add_tcPr()
            borders = parse_xml(
                f'<w:tcBorders {nsdecls("w")}>\n'
                f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>\n'
                f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>\n'
                f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>\n'
                f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="BBBBBB"/>\n'
                f'</w:tcBorders>'
            )
            tcPr.append(borders)
            if ws_cfg.type == WorkspaceType.GRID:
                p_grid = box_cell.paragraphs[0]
                r_grid = p_grid.add_run("[ Graph / Grid Area ]")
                r_grid.font.size = Pt(8.5)
                r_grid.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
        elif ws_cfg.type == WorkspaceType.LINES or ws_cfg.type == WorkspaceType.BLANK:
            # Clean empty whitespace for student work (no blank underlines)
            h_pt = max(14.0, placed.workspace_height_in * 72.0)
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.line_spacing = Pt(1)
            p.paragraph_format.space_after = Pt(max(4.0, h_pt - 8.0))

    def _render_side_by_side_problem(self, placed: PlacedProblem, has_next_in_column: bool = True) -> None:
        """Renders Layout A: Side-by-side text (left) and diagram (right) in an invisible table."""
        prob = placed.problem
        img = prob.image
        col_w = placed.width_in

        # 2 rows: Row 0 has (Text, Image), Row 1 has (Workspace across both)
        has_workspace = prob.workspace.type != WorkspaceType.NONE
        num_rows = 2 if has_workspace else 1

        table = self.doc.add_table(rows=num_rows, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        clear_table_borders(table)

        for row in table.rows:
            make_row_cant_split(row)

        text_w = placed.text_render_width_in
        img_w = placed.image_render_width_in

        table.columns[0].width = Inches(text_w)
        table.columns[1].width = Inches(img_w)
        set_cell_width(table.cell(0, 0), text_w)
        set_cell_width(table.cell(0, 1), img_w)
        set_cell_padding(table.cell(0, 0), top=20, bottom=20, left=20, right=40)
        set_cell_padding(table.cell(0, 1), top=20, bottom=20, left=20, right=20)

        # Row 0, Cell 0: Question Text + Choices
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        c_text = table.cell(0, 0)
        p_text = c_text.paragraphs[0]
        p_text.paragraph_format.space_before = Pt(0)
        p_text.paragraph_format.space_after = Pt(2)
        self._apply_prompt_text(c_text, prob, placed=placed, font_size_pt=fs)
        self._apply_choices(c_text, prob, font_size_pt=fs)

        # Row 0, Cell 1: Image
        c_img = table.cell(0, 1)
        p_img = c_img.paragraphs[0]
        p_img.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        p_img.paragraph_format.space_before = Pt(0)
        p_img.paragraph_format.space_after = Pt(0)

        if img and img.media_path and Path(img.media_path).exists():
            r_img = p_img.add_run()
            # Explicit width preserves native aspect ratio deterministically
            safe_img_w = max(0.5, img_w - 0.05)
            r_img.add_picture(img.media_path, width=Inches(safe_img_w))
            if img.caption:
                p_cap = c_img.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_cap.add_run(img.caption)
                r_cap.font.size = Pt(8)
                r_cap.italic = True

        # Row 1: Workspace spanning both columns
        if has_workspace:
            table.rows[1].height = Pt(max(14.0, placed.workspace_height_in * 72.0))
            c_work = table.cell(1, 0)
            c_work.merge(table.cell(1, 1))
            set_cell_width(c_work, col_w)
            set_cell_padding(c_work, top=20, bottom=20, left=20, right=20)
            self._render_workspace_in_cell(c_work, placed)

        # Inter-problem spacing paragraph (only between problems in the same column)
        if has_next_in_column:
            space_pt = max(4.0, getattr(placed, "spacing_after_in", 0.10) * 72.0)
            p_space = self.doc.add_paragraph()
            p_space.paragraph_format.space_before = Pt(0)
            p_space.paragraph_format.space_after = Pt(space_pt)

    def _render_stacked_problem(self, placed: PlacedProblem, has_next_in_column: bool = True) -> None:
        """Renders Layout B: Stacked text (top), diagram (middle), workspace (bottom)."""
        prob = placed.problem
        img = prob.image
        col_w = placed.width_in

        has_workspace = prob.workspace.type != WorkspaceType.NONE
        num_rows = 3 if has_workspace else 2

        table = self.doc.add_table(rows=num_rows, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        clear_table_borders(table)

        for row in table.rows:
            make_row_cant_split(row)

        for r_idx in range(num_rows):
            set_cell_width(table.cell(r_idx, 0), col_w)
            set_cell_padding(table.cell(r_idx, 0), top=20, bottom=20, left=20, right=20)

        # Row 0: Text + choices
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        c_text = table.cell(0, 0)
        p_text = c_text.paragraphs[0]
        p_text.paragraph_format.space_before = Pt(0)
        p_text.paragraph_format.space_after = Pt(2)
        self._apply_prompt_text(c_text, prob, placed=placed, font_size_pt=fs)
        self._apply_choices(c_text, prob, font_size_pt=fs)

        # Row 1: Centered diagram
        c_img = table.cell(1, 0)
        p_img = c_img.paragraphs[0]
        p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_img.paragraph_format.space_before = Pt(2)
        p_img.paragraph_format.space_after = Pt(2)

        if img and img.media_path and Path(img.media_path).exists():
            r_img = p_img.add_run()
            r_img.add_picture(img.media_path, width=Inches(placed.image_render_width_in))
            if img.caption:
                p_cap = c_img.add_paragraph()
                p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r_cap = p_cap.add_run(img.caption)
                r_cap.font.size = Pt(8)
                r_cap.italic = True

        # Row 2: Workspace
        if has_workspace:
            table.rows[2].height = Pt(max(14.0, placed.workspace_height_in * 72.0))
            c_work = table.cell(2, 0)
            self._render_workspace_in_cell(c_work, placed)

        if has_next_in_column:
            space_pt = max(4.0, getattr(placed, "spacing_after_in", 0.10) * 72.0)
            p_space = self.doc.add_paragraph()
            p_space.paragraph_format.space_before = Pt(0)
            p_space.paragraph_format.space_after = Pt(space_pt)

    def _render_text_only_problem(self, placed: PlacedProblem, has_next_in_column: bool = True) -> None:
        """Renders text-only problem inside an atomic invisible table."""
        prob = placed.problem
        col_w = placed.width_in
        has_workspace = prob.workspace.type != WorkspaceType.NONE

        table = self.doc.add_table(rows=2 if has_workspace else 1, cols=1)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        clear_table_borders(table)

        for row in table.rows:
            make_row_cant_split(row)

        fs = placed.font_size_pt or self.ws.default_font_size_pt
        c_text = table.cell(0, 0)
        set_cell_width(c_text, col_w)
        set_cell_padding(c_text, top=20, bottom=20, left=20, right=20)
        p_text = c_text.paragraphs[0]
        p_text.paragraph_format.space_before = Pt(0)
        p_text.paragraph_format.space_after = Pt(2)
        self._apply_prompt_text(c_text, prob, placed=placed, font_size_pt=fs)
        self._apply_choices(c_text, prob, font_size_pt=fs)

        if has_workspace:
            table.rows[1].height = Pt(max(14.0, placed.workspace_height_in * 72.0))
            c_work = table.cell(1, 0)
            set_cell_width(c_work, col_w)
            set_cell_padding(c_work, top=20, bottom=20, left=20, right=20)
            self._render_workspace_in_cell(c_work, placed)

        if has_next_in_column:
            space_pt = max(4.0, getattr(placed, "spacing_after_in", 0.10) * 72.0)
            p_space = self.doc.add_paragraph()
            p_space.paragraph_format.space_before = Pt(0)
            p_space.paragraph_format.space_after = Pt(space_pt)

    def _render_section_header(self, header: PlacedSectionHeader) -> None:
        """Renders section title and instructions."""
        if header.title:
            p_title = self.doc.add_paragraph()
            p_title.paragraph_format.keep_with_next = True
            p_title.paragraph_format.space_before = Pt(8)
            p_title.paragraph_format.space_after = Pt(2)
            clean_title = clean_math_text_for_docx(header.title)
            r = p_title.add_run(clean_title)
            r.bold = True
            r.font.size = Pt(11.5)
            r.font.color.rgb = hex_to_rgb(self.ws.theme_hex)

        if header.instructions:
            p_inst = self.doc.add_paragraph()
            p_inst.paragraph_format.keep_with_next = True
            p_inst.paragraph_format.space_before = Pt(0)
            p_inst.paragraph_format.space_after = Pt(4)
            clean_inst = clean_math_text_for_docx(header.instructions)
            r = p_inst.add_run(clean_inst)
            r.italic = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(0x55, 0x55, 0x55)

    def render(self, output_docx_path: str | Path) -> Path:
        """Executes document rendering and writes out the formatted .docx file."""
        out_path = Path(output_docx_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        self._render_header_block()

        for page_idx, page in enumerate(self.plan.pages):
            if page_idx > 0:
                self.doc.add_page_break()

            current_col = 0
            for idx, item in enumerate(page.items):
                if isinstance(item, PlacedSectionHeader):
                    self._render_section_header(item)
                elif isinstance(item, PlacedProblem):
                    if self.ws.default_columns > 1 and item.col_index > current_col:
                        p_break = self.doc.add_paragraph()
                        p_break.paragraph_format.space_before = Pt(0)
                        p_break.paragraph_format.space_after = Pt(0)
                        p_break.paragraph_format.line_spacing = Pt(1)
                        run = p_break.add_run()
                        run.font.size = Pt(1)
                        run.add_break(WD_BREAK.COLUMN)
                        current_col = item.col_index

                    next_in_col = any(
                        isinstance(other, PlacedProblem) and other.col_index == item.col_index
                        for other in page.items[idx + 1 :]
                    )

                    if item.layout == LayoutDecision.SIDE_BY_SIDE:
                        self._render_side_by_side_problem(item, has_next_in_column=next_in_col)
                    elif item.layout == LayoutDecision.STACKED:
                        self._render_stacked_problem(item, has_next_in_column=next_in_col)
                    else:
                        self._render_text_only_problem(item, has_next_in_column=next_in_col)

        self.doc.save(str(out_path))
        return out_path


```

### src\worksheet_packer\latex_renderer.py

```python
"""Deterministic LaTeX Renderer for Worksheets.

Compiles a RenderPlan AST into publication-grade, compilable LaTeX (.tex)
and invokes local LaTeX engines (pdflatex, xelatex, tectonic, latexmk) to output PDFs.
Uses side-by-side minipage environments and multicols for whitespace optimization.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple

from .worksheet_ast import (
    LayoutDecision,
    PlacedProblem,
    PlacedSectionHeader,
    Problem,
    RenderPlan,
    WorkspaceType,
    parse_prompt_parts,
)
from pdf_to_latex.latex_compiler import (
    compile_tex_to_pdf,
    escape_latex_text,
    format_hex_color,
)


class LatexWorksheetRenderer:
    """Compiles a RenderPlan into clean, compilable LaTeX code and PDFs."""

    def __init__(self, plan: RenderPlan):
        self.plan = plan
        self.ws = plan.worksheet
        self.theme_color = format_hex_color(self.ws.theme_hex)

    def _render_preamble(self) -> str:
        """Generates LaTeX document preamble with required packages."""
        lines = [
            "\\documentclass[10.5pt,letterpaper]{article}",
            "% --- Core Typography & Geometry ---",
            "\\usepackage[utf8]{inputenc}",
            "\\usepackage[T1]{fontenc}",
            "\\usepackage{lmodern}",
            f"\\usepackage[letterpaper,top={self.ws.margins.top_in:.2f}in,bottom={self.ws.margins.bottom_in:.2f}in,left={self.ws.margins.left_in:.2f}in,right={self.ws.margins.right_in:.2f}in]{{geometry}}",
            "\\usepackage{microtype}",
            "",
            "% --- Mathematics ---",
            "\\usepackage{amsmath,amssymb,amsfonts,mathtools}",
            "\\usepackage{bm}",
            "",
            "% --- Layout & Multi-column ---",
            "\\usepackage{multicol}",
            "\\usepackage{graphicx}",
            "\\usepackage{enumitem}",
            "\\usepackage{xcolor}",
            "\\usepackage[most]{tcolorbox}",
            f"\\definecolor{{PrimaryColor}}{{HTML}}{{{self.theme_color}}}",
            "\\definecolor{RuleColor}{HTML}{D0D7DE}",
            "",
            "% --- Spacing and Column Settings ---",
            f"\\setlength{{\\columnsep}}{{{self.ws.column_gap_in:.2f}in}}",
            "\\setlength{\\columnseprule}{0.2pt}",
            "\\setlength{\\parindent}{0pt}",
            "\\setlength{\\parskip}{2pt}",
            "",
            "% --- Worksheet Response Box ---",
            "\\newtcolorbox{worksheetbox}[1][]{",
            "    colback=white,",
            "    colframe=RuleColor,",
            "    boxrule=0.8pt,",
            "    arc=2pt,",
            "    left=6pt,right=6pt,top=6pt,bottom=6pt,",
            "    #1",
            "}",
            "",
            "\\pagestyle{empty}",
            "",
        ]
        return "\n".join(lines)

    def _render_header(self) -> str:
        """Renders title and student name/date header."""
        title_esc = escape_latex_text(self.ws.title)
        hdr_right = escape_latex_text(self.ws.header_right or "")

        lines = [
            "\\begin{minipage}[t]{0.50\\linewidth}",
            f"  {{\\large\\textbf{{\\color{{PrimaryColor}}{{{title_esc}}}}}}}",
        ]
        if self.ws.subtitle:
            sub_esc = escape_latex_text(self.ws.subtitle)
            lines.append(f"  \\\\[2pt] {{\\small\\textit{{{sub_esc}}}}}")
        lines.extend([
            "\\end{minipage}\\hfill",
            "\\begin{minipage}[t]{0.48\\linewidth}",
            "  \\raggedleft",
            f"  {{\\small {hdr_right}}}",
            "\\end{minipage}",
            "\\vspace{4pt}",
            "\\hrule height 0.5pt",
            "\\vspace{8pt}",
            "",
        ])
        return "\n".join(lines)

    def _render_prompt_text(
        self,
        problem: Problem,
        placed: Optional[PlacedProblem] = None,
        font_size_pt: Optional[float] = None,
    ) -> str:
        """Returns LaTeX-escaped text for problem prompt, preserving math and styling sub-parts."""
        fs = font_size_pt or self.ws.default_font_size_pt
        prefix = ""
        label = problem.full_label
        if label:
            prefix = f"\\textbf{{\\color{{PrimaryColor}}{{{escape_latex_text(label)}}}}} "

        if problem.prompt_runs and not problem.prompt_text:
            parts = []
            if prefix:
                parts.append(prefix)
            for r in problem.prompt_runs:
                if r.is_math:
                    math_txt = r.text.strip()
                    if not (math_txt.startswith("$") and math_txt.endswith("$")):
                        math_txt = f"${math_txt}$"
                    parts.append(math_txt)
                else:
                    t = escape_latex_text(r.text)
                    if r.bold and r.italic:
                        t = f"\\textbf{{\\textit{{{t}}}}}"
                    elif r.bold:
                        t = f"\\textbf{{{t}}}"
                    elif r.italic:
                        t = f"\\textit{{{t}}}"
                    parts.append(t)
            content = "".join(parts)
            if fs and abs(fs - self.ws.default_font_size_pt) >= 0.2:
                leading = fs * 1.25
                return f"{{\\fontsize{{{fs:.1f}pt}}{{{leading:.1f}pt}}\\selectfont {content}}}"
            return content

        raw_text = problem.prompt_text or ""
        if label and raw_text.startswith(label):
            raw_text = raw_text[len(label):].strip()

        segments = parse_prompt_parts(raw_text)
        if not segments:
            segments = [(None, "")]

        sub_parts = [(lbl, txt) for lbl, txt in segments if lbl is not None]
        num_sub_parts = len(sub_parts)

        # Detect available space to include open space between parts
        ws_h = placed.workspace_height_in if placed else 0.0
        spacing_after = getattr(placed, "spacing_after_in", 0.10) if placed else 0.10

        inter_part_space_pt = 3.0
        if num_sub_parts >= 2 and not getattr(placed, "_sub_parts_spaced", False):
            if ws_h >= 0.35 and placed and placed.problem.workspace.type in (WorkspaceType.BLANK, WorkspaceType.LINES):
                # Distribute part of the student workspace between sub-parts
                inter_space_in = min(0.40, max(0.12, (ws_h * 0.65) / num_sub_parts))
                inter_part_space_pt = inter_space_in * 72.0
                distributed_in = (num_sub_parts - 1) * inter_space_in
                placed.workspace_height_in = max(0.15, ws_h - distributed_in)
                placed._sub_parts_spaced = True
                placed._inter_part_space_pt = inter_part_space_pt
            elif spacing_after >= 0.30:
                inter_part_space_pt = min(14.0, max(6.0, spacing_after * 24.0))
                placed._sub_parts_spaced = True
                placed._inter_part_space_pt = inter_part_space_pt
        elif getattr(placed, "_sub_parts_spaced", False):
            inter_part_space_pt = getattr(placed, "_inter_part_space_pt", 3.0)

        lines_out = []
        for idx, (part_lbl, content) in enumerate(segments):
            part_line = ""
            if idx == 0 and prefix:
                part_line += prefix

            if part_lbl:
                part_bold = f"\\textbf{{\\color{{PrimaryColor}}{{{escape_latex_text(part_lbl)}}}}} "
                if idx > 0:
                    part_line += f"\\hspace*{{10pt}}{part_bold}"
                else:
                    part_line += part_bold

            if content:
                part_line += escape_latex_text(content)

            lines_out.append(part_line)

        if len(lines_out) > 1:
            sep = f"\\par\\vspace{{{inter_part_space_pt:.1f}pt}}\n"
            content = sep.join(lines_out)
        else:
            content = lines_out[0] if lines_out else ""

        if fs and abs(fs - self.ws.default_font_size_pt) >= 0.2:
            leading = fs * 1.25
            return f"{{\\fontsize{{{fs:.1f}pt}}{{{leading:.1f}pt}}\\selectfont {content}}}"
        return content

    def _render_choices(self, problem: Problem, font_size_pt: Optional[float] = None) -> str:
        """Renders multiple choice options using enumerate."""
        if not problem.choices:
            return ""
        font_cmd = ""
        if font_size_pt and abs(font_size_pt - self.ws.default_font_size_pt) >= 0.2:
            leading = font_size_pt * 1.25
            font_cmd = f"\\fontsize{{{font_size_pt:.1f}pt}}{{{leading:.1f}pt}}\\selectfont "

        lines = ["\\begin{enumerate}[label=(\\Alph*),itemsep=1pt,topsep=2pt,leftmargin=18pt]"]
        for ch in problem.choices:
            c_text = escape_latex_text(ch.text)
            if font_cmd:
                lines.append(f"  \\item {{{font_cmd}{c_text}}}")
            else:
                lines.append(f"  \\item {c_text}")
        lines.append("\\end{enumerate}")
        return "\n".join(lines)

    def _render_workspace(self, placed: PlacedProblem) -> str:
        """Renders work area lines, box, or blank space."""
        ws_cfg = placed.problem.workspace
        if ws_cfg.type == WorkspaceType.NONE:
            return ""

        h_pt = max(28.0, placed.workspace_height_in * 72.0)

        if ws_cfg.type == WorkspaceType.BOX:
            return f"\\begin{{worksheetbox}}[height={h_pt:.1f}pt]\\end{{worksheetbox}}"
        elif ws_cfg.type == WorkspaceType.GRID:
            return (
                f"\\begin{{worksheetbox}}[height={h_pt:.1f}pt]\n"
                f"  \\centering\\vspace*{{{h_pt / 3.0:.1f}pt}}\\textcolor{{gray!70}}{{\\scriptsize [ Graph / Grid Area ]}}\n"
                f"\\end{{worksheetbox}}"
            )
        elif ws_cfg.type in (WorkspaceType.BLANK, WorkspaceType.LINES):
            # Pure vertical whitespace for student work (no blank underlines)
            return f"\\vspace*{{{placed.workspace_height_in:.2f}in}}"
        else:
            return f"\\vspace*{{{placed.workspace_height_in:.2f}in}}"

    def _render_side_by_side_problem(self, placed: PlacedProblem) -> str:
        """Renders side-by-side text (62%) and image (35%) via minipage."""
        prob = placed.problem
        img = prob.image
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        prompt = self._render_prompt_text(prob, placed=placed, font_size_pt=fs)
        choices = self._render_choices(prob, font_size_pt=fs)
        workspace = self._render_workspace(placed)

        img_include = ""
        if img and img.media_path:
            img_path = img.media_path.replace("\\", "/")
            img_include = f"\\includegraphics[width=\\linewidth]{{{img_path}}}"
            if img.caption:
                img_include += f"\\\\[2pt]{{\\scriptsize\\textit{{{escape_latex_text(img.caption)}}}}}"

        tot_w = max(0.1, placed.width_in)
        img_ratio = min(0.50, max(0.25, placed.image_render_width_in / tot_w))
        text_ratio = round(0.96 - img_ratio, 2)
        img_ratio = round(img_ratio, 2)

        lines = [
            "\\noindent",
            f"\\begin{{minipage}}[t]{{{text_ratio:.2f}\\linewidth}}",
            f"  {prompt}",
        ]
        if choices:
            lines.append(f"  {choices}")
        lines.extend([
            "\\end{minipage}\\hfill",
            f"\\begin{{minipage}}[t]{{{img_ratio:.2f}\\linewidth}}",
            "  \\vspace{0pt}",
            "  \\centering",
            f"  {img_include}",
            "\\end{minipage}",
        ])
        if workspace:
            lines.append(f"\\par\\vspace{{2pt}}\n{workspace}")
        space_in = getattr(placed, "spacing_after_in", 0.10)
        lines.append(f"\\vspace{{{space_in:.2f}in}}")
        return "\n".join(lines)

    def _render_stacked_problem(self, placed: PlacedProblem) -> str:
        """Renders stacked problem: text, centered image, workspace."""
        prob = placed.problem
        img = prob.image
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        prompt = self._render_prompt_text(prob, placed=placed, font_size_pt=fs)
        choices = self._render_choices(prob, font_size_pt=fs)
        workspace = self._render_workspace(placed)

        lines = [
            "\\noindent",
            prompt,
        ]
        if choices:
            lines.append(choices)

        if img and img.media_path:
            img_path = img.media_path.replace("\\", "/")
            lines.extend([
                "\\begin{center}",
                f"  \\includegraphics[width={placed.image_render_width_in / placed.width_in:.2f}\\linewidth]{{{img_path}}}",
            ])
            if img.caption:
                lines.append(f"  \\\\[2pt]{{\\scriptsize\\textit{{{escape_latex_text(img.caption)}}}}}")
            lines.append("\\end{center}")

        if workspace:
            lines.append(workspace)

        space_in = getattr(placed, "spacing_after_in", 0.10)
        lines.append(f"\\vspace{{{space_in:.2f}in}}")
        return "\n".join(lines)

    def _render_text_only_problem(self, placed: PlacedProblem) -> str:
        """Renders text-only problem."""
        prob = placed.problem
        fs = placed.font_size_pt or self.ws.default_font_size_pt
        prompt = self._render_prompt_text(prob, placed=placed, font_size_pt=fs)
        choices = self._render_choices(prob, font_size_pt=fs)
        workspace = self._render_workspace(placed)

        lines = [
            "\\noindent",
            prompt,
        ]
        if choices:
            lines.append(choices)
        if workspace:
            lines.append(workspace)
        space_in = getattr(placed, "spacing_after_in", 0.10)
        lines.append(f"\\vspace{{{space_in:.2f}in}}")
        return "\n".join(lines)

    def _render_section_header(self, header: PlacedSectionHeader) -> str:
        """Renders section title."""
        lines = []
        if header.title:
            t = escape_latex_text(header.title)
            lines.append(f"\\vspace{{6pt}}\\textbf{{\\color{{PrimaryColor}}{{{t}}}}}\\\\[2pt]")
        if header.instructions:
            inst = escape_latex_text(header.instructions)
            lines.append(f"{{\\small\\textit{{{inst}}}}}\\\\[4pt]")
        return "\n".join(lines)

    def generate_latex(self) -> str:
        """Produces complete LaTeX document string."""
        preamble = self._render_preamble()
        header = self._render_header()

        body_parts = ["\\begin{document}", header]

        use_multicols = self.ws.default_columns > 1

        for page_idx, page in enumerate(self.plan.pages):
            if page_idx > 0:
                body_parts.append("\\newpage")

            if use_multicols:
                body_parts.append(f"\\begin{{multicols*}}{{{self.ws.default_columns}}}")

            current_col = 0
            for item in page.items:
                if isinstance(item, PlacedSectionHeader):
                    body_parts.append(self._render_section_header(item))
                elif isinstance(item, PlacedProblem):
                    if use_multicols and item.col_index > current_col:
                        body_parts.append("\\columnbreak\n")
                        current_col = item.col_index

                    if item.layout == LayoutDecision.SIDE_BY_SIDE:
                        body_parts.append(self._render_side_by_side_problem(item))
                    elif item.layout == LayoutDecision.STACKED:
                        body_parts.append(self._render_stacked_problem(item))
                    else:
                        body_parts.append(self._render_text_only_problem(item))

            if use_multicols:
                body_parts.append("\\end{multicols*}")

        body_parts.append("\\end{document}")

        return preamble + "\n" + "\n".join(body_parts) + "\n"

    def render(self, output_tex_path: str | Path, compile_pdf: bool = False) -> Path:
        """Writes .tex file to disk and optionally invokes LaTeX engine to build PDF."""
        out_p = Path(output_tex_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        tex_code = self.generate_latex()
        out_p.write_text(tex_code, encoding="utf-8")

        if compile_pdf:
            compile_tex_to_pdf(out_p)

        return out_p


```

### src\worksheet_packer\docx_extractor.py

```python
"""DOCX Extraction and Headless Rendering Utilities.

Enables existing Word (.docx) documents to be ingested into the Worksheet Packer pipeline:
1. Extracts embedded media assets directly from word/media/ within the DOCX zip archive.
2. Renders DOCX pages to high-resolution PNG images via LibreOffice or Windows Word COM
   so they can be analyzed by Gemini multimodal vision.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
import pymupdf as fitz


def extract_docx_media(docx_path: str | Path, output_dir: str | Path) -> Dict[str, Path]:
    """Extracts all embedded images from the word/media/ folder of a .docx file.

    Returns:
        Dictionary mapping internal media filename (e.g. 'image1.png') to extracted Path.
    """
    docx_file = Path(docx_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted_map = {}
    if not zipfile.is_zipfile(docx_file):
        return extracted_map

    with zipfile.ZipFile(docx_file, "r") as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                filename = Path(name).name
                target_path = out_dir / filename
                with z.open(name) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted_map[filename] = target_path

    return extracted_map


def convert_docx_to_pdf(docx_path: str | Path, output_pdf_path: Optional[str | Path] = None) -> Path:
    """Converts a DOCX document to PDF using headless LibreOffice or Windows Word COM.

    Raises:
        RuntimeError: If neither LibreOffice nor Word COM is available or conversion fails.
    """
    docx_file = Path(docx_path).resolve()
    if not docx_file.exists():
        raise FileNotFoundError(f"DOCX file not found: {docx_file}")

    if output_pdf_path is None:
        out_pdf = docx_file.with_suffix(".pdf")
    else:
        out_pdf = Path(output_pdf_path).resolve()

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = out_pdf.parent / f".temp_pdf_{docx_file.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Try LibreOffice CLI
    soffice_cmd = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice_cmd:
        candidates = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        ]
        for c in candidates:
            if c.exists():
                soffice_cmd = str(c)
                break

    if soffice_cmd:
        try:
            subprocess.run(
                [soffice_cmd, "--headless", "--convert-to", "pdf", str(docx_file), "--outdir", str(temp_dir)],
                check=True,
                capture_output=True,
                timeout=60,
            )
            candidate_pdf = temp_dir / f"{docx_file.stem}.pdf"
            if candidate_pdf.exists():
                shutil.move(str(candidate_pdf), str(out_pdf))
                shutil.rmtree(temp_dir, ignore_errors=True)
                return out_pdf
        except Exception:
            pass

    # 2. Try Windows MS Word COM
    if os.name == "nt":
        import time
        for attempt in range(3):
            try:
                import win32com.client  # type: ignore
                # Use DispatchEx for an isolated instance
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0  # wdAlertsNone
                try:
                    # Open read-only and unconfirmed
                    doc = word.Documents.Open(str(docx_file), ReadOnly=True, ConfirmConversions=False)
                    # 17 = wdFormatPDF
                    doc.SaveAs(str(out_pdf), FileFormat=17)
                    doc.Close(SaveChanges=False)
                    if out_pdf.exists() and out_pdf.stat().st_size > 0:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        return out_pdf
                finally:
                    word.Quit()
            except Exception as e:
                time.sleep(1.0)
                if attempt == 2:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    raise RuntimeError(f"Word COM conversion failed: {e}")

    shutil.rmtree(temp_dir, ignore_errors=True)
    raise RuntimeError(
        "Could not convert DOCX to PDF: neither LibreOffice CLI nor Windows MS Word COM automation succeeded."
    )


def render_docx_pages(
    docx_path: str | Path,
    output_dir: str | Path,
    dpi: int = 200,
) -> List[Path]:
    """Renders all pages of a Word document into high-resolution PNG images.

    Converts DOCX -> PDF, then renders each page using PyMuPDF.

    Returns:
        List of PNG paths for each page (1-indexed).
    """
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    temp_pdf = out_dir / f"{Path(docx_path).stem}_rendered.pdf"
    convert_docx_to_pdf(docx_path, temp_pdf)

    rendered_pages = []
    doc = fitz.open(str(temp_pdf))
    try:
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            page_png = out_dir / f"page_{page_idx + 1}.png"
            pix.save(str(page_png))
            rendered_pages.append(page_png)
    finally:
        doc.close()

    return rendered_pages


```

### src\worksheet_packer\cli.py

```python
"""Command Line Interface for Worksheet Packer.

Provides commands to inspect, parse, pack, and render space-efficient worksheets
into beautifully formatted Word (.docx) and LaTeX (.tex / .pdf) documents.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.table import Table

from .worksheet_ast import (
    RenderPlan,
    SectionOrdering,
    WorksheetSpec,
)
from .layout_engine import LayoutEngine
from .docx_renderer import DocxWorksheetRenderer
from .latex_renderer import LatexWorksheetRenderer
from .worksheet_parser import WorksheetParser
from .docx_extractor import convert_docx_to_pdf, extract_docx_media, render_docx_pages

app = typer.Typer(
    name="worksheet-packer",
    help="Space-efficient PDF worksheet parser, 2D bin-packer, and DOCX/LaTeX renderer.",
    add_completion=False,
)
console = Console()


@app.command()
def info(
    file_path: Path = typer.Argument(..., help="Path to PDF, Word DOCX, WorksheetSpec JSON, or RenderPlan JSON")
):
    """Inspects a PDF or Word document, or an existing AST/Plan JSON file."""
    if not file_path.exists():
        console.print(f"[red]Error:[/red] File not found: {file_path}")
        raise typer.Exit(1)

    if file_path.suffix.lower() == ".docx":
        from docx import Document
        doc = Document(str(file_path))
        media = extract_docx_media(file_path, file_path.parent / ".temp_inspect_media")
        console.print(f"[bold cyan]Word Document (.docx):[/bold cyan] {file_path.name}")
        console.print(f"Paragraphs: {len(doc.paragraphs)}")
        console.print(f"Tables: {len(doc.tables)}")
        console.print(f"Embedded Media Assets: {len(media)}")
        shutil = __import__("shutil")
        shutil.rmtree(file_path.parent / ".temp_inspect_media", ignore_errors=True)
    elif file_path.suffix.lower() == ".pdf":
        from pdf_to_docx.pdf_extractor import PDFExtractor
        with PDFExtractor(file_path) as ext:
            doc_info = ext.get_document_info()
            console.print(f"[bold cyan]PDF Document:[/bold cyan] {doc_info['title']}")
            console.print(f"Total Pages: {doc_info['page_count']}")
            table = Table(title="Pages Summary")
            table.add_column("Page", justify="right")
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
    elif file_path.suffix.lower() == ".json":
        data = json.loads(file_path.read_text(encoding="utf-8"))
        if "pages" in data and "stats" in data:
            console.print(f"[bold green]RenderPlan JSON[/bold green]: {file_path.name}")
            console.print(f"Total Pages: {data.get('total_pages')}")
            stats = data.get("stats", {})
            console.print(f"Problems: {stats.get('total_problems')}")
            console.print(f"Side-by-side layouts: {stats.get('side_by_side_count')}")
            console.print(f"Stacked layouts: {stats.get('stacked_count')}")
            console.print(f"Text-only layouts: {stats.get('text_only_count')}")
        elif "sections" in data:
            console.print(f"[bold green]WorksheetSpec JSON[/bold green]: {data.get('title')}")
            console.print(f"Default Columns: {data.get('default_columns')}")
            total_probs = sum(len(s.get("problems", [])) for s in data.get("sections", []))
            console.print(f"Sections: {len(data.get('sections', []))}")
            console.print(f"Total Problems: {total_probs}")


@app.command()
def parse(
    doc_path: Path = typer.Argument(..., help="Path to input worksheet (PDF or Word .docx)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to output WorksheetSpec JSON"),
    workspace_dir: Optional[Path] = typer.Option(None, "--workspace-dir", "-w", help="Cache directory for media assets"),
    ordering: str = typer.Option("strict", "--ordering", help="Section ordering: 'strict' or 'flexible'"),
    columns: int = typer.Option(2, "--columns", "-c", help="Default column count: 1 or 2"),
):
    """Parses a worksheet PDF or Word doc (.docx) into a WorksheetSpec AST JSON with harvested diagrams."""
    sec_ordering = SectionOrdering.FLEXIBLE if ordering.lower() == "flexible" else SectionOrdering.STRICT
    out_json = output or doc_path.with_name(f"{doc_path.stem}_spec.json")

    console.print(f"[cyan]Parsing worksheet document:[/cyan] {doc_path}")
    with WorksheetParser(doc_path) as parser:
        spec = parser.parse_worksheet(
            workspace_dir=workspace_dir,
            ordering=sec_ordering,
            default_columns=columns,
        )

    out_json.write_text(spec.model_dump_json(indent=2), encoding="utf-8")
    total_probs = sum(len(s.problems) for s in spec.sections)
    console.print(f"[bold green]Extracted {total_probs} problems into:[/bold green] {out_json}")


@app.command()
def pack(
    spec_path: Path = typer.Argument(..., help="Path to WorksheetSpec JSON"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Path to output RenderPlan JSON"),
    columns: Optional[int] = typer.Option(None, "--columns", "-c", help="Override default columns (1 or 2)"),
    ordering: Optional[str] = typer.Option(None, "--ordering", help="Override ordering: 'strict' or 'flexible'"),
):
    """Executes 2D layout packing on a WorksheetSpec AST to generate a RenderPlan."""
    spec_data = json.loads(spec_path.read_text(encoding="utf-8"))
    spec = WorksheetSpec.model_validate(spec_data)

    if columns is not None:
        spec.default_columns = columns
    if ordering:
        sec_ord = SectionOrdering.FLEXIBLE if ordering.lower() == "flexible" else SectionOrdering.STRICT
        for s in spec.sections:
            s.ordering = sec_ord

    engine = LayoutEngine(spec)
    plan = engine.pack()

    out_plan = output or spec_path.with_name(f"{spec_path.stem}_plan.json")
    out_plan.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    stats = plan.stats
    console.print(f"[bold green]Layout Plan Generated:[/bold green] {out_plan}")
    console.print(f"Total Pages: {plan.total_pages}")
    console.print(f"Side-by-side: {stats.get('side_by_side_count')} | Stacked: {stats.get('stacked_count')} | Text-only: {stats.get('text_only_count')}")


@app.command()
def render(
    plan_or_spec: Path = typer.Argument(..., help="Path to RenderPlan JSON or WorksheetSpec JSON"),
    output: Path = typer.Option(..., "--output", "-o", help="Output file path (.docx or .tex)"),
    fmt: str = typer.Option("docx", "--format", "-f", help="Output format: 'docx', 'latex', or 'pdf'"),
):
    """Renders a RenderPlan or WorksheetSpec to DOCX, LaTeX, or PDF."""
    data = json.loads(plan_or_spec.read_text(encoding="utf-8"))

    if "pages" in data and "stats" in data:
        plan = RenderPlan.model_validate(data)
    else:
        spec = WorksheetSpec.model_validate(data)
        plan = LayoutEngine(spec).pack()

    fmt_clean = fmt.lower()
    if fmt_clean == "docx" or output.suffix.lower() == ".docx":
        renderer = DocxWorksheetRenderer(plan)
        saved = renderer.render(output)
        console.print(f"[bold green]Successfully compiled DOCX:[/bold green] {saved}")
    elif fmt_clean in ("latex", "tex", "pdf") or output.suffix.lower() in (".tex", ".pdf"):
        renderer = LatexWorksheetRenderer(plan)
        compile_pdf = (fmt_clean == "pdf" or output.suffix.lower() == ".pdf")
        tex_path = output if output.suffix.lower() == ".tex" else output.with_suffix(".tex")
        saved = renderer.render(tex_path, compile_pdf=compile_pdf)
        console.print(f"[bold green]Successfully generated LaTeX:[/bold green] {saved}")


@app.command("render-docx-pages")
def render_docx_pages_cmd(
    docx_path: Path = typer.Argument(..., help="Path to input Word document (.docx)"),
    output_dir: Path = typer.Option(..., "--output-dir", "-o", help="Output directory for rendered page PNGs"),
    dpi: int = typer.Option(200, "--dpi", help="Rendering DPI (default 200 for vision analysis)"),
):
    """Renders all pages of a Word document (.docx) to PNG images via LibreOffice or Word COM."""
    console.print(f"[cyan]Rendering Word document pages to PNGs:[/cyan] {docx_path}")
    pages = render_docx_pages(docx_path, output_dir, dpi=dpi)
    console.print(f"[bold green]Rendered {len(pages)} pages into:[/bold green] {output_dir}")


@app.command()
def convert(
    doc_path: Path = typer.Argument(..., help="Path to input worksheet (PDF or Word .docx)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Destination path (.docx or .tex)"),
    fmt: str = typer.Option("docx", "--format", "-f", help="Format: 'docx', 'latex', or 'both'"),
    columns: int = typer.Option(2, "--columns", "-c", help="Number of columns (1 or 2)"),
    ordering: str = typer.Option("strict", "--ordering", help="Ordering: 'strict' or 'flexible'"),
    save_ast: bool = typer.Option(True, "--save-ast/--no-save-ast", help="Save intermediate spec and plan JSON"),
):
    """Autonomous end-to-end pipeline: PDF / DOCX -> Parsing -> 2D Packing -> DOCX / LaTeX."""
    sec_ordering = SectionOrdering.FLEXIBLE if ordering.lower() == "flexible" else SectionOrdering.STRICT

    console.print(f"[bold cyan]Starting end-to-end worksheet conversion:[/bold cyan] {doc_path}")
    with WorksheetParser(doc_path) as parser:
        spec = parser.parse_worksheet(ordering=sec_ordering, default_columns=columns)

    if save_ast:
        spec_file = doc_path.with_name(f"{doc_path.stem}_spec.json")
        spec_file.write_text(spec.model_dump_json(indent=2), encoding="utf-8")

    engine = LayoutEngine(spec)
    plan = engine.pack()

    if save_ast:
        plan_file = doc_path.with_name(f"{doc_path.stem}_plan.json")
        plan_file.write_text(plan.model_dump_json(indent=2), encoding="utf-8")

    fmt_lower = fmt.lower()
    if fmt_lower in ("docx", "both"):
        default_out = doc_path.with_name(f"{doc_path.stem}_packed.docx") if doc_path.suffix.lower() == ".docx" else doc_path.with_suffix(".docx")
        docx_out = output if (output and output.suffix.lower() == ".docx") else default_out
        DocxWorksheetRenderer(plan).render(docx_out)
        console.print(f"[bold green]Rendered Word Document:[/bold green] {docx_out}")

    if fmt_lower in ("latex", "tex", "both", "pdf"):
        tex_out = output if (output and output.suffix.lower() == ".tex") else doc_path.with_suffix(".tex")
        LatexWorksheetRenderer(plan).render(tex_out, compile_pdf=(fmt_lower == "pdf"))
        console.print(f"[bold green]Rendered LaTeX Document:[/bold green] {tex_out}")


def main():
    app()


if __name__ == "__main__":
    main()


```

### tests\test_worksheet_packer.py

```python
"""Comprehensive Unit & Integration Tests for Worksheet Packer.

Verifies:
1. AST schema serialization, validation, and ordering constraints.
2. Image auto-cropping, white border trimming, and aspect ratio calculation.
3. Layout engine: side-by-side vs stacked decision heuristics and 2D bin packing.
4. Strict vs flexible section ordering behavior.
5. Deterministic DOCX rendering with invisible tables and w:cantSplit.
6. Deterministic LaTeX rendering with minipage side-by-side and multicols.
"""

from __future__ import annotations
import json
import os
from pathlib import Path
import tempfile
import unittest
from docx import Document
from PIL import Image, ImageDraw

from worksheet_packer.worksheet_ast import (
    LayoutDecision,
    LayoutHint,
    PageMargins,
    PlacedProblem,
    Problem,
    ProblemImage,
    QuestionChoice,
    RenderPlan,
    SectionOrdering,
    TextRun,
    WorkspaceConfig,
    WorkspaceType,
    WorksheetSection,
    WorksheetSpec,
)
from worksheet_packer.image_utils import (
    auto_crop_image,
    inspect_diagram_dimensions,
    estimate_image_scale_bounds,
    audit_image_boundaries,
    ImageBoundaryAuditor,
)
from worksheet_packer.layout_engine import LayoutEngine
from worksheet_packer.docx_renderer import DocxWorksheetRenderer
from worksheet_packer.latex_renderer import LatexWorksheetRenderer
from worksheet_packer.docx_extractor import extract_docx_media, render_docx_pages


class TestWorksheetPacker(unittest.TestCase):

    def setUp(self):
        self.temp_dir_obj = tempfile.TemporaryDirectory()
        self.temp_dir = Path(self.temp_dir_obj.name)

        # Create a sample diagram image with artificial 60px white borders
        self.sample_diagram = self.temp_dir / "triangle_with_margins.png"
        img = Image.new("RGBA", (400, 300), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Content box: (100, 60) to (300, 240) -> 200x180, AR ~ 0.90
        draw.polygon([(100, 240), (300, 240), (100, 60)], fill=(31, 78, 121, 255), outline=(0, 0, 0, 255))
        draw.text((180, 210), "θ", fill=(255, 255, 255, 255))
        img.save(str(self.sample_diagram))

    def tearDown(self):
        self.temp_dir_obj.cleanup()

    def test_auto_crop_image(self):
        """Verifies that auto_crop_image trims white margins and recalculates true dimensions and AR."""
        cropped_path, w_px, h_px, ar = auto_crop_image(
            self.sample_diagram,
            output_path=self.temp_dir / "triangle_clean.png",
            tolerance=15,
            padding_px=4,
        )

        self.assertTrue(cropped_path.exists())
        self.assertTrue(190 <= w_px <= 220)
        self.assertTrue(170 <= h_px <= 200)
        self.assertTrue(0.80 <= ar <= 1.05)

        orig_w, orig_h, orig_ar = inspect_diagram_dimensions(self.sample_diagram)
        self.assertEqual(orig_w, 400)
        self.assertEqual(orig_h, 300)

    def test_audit_image_boundaries(self):
        """Verifies edge perimeter cutoff detection and boundary auditing."""
        # 1. Clean image with white borders should pass
        clean_res = audit_image_boundaries(self.sample_diagram)
        self.assertEqual(clean_res["status"], "PASS")
        self.assertEqual(clean_res["cutoffs"], [])
        self.assertEqual(clean_res["densities"]["top"], 0.0)
        self.assertEqual(clean_res["densities"]["bottom"], 0.0)
        self.assertEqual(clean_res["densities"]["left"], 0.0)
        self.assertEqual(clean_res["densities"]["right"], 0.0)

        # 2. Image with content extending to borders should flag cutoffs
        cutoff_path = self.temp_dir / "severed_diagram.png"
        img = Image.new("RGBA", (200, 200), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        # Draw dark lines directly across left edge (x=0) and bottom edge (y=199)
        draw.line([(0, 0), (0, 199)], fill=(0, 0, 0, 255), width=2)
        draw.line([(0, 199), (199, 199)], fill=(0, 0, 0, 255), width=2)
        img.save(str(cutoff_path))

        cutoff_res = audit_image_boundaries(cutoff_path)
        self.assertEqual(cutoff_res["status"], "FAIL")
        cutoff_edges = [edge for edge, _ in cutoff_res["cutoffs"]]
        self.assertIn("LEFT", cutoff_edges)
        self.assertIn("BOTTOM", cutoff_edges)
        self.assertNotIn("TOP", cutoff_edges)
        self.assertNotIn("RIGHT", cutoff_edges)

        # 3. Transparent background is treated as clean margin
        transparent_path = self.temp_dir / "transparent_diagram.png"
        trans_img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        trans_draw = ImageDraw.Draw(trans_img)
        # Content centered at (30, 30) to (70, 70)
        trans_draw.rectangle([(30, 30), (70, 70)], fill=(0, 0, 0, 255))
        trans_img.save(str(transparent_path))

        trans_res = audit_image_boundaries(transparent_path)
        self.assertEqual(trans_res["status"], "PASS")
        self.assertEqual(trans_res["cutoffs"], [])

        # 4. ImageBoundaryAuditor class wrapper produces identical results
        auditor = ImageBoundaryAuditor()
        class_res = auditor.audit_image_file(cutoff_path)
        self.assertEqual(class_res["status"], "FAIL")
        self.assertEqual(class_res["cutoffs"], cutoff_res["cutoffs"])

        # 5. Non-existent file raises FileNotFoundError
        with self.assertRaises(FileNotFoundError):
            audit_image_boundaries(self.temp_dir / "non_existent.png")

    def test_ast_schema_and_serialization(self):
        """Verifies WorksheetSpec AST creation, validation, and JSON round-trip."""
        spec = WorksheetSpec(
            title="AP Calculus Worksheet 3.1",
            subtitle="Related Rates & Geometric Optimization",
            default_columns=2,
            sections=[
                WorksheetSection(
                    id="sec_1",
                    title="Part A: Geometric Applications",
                    ordering=SectionOrdering.STRICT,
                    problems=[
                        Problem(
                            id="q1",
                            number=1,
                            prompt_text="A ladder 10 ft long rests against a vertical wall.",
                            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=4),
                        ),
                        Problem(
                            id="q2",
                            number=2,
                            part="a",
                            prompt_text="Find the rate at which the angle θ between ladder and ground changes.",
                            choices=[
                                QuestionChoice(label="(A)", text="-0.25 rad/s"),
                                QuestionChoice(label="(B)", text="-0.50 rad/s"),
                                QuestionChoice(label="(C)", text="-1.20 rad/s"),
                            ],
                            workspace=WorkspaceConfig(type=WorkspaceType.NONE),
                        ),
                    ],
                )
            ],
        )

        json_str = spec.model_dump_json(indent=2)
        reloaded = WorksheetSpec.model_validate_json(json_str)

        self.assertEqual(reloaded.title, "AP Calculus Worksheet 3.1")
        self.assertEqual(len(reloaded.sections), 1)
        self.assertEqual(len(reloaded.sections[0].problems), 2)
        self.assertEqual(reloaded.sections[0].problems[1].full_label, "2.(a)")
        self.assertEqual(len(reloaded.sections[0].problems[1].choices), 3)

    def test_layout_engine_decisions(self):
        """Verifies that the packing engine correctly assigns SIDE_BY_SIDE vs STACKED layouts."""
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)

        prob_square = Problem(
            id="q_square",
            number=1,
            prompt_text="In the right triangle below, find the angle θ.",
            image=ProblemImage(
                media_path=str(cropped_path),
                native_width_px=w,
                native_height_px=h,
                aspect_ratio=ar,  # ~0.90 -> Square-ish
            ),
            min_rendered_width_in=1.2,
            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3),
        )

        prob_wide = Problem(
            id="q_wide",
            number=2,
            prompt_text="Inspect the wide coordinate plane diagram below.",
            image=ProblemImage(
                media_path=str(cropped_path),
                native_width_px=800,
                native_height_px=200,
                aspect_ratio=0.25,  # Very wide -> Stacked
            ),
            workspace=WorkspaceConfig(type=WorkspaceType.BOX, height_pt=50),
        )

        prob_text_only = Problem(
            id="q_text",
            number=3,
            prompt_text="State the Fundamental Theorem of Calculus.",
            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=5),
        )

        ws = WorksheetSpec(
            title="Test Layout Decisions",
            default_columns=1,
            sections=[
                WorksheetSection(
                    id="sec_main",
                    problems=[prob_square, prob_wide, prob_text_only],
                )
            ],
        )

        engine = LayoutEngine(ws)
        col_w = ws.printable_width_in

        dec1, total_h1, text_w1, text_h1, img_w1, img_h1, ws_h1 = engine.calculate_problem_footprint(prob_square, col_w)
        self.assertEqual(dec1, LayoutDecision.SIDE_BY_SIDE)
        self.assertGreater(img_w1, 0)
        self.assertGreater(text_w1, 0)

        dec2, total_h2, text_w2, text_h2, img_w2, img_h2, ws_h2 = engine.calculate_problem_footprint(prob_wide, col_w)
        self.assertEqual(dec2, LayoutDecision.STACKED)

        dec3, total_h3, text_w3, text_h3, img_w3, img_h3, ws_h3 = engine.calculate_problem_footprint(prob_text_only, col_w)
        self.assertEqual(dec3, LayoutDecision.TEXT_ONLY)
        self.assertEqual(img_w3, 0.0)

    def test_flexible_vs_strict_ordering(self):
        """Verifies that flexible ordering sorts problems by footprint height for tighter packing."""
        probs = [
            Problem(id="short_1", number=1, prompt_text="Short Q1", workspace=WorkspaceConfig(lines=1)),
            Problem(id="tall_1", number=2, prompt_text="Tall Q2 with lots of lines", workspace=WorkspaceConfig(lines=10)),
            Problem(id="short_2", number=3, prompt_text="Short Q3", workspace=WorkspaceConfig(lines=1)),
            Problem(id="tall_2", number=4, prompt_text="Tall Q4 with lots of lines", workspace=WorkspaceConfig(lines=12)),
        ]

        ws_strict = WorksheetSpec(
            title="Strict Ordering",
            sections=[WorksheetSection(id="s1", ordering=SectionOrdering.STRICT, problems=list(probs))],
        )
        plan_strict = LayoutEngine(ws_strict).pack()
        strict_order = [item.problem.id for item in plan_strict.pages[0].items if isinstance(item, PlacedProblem)]
        self.assertEqual(strict_order, ["short_1", "tall_1", "short_2", "tall_2"])

        ws_flex = WorksheetSpec(
            title="Flexible Ordering",
            sections=[WorksheetSection(id="s1", ordering=SectionOrdering.FLEXIBLE, problems=list(probs))],
        )
        plan_flex = LayoutEngine(ws_flex).pack()
        flex_order = [item.problem.id for item in plan_flex.pages[0].items if isinstance(item, PlacedProblem)]
        self.assertIn(flex_order[0], ("tall_2", "tall_1"))

    def test_docx_rendering_with_invisible_tables(self):
        """Verifies that DocxWorksheetRenderer compiles into a valid .docx with atomic invisible tables."""
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)

        spec = WorksheetSpec(
            title="Geometry & Trig Quiz",
            subtitle="Period 4",
            header_right="Name: ________________ Date: ______",
            default_columns=2,
            sections=[
                WorksheetSection(
                    id="sec_1",
                    title="Section I: Triangle Trigonometry",
                    instructions="Answer all questions. Show complete work.",
                    ordering=SectionOrdering.STRICT,
                    problems=[
                        Problem(
                            id="q1",
                            number=1,
                            prompt_text="Find angle θ in the right triangle shown below.",
                            image=ProblemImage(
                                media_path=str(cropped_path),
                                native_width_px=w,
                                native_height_px=h,
                                aspect_ratio=ar,
                            ),
                            min_rendered_width_in=1.0,
                            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3),
                        ),
                        Problem(
                            id="q2",
                            number=2,
                            prompt_text="Which of the following is equal to sin(60°)?",
                            choices=[
                                QuestionChoice(label="(A)", text="1/2"),
                                QuestionChoice(label="(B)", text="√2 / 2"),
                                QuestionChoice(label="(C)", text="√3 / 2"),
                                QuestionChoice(label="(D)", text="1"),
                            ],
                            workspace=WorkspaceConfig(type=WorkspaceType.NONE),
                        ),
                        Problem(
                            id="q3",
                            number=3,
                            prompt_text="Plot the function f(x) = sin(x) on [-π, π].",
                            workspace=WorkspaceConfig(type=WorkspaceType.GRID, height_pt=80),
                        ),
                    ],
                )
            ],
        )

        plan = LayoutEngine(spec).pack()
        self.assertGreaterEqual(plan.total_pages, 1)

        docx_out = self.temp_dir / "test_worksheet.docx"
        renderer = DocxWorksheetRenderer(plan)
        saved_path = renderer.render(docx_out)

        self.assertTrue(saved_path.exists())
        self.assertGreater(saved_path.stat().st_size, 5000)

        from docx import Document
        doc = Document(str(saved_path))
        self.assertGreaterEqual(len(doc.tables), 4)

        for tbl in doc.tables[1:]:
            for row in tbl.rows:
                trPr = row._tr.get_or_add_trPr()
                cant_split = trPr.find("{http://schemas.openxmlformats.org/wordprocessingml/2006/main}cantSplit")
                self.assertIsNotNone(cant_split, "Every problem table row must enforce w:cantSplit!")

    def test_latex_rendering_with_minipage(self):
        """Verifies that LatexWorksheetRenderer generates valid LaTeX with minipage and multicols."""
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)

        spec = WorksheetSpec(
            title="Geometry & Trig Quiz",
            header_right="Name: \\underline{\\hspace{2in}}",
            default_columns=2,
            sections=[
                WorksheetSection(
                    id="sec_1",
                    title="Part A: Trigonometry",
                    problems=[
                        Problem(
                            id="q1",
                            number=1,
                            prompt_text="Find angle $\\theta$ if $\\sin(\\theta) = \\frac{1}{2}$.",
                            image=ProblemImage(
                                media_path=str(cropped_path),
                                native_width_px=w,
                                native_height_px=h,
                                aspect_ratio=ar,
                            ),
                            min_rendered_width_in=1.0,
                            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=2),
                        ),
                        Problem(
                            id="q2",
                            number=2,
                            prompt_text="Which choice represents $\\cos(0)$?",
                            choices=[
                                QuestionChoice(label="(A)", text="0"),
                                QuestionChoice(label="(B)", text="1"),
                            ],
                            workspace=WorkspaceConfig(type=WorkspaceType.NONE),
                        ),
                    ],
                )
            ],
        )

        plan = LayoutEngine(spec).pack()
        tex_out = self.temp_dir / "test_worksheet.tex"
        renderer = LatexWorksheetRenderer(plan)
        saved_tex = renderer.render(tex_out, compile_pdf=False)

        self.assertTrue(saved_tex.exists())
        tex_content = saved_tex.read_text(encoding="utf-8")

        self.assertIn("\\documentclass", tex_content)
        self.assertIn("\\usepackage{multicol}", tex_content)
        self.assertIn("{tcolorbox}", tex_content)
        self.assertIn("\\begin{multicols*}{2}", tex_content)
        self.assertIn("minipage", tex_content)
        self.assertTrue("\\sin(\\theta) = \\frac{1}{2}" in tex_content or "sin(\\theta)" in tex_content)

    def test_docx_media_extraction_and_rendering(self):
        """Verifies extracting embedded images from DOCX and rendering DOCX pages to PNGs."""
        # Compile a sample docx first
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)
        spec = WorksheetSpec(
            title="DOCX Extraction Test",
            sections=[
                WorksheetSection(
                    id="s1",
                    problems=[
                        Problem(
                            id="p1",
                            number=1,
                            prompt_text="Inspect triangle.",
                            image=ProblemImage(
                                media_path=str(cropped_path),
                                native_width_px=w,
                                native_height_px=h,
                                aspect_ratio=ar,
                            ),
                        )
                    ],
                )
            ],
        )
        plan = LayoutEngine(spec).pack()
        docx_file = self.temp_dir / "extracted_test.docx"
        DocxWorksheetRenderer(plan).render(docx_file)

        # 1. Test zip-based media extraction
        media_out = self.temp_dir / "media_extracted"
        extracted = extract_docx_media(docx_file, media_out)
        self.assertGreaterEqual(len(extracted), 1)
        for name, p in extracted.items():
            self.assertTrue(p.exists())
            self.assertGreater(p.stat().st_size, 0)

        # 2. Test headless page rendering (if Word COM or LibreOffice available)
        try:
            rendered_dir = self.temp_dir / "pages_rendered"
            pages = render_docx_pages(docx_file, rendered_dir, dpi=150)
            self.assertGreaterEqual(len(pages), 1)
            self.assertTrue(pages[0].exists())
        except RuntimeError as e:
            # If neither Word nor LibreOffice is present in the test environment, skip gracefully
            pass

    def test_dynamic_scale_bounds_estimation(self):
        """Verifies that estimate_image_scale_bounds correctly bounds formula icons and geometry diagrams."""
        # 1. Formula Icon (e.g. sqrt[5]{x^7}) - small native dimensions, source width ~0.44 in
        formula_bounds = estimate_image_scale_bounds(
            image_path=self.sample_diagram,
            native_width_px=119,
            native_height_px=83,
            aspect_ratio=0.70,
            bbox=[500, 100, 530, 152],  # width ratio 52/1000 -> 0.44 in
            page_width_in=8.5,
            col_width_in=3.5,
        )
        self.assertEqual(formula_bounds.category, "formula_icon")
        self.assertLessEqual(formula_bounds.max_width_in, 1.40)
        self.assertGreaterEqual(formula_bounds.min_width_in, 0.35)

        # 2. Detailed Geometric Diagram (fine angle text, source width ~2.2 in)
        geom_bounds = estimate_image_scale_bounds(
            image_path=self.sample_diagram,
            native_width_px=450,
            native_height_px=400,
            aspect_ratio=0.88,
            bbox=[200, 100, 450, 360],  # width ratio 260/1000 -> 2.21 in
            page_width_in=8.5,
            col_width_in=3.5,
        )
        self.assertIn(geom_bounds.category, ("detailed_diagram", "compact_shape"))
        self.assertGreaterEqual(geom_bounds.min_width_in, 1.10)
        self.assertGreaterEqual(geom_bounds.preferred_width_in, 1.50)

    def test_elastic_squeeze_overflow_prevention(self):
        """Verifies that the packing engine elastically compresses diagrams to absorb slight overflows and prevent extra pages."""
        cropped_path, w, h, ar = auto_crop_image(self.sample_diagram)

        # Create two problems in a single-column layout whose preferred heights together
        # slightly overflow printable page height (10.0 in), but can fit if squeezed.
        p1 = Problem(
            id="p1",
            number=1,
            prompt_text="Solve the triangle problem below with all detailed steps.",
            image=ProblemImage(
                media_path=str(cropped_path),
                native_width_px=w,
                native_height_px=h,
                aspect_ratio=1.0,
                preferred_width_in=3.0,
                min_width_in=1.8,
                max_width_in=3.5,
                elasticity=1.0,
            ),
            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3),  # ~0.9 in
        )

        p2 = Problem(
            id="p2",
            number=2,
            prompt_text="Solve the second geometry proof below.",
            image=ProblemImage(
                media_path=str(cropped_path),
                native_width_px=w,
                native_height_px=h,
                aspect_ratio=1.0,
                preferred_width_in=3.0,
                min_width_in=1.8,
                max_width_in=3.5,
                elasticity=1.0,
            ),
            workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3),
        )

        ws = WorksheetSpec(
            title="Single Page Elastic Squeeze Test",
            default_columns=1,
            sections=[
                WorksheetSection(
                    id="sec_squeeze",
                    problems=[p1, p2],
                )
            ],
        )

        # Total preferred stacked height for each is ~ text (0.4) + img (3.0) + ws (0.9) + pad (0.16) = ~4.46 in
        # Header on page 1 is 0.75 in.
        # Two problems = 0.75 + 4.46 + 0.10 + 4.46 + 0.10 = 9.87 in (just on edge)
        # Let's adjust workspace lines slightly to induce an overflow of 0.4 in
        p1.workspace.lines = 6  # ~1.8 in -> total footprint ~5.36 in
        p2.workspace.lines = 6  # ~1.8 in -> total footprint ~5.36 in
        # Without squeeze: 0.75 + 5.36 + 0.1 + 5.36 = 11.57 in > 10.0 in printable height!
        # With image squeeze from 3.0 in down towards 1.8 in:
        # Can save up to 2 * (3.0 - 1.8) = 2.4 in!
        # Overflow is ~1.57 in, so squeezing both images to ~2.2 in will allow both to fit on 1 page!

        plan = LayoutEngine(ws).pack()

        # Both problems must be packed onto page 1!
        self.assertEqual(plan.total_pages, 1)
        self.assertEqual(len(plan.pages[0].items), 2)
        # Verify both images were compressed within valid bounds
        item1: PlacedProblem = plan.pages[0].items[0]
        item2: PlacedProblem = plan.pages[0].items[1]
        self.assertLess(item1.image_render_width_in, 3.0)
        self.assertGreaterEqual(item1.image_render_width_in, 1.8)
        self.assertLess(item2.image_render_width_in, 3.0)
        self.assertGreaterEqual(item2.image_render_width_in, 1.8)

    def test_empty_workspace_budgeting_and_no_underlines(self):
        """Verifies approx workspace budgeting and confirms no underline rules are rendered."""
        # 1. Test AST syncing & area scaling
        p1 = Problem(id="q1", number=1, prompt_text="Solve for x.", approx_workspace_in=1.5)
        self.assertEqual(p1.workspace.approx_height_in, 1.5)
        self.assertEqual(p1.workspace.effective_height_in(col_width_in=3.5), 1.5)

        p2 = Problem(id="q2", number=2, prompt_text="Explain reasoning.", approx_workspace_area_sq_in=7.0)
        self.assertEqual(p2.workspace.approx_area_sq_in, 7.0)
        self.assertAlmostEqual(p2.workspace.effective_height_in(col_width_in=3.5), 2.0, places=2)

        p3 = Problem(id="q3", number=3, prompt_text="Legacy lines question.", workspace=WorkspaceConfig(type=WorkspaceType.LINES, lines=3))

        ws = WorksheetSpec(
            title="Clean Workspace Test",
            default_columns=1,
            sections=[
                WorksheetSection(
                    id="sec_clean",
                    problems=[p1, p2, p3],
                )
            ],
        )

        plan = LayoutEngine(ws).pack()
        self.assertGreaterEqual(plan.total_pages, 1)

        # Footprint of p1 must reflect 1.5 in workspace
        placed_p1: PlacedProblem = plan.pages[0].items[0]
        self.assertAlmostEqual(placed_p1.workspace_height_in, 1.5, places=2)

        # 2. DOCX Rendering Verification: must NOT contain underscore lines
        docx_file = self.temp_dir / "clean_workspace.docx"
        DocxWorksheetRenderer(plan).render(docx_file)
        self.assertTrue(docx_file.exists())

        from docx import Document
        doc = Document(str(docx_file))
        # Ensure problem tables (tbl 1 onwards) contain no underscore strings
        self.assertGreater(len(doc.tables), 1)
        for tbl in doc.tables[1:]:
            for row in tbl.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        self.assertNotIn("____", p.text)

        # 3. LaTeX Rendering Verification: must contain \vspace and NO workspace \hrule rules
        tex_file = self.temp_dir / "clean_workspace.tex"
        LatexWorksheetRenderer(plan).render(tex_file, compile_pdf=False)
        self.assertTrue(tex_file.exists())
        tex_str = tex_file.read_text(encoding="utf-8")
        self.assertIn("\\vspace*{1.50in}", tex_str)
        self.assertNotIn("height 0.3pt", tex_str)  # Legacy workspace rules must not be generated

    def test_column_balancing_and_even_spacing(self):
        """Verifies that 6 questions on a 2-column page balance evenly (3 in each column) with generous spacing."""
        mc_probs = [
            Problem(
                id=f"q{i}",
                number=i,
                prompt_text=f"Question {i}: What is the output of the following Java snippet?",
                choices=[
                    QuestionChoice(label="(A)", text=f"Result A{i}"),
                    QuestionChoice(label="(B)", text=f"Result B{i}"),
                    QuestionChoice(label="(C)", text=f"Result C{i}"),
                    QuestionChoice(label="(D)", text=f"Result D{i}"),
                ],
                workspace=WorkspaceConfig(type=WorkspaceType.NONE),
            )
            for i in range(1, 7)
        ]

        spec = WorksheetSpec(
            title="CodeHS Unit 1 Retake Assessment",
            subtitle="Balanced Column Spacing Verification",
            default_columns=2,
            sections=[
                WorksheetSection(
                    id="mc_sec",
                    title="Part I: Multiple Choice",
                    ordering=SectionOrdering.STRICT,
                    problems=mc_probs,
                )
            ],
        )

        plan = LayoutEngine(spec).pack()

        # All 6 questions must fit on 1 page
        self.assertEqual(plan.total_pages, 1)
        page1 = plan.pages[0]

        problems_placed = [it for it in page1.items if isinstance(it, PlacedProblem)]
        self.assertEqual(len(problems_placed), 6)

        col0_items = [p for p in problems_placed if p.col_index == 0]
        col1_items = [p for p in problems_placed if p.col_index == 1]

        # Crucial check: Exactly 3 in Col 0 and 3 in Col 1 (NOT 4 or 5 in Col 0 and 1 or 2 in Col 1!)
        self.assertEqual(len(col0_items), 3, "Col 0 must have exactly 3 questions!")
        self.assertEqual(len(col1_items), 3, "Col 1 must have exactly 3 questions!")

        # Verify problem order
        self.assertEqual([p.problem.number for p in col0_items], [1, 2, 3])
        self.assertEqual([p.problem.number for p in col1_items], [4, 5, 6])

        # Verify vertical spacing is expanded beyond base 0.10 in
        for p in problems_placed:
            self.assertGreater(p.spacing_after_in, 0.15, "Spacing must be expanded to make better use of page space!")

        # Verify LaTeX renderer output includes \columnbreak
        tex_path = self.temp_dir / "balanced_test.tex"
        saved_tex = LatexWorksheetRenderer(plan).render(tex_path, compile_pdf=False)
        tex_content = saved_tex.read_text(encoding="utf-8")
        self.assertIn("\\columnbreak", tex_content, "LaTeX must include explicit \\columnbreak between balanced columns!")

        # Verify DOCX renderer output compiles cleanly
        docx_path = self.temp_dir / "balanced_test.docx"
        saved_docx = DocxWorksheetRenderer(plan).render(docx_path)
        self.assertTrue(saved_docx.exists())

    def test_odd_count_column_balancing(self):
        """Verifies that 5 questions on a 2-column page balance as 3 in left column and 2 in right column."""
        probs = [
            Problem(
                id=f"q{i}",
                number=i,
                prompt_text=f"Short question {i} prompt text for odd count test.",
                choices=[
                    QuestionChoice(label="(A)", text="Choice 1"),
                    QuestionChoice(label="(B)", text="Choice 2"),
                ],
                workspace=WorkspaceConfig(type=WorkspaceType.NONE),
            )
            for i in range(1, 6)
        ]

        spec = WorksheetSpec(
            title="Odd Count Balance Test",
            default_columns=2,
            sections=[
                WorksheetSection(
                    id="sec_odd",
                    ordering=SectionOrdering.STRICT,
                    problems=probs,
                )
            ],
        )

        plan = LayoutEngine(spec).pack()
        self.assertEqual(plan.total_pages, 1)

        problems_placed = [it for it in plan.pages[0].items if isinstance(it, PlacedProblem)]
        col0_items = [p for p in problems_placed if p.col_index == 0]
        col1_items = [p for p in problems_placed if p.col_index == 1]

        self.assertEqual(len(col0_items), 3, "Col 0 must have 3 questions for a 5-question set!")
        self.assertEqual(len(col1_items), 2, "Col 1 must have 2 questions for a 5-question set!")
        self.assertEqual([p.problem.number for p in col0_items], [1, 2, 3])
        self.assertEqual([p.problem.number for p in col1_items], [4, 5])

    def test_multipage_balanced_distribution_and_column_balance(self):
        """Verifies that 20 questions in a multi-page section distribute evenly (e.g. 7, 7, 6)

        and that the final 6-question page splits evenly into 3 in each column.
        """
        probs = [
            Problem(
                id=f"q{i}",
                number=i,
                prompt_text=f"Question {i}: What is the output of running this Java program?\nint x = {i * 2};\nSystem.out.println(x);",
                choices=[
                    QuestionChoice(label="(A)", text=f"{i * 2}"),
                    QuestionChoice(label="(B)", text=f"{i}"),
                    QuestionChoice(label="(C)", text=f"{i * 4}"),
                    QuestionChoice(label="(D)", text="0"),
                ],
                workspace=WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=1.15),
            )
            for i in range(1, 21)
        ]

        spec = WorksheetSpec(
            title="AP Computer Science A Assessment",
            default_columns=2,
            margins=PageMargins(top_in=0.38, bottom_in=0.38, left_in=0.42, right_in=0.42),
            default_font_size_pt=8.5,
            sections=[
                WorksheetSection(
                    id="sec_all",
                    ordering=SectionOrdering.STRICT,
                    problems=probs,
                )
            ],
        )

        plan = LayoutEngine(spec).pack()
        self.assertEqual(plan.total_pages, 3, "20 questions should pack into 3 pages!")

        # Page 1: 7 questions (4 in col 0, 3 in col 1)
        p1_probs = [it for it in plan.pages[0].items if isinstance(it, PlacedProblem)]
        p1_c0 = [it for it in p1_probs if it.col_index == 0]
        p1_c1 = [it for it in p1_probs if it.col_index == 1]
        self.assertEqual(len(p1_c0), 4)
        self.assertEqual(len(p1_c1), 3)

        # Page 2: 7 questions (4 in col 0, 3 in col 1)
        p2_probs = [it for it in plan.pages[1].items if isinstance(it, PlacedProblem)]
        p2_c0 = [it for it in p2_probs if it.col_index == 0]
        p2_c1 = [it for it in p2_probs if it.col_index == 1]
        self.assertEqual(len(p2_c0), 4)
        self.assertEqual(len(p2_c1), 3)

        # Page 3: 6 questions (3 in col 0, 3 in col 1)
        p3_probs = [it for it in plan.pages[2].items if isinstance(it, PlacedProblem)]
        p3_c0 = [it for it in p3_probs if it.col_index == 0]
        p3_c1 = [it for it in p3_probs if it.col_index == 1]
        self.assertEqual(len(p3_c0), 3, "Page 3 Column 0 must have exactly 3 questions!")
        self.assertEqual(len(p3_c1), 3, "Page 3 Column 1 must have exactly 3 questions!")
        self.assertTrue(all(it.spacing_after_in > 0.15 for it in p3_probs), "Problems should be spaced out!")

    def test_font_scaling_on_sparse_page(self):
        """Verifies that when content doesn't use the whole page, font size is increased to fill space."""
        probs = [
            Problem(
                id=f"q{i}",
                number=i,
                prompt_text=f"Evaluate the derivative of f(x) = {i}x^2 + {i*3}x - 5.",
                workspace=WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=1.0),
            )
            for i in range(1, 4)
        ]

        spec = WorksheetSpec(
            title="Calculus Derivatives Quiz",
            default_columns=1,
            default_font_size_pt=10.5,
            max_font_size_pt=14.0,
            auto_scale_font=True,
            sections=[
                WorksheetSection(
                    id="sec_main",
                    ordering=SectionOrdering.STRICT,
                    problems=probs,
                )
            ],
        )

        plan = LayoutEngine(spec).pack()
        self.assertEqual(plan.total_pages, 1)

        placed_probs = [it for it in plan.pages[0].items if isinstance(it, PlacedProblem)]
        self.assertEqual(len(placed_probs), 3)

        # The font size should have scaled up from default 10.5 pt because there was ample space
        scaled_fs = placed_probs[0].font_size_pt
        self.assertIsNotNone(scaled_fs)
        self.assertGreater(scaled_fs, 10.5, f"Font size should increase from 10.5 pt, got {scaled_fs}")
        self.assertLessEqual(scaled_fs, 14.0)
        self.assertEqual(plan.pages[0].font_size_pt, scaled_fs)

        # Workspace height should be preserved
        for p in placed_probs:
            self.assertAlmostEqual(p.workspace_height_in, 1.0, places=2)

        # Verify DOCX rendering applies the scaled font size
        docx_path = self.temp_dir / "scaled_font.docx"
        DocxWorksheetRenderer(plan).render(docx_path)
        self.assertTrue(docx_path.exists())

        from docx import Document
        doc = Document(str(docx_path))
        # Find runs in tables to ensure font size is set
        found_scaled_run = False
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        for r in p.runs:
                            if r.font.size and abs(r.font.size.pt - scaled_fs) < 0.1:
                                found_scaled_run = True
                                break
        self.assertTrue(found_scaled_run, f"DOCX should contain runs with font size {scaled_fs} pt")

        # Verify LaTeX rendering applies the scaled font size
        tex_path = self.temp_dir / "scaled_font.tex"
        LatexWorksheetRenderer(plan).render(tex_path, compile_pdf=False)
        self.assertTrue(tex_path.exists())
        tex_content = tex_path.read_text(encoding="utf-8")
        self.assertIn(f"\\fontsize{{{scaled_fs:.1f}pt}}", tex_content)

    def test_font_scaling_disabled_behavior(self):
        """Verifies that auto_scale_font=False keeps default_font_size_pt."""
        probs = [
            Problem(
                id=f"q{i}",
                number=i,
                prompt_text=f"Evaluate the limit as x approaches {i}.",
                workspace=WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=1.0),
            )
            for i in range(1, 3)
        ]

        spec = WorksheetSpec(
            title="Limits Quiz",
            default_columns=1,
            default_font_size_pt=10.5,
            auto_scale_font=False,
            sections=[
                WorksheetSection(
                    id="sec_main",
                    ordering=SectionOrdering.STRICT,
                    problems=probs,
                )
            ],
        )

        plan = LayoutEngine(spec).pack()
        placed_probs = [it for it in plan.pages[0].items if isinstance(it, PlacedProblem)]
        # When disabled, font_size_pt remains default 10.5 pt
        self.assertEqual(placed_probs[0].font_size_pt, 10.5)

    def test_multipart_problem_formatting_and_workspace_distribution(self):
        """Verifies multi-part problems receive bold part letters and workspace redistribution."""
        from worksheet_packer.worksheet_ast import parse_prompt_parts

        # Test regex parser
        sample_prompt = (
            "Given triangle ABC with vertices on the coordinate plane:\n"
            "a. Calculate the length of segment AB.\n"
            "b. Find the midpoint of segment BC.\n"
            "c. Determine the equation of the median to AC."
        )
        parts = parse_prompt_parts(sample_prompt)
        self.assertEqual(len(parts), 4)
        self.assertIsNone(parts[0][0])
        self.assertEqual(parts[1][0], "a.")
        self.assertEqual(parts[2][0], "b.")
        self.assertEqual(parts[3][0], "c.")

        # Test DOCX and LaTeX rendering with workspace redistribution
        prob = Problem(
            id="multi_1",
            number=1,
            prompt_text=sample_prompt,
            workspace=WorkspaceConfig(type=WorkspaceType.BLANK, approx_height_in=1.2),
        )
        spec = WorksheetSpec(
            title="Multi-Part Assessment",
            default_columns=1,
            default_font_size_pt=10.0,
            sections=[
                WorksheetSection(
                    id="sec_main",
                    ordering=SectionOrdering.STRICT,
                    problems=[prob],
                )
            ],
        )
        plan = LayoutEngine(spec).pack()
        placed = [it for it in plan.pages[0].items if isinstance(it, PlacedProblem)][0]
        initial_ws = placed.workspace_height_in

        # DOCX rendering
        docx_path = self.temp_dir / "multipart_test.docx"
        DocxWorksheetRenderer(plan).render(docx_path)
        self.assertTrue(docx_path.exists())

        doc = Document(docx_path)
        # Find bold runs corresponding to sub-part letters
        found_parts = []
        for tbl in doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    for p in cell.paragraphs:
                        for r in p.runs:
                            if r.bold and r.text.strip() in ("a.", "b.", "c."):
                                found_parts.append(r.text.strip())
        self.assertEqual(found_parts, ["a.", "b.", "c."])

        # LaTeX rendering
        tex_path = self.temp_dir / "multipart_test.tex"
        LatexWorksheetRenderer(plan).render(tex_path, compile_pdf=False)
        self.assertTrue(tex_path.exists())
        tex_content = tex_path.read_text(encoding="utf-8")
        self.assertIn("textbf{\\color{PrimaryColor}{a.}}", tex_content)
        self.assertIn("textbf{\\color{PrimaryColor}{b.}}", tex_content)
        self.assertIn("textbf{\\color{PrimaryColor}{c.}}", tex_content)
        self.assertIn(r"\par\vspace{", tex_content)


if __name__ == "__main__":
    unittest.main()

```

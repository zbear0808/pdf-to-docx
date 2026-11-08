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


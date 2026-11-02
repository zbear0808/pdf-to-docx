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
from .image_utils import auto_crop_image, inspect_diagram_dimensions
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
    workspace_type: str = "lines"  # "lines", "box", "grid", "blank", "none"
    workspace_lines: int = 3
    workspace_height_pt: Optional[float] = None
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
   - If the diagram is square-ish or portrait, note layout_hint = "side_by_side". If it is wide or full-width, note layout_hint = "stacked".
4. WORKSPACE:
   - Note the student workspace under the question: "lines" (blank ruled lines), "box" (empty box), "grid" (graph paper), "blank" (empty space), or "none" (inline/multiple choice).
   - Estimate workspace_lines (count of visible work lines, typically 2-6) or workspace_height_pt.
5. If there is a section header (e.g. "Part I: Multiple Choice" or "Free Response"), record section_title.
"""


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

        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
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

        from google.genai import types

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
        title = doc_info.get("title") or self.doc_path.stem.replace("_", " ").title()

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

                    prob_image = ProblemImage(
                        media_path=str(clean_crop_path.resolve()),
                        native_width_px=w_px,
                        native_height_px=h_px,
                        aspect_ratio=ar,
                        auto_cropped=True,
                        caption=raw_p.diagram_caption,
                        bbox=raw_p.diagram_bbox,
                    )

                # Workspace config
                ws_type_str = raw_p.workspace_type.lower()
                ws_type = WorkspaceType.LINES
                if "box" in ws_type_str:
                    ws_type = WorkspaceType.BOX
                elif "grid" in ws_type_str:
                    ws_type = WorkspaceType.GRID
                elif "blank" in ws_type_str:
                    ws_type = WorkspaceType.BLANK
                elif "none" in ws_type_str or (raw_p.choices and raw_p.workspace_lines <= 0):
                    ws_type = WorkspaceType.NONE

                ws_cfg = WorkspaceConfig(
                    type=ws_type,
                    lines=max(0, raw_p.workspace_lines),
                    height_pt=raw_p.workspace_height_pt,
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


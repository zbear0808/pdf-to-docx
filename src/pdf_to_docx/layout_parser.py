"""Unified Multimodal Layout Parser using Gemini 2.5 Flash.

Interprets rendered PDF page images, performs spatial layout decomposition,
and produces strongly-typed PageSpec / DocumentSpec AST instances.
Supports both Markdown fast-track (for DOCX) and LaTeX fragment fast-track (for LaTeX).
"""

from __future__ import annotations
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import ValidationError

from .ir_schema import (
    Alignment,
    BoundingBox,
    BoxBlock,
    ChartBlock,
    ChartSeries,
    ChartType,
    CodeBlock,
    DocumentBlock,
    DocumentSpec,
    EquationBlock,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageSpec,
    ParagraphBlock,
    QuestionBlock,
    QuestionChoice,
    TableBlock,
    TableCell,
    TextRun,
)


LAYOUT_EXTRACTION_PROMPT = """Analyze this document page image and output a precise structured JSON matching the PageSpec schema.

Guidelines:
1. Deconstruct the layout into logical blocks in reading order: headings, paragraphs, equations, tables, charts, images, boxes, or questions.
2. For HEADINGS: Identify hierarchical level (1-4), text, alignment, and bounding box [ymin, xmin, ymax, xmax] (0-1000 scale).
3. For PARAGRAPHS: Preserve typography (bold, italic, colors), detect if it's a bullet list or numbered list, and identify callouts/highlights.
4. For MATHEMATICAL FORMULAS & SYMBOLS:
   - Inline math: Set TextRun.is_math = true or enclose in $...$ (e.g. $z = \\frac{x - \\mu}{\\sigma}$, $\\bar{x}$, $\\sigma^2$, $\\hat{p}$).
   - Display equations: Use EquationBlock with latex_code.
   - Preserve all Greek letters, fractions, superscripts, subscripts, summations, integrals.
5. For EXAM & QUIZ QUESTIONS:
   - If this is an exam, test, or problem set, use QuestionBlock with number, points, prompt, multiple choice options, and response_box_height_pt.
6. For TABLES: Extract full tabular structure with headers and rows. Preserve exact mathematical symbols, numbers, and units.
7. For CHARTS: Identify chart type (bar, line, pie), extract the title, category labels, and series data values so it can be re-rendered programmatically. Also provide bbox.
8. For FIGURES / IMAGES / LOGOS / SIGNATURES: Provide bounding box [ymin, xmin, ymax, xmax] (0-1000 scale) so they can be cropped from the PDF.
9. For CALLOUT / FRAMED BOXES: Use BoxBlock with title and content.
10. Set page orientation to 'portrait' or 'landscape'.
"""


FAST_TRACK_LATEX_PROMPT = """Convert this document page image directly into a clean, modular LaTeX body fragment suitable for \\input{...}.

Formatting Rules:
1. Do NOT include \\documentclass, \\begin{document}, or preamble. Output ONLY the body content for this page.
2. Mathematics: Use proper LaTeX math environments ($...$ for inline, \\[...\\] or \\begin{equation} for display math, \\frac, \\sqrt, Greek letters, etc.).
3. Headings: Use \\section*, \\subsection*, \\subsubsection*.
4. Tables: Use clean booktabs formatting (\\begin{table}[htbp] \\centering \\begin{tabular}{...} \\toprule ... \\midrule ... \\bottomrule \\end{tabular} \\end{table}).
5. Exam / Quiz Questions: Format with \\paragraph{Question X} or \\question, multiple choices with enumerate or choices environment, and empty response boxes using \\begin{tcolorbox}[height=...cm] or \\makeemptybox{...}.
6. Figures / Diagrams: If there is a visual image or diagram, mark it as \\begin{figure}[htbp] \\centering \\includegraphics[width=0.8\\linewidth]{assets/p{PAGE}_asset.png} \\caption{...} \\end{figure}.
7. Do NOT include Markdown backticks (```latex) or conversational commentary.
"""


class LayoutParser:
    """Invokes Gemini Flash multimodal vision model to parse page layouts."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        self._client = None

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

    def parse_page_image(self, image_path: str | Path, page_number: int = 1) -> PageSpec:
        """Parses a rendered page image using Gemini Flash into a unified PageSpec AST."""
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")

        img_bytes = img_path.read_bytes()

        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                LAYOUT_EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PageSpec,
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )

        try:
            parsed_json = json.loads(response.text)
            spec = PageSpec.model_validate(parsed_json)
            spec.page_number = page_number
            return spec
        except (json.JSONDecodeError, ValidationError) as e:
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()
            parsed_json = json.loads(raw_text)
            spec = PageSpec.model_validate(parsed_json)
            spec.page_number = page_number
            return spec

    def parse_markdown_fast_path(self, image_path: str | Path) -> str:
        """Fast-track parsing: Converts a page image directly into GitHub-Flavored Markdown (for Word)."""
        img_path = Path(image_path)
        img_bytes = img_path.read_bytes()

        from google.genai import types

        prompt = (
            "Convert this document page into clean GitHub-Flavored Markdown (GFM). "
            "Preserve all headings (#, ##), bold, italics, bullet lists, numbered lists, "
            "and standard markdown tables (| Header | ... |). Do not include conversational text or enclosing ```markdown blocks."
        )

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        return response.text.strip()

    def parse_latex_fast_path(self, image_path: str | Path, page_number: int = 1) -> str:
        """Fast-track parsing: Converts a page image directly into a LaTeX fragment (.tex)."""
        img_path = Path(image_path)
        img_bytes = img_path.read_bytes()

        from google.genai import types

        prompt = FAST_TRACK_LATEX_PROMPT.replace("{PAGE}", str(page_number))

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                prompt,
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            ),
        )
        text = response.text.strip()
        if text.startswith("```latex"):
            text = text.split("```latex", 1)[1].split("```", 1)[0].strip()
        elif text.startswith("```tex"):
            text = text.split("```tex", 1)[1].split("```", 1)[0].strip()
        elif text.startswith("```"):
            text = text.split("```", 1)[1].split("```", 1)[0].strip()
        return text


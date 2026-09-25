"""Multimodal Layout Parser using Gemini 2.5 Flash.

Interprets rendered PDF page images, performs spatial layout decomposition,
and produces strongly-typed PageSpec / DocumentSpec AST instances.
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
    ChartBlock,
    ChartSeries,
    ChartType,
    DocumentBlock,
    DocumentSpec,
    HeadingBlock,
    ImageBlock,
    ListType,
    PageSpec,
    ParagraphBlock,
    TableBlock,
    TextRun,
)


LAYOUT_EXTRACTION_PROMPT = """Analyze this document page image and output a precise structured JSON matching the PageSpec schema.

Guidelines:
1. Deconstruct the layout into logical blocks in reading order: headings, paragraphs, tables, charts, or images.
2. For HEADINGS: Identify hierarchical level (1-4), text, alignment, and bounding box [ymin, xmin, ymax, xmax] (0-1000 scale).
3. For PARAGRAPHS: Preserve typography (bold, italic, colors), detect if it's a bullet list or numbered list, and identify callouts/highlights.
4. For TABLES: Extract full tabular structure with headers and rows. If cells have numbers or currencies, preserve exact symbols.
5. For CHARTS: Identify chart type (bar, line, pie), extract the title, category labels, and series data values so it can be re-rendered programmatically. Also provide bbox.
6. For FIGURES / IMAGES / LOGOS / SIGNATURES: Provide bounding box [ymin, xmin, ymax, xmax] so they can be cropped from the PDF.
7. Set page orientation to 'portrait' or 'landscape'.
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
            if self.api_key:
                self._client = genai.Client(api_key=self.api_key)
            else:
                self._client = genai.Client()
        return self._client

    def parse_page_image(self, image_path: str | Path, page_number: int = 1) -> PageSpec:
        """Parses a rendered page image using Gemini Flash into a PageSpec AST."""
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
            ),
        )

        try:
            parsed_json = json.loads(response.text)
            spec = PageSpec.model_validate(parsed_json)
            spec.page_number = page_number
            return spec
        except (json.JSONDecodeError, ValidationError) as e:
            # Fallback parsing if JSON contains wrapped content
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
        """Fast-track parsing: Converts a page image directly into GitHub-Flavored Markdown.

        Ideal for text and table-heavy documents that can be fed straight into docx-mcp's
        create_from_markdown tool.
        """
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
            ),
        )
        return response.text.strip()

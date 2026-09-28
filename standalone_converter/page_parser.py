"""Page-level layout parser using Gemini Flash Lite.

Sends a rendered PDF page image to Gemini with a highly constrained prompt
and receives a strongly-typed PageSpec JSON via Pydantic response_schema.

Key design choices:
- Uses gemini-2.0-flash-lite for cost/speed (structured output is well supported)
- Single deterministic prompt with no reasoning steps
- Retry with exponential backoff for transient API failures
- Per-page isolation: one image in, one PageSpec out
"""

from __future__ import annotations
import json
import logging
import os
import time
from pathlib import Path
from typing import Optional

from pydantic import ValidationError

from .ir_schema import PageSpec

logger = logging.getLogger(__name__)

def _get_api_key(api_key: Optional[str] = None) -> Optional[str]:
    """Retrieves GEMINI_API_KEY from parameter, env var, or .env file."""
    if api_key:
        return api_key
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    cur = Path.cwd()
    for parent in [cur] + list(cur.parents)[:3]:
        env_file = parent / ".env"
        if env_file.exists():
            try:
                for line in env_file.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        val = line.split("=", 1)[1].strip().strip('"').strip("'")
                        if val:
                            os.environ["GEMINI_API_KEY"] = val
                            return val
            except Exception:
                pass
    return None


# Maximally constrained prompt for Flash Lite — no reasoning, just structured extraction.
# Each instruction is numbered and specific to eliminate ambiguity.
EXTRACTION_PROMPT = """\
Extract the layout of this document page image into structured JSON matching the PageSpec schema.

Rules:
1. Output ONLY valid JSON matching the schema. No commentary, no markdown fences.
2. Identify blocks in top-to-bottom reading order. Each block is one of: heading, paragraph, table, chart, image, page_break.
3. HEADINGS: Use ONLY for major document or section titles (level 1-4). Do NOT classify numbered questions (e.g. "1.", "2.", "(a)", "(b)"), test instructions, or problem statements as headings; classify them as paragraphs.
4. PARAGRAPHS: Split text into runs. Mark bold, italic, underline, font_size_pt per run. Set list_type="bullet" or "numbered" if applicable, otherwise "none". Leave color_hex null unless the original text on the page is printed in an explicit, distinct non-black color (e.g. bright red or green). For standard black or dark monochrome text, leave color_hex null.
5. TABLES: Extract all tabular data into TableBlock.
   - Set 'headers' to the column header string list.
   - Set 'rows' to the 2D string list of data rows.
   - CRITICAL: Do NOT include the header row inside 'rows'.
   - CRITICAL: Do NOT create separate ParagraphBlocks for any text, labels, numbers, or headers that belong to a TableBlock. All table content must exist strictly inside the TableBlock to avoid duplicate data.
   - Estimate col_widths_pct (must sum to ~100).
6. CHARTS: Identify chart_type (bar/line/pie). Extract title, categories (x-axis labels), and series (name + numeric values). Provide bbox [ymin, xmin, ymax, xmax] on 0-1000 scale.
7. IMAGES/FIGURES/LOGOS: Set type="image" with bbox [ymin, xmin, ymax, xmax] on 0-1000 scale so the image can be cropped. Add caption if visible.
8. Set page orientation to "portrait" or "landscape" based on aspect ratio.
9. Bounding boxes use a 0-1000 normalized coordinate system: ymin=top edge, ymax=bottom edge, xmin=left edge, xmax=right edge.
"""


class PageParser:
    """Parses a single page image into a PageSpec AST using Gemini Flash Lite."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3.5-flash-lite",
        max_retries: int = 3,
    ):
        self.api_key = _get_api_key(api_key)
        self.model_name = model_name
        self.max_retries = max_retries
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

    def parse_page(self, image_path: str | Path, page_number: int = 1) -> PageSpec:
        """Sends a page image to Gemini Flash Lite and returns a validated PageSpec.

        Args:
            image_path: Path to the rendered page PNG.
            page_number: 1-indexed page number (set on the resulting PageSpec).

        Returns:
            A validated PageSpec instance.

        Raises:
            RuntimeError: If all retry attempts fail.
        """
        img_path = Path(image_path)
        if not img_path.exists():
            raise FileNotFoundError(f"Image not found: {img_path}")

        img_bytes = img_path.read_bytes()
        last_error: Optional[Exception] = None

        for attempt in range(1, self.max_retries + 1):
            try:
                return self._call_gemini(img_bytes, page_number)
            except Exception as e:
                last_error = e
                if attempt < self.max_retries:
                    wait = 2 ** attempt  # 2s, 4s, 8s
                    logger.warning(
                        f"Page {page_number} attempt {attempt}/{self.max_retries} failed: {e}. "
                        f"Retrying in {wait}s..."
                    )
                    time.sleep(wait)
                else:
                    logger.error(f"Page {page_number} failed after {self.max_retries} attempts: {e}")

        raise RuntimeError(
            f"Failed to parse page {page_number} after {self.max_retries} attempts. "
            f"Last error: {last_error}"
        )

    def _call_gemini(self, img_bytes: bytes, page_number: int) -> PageSpec:
        """Single Gemini API call with structured JSON output."""
        from google.genai import types

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=img_bytes, mime_type="image/png"),
                EXTRACTION_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=PageSpec,
                temperature=0.0,
            ),
        )

        raw_text = response.text.strip()

        # Strip markdown fences if the model wraps them despite instructions
        if raw_text.startswith("```"):
            # Remove ```json or ``` prefix and trailing ```
            if raw_text.startswith("```json"):
                raw_text = raw_text[7:]
            else:
                raw_text = raw_text[3:]
            if raw_text.endswith("```"):
                raw_text = raw_text[:-3]
            raw_text = raw_text.strip()

        parsed = json.loads(raw_text)
        spec = PageSpec.model_validate(parsed)
        spec.page_number = page_number
        return spec

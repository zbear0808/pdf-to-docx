"""Visual Diff and Self-Correction Engine.

Renders compiled DOCX documents headlessly and utilizes Gemini Flash vision
to inspect visual fidelity against original PDF page images.
"""

from __future__ import annotations
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional
import pymupdf as fitz
from pydantic import BaseModel, Field


class Discrepancy(BaseModel):
    category: str = Field(..., description="typography, table, chart, layout, image, margins")
    description: str
    severity: str = Field("medium", description="low, medium, high, critical")
    suggested_fix: str


class VisualCritique(BaseModel):
    fidelity_score: int = Field(..., ge=0, le=100, description="Overall layout fidelity score from 0 to 100")
    page_number: int
    matches_well: List[str] = Field(default_factory=list)
    discrepancies: List[Discrepancy] = Field(default_factory=list)
    actionable_adjustments: Dict[str, Any] = Field(default_factory=dict)


def render_docx_to_png(
    docx_path: str | Path,
    output_png_path: str | Path,
    page_number: int = 1,
    dpi: int = 200,
) -> Optional[Path]:
    """Attempts to render a DOCX page to PNG via available headless tools.

    Tries:
    1. LibreOffice ('soffice' or 'libreoffice' on PATH)
    2. Windows MS Word COM automation (if on Windows with Office installed)
    """
    docx_file = Path(docx_path).resolve()
    out_png = Path(output_png_path).resolve()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = out_png.parent / ".temp_render"
    temp_dir.mkdir(parents=True, exist_ok=True)
    pdf_out = temp_dir / f"{docx_file.stem}.pdf"

    converted = False

    # 1. Try LibreOffice CLI
    soffice_cmd = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice_cmd:
        # Check standard Windows paths
        win_candidates = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        ]
        for c in win_candidates:
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
            if pdf_out.exists():
                converted = True
        except Exception:
            pass

    # 2. Try Windows Word COM if LibreOffice unavailable
    if not converted and os.name == "nt":
        try:
            import win32com.client  # type: ignore
            word = win32com.client.Dispatch("Word.Application")
            word.Visible = False
            doc = word.Documents.Open(str(docx_file))
            # 17 = wdFormatPDF
            doc.SaveAs(str(pdf_out), FileFormat=17)
            doc.Close()
            word.Quit()
            if pdf_out.exists():
                converted = True
        except Exception:
            pass

    if not converted or not pdf_out.exists():
        return None

    # Render PDF page to PNG using PyMuPDF
    doc = fitz.open(str(pdf_out))
    if page_number > len(doc):
        page_number = 1
    page = doc[page_number - 1]
    zoom = dpi / 72.0
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(str(out_png))
    doc.close()

    # Clean up temp PDF
    try:
        shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:
        pass

    return out_png


DIFF_PROMPT = """You are a document layout QA expert. Compare these two images side-by-side:
Image 1: ORIGINAL PDF PAGE (Reference standard)
Image 2: GENERATED WORD (.DOCX) PAGE (Compiled output)

Perform a meticulous layout discrepancy analysis:
1. Typography & Hierarchy: Are heading sizes, weights, and colors faithfully reproduced?
2. Tables: Are table columns properly proportioned, borders crisp, cell padding balanced, headers distinct?
3. Charts & Figures: Are chart dimensions, titles, and legends placed accurately?
4. Page Flow: Did any content overflow or wrap awkwardly?
5. Assign a fidelity score from 0-100 and provide clear, actionable suggestions to adjust the styling AST or docx-mcp properties.
"""


class VisualDiffInspector:
    """Uses Gemini multimodal capabilities to critique and guide self-correction."""

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

    def inspect_and_critique(
        self,
        original_image_path: str | Path,
        rendered_image_path: str | Path,
        page_number: int = 1,
    ) -> VisualCritique:
        """Sends original vs rendered DOCX page to Gemini Flash for critique."""
        from google.genai import types

        orig_bytes = Path(original_image_path).read_bytes()
        rend_bytes = Path(rendered_image_path).read_bytes()

        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[
                types.Part.from_bytes(data=orig_bytes, mime_type="image/png"),
                types.Part.from_bytes(data=rend_bytes, mime_type="image/png"),
                DIFF_PROMPT,
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=VisualCritique,
                temperature=0.2,
            ),
        )

        try:
            data = json.loads(response.text)
            critique = VisualCritique.model_validate(data)
            critique.page_number = page_number
            return critique
        except Exception:
            raw_text = response.text.strip()
            if raw_text.startswith("```json"):
                raw_text = raw_text.split("```json", 1)[1].split("```", 1)[0].strip()
            elif raw_text.startswith("```"):
                raw_text = raw_text.split("```", 1)[1].split("```", 1)[0].strip()
            data = json.loads(raw_text)
            critique = VisualCritique.model_validate(data)
            critique.page_number = page_number
            return critique

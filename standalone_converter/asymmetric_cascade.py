"""Asymmetric Cascade Harness: Local Laya Router + Gemini Flash Lite Escalation.

Architecture:
    Raw PDF Block
         │
         ▼
    [ Laya Router (Local ~40ms) ]
         │
         ├─── High Confidence (>=0.85) ──► Direct DOCX MCP Tool Call (Zero API cost)
         │                                (e.g., `add_paragraph`, `add_heading`)
         │
         └─── Low Confidence / Complex ──► [ Gemini Flash-Lite ] ──► Formatted DOCX MCP Call
              (Tables, figures, bad scans)   (Reasoning + Vision)    (e.g., `add_table`, `insert_image`)

Key design properties:
- Fast local triage with Laya on GPU (CUDA) or CPU
- Zero API cost for ~80-85% of standard typography blocks
- Automatic escalation for tables, diagrams, and low-confidence structures
- Dispatches tool calls via standard DOCX MCP interface
"""

from __future__ import annotations
import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pymupdf as fitz

from .laya_router import LayaTriageRouter, TriageResult
from .mcp_dispatcher import (
    DOCX_MCP_TOOL_SCHEMAS,
    BaseDocxDispatcher,
    InProcessDocxDispatcher,
)
from .pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)


def _get_api_key(provided_key: Optional[str] = None) -> Optional[str]:
    if provided_key:
        return provided_key
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    # Try reading from .env in current or parent dirs
    for check_dir in [Path.cwd(), Path(__file__).resolve().parent.parent]:
        env_file = check_dir / ".env"
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


@dataclass
class CascadeStats:
    """Performance statistics for an asymmetric cascade conversion run."""
    total_blocks: int = 0
    artifacts_dropped: int = 0
    fast_path_blocks: int = 0
    escalated_blocks: int = 0
    fast_path_ratio: float = 0.0
    elapsed_seconds: float = 0.0


class AsymmetricCascadeConverter:
    """Orchestrates document conversion via an asymmetric cascade of Laya + Gemini."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3.5-flash-lite",
        device: Optional[str] = None,

        confidence_threshold: float = 0.85,
        theme_hex: str = "#1F4E79",
        dispatcher: Optional[BaseDocxDispatcher] = None,
    ):
        self.api_key = _get_api_key(api_key)
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.theme_hex = theme_hex
        self.dispatcher = dispatcher or InProcessDocxDispatcher(theme_hex=theme_hex)

        # Layer 1: Laya local router
        self.laya = LayaTriageRouter(
            device=device,
            confidence_threshold=confidence_threshold,
        )

        # Layer 2: Gemini client
        self._gemini_client = None

    @property
    def gemini_client(self):
        if self._gemini_client is None:
            from google import genai
            if self.api_key:
                self._gemini_client = genai.Client(api_key=self.api_key)
            else:
                self._gemini_client = genai.Client()
        return self._gemini_client

    def convert(
        self,
        pdf_path: str | Path,
        output_path: str | Path = "output.docx",
        workspace_dir: Optional[str | Path] = None,
    ) -> Path:
        """Runs the Asymmetric Cascade pipeline on a PDF file.

        Args:
            pdf_path: Path to input PDF.
            output_path: Target .docx path.
            workspace_dir: Directory for temporary cropped images.

        Returns:
            Path to created .docx file.
        """
        start_time = time.perf_counter()
        pdf_path = Path(pdf_path)
        output_path = Path(output_path)
        work_dir = Path(workspace_dir or output_path.parent / f".cascade_{pdf_path.stem}")
        crops_dir = work_dir / "crops"
        crops_dir.mkdir(parents=True, exist_ok=True)

        stats = CascadeStats()

        logger.info(f"Starting Asymmetric Cascade for: {pdf_path}")

        with PDFExtractor(pdf_path) as extractor:
            doc = extractor.doc

            for page_idx, page in enumerate(doc):
                page_num = page_idx + 1
                logger.info(f"--- Processing Page {page_num}/{len(doc)} ---")

                if page_idx > 0:
                    self.dispatcher.add_page_break()

                # Extract raw blocks: (x0, y0, x1, y1, text, block_no, block_type)
                # block_type 0 = text, 1 = image
                raw_blocks = page.get_text("blocks")
                page_rect = page.rect

                # Pure image or scanned page with no text stream
                if len(raw_blocks) == 0:
                    logger.info(f"[Page {page_num}] No text blocks found (image-only/scanned page). Rendering page...")
                    page_img_path = crops_dir / f"p{page_num}_fullpage.png"
                    extractor.render_page_to_png(page_num, page_img_path, dpi=200)
                    self.dispatcher.insert_image(page_img_path, width_inches=6.0)
                    stats.fast_path_blocks += 1
                    continue


                # 2. Collect text blocks and embedded images in vertical reading order
                page_items = []
                for b_idx, b in enumerate(raw_blocks):
                    x0, y0, x1, y1, text, block_no, b_type = b
                    page_items.append({
                        "kind": "text",
                        "y0": y0,
                        "x0": x0,
                        "raw_block": b,
                        "idx": b_idx,
                    })

                try:
                    embedded_images = page.get_image_info(xrefs=True)
                    for img_idx, img_info in enumerate(embedded_images):
                        xref = img_info.get("xref")
                        bbox = img_info.get("bbox")
                        if xref and bbox:
                            page_items.append({
                                "kind": "embedded_image",
                                "y0": bbox[1],
                                "x0": bbox[0],
                                "bbox": bbox,
                                "xref": xref,
                                "idx": img_idx,
                            })
                except Exception as img_err:
                    logger.debug(f"Could not get image info for page {page_num}: {img_err}")

                # Sort top-to-bottom
                page_items.sort(key=lambda item: (item["y0"], item["x0"]))

                for item in page_items:
                    # Handle embedded raster figures (charts, plots, diagrams)
                    if item["kind"] == "embedded_image":
                        bbox = item["bbox"]
                        xref = item["xref"]
                        w_pt = bbox[2] - bbox[0]
                        h_pt = bbox[3] - bbox[1]
                        if w_pt < 25 or h_pt < 25:
                            continue

                        stats.total_blocks += 1
                        img_path = crops_dir / f"p{page_num}_img_xref{xref}.png"
                        if not img_path.exists():
                            try:
                                pix = doc.extract_image(xref)
                                ext = pix.get("ext", "png")
                                img_path = crops_dir / f"p{page_num}_img_xref{xref}.{ext}"
                                img_path.write_bytes(pix["image"])
                            except Exception as e:
                                logger.warning(f"Could not extract image xref {xref}: {e}")
                                continue

                        w_in = min(6.0, max(2.5, w_pt / 72.0))
                        self.dispatcher.insert_image(img_path, width_inches=w_in)
                        stats.fast_path_blocks += 1
                        logger.info(f"[Page {page_num}] Inserted embedded figure/chart: {img_path.name} ({w_in:.2f} in)")
                        continue

                    # Text block processing
                    b = item["raw_block"]
                    b_idx = item["idx"]
                    x0, y0, x1, y1, text, block_no, b_type = b
                    clean_text = text.strip() if isinstance(text, str) else ""

                    stats.total_blocks += 1

                    # Normalized bbox (0-1000 scale)
                    ymin = int((y0 / page_rect.height) * 1000)
                    xmin = int((x0 / page_rect.width) * 1000)
                    ymax = int((y1 / page_rect.height) * 1000)
                    xmax = int((x1 / page_rect.width) * 1000)
                    bbox = [max(0, ymin), max(0, xmin), min(1000, ymax), min(1000, xmax)]

                    # Handle native PDF inline image blocks
                    if b_type == 1 or not clean_text:
                        crop_path = crops_dir / f"p{page_num}_b{b_idx}_img.png"
                        try:
                            extractor.extract_region(page_num, bbox, crop_path, dpi=300)
                            self.dispatcher.insert_image(crop_path)
                            stats.fast_path_blocks += 1
                        except Exception as e:
                            logger.warning(f"Failed to crop image block {b_idx}: {e}")
                        continue

                    # ── STEP 1: Fast local evaluation with Laya (~40ms) ──
                    triage: TriageResult = self.laya.predict(clean_text, bbox=bbox)

                    # Drop artifacts immediately (headers, footers, page numbers)
                    if triage.is_artifact:
                        logger.debug(f"[Page {page_num}] Dropped artifact: '{clean_text[:40]}...'")
                        stats.artifacts_dropped += 1
                        continue

                    # ── STEP 2: Fast Path (Direct DOCX Tool Calling) ──
                    # Zero API cost for confident typography blocks
                    if not triage.should_escalate:
                        choice = triage.block_type
                        if choice == "heading_1":
                            self.dispatcher.add_heading(clean_text, level=1)
                        elif choice == "heading_2":
                            self.dispatcher.add_heading(clean_text, level=2)
                        elif choice == "list_item":
                            # Strip leading bullet/number marker if desired
                            self.dispatcher.add_paragraph(clean_text, style="List Bullet")
                        else:
                            self.dispatcher.add_paragraph(clean_text, style="Normal")

                        stats.fast_path_blocks += 1
                        logger.debug(
                            f"[Page {page_num}] FAST PATH ({choice}, conf={triage.confidence:.2f}): "
                            f"'{clean_text[:40]}...'"
                        )
                        continue

                    # ── STEP 3: Escalation Path (Gemini Flash-Lite) ──
                    # Triggered for tables, complex layouts, figures, or low-confidence blocks
                    logger.info(
                        f"[Page {page_num}] ESCALATING block {b_idx} ({triage.block_type}, "
                        f"conf={triage.confidence:.2f}): '{clean_text[:40]}...'"
                    )
                    stats.escalated_blocks += 1

                    # Crop region snippet for vision analysis
                    crop_path = crops_dir / f"p{page_num}_b{b_idx}_crop.png"
                    try:
                        extractor.extract_region(page_num, bbox, crop_path, dpi=300)
                    except Exception as crop_err:
                        logger.warning(f"Could not crop region: {crop_err}")
                        crop_path = None

                    self._escalate_to_gemini(clean_text, crop_path, page_num)

        # Save the completed document
        out_file = self.dispatcher.save(output_path)

        stats.elapsed_seconds = time.perf_counter() - start_time
        non_artifact_blocks = max(1, stats.total_blocks - stats.artifacts_dropped)
        stats.fast_path_ratio = stats.fast_path_blocks / non_artifact_blocks

        logger.info(
            f"Cascade Complete in {stats.elapsed_seconds:.2f}s! "
            f"Total blocks: {stats.total_blocks} | Artifacts dropped: {stats.artifacts_dropped} | "
            f"Fast path: {stats.fast_path_blocks} ({stats.fast_path_ratio * 100:.1f}%) | "
            f"Escalated: {stats.escalated_blocks} | Output: {out_file}"
        )

        return out_file

    def _escalate_to_gemini(
        self,
        block_text: str,
        crop_image_path: Optional[Path],
        page_number: int,
    ):
        """Escalates complex or ambiguous blocks to Gemini Flash Lite for structured extraction."""
        from google.genai import types

        contents: List[Any] = []

        if crop_image_path and crop_image_path.exists():
            contents.append(
                types.Part.from_bytes(
                    data=crop_image_path.read_bytes(),
                    mime_type="image/png",
                )
            )

        prompt = (
            f"Analyze this document block from page {page_number} and extract its structure.\n"
            f"Raw text:\n\"\"\"{block_text}\"\"\"\n\n"
            "Call the appropriate tool with structured arguments:\n"
            "- If it is tabular data, call `add_table` with `headers` and 2D `rows`.\n"
            "- If it is a heading, call `add_heading` with `text` and `level` (1-4).\n"
            "- If it is a diagram or graphic, call `insert_image`.\n"
            "- Otherwise, call `add_paragraph` with `text` and `style` ('Normal', 'List Bullet')."
        )
        contents.append(prompt)

        # Convert tool schemas to Gemini FunctionDeclarations
        function_declarations = []
        for schema in DOCX_MCP_TOOL_SCHEMAS:
            function_declarations.append(
                types.FunctionDeclaration(
                    name=schema["name"],
                    description=schema["description"],
                    parameters=schema["parameters"],
                )
            )

        tools = [types.Tool(function_declarations=function_declarations)]

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.gemini_client.models.generate_content(
                    model=self.model_name,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        tools=tools,
                        temperature=0.0,
                    ),
                )

                # Execute tool calls returned by Gemini
                calls = response.function_calls
                if calls:
                    for call in calls:
                        call_args = dict(call.args or {})
                        if call.name == "insert_image" and crop_image_path:
                            if not call_args.get("image_path") or call_args.get("image_path") in ("CROP", "image", "", "crop"):
                                call_args["image_path"] = str(crop_image_path)
                        logger.info(f"  Gemini dispatched tool: {call.name}")
                        self.dispatcher.call_tool(call.name, call_args)
                else:
                    # If model responded with text instead of a tool call, add as paragraph
                    logger.debug("Gemini returned text response without tool calls; adding as paragraph.")
                    self.dispatcher.add_paragraph(block_text, style="Normal")

                # Polite pause to stay well within free tier RPM limits
                time.sleep(1.0)
                return

            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "ResourceExhausted" in err_str or "quota" in err_str.lower()) and attempt < max_retries - 1:
                    wait_sec = (attempt + 1) * 8
                    logger.warning(f"Gemini rate limited (429). Retrying in {wait_sec}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_sec)
                    continue
                logger.error(f"Gemini escalation failed ({e}). Falling back to plain paragraph.")
                self.dispatcher.add_paragraph(block_text, style="Normal")
                return


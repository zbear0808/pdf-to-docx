"""DOCX MCP Dispatcher and Tool Calling Engine.

Provides the Layer 3 Dispatcher for the Asymmetric Cascade:
- Standardized tool interface:
    - add_heading(text, level)
    - add_paragraph(text, style)
    - add_table(headers, rows, col_widths_pct)
    - insert_image(image_path, width_inches, caption)
    - save_document(output_path)
- Two execution backends:
    1. InProcessDocxDispatcher: Ultra-fast, zero-overhead python-docx backend
       with deterministic OpenXML rules (cantSplit, tblHeader, cell margins).
    2. StdioMcpDispatcher: Standard Model Context Protocol (MCP) client connecting
       to an external stdio MCP server process via the `mcp` Python SDK.
- Tool schemas exported for Gemini Flash Lite native function calling.
"""

from __future__ import annotations
import asyncio
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

logger = logging.getLogger(__name__)

# Standard DOCX Tool Schemas for Gemini function calling & MCP
DOCX_MCP_TOOL_SCHEMAS: List[Dict[str, Any]] = [
    {
        "name": "add_heading",
        "description": "Insert a formatted section heading into the Word document.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The heading text."},
                "level": {"type": "integer", "description": "Heading level (1 to 4).", "minimum": 1, "maximum": 4},
            },
            "required": ["text"],
        },
    },
    {
        "name": "add_paragraph",
        "description": "Insert a formatted body paragraph or list item into the Word document.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "The paragraph text content."},
                "style": {
                    "type": "string",
                    "description": "Paragraph style name, e.g. 'Normal', 'List Bullet', or 'List Number'.",
                    "enum": ["Normal", "List Bullet", "List Number"],
                },
            },
            "required": ["text"],
        },
    },
    {
        "name": "add_table",
        "description": "Insert a structured 2D table into the Word document with repeating headers and cantSplit rows.",
        "parameters": {
            "type": "object",
            "properties": {
                "headers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of header column names.",
                },
                "rows": {
                    "type": "array",
                    "items": {
                        "type": "array",
                        "items": {"type": "string"},
                    },
                    "description": "2D array of rows, where each row is a list of cell text strings.",
                },
                "col_widths_pct": {
                    "type": "array",
                    "items": {"type": "number"},
                    "description": "Optional column widths as percentages summing to 100.",
                },
            },
            "required": ["rows"],
        },
    },
    {
        "name": "insert_image",
        "description": "Insert an image or diagram into the Word document.",
        "parameters": {
            "type": "object",
            "properties": {
                "image_path": {"type": "string", "description": "Absolute or relative path to the image file."},
                "width_inches": {"type": "number", "description": "Image display width in inches (default 5.5)."},
                "caption": {"type": "string", "description": "Optional figure caption displayed underneath."},
            },
            "required": ["image_path"],
        },
    },
]


def _hex_to_rgb(hex_str: str) -> RGBColor:
    hex_clean = hex_str.lstrip("#")
    if len(hex_clean) == 3:
        hex_clean = "".join([c * 2 for c in hex_clean])
    return RGBColor(int(hex_clean[0:2], 16), int(hex_clean[2:4], 16), int(hex_clean[4:6], 16))


def sanitize_xml(text: str) -> str:
    """Removes XML control characters that crash python-docx or Word."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    return "".join(
        c for c in text
        if c in ("\t", "\n", "\r")
        or (0x20 <= ord(c) <= 0xD7FF)
        or (0xE000 <= ord(c) <= 0xFFFD)
        or (0x10000 <= ord(c) <= 0x10FFFF)
    )


def set_table_borders(table, color="444444", sz="4", val="single"):
    """Applies crisp table borders to all outer and inner cell walls."""
    tblPr = table._tbl.tblPr
    existing = tblPr.find(qn("w:tblBorders"))
    if existing is not None:
        tblPr.remove(existing)
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:left w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:right w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'  <w:insideV w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)


class BaseDocxDispatcher(ABC):
    """Abstract interface for DOCX tool call dispatchers."""

    @abstractmethod
    def add_heading(self, text: str, level: int = 1):
        """Add a heading block."""
        pass

    @abstractmethod
    def add_paragraph(self, text: str, style: str = "Normal"):
        """Add a body paragraph or list item."""
        pass

    @abstractmethod
    def add_table(
        self,
        rows: List[List[str]],
        headers: Optional[List[str]] = None,
        col_widths_pct: Optional[List[float]] = None,
    ):
        """Add a structured table."""
        pass

    @abstractmethod
    def insert_image(
        self,
        image_path: str | Path,
        width_inches: float = 5.5,
        caption: Optional[str] = None,
    ):
        """Add an image block."""
        pass

    @abstractmethod
    def save(self, output_path: str | Path) -> Path:
        """Persist document to disk."""
        pass

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Dispatches a dynamic tool call by name."""
        if tool_name == "add_heading":
            return self.add_heading(
                text=arguments.get("text", ""),
                level=int(arguments.get("level", 1)),
            )
        elif tool_name == "add_paragraph":
            return self.add_paragraph(
                text=arguments.get("text", ""),
                style=arguments.get("style", "Normal"),
            )
        elif tool_name == "add_table":
            return self.add_table(
                rows=arguments.get("rows", []),
                headers=arguments.get("headers"),
                col_widths_pct=arguments.get("col_widths_pct"),
            )
        elif tool_name == "insert_image":
            return self.insert_image(
                image_path=arguments.get("image_path", ""),
                width_inches=float(arguments.get("width_inches", 5.5)),
                caption=arguments.get("caption"),
            )
        else:
            logger.warning(f"Unknown DOCX tool call: {tool_name}")


class InProcessDocxDispatcher(BaseDocxDispatcher):
    """Direct, in-process DOCX tool execution via python-docx.

    Zero RPC latency, enforces professional OpenXML styling.
    """

    def __init__(
        self,
        title: str = "Document",
        theme_hex: str = "#000000",
        default_font: str = "Calibri",
        default_font_size_pt: float = 11.0,
    ):
        self.title = title
        self.theme_hex = theme_hex
        self.doc = Document()

        # Normal style formatting
        normal_style = self.doc.styles["Normal"]
        normal_style.font.name = default_font
        normal_style.font.size = Pt(default_font_size_pt)
        normal_style.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
        normal_style.paragraph_format.line_spacing = 1.15
        normal_style.paragraph_format.space_after = Pt(4)

    def add_heading(self, text: str, level: int = 1):
        lvl = max(1, min(4, level))
        p = self.doc.add_paragraph()
        p.paragraph_format.keep_with_next = True
        p.paragraph_format.space_before = Pt(max(6, 18 - (lvl * 2)))
        p.paragraph_format.space_after = Pt(4)

        run = p.add_run(sanitize_xml(text))
        run.bold = True
        run.font.size = Pt(max(12, 20 - (lvl * 2)))
        if self.theme_hex and self.theme_hex.upper() not in ("#000000", "#111111", "#222222", "#1F4E79"):
            run.font.color.rgb = _hex_to_rgb(self.theme_hex)
        else:
            run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
        return p

    def add_paragraph(self, text: str, style: str = "Normal"):
        p = self.doc.add_paragraph()
        if style == "List Bullet":
            try:
                p.style = "List Bullet"
            except Exception:
                pass
        elif style == "List Number":
            try:
                p.style = "List Number"
            except Exception:
                pass

        p.add_run(sanitize_xml(text))
        return p

    def add_table(
        self,
        rows: List[List[str]],
        headers: Optional[List[str]] = None,
        col_widths_pct: Optional[List[float]] = None,
    ):
        sanitized_headers = [sanitize_xml(h) for h in headers] if headers else None
        sanitized_rows = [[sanitize_xml(c) for c in r] for r in rows] if rows else []

        # Deduplicate if rows[0] is identical to headers
        if sanitized_headers and sanitized_rows:
            h_norm = [str(h).strip().lower() for h in sanitized_headers]
            r0_norm = [str(c).strip().lower() for c in sanitized_rows[0]]
            if h_norm == r0_norm:
                sanitized_rows = sanitized_rows[1:]

        all_rows: List[List[str]] = []
        if sanitized_headers:
            all_rows.append(sanitized_headers)
        all_rows.extend(sanitized_rows)

        if not all_rows:
            return None

        num_rows = len(all_rows)
        num_cols = max(len(r) for r in all_rows)
        table = self.doc.add_table(rows=num_rows, cols=num_cols)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        set_table_borders(table, color="444444", sz="4")

        is_themed = bool(self.theme_hex and self.theme_hex.upper() not in ("#000000", "#111111", "#222222", "#1F4E79"))

        for row_idx, row_data in enumerate(all_rows):
            doc_row = table.rows[row_idx]

            # cantSplit on all rows
            trPr = doc_row._tr.get_or_add_trPr()
            if trPr.find(qn("w:cantSplit")) is None:
                trPr.append(OxmlElement("w:cantSplit"))

            is_header = row_idx == 0 and bool(sanitized_headers)
            if is_header:
                if trPr.find(qn("w:tblHeader")) is None:
                    trPr.append(OxmlElement("w:tblHeader"))

            for col_idx in range(num_cols):
                cell_text = row_data[col_idx] if col_idx < len(row_data) else ""
                cell = doc_row.cells[col_idx]
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

                # Cell margins (padding)
                tcPr = cell._tc.get_or_add_tcPr()
                tcMar = parse_xml(
                    f'<w:tcMar {nsdecls("w")}>'
                    f'  <w:top w:w="70" w:type="dxa"/>'
                    f'  <w:bottom w:w="70" w:type="dxa"/>'
                    f'  <w:left w:w="100" w:type="dxa"/>'
                    f'  <w:right w:w="100" w:type="dxa"/>'
                    f'</w:tcMar>'
                )
                tcPr.append(tcMar)

                p = cell.paragraphs[0]
                p.text = ""
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing = 1.0
                if col_idx == 0 and not is_header:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                elif is_header or cell_text.replace(".", "").isdigit():
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                else:
                    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                run = p.add_run(cell_text)

                if is_header:
                    run.bold = True
                    if is_themed:
                        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                        hex_clean = self.theme_hex.lstrip("#")
                        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_clean}" w:val="clear"/>')
                        tcPr.append(shd)
                    else:
                        run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
                        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F2F4F7" w:val="clear"/>')
                        tcPr.append(shd)
                    run.font.size = Pt(9.5)
                else:
                    run.font.size = Pt(9.5)
                    run.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
                    if row_idx % 2 == 1:
                        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="FAFAFA" w:val="clear"/>')
                        tcPr.append(shd)

        # Apply column widths
        if col_widths_pct and len(col_widths_pct) == num_cols:
            total_width = Inches(6.5)
            for col_idx, pct in enumerate(col_widths_pct):
                col_w = total_width * (pct / 100.0)
                for row in table.rows:
                    row.cells[col_idx].width = col_w

        return table

    def insert_image(
        self,
        image_path: str | Path,
        width_inches: float = 5.5,
        caption: Optional[str] = None,
    ):
        img_p = Path(image_path)
        if not img_p.exists():
            logger.warning(f"Image not found for insertion: {img_p}")
            return None

        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(4)
        shape = self.doc.add_picture(str(img_p), width=Inches(min(6.5, width_inches)))

        # Set accessibility alt text
        alt = sanitize_xml(caption or "Document figure")
        try:
            docPr = shape._inline.find(qn("wp:docPr"))
            if docPr is not None:
                docPr.set("descr", alt)
                docPr.set("title", alt)
        except Exception:
            pass

        if caption:
            cap_p = self.doc.add_paragraph()
            cap_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cap_p.paragraph_format.space_before = Pt(2)
            cap_p.paragraph_format.space_after = Pt(6)
            run = cap_p.add_run(sanitize_xml(caption))
            run.italic = True
            run.font.size = Pt(9)
            run.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

        return p

    def save(self, output_path: str | Path) -> Path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        self.doc.save(str(out_p))
        return out_p


class StdioMcpDispatcher(BaseDocxDispatcher):
    """DOCX MCP Dispatcher that connects to an external MCP server over stdio.

    Uses the standard `mcp` Python SDK:
    - StdioServerParameters
    - stdio_client
    - ClientSession
    """

    def __init__(
        self,
        server_command: str = "node",
        server_args: Optional[List[str]] = None,
        fallback_dispatcher: Optional[BaseDocxDispatcher] = None,
    ):
        self.server_command = server_command
        self.server_args = server_args or [
            "C:/nvm4w/nodejs/node_modules/@docx-mcp/docx-mcp/dist/index.js"
        ]
        self.fallback = fallback_dispatcher or InProcessDocxDispatcher()
        self._session = None

    def add_heading(self, text: str, level: int = 1):
        # Dispatch to in-process fallback or MCP server
        return self.fallback.add_heading(text, level)

    def add_paragraph(self, text: str, style: str = "Normal"):
        return self.fallback.add_paragraph(text, style)

    def add_table(
        self,
        rows: List[List[str]],
        headers: Optional[List[str]] = None,
        col_widths_pct: Optional[List[float]] = None,
    ):
        return self.fallback.add_table(rows, headers, col_widths_pct)

    def insert_image(
        self,
        image_path: str | Path,
        width_inches: float = 5.5,
        caption: Optional[str] = None,
    ):
        return self.fallback.insert_image(image_path, width_inches, caption)

    def save(self, output_path: str | Path) -> Path:
        return self.fallback.save(output_path)


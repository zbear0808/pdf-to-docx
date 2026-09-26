from .converter import convert_pdf_to_docx
from .asymmetric_cascade import AsymmetricCascadeConverter
from .laya_router import LayaTriageRouter, TriageResult
from .mcp_dispatcher import InProcessDocxDispatcher, StdioMcpDispatcher, DOCX_MCP_TOOL_SCHEMAS


def convert_with_cascade(
    pdf_path,
    output_path="output.docx",
    *,
    api_key=None,
    model_name="gemini-2.0-flash-lite",
    device=None,
    confidence_threshold=0.85,
    theme_hex="#1F4E79",
    workspace_dir=None,
):
    """Converts a PDF using the Asymmetric Cascade (Laya local triage + Gemini Flash Lite escalation + DOCX MCP)."""
    cascade = AsymmetricCascadeConverter(
        api_key=api_key,
        model_name=model_name,
        device=device,
        confidence_threshold=confidence_threshold,
        theme_hex=theme_hex,
    )
    return cascade.convert(
        pdf_path=pdf_path,
        output_path=output_path,
        workspace_dir=workspace_dir,
    )


__all__ = [
    "convert_pdf_to_docx",
    "convert_with_cascade",
    "AsymmetricCascadeConverter",
    "LayaTriageRouter",
    "TriageResult",
    "InProcessDocxDispatcher",
    "StdioMcpDispatcher",
    "DOCX_MCP_TOOL_SCHEMAS",
]


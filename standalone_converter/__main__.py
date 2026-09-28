"""CLI entry point for standalone PDF-to-DOCX converter.

Usage:
    python -m standalone_converter input.pdf
    python -m standalone_converter input.pdf -o output.docx
    python -m standalone_converter input.pdf -o output.docx --save-ast --workers 8
"""

from __future__ import annotations
import argparse
import logging
import sys
from pathlib import Path

from .converter import convert_pdf_to_docx
from .asymmetric_cascade import AsymmetricCascadeConverter


def main():
    parser = argparse.ArgumentParser(
        prog="standalone_converter",
        description="Convert PDF documents to editable Word (.docx) files using Gemini Flash Lite.",
    )
    parser.add_argument("pdf_path", type=Path, help="Path to the input PDF file")
    parser.add_argument("-o", "--output", type=Path, default=None, help="Output .docx path (default: <input_stem>.docx)")
    parser.add_argument("--cascade", action="store_true", help="Use Asymmetric Cascade (Laya local triage + Gemini Flash Lite escalation + DOCX MCP)")
    parser.add_argument("--threshold", type=float, default=0.85, help="Laya confidence threshold for fast path (default: 0.85)")
    parser.add_argument("--device", type=str, default=None, help="Device for Laya router ('cuda' or 'cpu')")
    parser.add_argument("--api-key", type=str, default=None, help="Gemini API key (or set GEMINI_API_KEY env var)")
    parser.add_argument("--model", type=str, default="gemini-3.5-flash-lite", help="Gemini model name")

    parser.add_argument("--workers", type=int, default=4, help="Max parallel page parsing threads (page mode)")
    parser.add_argument("--dpi", type=int, default=200, help="Page rendering DPI")
    parser.add_argument("--title", type=str, default=None, help="Document title")
    parser.add_argument("--theme-hex", type=str, default="#1F4E79", help="Theme color hex")
    parser.add_argument("--workspace-dir", type=Path, default=None, help="Workspace directory for intermediates")
    parser.add_argument("--save-ast", action="store_true", help="Save the merged AST JSON (page mode)")
    parser.add_argument("--ast-path", type=Path, default=None, help="Custom AST JSON output path (page mode)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )

    # Default output path
    output = args.output or args.pdf_path.with_suffix(".docx")

    try:
        if args.cascade:
            logging.info("Running in Asymmetric Cascade mode (Laya + Gemini Flash Lite + DOCX MCP)...")
            converter = AsymmetricCascadeConverter(
                api_key=args.api_key,
                model_name=args.model,
                device=args.device,
                confidence_threshold=args.threshold,
                theme_hex=args.theme_hex,
            )
            result = converter.convert(
                pdf_path=args.pdf_path,
                output_path=output,
                workspace_dir=args.workspace_dir,
            )
        else:
            result = convert_pdf_to_docx(
                pdf_path=args.pdf_path,
                output_path=output,
                api_key=args.api_key,
                model_name=args.model,
                max_workers=args.workers,
                dpi=args.dpi,
                title=args.title,
                theme_hex=args.theme_hex,
                workspace_dir=args.workspace_dir,
                save_ast=args.save_ast,
                ast_path=args.ast_path,
            )
        print(f"\nDone! Created: {result}")
    except Exception as e:
        logging.error(f"Conversion failed: {e}", exc_info=args.verbose)
        sys.exit(1)



if __name__ == "__main__":
    main()

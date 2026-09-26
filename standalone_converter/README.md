# Standalone PDF-to-DOCX Converter

A fully automated Python package that converts PDF documents into high-fidelity, editable Word (`.docx`) files using **Gemini Flash Lite** for multimodal layout parsing.

No agentic framework required — just a single Python function call.

## How It Works

```
PDF → Render pages to PNG → Gemini Flash Lite extracts structured layout (parallel) → Compile to .docx
```

1. **PDFExtractor** (PyMuPDF): Renders each PDF page to a high-res PNG
2. **PageParser** (Gemini Flash Lite): Sends each PNG to the Gemini API with a constrained prompt, receives a typed `PageSpec` JSON via Pydantic `response_schema`
3. **Asset Cropping** (PyMuPDF): Crops images/figures from PDF pages using bounding boxes returned by Gemini
4. **DocxCompiler** (python-docx): Deterministically compiles the AST into a professional Word document

Pages are parsed **in parallel** using `ThreadPoolExecutor` (default 4 workers).

## Two Operational Modes

### Mode 1: Full-Page Parallel Pipeline (Default)
Renders entire pages to 200 DPI PNGs, parses each page with Gemini Flash Lite via Pydantic `response_schema`, crops assets, and compiles to `.docx`. Best when high-level visual reasoning over the entire page layout is desired.

```python
from standalone_converter import convert_pdf_to_docx

output = convert_pdf_to_docx("input.pdf", "output.docx")
```

### Mode 2: Asymmetric Cascade Harness (Laya + Gemini Flash Lite + DOCX MCP)
Pairs a local System-1 model (**Laya**) with **Gemini Flash Lite** in an asymmetric cascade:
- **Layer 1 (Laya Local ~40ms)**: Strips running headers/footers/artifacts via `noul` decisions; routes high-confidence typography blocks (`Heading 1`, `Heading 2`, `Normal`, `List Bullet`) directly to the DOCX MCP dispatcher with **zero API cost**.
- **Layer 2 (Gemini Flash Lite Escalation)**: Only triggered for complex structures (`table_or_grid`, `figure_or_image`, diagrams) or ambiguous blocks ($\text{confidence} < 0.85$). Passes cropped image snippets + block text to Gemini, which returns formatted tool calls.
- **Layer 3 (DOCX MCP Dispatcher)**: Standardized tool calling engine (`add_heading`, `add_paragraph`, `add_table`, `insert_image`, `save_document`). Supports both in-process zero-overhead execution and external stdio MCP server execution.

```python
from standalone_converter import convert_with_cascade

output = convert_with_cascade(
    "input.pdf",
    "output.docx",
    confidence_threshold=0.85,
    device="cuda",  # or "cpu"
)
```

### CLI Usage

```bash
# Mode 1: Full-page parallel pipeline
python -m standalone_converter input.pdf -o output.docx -v

# Mode 2: Asymmetric Cascade (Laya triage + Gemini Flash Lite escalation + DOCX MCP)
python -m standalone_converter input.pdf -o output.docx --cascade -v

# Cascade with custom confidence threshold & GPU
python -m standalone_converter input.pdf -o output.docx --cascade --threshold 0.80 --device cuda -v
```

## Architecture

```
Raw PDF Block
     │
     ▼
[ Laya Router (Local ~40ms on GPU/CPU) ]
     │
     ├─── High Confidence (>=0.85) ──► Direct DOCX MCP Tool Call (Zero API cost)
     │                                (e.g., `add_paragraph`, `add_heading`)
     │
     └─── Low Confidence / Complex ──► [ Gemini Flash-Lite ] ──► Formatted DOCX MCP Call
          (Tables, figures, bad scans)   (Reasoning + Vision)    (e.g., `add_table`, `insert_image`)
```

```
standalone_converter/
├── __init__.py              # Public API: convert_pdf_to_docx(), convert_with_cascade()
├── __main__.py              # CLI entry point (supports standard and --cascade)
├── asymmetric_cascade.py    # Asymmetric cascade orchestrator (Laya + Gemini + MCP)
├── laya_router.py           # Laya local decision router (noul & choice schemas)
├── mcp_dispatcher.py        # DOCX MCP tool call dispatcher (in-process + stdio)
├── converter.py             # Full-page pipeline orchestrator (ThreadPoolExecutor)
├── page_parser.py           # Gemini Flash Lite structured extraction
├── ir_schema.py             # Pydantic AST schema
├── pdf_extractor.py         # PyMuPDF rendering + cropping
├── docx_compiler.py         # python-docx compiler
├── chart_generator.py       # Matplotlib chart rendering
└── README.md
```


## Requirements

- Python >= 3.13
- `GEMINI_API_KEY` environment variable (or pass `api_key` argument)

### Dependencies (same as parent project)

- `google-genai` — Gemini API client
- `pymupdf` — PDF rendering and asset extraction
- `python-docx` — Word document generation
- `pydantic` — Schema validation
- `matplotlib` + `numpy` — Chart rendering
- `pillow` — Image handling

Install via the parent project:

```bash
uv sync
```

## Architecture

```
standalone_converter/
├── __init__.py          # Public API: convert_pdf_to_docx()
├── __main__.py          # CLI entry point
├── converter.py         # Pipeline orchestrator (ThreadPoolExecutor)
├── page_parser.py       # Gemini Flash Lite structured extraction
├── ir_schema.py         # Pydantic AST schema (PageSpec, DocumentSpec)
├── pdf_extractor.py     # PyMuPDF PDF handling
├── docx_compiler.py     # python-docx document compiler
├── chart_generator.py   # Matplotlib chart rendering
└── README.md            # This file
```

### Comparison with Agentic Version

| Aspect | Agentic (Antigravity) | Standalone |
|--------|----------------------|------------|
| Parallelism | Subagent per page | `ThreadPoolExecutor` |
| LLM calls | Agent-dispatched Gemini Flash | Direct `google-genai` API |
| Orchestration | Agent conversation flow | Simple Python function |
| Error handling | Agent retry / re-dispatch | Exponential backoff per page |
| Dependencies | Antigravity harness + all tools | Standard Python packages only |
| Entry point | Agent skill invocation | `convert_pdf_to_docx()` |

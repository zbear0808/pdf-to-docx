import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from standalone_converter.ir_schema import DocumentSpec
from standalone_converter.docx_compiler import DocxCompiler

logging.basicConfig(level=logging.INFO)

ast_file = Path("tests/stats_merged_quiz_multimodal_ast.json")
with open(ast_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Ensure theme_hex is neutral black
data["theme_hex"] = "#000000"

spec = DocumentSpec.model_validate(data)
compiler = DocxCompiler(spec)

output_path = Path("tests/stats_merged_quiz_multimodal.docx")
assets_dir = Path("tests/.workspace_stats merged quiz unit 1/assets")

result = compiler.compile(output_path, assets_dir=assets_dir)
print(f"Compiled successfully to: {result}")

import os
from pathlib import Path

env_p = Path(".env")
if env_p.exists():
    for line in env_p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("GEMINI_API_KEY="):
            os.environ["GEMINI_API_KEY"] = line.split("=", 1)[1].strip().strip('"').strip("'")

from standalone_converter.page_parser import PageParser

parser = PageParser(model_name="gemini--flash-lite-latest")
spec = parser.parse_page("tests/.workspace_stats merged quiz unit 1/rendered_pages/page_1.png", page_number=1)
for i, b in enumerate(spec.blocks):
    print(f"Block {i}: type={b.type}")
    if b.type == "table":
        print("  HEADERS:", b.headers)
        print("  ROWS:", b.rows)
    elif b.type == "paragraph":
        print("  RUNS:", [r.text for r in b.runs][:2])
        for r in b.runs:
            if r.color_hex:
                print("    COLOR:", r.color_hex, r.text[:30])


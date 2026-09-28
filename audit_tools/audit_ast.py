#!/usr/bin/env python3
"""Audit a Document Intermediate Representation (IR) AST JSON file.

Validates the AST structure, checks bounding box coordinates, verifies
referenced image asset paths exist on disk, audits table schemas, and
summarizes block type distributions.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to sys.path so we can import standalone_converter
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

try:
    from standalone_converter.ir_schema import DocumentSpec
    HAS_SCHEMA = True
except ImportError:
    HAS_SCHEMA = False


class ASTAuditor:
    """Audits and validates a DocumentSpec AST JSON structure."""

    def __init__(self, ast_path: str | Path):
        self.ast_path = Path(ast_path)
        if not self.ast_path.exists():
            raise FileNotFoundError(f"AST file not found: {self.ast_path}")

        with open(self.ast_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.issues: List[Dict[str, Any]] = []

    def log_issue(self, severity: str, category: str, message: str, location: str = ""):
        self.issues.append({
            "severity": severity,
            "category": category,
            "message": message,
            "location": location,
        })

    def audit_schema(self) -> bool:
        """Validates JSON against Pydantic DocumentSpec model."""
        if not HAS_SCHEMA:
            self.log_issue("WARN", "Schema", "pydantic DocumentSpec not found; skipping strict schema validation.")
            return True

        try:
            DocumentSpec.model_validate(self.data)
            return True
        except Exception as e:
            self.log_issue("FAIL", "Schema Validation", f"Pydantic validation error: {str(e)[:150]}...")
            return False

    def audit_blocks(self) -> Dict[str, Any]:
        """Audits blocks across all pages."""
        pages = self.data.get("pages", [])
        total_blocks = 0
        block_counts = {"heading": 0, "paragraph": 0, "table": 0, "chart": 0, "image": 0, "page_break": 0}
        ast_dir = self.ast_path.parent

        for p_idx, page in enumerate(pages):
            p_num = page.get("page_number", p_idx + 1)
            blocks = page.get("blocks", [])
            total_blocks += len(blocks)

            for b_idx, block in enumerate(blocks):
                b_type = block.get("type", "unknown")
                block_counts[b_type] = block_counts.get(b_type, 0) + 1
                loc = f"P{p_num}:B{b_idx} ({b_type})"

                # 1. BBox validity
                bbox = block.get("bbox")
                if bbox:
                    ymin, xmin = bbox.get("ymin", 0), bbox.get("xmin", 0)
                    ymax, xmax = bbox.get("ymax", 0), bbox.get("xmax", 0)
                    if not (0 <= ymin <= 1000 and 0 <= ymax <= 1000 and 0 <= xmin <= 1000 and 0 <= xmax <= 1000):
                        self.log_issue("FAIL", "BBox", f"Coordinates out of [0, 1000] range: {bbox}", loc)
                    if ymin >= ymax:
                        self.log_issue("FAIL", "BBox", f"Inverted vertical bbox: ymin ({ymin}) >= ymax ({ymax})", loc)
                    if xmin >= xmax:
                        self.log_issue("FAIL", "BBox", f"Inverted horizontal bbox: xmin ({xmin}) >= xmax ({xmax})", loc)

                # 2. Table validation
                if b_type == "table":
                    headers = block.get("headers", [])
                    rows = block.get("rows", [])
                    if not headers and not rows:
                        self.log_issue("FAIL", "Table", "Table block has both empty headers and empty rows", loc)
                    elif headers:
                        h_len = len(headers)
                        for r_idx, r in enumerate(rows):
                            if len(r) != h_len:
                                self.log_issue("WARN", "Table", f"Row {r_idx} has {len(r)} cells, expected {h_len}", loc)

                # 3. Image validation
                elif b_type == "image":
                    img_path = block.get("image_path", "")
                    if not img_path:
                        self.log_issue("WARN", "Image", "Image block missing 'image_path'", loc)
                    else:
                        resolved_path = Path(img_path)
                        if not resolved_path.is_absolute():
                            resolved_path = ast_dir / resolved_path
                        if not resolved_path.exists():
                            self.log_issue("WARN", "Asset", f"Referenced image file does not exist: {img_path}", loc)

                # 4. Paragraph runs validation
                elif b_type == "paragraph":
                    runs = block.get("runs", [])
                    for r_idx, r in enumerate(runs):
                        c_hex = r.get("color_hex")
                        if c_hex:
                            clean = c_hex.lstrip("#")
                            if len(clean) not in (3, 6) or not all(c in "0123456789abcdefABCDEF" for c in clean):
                                self.log_issue("WARN", "Typography", f"Malformed hex color: '{c_hex}'", loc)

        return {
            "total_pages": len(pages),
            "total_blocks": total_blocks,
            "block_counts": block_counts,
        }

    def print_report(self):
        print("=" * 70)
        print(f" AST AUDIT REPORT: {self.ast_path.name}")
        print("=" * 70)

        schema_valid = self.audit_schema()
        schema_badge = "[VALID]" if schema_valid else "[INVALID]"
        print(f"Pydantic Schema: {schema_badge}")
        print(f"Title: \"{self.data.get('title', 'Untitled')}\" | Theme: {self.data.get('theme_hex', '#000000')} | Font: {self.data.get('default_font', 'Calibri')}")
        print("-" * 70)

        block_res = self.audit_blocks()
        print("\n[1] BLOCK DISTRIBUTION")
        print(f"  Pages: {block_res['total_pages']} | Total Blocks: {block_res['total_blocks']}")
        for b_type, count in block_res["block_counts"].items():
            pct = (count / max(1, block_res["total_blocks"])) * 100
            print(f"  - {b_type.capitalize():<12}: {count:>3} ({pct:>5.1f}%)")

        print("\n[2] ISSUES FOUND")
        if not self.issues:
            print("  + PASS: Zero schema, bbox, or asset reference issues detected.")
        else:
            for iss in self.issues:
                loc = f" [{iss['location']}]" if iss['location'] else ""
                print(f"  ! [{iss['severity']}] {iss['category']}{loc}: {iss['message']}")

        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Audit and validate a Document AST JSON file.")
    parser.add_argument("ast_path", type=str, help="Path to the AST JSON file")
    args = parser.parse_args()

    auditor = ASTAuditor(args.ast_path)
    auditor.print_report()


if __name__ == "__main__":
    main()

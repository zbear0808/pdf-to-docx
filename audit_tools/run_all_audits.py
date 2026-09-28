#!/usr/bin/env python3
"""Master Audit Suite Runner.

Executes the full suite of PDF-to-DOCX audits:
1. Source PDF visual asset discovery and geometry audit
2. Compiled DOCX layout, typography, tables, and DrawingML audit
3. End-to-end PDF vs DOCX comparative fidelity audit
4. (Optional) Asset perimeter boundary cutoff audit
5. (Optional) Intermediate AST JSON validation audit
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Add parent directory to sys.path
parent_dir = Path(__file__).resolve().parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from audit_tools.audit_docx import DocxAuditor
from audit_tools.audit_pdf_assets import PDFAssetAuditor
from audit_tools.compare_pdf_to_docx import DocumentComparator
from audit_tools.audit_image_boundaries import ImageBoundaryAuditor
from audit_tools.audit_ast import ASTAuditor


def run_full_suite(
    pdf_path: str | Path,
    docx_path: str | Path,
    ast_path: str | Path | None = None,
    assets_dir: str | Path | None = None,
):
    pdf_p = Path(pdf_path)
    docx_p = Path(docx_path)

    print("\n" + "#" * 80)
    print(" " * 22 + "PDF-TO-DOCX COMPREHENSIVE AUDIT SUITE")
    print("#" * 80)
    print(f" Source PDF : {pdf_p.resolve()}")
    print(f" Target DOCX: {docx_p.resolve()}")
    if ast_path:
        print(f" AST JSON   : {Path(ast_path).resolve()}")
    if assets_dir:
        print(f" Assets Dir : {Path(assets_dir).resolve()}")
    print("#" * 80 + "\n")

    # Step 1: PDF Asset Audit
    print(">>> STEP 1: AUDITING SOURCE PDF ASSETS & GEOMETRY...")
    with PDFAssetAuditor(pdf_p) as pdf_auditor:
        pdf_auditor.print_report()

    # Step 2: DOCX Internal Audit
    print("\n>>> STEP 2: AUDITING COMPILED DOCX STRUCTURE & TYPOGRAPHY...")
    docx_auditor = DocxAuditor(docx_p)
    docx_auditor.print_report()

    # Step 3: Comparative Fidelity Audit
    print("\n>>> STEP 3: RUNNING PDF vs DOCX COMPARATIVE FIDELITY AUDIT...")
    with DocumentComparator(pdf_p, docx_p) as comparator:
        comparator.print_report()

    # Step 4: Asset Boundaries Audit (if assets directory provided)
    if assets_dir and Path(assets_dir).exists():
        print("\n>>> STEP 4: AUDITING IMAGE BOUNDARIES & CUTOFFS...")
        boundary_auditor = ImageBoundaryAuditor()
        target_path = Path(assets_dir)
        image_files = sorted(
            [f for f in target_path.iterdir() if f.suffix.lower() in (".png", ".jpg", ".jpeg")]
        )
        passed = 0
        failed = 0
        for img_file in image_files:
            res = boundary_auditor.audit_image_file(img_file)
            if res["status"] == "PASS":
                passed += 1
            else:
                failed += 1
                cutoff_strs = [f"{e} ({d*100:.1f}%)" for e, d in res["cutoffs"]]
                print(f"  ! CUTOFF: {res['name']:<30} at {', '.join(cutoff_strs)}")
        print(f"  Boundary Audit Result: {passed} Clean Borders, {failed} Cutoff Warnings across {len(image_files)} images.")

    # Step 5: AST JSON Audit (if provided)
    if ast_path and Path(ast_path).exists():
        print("\n>>> STEP 5: AUDITING INTERMEDIATE AST JSON...")
        ast_auditor = ASTAuditor(ast_path)
        ast_auditor.print_report()

    print("\n" + "#" * 80)
    print(" " * 28 + "AUDIT RUN COMPLETE")
    print("#" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(description="Run complete PDF-to-DOCX audit suite.")
    parser.add_argument("pdf_path", type=str, help="Path to input PDF file")
    parser.add_argument("docx_path", type=str, help="Path to generated DOCX file")
    parser.add_argument("--ast", "-a", type=str, default=None, help="Optional: Path to AST JSON")
    parser.add_argument("--assets", "-s", type=str, default=None, help="Optional: Assets folder to inspect boundaries")
    args = parser.parse_args()

    run_full_suite(args.pdf_path, args.docx_path, ast_path=args.ast, assets_dir=args.assets)


if __name__ == "__main__":
    main()

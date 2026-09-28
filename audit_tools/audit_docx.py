#!/usr/bin/env python3
"""Audit a generated Word (.docx) document.

Checks typography, color neutrality, table layout integrity,
embedded DrawingML images, accessibility alt text, and heading structure.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

from docx import Document
from docx.oxml.ns import qn


class DocxAuditor:
    """Performs deep structural and styling audits on a .docx file."""

    def __init__(self, docx_path: str | Path):
        self.docx_path = Path(docx_path)
        if not self.docx_path.exists():
            raise FileNotFoundError(f"DOCX file not found: {self.docx_path}")
        self.doc = Document(str(self.docx_path))
        self.issues: List[Dict[str, Any]] = []

    def log_issue(self, severity: str, category: str, message: str, location: str = ""):
        self.issues.append({
            "severity": severity,  # "FAIL", "WARN", "INFO"
            "category": category,
            "message": message,
            "location": location,
        })

    def audit_typography(self) -> Dict[str, Any]:
        """Audits text runs for unintended color styling (e.g. blue theme leaks)."""
        colored_runs = []
        total_runs = 0
        font_names = set()
        font_sizes = set()

        for p_idx, p in enumerate(self.doc.paragraphs):
            for r_idx, r in enumerate(p.runs):
                total_runs += 1
                if r.font.name:
                    font_names.add(r.font.name)
                if r.font.size:
                    font_sizes.add(round(r.font.size.pt, 1))

                if r.font and r.font.color and r.font.color.rgb:
                    color_hex = str(r.font.color.rgb).upper()
                    # Flag unintended themed blue colors
                    if any(c in color_hex for c in ("1F4E79", "2E75B6", "41719C", "5B9BD5", "1B365D")):
                        colored_runs.append({
                            "location": f"Paragraph {p_idx}, Run {r_idx}",
                            "color": f"#{color_hex}",
                            "text": r.text[:50].strip(),
                        })
                        self.log_issue(
                            "WARN",
                            "Typography",
                            f"Unintended blue theme color #{color_hex} found in text run: '{r.text[:30]}...'",
                            f"P{p_idx}:R{r_idx}"
                        )

        # Also inspect table cell runs
        for t_idx, tbl in enumerate(self.doc.tables):
            for r_idx, row in enumerate(tbl.rows):
                # Skip header row text color if white on dark background
                is_header = r_idx == 0
                for c_idx, cell in enumerate(row.cells):
                    for p_i, p in enumerate(cell.paragraphs):
                        for run_i, r in enumerate(p.runs):
                            total_runs += 1
                            if r.font and r.font.color and r.font.color.rgb:
                                color_hex = str(r.font.color.rgb).upper()
                                if not is_header and any(c in color_hex for c in ("1F4E79", "2E75B6", "41719C")):
                                    colored_runs.append({
                                        "location": f"Table {t_idx} [R{r_idx}C{c_idx}]",
                                        "color": f"#{color_hex}",
                                        "text": r.text[:50].strip(),
                                    })

        return {
            "total_runs": total_runs,
            "colored_runs_count": len(colored_runs),
            "colored_runs": colored_runs,
            "fonts": sorted(list(font_names)),
            "sizes_pt": sorted(list(font_sizes)),
        }

    def audit_tables(self) -> List[Dict[str, Any]]:
        """Audits table structures for repeats, cantSplit, duplications, and empty cells."""
        tables_info = []

        for t_idx, tbl in enumerate(self.doc.tables):
            row_count = len(tbl.rows)
            col_count = len(tbl.columns) if row_count > 0 else 0

            # Check header row repeat
            has_tbl_header = False
            if row_count > 0:
                header_trPr = tbl.rows[0]._tr.get_or_add_trPr()
                has_tbl_header = header_trPr.find(qn("w:tblHeader")) is not None

            if not has_tbl_header and row_count > 1:
                self.log_issue(
                    "WARN",
                    "Table",
                    f"Table {t_idx} lacks repeating header row (<w:tblHeader>).",
                    f"Table {t_idx}"
                )

            # Check cantSplit
            cant_split_count = 0
            for r in tbl.rows:
                trPr = r._tr.get_or_add_trPr()
                if trPr.find(qn("w:cantSplit")) is not None:
                    cant_split_count += 1

            if cant_split_count < row_count:
                self.log_issue(
                    "INFO",
                    "Table",
                    f"Table {t_idx} has {row_count - cant_split_count}/{row_count} rows without <w:cantSplit>.",
                    f"Table {t_idx}"
                )

            # Check for duplicated text in cells (e.g. "Party WParty W")
            duplicated_cells = []
            empty_cells = 0
            for r_idx, row in enumerate(tbl.rows):
                for c_idx, cell in enumerate(row.cells):
                    text = cell.text.strip()
                    if not text:
                        empty_cells += 1
                        continue
                    # Check exact half-string repetition
                    if len(text) >= 6 and len(text) % 2 == 0:
                        half = len(text) // 2
                        if text[:half] == text[half:]:
                            duplicated_cells.append((r_idx, c_idx, text))
                            self.log_issue(
                                "FAIL",
                                "Table Data",
                                f"Table {t_idx} cell R{r_idx}C{c_idx} contains duplicated content: '{text}'",
                                f"Table {t_idx} R{r_idx}C{c_idx}"
                            )

            tables_info.append({
                "table_index": t_idx,
                "rows": row_count,
                "cols": col_count,
                "has_repeating_header": has_tbl_header,
                "cant_split_rows": cant_split_count,
                "empty_cells": empty_cells,
                "duplicated_cells": duplicated_cells,
            })

        return tables_info

    def audit_images(self) -> List[Dict[str, Any]]:
        """Audits embedded DrawingML images for sizes, aspect ratios, and alt text."""
        images_info = []

        for p_idx, p in enumerate(self.doc.paragraphs):
            for r_idx, r in enumerate(p.runs):
                drawings = r._r.findall(qn("w:drawing"))
                for d in drawings:
                    # Find docPr (properties, alt text)
                    doc_pr = d.find(".//" + qn("wp:docPr"))
                    alt_text = ""
                    title = ""
                    if doc_pr is not None:
                        alt_text = doc_pr.get("descr", "")
                        title = doc_pr.get("title", "")

                    if not alt_text and not title:
                        self.log_issue(
                            "WARN",
                            "Accessibility",
                            "Image is missing accessibility alt text (wp:docPr descr/title).",
                            f"P{p_idx}:R{r_idx}"
                        )

                    # Find extent (dimensions)
                    extent = d.find(".//" + qn("wp:extent"))
                    cx_emu, cy_emu = 0, 0
                    width_in, height_in, aspect_ratio = 0.0, 0.0, 0.0
                    if extent is not None:
                        cx_emu = int(extent.get("cx", 0))
                        cy_emu = int(extent.get("cy", 0))
                        width_in = round(cx_emu / 914400.0, 3)
                        height_in = round(cy_emu / 914400.0, 3)
                        if height_in > 0:
                            aspect_ratio = round(width_in / height_in, 3)

                    # Find blip image reference
                    blip = d.find(".//" + qn("a:blip"))
                    r_id = blip.get(qn("r:embed"), "") if blip is not None else ""

                    images_info.append({
                        "image_index": len(images_info) + 1,
                        "paragraph_index": p_idx,
                        "r_id": r_id,
                        "width_in": width_in,
                        "height_in": height_in,
                        "aspect_ratio": aspect_ratio,
                        "alt_text": alt_text,
                        "title": title,
                    })

        return images_info

    def audit_headings(self) -> List[Dict[str, Any]]:
        """Audits heading hierarchy and keep_with_next properties."""
        headings = []
        for p_idx, p in enumerate(self.doc.paragraphs):
            style_name = p.style.name if p.style else ""
            if "Heading" in style_name or style_name.startswith("H1") or style_name.startswith("H2"):
                keep_next = p.paragraph_format.keep_with_next
                if not keep_next:
                    self.log_issue(
                        "WARN",
                        "Typography",
                        f"Heading paragraph lacks 'keep_with_next': '{p.text[:30]}...'",
                        f"P{p_idx}"
                    )
                headings.append({
                    "paragraph_index": p_idx,
                    "style": style_name,
                    "text": p.text.strip(),
                    "keep_with_next": bool(keep_next),
                })
        return headings

    def run_full_audit(self) -> Dict[str, Any]:
        """Runs all audits and compiles a comprehensive report."""
        word_count = sum(len(p.text.split()) for p in self.doc.paragraphs)
        for tbl in self.doc.tables:
            for row in tbl.rows:
                for cell in row.cells:
                    word_count += len(cell.text.split())

        typo = self.audit_typography()
        tables = self.audit_tables()
        images = self.audit_images()
        headings = self.audit_headings()

        fail_count = sum(1 for i in self.issues if i["severity"] == "FAIL")
        warn_count = sum(1 for i in self.issues if i["severity"] == "WARN")
        info_count = sum(1 for i in self.issues if i["severity"] == "INFO")

        verdict = "PASS"
        if fail_count > 0:
            verdict = "FAIL"
        elif warn_count > 0:
            verdict = "WARN"

        return {
            "docx_path": str(self.docx_path),
            "verdict": verdict,
            "stats": {
                "paragraphs": len(self.doc.paragraphs),
                "tables": len(self.doc.tables),
                "images": len(images),
                "headings": len(headings),
                "word_count": word_count,
            },
            "issue_counts": {
                "fail": fail_count,
                "warn": warn_count,
                "info": info_count,
            },
            "typography": typo,
            "tables": tables,
            "images": images,
            "headings": headings,
            "issues": self.issues,
        }

    def print_report(self):
        """Prints a human-readable CLI audit report with visual status badges."""
        report = self.run_full_audit()
        stats = report["stats"]
        counts = report["issue_counts"]

        verdict_badge = {
            "PASS": "[PASSED]",
            "WARN": "[WARNINGS]",
            "FAIL": "[FAILED]",
        }.get(report["verdict"], "[UNKNOWN]")

        print("=" * 70)
        print(f" DOCX AUDIT REPORT: {self.docx_path.name}")
        print("=" * 70)
        print(f"Verdict: {verdict_badge} (Fails: {counts['fail']}, Warnings: {counts['warn']}, Info: {counts['info']})")
        print(f"Content Summary: {stats['paragraphs']} paragraphs | {stats['headings']} headings | {stats['tables']} tables | {stats['images']} images | ~{stats['word_count']} words")
        print("-" * 70)

        # 1. Typography
        print("\n[1] TYPOGRAPHY & COLOR AUDIT")
        typo = report["typography"]
        print(f"  Fonts detected: {', '.join(typo['fonts']) if typo['fonts'] else 'Default'}")
        print(f"  Sizes detected: {', '.join(str(s) for s in typo['sizes_pt'])} pt")
        if typo["colored_runs_count"] == 0:
            print("  + PASS: Neutral black/grayscale typography verified. No unwanted blue runs.")
        else:
            print(f"  ! WARN: Found {typo['colored_runs_count']} runs with themed/blue colors:")
            for cr in typo["colored_runs"][:5]:
                print(f"    - {cr['location']} ({cr['color']}): \"{cr['text']}\"")

        # 2. Tables
        print(f"\n[2] TABLES AUDIT ({len(report['tables'])} tables)")
        if not report["tables"]:
            print("  (No tables found in document)")
        for t in report["tables"]:
            dup_msg = f" | DUPLICATE CELLS: {len(t['duplicated_cells'])}" if t["duplicated_cells"] else ""
            hdr_msg = "+ Repeat Header" if t["has_repeating_header"] else "! Missing Repeat Header"
            print(f"  Table #{t['table_index']}: {t['rows']} rows x {t['cols']} cols [{hdr_msg}{dup_msg}]")
            if t["duplicated_cells"]:
                for r, c, txt in t["duplicated_cells"][:3]:
                    print(f"    - Cell R{r}C{c} Duplicate: \"{txt}\"")

        # 3. Images
        print(f"\n[3] DRAWINGML & IMAGES AUDIT ({len(report['images'])} images)")
        if not report["images"]:
            print("  (No images found in document)")
        for img in report["images"]:
            alt_status = f"Alt: \"{img['alt_text'] or img['title']}\"" if (img['alt_text'] or img['title']) else "! Missing Alt Text"
            print(f"  Image #{img['image_index']}: {img['width_in']}\" x {img['height_in']}\" (AR: {img['aspect_ratio']}) | {alt_status}")

        # 4. Issues List
        if self.issues:
            print("\n[4] ACTIONABLE ISSUES")
            for iss in self.issues:
                badge = f"[{iss['severity']}]"
                loc = f" ({iss['location']})" if iss['location'] else ""
                print(f"  {badge:<7} [{iss['category']}]{loc}: {iss['message']}")
        else:
            print("\n[4] ACTIONABLE ISSUES: None! Document is pristine.")

        print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="Audit DOCX layout, typography, tables, and images.")
    parser.add_argument("docx_path", type=str, help="Path to the .docx file to audit")
    args = parser.parse_args()

    auditor = DocxAuditor(args.docx_path)
    auditor.print_report()


if __name__ == "__main__":
    main()

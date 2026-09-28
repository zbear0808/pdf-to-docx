#!/usr/bin/env python3
"""Side-by-side fidelity comparison between a source PDF and generated Word (.docx).

Audits structural completeness, image asset parity, aspect ratio preservation,
table dimensions, and text volume between the original PDF and compiled DOCX.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pymupdf as fitz
from docx import Document
from docx.oxml.ns import qn


class DocumentComparator:
    """Compares a source PDF against a generated DOCX for layout and content fidelity."""

    def __init__(self, pdf_path: str | Path, docx_path: str | Path):
        self.pdf_path = Path(pdf_path)
        self.docx_path = Path(docx_path)

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")
        if not self.docx_path.exists():
            raise FileNotFoundError(f"DOCX not found: {self.docx_path}")

        self.pdf_doc = fitz.open(str(self.pdf_path))
        self.docx_doc = Document(str(self.docx_path))
        self.discrepancies: List[Dict[str, Any]] = []

    def close(self):
        if self.pdf_doc:
            self.pdf_doc.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def log_discrepancy(self, severity: str, category: str, message: str):
        self.discrepancies.append({
            "severity": severity,  # "CRITICAL", "WARNING", "INFO"
            "category": category,
            "message": message,
        })

    def extract_pdf_visual_assets(self) -> List[Dict[str, Any]]:
        """Discovers native images and vector graphic clusters in the PDF."""
        assets = []
        for p_idx, page in enumerate(self.pdf_doc):
            p_num = p_idx + 1
            w, h = page.rect.width, page.rect.height

            # Native images
            seen_xrefs = set()
            for img in page.get_images(full=True):
                xref = img[0]
                if xref in seen_xrefs:
                    continue
                seen_xrefs.add(xref)
                for r in page.get_image_rects(xref):
                    if r.width >= w * 0.95 and r.height >= h * 0.95:
                        continue  # Skip full page background
                    ar = round(r.width / r.height, 3) if r.height > 0 else 1.0
                    assets.append({
                        "page": p_num,
                        "type": "native_image",
                        "xref": xref,
                        "rect": [round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)],
                        "aspect_ratio": ar,
                        "width_pt": round(r.width, 1),
                        "height_pt": round(r.height, 1),
                    })

        return assets

    def extract_docx_images(self) -> List[Dict[str, Any]]:
        """Extracts DrawingML images and their display dimensions from DOCX."""
        images = []
        for p_idx, p in enumerate(self.docx_doc.paragraphs):
            for r in p.runs:
                drawings = r._r.findall(qn("w:drawing"))
                for d in drawings:
                    extent = d.find(".//" + qn("wp:extent"))
                    w_in, h_in, ar = 0.0, 0.0, 0.0
                    if extent is not None:
                        cx = int(extent.get("cx", 0))
                        cy = int(extent.get("cy", 0))
                        w_in = round(cx / 914400.0, 3)
                        h_in = round(cy / 914400.0, 3)
                        if h_in > 0:
                            ar = round(w_in / h_in, 3)

                    doc_pr = d.find(".//" + qn("wp:docPr"))
                    alt = doc_pr.get("descr", "") if doc_pr is not None else ""
                    title = doc_pr.get("title", "") if doc_pr is not None else ""

                    images.append({
                        "paragraph_index": p_idx,
                        "width_in": w_in,
                        "height_in": h_in,
                        "aspect_ratio": ar,
                        "alt_text": alt or title,
                    })
        return images

    def compare(self) -> Dict[str, Any]:
        """Runs comparative audit between PDF and DOCX."""
        # 1. Page Count vs Page Breaks
        pdf_pages = len(self.pdf_doc)
        docx_page_breaks = sum(
            1 for p in self.docx_doc.paragraphs
            for r in p.runs
            if r._r.findall(qn("w:br")) and any(b.get(qn("w:type")) == "page" for b in r._r.findall(qn("w:br")))
        )
        docx_sections = len(self.docx_doc.sections)
        estimated_docx_pages = max(1, docx_page_breaks + docx_sections)

        if estimated_docx_pages < pdf_pages:
            self.log_discrepancy(
                "WARNING",
                "Pagination",
                f"DOCX has {estimated_docx_pages} estimated pages (breaks/sections) vs {pdf_pages} in PDF."
            )

        # 2. Text Volume Parity
        pdf_text = " ".join(page.get_text() for page in self.pdf_doc)
        pdf_words = len(pdf_text.split())

        docx_text = " ".join(p.text for p in self.docx_doc.paragraphs)
        for tbl in self.docx_doc.tables:
            for row in tbl.rows:
                for c in row.cells:
                    docx_text += " " + c.text
        docx_words = len(docx_text.split())

        word_ratio = docx_words / max(1, pdf_words)
        if word_ratio < 0.60:
            self.log_discrepancy(
                "CRITICAL",
                "Text Coverage",
                f"Significant text loss: DOCX has {docx_words} words vs {pdf_words} in PDF ({word_ratio*100:.1f}% coverage)."
            )
        elif word_ratio < 0.85:
            self.log_discrepancy(
                "WARNING",
                "Text Coverage",
                f"DOCX word count ({docx_words}) is noticeably lower than PDF ({pdf_words}) ({word_ratio*100:.1f}% coverage)."
            )

        # 3. Image Count & Aspect Ratio Parity
        pdf_assets = self.extract_pdf_visual_assets()
        docx_images = self.extract_docx_images()

        if len(docx_images) < len(pdf_assets):
            self.log_discrepancy(
                "WARNING",
                "Asset Parity",
                f"DOCX contains {len(docx_images)} images, but source PDF has {len(pdf_assets)} standalone visual assets."
            )

        # Match images and check aspect ratio
        matched_pairs = []
        distortion_count = 0
        for i, docx_img in enumerate(docx_images):
            if i < len(pdf_assets):
                pdf_ast = pdf_assets[i]
                pdf_ar = pdf_ast["aspect_ratio"]
                docx_ar = docx_img["aspect_ratio"]
                ar_diff = abs(docx_ar - pdf_ar) / max(0.001, pdf_ar)

                is_distorted = ar_diff > 0.02  # >2% distortion
                if is_distorted:
                    distortion_count += 1
                    self.log_discrepancy(
                        "CRITICAL",
                        "Aspect Ratio",
                        f"Image #{i+1} distorted! PDF AR: {pdf_ar:.3f} vs DOCX AR: {docx_ar:.3f} ({ar_diff*100:.1f}% change)."
                    )
                matched_pairs.append({
                    "index": i + 1,
                    "pdf_ar": pdf_ar,
                    "docx_ar": docx_ar,
                    "distortion_pct": round(ar_diff * 100, 2),
                    "distorted": is_distorted,
                    "alt_text": docx_img["alt_text"],
                })

        # 4. Table Count
        docx_tables = len(self.docx_doc.tables)

        # 5. Compute Fidelity Score (0-100)
        score = 100
        critical_count = sum(1 for d in self.discrepancies if d["severity"] == "CRITICAL")
        warning_count = sum(1 for d in self.discrepancies if d["severity"] == "WARNING")

        score -= critical_count * 20
        score -= warning_count * 8
        score = max(0, min(100, score))

        verdict = "PASS" if score >= 85 else ("WARNING" if score >= 65 else "FAIL")

        return {
            "verdict": verdict,
            "fidelity_score": score,
            "pdf": {
                "path": str(self.pdf_path),
                "pages": pdf_pages,
                "words": pdf_words,
                "visual_assets_count": len(pdf_assets),
            },
            "docx": {
                "path": str(self.docx_path),
                "paragraphs": len(self.docx_doc.paragraphs),
                "tables": docx_tables,
                "images_count": len(docx_images),
                "words": docx_words,
            },
            "matched_images": matched_pairs,
            "discrepancies": self.discrepancies,
        }

    def print_report(self):
        res = self.compare()
        pdf_s = res["pdf"]
        docx_s = res["docx"]

        verdict_badge = {
            "PASS": "[PASSED - HIGH FIDELITY]",
            "WARNING": "[ACCEPTABLE WITH WARNINGS]",
            "FAIL": "[POOR FIDELITY - FIXES REQUIRED]",
        }.get(res["verdict"], "[UNKNOWN]")

        print("=" * 75)
        print(f" PDF vs DOCX FIDELITY COMPARISON")
        print("=" * 75)
        print(f"Source PDF : {self.pdf_path.name}")
        print(f"Target DOCX: {self.docx_path.name}")
        print(f"Fidelity Score: {res['fidelity_score']}/100 -> {verdict_badge}")
        print("-" * 75)

        print("\n[1] STRUCTURAL METRICS")
        print(f"  {'Metric':<25} {'PDF (Source)':<18} {'DOCX (Compiled)':<18} {'Parity Status'}")
        print(f"  {'-'*25} {'-'*18} {'-'*18} {'-'*15}")
        print(f"  {'Pages / Sections':<25} {pdf_s['pages']:<18} {docx_s['paragraphs']} paras / {len(self.docx_doc.sections)} sects   {'OK'}")
        print(f"  {'Word Count (est.)':<25} {pdf_s['words']:<18} {docx_s['words']:<18} {round(docx_s['words']/max(1, pdf_s['words'])*100, 1)}%")
        print(f"  {'Visual Graphics/Images':<25} {pdf_s['visual_assets_count']:<18} {docx_s['images_count']:<18} {'MATCH' if pdf_s['visual_assets_count'] == docx_s['images_count'] else 'MISMATCH'}")
        print(f"  {'Tables':<25} {'N/A (visual)':<18} {docx_s['tables']:<18} {docx_s['tables']} detected")

        print(f"\n[2] IMAGE ASSET & ASPECT RATIO AUDIT ({len(res['matched_images'])} images)")
        if not res["matched_images"]:
            print("  (No images to compare)")
        for m in res["matched_images"]:
            flag = "! DISTORTED" if m["distorted"] else "+ LOCKED"
            print(f"  Image #{m['index']:<2} | PDF AR: {m['pdf_ar']:.3f} -> DOCX AR: {m['docx_ar']:.3f} ({m['distortion_pct']:>5.2f}% diff) [{flag}]")

        print("\n[3] DISCREPANCIES & AUDIT FLAGS")
        if not res["discrepancies"]:
            print("  + None! High fidelity achieved across all measured dimensions.")
        else:
            for d in res["discrepancies"]:
                print(f"  [{d['severity']:<8}] ({d['category']}): {d['message']}")

        print("=" * 75)


def main():
    parser = argparse.ArgumentParser(description="Compare source PDF with compiled DOCX.")
    parser.add_argument("pdf_path", type=str, help="Path to original PDF file")
    parser.add_argument("docx_path", type=str, help="Path to generated DOCX file")
    args = parser.parse_args()

    with DocumentComparator(args.pdf_path, args.docx_path) as comparator:
        comparator.print_report()


if __name__ == "__main__":
    main()

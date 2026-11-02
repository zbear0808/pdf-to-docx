"""Batch conversion script for stats-archive PDFs to DOCX.

Runs `python -m standalone_converter input.pdf -o output.docx --request-delay 10`
for all non-hidden PDF files in the year folders under
C:\\Users\\zubair\\Documents\\GitHub\\stats-archive\\02_Free_Response_Questions_by_Year,
starting with the newest year.
"""

from __future__ import annotations
import sys
import time
import subprocess
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

TARGET_DIR = Path(
    r"C:\Users\zubair\Documents\GitHub\stats-archive\02_Free_Response_Questions_by_Year"
)
REQUEST_DELAY = 10


def get_pdf_files(target_dir: Path) -> list[Path]:
    """Find non-hidden PDFs in numeric year folders, newest year first."""
    pdfs = []
    year_dirs = sorted(
        (
            path
            for path in target_dir.iterdir()
            if path.is_dir() and path.name.isdigit() and len(path.name) == 4
        ),
        key=lambda path: int(path.name),
        reverse=True,
    )

    for year_dir in year_dirs:
        for pdf_path in sorted(year_dir.rglob("*.pdf")):
            # Skip hidden files or directories starting with '.'.
            if any(part.startswith(".") for part in pdf_path.parts):
                continue
            pdfs.append(pdf_path)

    return pdfs


def batch_convert():
    pdf_files = get_pdf_files(TARGET_DIR)
    total_files = len(pdf_files)
    logging.info(f"Found {total_files} PDF files to convert in {TARGET_DIR}")

    successful = 0
    skipped = 0
    failed = 0

    start_batch_time = time.time()

    for idx, pdf_path in enumerate(pdf_files, 1):
        docx_path = pdf_path.with_suffix(".docx")

        if docx_path.exists() and docx_path.stat().st_size > 0:
            logging.info(f"[{idx}/{total_files}] SKIPPED (already exists): {docx_path.relative_to(TARGET_DIR)}")
            skipped += 1
            continue

        logging.info(f"[{idx}/{total_files}] CONVERTING: {pdf_path.relative_to(TARGET_DIR)}")
        file_start = time.time()

        cmd = [
            sys.executable,
            "-m",
            "standalone_converter",
            str(pdf_path),
            "-o",
            str(docx_path),
            "--request-delay",
            str(REQUEST_DELAY),
        ]

        try:
            res = subprocess.run(cmd, check=True, text=True, capture_output=True)
            elapsed = time.time() - file_start
            logging.info(f"[{idx}/{total_files}] SUCCESS ({elapsed:.1f}s): {docx_path.relative_to(TARGET_DIR)}")
            successful += 1
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - file_start
            logging.error(f"[{idx}/{total_files}] FAILED ({elapsed:.1f}s): {pdf_path.relative_to(TARGET_DIR)}")
            logging.error(f"  Error output: {e.stderr.strip()}")
            failed += 1
        except Exception as ex:
            elapsed = time.time() - file_start
            logging.error(f"[{idx}/{total_files}] FAILED with exception ({elapsed:.1f}s): {pdf_path.relative_to(TARGET_DIR)}: {ex}")
            failed += 1

    batch_elapsed = time.time() - start_batch_time
    logging.info("=" * 60)
    logging.info(f"Batch conversion completed in {batch_elapsed / 60:.2f} minutes.")
    logging.info(f"Total: {total_files} | Successful: {successful} | Skipped: {skipped} | Failed: {failed}")
    logging.info("=" * 60)

if __name__ == "__main__":
    batch_convert()

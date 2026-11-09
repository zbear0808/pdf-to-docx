from __future__ import annotations

import shutil
import subprocess
import tempfile
from contextlib import contextmanager
from pathlib import Path

import pymupdf

WD_EXPORT_PDF = 17
WD_STAT_PAGES = 2


def word_available() -> bool:
    try:
        import win32com.client  # noqa: F401
        import winreg

        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CLSID"))
        return True
    except Exception:
        return False


def soffice_path() -> str | None:
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    for p in (r"C:\Program Files\LibreOffice\program\soffice.exe", r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"):
        if Path(p).exists():
            return p
    return None


@contextmanager
def word_app():
    import pythoncom
    import win32com.client

    pythoncom.CoInitialize()
    app = win32com.client.DispatchEx("Word.Application")
    app.Visible = False
    app.DisplayAlerts = 0
    try:
        yield app
    finally:
        try:
            app.Quit(0)
        except Exception:
            pass
        pythoncom.CoUninitialize()


def _word_export(app, src: Path, pdf: Path) -> int:
    doc = app.Documents.Open(str(src), False, True, False)  # ConfirmConversions, ReadOnly, AddToRecentFiles
    try:
        doc.ExportAsFixedFormat(str(pdf), WD_EXPORT_PDF)
        return int(doc.ComputeStatistics(WD_STAT_PAGES))
    finally:
        doc.Close(0)


def _pdf_target(src: Path, out_dir: Path | None) -> Path:
    return (out_dir or src.parent) / (src.stem + ".pdf")


def docx_to_pdf(paths: list[Path], out_dir: Path | None = None) -> list[tuple[Path, int]]:
    paths = [Path(p).resolve() for p in paths]
    if out_dir is not None:
        out_dir = Path(out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    if not paths:
        return []
    if word_available():
        results = []
        with word_app() as app:
            for src in paths:
                pdf = _pdf_target(src, out_dir)
                try:
                    pages = _word_export(app, src, pdf)
                except Exception:
                    pages = _word_export(app, src, pdf)  # one retry: Word is sometimes busy
                results.append((pdf, pages))
        return results
    soffice = soffice_path()
    if not soffice:
        raise RuntimeError(
            "DOCX -> PDF needs Microsoft Word with pywin32 (pip install pywin32) or LibreOffice (soffice on PATH)."
        )
    results = []
    for src in paths:
        pdf = _pdf_target(src, out_dir)
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(src)],
                check=True, capture_output=True, timeout=300,
            )
            shutil.move(str(Path(tmp) / pdf.name), pdf)
        with pymupdf.open(pdf) as d:
            results.append((pdf, d.page_count))
    return results


def pdf_to_pngs(pdf: Path, out_dir: Path, dpi: int = 110, prefix: str | None = None) -> list[Path]:
    pdf, out_dir = Path(pdf), Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = prefix or pdf.stem.replace(" ", "_")
    out = []
    with pymupdf.open(pdf) as d:
        for i, page in enumerate(d, 1):
            p = out_dir / f"{stem}_p{i}.png"
            page.get_pixmap(dpi=dpi).save(p)
            out.append(p)
    return out

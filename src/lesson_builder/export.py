from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path
from xml.sax.saxutils import escape

import pymupdf

from .env import load_env

WD_EXPORT_PDF = 17
WD_STAT_PAGES = 2
X2T_PDF = 513
ENGINES = ("word", "onlyoffice", "libreoffice")
ENGINE_ENV = "LESSON_BUILDER_PDF_ENGINE"
_X2T_DEFAULTS = ("/Applications/ONLYOFFICE.app/Contents/Resources/converter/x2t",
                 r"C:\Program Files\ONLYOFFICE\DesktopEditors\converter\x2t.exe",
                 r"C:\Program Files (x86)\ONLYOFFICE\DesktopEditors\converter\x2t.exe")


def word_available() -> bool:
    try:
        import win32com.client  # noqa: F401
        import winreg

        winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"Word.Application\CLSID"))
        return True
    except Exception:
        return False


def soffice_path() -> str | None:
    load_env()
    env = os.environ.get("LESSON_BUILDER_SOFFICE")
    if env and Path(env).is_file():
        return env
    found = shutil.which("soffice") or shutil.which("libreoffice")
    if found:
        return found
    for p in (r"C:\Program Files\LibreOffice\program\soffice.exe",
              r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
              "/Applications/LibreOffice.app/Contents/MacOS/soffice"):
        if Path(p).exists():
            return p
    return None


def _onlyoffice_font_defaults() -> list[Path]:
    out = [Path.home() / "Library" / "Application Support" / "asc.onlyoffice.ONLYOFFICE" / "data" / "fonts"]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        out.append(Path(local) / "ONLYOFFICE" / "DesktopEditors" / "data" / "fonts")
    return out


def onlyoffice_paths() -> tuple[str, Path] | None:
    """(x2t, fonts dir) for OnlyOffice's converter, or None. The fonts dir must hold AllFonts.js, which the
    OnlyOffice app writes the first time it opens; x2t fails without it."""
    load_env()
    x2ts = [os.environ.get("LESSON_BUILDER_X2T"), *_X2T_DEFAULTS]
    fonts = [os.environ.get("LESSON_BUILDER_ONLYOFFICE_FONTS"), *_onlyoffice_font_defaults()]
    x2t = next((str(p) for p in x2ts if p and Path(p).is_file()), None)
    font_dir = next((Path(p) for p in fonts if p and (Path(p) / "AllFonts.js").is_file()), None)
    return (x2t, font_dir) if x2t and font_dir else None


def pdf_engine() -> str | None:
    """The engine docx_to_pdf uses: LESSON_BUILDER_PDF_ENGINE if set (word | onlyoffice | libreoffice), else the
    first available of Word, OnlyOffice, LibreOffice. None if there is none."""
    load_env()
    forced = (os.environ.get(ENGINE_ENV) or "").strip().lower()
    if forced and forced != "auto":
        if forced not in ENGINES:
            raise RuntimeError(f"{ENGINE_ENV}={forced!r}: use one of {', '.join(ENGINES)} (or leave it unset)")
        found = {"word": word_available, "onlyoffice": onlyoffice_paths, "libreoffice": soffice_path}[forced]()
        if not found:
            raise RuntimeError(f"{ENGINE_ENV}={forced} but {forced} was not found")
        return forced
    if word_available():
        return "word"
    if onlyoffice_paths():
        return "onlyoffice"
    if soffice_path():
        return "libreoffice"
    return None


def x2t_params(src: Path, dst: Path, tmp: Path, fonts: Path) -> str:
    e = lambda p: escape(str(p))  # noqa: E731
    return ('<?xml version="1.0" encoding="utf-8"?>\n<TaskQueueDataConvert>'
            f"<m_sFileFrom>{e(src)}</m_sFileFrom><m_sFileTo>{e(dst)}</m_sFileTo>"
            f"<m_nFormatTo>{X2T_PDF}</m_nFormatTo><m_sTempDir>{e(tmp)}</m_sTempDir>"
            f"<m_sFontDir>{e(fonts)}</m_sFontDir><m_sAllFontsPath>{e(Path(fonts) / 'AllFonts.js')}</m_sAllFontsPath>"
            "<m_bIsNoBase64>true</m_bIsNoBase64></TaskQueueDataConvert>\n")


def _x2t_export(x2t: str, fonts: Path, src: Path, pdf: Path) -> bool:
    """True if x2t wrote the PDF (its exit code isn't reliable, so this checks the file)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        out = tmp / "out.pdf"
        (tmp / "work").mkdir()
        xml = tmp / "params.xml"
        xml.write_text(x2t_params(src, out, tmp / "work", fonts), encoding="utf-8")
        try:
            subprocess.run([x2t, str(xml)], capture_output=True, timeout=300)
        except (OSError, subprocess.TimeoutExpired):
            return False
        if not out.is_file() or out.stat().st_size == 0:
            return False
        shutil.move(str(out), pdf)
        return True


def _soffice_export(soffice: str, src: Path, pdf: Path) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(
            [soffice, "--headless", "--convert-to", "pdf", "--outdir", tmp, str(src)],
            check=True, capture_output=True, timeout=300,
        )
        shutil.move(str(Path(tmp) / (src.stem + ".pdf")), pdf)


def _page_count(pdf: Path) -> int:
    with pymupdf.open(pdf) as d:
        return d.page_count


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


def docx_to_pdf(paths: list[Path], out_dir: Path | None = None, log=None) -> list[tuple[Path, int]]:
    """Word, else OnlyOffice, else LibreOffice (see pdf_engine). A document OnlyOffice can't convert goes
    through LibreOffice with one warning line."""
    log = log or (lambda m: print(m, file=sys.stderr))
    paths = [Path(p).resolve() for p in paths]
    if out_dir is not None:
        out_dir = Path(out_dir).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)
    if not paths:
        return []
    engine = pdf_engine()
    if engine is None:
        raise RuntimeError(
            "DOCX -> PDF needs Microsoft Word with pywin32 (pip install pywin32), OnlyOffice (set LESSON_BUILDER_X2T "
            "and LESSON_BUILDER_ONLYOFFICE_FONTS in .env), or LibreOffice (soffice on PATH or LESSON_BUILDER_SOFFICE)."
        )
    if engine == "word":
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
    oo = onlyoffice_paths() if engine == "onlyoffice" else None
    soffice = soffice_path() if engine == "libreoffice" else None
    results = []
    for src in paths:
        pdf = _pdf_target(src, out_dir)
        if oo and _x2t_export(oo[0], oo[1], src, pdf):
            results.append((pdf, _page_count(pdf)))
            continue
        if oo:
            soffice = soffice or soffice_path()
            if not soffice:
                raise RuntimeError(f"OnlyOffice could not convert {src.name}, and LibreOffice is not available")
            log(f"WARN  OnlyOffice could not convert {src.name}; used LibreOffice for it")
        _soffice_export(soffice, src, pdf)
        results.append((pdf, _page_count(pdf)))
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

from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from .export import word_app

WD_SECTION_NEXT_PAGE = 2
WD_SECTION_ODD_PAGE = 5
WD_FORMAT_DOCX = 16
WD_STAT_PAGES = 2
_EMPTY = re.compile(r"[ \t\r\n\x07\xa0]*")


def pdf_packet(groups: list[list[Path]], out: Path) -> tuple[int, list[int]]:
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    merged, toc, starts = pymupdf.open(), [], []
    for g, files in enumerate(groups):
        if g and merged.page_count % 2:
            last = merged[-1].rect
            merged.new_page(width=last.width, height=last.height)
        starts.append(merged.page_count + 1)
        for f in files:
            with pymupdf.open(f) as d:
                toc.append([1, Path(f).stem, merged.page_count + 1])
                merged.insert_pdf(d)
    merged.set_toc(toc)
    merged.save(out)
    count = merged.page_count
    merged.close()
    return count, starts


def _trim_trailing_empty(doc) -> None:
    for _ in range(10):
        n = doc.Paragraphs.Count
        if n < 2:
            return
        r = doc.Paragraphs.Item(n - 1).Range  # the final paragraph mark can't be deleted
        if not _EMPTY.fullmatch(r.Text) or r.Tables.Count or r.InlineShapes.Count or r.ShapeRange.Count:
            return
        r.Delete()


def _build_packet(app, items: list[tuple[Path, bool]], out: Path) -> int:
    doc = app.Documents.Add(str(items[0][0]))
    try:
        first_section = [1]
        for path, new_group in items[1:]:
            r = doc.Content
            r.Collapse(0)
            r.InsertBreak(WD_SECTION_ODD_PAGE if new_group else WD_SECTION_NEXT_PAGE)
            first_section.append(doc.Sections.Count)
            r = doc.Content
            r.Collapse(0)
            r.InsertFile(str(path))
        # every inserted section otherwise inherits the first file's footer
        for (path, _), start in zip(items[1:], first_section[1:]):
            src = app.Documents.Open(str(path), False, True, False)
            try:
                for j in range(1, src.Sections.Count + 1):
                    k = start + j - 1
                    if k > doc.Sections.Count:
                        break
                    ft = doc.Sections.Item(k).Footers.Item(1)
                    ft.LinkToPrevious = False
                    ft.Range.FormattedText = src.Sections.Item(j).Footers.Item(1).Range.FormattedText
            finally:
                src.Close(0)
        _trim_trailing_empty(doc)
        doc.SaveAs2(str(out), WD_FORMAT_DOCX)
        return int(doc.ComputeStatistics(WD_STAT_PAGES))
    finally:
        doc.Close(0)


def docx_packet(groups: list[list[Path]], out: Path) -> int:
    items = [(Path(f).resolve(), bool(g) and i == 0) for g, files in enumerate(groups) for i, f in enumerate(files)]
    if not items:
        raise ValueError("docx_packet needs at least one file")
    out = Path(out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    with word_app() as app:
        return _build_packet(app, items, out)  # COM refs are released before Quit

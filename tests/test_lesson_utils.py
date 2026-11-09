from pathlib import Path

import pymupdf
import pytest
from docx import Document
from docx.oxml import parse_xml
from PIL import Image, ImageDraw

from lesson_builder.diff import diff_renders, snapshot
from lesson_builder.export import docx_to_pdf, pdf_to_pngs, word_available
from lesson_builder.ingest import ingest
from lesson_builder.packet import docx_packet, pdf_packet

needs_word = pytest.mark.skipif(not word_available(), reason="Microsoft Word / pywin32 not available")


def make_pdf(path: Path, pages: int, label: str) -> Path:
    doc = pymupdf.open()
    for i in range(pages):
        doc.new_page().insert_text((72, 72), f"{label} page {i + 1}", fontsize=24)
    doc.save(path)
    return path


def make_docx(path: Path, text: str, footer: str, pages: int = 1) -> Path:
    doc = Document()
    doc.sections[0].footer.paragraphs[0].text = footer
    for i in range(pages):
        doc.add_paragraph(f"{text} {i + 1}")
        if i < pages - 1:
            doc.add_page_break()
    doc.save(path)
    return path


def test_pdf_to_pngs(tmp_path):
    pdf = make_pdf(tmp_path / "My Lesson.pdf", 2, "L")
    pngs = pdf_to_pngs(pdf, tmp_path / "r", dpi=50)
    assert [p.name for p in pngs] == ["My_Lesson_p1.png", "My_Lesson_p2.png"]
    assert all(p.exists() for p in pngs)
    assert pdf_to_pngs(pdf, tmp_path / "r", dpi=50, prefix="x")[0].name == "x_p1.png"


def test_pdf_packet_duplex(tmp_path):
    a = make_pdf(tmp_path / "A handout.pdf", 2, "A")
    b = make_pdf(tmp_path / "A practice.pdf", 1, "Ap")
    c = make_pdf(tmp_path / "B handout.pdf", 2, "B")
    out = tmp_path / "out" / "packet.pdf"
    count, starts = pdf_packet([[a, b], [c]], out)
    assert (count, starts) == (6, [1, 5])  # 3 pages + 1 blank + 2 pages
    with pymupdf.open(out) as d:
        assert d.page_count == 6
        assert d[3].get_text().strip() == ""
        assert [(t[1], t[2]) for t in d.get_toc()] == [("A handout", 1), ("A practice", 3), ("B handout", 5)]
    count, starts = pdf_packet([[a], [c]], tmp_path / "even.pdf")
    assert (count, starts) == (4, [1, 3])


def _page(path: Path, mark: bool = False) -> None:
    im = Image.new("RGB", (200, 200), "white")
    d = ImageDraw.Draw(im)
    d.text((10, 10), "page", fill="black")
    if mark:
        d.rectangle((50, 50, 150, 150), fill="black")
    im.save(path)


def test_diff_renders(tmp_path):
    new, prev, out = tmp_path / "new", tmp_path / "prev", tmp_path / "diff"
    new.mkdir()
    for n in ("a_p1.png", "a_p2.png"):
        _page(new / n)
    snapshot(new, prev)
    assert diff_renders(new, prev, out) == []
    _page(new / "a_p2.png", mark=True)
    _page(new / "a_p3.png")
    assert diff_renders(new, prev, out) == ["a_p2.png", "a_p3.png"]
    assert (out / "a_p2_diff.png").exists()
    snapshot(new, prev)
    assert diff_renders(new, prev) == []


OMML = (
    '<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
    "<m:r><m:t>△ABC≅△DEF</m:t></m:r></m:oMath>"
)
OMML_FRAC = (
    '<m:oMath xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math">'
    "<m:f><m:num><m:r><m:t>1</m:t></m:r></m:num><m:den><m:r><m:t>2</m:t></m:r></m:den></m:f>"
    "<m:sSup><m:e><m:r><m:t>x</m:t></m:r></m:e><m:sup><m:r><m:t>2</m:t></m:r></m:sup></m:sSup></m:oMath>"
)


def test_ingest_docx(tmp_path):
    img = tmp_path / "dot.png"
    Image.new("RGB", (40, 30), "red").save(img)
    doc = Document()
    doc.add_heading("Lesson 9", level=1)
    p = doc.add_paragraph("We know that ")
    p._p.append(parse_xml(OMML))
    p.add_run(" by SSS.")
    doc.add_paragraph()._p.append(parse_xml(OMML_FRAC))
    t = doc.add_table(rows=2, cols=2)
    for (r, c), v in {(0, 0): "Side", (0, 1): "Length", (1, 0): "AB", (1, 1): "5"}.items():
        t.cell(r, c).text = v
    doc.add_paragraph("Figure:").add_run().add_picture(str(img))
    src = tmp_path / "Lesson 9 Notes.docx"
    doc.save(src)

    out = tmp_path / "ingest"
    [md] = ingest([src], out, render=False)
    text = md.read_text(encoding="utf-8")
    assert md.name == "Lesson 9 Notes.md"
    assert "# Lesson 9" in text
    assert "We know that $△ABC≅△DEF$ by SSS." in text
    assert "$(1)/(2)x^2$" in text or "$1/2x^2$" in text
    assert "| Side | Length |" in text and "| AB | 5 |" in text and "| --- |" in text
    assert "![](<Lesson 9 Notes_media/" in text
    assert len(list((out / "Lesson 9 Notes_media").iterdir())) == 1
    assert text.index("SSS") < text.index("| Side") < text.index("![](")


def test_ingest_pdf(tmp_path):
    pdf = tmp_path / "quiz.pdf"
    doc = pymupdf.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Question 1", fontsize=14)
    im = tmp_path / "blue.png"
    Image.new("RGB", (60, 60), "blue").save(im)
    page.insert_image(pymupdf.Rect(72, 100, 172, 200), filename=str(im))
    doc.save(pdf)
    [md] = ingest([pdf], tmp_path / "o", render=True, dpi=40)
    text = md.read_text(encoding="utf-8")
    assert "Question 1" in text and "![](quiz_media/p1_img" in text
    assert (tmp_path / "o" / "quiz_pages" / "quiz_p1.png").exists()


@needs_word
def test_docx_to_pdf_word(tmp_path):
    a = make_docx(tmp_path / "a doc.docx", "Alpha", "Footer A", pages=2)
    b = make_docx(tmp_path / "b.docx", "Beta", "Footer B")
    res = docx_to_pdf([a, b], tmp_path / "pdf")
    assert [(p.name, n) for p, n in res] == [("a doc.pdf", 2), ("b.pdf", 1)]
    assert all(p.exists() for p, _ in res)
    [(p, n)] = docx_to_pdf([b])
    assert p == b.with_suffix(".pdf") and n == 1


@needs_word
def test_docx_packet_word(tmp_path):
    a1 = make_docx(tmp_path / "a1.docx", "A1", "Footer A1")
    a2 = make_docx(tmp_path / "a2.docx", "A2", "Footer A2", pages=2)
    b1 = make_docx(tmp_path / "b1.docx", "B1", "Footer B1")
    out = tmp_path / "packet.docx"
    pages = docx_packet([[a1, a2], [b1]], out)
    assert out.exists()
    [(pdf, n)] = docx_to_pdf([out])
    assert pages == n
    with pymupdf.open(pdf) as d:
        texts = [pg.get_text() for pg in d]
    starts = [i + 1 for i, t in enumerate(texts) if "B1 1" in t]
    assert starts and starts[0] % 2 == 1
    assert "Footer A2" in texts[1] and "Footer B1" in texts[starts[0] - 1]

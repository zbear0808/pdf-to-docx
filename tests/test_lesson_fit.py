from pathlib import Path

import pymupdf
import pytest

from lesson_builder.export import docx_to_pdf, word_available
from lesson_builder.pagefill import (PageFill, format_report, mismatch, overflow, page_report, pinned,
                                     summary_line, uneven)

needs_word = pytest.mark.skipif(not word_available(), reason="Microsoft Word / pywin32 not available")


def _pdf(path: Path, pages: list[list[tuple]]) -> Path:
    """Each page is a list of (kind, y, text): num = bold item number with body text after it, text = body
    line, head = bold 12 pt heading, img = 1 in tall image whose top is y, rect = drawn box from y to text (y1),
    foot = 8 pt footer line."""
    doc = pymupdf.open()
    pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 20, 20), False)
    pix.clear_with(200)
    for spec in pages:
        pg = doc.new_page(width=612, height=792)
        for kind, y, text in spec:
            if kind == "num":
                pg.insert_text((43, y), text, fontname="hebo", fontsize=11)
                pg.insert_text((65, y), "Find the missing side and explain your steps.", fontname="helv",
                               fontsize=11)
            elif kind == "text":
                pg.insert_text((65, y), text or "Some body text for the problem.", fontname="helv", fontsize=11)
            elif kind == "head":
                pg.insert_text((43, y), text, fontname="hebo", fontsize=12)
            elif kind == "img":
                pg.insert_image(pymupdf.Rect(300, y, 372, y + 72), pixmap=pix)
            elif kind == "rect":
                pg.draw_rect(pymupdf.Rect(65, y, 560, float(text)), color=(0, 0, 0), width=0.75)
            elif kind == "foot":
                pg.insert_text((400, y), text, fontname="helv", fontsize=8)
    doc.save(path)
    return path


def _body(y0, y1, step=40):
    return [("text", y, None) for y in range(y0, y1, step)]


def test_slack_items_and_footer(tmp_path):
    p = _pdf(tmp_path / "a.pdf", [
        [("head", 50, "Warm-up"), ("num", 80, "1."), *_body(100, 300), ("num", 320, "2."), *_body(340, 700),
         ("foot", 770, "Geometry Unit 2 | Lesson 2.1 | page 1")],
        [("num", 60, "3."), *_body(80, 280), ("foot", 770, "page 2")],
    ])
    r = page_report(p)
    assert [x.page for x in r] == [1, 2]
    assert r[0].items == ["1", "2"] and r[1].items == ["3"]
    assert r[0].headings == ["Warm-up"]
    assert not r[0].continued and not r[1].continued
    assert r[0].slack == pytest.approx((756 - 663) / 72, abs=0.08)  # last line at y=660; footer ignored
    assert r[1].slack == pytest.approx((756 - 243) / 72, abs=0.08)


def test_images_and_drawings_count_as_content(tmp_path):
    p = _pdf(tmp_path / "b.pdf", [
        [("num", 60, "1."), ("img", 500, None)],
        [("num", 60, "2."), ("rect", 80, "650")],
    ])
    r = page_report(p)
    assert r[0].slack == pytest.approx((756 - 572) / 72, abs=0.05)
    assert r[1].slack == pytest.approx((756 - 650) / 72, abs=0.05)


def test_continuation_and_overflow(tmp_path):
    p = _pdf(tmp_path / "c.pdf", [
        [("num", 60, "1."), *_body(80, 400), ("num", 420, "2."), *_body(440, 740)],
        [*_body(50, 200), ("num", 220, "3."), *_body(240, 500)],
        [("num", 60, "4."), *_body(80, 200)],
    ])
    r = page_report(p)
    assert r[1].continued and r[1].carried == "2"
    assert not r[2].continued and r[2].first == "item 4"
    assert r[1].lead == pytest.approx((220 - 8 - 42) / 72, abs=0.1)  # top line to item 3
    assert overflow(r, 3) is None
    assert overflow(r, 1) == "item 2 continues onto p2 (budget 1)"
    assert overflow(r, 2) == "item 4 starts p3 (budget 2)"
    txt = format_report("handout", r, 2)
    assert txt.splitlines()[0].startswith("handout p1: slack ")
    assert "items 1-2" in txt and "items 3 (cont. 2)" in txt
    assert txt.splitlines()[-1] == "OVER: item 4 starts p3 (budget 2)"
    assert summary_line("handout", r, 2).startswith("handout 3p/2: p1 ")


def test_heading_at_top_is_not_a_continuation(tmp_path):
    p = _pdf(tmp_path / "d.pdf", [[("num", 60, "1."), *_body(80, 700)], [("head", 50, "Exit ticket"),
                                                                           ("num", 80, "2.")]])
    r = page_report(p)
    assert not r[1].continued and r[1].headings == ["Exit ticket"]


def test_running_header_is_skipped(tmp_path):
    hdr = ("text", 50, "Lesson 2.1  Congruent parts      Name ________")
    p = _pdf(tmp_path / "e.pdf", [[hdr, ("num", 90, "1."), *_body(110, 700)],
                                  [hdr, ("num", 90, "2."), *_body(110, 300)],
                                  [hdr, *_body(90, 200), ("num", 220, "3.")]])
    r = page_report(p)
    assert [x.continued for x in r] == [False, False, True] and r[2].carried == "2"


def test_uneven_and_mismatch():
    full, empty = PageFill(1, ["1", "2"], slack=0.1), PageFill(2, ["3"], slack=3.0)
    last = PageFill(3, ["4", "5"], slack=0.2, first="item 4", lead=3.5)
    w = uneven("handout", [full, empty, last])
    assert w == ["WARN handout p2: 3.0 in empty while p1 is full (0.1 in); item 4 on p3 did not fit"]
    last.lead = 1.2
    assert uneven("handout", [full, empty, last])[0].endswith("page break before item 4 on p3 (1.2 in would fit)")
    assert pinned([full, empty, last], 2) == ("p3 starts after a page break: its first block (1.2 in) fits in "
                                              "the 3.0 in left on p2")
    assert pinned([full, empty, last], 3) is None
    head = PageFill(3, ["1"], slack=3.0, first="'QuickNotes'", lead=2.0)
    assert overflow([full, empty, head], 2) == "'QuickNotes' starts p3, then item 1 (budget 2)"
    assert uneven("handout", [full, PageFill(2, ["3"], slack=4.0)]) == []          # short last page is fine
    assert uneven("handout", [full, PageFill(2, ["3"], slack=4.0)], shrunk=True)  # unless we shrank
    student = [PageFill(1, ["1", "2"], slack=0.6), PageFill(2, ["3"], slack=2.0)]
    key = [PageFill(1, ["1"], slack=0.0), PageFill(2, ["2", "3"], slack=1.0)]
    assert mismatch("key", student, student) is None
    assert mismatch("key", student, key) == ("WARN key: item 2 is on key p2 but student p1 "
                                             "(slack key p2 1.0 in, student p1 0.6 in)")


@needs_word
def test_template_lesson_page_report(tmp_path):
    from typer.testing import CliRunner

    from lesson_builder.cli import app
    from lesson_builder.figures import render_all
    from lesson_builder.render import Figures, render_lesson
    from lesson_builder.spec import load_unit
    dest = tmp_path / "unit"
    res = CliRunner().invoke(app, ["new-unit", str(dest), "--course", "Algebra 1", "--unit", "3",
                                   "--title", "Linear functions"])
    assert res.exit_code == 0, res.output
    u = load_unit(dest)
    figs = render_all(u.dir / "figures.py", u.dir / "_temp" / "figures")
    lesson = next(l for l in u.lesson_specs() if l.doc_type == "lesson")
    out = render_lesson(u, lesson, Figures(u, figs))
    (s, _), (k, _) = docx_to_pdf([out["handout"], out["key"]], tmp_path / "pdf")
    rs, rk = page_report(s), page_report(k)
    assert rs and all(0 <= p.slack < 10.5 for p in rs)
    assert [i for p in rs for i in p.items], "no item numbers found on the template handout"
    assert not rs[0].continued
    assert mismatch("key", rs, rk) is None

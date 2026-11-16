import os
from pathlib import Path
from types import SimpleNamespace
from xml.etree import ElementTree

import pymupdf
import pytest
from docx import Document

from lesson_builder import cli, env, export

ENV_VARS = ("LESSON_BUILDER_PDF_ENGINE", "LESSON_BUILDER_X2T", "LESSON_BUILDER_ONLYOFFICE_FONTS",
            "LESSON_BUILDER_SOFFICE")


@pytest.fixture
def engines(monkeypatch):
    """Availability of each engine, set per test; .env is not read."""
    monkeypatch.setattr(env, "_loaded", True)
    for k in ENV_VARS:
        monkeypatch.delenv(k, raising=False)
    have = {"word": False, "onlyoffice": False, "libreoffice": False}
    monkeypatch.setattr(export, "word_available", lambda: have["word"])
    monkeypatch.setattr(export, "onlyoffice_paths", lambda: ("x2t", Path("fonts")) if have["onlyoffice"] else None)
    monkeypatch.setattr(export, "soffice_path", lambda: "soffice" if have["libreoffice"] else None)
    return have


def test_parse_env_quotes_comments_export():
    text = '''# comment
A=1
B="two words"   
C='single # not a comment'
D=plain # trailing comment
export E=exported
F=
  # indented comment
no_equals_line
G="C:\\Program Files\\x2t.exe"
H="/a/b=c"
'''
    assert env.parse_env(text) == {"A": "1", "B": "two words", "C": "single # not a comment", "D": "plain",
                                   "E": "exported", "F": "", "G": "C:\\Program Files\\x2t.exe", "H": "/a/b=c"}


def test_load_env_does_not_override(tmp_path, monkeypatch):
    a, b = tmp_path / "a.env", tmp_path / "b.env"
    a.write_text('LB_TEST_X="from a"\nLB_TEST_EMPTY=\n', encoding="utf-8")
    b.write_text("LB_TEST_X=from b\nLB_TEST_Y=from b\nLB_TEST_SET=from b\n", encoding="utf-8")
    for k in ("LB_TEST_X", "LB_TEST_Y", "LB_TEST_EMPTY"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("LB_TEST_SET", "already")
    set_ = env.load_env([a, b, tmp_path / "missing.env"])
    assert set_ == {"LB_TEST_X": "from a", "LB_TEST_Y": "from b"}
    assert os.environ["LB_TEST_X"] == "from a" and os.environ["LB_TEST_SET"] == "already"
    assert "LB_TEST_EMPTY" not in os.environ


def test_engine_order(engines):
    assert export.pdf_engine() is None
    engines["libreoffice"] = True
    assert export.pdf_engine() == "libreoffice"
    engines["onlyoffice"] = True
    assert export.pdf_engine() == "onlyoffice"
    engines["word"] = True
    assert export.pdf_engine() == "word"


def test_engine_forced(engines, monkeypatch):
    engines.update(word=True, onlyoffice=True, libreoffice=True)
    monkeypatch.setenv("LESSON_BUILDER_PDF_ENGINE", "LibreOffice")
    assert export.pdf_engine() == "libreoffice"
    monkeypatch.setenv("LESSON_BUILDER_PDF_ENGINE", "auto")
    assert export.pdf_engine() == "word"
    monkeypatch.setenv("LESSON_BUILDER_PDF_ENGINE", "pages")
    with pytest.raises(RuntimeError, match="use one of"):
        export.pdf_engine()
    engines["onlyoffice"] = False
    monkeypatch.setenv("LESSON_BUILDER_PDF_ENGINE", "onlyoffice")
    with pytest.raises(RuntimeError, match="not found"):
        export.pdf_engine()


def test_no_engine_message(engines, tmp_path):
    with pytest.raises(RuntimeError, match="Word.*OnlyOffice.*LibreOffice"):
        export.docx_to_pdf([tmp_path / "a.docx"])


def test_onlyoffice_falls_back_to_libreoffice(engines, monkeypatch, tmp_path):
    engines.update(onlyoffice=True, libreoffice=True)
    calls = []

    def fake_x2t(x2t, fonts, src, pdf):
        if "bad" in src.name:
            return False
        _pdf(pdf, 2)
        calls.append(("oo", src.name))
        return True

    def fake_soffice(soffice, src, pdf):
        _pdf(pdf, 1)
        calls.append(("lo", src.name))

    monkeypatch.setattr(export, "_x2t_export", fake_x2t)
    monkeypatch.setattr(export, "_soffice_export", fake_soffice)
    logs = []
    res = export.docx_to_pdf([tmp_path / "good.docx", tmp_path / "bad.docx"], tmp_path / "pdf", log=logs.append)
    assert [(p.name, n) for p, n in res] == [("good.pdf", 2), ("bad.pdf", 1)]
    assert calls == [("oo", "good.docx"), ("lo", "bad.docx")]
    assert len(logs) == 1 and "bad.docx" in logs[0] and "LibreOffice" in logs[0]


def test_x2t_params_escape(tmp_path):
    xml = export.x2t_params(Path("/u/A & B <1>/in.docx"), Path("/u/out's.pdf"), Path("/t"), Path("/f/fonts & co"))
    root = ElementTree.fromstring(xml.encode("utf-8"))
    get = {c.tag: c.text for c in root}
    assert get["m_sFileFrom"] == str(Path("/u/A & B <1>/in.docx"))
    assert get["m_sFileTo"] == str(Path("/u/out's.pdf"))
    assert get["m_sAllFontsPath"] == str(Path("/f/fonts & co") / "AllFonts.js")
    assert get["m_nFormatTo"] == "513" and get["m_bIsNoBase64"] == "true"


def test_onlyoffice_paths_env_and_allfonts(tmp_path, monkeypatch):
    monkeypatch.setattr(env, "_loaded", True)
    monkeypatch.setattr(export, "_X2T_DEFAULTS", ())
    monkeypatch.setattr(export, "_onlyoffice_font_defaults", lambda: [])
    x2t, fonts = tmp_path / "x2t", tmp_path / "fonts"
    x2t.write_text("")
    fonts.mkdir()
    monkeypatch.setenv("LESSON_BUILDER_X2T", str(x2t))
    monkeypatch.setenv("LESSON_BUILDER_ONLYOFFICE_FONTS", str(fonts))
    assert export.onlyoffice_paths() is None                 # no AllFonts.js yet
    (fonts / "AllFonts.js").write_text("")
    assert export.onlyoffice_paths() == (str(x2t), fonts)


def _pdf(path: Path, pages: int) -> Path:
    d = pymupdf.open()
    for i in range(pages):
        d.new_page().insert_text((72, 72), f"{path.stem} page {i + 1}")
    d.save(path)
    d.close()
    return path


def test_packets_pdf_only_without_word(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(export, "word_available", lambda: False)
    lessons = [SimpleNamespace(id=i, doc_type="lesson") for i in ("1", "2")]
    unit = SimpleNamespace(dir=tmp_path, course="Geometry", unit="9", lesson_specs=lambda: lessons)
    (tmp_path / "output").mkdir()

    def outputs(unit, l):
        return {k: tmp_path / "output" / f"{l.id} {k}.docx" for k in ("handout", "practice", "key", "practice_key")}

    monkeypatch.setattr("lesson_builder.render.outputs", outputs)
    for l in lessons:
        for p in outputs(unit, l).values():
            _pdf(p.with_suffix(".pdf"), 1)
    (tmp_path / "output" / "Geometry Unit 9 Key Packet.docx").write_bytes(b"old")
    cli._packets(unit)
    out = capsys.readouterr().out
    assert out.count("DOCX packets skipped") == 1
    with pymupdf.open(tmp_path / "output" / "Geometry Unit 9 Student Packet.pdf") as d:
        assert d.page_count == 4
    assert not (tmp_path / "output" / "Geometry Unit 9 Student Packet.docx").exists()
    assert "Student Packet: PDF 4p (lessons start [1, 3]), DOCX skipped" in out
    assert "Key Packet.docx is from an older build" in out


needs_onlyoffice = pytest.mark.skipif(not export.onlyoffice_paths(), reason="OnlyOffice x2t / fonts not available")


@needs_onlyoffice
def test_onlyoffice_real_conversion(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSON_BUILDER_PDF_ENGINE", "onlyoffice")
    src = tmp_path / "A & B doc.docx"
    doc = Document()
    doc.add_paragraph("Alpha 1")
    doc.add_page_break()
    doc.add_paragraph("Alpha 2")
    doc.save(src)
    logs = []
    [(pdf, n)] = export.docx_to_pdf([src], tmp_path / "pdf", log=logs.append)
    assert pdf == (tmp_path / "pdf" / "A & B doc.pdf").resolve() and n == 2 and not logs
    with pymupdf.open(pdf) as d:
        assert "Alpha 2" in d[1].get_text()


def test_label_widths_use_real_font_metrics():
    import pytest
    from lesson_builder.docbuilder import _font, _measure_rich
    if not (_font("calibri.ttf", 11) and _font("cambria.ttc", 11)):
        pytest.skip("neither Calibri/Cambria nor Carlito/Caladea is installed")
    # a real font, not the 0.5 em-per-character guess (which gives 0.229 in for 3 characters at 11 pt)
    assert _measure_rich("$NM \\cong$", 11) > 0.3
    assert _measure_rich("abc", 11) < 0.25

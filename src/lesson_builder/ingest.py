from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

import pymupdf
from docx import Document
from docx.oxml.ns import qn

from .export import docx_to_pdf, pdf_to_pngs

M_NS = "http://schemas.openxmlformats.org/officeDocument/2006/math"
MC_FALLBACK = "{http://schemas.openxmlformats.org/markup-compatibility/2006}Fallback"
R_EMBED = qn("r:embed")
R_ID = qn("r:id")


def _local(el) -> str:
    return el.tag.rsplit("}", 1)[-1] if isinstance(el.tag, str) else ""


def _link(rel: str) -> str:
    return f"![](<{rel}>)" if " " in rel else f"![]({rel})"


# --- OMML -> linear text -----------------------------------------------------------------------

def _wrap(s: str) -> str:
    return s if len(s) <= 1 else f"({s})"


def _omml(el) -> str:
    if not isinstance(el.tag, str) or el.tag.endswith("Pr"):
        return ""
    name, ns = _local(el), el.tag[1:].split("}")[0]
    if ns != M_NS:
        return "".join(t.text or "" for t in el.iter(qn("w:t"), qn("m:t")))

    def part(tag):
        child = el.find(f"{{{M_NS}}}{tag}")
        return "" if child is None else _omml(child)

    def prop(tag, default):
        node = el.find(f"{{{M_NS}}}{name}Pr/{{{M_NS}}}{tag}")
        return default if node is None else node.get(f"{{{M_NS}}}val", default)

    if name == "t":
        return el.text or ""
    if name == "f":
        return f"{_wrap(part('num'))}/{_wrap(part('den'))}"
    if name == "sSup":
        sup = part("sup")
        return part("e") + ("°" if sup in ("∘", "°") else sup if sup in ("'", "′", "″") else f"^{_wrap(sup)}")
    if name == "sSub":
        return f"{part('e')}_{_wrap(part('sub'))}"
    if name == "sSubSup":
        return f"{part('e')}_{_wrap(part('sub'))}^{_wrap(part('sup'))}"
    if name == "rad":
        deg = part("deg")
        return f"{'∛' if deg == '3' else '√'}{_wrap(part('e'))}" if deg in ("", "3") else f"root({deg}, {part('e')})"
    if name == "d":
        es = [_omml(e) for e in el.findall(f"{{{M_NS}}}e")]
        return prop("begChr", "(") + prop("sepChr", "|").join(es) + prop("endChr", ")")
    if name == "nary":
        lim = (f"_{_wrap(part('sub'))}" if part("sub") else "") + (f"^{_wrap(part('sup'))}" if part("sup") else "")
        return f"{prop('chr', '∫')}{lim} {part('e')}"
    if name == "acc":
        return part("e") + prop("chr", "\u0302")
    if name == "bar":
        return part("e") + "\u0305"
    if name == "groupChr":
        return part("e") + prop("chr", "\u23df")
    return "".join(_omml(c) for c in el)


# --- DOCX ----------------------------------------------------------------------------------------

class _Numbering:
    def __init__(self, doc):
        self.fmt: dict[tuple[str, str], tuple[str, str]] = {}
        self.count: dict[str, list[int]] = {}
        try:
            root = doc.part.numbering_part.element
        except Exception:
            return
        abstract = {}
        for a in root.findall(qn("w:abstractNum")):
            levels = {}
            for lvl in a.findall(qn("w:lvl")):
                fmt, txt = lvl.find(qn("w:numFmt")), lvl.find(qn("w:lvlText"))
                levels[lvl.get(qn("w:ilvl"))] = (
                    fmt.get(qn("w:val")) if fmt is not None else "decimal",
                    txt.get(qn("w:val")) if txt is not None else "",
                )
            abstract[a.get(qn("w:abstractNumId"))] = levels
        for num in root.findall(qn("w:num")):
            aid = num.find(qn("w:abstractNumId"))
            if aid is not None:
                for ilvl, v in abstract.get(aid.get(qn("w:val")), {}).items():
                    self.fmt[(num.get(qn("w:numId")), ilvl)] = v

    @staticmethod
    def _label(n: int, fmt: str) -> str:
        if fmt in ("lowerLetter", "upperLetter"):
            s = ""
            while n:
                n, r = divmod(n - 1, 26)
                s = chr(97 + r) + s
            return s.upper() if fmt == "upperLetter" else s
        if fmt in ("lowerRoman", "upperRoman"):
            vals = [(1000, "m"), (900, "cm"), (500, "d"), (400, "cd"), (100, "c"), (90, "xc"),
                    (50, "l"), (40, "xl"), (10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
            s = ""
            for v, r in vals:
                while n >= v:
                    s, n = s + r, n - v
            return s.upper() if fmt == "upperRoman" else s
        return str(n)

    def prefix(self, p) -> str:
        num_pr = p.find(f"{qn('w:pPr')}/{qn('w:numPr')}")
        if num_pr is None:
            return ""
        nid, lvl = num_pr.find(qn("w:numId")), num_pr.find(qn("w:ilvl"))
        nid = nid.get(qn("w:val")) if nid is not None else None
        ilvl = lvl.get(qn("w:val")) if lvl is not None else "0"
        if not nid or nid == "0":
            return ""
        fmt, text = self.fmt.get((nid, ilvl), ("bullet", ""))
        indent = "  " * int(ilvl)
        if fmt in ("bullet", "none"):
            return indent + "- "
        counts = self.count.setdefault(nid, [0] * 9)
        i = int(ilvl)
        counts[i] += 1
        counts[i + 1:] = [0] * (8 - i)
        label = text or f"%{i + 1}."
        for k in range(9):
            label = label.replace(f"%{k + 1}", self._label(max(counts[k], 1), self.fmt.get((nid, str(k)), (fmt,))[0]))
        return f"{indent}{label} "


class _DocxWriter:
    def __init__(self, path: Path, out_dir: Path):
        self.doc = Document(str(path))
        self.media_dir = out_dir / f"{path.stem}_media"
        self.saved: dict[str, str] = {}
        self.numbering = _Numbering(self.doc)

    def image(self, rid: str | None) -> str:
        if not rid:
            return ""
        if rid not in self.saved:
            part = self.doc.part.related_parts.get(rid)
            if part is None or not hasattr(part, "blob"):
                return ""
            self.media_dir.mkdir(parents=True, exist_ok=True)
            name = Path(str(part.partname)).name
            (self.media_dir / name).write_bytes(part.blob)
            self.saved[rid] = f"{self.media_dir.name}/{name}"
        return _link(self.saved[rid])

    def inline(self, el) -> str:
        out = []
        for c in el:
            name = _local(c)
            if c.tag == MC_FALLBACK or name.endswith("Pr") or name in ("instrText", "delText"):
                continue
            if name == "t":
                out.append(c.text or "")
            elif name == "tab":
                out.append("\t")
            elif name in ("br", "cr"):
                out.append("  \n")
            elif name in ("oMath", "oMathPara") and c.tag.startswith(f"{{{M_NS}}}"):
                text = _omml(c).strip()
                if text:
                    out.append(f"${text}$")
            elif name == "blip":
                out.append(self.image(c.get(R_EMBED)))
            elif name == "imagedata":
                out.append(self.image(c.get(R_ID)))
            elif name == "txbxContent":
                inner = " / ".join(t for t in (self.para(p) for p in c.iter(qn("w:p"))) if t.strip())
                if inner:
                    out.append(f" [{inner}] ")
            else:
                out.append(self.inline(c))
        return "".join(out)

    def para(self, p) -> str:
        text = self.inline(p).rstrip()
        if not text.strip():
            return text.strip()
        style = p.find(f"{qn('w:pPr')}/{qn('w:pStyle')}")
        sid = style.get(qn("w:val")) if style is not None else ""
        if sid.lower().startswith("heading") and sid[7:].isdigit():
            return "#" * min(int(sid[7:]), 6) + " " + text.strip()
        if sid.lower() == "title":
            return "# " + text.strip()
        return self.numbering.prefix(p) + text

    def cell(self, tc) -> str:
        parts = []
        for child in tc:
            if child.tag == qn("w:p"):
                parts.append(self.para(child))
            elif child.tag == qn("w:tbl"):
                parts.append(" ; ".join(" | ".join(self.cell(c) for c in r.findall(qn("w:tc")))
                                        for r in child.findall(qn("w:tr"))))
            elif child.tag == qn("w:sdt"):
                parts.append(self.cell(child.find(qn("w:sdtContent"))))
        return "<br>".join(s.strip() for s in parts if s and s.strip()).replace("|", "\\|")

    def table(self, tbl) -> str:
        rows = []
        for tr in tbl.findall(qn("w:tr")):
            row = []
            cells = [c for c in tr if c.tag == qn("w:tc")] or tr.findall(f"{qn('w:sdt')}/{qn('w:sdtContent')}/{qn('w:tc')}")
            for tc in cells:
                pr = tc.find(qn("w:tcPr"))
                vm = pr.find(qn("w:vMerge")) if pr is not None else None
                span = pr.find(qn("w:gridSpan")) if pr is not None else None
                text = "" if vm is not None and vm.get(qn("w:val")) in (None, "continue") else self.cell(tc)
                row.append(text.replace("\n", " "))
                row += [""] * (int(span.get(qn("w:val"))) - 1 if span is not None else 0)
            rows.append(row)
        if not rows:
            return ""
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        lines = ["| " + " | ".join(rows[0]) + " |", "|" + " --- |" * width]
        lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return "\n".join(lines)

    def blocks(self, parent) -> list[str]:
        out = []
        for el in parent:
            if el.tag == qn("w:p"):
                out.append(self.para(el))
            elif el.tag == qn("w:tbl"):
                out.append(self.table(el))
            elif el.tag in (qn("w:sdt"), qn("w:customXml")):
                content = el.find(qn("w:sdtContent"))
                out += self.blocks(content if content is not None else el)
        return out

    def markdown(self) -> str:
        if self.media_dir.exists():
            shutil.rmtree(self.media_dir)
        return "\n\n".join(b for b in self.blocks(self.doc.element.body) if b.strip()) + "\n"


# --- PDF -----------------------------------------------------------------------------------------

def _pdf_markdown(path: Path, out_dir: Path) -> str:
    media = out_dir / f"{path.stem}_media"
    if media.exists():
        shutil.rmtree(media)
    out = []
    with pymupdf.open(path) as doc:
        for pno, page in enumerate(doc, 1):
            out.append(f"<!-- page {pno} -->")
            for i, b in enumerate(page.get_text("dict", sort=True)["blocks"]):
                if b["type"] == 0:
                    lines = ["".join(s["text"] for s in ln["spans"]).rstrip() for ln in b["lines"]]
                    text = "  \n".join(ln for ln in lines if ln.strip())
                    if text:
                        out.append(text)
                elif b["type"] == 1 and b.get("image") and b["width"] >= 8 and b["height"] >= 8:
                    media.mkdir(parents=True, exist_ok=True)
                    name = f"p{pno}_img{i}.{b.get('ext', 'png')}"
                    (media / name).write_bytes(b["image"])
                    out.append(_link(f"{media.name}/{name}"))
    return "\n\n".join(out) + "\n"


def ingest(files: list[Path], out_dir: Path, render: bool = True, dpi: int = 110) -> list[Path]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written, to_render, docx_files = [], [], []
    for f in map(Path, files):
        ext = f.suffix.lower()
        if ext == ".docx":
            text = _DocxWriter(f, out_dir).markdown()
            docx_files.append(f)
        elif ext == ".pdf":
            text = _pdf_markdown(f, out_dir)
            to_render.append((f, f.stem))
        else:
            raise ValueError(f"ingest supports .docx and .pdf, not {f.name}")
        md = out_dir / f"{f.stem}.md"
        md.write_text(f"<!-- source: {f.name} -->\n\n{text}", encoding="utf-8")
        written.append(md)
    if render:
        with tempfile.TemporaryDirectory() as tmp:
            if docx_files:
                for src, (pdf, _) in zip(docx_files, docx_to_pdf(docx_files, Path(tmp))):
                    to_render.append((pdf, src.stem))
            for pdf, stem in to_render:
                pages = out_dir / f"{stem}_pages"
                if pages.exists():
                    shutil.rmtree(pages)
                pdf_to_pngs(pdf, pages, dpi=dpi)
    return written

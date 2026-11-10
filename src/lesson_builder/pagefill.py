"""Page-fill report for built PDFs: slack per page, items per page, and the item past the page budget."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

from .check import _labels, _red

BOTTOM_MARGIN = 0.5   # in; docbuilder.Handout page margin
FOOTER_ZONE = 0.5     # in from the page bottom; Word puts the footer here (top at about 0.45 in), not content
TOP_TOL = 12          # pt; an item number or heading this close to the top content starts the page
FULL = 0.5            # in; a page with less slack than this is full
EMPTY = 2.0           # in; a page with more slack than this, next to a full page, is uneven fill


@dataclass
class PageFill:
    page: int                       # 1-based
    items: list[str] = field(default_factory=list)      # item numbers without the dot, in reading order
    headings: list[str] = field(default_factory=list)
    slack: float = 0.0              # inches between the last content and the bottom margin
    continued: bool = False         # the page starts mid-item (top is not an item number or heading)
    carried: str | None = None      # the item that continues from the previous page, if known
    first: str = ""                 # what starts the page: "item 4", or a heading / box title in quotes
    lead: float = 0.0               # inches from the top of the content to the next item or heading


def _headings(pg, body_size: float, below: float = 0) -> list[tuple[float, str]]:
    out = []
    for b in pg.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if not spans:
                continue
            s = spans[0]
            t = "".join(x["text"] for x in spans).strip()
            bold = bool(s["flags"] & 16) or "Bold" in s["font"]
            if (bold and s["size"] >= body_size + 0.3 and not _red(s["color"]) and s["bbox"][1] >= below
                    and not re.match(r"\d{1,2}\.$", s["text"].strip()) and len(t) > 2):
                out.append((s["bbox"][1], t))
    return out


def _bold_lines(pg, below: float) -> list[tuple[float, str]]:
    """Bold, non-red lines that are not part labels (box titles such as QuickNotes start a block)."""
    out = []
    for b in pg.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            spans = [s for s in ln["spans"] if s["text"].strip()]
            if spans and ln["bbox"][1] >= below:
                s = spans[0]
                if ((s["flags"] & 16 or "Bold" in s["font"]) and not _red(s["color"])
                        and not re.fullmatch(r"[a-d]\.", s["text"].strip())):
                    out.append((ln["bbox"][1], "".join(x["text"] for x in spans).strip()))
    return out


def _header_bottoms(doc) -> list[float]:
    """Per page, the bottom (pt) of the running header: text lines in the top 1 in that also appear at the
    same height on another page. 0 when there is none."""
    tops = []
    for pg in doc:
        lines = {}
        for b in pg.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                t = "".join(s["text"] for s in ln["spans"]).strip()
                if t and ln["bbox"][3] < 72:
                    lines[(round(ln["bbox"][1]), t)] = ln["bbox"][3]
        tops.append(lines)
    out = []
    for i, lines in enumerate(tops):
        rep = [y1 for k, y1 in lines.items() if any(k in o for j, o in enumerate(tops) if j != i)]
        out.append(max(rep) + 6 if rep else 0.0)
    return out


def _body_size(doc) -> float:
    sizes: dict[float, int] = {}
    for pg in doc:
        for b in pg.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                for s in ln["spans"]:
                    if s["text"].strip():
                        k = round(s["size"], 1)
                        sizes[k] = sizes.get(k, 0) + len(s["text"])
    return max(sizes, key=sizes.get) if sizes else 11.0


def _content_extent(pg, below: float = 0) -> tuple[float | None, float | None]:
    """(top, bottom) in pt of text, images and drawings above the footer zone. The top ignores anything
    above `below` (the running header)."""
    H = pg.rect.height
    limit = H - FOOTER_ZONE * 72
    boxes = []
    for b in pg.get_text("dict")["blocks"]:
        if b["type"] == 0:
            for ln in b.get("lines", []):
                if any(s["text"].strip() for s in ln["spans"]):
                    boxes.append(ln["bbox"])
        else:
            boxes.append(b["bbox"])
    boxes += [i["bbox"] for i in pg.get_image_info()]
    for d in pg.get_drawings():
        r = d["rect"]
        if r.height > 0.9 * H or (r.width < 0.5 and r.height < 0.5):
            continue  # page backgrounds and specks
        if d.get("fill") == (1.0, 1.0, 1.0) and not d.get("color"):
            continue  # white fills draw nothing
        boxes.append((r.x0, r.y0, r.x1, r.y1))
    boxes = [b for b in boxes if b[1] < limit]
    if not boxes:
        return None, None
    body = [b[1] for b in boxes if b[1] >= below]
    return (min(body) if body else None), min(max(b[3] for b in boxes), H)


def page_report(pdf: Path) -> list[PageFill]:
    out: list[PageFill] = []
    with pymupdf.open(pdf) as doc:
        nums = [l for l in _labels(doc) if l["kind"] == "num"]
        size = _body_size(doc)
        head = _header_bottoms(doc)
        last_item = None
        for pi, pg in enumerate(doc):
            H = pg.rect.height
            top, bottom = _content_extent(pg, head[pi])
            floor = H - BOTTOM_MARGIN * 72
            slack = (floor - bottom) / 72 if bottom is not None else (floor - BOTTOM_MARGIN * 72) / 72
            here = [l for l in nums if l["page"] == pi]
            heads = _headings(pg, size, head[pi])
            marks = sorted([(l["y"], "item " + l["text"].rstrip(".")) for l in here]
                           + [(y, f"'{t[:30]}'") for y, t in heads + _bold_lines(pg, head[pi])])
            continued = pi > 0 and top is not None and (not marks or marks[0][0] - top > TOP_TOL)
            major = [y for y, _ in heads] + [l["y"] for l in here]
            nxt = [y for y in major if top is not None and y > top + TOP_TOL]
            lead = ((min(nxt) if nxt else bottom) - top) / 72 if top is not None else 0.0
            out.append(PageFill(page=pi + 1, items=[l["text"].rstrip(".") for l in here],
                                headings=[t for _, t in heads], slack=round(max(slack, 0.0), 2),
                                continued=continued, carried=last_item if continued else None,
                                first="" if continued or not marks else marks[0][1], lead=round(lead, 2)))
            if here:
                last_item = here[-1]["text"].rstrip(".")
    return out


def _span(items: list[str]) -> str:
    if not items:
        return "none"
    try:
        n = [int(i) for i in items]
    except ValueError:
        return ", ".join(items)
    if len(n) > 1 and n == list(range(n[0], n[0] + len(n))):
        return f"{n[0]}-{n[-1]}"
    return ", ".join(items)


def overflow(report: list[PageFill], budget: int) -> str | None:
    """Names the first item on the first page past the budget, or None if the document fits."""
    if len(report) <= budget:
        return None
    p = report[budget]
    if p.continued and p.carried:
        what = f"item {p.carried} continues onto p{p.page}"
    elif p.first.startswith("'") and p.items:
        what = f"{p.first} starts p{p.page}, then item {p.items[0]}"
    elif p.items:
        what = f"item {p.items[0]} starts p{p.page}"
    elif p.first:
        what = f"{p.first} starts p{p.page}"
    else:
        what = f"p{p.page} has no item numbers"
    return f"{what} (budget {budget})"


def pinned(report: list[PageFill], budget: int) -> str | None:
    """The page past the budget starts with a block short enough for the slack on the page before it, so
    Word did not move it for lack of room: a page break (or a keep-with-next chain) holds it there, and
    shrinking workspace will not pull it back unless the pages before the break merge."""
    if len(report) <= budget or budget < 1:
        return None
    p, prev = report[budget], report[budget - 1]
    if p.continued or not p.lead or p.lead >= prev.slack:
        return None
    return (f"p{p.page} starts after a page break: its first block ({p.lead:.1f} in) fits in the "
            f"{prev.slack:.1f} in left on p{prev.page}")


def slack_list(report: list[PageFill]) -> str:
    return ", ".join(f"p{p.page} {p.slack:.1f}" for p in report) + " in"


def format_report(name: str, report: list[PageFill], budget: int) -> str:
    lines = []
    for p in report:
        cont = f" (cont. {p.carried})" if p.carried else (" (cont.)" if p.continued else "")
        lines.append(f"{name} p{p.page}: slack {p.slack:.1f} in, items {_span(p.items)}{cont}")
    over = overflow(report, budget)
    if over:
        lines.append(f"OVER: {over}")
    return "\n".join(lines)


def summary_line(name: str, report: list[PageFill], budget: int) -> str:
    pages = "; ".join(f"p{p.page} {p.slack:.1f} in [{_span(p.items)}]" for p in report)
    return f"{name} {len(report)}p/{budget}: {pages}"


def uneven(name: str, report: list[PageFill], shrunk: bool = False) -> list[str]:
    """Pages with lots of room while another page of the same document is full. The last page counts only
    after a workspace shrink (otherwise a short last page is just the end of the document)."""
    full = [p for p in report if p.slack < FULL]
    if not full:
        return []
    out = []
    for i, p in enumerate(report):
        if p.slack <= EMPTY or (i == len(report) - 1 and not shrunk):
            continue
        f = next(q for q in full if q is not p)
        nxt = report[i + 1] if i + 1 < len(report) else None
        why = ""
        if nxt is not None:
            first = nxt.first or (f"item {nxt.items[0]}" if nxt.items else "")
            if nxt.continued and nxt.carried:
                why = f"; item {nxt.carried} continues on p{nxt.page}"
            elif first and nxt.lead and nxt.lead < p.slack:
                why = f"; page break before {first} on p{nxt.page} ({nxt.lead:.1f} in would fit)"
            elif first:
                why = f"; {first} on p{nxt.page} did not fit"
        out.append(f"WARN {name} p{p.page}: {p.slack:.1f} in empty while p{f.page} is full "
                   f"({f.slack:.1f} in){why}")
    return out


def mismatch(name: str, student: list[PageFill], key: list[PageFill]) -> str | None:
    """First item that sits on a different page in the key than on the student copy."""
    def where(rep):
        return [(i, p.page) for p in rep for i in p.items]
    s, k = where(student), where(key)
    if s == k:
        return None
    for j in range(max(len(s), len(k))):
        a = s[j] if j < len(s) else None
        b = k[j] if j < len(k) else None
        if a == b:
            continue
        if a and b and a[0] == b[0]:
            sp, kp = student[a[1] - 1], key[b[1] - 1]
            return (f"WARN {name}: item {a[0]} is on key p{b[1]} but student p{a[1]} "
                    f"(slack key p{kp.page} {kp.slack:.1f} in, student p{sp.page} {sp.slack:.1f} in)")
        if a and b:
            return f"WARN {name}: item order differs at student {a[0]} (p{a[1]}) vs key {b[0]} (p{b[1]})"
        if a:
            return f"WARN {name}: item {a[0]} (student p{a[1]}) not found in the key"
        return f"WARN {name}: key item {b[0]} (p{b[1]}) not found on the student copy"
    return None

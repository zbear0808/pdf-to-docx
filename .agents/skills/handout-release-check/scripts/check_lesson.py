"""Release checks for lesson handouts, keys, and practice sets.

  check_lesson.py draft   --draft lesson/draft.md [--minutes 40]
  check_lesson.py outputs --student "X Student Handout.pdf" --key "X Lesson Key.pdf" [--max-pages 3]

draft:   `___` in student text, Problem refs that don't exist, plan timing over budget,
         draw/sketch/mark tasks without a `**Key image**` line.
outputs: `___` or red text on the student copy, blank or extra pages, item numbers that differ between
         student and key, and items or parts with no red answer on the key.
Exit code 1 on any ERROR.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

DRAW = re.compile(r"(?:^|[.:]\s+|\b(?:then|and)\s+)(draw|sketch|construct|mark|shade|plot|graph|reflect|rotate)\b",
                  re.I)
PROB = re.compile(r"^#{3,5}\s+(?:Problem|CYU)\s+(\d+)\b", re.I)


def section(md: str, start: str, stop: str | None) -> str:
    i = md.find(start)
    if i < 0:
        return ""
    j = md.find(stop, i + 1) if stop else -1
    return md[i:j if j > 0 else None]


def check_draft(path: Path, minutes: int, issues: list[str]) -> None:
    md = path.read_text(encoding="utf-8")
    student = section(md, "## A.", "## B.")
    plan = section(md, "## D.", None)
    if not student:
        issues.append("WARN  no '## A.' student section found; draft checks skipped")
        return
    # 1. blanks in student text (header name lines are built by code, not drafts)
    for n, line in enumerate(student.splitlines(), 1):
        if "___" in line:
            issues.append(f"ERROR A:{n} '___' blank; use a labeled box: {line.strip()[:70]}")
    # 2. problem refs. CYU items have their own numbering, so check each block separately.
    blocks = re.split(r"\n(?=#{3,4}\s+Check your understanding)", student, flags=re.I)
    for b in blocks:
        nums = {int(m.group(1)) for m in (PROB.match(l) for l in b.splitlines()) if m}
        for m in re.finditer(r"\bProblems?\s+(\d+)(?:\s*-\s*(\d+))?", b):
            for k in {int(m.group(1)), int(m.group(2) or m.group(1))}:
                if nums and k not in nums:
                    issues.append(f"ERROR reference to Problem {k}, which isn't in this part (has {sorted(nums)})")
        for m in re.finditer(r"(claim|answer|work|result) from Problem (\d+)", b, re.I):
            issues.append(f"WARN  '{m.group(0)}': check that Problem {m.group(2)} really supports this task")
    # 3. drawing tasks need a key figure
    for chunk in re.split(r"\n(?=#{3,5}\s+(?:Problem|CYU)\s+\d+)", student):
        head = PROB.match(chunk.strip().splitlines()[0]) if chunk.strip() else None
        if not head:
            continue
        body = re.sub(r"`[^`]*`", "", chunk)
        optional = re.search(r"optional|if it helps", body, re.I)
        if DRAW.search(body) and "**Key image**" not in chunk and not optional:
            issues.append(f"ERROR Problem {head.group(1)} asks students to draw or mark; add "
                          "'- **Key image**: <path>' with a labeled answer figure")
    # 4. timing
    ends = [int(m.group(2)) for m in re.finditer(r"^\|\s*(\d+)\s*-\s*(\d+)\s*\|", plan, re.M)]
    if not ends:
        issues.append("WARN  no timing table ('| 0-4 | ...') in section D")
    elif max(ends) > minutes:
        issues.append(f"ERROR plan runs {max(ends)} min; budget is {minutes}. Cut items (see lesson-scope)")


# ----------------------------------------------------------------------------- rendered PDFs
def red(color: int) -> bool:
    r, g, b = (color >> 16) & 255, (color >> 8) & 255, color & 255
    return r > 150 and g < 80 and b < 80


def labels(doc, stop_at="Answers to selected problems"):
    """Problem labels (bold 'N.') and part labels ('a.' at line start) with positions."""
    out, stopped = [], False
    for pi, pg in enumerate(doc):
        for b in pg.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                spans = [s for s in ln["spans"] if s["text"].strip()]
                if not spans:
                    continue
                if stop_at in "".join(s["text"] for s in spans):
                    stopped = True
                if stopped:
                    continue
                s = spans[0]
                t = s["text"].strip()
                bold = bool(s["flags"] & 16) or "Bold" in s["font"]
                if bold and re.fullmatch(r"\d{1,2}\.", t) and not red(s["color"]):
                    out.append(dict(page=pi, kind="num", text=t, x=s["bbox"][0], y=s["bbox"][1]))
                elif re.fullmatch(r"[a-d]\.", t) and not red(s["color"]):
                    out.append(dict(page=pi, kind="part", text=t, x=s["bbox"][0], y=s["bbox"][1]))
        stopped = False if pi + 1 < len(doc) else stopped
    return out


def answered(pg, x0, x1, y0, y1, student_imgs):
    for b in pg.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for s in ln["spans"]:
                bx0, by0 = s["bbox"][0], s["bbox"][1]
                if s["text"].strip() and red(s["color"]) and x0 <= bx0 < x1 and y0 <= by0 < y1:
                    return True
    for d in pg.get_drawings():
        c = d.get("color") or d.get("fill")
        r = d["rect"]
        if c and c[0] > 0.6 and c[1] < 0.3 and c[2] < 0.3 and x0 <= r.x0 < x1 and y0 <= r.y0 < y1:
            return True
    imgs = [i for i in pg.get_image_info() if x0 - 5 <= i["bbox"][0] < x1 and y0 <= i["bbox"][1] < y1]
    return len(imgs) > student_imgs  # a key-only figure counts as an answer


def check_outputs(student: Path, key: Path, max_pages: int, issues: list[str]) -> None:
    import pymupdf
    s, k = pymupdf.open(student), pymupdf.open(key)
    for name, d in (("student", s), ("key", k)):
        if len(d) > max_pages:
            issues.append(f"ERROR {name} has {len(d)} pages; budget is {max_pages}")
        for i, pg in enumerate(d):
            body = [b for b in pg.get_text("blocks") if b[1] < pg.rect.height - 50 and b[4].strip()]
            if not body and not pg.get_images():
                issues.append(f"ERROR {name} page {i + 1} is blank")
    if len(s) != len(k):
        issues.append(f"ERROR page count differs: student {len(s)}, key {len(k)}")
    for i, pg in enumerate(s):
        for b in pg.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                txt = "".join(sp["text"] for sp in ln["spans"])
                if "___" in txt and "Name" not in txt and "Period" not in txt:
                    issues.append(f"ERROR student p{i + 1}: '___' blank: {txt.strip()[:60]}")
                if any(red(sp["color"]) and sp["text"].strip() for sp in ln["spans"]):
                    issues.append(f"ERROR student p{i + 1}: red (key) text on student copy: {txt.strip()[:60]}")
    ls, lk = labels(s), labels(k)
    nums = lambda L: [(l["page"], l["text"]) for l in L if l["kind"] == "num"]  # noqa: E731
    if nums(ls) != nums(lk):
        issues.append(f"ERROR item numbers differ between student and key: {nums(ls)} vs {nums(lk)}")
    # answer regions on the key: each leaf item (a part, or a numbered item without parts)
    simg = {}
    for l in ls:
        simg.setdefault(l["page"], s[l["page"]].get_image_info())
    for pi in sorted({l["page"] for l in lk}):
        pg = k[pi]
        W, H = pg.rect.width, pg.rect.height - 45
        page_l = [l for l in lk if l["page"] == pi]
        xs = sorted({round(l["x"]) for l in page_l if l["kind"] == "num"})
        cols = []
        for x in xs:
            if not cols or x - cols[-1] > 40:
                cols.append(x)
        for l in page_l:
            ci = max([i for i, c in enumerate(cols) if c <= l["x"] + 5] or [0])
            l["col"] = ci
        for idx, l in enumerate(page_l):
            x0 = cols[l["col"]] - 8 if cols else 0
            x1 = cols[l["col"] + 1] - 8 if l["col"] + 1 < len(cols) else W
            later = [m for m in page_l if m["col"] == l["col"] and m["y"] > l["y"] + 2]
            y1 = min([m["y"] for m in later], default=H)
            nxt = min(later, key=lambda m: m["y"]) if later else None
            if l["kind"] == "num" and nxt is not None and nxt["kind"] == "part":
                continue  # stem of a multi-part item; the parts carry the answers
            si = [i for i in simg.get(pi, []) if x0 - 5 <= i["bbox"][0] < x1 and l["y"] <= i["bbox"][1] < y1]
            if not answered(pg, x0, x1, l["y"] - 2, y1, len(si)):
                issues.append(f"ERROR key p{pi + 1}: no answer found for {l['text']} near y={l['y'] / 72:.1f} in")


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("draft")
    d.add_argument("--draft", type=Path, required=True)
    d.add_argument("--minutes", type=int, default=40)
    o = sub.add_parser("outputs")
    o.add_argument("--student", type=Path, required=True)
    o.add_argument("--key", type=Path, required=True)
    o.add_argument("--max-pages", type=int, default=3)
    a = ap.parse_args()
    issues: list[str] = []
    if a.cmd == "draft":
        check_draft(a.draft, a.minutes, issues)
    else:
        check_outputs(a.student, a.key, a.max_pages, issues)
    for i in issues:
        print(i)
    errs = sum(i.startswith("ERROR") for i in issues)
    print(f"{errs} errors, {len(issues) - errs} warnings")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())

"""Release checks. Spec checks read the lesson YAML; output checks read the rendered PDFs."""
from __future__ import annotations

import re
from pathlib import Path

from .spec import Item, LessonSpec, Part, UnitSpec, as_list

DRAW = re.compile(r"(?:^|[.:]\s+|\b(?:then|and)\s+)(draw|sketch|construct|mark|shade|plot|graph)\b", re.I)


def _texts(it: Item | Part) -> list[str]:
    t = as_list(it.prompt)
    t += [r[0] for r in it.fill or []] + [str(r[0]) for r in it.frame or []]
    if isinstance(it, Item):
        t += it.choices or []
    return t


def _has_answer(it: Item | Part) -> bool:
    if it.no_answer or as_list(it.answer) or it.fill or it.frame:
        return True
    if isinstance(it, Item) and (it.table or (it.columns and it.columns.answers) or it.draw or it.choices and
                                 as_list(it.answer)):
        return True
    return False


def check_spec(unit: UnitSpec, lesson: LessonSpec, figures: dict | None = None) -> list[str]:
    figures = figures or {}
    issues = []
    where = f"{lesson.id}"
    if lesson.minutes > unit.budget.minutes:
        issues.append(f"ERROR {where}: item minutes add up to {lesson.minutes:g}; budget is {unit.budget.minutes}")
    plan_end = [int(m.group(1)) for m in re.finditer(r"^\|\s*\d+\s*-\s*(\d+)\s*\|", lesson.plan, re.M)]
    if plan_end and max(plan_end) > unit.budget.minutes:
        issues.append(f"ERROR {where}: plan timing table runs to {max(plan_end)} min")

    groups = []  # numbering restarts on the QuickNotes page
    cur = []
    for s in lesson.sections:
        if s.kind == "notes":
            groups.append(cur)
            cur = []
        cur += [it for it in s.items]
    groups.append(cur)
    if lesson.practice:
        groups.append([it for r in lesson.practice.rows for it in r.cells])

    for g in groups:
        nums = {it.n for it in g if it.n}
        for it in g:
            label = f"{where} item {it.n or '(unnumbered)'}"
            for part in [it] + list(it.parts):
                plabel = label + (f" part {part.label}" if isinstance(part, Part) else "")
                text = " ".join(_texts(part))
                if "___" in text:
                    issues.append(f"ERROR {plabel}: '___' blank; use fill/frame boxes")
                for m in re.finditer(r"\bProblems?\s+(\d+)(?:\s*-\s*(\d+))?", text):
                    for k in {m.group(1), m.group(2) or m.group(1)}:
                        if k not in nums:
                            issues.append(f"ERROR {plabel}: refers to Problem {k}, which isn't in this part")
                for m in re.finditer(r"(claim|answer|work|result) from Problem (\d+)", text, re.I):
                    issues.append(f"WARN  {plabel}: '{m.group(0)}': make sure Problem {m.group(2)} supports this")
                if not _has_answer(part) and not (isinstance(part, Item) and part.parts):
                    issues.append(f"ERROR {plabel}: no answer (add `answer:` or `no_answer: true`)")
            text = " ".join(t for p in [it] + list(it.parts) for t in _texts(p))
            if DRAW.search(text) and not re.search(r"if it helps|optional", text, re.I):
                has_key_fig = bool(it.key_figure or (it.draw and (it.draw.key_figure or it.figure))
                                   or figures.get(it.figure or "", {}).get("key"))
                if not has_key_fig:
                    issues.append(f"ERROR {label}: drawing task without a key figure (key_figure, draw.key_figure, "
                                  "or a registered figure with an answer layer)")
    return issues


# ----------------------------------------------------------------------------- rendered PDFs
def _red(color: int) -> bool:
    r, g, b = (color >> 16) & 255, (color >> 8) & 255, color & 255
    return r > 150 and g < 80 and b < 80


def _labels(doc, stop_at="Answers to selected problems"):
    out = []
    for pi, pg in enumerate(doc):
        stopped = False
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
                if bold and re.fullmatch(r"\d{1,2}\.", t) and not _red(s["color"]):
                    out.append(dict(page=pi, kind="num", text=t, x=s["bbox"][0], y=s["bbox"][1]))
                elif re.fullmatch(r"[a-d]\.", t) and not _red(s["color"]):
                    out.append(dict(page=pi, kind="part", text=t, x=s["bbox"][0], y=s["bbox"][1]))
    return out


def _answered(pg, x0, x1, y0, y1, student_imgs):
    for b in pg.get_text("dict")["blocks"]:
        for ln in b.get("lines", []):
            for s in ln["spans"]:
                if s["text"].strip() and _red(s["color"]) and x0 <= s["bbox"][0] < x1 and y0 <= s["bbox"][1] < y1:
                    return True
    for d in pg.get_drawings():
        c, r = d.get("color") or d.get("fill"), d["rect"]
        if c and c[0] > 0.6 and c[1] < 0.3 and c[2] < 0.3 and x0 <= r.x0 < x1 and y0 <= r.y0 < y1:
            return True
    imgs = [i for i in pg.get_image_info() if x0 - 5 <= i["bbox"][0] < x1 and y0 <= i["bbox"][1] < y1]
    return len(imgs) > student_imgs


def check_outputs(student: Path, key: Path, max_pages: int) -> list[str]:
    import pymupdf
    issues = []
    s, k = pymupdf.open(student), pymupdf.open(key)
    tag = Path(student).stem
    for name, d in (("student", s), ("key", k)):
        if len(d) > max_pages:
            issues.append(f"ERROR {tag} {name}: {len(d)} pages; budget is {max_pages}")
        for i, pg in enumerate(d):
            body = [b for b in pg.get_text("blocks") if b[1] < pg.rect.height - 50 and b[4].strip()]
            if not body and not pg.get_images():
                issues.append(f"ERROR {tag} {name}: page {i + 1} is blank")
    if len(s) != len(k):
        issues.append(f"ERROR {tag}: page count differs: student {len(s)}, key {len(k)}")
    for i, pg in enumerate(s):
        for b in pg.get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                txt = "".join(sp["text"] for sp in ln["spans"])
                if "___" in txt and "Name" not in txt and "Period" not in txt:
                    issues.append(f"ERROR {tag} student p{i + 1}: '___' blank: {txt.strip()[:60]}")
                if any(_red(sp["color"]) and sp["text"].strip() for sp in ln["spans"]):
                    issues.append(f"ERROR {tag} student p{i + 1}: red key text on the student copy")
    ls, lk = _labels(s), _labels(k)
    nums = lambda L: [(l["page"], l["text"]) for l in L if l["kind"] == "num"]  # noqa: E731
    if nums(ls) != nums(lk):
        issues.append(f"ERROR {tag}: item numbers differ between student and key")
    simg = {p: s[p].get_image_info() for p in {l["page"] for l in ls}}
    for pi in sorted({l["page"] for l in lk}):
        pg = k[pi]
        W, H = pg.rect.width, pg.rect.height - 45
        page_l = [l for l in lk if l["page"] == pi]
        cols = []
        for x in sorted({round(l["x"]) for l in page_l if l["kind"] == "num"}):
            if not cols or x - cols[-1] > 40:
                cols.append(x)
        for l in page_l:
            l["col"] = max([i for i, c in enumerate(cols) if c <= l["x"] + 5] or [0])
        for l in page_l:
            x0 = cols[l["col"]] - 8 if cols else 0
            x1 = cols[l["col"] + 1] - 8 if l["col"] + 1 < len(cols) else W
            later = [m for m in page_l if m["col"] == l["col"] and m["y"] > l["y"] + 2]
            y1 = min([m["y"] for m in later], default=H)
            nxt = min(later, key=lambda m: m["y"]) if later else None
            if l["kind"] == "num" and nxt is not None and nxt["kind"] == "part":
                continue
            si = [i for i in simg.get(pi, []) if x0 - 5 <= i["bbox"][0] < x1 and l["y"] <= i["bbox"][1] < y1]
            if not _answered(pg, x0, x1, l["y"] - 2, y1, len(si)):
                issues.append(f"ERROR {tag} key p{pi + 1}: no answer for {l['text']} near y={l['y'] / 72:.1f} in")
    return issues


def summarize(issues: list[str]) -> tuple[int, int]:
    errs = sum(i.startswith("ERROR") for i in issues)
    return errs, len(issues) - errs

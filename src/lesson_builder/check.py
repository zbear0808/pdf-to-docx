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


def _all_items(lesson: LessonSpec):
    for _, it in lesson.items():
        yield it
    if lesson.practice:
        for r in lesson.practice.rows:
            yield from r.cells


def placed_widths(lesson: LessonSpec, figures: dict) -> dict[str, list[tuple[str, float, str]]]:
    """{figure name: [(item label, printed width in inches, 'student'|'key')]} for registered figures."""
    out: dict[str, list] = {}

    def add(name, w, label, which):
        r = figures.get(name or "")
        if not r:
            return
        drawn = (r.get("meta") or {}).get("width_in")
        out.setdefault(name, []).append((label, float(w) if w else drawn, which))

    for it in _all_items(lesson):
        label = f"item {it.n}" if it.n else "unnumbered item"
        add(it.figure, it.fig_w, label, "student")
        if it.key_figure:
            add(it.key_figure, it.fig_w, label, "key")
        if it.draw and it.draw.key_figure:
            add(it.draw.key_figure, it.draw.key_fig_w, label, "key")
    return out


MIN_PT, WARN_PT = 7.0, 8.0
MIN_BOX_W = 0.9   # inches: narrowest fill-in box a student can write in (handout-release-check)


def _box_issues(it: Item | Part, label: str) -> list[str]:
    out = []
    if it.fill and it.box_w < MIN_BOX_W:
        out.append(f"ERROR {label}: fill box_w {it.box_w:g} in; the minimum is {MIN_BOX_W:g}")
    if it.frame:
        widths = [float(r[3]) if len(r) > 3 and r[3] is not None else it.frame_box_w for r in it.frame]
        if min(widths) < MIN_BOX_W:
            out.append(f"ERROR {label}: frame box width {min(widths):g} in; the minimum is {MIN_BOX_W:g}")
    return out


def check_guide_text(md: str, where: str) -> list[str]:
    """Punctuation the guide renderer must never produce."""
    out = []
    for m in re.finditer(r"[.?!:][;,]|;;", md):
        ctx = md[max(0, m.start() - 25):m.end() + 15].replace("\n", " ")
        out.append(f"WARN  {where} teacher guide: odd punctuation: ...{ctx}...")
    for line in md.splitlines():
        segs = line.split("**")
        for k in range(2, len(segs), 2):   # text right after a closing **
            if segs[k][:1].isalnum() or segs[k][:1] == "$":
                out.append(f"WARN  {where} teacher guide: missing space after bold: ...**{segs[k - 1][-20:]}**"
                           f"{segs[k][:15]}...")
    return out


def check_figures(lesson: LessonSpec, figures: dict) -> list[str]:
    """Label lint from the figure renders, and printed text size at the width each item places the figure."""
    issues = []
    where = lesson.id
    for name, uses in placed_widths(lesson, figures).items():
        meta = figures[name].get("meta") or {}
        for msg in meta.get("lint", []):
            issues.append(f"WARN  {where} figure {name}: {msg} (move it, enlarge the figure, or set fixed=True)")
        drawn, pt = meta.get("width_in"), meta.get("min_text_pt")
        if not drawn or not pt:
            continue
        for label, w, which in uses:
            if not w:
                continue
            printed = pt * w / drawn
            if printed < WARN_PT:
                need = drawn * 9 / pt
                level = "ERROR" if printed < MIN_PT else "WARN "
                issues.append(f"{level} {where} {label}: figure {name} text prints at {printed:.1f} pt "
                              f"(placed {w:.2f} in, drawn {drawn:.2f} in); use fig_w >= {need:.1f} or larger labels")
    return issues


def check_assets(lesson: LessonSpec, unit_dir: Path) -> list[str]:
    """Image files (not registered figures): colour on student copies and print resolution."""
    import numpy as np
    from PIL import Image
    issues = []
    for it in _all_items(lesson):
        ref = it.figure
        if not ref or not re.search(r"\.(png|jpe?g|gif|bmp)$", ref, re.I):
            continue
        p = Path(ref) if Path(ref).is_absolute() else unit_dir / ref
        if not p.exists():
            continue
        label = f"{lesson.id} item {it.n}" if it.n else lesson.id
        with Image.open(p) as im:
            rgb = np.asarray(im.convert("RGB"), dtype=np.int16)
            w_px = im.width
        sat = rgb.max(-1) - rgb.min(-1)
        frac = float((sat > 60).mean())
        if frac > 0.002:
            issues.append(f"WARN  {label}: {p.name} has colour ({frac:.1%} of pixels); student copies print black "
                          "and white. Redraw it or convert to grayscale")
        if it.fig_w:
            dpi = w_px / it.fig_w
            if dpi < 150:
                issues.append(f"WARN  {label}: {p.name} prints at {dpi:.0f} dpi (under 150); it will look blurry")
    return issues


def check_spec(unit: UnitSpec, lesson: LessonSpec, figures: dict | None = None) -> list[str]:
    figures = figures or {}
    issues = check_figures(lesson, figures)
    if unit.dir:
        issues += check_assets(lesson, unit.dir)
    where = f"{lesson.id}"
    if lesson.doc_type == "lesson":
        if lesson.minutes > unit.budget.minutes:
            issues.append(f"ERROR {where}: item minutes add up to {lesson.minutes:g}; budget is {unit.budget.minutes}")
        plan_end = [int(m.group(1)) for m in re.finditer(r"^\|\s*\d+\s*-\s*(\d+)\s*\|", lesson.plan, re.M)]
        if plan_end and max(plan_end) > unit.budget.minutes:
            issues.append(f"ERROR {where}: plan timing table runs to {max(plan_end)} min")
        if not lesson.notes_title or not lesson.framing:
            issues.append(f"ERROR {where}: lessons need notes_title and framing")
    if lesson.doc_type == "assessment" and lesson.total_points is not None and lesson.points != lesson.total_points:
        issues.append(f"ERROR {where}: item points add up to {lesson.points:g}, total_points is "
                      f"{lesson.total_points:g}")
    for _, it in lesson.items():
        if it.choices and len(it.choices) > 10:
            issues.append(f"ERROR {where} item {it.n}: {len(it.choices)} choices; the most is 10 (A-J)")
    needs_answers = lesson.doc_type != "reference"

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
                issues += _box_issues(part, plabel)
                for t in _texts(part) + as_list(part.answer):
                    if str(t).count("$") % 2:
                        issues.append(f"ERROR {plabel}: odd number of '$' in {str(t)[:50]!r}; math is $...$ "
                                      "(write dollars as 'dollars' or \\$)")
                for m in re.finditer(r"\bProblems?\s+(\d+)(?:\s*-\s*(\d+))?", text):
                    for k in {m.group(1), m.group(2) or m.group(1)}:
                        if k not in nums:
                            issues.append(f"ERROR {plabel}: refers to Problem {k}, which isn't in this part")
                for m in re.finditer(r"(claim|answer|work|result) from Problem (\d+)", text, re.I):
                    issues.append(f"WARN  {plabel}: '{m.group(0)}': make sure Problem {m.group(2)} supports this")
                if needs_answers and not _has_answer(part) and not (isinstance(part, Item) and part.parts):
                    issues.append(f"ERROR {plabel}: no answer (add `answer:` or `no_answer: true`)")
            text = " ".join(t for p in [it] + list(it.parts) for t in _texts(p))
            if needs_answers and DRAW.search(text) and not re.search(r"if it helps|optional", text, re.I):
                has_key_fig = bool(it.key_figure or (it.draw and (it.draw.key_figure or it.figure))
                                   or figures.get(it.figure or "", {}).get("key"))
                if not has_key_fig:
                    issues.append(f"ERROR {label}: drawing task without a key figure (key_figure, draw.key_figure, "
                                  "or a registered figure with an answer layer)")
    if needs_answers:
        from .render import guide_markdown
        issues += check_guide_text(guide_markdown(lesson), where)
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
                if "___" in txt and not re.search(r"Name|Period|Per\b|Score", txt):
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

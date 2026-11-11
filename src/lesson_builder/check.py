"""Release checks. Spec checks read the lesson YAML; output checks read the rendered PDFs."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from statistics import median

from .numbering import spec_groups, unresolved
from .spec import Item, LessonSpec, Part, UnitSpec, as_list
from .voice import prose, voice_issues

DRAW = re.compile(r"(?:^|[.:]\s+|\b(?:then|and)\s+)(draw|sketch|construct|mark|shade|plot|graph)\b", re.I)
IMG = re.compile(r"\.(png|jpe?g|gif|bmp|svg)$", re.I)
PROBLEM = re.compile(r"\bProblems?\s+(\d+)(?:\s*-\s*(\d+))?")
NOTA = re.compile(r"\b(all|none) of the (above|choices|these)\b|\b(both|neither) \(?[A-D]\)? (and|nor|or) \(?[A-D]\)?"
                  r"|^\(?[A-D]\)? (and|or) \(?[A-D]\)?$", re.I)
TRUE_FALSE = ({"true", "false"}, {"yes", "no"})


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


def _labeled(lesson: LessonSpec):
    """(label, item) for section items, then practice cells."""
    for _, it in lesson.items():
        yield f"item {it.n or '(unnumbered)'}", it
    if lesson.practice:
        for r in lesson.practice.rows:
            for it in r.cells:
                yield f"practice item {it.n or '(unnumbered)'}", it


def _with_parts(it: Item, label: str):
    yield it, label
    for p in it.parts:
        yield p, f"{label} part {p.label}"


def draw_key_width(d, figures: dict, ref: str | None = None) -> float | None:
    """Printed width of a draw item's key figure: key_fig_w, except that an actual-size figure prints at its
    drawn width (None) unless key_fig_w is set explicitly."""
    meta = (figures.get(ref or d.key_figure or "") or {}).get("meta") or {}
    if meta.get("actual_size") and "key_fig_w" not in d.model_fields_set:
        return None
    return d.key_fig_w


def placed_widths(lesson: LessonSpec, figures: dict, explicit: bool = False) -> dict[str, list[tuple[str, float, str]]]:
    """{figure name: [(item label, printed width in inches, 'student'|'key')]} for registered figures. A use
    without fig_w / fig prints at the drawn width; explicit=True leaves those uses out."""
    out: dict[str, list] = {}

    def add(name, w, label, which):
        r = figures.get(name or "")
        if not r or (explicit and not w):
            return
        drawn = (r.get("meta") or {}).get("width_in")
        out.setdefault(name, []).append((label, float(w) if w else drawn, which))

    for it in lesson.all_items():
        label = f"item {it.n}" if it.n else "unnumbered item"
        add(it.figure, it.width, label, "student")
        if it.key_figure:
            add(it.key_figure, it.width, label, "key")
        if it.draw and it.draw.key_figure:
            add(it.draw.key_figure, draw_key_width(it.draw, figures), label, "key")
    if lesson.notes_figure:
        add(lesson.notes_figure, lesson.notes_fig_w, "QuickNotes", "student")
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
        if meta.get("actual_size"):
            for label, w, which in placed_widths(lesson, {name: figures[name]}, explicit=True).get(name, []):
                if drawn and abs(w - drawn) > 0.01:
                    issues.append(f"ERROR {where} {label}: figure {name} is drawn at actual size "
                                  f"(1 unit = 1 {meta['actual_size']}) but fig_w/fig prints it at {w:.2f} in "
                                  f"instead of {drawn:.2f} in ({100 * w / drawn:.0f}%); delete fig_w/fig")
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
    for it in lesson.all_items():
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
        if it.width:
            dpi = w_px / it.width
            if dpi < 150:
                issues.append(f"WARN  {label}: {p.name} prints at {dpi:.0f} dpi (under 150); it will look blurry")
    return issues


def _student_texts(lesson: LessonSpec) -> list[tuple[str, str]]:
    """(where, text) for everything printed on the student copies."""
    out = [("title", lesson.title), ("framing", lesson.framing), ("directions", lesson.directions)]
    for s in lesson.sections:
        sec = f"{s.kind} section"
        out += [(f"{sec} title", s.title), (f"{sec} sub", s.sub), (f"{sec} intro", s.intro)]
        out += [(f"{sec} box", t) for t in as_list(s.box)] + [(f"{sec} bank", t) for t in s.bank]
    for label, it in _labeled(lesson):
        for p, pl in _with_parts(it, label):
            out += [(pl, t) for t in as_list(p.prompt)]
            out += [(f"{pl} choice {chr(65 + k)}", c) for k, c in enumerate(p.choices or [])]
            out += [(f"{pl} fill label", r[0]) for r in p.fill or []]
            out += [(f"{pl} frame", str(x)) for r in p.frame or [] for x in r[:3:2]]
        out += [(f"{label} step", t) for t in it.steps]
        out += [(f"{label} table", t) for t in ([it.table.row_label] + it.table.header if it.table else [])]
        out += [(f"{label} columns", t) for t in (it.columns.headers if it.columns else [])]
    for q in lesson.quicknotes:
        out += [("quicknotes", t) for t in ([q] if isinstance(q, str) else [q.title or ""] + q.bullets)]
    if lesson.practice:
        out += [("practice title", lesson.practice.title)] + [("practice heading", r.heading)
                                                              for r in lesson.practice.rows]
    return [(w, t) for w, t in out if t]


def _answer_letters(p: Item | Part) -> list[str]:
    """Leading [B] or [B], [C], [E] of the first answer line."""
    m = re.match(r"\s*\[[A-Z]\](?:\s*(?:,|and)\s*\[[A-Z]\])*", (as_list(p.answer) or [""])[0])
    return re.findall(r"\[([A-Z])\]", m.group(0)) if m else []


def _printed_len(s: str) -> int:
    """Rough printed length of a choice: a fraction counts as its longer part, a command (\\angle) as one
    symbol, and $ { } ^ _ as nothing, so '$\\frac{5}{3}$' is about as long as '15'."""
    s = re.sub(r"\\[dt]?frac\s*\{([^{}]*)\}\s*\{([^{}]*)\}", lambda m: max(m.group(1), m.group(2), key=len), s)
    s = re.sub(r"\\[A-Za-z]+\s*", "#", s)
    return len(re.sub(r"[${}^_]", "", s))


def _mc_issues(p: Item | Part, label: str) -> tuple[list[str], list[str]]:
    """(issues, key letters) for an item or part with choices (assessment-builder item-rules section 2)."""
    raw = [str(c).strip() for c in p.choices]
    n, out = len(raw), []
    key = re.findall(r"[A-Z]", p.key or "")
    ans = _answer_letters(p)
    letters = key or ans
    select_all = p.select_all or len(letters) > 1 or re.search(r"select\W+all|choose\W+all|all that apply",
                                                                " ".join(as_list(p.prompt)), re.I)
    if not 3 <= n <= 4 and not select_all and not (n == 2 and {c.lower().rstrip(".") for c in raw} in TRUE_FALSE):
        out.append(f"WARN  {label}: {n} choices; use 3 or 4")
    if any(not c for c in raw):
        out.append(f"ERROR {label}: empty choice")
    dup = [c for c, k in Counter(c.lower() for c in raw if c).items() if k > 1]
    if dup:
        out.append(f"ERROR {label}: duplicate choices {dup}")
    for k, c in enumerate(raw):
        if NOTA.search(prose(c).strip()):
            out.append(f"ERROR {label}: choice {chr(65 + k)} {c!r}: no 'all/none of the above' or combined choices")
    lens = [_printed_len(c) for c in raw]
    med = median(lens) if lens else 0
    if n >= 3 and max(lens) > 2 * med and max(lens) - med >= 10:
        k = lens.index(max(lens))
        out.append(f"WARN  {label}: choice {chr(65 + k)} is over twice the median choice length; the key may stand out")
    if key and ans and set(key) != set(ans):
        out.append(f"ERROR {label}: key {p.key} but the answer starts with {', '.join(f'[{a}]' for a in ans)}")
    bad = [x for x in letters if ord(x) - 65 >= n]
    if bad:
        out.append(f"ERROR {label}: key letter {', '.join(bad)} is outside the choices A-{chr(64 + n)}")
    return out, letters


def _key_pattern(seq: list[tuple[str, str]], where: str) -> list[str]:
    """seq: (label, letter) for single-answer MC in print order."""
    out = []
    if len(seq) >= 4:
        letter, k = Counter(x for _, x in seq).most_common(1)[0]
        if k > len(seq) / 2:
            out.append(f"WARN  {where}: {letter} is the key on {k} of {len(seq)} multiple-choice items; vary it")
    for i in range(2, len(seq)):
        if seq[i][1] == seq[i - 1][1] == seq[i - 2][1] and (i == 2 or seq[i - 3][1] != seq[i][1]):
            out.append(f"WARN  {where}: key {seq[i][1]} three times in a row ({seq[i - 2][0]} to {seq[i][0]})")
    return out


def _target_issues(unit: UnitSpec, lesson: LessonSpec, where: str) -> list[str]:
    ids = Counter(t.id for t in unit.targets + lesson.targets)
    out = [f"ERROR {where}: target id {t} is defined {k} times (unit and document targets)"
           for t, k in ids.items() if k > 1]
    used = set()
    tagged = [(f"{s.kind} section", s.target) for s in lesson.sections]
    tagged += [(pl, p.target) for label, it in _labeled(lesson) for p, pl in _with_parts(it, label)]
    for loc, t in tagged:
        if t:
            used.add(t)
            if t not in ids:
                out.append(f"ERROR {where} {loc}: target {t!r} isn't in the unit or document targets")
    if lesson.doc_type == "assessment":
        out += [f"WARN  {where}: target {t.id} has no items" for t in (lesson.targets or unit.targets)
                if t.id not in used]
    dem = [p.demand for label, it in _labeled(lesson) for p, _ in _with_parts(it, label) if p.demand]
    if len(dem) >= 4 and set(dem) <= {"mem", "pwoc"}:
        out.append(f"WARN  {where}: all {len(dem)} items with `demand` are mem/pwoc (all procedural); "
                   "add a pwc or dm item")
    return out


def _unresolved_refs(lesson: LessonSpec, where: str) -> list[str]:
    out = []

    def walk(v, path):
        if isinstance(v, str):
            out.extend(f"ERROR {where} {path}: {r}: unknown id" for r in unresolved(v))
        elif isinstance(v, list):
            for k, x in enumerate(v):
                walk(x, f"{path}[{k}]")
        elif isinstance(v, dict):
            for k, x in v.items():
                if k not in ("id", "figure", "key_figure"):
                    walk(x, f"{path}.{k}" if path else k)
    walk(lesson.model_dump(), "")
    return out


def _dollar_issues(t: str, label: str) -> list[str]:
    out = []
    if t.count("$") % 2:
        out.append(f"ERROR {label}: odd number of '$' in {t[:50]!r}; math is $...$ (write money as '3 dollars')")
    for m in re.finditer(r"\$([^$]*)\$", t):
        c = m.group(1)
        if re.match(r"\d[\d.,]*\s+[A-Za-z]{2,}\b", c) or re.fullmatch(r"\d[\d.,]*\s*,?\s+", c):
            out.append(f"WARN  {label}: {m.group(0)!r} looks like money, not math; write '3 dollars'")
    return out


def _block_primes(raw: str, where: str) -> list[str]:
    """`''` inside a | or > block scalar is two quote marks (prints a double prime), not an apostrophe."""
    out, indent = [], None
    for n, line in enumerate(raw.splitlines(), 1):
        ind = len(line) - len(line.lstrip(" "))
        if indent is not None:
            if not line.strip() or ind > indent:
                if "''" in line:
                    out.append(f"WARN  {where} line {n}: '' in a block scalar prints a double prime; write A' "
                               "inside block scalars")
                continue
            indent = None
        if not line.lstrip().startswith("#") and re.search(r"(?:^|:|-)\s*[|>][-+0-9]*\s*(?:#.*)?$", line.rstrip()):
            indent = ind
    return out


def _figure_refs(unit: UnitSpec, lesson: LessonSpec, figures: dict | None, where: str) -> list[str]:
    """Names that are neither registered figures nor files. figures=None (not rendered): only path-like names."""
    out = []
    refs = [(label, it, (it.figure, it.key_figure, it.draw.key_figure if it.draw else None))
            for label, it in _labeled(lesson)]
    if lesson.notes_figure:
        refs.append(("QuickNotes", None, (lesson.notes_figure,)))
    for label, _it, names in refs:
        for name in names:
            if not name or (figures is not None and name in figures):
                continue
            pathlike = "/" in name or "\\" in name or IMG.search(name)
            if (pathlike and not unit.dir) or (not pathlike and figures is None):
                continue
            if unit.dir and (unit.dir / name).exists():
                continue
            out.append(f"ERROR {where} {label}: figure '{name}' is not a registered figure or a file under the "
                       "unit folder")
    return out


def check_spec(unit: UnitSpec, lesson: LessonSpec, figures: dict | None = None) -> list[str]:
    figs_given, figures = figures, figures or {}
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
    if lesson.header_right:
        issues.append(f"WARN  {where}: header_right is deprecated; the builder prints Name / Per / Score")
    issues += _figure_refs(unit, lesson, figs_given, where)
    issues += _target_issues(unit, lesson, where)
    issues += _unresolved_refs(lesson, where)
    issues += _block_primes(lesson.raw, where)
    for k, line in enumerate(lesson.raw.splitlines(), 1):
        if re.search(r"\bTODO\b", line) and not line.lstrip().startswith("#"):
            issues.append(f"WARN  {where} line {k}: unfilled TODO placeholder")
    for loc, t in _student_texts(lesson):
        issues += [f"WARN  {where} {loc}: {m}" for m in voice_issues(t)]

    groups = spec_groups(lesson)   # numbering restarts on the QuickNotes page; practice is its own group
    pi = len(groups) - 1 if lesson.practice else -1
    notes_items = [it for s in lesson.sections if s.kind == "notes" for it in s.items]
    if notes_items:
        groups.append(notes_items)
    all_nums = {it.n for g in groups for it in g if it.n}
    for name in ("plan", "guide_notes"):
        bad = {k for m in PROBLEM.finditer(getattr(lesson, name)) for k in {m.group(1), m.group(2) or m.group(1)}}
        for k in sorted(bad - all_nums, key=int):
            issues.append(f"WARN  {where} {name}: refers to Problem {k}, which isn't in this document")
    if lesson.practice and isinstance(lesson.practice.selected, list):
        cells = {it.n for r in lesson.practice.rows for it in r.cells if it.n}
        for e in lesson.practice.selected:
            k = str(e[0] if isinstance(e, list) else e)
            if k not in cells and (re.match(r"\d+", k) or [None])[0] not in cells:
                issues.append(f"ERROR {where} practice selected: {k} isn't a numbered practice item")

    seqs: dict[bool, list] = {False: [], True: []}   # single-letter MC keys: handout, practice
    for gi, g in enumerate(groups):
        nums = {it.n for it in g if it.n}
        in_practice = gi == pi
        keys = seqs[in_practice]
        for it in g:
            label = f"{where} {'practice ' if in_practice else ''}item {it.n or '(unnumbered)'}"
            for part in [it] + list(it.parts):
                plabel = label + (f" part {part.label}" if isinstance(part, Part) else "")
                text = " ".join(_texts(part))
                if "___" in text:
                    issues.append(f"ERROR {plabel}: '___' blank; use fill/frame boxes")
                issues += _box_issues(part, plabel)
                for t in _texts(part) + as_list(part.answer):
                    issues += _dollar_issues(str(t), plabel)
                if part.choices:
                    mc, letters = _mc_issues(part, plabel)
                    issues += mc
                    if len(letters) == 1:
                        keys.append((plabel.removeprefix(where + " "), letters[0]))
                for m in PROBLEM.finditer(text):
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
    issues += _key_pattern(seqs[False], where) + _key_pattern(seqs[True], f"{where} practice")
    if needs_answers:
        from .integrity import answer_cues
        from .render import guide_markdown
        issues += answer_cues(lesson, figures, where)
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
                if bold and re.fullmatch(r"\d{1,3}\.", t) and not _red(s["color"]):
                    out.append(dict(page=pi, kind="num", text=t, x=s["bbox"][0], y=s["bbox"][1]))
                elif re.fullmatch(r"[a-z]\.", t) and not _red(s["color"]):
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


ANCHOR_TOL_PT = 0.5   # student/key item labels may differ by this much (PDF points) before it is an error
SIZE_TOL_MM = 0.3     # actual-size figures: printed width may differ from drawn width by this much


def anchor_drift(ls: list[dict], lk: list[dict], tag: str, tol: float = ANCHOR_TOL_PT) -> list[str]:
    """Each item and part label must start at the same spot on the student copy and the key. One ERROR per
    page, at the first label that moved: the item above it takes a different height on the key."""
    sig = lambda L: [(l["page"], l["kind"], l["text"]) for l in L]  # noqa: E731
    if sig(ls) != sig(lk):   # part labels differ (e.g. a part printed only on one copy): compare item numbers
        ls, lk = [l for l in ls if l["kind"] == "num"], [l for l in lk if l["kind"] == "num"]
    out, seen, item = [], set(), None
    for a, b in zip(ls, lk):
        if a["kind"] == "num":
            item = a["text"].rstrip(".")
        dy, dx = b["y"] - a["y"], b["x"] - a["x"]
        if a["page"] in seen or (abs(dy) <= tol and abs(dx) <= tol):
            continue
        seen.add(a["page"])
        later = sum(1 for m, n in zip(ls, lk) if m["page"] == a["page"] and m["y"] > a["y"] + 1
                    and (abs(n["y"] - m["y"]) > tol or abs(n["x"] - m["x"]) > tol))
        what = f"item {item}" + (f" part {a['text']}" if a["kind"] == "part" else "")
        move = []
        if abs(dy) > tol:
            move.append(f"{abs(dy):.1f} pt {'lower' if dy > 0 else 'higher'}")
        if abs(dx) > tol:
            move.append(f"{abs(dx):.1f} pt {'right' if dx > 0 else 'left'}")
        tail = f" ({later} more below it on this page)" if later else ""
        out.append(f"ERROR {tag} key p{a['page'] + 1}: {what} starts {' and '.join(move)} than on the student copy "
                   f"(limit {tol:g} pt){tail}; the content above it has a different height on the key (answer "
                   "text, a larger key figure)")
    return out


def _png_in(path) -> tuple[float, float]:
    from PIL import Image

    from .figures.core import DPI
    with Image.open(path) as im:
        return im.width / DPI, im.height / DPI


def actual_size_issues(s, k, actual: list, tag: str, tol_mm: float = SIZE_TOL_MM) -> list[str]:
    """Figures drawn at actual size (Figure(actual_size=...)) must print at their drawn width, so a ruler on
    the paper reads the lengths the figure was drawn with. Finds each figure by its aspect ratio and size."""
    out = []
    for name, spng, kpng in actual:
        for which, doc, png in (("student", s, spng), ("key", k, kpng)):
            if png is None:
                continue
            w_in, h_in = _png_in(png)
            found = []
            for pi, pg in enumerate(doc):
                for info in pg.get_image_info():
                    x0, y0, x1, y1 = info["bbox"]
                    w, h = (x1 - x0) / 72, (y1 - y0) / 72
                    if h > 0 and abs(w / h - w_in / h_in) <= 0.015 * (w_in / h_in) and 0.6 <= w / w_in <= 1.4:
                        found.append((pi, w))
            if not found:
                out.append(f"WARN  {tag} {which}: actual-size figure {name} ({w_in * 25.4:.1f} mm wide) not found "
                           "in the PDF to measure")
            for pi, w in found:
                err = abs(w - w_in) * 25.4
                if err > tol_mm:
                    out.append(f"ERROR {tag} {which} p{pi + 1}: actual-size figure {name} prints {w * 25.4:.1f} mm "
                               f"wide ({100 * w / w_in:.1f}%), drawn {w_in * 25.4:.1f} mm; remove fig_w/fig so it "
                               "prints at its drawn width")
    return out


def actual_figures(lesson: LessonSpec, figures: dict) -> dict[str, list[tuple[str, Path | None, Path | None]]]:
    """{"handout" | "practice": [(figure name, PNG on the student copy or None, PNG on the key or None)]} for
    figures drawn at actual size, as each copy prints them."""
    out: dict[str, dict] = {"handout": {}, "practice": {}}

    def add(group, name, student, key):
        r = figures.get(name or "")
        if not r or not (r.get("meta") or {}).get("actual_size"):
            return
        s, k = out[group].get(name, (None, None))
        out[group][name] = (s or (r["student"] if student else None),
                            k or ((r.get("key") or r["student"]) if key else None))

    groups = [("handout", it) for _, it in lesson.items()]
    groups += [("practice", it) for r in (lesson.practice.rows if lesson.practice else []) for it in r.cells]
    for g, it in groups:
        if it.draw:   # the drawing box: the key shows the answer figure, the student copy shows nothing
            add(g, it.draw.key_figure or it.key_figure or it.figure, False, True)
            continue
        add(g, it.figure, True, not it.key_figure)
        add(g, it.key_figure, False, True)
    add("handout", lesson.notes_figure, True, True)
    return {g: [(n, s, k) for n, (s, k) in v.items()] for g, v in out.items()}


def _key_texts(lesson: LessonSpec) -> dict[str, list[tuple[str, str]]]:
    """{"handout" | "practice": [(label, text)]}: answer text the key prints (answers, rubrics, box answers)."""
    from .render import _answer_lines, _rubric_lines
    out: dict[str, list] = {"handout": [], "practice": []}
    groups = [("handout", "item", it) for _, it in lesson.items()]
    groups += [("practice", "practice item", it) for r in (lesson.practice.rows if lesson.practice else [])
               for it in r.cells]
    for g, pre, it in groups:
        for o, lab in _with_parts(it, f"{pre} {it.n or '(unnumbered)'}"):
            texts = _answer_lines(o) + _rubric_lines(o) + [str(r[1]) for r in o.fill or [] if len(r) > 1]
            texts += [str(r[1]) for r in o.frame or [] if len(r) > 1]
            if isinstance(o, Item):
                texts += (o.table.answers if o.table else []) + [a for c in (o.columns.answers if o.columns else [])
                                                                 for a in c]
                texts += [o.draw.key_note] if o.draw and o.draw.key_note else []
            out[g] += [(lab, t) for t in texts if t]
    return out


def _probe(text: str) -> str | None:
    """The last two words of the last run of plain words (no math) in an answer, lower case, or None."""
    for seg in reversed(re.split(r"\$[^$]*\$", str(text))):
        words = re.findall(r"[a-z]+", seg.lower())
        if len(words) >= 2:
            return " ".join(words[-2:])
    return None


def clipped_answers(lesson: LessonSpec, key_pdf, group: str, tag: str) -> list[str]:
    """Word drops lines that overflow an exact-height box from the PDF. Each answer's closing words must be in
    the key's red text."""
    import pymupdf
    words = []
    with pymupdf.open(key_pdf) as doc:
        for pg in doc:
            for b in pg.get_text("dict")["blocks"]:
                for ln in b.get("lines", []):
                    words += [w for s in ln["spans"] if _red(s["color"]) for w in re.findall(r"[a-z]+", s["text"].lower())]
    stream = f" {' '.join(words)} "
    out = []
    for lab, text in _key_texts(lesson)[group]:
        probe = _probe(text)
        if probe and f" {probe} " not in stream:
            out.append(f"ERROR {tag} key: {lab}: the answer's last words ({probe!r}) are not on the key; the box "
                       f"is too short and Word cut the text off: {str(text)[:70]!r}")
    return out


def no_answer_labels(lesson: LessonSpec) -> dict[str, set[str]]:
    """{"handout" | "practice": {"7.", ...}}: numbered items marked `no_answer: true` with no answer text."""
    out = {"handout": set(), "practice": set()}
    groups = [("handout", it) for _, it in lesson.items()]
    groups += [("practice", it) for r in (lesson.practice.rows if lesson.practice else []) for it in r.cells]
    for g, it in groups:
        if it.n and it.no_answer and not as_list(it.answer) and not it.parts:
            out[g].add(f"{it.n}.")
    return out


def _frames(doc) -> list[list[tuple]]:
    """Per page: black or gray vector rectangles and rules (box borders, table lines), as rounded tuples. Red
    key drawings are left out."""
    out = []
    for pg in doc:
        rows = []
        for d in pg.get_drawings():
            c = d.get("color") or d.get("fill")
            if c and c[0] > 0.6 and c[1] < 0.3 and c[2] < 0.3:
                continue
            r = d["rect"]
            if r.width < 3 and r.height < 3:
                continue
            rows.append((round(r.x0, 1), round(r.y0, 1), round(r.x1, 1), round(r.y1, 1)))
        out.append(sorted(rows, key=lambda t: (t[1], t[0])))
    return out


def frame_drift(s, k, tag: str, tol: float = ANCHOR_TOL_PT) -> list[str]:
    """Answer boxes and rules must sit at the same spot on both copies (catches a shift inside an item, which
    the label check can't see). Each student box is matched to the key box of the same size and x position
    nearest in y; the key's extra drawings are ignored. One ERROR per page, at the first box that moved."""
    out = []
    for pi, (a, b) in enumerate(zip(_frames(s), _frames(k))):
        for x in a:
            w, h = x[2] - x[0], x[3] - x[1]
            same = [y for y in b if abs(y[0] - x[0]) <= tol and abs((y[2] - y[0]) - w) <= tol
                    and abs((y[3] - y[1]) - h) <= tol]
            if not same:
                continue
            y = min(same, key=lambda t: abs(t[1] - x[1]))
            dy = y[1] - x[1]
            if abs(dy) > tol:
                out.append(f"ERROR {tag} key p{pi + 1}: the box or rule at y={x[1] / 72:.2f} in is {abs(dy):.1f} pt "
                           f"{'lower' if dy > 0 else 'higher'} on the key (limit {tol:g} pt); something above it in "
                           "the same item is taller on the key (a key-only figure or note)")
                break
    return out


def check_outputs(student: Path, key: Path, max_pages: int, actual: list | None = None,
                  no_answer: set | None = None) -> list[str]:
    """actual: [(figure name, student png, key png or None)] for figures drawn at actual size.
    no_answer: item labels ("7.") whose YAML says `no_answer: true`; the key needs no red answer for them."""
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
    else:
        issues += anchor_drift(ls, lk, tag)
        if not any(i.startswith(f"ERROR {tag} key") for i in issues):   # one cause, one report
            issues += frame_drift(s, k, tag)
    if actual:
        issues += actual_size_issues(s, k, actual, tag)
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
            if l["kind"] == "num" and l["text"] in (no_answer or set()):
                continue
            si = [i for i in simg.get(pi, []) if x0 - 5 <= i["bbox"][0] < x1 and l["y"] <= i["bbox"][1] < y1]
            if not _answered(pg, x0, x1, l["y"] - 2, y1, len(si)):
                issues.append(f"ERROR {tag} key p{pi + 1}: no answer for {l['text']} near y={l['y'] / 72:.1f} in")
    return issues


def summarize(issues: list[str]) -> tuple[int, int]:
    errs = sum(i.startswith("ERROR") for i in issues)
    return errs, len(issues) - errs

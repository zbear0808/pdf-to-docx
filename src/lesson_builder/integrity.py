"""Exam integrity (tooling plan T3): parallel forms (A, B, Retake) must not share letters, numbers, or MC key
positions, and a review or notes sheet must not print a test's numbers, angle sets, or answers.

Heuristics, per item (parts folded in): point letters (capitals in math and figure labels), line names
(\\ell, "line $m$"), polygon names (triangle JKL), numbers (ints, decimals, fractions, angles) from the prompt,
choices, box labels, answers, and figure labels. Small numbers 0-2, point values, item/lesson references, years,
and numbers in the document's directions are ignored."""
from __future__ import annotations

import ast
import re
from collections import Counter
from dataclasses import dataclass, field
from fnmatch import fnmatch
from fractions import Fraction
from itertools import combinations
from pathlib import Path

from .spec import Item, LessonSpec, UnitSpec, as_list, load_lesson, load_unit

LABEL_CALLS = {"label", "label_poly", "side_label", "angle_label", "text"}
GENERIC = {frozenset("ABC"), frozenset("DEF"), frozenset("ABCD"), frozenset("XYZ")}   # too common to flag across docs
SMALL = {Fraction(0), Fraction(1), Fraction(2)}
NOT_ANGLES = {Fraction(90), Fraction(180), Fraction(360)}

_PTS = r"(?:\d|\}|\$)\s*\$?\s*(?:pts?|points?)\b"
_PAREN_PTS = re.compile(r"\([^()]*" + _PTS + r"[^()]*\)", re.I)
_SENT_PTS = re.compile(r"[^.!?]*" + _PTS + r"[^.!?]*[.!?]?", re.I)
_REFS = re.compile(r"\b(?:Problems?|Items?|Questions?|Parts?|Steps?|Lessons?|Practice|pages?|p\.)\s*\d+(?:\.\d+)?"
                   r"(?:\s*[-\u2013]\s*\d+(?:\.\d+)?)?|\b(?:19|20)\d\d\b", re.I)
_ANGLE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:\^\s*\{?\s*\\circ\s*\}?|\u00b0)")
_FRAC = re.compile(r"\\[dt]?frac\s*\{\s*(\d+(?:\.\d+)?)\s*\}\s*\{\s*(\d+(?:\.\d+)?)\s*\}|(?<![\d.])(\d+)\s*/\s*(\d+)(?![\d.])")
_EXP = re.compile(r"\^\s*\{?\s*\d+\s*\}?")
_NUM = re.compile(r"(?<![A-Za-z\d.])\d+(?:\.\d+)?")
_MATH = re.compile(r"\$([^$]+)\$")
_VTX = r"[A-Z](?:_(?:\{[A-Za-z0-9]+\}|[A-Za-z0-9]))?"   # a point name: A, A_1, A_{12} (LaTeX subscripts)
_VTX_RE = re.compile(_VTX)
_SUB = re.compile(r"(?<=[A-Za-z'\u2032}])\s*_\s*(?:\{\s*\d+\s*\}|\d)")   # subscript digits are names, not values
_POLY = re.compile(rf"\\triangle\s*((?:{_VTX}['\u2032]*){{3}})|(?:rectangle|quadrilateral|parallelogram|polygon|"
                   rf"square|trapezoid|rhombus|pentagon|hexagon|kite)\s+\$((?:{_VTX}['\u2032]*){{3,}})\$", re.I)
_LINE = re.compile(r"\blines?\s+\$(\\ell|[a-z])['\u2032]*\$|^\s*\$(\\ell|[a-z])['\u2032]*\$\s*$")
_POINTS_ONLY = re.compile(rf"^\$?\s*(?:{_VTX}(?:'|\u2032|\\prime|\^\{{?\\prime\}}?)*\s*)+\$?$")
_KEY = re.compile(r"^\s*((?:(?:and\s+)?\[[A-H]\][,;]?\s*)+)")


@dataclass
class Fingerprint:
    letters: set = field(default_factory=set)     # capital point letters (primes dropped)
    lines: set = field(default_factory=set)       # line names: "l" for \ell, "m", ...
    names: set = field(default_factory=set)       # polygon names as frozensets of letters
    fig_letters: set = field(default_factory=set)  # letters on the item's given figure
    numbers: Counter = field(default_factory=Counter)   # everything printed or answered (multiset)
    raw: Counter = field(default_factory=Counter)       # the same, with 0, 1, 2 kept (exact-copy test)
    shown: set = field(default_factory=set)       # numbers a student sees (prompt, choices, given labels; fractions split)
    values: set = field(default_factory=set)      # test-side givens: prompt, choices, figure labels (whole values)
    answers: set = field(default_factory=set)     # short answers: boxes, keyed choices, answer-layer labels
    angles: set = field(default_factory=set)      # angle measures seen or answered
    key: str | None = None                        # MC key letters, "A,D,E"
    kind: str = ""                                # structure: "mc", "fill", "parts:3", ...
    part: bool = False                            # a part entry ("3a"); its item entry already includes it
    seen_angles: set = field(default_factory=set)  # angles printed or in short answers (not worked solutions)
    keyed: dict = field(default_factory=dict)     # MC key letter -> choice text
    fig_shown: set = field(default_factory=set)   # numbers on the item's own given figure
    prompt_nums: set = field(default_factory=set)  # numbers in the prompt, choices, and box labels


def _clean(s: str) -> str:
    s = _PAREN_PTS.sub(" ", str(s))
    s = _SENT_PTS.sub(" ", s)
    return _REFS.sub(" ", s)


def numbers(s: str, split=False, keep_small=False) -> tuple[list[Fraction], list[Fraction]]:
    """(numbers, angles) in a string. split=True also returns a fraction's numerator and denominator.
    0, 1, and 2 are dropped unless keep_small."""
    s = _SUB.sub(" ", _clean(s))
    angles = [Fraction(m.group(1)) for m in _ANGLE.finditer(s)]
    s = _ANGLE.sub(" ", s)
    out = list(angles)
    for m in _FRAC.finditer(s):
        a, b = (m.group(1), m.group(2)) if m.group(1) else (m.group(3), m.group(4))
        if Fraction(b):
            out.append(Fraction(a) / Fraction(b))
            if split:
                out += [Fraction(a), Fraction(b)]
    s = _EXP.sub(" ", _FRAC.sub(" ", s))
    out += [Fraction(m.group(0)) for m in _NUM.finditer(s)]
    return [x for x in out if keep_small or x not in SMALL], [a for a in angles if a not in NOT_ANGLES]


def _ident(tok: str) -> str:
    """Normalized point name: A_{1} -> A_1."""
    return re.sub(r"[{}\s]", "", tok)


def letters(s: str) -> set[str]:
    """Point names in math: capitals with their subscripts (A_2 and A_7 are different points)."""
    out = set()
    for m in _MATH.finditer(str(s)):
        t = re.sub(r"\\(?:text|mathrm|operatorname|textbf)\s*\{[^}]*\}", " ", m.group(1))
        out |= {_ident(x) for x in _VTX_RE.findall(re.sub(r"\\[A-Za-z]+", " ", t))}
    return out


def lines(s: str) -> set[str]:
    return {("l" if (a or b) == "\\ell" else (a or b)) for a, b in _LINE.findall(str(s))} | (
        {"l"} if "\\ell" in str(s) else set())


def names(s: str) -> set[frozenset]:
    return {frozenset(_ident(v) for v in _VTX_RE.findall(a or b)) for a, b in _POLY.findall(str(s))}


def label_letters(text: str) -> set[str]:
    return {_ident(v) for v in _VTX_RE.findall(text)} if _POINTS_ONLY.match(text.strip()) else set()


def _join(names_: set) -> str:
    """Point names for a message: 'ABC', or 'A_2 B_2 C_2' when any has a subscript."""
    return (" " if any(len(n) > 1 for n in names_) else "").join(sorted(names_))


def fmt(x: Fraction) -> str:
    if x.denominator == 1:
        return str(x.numerator)
    return f"{float(x):g}" if 10 ** 6 % x.denominator == 0 else f"{x.numerator}/{x.denominator}"


# ------------------------------------------------------------------ figure labels
_AST_CACHE: dict = {}


def _str_of(node, consts):
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for v in node.values:
            if isinstance(v, ast.FormattedValue) and isinstance(v.value, ast.Name) and v.value.id in consts:
                parts.append(consts[v.value.id])
            elif isinstance(v, ast.Constant):
                parts.append(str(v.value))
            else:
                return None
        return "".join(parts)
    return None


def ast_labels(path: Path) -> dict[str, list[tuple[str, str]]]:
    """{figure name: [(text, layer)]} from a figures file without running it: every string literal in the
    @figure function except keyword values, docstrings, and assert messages. Strings passed to a label call
    with layer="answer" are answer labels."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    consts = {t.id: n.value.value for n in tree.body if isinstance(n, ast.Assign)
              and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str)
              for t in n.targets if isinstance(t, ast.Name)}
    out = {}
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef):
            continue
        name = next((_str_of(d.args[0], consts) for d in fn.decorator_list if isinstance(d, ast.Call) and d.args
                     and getattr(d.func, "id", getattr(d.func, "attr", "")) == "figure"), None)
        if not name:
            continue
        body = fn.body[1:] if fn.body and isinstance(fn.body[0], ast.Expr) and isinstance(
            getattr(fn.body[0], "value", None), ast.Constant) else fn.body
        skip, answer = set(), set()
        for node in (n for st in body for n in ast.walk(st)):
            if isinstance(node, ast.keyword):
                skip |= {id(x) for x in ast.walk(node.value)}
            elif isinstance(node, ast.Assert) and node.msg is not None:
                skip |= {id(x) for x in ast.walk(node.msg)}
            elif isinstance(node, ast.JoinedStr):
                skip |= {id(x) for x in ast.walk(node)}
            if isinstance(node, ast.Call) and getattr(node.func, "attr", "") in LABEL_CALLS and any(
                    k.arg == "layer" and getattr(k.value, "value", None) == "answer" for k in node.keywords):
                answer |= {id(x) for a in node.args for x in ast.walk(a)}
        out[name] = [(n.value, "answer" if id(n) in answer else "given") for st in body for n in ast.walk(st)
                     if isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in skip]
    return out


def _unit_dir(lesson: LessonSpec) -> Path | None:
    for d in (lesson.path.resolve().parents if lesson.path else []):
        if (d / "unit.yaml").is_file():
            return d
    return None


def _source_index(unit_dir: Path | None) -> dict:
    if unit_dir is None:
        return {}
    files = sorted((unit_dir / "figures").glob("*.py")) + [p for p in [unit_dir / "figures.py"] if p.is_file()]
    stamp = tuple((str(p), p.stat().st_mtime) for p in files)
    if _AST_CACHE.get(unit_dir, (None,))[0] != stamp:
        idx = {}
        for p in files:
            try:
                idx.update(ast_labels(p))
            except (SyntaxError, OSError, UnicodeDecodeError):
                pass
        _AST_CACHE[unit_dir] = (stamp, idx)
    return _AST_CACHE[unit_dir][1]


def figure_labels(name: str, rendered: dict, lesson: LessonSpec) -> list[tuple[str, str]]:
    """[(text, layer)] for a figure: sidecar meta["labels"] / meta["key_labels"] if present, else the source."""
    meta = (rendered.get(name) or {}).get("meta") or {}
    if "labels" in meta or "key_labels" in meta:
        out = []
        for lab in meta.get("labels", []):
            out.append((lab.get("text", ""), lab.get("layer", "given")) if isinstance(lab, dict) else (str(lab), "given"))
        for lab in meta.get("key_labels", []):
            out.append((lab.get("text", "") if isinstance(lab, dict) else str(lab), "answer"))
        return out
    return _source_index(_unit_dir(lesson)).get(name, [])


# ------------------------------------------------------------------ fingerprints
def _texts(o) -> tuple[list[str], list[str], list[str]]:
    """(shown, short answers, answer text) strings of an item or part (not its parts)."""
    shown = as_list(o.prompt) + list(getattr(o, "steps", []) or []) + list(o.choices or [])
    short, long_ = [], as_list(o.answer)
    shown += [r[0] for r in o.fill or []]
    short += [r[1] for r in o.fill or [] if len(r) > 1]
    for r in o.frame or []:
        shown += [str(r[0]), str(r[2]) if len(r) > 2 else ""]
        short.append(str(r[1]))
    for name in ("table", "columns"):
        t = getattr(o, name, None)
        if t is not None:
            shown += list(t.header if name == "table" else t.headers)
            short += list(t.answers) if name == "table" else [a for col in t.answers for a in col]
    draw = getattr(o, "draw", None)
    if draw is not None and draw.key_note:
        long_.append(draw.key_note)
    key = _key(o)
    if key:
        short += [o.choices[ord(k) - 65] for k in re.findall(r"[A-H]", key) if ord(k) - 65 < len(o.choices)]
    return shown, short, long_


def _key(o) -> str | None:
    if not o.choices:
        return None
    if o.key:
        return ",".join(re.findall(r"[A-H]", o.key))
    m = _KEY.match(" ".join(as_list(o.answer)))
    return ",".join(re.findall(r"[A-H]", m.group(1))) if m else None


def _kind(it) -> str:
    if it.parts:
        return f"parts:{len(it.parts)}"
    return next((k for k, v in (("mc", it.choices), ("fill", it.fill), ("frame", it.frame), ("draw", it.draw),
                                ("table", it.table), ("columns", it.columns)) if v), "open")


def _fp(objs, figs: list[tuple[str, str]], skip: set, kind="") -> Fingerprint:
    f = Fingerprint(kind=kind)
    for o in objs:
        shown, short, long_ = _texts(o)
        for s in shown:
            f.letters |= letters(s)
            f.lines |= lines(s)
            f.names |= names(s)
        for group in (shown, short, long_):
            for s in group:
                whole, angs = numbers(s)
                whole = [x for x in whole if x not in skip]
                f.numbers.update(whole)
                f.raw.update(x for x in numbers(s, keep_small=True)[0] if x not in skip)
                f.angles |= set(angs)
                if group is shown:
                    f.seen_angles |= set(angs)
                    f.shown |= {x for x in numbers(s, True)[0] if x not in skip}
                    f.values |= set(whole)
                    f.prompt_nums |= set(whole)
                elif group is short:
                    f.seen_angles |= set(angs)
                    f.answers |= set(whole)
    for text, layer in figs:
        whole, angs = numbers(text)
        whole = [x for x in whole if x not in skip]
        f.numbers.update(whole)
        f.raw.update(x for x in numbers(text, keep_small=True)[0] if x not in skip)
        f.angles |= set(angs)
        f.seen_angles |= set(angs)
        if layer == "answer":
            f.answers |= set(whole)
        else:
            f.letters |= label_letters(text)
            f.fig_letters |= label_letters(text)
            f.shown |= {x for x in numbers(text, True)[0] if x not in skip}
            f.values |= set(whole)
            f.fig_shown |= set(whole)
    return f


def _keyed(o) -> dict[str, str]:
    key = _key(o) or ""
    return {k: re.sub(r"\s+", "", o.choices[ord(k) - 65]) for k in key.split(",") if k and ord(k) - 65 < len(o.choices)}


def _label(it, pos: int) -> str:
    return str(it.n) if it.n is not None else f"#{pos}"


def fingerprint(lesson: LessonSpec, rendered_figs: dict | None = None) -> dict[str, Fingerprint]:
    """{item label: Fingerprint} for every item (parts folded in), plus "<n><part>" entries ("3a") for parts.
    Unnumbered items are "#<position>". QuickNotes are one entry, "notes"."""
    rendered_figs = rendered_figs or {}
    skip = set(numbers(lesson.directions or "")[0])
    out = {}
    for pos, it in enumerate(lesson.all_items(), 1):
        names_ = [n for n in (it.figure, it.key_figure, it.draw.key_figure if it.draw else None) if n]
        figs = []
        for n in names_:
            labs = figure_labels(n, rendered_figs, lesson)
            figs += labs if n == it.figure else [(t, "answer") for t, _ in labs]
        lab = _label(it, pos)
        if lab in out:   # practice items restart numbering
            lab = f"P{lab}"
        out[lab] = _fp([it, *it.parts], figs, skip, _kind(it))
        out[lab].key, out[lab].keyed = _key(it), _keyed(it) if it.choices else {}
        for p in it.parts:
            pf = _fp([p], [], skip, "mc" if p.choices else "")
            pf.key, pf.part, pf.keyed = _key(p), True, _keyed(p) if p.choices else {}
            out[lab + p.label.strip(". )")] = pf
    notes = [b if isinstance(b, str) else " ".join([b.title or ""] + b.bullets) for b in lesson.quicknotes]
    if notes:
        out["notes"] = _fp([Item(prompt=notes)], [], skip, "notes")
    return out


# ------------------------------------------------------------------ checks
def _nums(xs) -> str:
    return ", ".join(fmt(x) for x in sorted(xs))


def _items(fps: dict) -> list[str]:
    return [k for k, v in fps.items() if not v.part and k != "notes"]


def _same_key(a: str, b: str) -> bool:
    return set(a.split(",")) == set(b.split(","))


def compare(a: LessonSpec, b: LessonSpec, rendered_a: dict | None = None, rendered_b: dict | None = None,
            fa: dict | None = None, fb: dict | None = None) -> list[str]:
    """Parallel forms (B vs A, Retake vs A/B). Items are matched by number."""
    fa = fa if fa is not None else fingerprint(a, rendered_a)
    fb = fb if fb is not None else fingerprint(b, rendered_b)
    out = []
    for k in _items(fa):
        if k not in fb or fa[k].kind != fb[k].kind:   # different item here: reported as type drift below
            continue
        x, y, where = fa[k], fb[k], f"{a.stem} item {k} vs {b.stem} item {k}"
        if x.letters and x.letters == y.letters:
            lv = "ERROR" if len(x.letters) >= 3 else "WARN "
            out.append(f"{lv} {where}: same letters {_join(x.letters)}")
        elif x.names & y.names:
            out.append(f"WARN  {where}: same names {', '.join(_join(n) for n in x.names & y.names)}")
        if x.lines and x.lines == y.lines:
            out.append(f"WARN  {where}: same line names {', '.join(sorted(x.lines))}")
        sx, sy = set(x.numbers), set(y.numbers)
        n, common = max(len(sx), len(sy)), sx & sy
        if len(sx) >= 3 and sx == sy:
            exact = x.raw == y.raw or any(v > 10 or (v.denominator > 1 and v.numerator > 1) for v in sx)
            out.append(f"{'ERROR' if exact else 'WARN '} {where}: same numbers {_nums(sx)}")
        elif len(common) >= 3 and len(common) >= 0.6 * n:
            out.append(f"WARN  {where}: {round(100 * len(common) / n)}% of the numbers are shared ({_nums(common)})")
    for k in fa:
        if k in fb and fa[k].keyed and fb[k].keyed:
            dup = sorted(c for c, txt in fa[k].keyed.items() if fb[k].keyed.get(c) == txt)
            if dup and (fa[k].keyed == fb[k].keyed or min(len(fa[k].keyed), len(fb[k].keyed)) == 1):
                out.append(f"WARN  {a.stem} item {k} vs {b.stem} item {k}: same correct choice at "
                           f"{', '.join(f'[{c}]' for c in dup)}")
    keyed = [(k, fa[k].key) for k in fa if k in fb and fa[k].key and fb[k].key]
    same = [(k, ka) for k, ka in keyed if _same_key(ka, fb[k].key)]
    if keyed and len(same) > len(keyed) / 2:
        out.append(f"WARN  {a.stem} vs {b.stem}: MC key in the same position on {len(same)} of {len(keyed)} "
                   f"items ({', '.join(f'{k} [{ka}]' for k, ka in same)})")
    ia, ib = _items(fa), _items(fb)
    if ia != ib:
        out.append(f"WARN  {a.stem} vs {b.stem}: items differ ({' '.join(ia)} vs {' '.join(ib)})")
    drift = [f"{k} {fa[k].kind}/{fb[k].kind}" for k in ia if k in fb and fa[k].kind != fb[k].kind]
    if drift:
        out.append(f"WARN  {a.stem} vs {b.stem}: item types differ: {', '.join(drift)}")
    return out


def do_not_reuse(doc: LessonSpec, others: list[LessonSpec], rendered: dict | None = None,
                 fps: dict | None = None) -> list[str]:
    """A review or notes sheet vs the tests it must not give away. ERROR when a doc item prints every number of
    a test item (3+, angles aside) or all of its angles (2+); WARN when it prints 4+ of them including an
    answer. Reviews (not reference sheets) also WARN on the same figure labels or a non-generic polygon name."""
    fps = fps if fps is not None else {}
    fd = fps.get(doc.stem) or fingerprint(doc, rendered)
    notation_ok = doc.doc_type == "reference"   # notes sheets name things ABC on purpose
    out = []
    for o in others:
        fo = fps.get(o.stem) or fingerprint(o)
        for kd in [k for k, v in fd.items() if not v.part]:
            d = fd[kd]
            seen = (d.shown | d.answers) - d.seen_angles
            for ko in _items(fo):
                t, where = fo[ko], f"{doc.stem} item {kd} vs {o.stem} item {ko}"
                tup = (t.values | t.answers) - t.angles
                shared = tup & seen
                hit = shared & t.answers
                if len(tup) >= 3 and shared == tup:
                    tail = f" (answer {_nums(hit)})" if hit else ""
                    out.append(f"ERROR {where}: prints all of the test item's numbers {_nums(shared)}{tail}")
                elif len(shared) >= 4 and hit:
                    out.append(f"WARN  {where}: prints {len(shared)} of the test item's numbers {_nums(shared)} "
                               f"(answer {_nums(hit)})")
                if len(t.angles) >= 2 and t.angles <= d.seen_angles:
                    out.append(f"ERROR {where}: same angles {'/'.join(fmt(x) for x in sorted(t.angles))}")
                if notation_ok:
                    continue
                if len(t.fig_letters) >= 3 and t.fig_letters == d.fig_letters:
                    out.append(f"WARN  {where}: same figure labels {_join(t.fig_letters)}")
                nm = (t.names & d.names) - GENERIC
                if nm:
                    out.append(f"WARN  {where}: same names {', '.join(_join(n) for n in nm)}")
    return out


def answers_on_figure(lesson: LessonSpec, fps: dict | None = None) -> list[str]:
    """WARN when a short answer (not an angle, not in the prompt) is printed on the item's own figure."""
    fps = fps if fps is not None else fingerprint(lesson)
    out = []
    for k in _items(fps):
        f = fps[k]
        hit = (f.answers & f.fig_shown) - f.prompt_nums - f.angles
        if hit:
            out.append(f"WARN  {lesson.stem} item {k}: answer {_nums(hit)} is printed on the figure")
    return out


# ------------------------------------------------------------------ answer cues inside one document
_PVTX = rf"{_VTX}(?:'|\u2032|\\prime)*"
_SEQ = re.compile(rf"(?<![A-Za-z0-9_'\u2032])((?:{_PVTX}){{3,}})(?![A-Za-z0-9_])")
_PT = rf"{_PVTX}(?:\s*\([^()]*\))?"   # a point, maybe with coordinates: A(1, 2)
_LIST = re.compile(rf"(?<![A-Za-z0-9_])({_PT}(?:\s*(?:,\s*(?:and\s+)?|and\s+){_PT}){{2,}})(?![A-Za-z0-9_])")
_ARROW = re.compile(rf"(?<![A-Za-z0-9_])({_PVTX})\s*\u2192\s*({_PVTX})(?![A-Za-z0-9_])")
_ACRONYMS = {"SAS", "SSS", "ASA", "AAS", "AAA", "SSA", "HL", "MLL", "USA", "LT", "CR", "SR"}


def _vertices(seq: str) -> tuple[str, ...]:
    return tuple(_ident(re.sub(r"\\prime|\u2032", "'", v)) for v in re.findall(_PVTX, seq))


def _flat(text: str) -> str:
    """Math as plain point names: arrows as \u2192, other commands, $ and braces dropped (subscripts kept)."""
    t = re.sub(r"\\(?:to|rightarrow|mapsto|longrightarrow)(?![A-Za-z])", " \u2192 ", str(text).replace("$", " "))
    # angle, segment, and arc names are not polygon names: "angle LPA and angle LQB" states no correspondence
    t = re.sub(r"\\(?:angle|measuredangle|overline|overrightarrow|overleftrightarrow|widehat|stackrel\{\\frown\})"
               r"\s*\{?\s*(?:[A-Z]|_\{?[A-Za-z0-9]+\}?|['\s]|\\prime)+\}?", " ", t)
    t = re.sub(r"_\s*\{\s*([A-Za-z0-9]+)\s*\}", "_\x00\\1\x01", t)
    t = re.sub(r"\\[A-Za-z]+", " ", t)
    return re.sub(r"[{}]", " ", t).replace("\x00", "{").replace("\x01", "}")


def correspondences(text: str) -> set[frozenset]:
    """Vertex correspondences a string states: two point-name sequences in a row ('ABC ~ DEF', 'from NPQ to
    RST', 'taking A(1,1), B(3,1), C(1,2) onto D(...), E(...), F(...)') or two or more arrows ('A -> D, B -> E').
    Each is a frozenset of (from, to) pairs, so 'BCA ~ EFD' states the same correspondence as 'ABC ~ DEF'.
    Primed images (ABC -> A'B'C') state nothing new."""
    t = _flat(text)
    out = set()
    found = [(m.start(), _vertices(m.group(1))) for m in _SEQ.finditer(t) if m.group(1) not in _ACRONYMS]
    found += [(m.start(), _vertices(re.sub(r"\([^()]*\)", " ", m.group(1)))) for m in _LIST.finditer(t)]
    seqs = [v for _, v in sorted(found)]
    for a, b in zip(seqs, seqs[1:]):
        if len(a) == len(b) and a != b and not all(y.rstrip("'") == x.rstrip("'") for x, y in zip(a, b)):
            out.add(frozenset(zip(a, b)))
    arrows = {tuple(_vertices(v)[0] for v in m.groups()) for m in _ARROW.finditer(t)}
    arrows = {(x, y) for x, y in arrows if y.rstrip("'") != x.rstrip("'")}
    if len(arrows) >= 2:
        out.add(frozenset(arrows))
    return out


def _states(shown: set[frozenset], answer: frozenset) -> bool:
    """A shown correspondence gives the answer away: the same pairs, or at least two of them."""
    return any(s <= answer and len(s) >= 2 for s in shown)


def _box_labels(o) -> list[str]:
    return [str(r[0]) for r in o.fill or []] + [str(x) for r in o.frame or [] for x in r[:3:2] if x]


def _prompt_texts(o) -> list[str]:
    return as_list(o.prompt) + list(getattr(o, "steps", []) or [])


def _box_answers(o) -> list[tuple[str, str, str]]:
    """(label text, answer text, label + answer) per box: 'triangle QNP ~' + 'triangle TRS'."""
    out = [(str(r[0]), str(r[1]), f"{r[0]} {r[1]}") for r in o.fill or [] if len(r) > 1]
    return out + [(" ".join(str(x) for x in r[:3:2]), str(r[1]), " ".join(str(x) for x in r[:3]))
                  for r in o.frame or []]


def _answer_texts(o) -> list[str]:
    """Key-only text: worked answers, key notes, and box answers."""
    draw = getattr(o, "draw", None)
    return as_list(o.answer) + [t for *_, t in _box_answers(o)] + (
        [draw.key_note] if draw is not None and draw.key_note else [])


def _ink(path) -> "np.ndarray | None":
    """Ink mask of a figure PNG, cropped to its ink, resized to 128 px, lines thickened to forgive small shifts."""
    import numpy as np
    from PIL import Image, ImageFilter
    try:
        with Image.open(path) as im:
            g = im.convert("L")
    except OSError:
        return None
    mask = g.point(lambda v: 255 if v < 200 else 0)
    box = mask.getbbox()
    if not box:
        return None
    small = mask.crop(box).resize((128, 128), Image.BILINEAR).point(lambda v: 255 if v > 40 else 0)
    return np.asarray(small.filter(ImageFilter.MaxFilter(7))) > 0


def same_drawing(a, b, threshold: float = 0.45) -> bool:
    """True when two figure images draw mostly the same ink (intersection over union of thickened masks)."""
    x, y = _ink(a), _ink(b)
    if x is None or y is None:
        return False
    return (x & y).sum() / max((x | y).sum(), 1) >= threshold


def answer_cues(lesson: LessonSpec, rendered: dict | None = None, where: str | None = None) -> list[str]:
    """WARN when the student copy gives away an answer the key holds:
    - the prompt or a box label states the correspondence a box asks for ("Scale factor from NPQ to RST"
      above a box for "triangle QNP ~ ___"), or a box label prints one of the item's short-answer numbers;
    - another item prints this item's answer correspondence, or (assessments) a distinctive answer number
      (not a whole number up to 20);
    - another item's figure draws in black what this item's key adds: two or more of the key's new point
      labels, on a figure that refers to this item ("Problem 3") or draws mostly the same ink."""
    rendered = rendered or {}
    out, where = [], where or lesson.stem
    groups = [[("", it) for _, it in lesson.items()]]
    if lesson.practice:
        groups.append([("practice ", it) for r in lesson.practice.rows for it in r.cells])
    fps = fingerprint(lesson, rendered)
    for group in groups:
        info = []
        for pre, it in group:
            objs = [it, *it.parts]
            lab = f"{pre}item {it.n or '(unnumbered)'}"
            prompts = [t for o in objs for t in _prompt_texts(o)]
            labels = [t for o in objs for t in _box_labels(o)]
            given = set().union(*(correspondences(t) for t in prompts))
            # a box asks for a correspondence when its answer completes one its label starts ("QNP ~" + "TRS")
            asked = {c for o in objs for label, ans, full in _box_answers(o)
                     for c in correspondences(full) - correspondences(label) - correspondences(ans)}
            # a worked answer restating a correspondence the prompt gives is not asking for it
            answers = asked | (set().union(*(correspondences(t) for o in objs for t in _answer_texts(o))) - given)
            shown = [t for o in objs for t in _prompt_texts(o) + list(o.choices or [])] + labels
            fig_given = {n for t, layer in figure_labels(it.figure, rendered, lesson) if layer == "given"
                         for n in label_letters(t)} if it.figure else set()
            key_names = {n for t, layer in figure_labels(it.figure, rendered, lesson) if layer == "answer"
                         for n in label_letters(t)} if it.figure else set()
            for name in (it.key_figure, it.draw.key_figure if it.draw else None):
                if name:
                    key_names |= {n for t, _ in figure_labels(name, rendered, lesson) for n in label_letters(t)}
            fp = fps.get(str(it.n)) if it.n and not pre else None
            key_name = (it.draw.key_figure if it.draw else None) or it.key_figure or it.figure
            kr = rendered.get(key_name or "") or {}
            # the key's drawing: the answer layer of the item's figure, or a separate key figure as drawn
            key_png = kr.get("key") if key_name == it.figure else (kr.get("key") or kr.get("student"))
            student_png = None if it.draw else (rendered.get(it.figure or "") or {}).get("student")
            info.append(dict(lab=lab, n=it.n, answers=answers, labels=labels, shown=shown, fig_given=fig_given,
                             added=key_names - fig_given, fp=fp, key_png=key_png, student_png=student_png))
            for c in asked:
                for t in prompts:
                    if _states(correspondences(t), c):
                        out.append(f"WARN  {where} {lab}: the prompt {t[:60]!r} states {_pairs_str(c)}, the "
                                   "correspondence its boxes ask for")
            for t in labels:
                for c in answers:
                    if _states(correspondences(t), c):
                        out.append(f"WARN  {where} {lab}: box label {t!r} states the answer correspondence "
                                   f"{_pairs_str(c)}; name the figures another way (left/right, first/second)")
                if fp is not None:
                    hit = set(numbers(t)[0]) & fp.answers - fp.prompt_nums - fp.fig_shown
                    if hit:
                        out.append(f"WARN  {where} {lab}: box label {t!r} prints the answer {_nums(hit)}")
        test = lesson.doc_type == "assessment"
        for i, a in enumerate(info):
            for j, b in enumerate(info):
                # a test item must not help with any other; in a lesson, earlier items set up later ones on
                # purpose, so only a later item that shows an earlier item's answer is a cue
                if i == j or (j < i and not test):
                    continue
                for c in a["answers"]:
                    if any(_states(correspondences(t), c) for t in b["shown"]):
                        out.append(f"WARN  {where} {b['lab']} prints {_pairs_str(c)}, the correspondence "
                                   f"{a['lab']} asks for")
                refers = any(re.search(rf"\bProblems?\s+(?:\d+\s*(?:,|and|-|\u2013)\s*)*{re.escape(str(a['n']))}\b", t)
                             for t in b["shown"]) if a["n"] else False
                if (len(a["added"]) >= 2 and a["added"] <= b["fig_given"] and a["key_png"] and b["student_png"]
                        and (refers or same_drawing(a["key_png"], b["student_png"]))):
                    out.append(f"WARN  {where} {b['lab']}: its figure shows, in black, the drawing {a['lab']}'s key "
                               f"adds (points {_join(a['added'])}); draw it on the answer layer or change it")
                if test and a["fp"] is not None and b["fp"] is not None:
                    fa, fb = a["fp"], b["fp"]
                    hit = {x for x in (fa.answers - fa.values - fa.angles) if x.denominator > 1 or x > 20}
                    hit &= fb.values - fb.angles
                    if hit:
                        out.append(f"WARN  {where} {b['lab']} prints {_nums(hit)}, {a['lab']}'s answer")
    return out


def _pairs_str(c: frozenset) -> str:
    return ", ".join(f"{x}\u2192{y}" for x, y in sorted(c))


def _match(docs: list[LessonSpec], pattern: str) -> list[LessonSpec]:
    return [d for d in docs if fnmatch(d.stem, pattern) or fnmatch(d.id, pattern)
            or (d.set is not None and fnmatch(d.set, pattern))]


def check_set(unit, stems_or_globs: list[str], vs: list[str] = (), rendered: dict | None = None) -> list[str]:
    """Compare every pair of forms in each set (by `set`, else by the glob that matched) and every
    `parallel_to` link; check each `vs` doc and each doc's `do_not_reuse` globs against the tests.
    rendered: {doc stem or "": {figure name: {"meta": ...}}} as from cli._figures; None reads figure sources."""
    unit = unit if isinstance(unit, UnitSpec) else load_unit(unit)
    docs = []
    for p in unit.doc_paths():
        try:
            docs.append(load_lesson(p))
        except Exception:
            continue
    rendered = rendered or {}
    fps = {d.stem: fingerprint(d, {**rendered.get("", {}), **rendered.get(d.stem, {})}) for d in docs}
    stem = {d.stem: d for d in docs}
    out, groups = [], {}
    for g in stems_or_globs:
        found = _match(docs, g)
        if not found:
            out.append(f"ERROR no document matches {g!r}")
        for d in found:
            groups.setdefault(d.set or g, set()).add(d.stem)
    tests = sorted({s for grp in groups.values() for s in grp})
    pairs = {p for grp in groups.values() for p in combinations(sorted(grp), 2)}
    by_name = {**{d.id: d for d in docs}, **stem}
    for s in tests:
        target = by_name.get(stem[s].parallel_to or "")
        if target is not None and target.stem != s:
            pairs.add(tuple(sorted((target.stem, s))))
    for x, y in sorted(pairs):
        out += compare(stem[x], stem[y], fa=fps[x], fb=fps[y])
    for s in tests:
        out += answers_on_figure(stem[s], fps[s])
    reuse: dict[str, set] = {}
    for g in vs:
        found = _match(docs, g)
        if not found:
            out.append(f"ERROR no document matches {g!r}")
        for d in found:
            reuse.setdefault(d.stem, set()).update(t for t in tests if t != d.stem)
    for d in docs:   # a doc's own do_not_reuse list, when it is checked or names a checked doc
        others = {o.stem for g in d.do_not_reuse for o in _match(docs, g) if o.stem != d.stem}
        if others and (d.stem in tests or d.stem in reuse or others & set(tests)):
            reuse.setdefault(d.stem, set()).update(others)
    for s, others in reuse.items():
        out += do_not_reuse(stem[s], [stem[o] for o in sorted(others)], fps=fps)
    return out


def has_errors(msgs: list[str]) -> bool:
    return any(m.startswith("ERROR") for m in msgs)

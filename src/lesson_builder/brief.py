"""`lesson-builder brief`: one self-contained Markdown brief per step subagent (references/orchestration.md).

`_temp/specs/<stem>/brief_<step>.md` holds the header (unit, document, budget), skills to load, inputs, the files
the step may write, the done condition and reply format, plus per step: source text inline (plan), the figure plan
(figures, write), the schema subset for the doc type and one example per section kind (write). Deterministic:
the same unit state gives the same file.
"""
from __future__ import annotations

import difflib
import fnmatch
import inspect
import re
from pathlib import Path
from typing import Optional, Union

import yaml

from . import spec as S
from .spec import UnitSpec, load_unit

STEPS = ("plan", "figures", "write", "audit")
REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "templates" / "unit"
MAX_SOURCE_LINES = 400
SK = ".agents/skills"
LB = f"{SK}/lesson-builder/references"
RULES = ("Write files in pieces of 150 lines or fewer; use the edit tool, not PowerShell replace; no `python -c` "
         "with nested quotes (save a script in _temp/build/). Never edit src/, unit.yaml, other documents, or a DOCX. "
         "A missing builder feature or figure helper: use the closest existing field and log "
         "`GAP: <file>:<feature>: <symptom> | workaround` in changes.md.")
REPLY = {
    "plan": "Reply in 10 lines or fewer: files written, item count and minutes or points, open questions.",
    "figures": "Reply in 10 lines or fewer: files written, figure names, `figs` errors/warnings, GAP lines.",
    "write": "Reply in 10 lines or fewer: files written, check results (errors/warnings), open questions, GAP lines. "
             "Details go in the handoff files, not the reply.",
    "audit": "Reply in 10 lines or fewer: counts of Must fix / Should fix, the worst problem, pages looked at.",
}


def _rel(p: Path) -> str:
    p = Path(p).resolve()
    try:
        return p.relative_to(REPO).as_posix()
    except ValueError:
        return p.as_posix()


def _norm(s: str) -> str:
    return re.sub(r"[^a-z0-9.]+", " ", s.lower()).strip()


def find_doc(unit: UnitSpec, stem: str) -> Path:
    """The document YAML by file stem or id: unit.yaml's list first, then lessons/ and assessments/."""
    cands = list(unit.doc_paths()) + sorted((unit.dir / "lessons").glob("*.yaml")) \
        + sorted((unit.dir / "assessments").glob("*.yaml"))
    for p in cands:
        if p.stem == stem:
            return p
    for p in cands:
        try:
            if str((yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("id", "")) == stem:
                return p
        except Exception:
            continue
    raise FileNotFoundError(f"no lessons/{stem}.yaml or assessments/{stem}.yaml in {unit.dir}; "
                            f"run `lesson-builder scaffold` first")


def _doc_data(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception:   # mid-edit YAML: the header fields are still useful
        return {}


def requirements_path(unit: UnitSpec, stem: str, data: dict) -> Optional[Path]:
    """The document's requirements.md, or its assessment set's (shared across forms)."""
    for s in (stem, data.get("set")):
        if s:
            p = unit.dir / "_temp" / "specs" / str(s) / "requirements.md"
            if p.exists():
                return p
    return None


def _section(md: str, title: str) -> str:
    """Body of the `## ... <title>` section of a Markdown file ('' if absent)."""
    m = re.search(rf"^##\s+(?:\d+\.\s*)?{re.escape(title)}\b.*?$(.*?)(?=^##\s|\Z)", md, re.M | re.S | re.I)
    return m.group(1).strip() if m else ""


def planned_figures(req_md: str) -> list[str]:
    """Figure names from the requirements.md Figure plan: first cell of each table row, or the leading `name`
    of each list item."""
    names = []
    for ln in _section(req_md, "Figure plan").splitlines():
        ln = ln.strip()
        if ln.startswith("|"):
            cell = ln.strip("|").split("|")[0].strip().strip("`")
            if cell and not re.fullmatch(r"[-: ]+|name", cell, re.I):
                names.append(cell)
        elif re.match(r"[-*]\s+", ln):
            m = re.match(r"[-*]\s+`([^`]+)`|[-*]\s+([^\s:]+)", ln)
            names.append((m.group(1) or m.group(2)).strip("*"))
    return list(dict.fromkeys(n for n in names if n))


def registered_figures(fig_file: Path) -> list[str]:
    """`@figure(...)` names in a figures file, with `{S}` filled in from `S = "..."`."""
    if not fig_file.exists():
        return []
    src = fig_file.read_text(encoding="utf-8")
    m = re.search(r"^S\s*=\s*(['\"])(.*?)\1", src, re.M)
    s = m.group(2) if m else ""
    return [n.replace("{S}", s) for n in re.findall(r"@figure\(\s*f?['\"]([^'\"]+)['\"]", src)]


def used_figures(data: dict) -> list[str]:
    out = []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k in ("figure", "key_figure") and isinstance(x, str):
                    out.append(x)
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk({k: data.get(k) for k in ("sections", "practice")})
    return list(dict.fromkeys(out))


def _sources_text(data: dict) -> str:
    out = []

    def walk(v):
        if isinstance(v, dict):
            for k, x in v.items():
                if k == "source" and isinstance(x, str):
                    out.append(x)
                else:
                    walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(data)
    return " ".join(out)


def source_files(unit: UnitSpec, stem: str, data: dict, req_md: str = "") -> list[Path]:
    """Ingested `_temp/ingest/**/*.md` files for this document: named in a `source:` field or the Intake, else
    files whose name contains the stem, id, or set as a token, else the closest names by similarity."""
    ingest = unit.dir / "_temp" / "ingest"
    mds = sorted(ingest.rglob("*.md")) if ingest.is_dir() else []
    if not mds:
        return []
    named = _norm(_sources_text(data) + " " + _section(req_md, "Intake"))
    hits = [p for p in mds if _norm(p.stem) and _norm(p.stem) in named]
    if hits:
        return hits
    keys = [_norm(str(k)) for k in (stem, data.get("id"), data.get("set")) if k]
    for k in dict.fromkeys(keys):
        pat = re.compile(rf"(?<![\w.]){re.escape(k)}(?![\w]|\.\d)")
        hits = [p for p in mds if pat.search(_norm(p.stem))]
        if hits:
            return hits
    scored = sorted(((max(difflib.SequenceMatcher(None, k, _norm(p.stem)).ratio() for k in keys), p.as_posix(), p)
                     for p in mds), key=lambda t: (-t[0], t[1]))
    return [p for r, _, p in scored[:3] if r >= 0.6]


# ---------------------------------------------------------------- schema subset
MODELS = {
    "lesson": ["LessonSpec", "Target", "Section", "Item", "Part", "Table", "Columns", "Draw", "Practice",
               "PracticeRow", "NoteBlock"],
    "assessment": ["LessonSpec", "Target", "Section", "Item", "Part", "RubricLevel", "Table", "Columns"],
    "reference": ["LessonSpec", "Section", "Item", "Part"],
}
_ASSESS_ONLY = {"directions", "total_points", "set", "form", "parallel_to", "do_not_reuse"}
_LESSON_ONLY = {"notes_title", "framing", "materials", "quicknotes", "notes_height", "practice"}
SKIP = {
    "lesson": {"LessonSpec": _ASSESS_ONLY | {"header_right"}},
    "assessment": {"LessonSpec": _LESSON_ONLY | {"header_right"}},
    "reference": {"LessonSpec": (_LESSON_ONLY | _ASSESS_ONLY | {"header_right", "plan", "guide_notes"}) - {"directions"},
                  "Item": {"key", "distractors", "rubric", "scoring", "answer", "key_figure", "draw", "points",
                           "minutes", "no_answer", "choices", "choice_cols"},
                  "Part": {"key", "distractors", "rubric", "scoring", "answer", "points", "no_answer"}},
}
FIGURE_FIELDS = {"Item": ["figure", "fig_w", "fig", "key_figure", "layout", "draw"],
                 "Draw": ["height", "steps_w", "key_figure", "key_fig_w", "key_note"]}


def _type(a) -> str:
    s = a.__name__ if isinstance(a, type) else repr(a)
    s = re.sub(r"\b(typing|pathlib|lesson_builder\.spec)\.", "", s)
    return s.replace("NoneType", "None")


def _comments(cls) -> dict[str, str]:
    """Inline (and preceding full-line) comments per field, from spec.py source, base classes included."""
    out: dict[str, str] = {}
    for c in reversed(cls.__mro__):
        if getattr(c, "__module__", "") != S.__name__ or c.__name__.startswith("_M"):
            continue
        try:
            src = inspect.getsource(c).splitlines()
        except (OSError, TypeError):
            continue
        pending: list[str] = []
        for ln in src:
            full = re.match(r"^\s{4}#\s?(.*)$", ln)
            if full:
                pending.append(full.group(1).strip())
                continue
            m = re.match(r"^\s{4}(\w+)\s*:[^#]*?(?:#\s?(.*))?$", ln)
            if m and not ln.strip().startswith(("def ", "@", "return")):
                txt = " ".join(pending + ([m.group(2).strip()] if m.group(2) else []))
                if txt:
                    out[m.group(1)] = txt
            pending = []
    return out


def schema_md(doc_type: str, figures_only: bool = False) -> str:
    """Field name, type, default, and the spec.py comment for each model this doc type uses."""
    out = []
    names = list(FIGURE_FIELDS) if figures_only else MODELS[doc_type]
    for name in names:
        cls = getattr(S, name)
        skip = SKIP.get(doc_type, {}).get(name, set())
        notes = _comments(cls)
        doc = (inspect.getdoc(cls) or "").splitlines()
        out.append(f"**{name}**" + (f": {doc[0]}" if doc and cls.__doc__ else ""))
        for fname, f in cls.model_fields.items():
            if f.exclude or fname in skip or (figures_only and fname not in FIGURE_FIELDS[name]):
                continue
            if f.is_required():
                d = "required"
            elif f.default_factory is not None:
                d = f"= {f.default_factory()!r}"
            else:
                d = f"= {f.default!r}"
            note = f"  # {notes[fname]}" if fname in notes else ""
            out.append(f"- `{fname}`: {_type(f.annotation)} {d}{note}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------- template examples
def yaml_blocks(text: str) -> list[tuple[str, str]]:
    """Split a template YAML into ('header', ...), ('section:<kind>', ...) (first of each kind), and
    (<top-level key>, ...) blocks after `sections:`, keeping comments."""
    blocks: list[tuple[str, list[str]]] = [("header", [])]
    after = False
    for ln in text.splitlines():
        m = re.match(r"^([A-Za-z_]\w*):", ln)
        if m and (m.group(1) == "sections" or after):
            after = True
            blocks.append((m.group(1), [ln]))
        else:
            blocks[-1][1].append(ln)
    out, seen = [], set()
    for key, lines in blocks:
        if key == "sections":
            chunks: list[tuple[str, list[str]]] = []
            for ln in lines[1:]:
                m = re.match(r"^\s*-\s+kind:\s*(\w+)", ln)
                if m:
                    chunks.append((m.group(1), [ln]))
                elif chunks:
                    chunks[-1][1].append(ln)
            for kind, ch in chunks:
                if kind not in seen:
                    seen.add(kind)
                    out.append((f"section:{kind}", "\n".join(ch).rstrip()))
        elif "\n".join(lines).strip():
            out.append((key, "\n".join(lines).rstrip()))
    return out


def examples_md(doc_type: str) -> str:
    rel = "lessons/example.yaml" if doc_type == "lesson" else "assessments/example.yaml"
    path = TEMPLATES / rel
    if not path.exists():
        return f"(missing {_rel(path)})\n"
    out = [f"From `{_rel(path)}` (all fields there are valid; copy the shape, not the content).", ""]
    for key, text in yaml_blocks(path.read_text(encoding="utf-8")):
        title = ("Section `kind: " + key.split(":", 1)[1] + "` (under `sections:`)" if key.startswith("section:")
                 else "Header" if key == "header" else f"`{key}:`")
        out += [f"### {title}", "", "```yaml", text, "```", ""]
    return "\n".join(out)


# ---------------------------------------------------------------- brief
def _skills(step: str, doc_type: str, mll: Optional[bool], forms: bool) -> list[str]:
    m = (["`mll-literacy-scaffolding`" + ("" if mll else " (if the class has MLLs)")] if mll is not False else [])
    if step == "plan":
        out = ["`lesson-assessment-designer` (Steps 1-2" + (", 4)" if doc_type == "lesson" else ")")]
        if doc_type == "lesson":
            out.append("`lesson-scope`")
        out += m + ["`course-content-extractor` (only if sources are missing)"]
        if forms:
            out.append("`assessment-builder` section \"Exam integrity\"")
        return out
    if step == "figures":
        return ["`curriculum-visual-generator`", f"`{LB}/api_cheatsheet.md`"]
    if step == "write":
        return [f"`{LB}/api_cheatsheet.md`", "`authentic-writer`", f"`{SK}/assessment-builder/references/item-rules.md`",
                "`handout-release-check` sections 1-2"] + m
    return ["`visual-layout-checker`", "`handout-release-check`", "item-rules "
            f"(`{SK}/assessment-builder/references/item-rules.md`)"] + \
        ([m[0].replace("`mll-literacy-scaffolding`", "`mll-literacy-scaffolding` checklist")] if m else []) + \
        ["`lesson-assessment-designer` final check"]


def _mll(period: str) -> Optional[bool]:
    """True for Period 4 (high MLL population), False for another named period, None if unknown."""
    if not period.strip():
        return None
    return bool(re.search(r"\b4\b|MLL|\bEL", period, re.I))


def _outputs(path: Path, data: dict, unit: UnitSpec) -> list[str]:
    try:
        from .render import outputs
        from .spec import load_lesson
        return [_rel(p.with_suffix(".pdf")) for p in outputs(unit, load_lesson(path)).values()]
    except Exception:
        return [_rel(unit.dir / "output") + "/ (the document's PDFs)"]


def _q(stem: str) -> str:
    return f'"{stem}"' if " " in stem else stem


def brief(unit: Union[str, Path, UnitSpec], stem: str, step: str = "plan", out: Optional[Path] = None) -> Path:
    """Write `_temp/specs/<stem>/brief_<step>.md` (or `out`) for a step subagent and return its path."""
    if step not in STEPS:
        raise ValueError(f"step must be one of {STEPS}, not {step!r}")
    u = unit if isinstance(unit, UnitSpec) else load_unit(Path(unit))
    path = find_doc(u, stem)
    stem = path.stem
    data = _doc_data(path)
    doc_type = str(data.get("doc_type") or ("lesson" if path.parent.name == "lessons" else "assessment"))
    specs = u.dir / "_temp" / "specs"
    req = requirements_path(u, stem, data)
    req_md = req.read_text(encoding="utf-8") if req else ""
    srcs = source_files(u, stem, data, req_md)
    fig_file = u.dir / "figures" / f"{stem}.py"
    ud, uq, sq = _rel(u.dir), _q(_rel(u.dir)), _q(stem)
    b = u.budget
    forms = bool(data.get("set") or data.get("form"))
    own_req = req or specs / str(data.get("set") or stem) / "requirements.md"

    if doc_type == "lesson":
        budget = f"{b.minutes} minutes; handout {data.get('max_pages') or b.handout_pages} pages, practice " \
                 f"{b.practice_pages}"
    else:
        budget = f"{data.get('max_pages') or b.handout_pages} pages" + (
            f"; total_points {data['total_points']}" if data.get("total_points") is not None else "")
    lines = [f"# Brief: {step} step for {doc_type} \"{stem}\"", "",
             "Generated by `lesson-builder brief`; this file and the ones under Read are all you need.", "",
             "| | |", "|---|---|",
             f"| Repo | `{REPO}` (Windows pwsh, Python via `uv run`) |",
             f"| Unit | `{ud}` ({u.course} Unit {u.unit}: {u.unit_title}) |",
             f"| Period | {u.period or 'not set in unit.yaml'} |",
             f"| Document | `{_rel(path)}` (id `{data.get('id', stem)}`) |",
             f"| Budget | {budget} |"]
    if forms:
        bits = [f"set {data.get('set')}" if data.get("set") else "", f"form {data.get('form')}" if data.get("form")
                else "", f"parallel to {data.get('parallel_to')}" if data.get("parallel_to") else ""]
        lines.append(f"| Set / form | {', '.join(x for x in bits if x)} |")
    lines.append("")

    reads: list[str] = [f"`{_rel(own_req)}`" + ("" if req else " (not written yet)")]
    if step == "plan":
        reads += [f"`{_rel(p)}` (inline below)" for p in srcs]
    else:
        reads.append(f"`{_rel(path)}`")
    if step in ("plan", "figures"):
        for p in srcs:
            for suffix in ("_pages", "_media"):
                d = p.with_name(p.stem + suffix)
                if d.is_dir():
                    n = len(list(d.glob("*.png"))) if suffix == "_pages" else len(list(d.iterdir()))
                    what = "page renders: open only to see figures" if suffix == "_pages" else "source images"
                    reads.append(f"`{_rel(d)}/` ({n} file{'' if n == 1 else 's'}; {what})")
    if step in ("figures", "write"):
        reads.append(f"`{_rel(fig_file)}`" + ("" if fig_file.exists() else " (not written yet)"))
    if step == "audit":
        reads += [f"`{p}`" for p in _outputs(path, data, u)]
        reads += [f"`{_rel(u.dir / '_temp' / 'renders' / 'current' / stem)}/` (page renders)",
                  f"`{_rel(u.dir / '_temp' / 'figures' / (stem + '_sheet.png'))}` (figure sheet)"]
    for g in data.get("do_not_reuse") or []:
        hits = [p for p in u.doc_paths() if fnmatch.fnmatch(p.stem, g) and p != path]
        reads += [f"`{_rel(p)}` (do not reuse: `{g}`)" for p in hits]

    sections = "sections 2-5" if doc_type == "assessment" else "sections 2-4"
    writes = {"plan": [f"`{_rel(own_req)}` {sections} (keep the Intake as written)"],
              "figures": [f"`{_rel(fig_file)}`", f"`{_rel(u.dir / 'assets' / stem)}/`",
                          f"`{_rel(specs / stem / 'changes.md')}` (GAP lines only)"],
              "write": [f"`{_rel(path)}`", f"`{_rel(specs / stem / 'changes.md')}`"],
              "audit": [f"`{_rel(specs / stem / 'audit.md')}` only; everything else is read-only"]}[step]
    done = {"plan": "The blueprint covers every target; " + (
                f"item minutes add up to {b.minutes} or less" if doc_type == "lesson"
                else "points add up to total_points") + "; every figure has a name in the Figure plan.",
            "figures": f"`uv run lesson-builder figs {uq} -l {sq}` shows 0 errors and no label warnings, and "
                       f"`{_rel(u.dir / '_temp' / 'figures' / (stem + '_sheet.png'))}` looks right at print size.",
            "write": f"`uv run lesson-builder build {uq} -l {sq}` shows 0 errors, in at most 4 builds.",
            "audit": "Every page and figure has been looked at; `audit.md` lists Must fix / Should fix / Looks fine, "
                     "each line naming page, item, and the file and field to change."}[step]
    lines += ["## Load", "", "Skills are in `.agents/skills/<name>/SKILL.md`. Load only these:", ""]
    lines += [f"- {s}" for s in _skills(step, doc_type, _mll(u.period), forms)] + [""]
    lines += ["## Read", ""] + [f"- {r}" for r in reads] + [""]
    lines += ["## Write only", ""] + [f"- {w}" for w in writes] + [""]
    lines += ["## Done when", "", done, "", "## Rules", "", RULES, "", "## Reply", "", REPLY[step], ""]
    lines += _extras(step, doc_type, u, stem, data, req_md, srcs, fig_file)
    dest = Path(out) if out else specs / stem / f"brief_{step}.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8", newline="\n")
    return dest


def _figure_names(u: UnitSpec, data: dict, req_md: str, fig_file: Path) -> list[str]:
    planned, own = planned_figures(req_md), registered_figures(fig_file)
    shared_file = u.dir / (u.figures or "figures.py")
    shared = registered_figures(shared_file) if shared_file.is_file() else []
    used = used_figures(data)
    missing = [n for n in dict.fromkeys(planned + used)
               if n not in own and n not in shared and not re.search(r"[/\\]|\.(png|jpe?g|gif)$", n, re.I)]

    def fmt(xs):
        return ", ".join(f"`{x}`" for x in xs) or "none"
    out = ["## Figure names", "",
           f"- Planned (requirements.md Figure plan): {fmt(planned)}",
           f"- Registered in `{_rel(fig_file)}`: {fmt(own)}",
           f"- Used in the YAML: {fmt(used)}"]
    if shared:
        out.append(f"- Shared (`{_rel(shared_file)}`, every document sees them): {fmt(shared)}")
    if missing:
        out.append(f"- Not registered yet: {fmt(missing)}")
    return out + [""]


def _extras(step: str, doc_type: str, u: UnitSpec, stem: str, data: dict, req_md: str, srcs: list[Path],
            fig_file: Path) -> list[str]:
    out: list[str] = []
    if step == "plan":
        if u.targets:
            out += ["## Unit targets", ""] + [f"- {t.id}: understand that {t.understand or 'TODO'}; able to "
                                               f"{t.able_to or 'TODO'}" + (f" ({t.standard})" if t.standard else "")
                                               for t in u.targets] + [""]
        out += ["## Source text", ""]
        if not srcs:
            out += ["No ingested source matched this document. Name the source in the requirements.md Intake, "
                    "or run `lesson-builder ingest` first.", ""]
        for p in srcs:
            text = p.read_text(encoding="utf-8").splitlines()
            out += [f"### `{_rel(p)}`", "", "````markdown"] + text[:MAX_SOURCE_LINES] + ["````"]
            if len(text) > MAX_SOURCE_LINES:
                out.append(f"(truncated at {MAX_SOURCE_LINES} of {len(text)} lines; read the rest from the file)")
            out.append("")
        return out
    out += _figure_names(u, data, req_md, fig_file)
    if step == "figures":
        out += ["## YAML fields that place figures", "",
                f"The figure API (Figure, labels, helpers, a worked example) is in `{LB}/api_cheatsheet.md` "
                "section 4. Name figures `<stem>_<item>`; student ink on `layer=\"given\"`, key ink on "
                "`layer=\"answer\"`; assert the math in code.", "", schema_md(doc_type, figures_only=True)]
    elif step == "write":
        out += [f"## Schema ({doc_type})", "",
                f"From `src/lesson_builder/spec.py` (authoritative; unknown keys are errors). Pitfalls, math "
                f"commands, and YAML quoting: `{LB}/api_cheatsheet.md` sections 3, 5, and 6.", "",
                schema_md(doc_type), "## Examples", "", examples_md(doc_type)]
    else:
        out += ["## Commands", "", f"- `uv run lesson-builder check {_q(_rel(u.dir))} -l {_q(stem)}` "
                "(read-only; report its errors in audit.md)", ""]
    return out

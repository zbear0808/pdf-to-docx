"""`lesson-builder scaffold`: skeleton YAML, figures/<stem>.py, and handoff files for a new document.

Placeholders are valid YAML that loads and renders; every open spot says TODO. Existing files are never
overwritten unless force=True. The YAML is added to unit.yaml if `lessons:` or the `assessments:` globs don't
cover it (a minimal text edit that keeps comments).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Optional, Union

from .spec import UnitSpec, load_unit

DOC_TYPES = ("lesson", "assessment", "reference")
# (plan row, section kind or None for no section, minutes at a 40-minute budget, who talks)
LESSON_ROWS = [("Warm-up", "warmup", 5, "Students"), ("Together", "together", 7, "Teacher + class"),
               ("With a partner", "partner", 15, "Students (pairs)"), ("QuickNotes", "notes", 4, "Teacher + class"),
               ("Check your understanding", "cyu", 3, "Students"), ("Exit ticket", "exit", 4, "Students"),
               ("Collect, assign practice", None, 2, "Teacher")]


def q(s: str) -> str:
    """Single-quoted YAML scalar."""
    return "'" + str(s).replace("'", "''") + "'"


def _unit(unit: Union[str, Path, UnitSpec]) -> UnitSpec:
    return unit if isinstance(unit, UnitSpec) else load_unit(Path(unit))


def lesson_minutes(budget: int) -> list[int]:
    """Minutes per LESSON_ROWS row, scaled to the budget; the rows end exactly at the budget."""
    base = [r[2] for r in LESSON_ROWS]
    out = [max(1, round(m * budget / 40)) for m in base[:-1]]
    out.append(budget - sum(out))
    while out[-1] < 0:   # tiny budgets: take minutes back from the longest row
        i = out.index(max(out[:-1]))
        out[i] -= 1
        out[-1] += 1
    return out


def _targets_yaml() -> str:
    return ("targets:                          # TODO: from requirements.md section 2\n"
            "  - id: LT1\n"
            "    understand: 'TODO: Students will understand that ...'\n"
            "    able_to: 'TODO: Students will be able to ...'\n")


def lesson_yaml(unit: UnitSpec, stem: str, title: Optional[str]) -> str:
    mins = lesson_minutes(unit.budget.minutes)
    fig = q(f"{stem}_example")
    body = {
        "warmup": "      - minutes: {m}\n        prompt: 'TODO warm-up prompt.'\n        answer: TODO\n",
        "together": ("      - id: together_1\n        minutes: {m}\n        target: LT1\n"
                     "        prompt: 'TODO prompt.'\n        figure: " + fig + "\n        answer: TODO\n"),
        "partner": ("      - minutes: {m}\n        target: LT1\n"
                    "        prompt: 'TODO prompt. Look back at {{ref:together_1}}.'\n        answer: TODO\n"),
        "cyu": "      - minutes: {m}\n        target: LT1\n        prompt: 'TODO prompt.'\n        answer: TODO\n",
        "exit": ("      - minutes: {m}\n        target: LT1\n        prompt: 'TODO prompt.'\n        box: 1.2\n"
                 "        answer: TODO\n"),
    }
    out = [f"# Lesson {stem} (scaffold). Replace every TODO, then: uv run lesson-builder check <unit> -l {q(stem)}\n",
           "# Fields: templates/unit/lessons/example.yaml and .agents/skills/lesson-builder/references/api_cheatsheet.md\n",
           f"id: {q(stem)}\n",
           f"title: {q(title or 'TODO title')}\n",
           "notes_title: 'TODO topic for the QuickNotes page'\n",
           "framing: >-\n  TODO: one or two sentences that pose today's question.\n",
           "materials: TODO\n",
           "numbering: auto                   # items without n: are numbered; numbering restarts after notes\n",
           _targets_yaml(), "\nsections:\n"]
    for (_, kind, _, _), m in zip(LESSON_ROWS, mins):
        if kind is None:
            continue
        if kind == "notes":
            out.append("  - kind: notes                   # new page: notes_title + QuickNotes\n")
            continue
        out.append(f"  - kind: {kind}\n    items:\n" + body[kind].format(m=m))
    out.append("\nquicknotes:\n  - target: LT1\n    bullets: ['TODO: one fact per bullet.']\n")
    out.append("\npractice:\n  title: 'TODO topic: practice'\n  rows:\n    - cells:\n"
               "        - prompt: 'TODO practice item.'\n          answer: TODO\n"
               "        - prompt: 'TODO practice item.'\n          answer: TODO\n"
               "  selected: auto                  # answers to selected problems, taken from each item\n")
    out.append(f"\nplan: |\n  **Overview.** TODO: where this lesson sits in the unit.\n\n"
               f"  **Quick look ({unit.budget.minutes} min).**\n  | Time | Part | Who talks |\n  |---|---|---|\n")
    t = 0
    for (part, _, _, who), m in zip(LESSON_ROWS, mins):
        out.append(f"  | {t}-{t + m} | {part} | {who} |\n")
        t += m
    return "".join(out)


def assessment_yaml(unit: UnitSpec, doc_id: str, title: Optional[str], set_name: Optional[str] = None,
                    form: Optional[str] = None, parallel_to: Optional[str] = None) -> str:
    out = [f"# {doc_id} (scaffold). Replace every TODO, then: uv run lesson-builder check <unit> -l {q(doc_id)}\n",
           "# Fields: templates/unit/assessments/example.yaml and "
           ".agents/skills/lesson-builder/references/api_cheatsheet.md\n",
           f"id: {q(doc_id)}\n",
           "doc_type: assessment\n",
           f"title: {q(title or 'TODO title')}\n",
           "directions: Show your work.\n",
           "numbering: auto\n"]
    if set_name:
        out.append(f"set: {q(set_name)}\n")
    if form:
        out.append(f"form: {q(form)}\n")
    if parallel_to:
        out.append(f"parallel_to: {q(parallel_to)}          # new letters, numbers, and MC positions (version table)\n")
    out += ["total_points: 4                   # TODO: the blueprint total; must equal the sum of points\n",
            f"max_pages: {unit.budget.handout_pages}                      # TODO: the source's page count\n",
            _targets_yaml(),
            "\nsections:\n  - kind: plain\n    target: LT1                     # TODO: one section per target\n"
            "    items:\n"
            "      - points: 2\n        target: LT1\n        type: cr\n        demand: pwc\n"
            f"        prompt: 'TODO prompt.'\n        figure: {q(doc_id + '_example')}\n        answer: TODO\n"
            "      - points: 2\n        target: LT1\n        type: cr\n        demand: pwoc\n"
            "        prompt: 'TODO prompt.'\n        answer: TODO\n",
            "\nguide_notes: |\n  **Scoring notes.** TODO. Credit any valid method. Score the math, not English grammar "
            "or spelling.\n"]
    return "".join(out)


def reference_yaml(unit: UnitSpec, doc_id: str, title: Optional[str]) -> str:
    return "".join([
        f"# {doc_id} (scaffold): reference sheet, no key. Then: uv run lesson-builder check <unit> -l {q(doc_id)}\n",
        f"id: {q(doc_id)}\n",
        "doc_type: reference\n",
        f"title: {q(title or 'TODO title')}\n",
        "max_pages: 1\n",
        "\nsections:\n  - kind: plain\n    title: 'TODO heading'\n    items:\n",
        "      - prompt: ['TODO: one fact per line.', 'TODO: a second fact.']\n"
        f"        figure: {q(doc_id + '_example')}\n        work: 0\n",
    ])


def requirements_md(unit: UnitSpec, stem: str, doc_type: str, forms: Optional[list[str]] = None) -> str:
    """The handoff headings from references/orchestration.md (Intake is the orchestrator's; the rest the plan's)."""
    b = unit.budget
    amount = f"Minutes: {b.minutes}" if doc_type == "lesson" else "Total points: TODO"
    pages = (f"handout {b.handout_pages}, practice {b.practice_pages}" if doc_type == "lesson"
             else "TODO (max_pages)")
    out = [f"# Requirements: {stem}\n\n",
           "## 1. Intake\n\n",
           "- Mode: TODO (new / rewrite)\n",
           f"- Course and period: {unit.course}, {unit.period or 'TODO period'}\n",
           f"- Doc type: {doc_type}\n",
           "- Source files: TODO (`_temp/ingest/<name>.md`)\n",
           f"- Page budget: {pages}\n",
           f"- {amount}\n",
           "- Keep / change (teacher): TODO\n"]
    if forms:
        out.append(f"- Forms: {', '.join(forms)}\n")
    unit_word = "minutes" if doc_type == "lesson" else "points"
    out += ["\n## 2. Targets\n\n",
            "| id | understand that... | able to... | standard |\n|---|---|---|---|\n",
            "| LT1 | TODO | TODO | TODO |\n",
            "\n## 3. Blueprint\n\n",
            f"| n | target | type (SR/CR/performance) | demand | {unit_word} | figure name |\n",
            "|---|---|---|---|---|---|\n",
            "\n## 4. Figure plan\n\n",
            "| name | shows | coordinates or measurements | asserts | answer layer |\n|---|---|---|---|---|\n"]
    for s in ([f"{stem} {f}" for f in forms] if forms else [stem]):
        out.append(f"| {s}_example | TODO | TODO | TODO | TODO |\n")
    if doc_type == "assessment":
        cols = forms or ["A"]
        out += ["\n## 5. Version table\n\n",
                "| item | " + " | ".join(cols) + " |\n", "|---|" + "---|" * len(cols) + "\n",
                "\nMC answer positions per form: TODO\n",
                "\nDo not reuse (documents from earlier waves): TODO\n"]
    return "".join(out)


def changes_md(stem: str) -> str:
    return (f"# Changes: {stem}\n\n"
            "One line per change: `item: what changed | why (rule)`.\n"
            "Builder gaps: `GAP: <file>:<feature>: <symptom> | workaround`.\n\n")


def _yaml_entry(s: str) -> str:
    return s if re.fullmatch(r"[A-Za-z0-9_][\w./ *-]*", s) and not s.endswith(" ") else q(s)


def add_to_list(text: str, key: str, entry: str) -> str:
    """Append `entry` to the top-level list `key:` in YAML text, keeping comments and layout.
    Handles block lists (`key:` then `  - x` lines), flow lists (`key: [a, b]`), and a missing key."""
    nl = "\r\n" if "\r\n" in text else "\n"
    lines = text.splitlines(keepends=True)
    e = _yaml_entry(entry)
    for i, ln in enumerate(lines):
        m = re.match(rf"^{re.escape(key)}:[ \t]*(\[[^\]#]*\]|[^#]*?)[ \t]*(#.*)?$", ln.rstrip("\r\n"))
        if not m:
            continue
        val = m.group(1).strip()
        if val.startswith("["):
            inner = val[1:-1].strip()
            a = ln.index("[")
            b = ln.index("]", a)
            lines[i] = f"{ln[:a]}[{inner + ', ' if inner else ''}{e}]{ln[b + 1:].rstrip(chr(13) + chr(10))}{nl}"
            return "".join(lines)
        if val:
            raise ValueError(f"unit.yaml `{key}:` is not a list: {val!r}")
        last, indent, j = i, "  ", i + 1
        while j < len(lines):
            s = lines[j]
            if not s.strip() or s.lstrip().startswith("#"):
                j += 1
                continue
            mm = re.match(r"^(\s*)-\s", s)
            if not mm:
                break
            last, indent, j = j, mm.group(1), j + 1
        lines.insert(last + 1, f"{indent}- {e}{nl}")
        return "".join(lines)
    if text and not text.endswith(("\n", "\r")):
        text += nl
    return text + f"{key}: [{e}]{nl}"


def figures_py(stem: str, doc_type: str, yaml_rel: str) -> str:
    return f'''"""Figures for {doc_type} "{stem}" ({yaml_rel}). Name each figure f"{{S}}_<item>".
Given ink (layer="given") prints on the student copy and the key; answer ink (layer="answer") is red, key only.
Assert the math before drawing. Loop: uv run lesson-builder figs <unit> -l "{stem}" (0 errors, no label warnings).
Helpers: .agents/skills/lesson-builder/references/api_cheatsheet.md section 4.
"""
import numpy as np

from lesson_builder.figures import Figure, P, dilate, figure, similarity_ratio

S = {stem!r}


@figure(f"{{S}}_example")
def example() -> Figure:
    """Placeholder: triangle ABC (given) and its image under a dilation by 2 from O (answer). Replace it."""
    O = np.array((0.0, 0.0))
    abc = P((1, 0.5), (2, 0.5), (1, 1.5))
    img = dilate(abc, 2, center=O)
    assert np.isclose(similarity_ratio(abc, img), 2)
    f = Figure(width_in=2.2, height_in=1.9)
    f.grid(0, 4, 0, 3)
    f.dots([O])
    f.label(O, "O", direction=(-1, -1))
    f.poly(abc)
    f.dots(abc)
    f.label_poly(abc, "ABC")
    f.poly(img, layer="answer")
    f.dots(img, layer="answer")
    f.label_poly(img, ["A'", "B'", "C'"], layer="answer")
    return f
'''


def _write(path: Path, text: str, force: bool, written: list, log: Optional[Callable[[str], None]]):
    if path.exists() and not force:
        if log:
            log(f"exists, not overwritten (use --force): {path}")
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    written.append(path)


def _register(unit: UnitSpec, path: Path, doc_type: str) -> bool:
    """List `path` in unit.yaml unless `lessons:` or an `assessments:` glob already covers it."""
    if path.resolve() in {p.resolve() for p in unit.doc_paths()}:
        return False
    y = unit.dir / "unit.yaml"
    old = y.read_bytes().decode("utf-8")
    if doc_type == "lesson":
        new = add_to_list(old, "lessons", path.name)
    else:
        entry = path.relative_to(unit.dir).as_posix() if unit.assessments else "assessments/*.yaml"
        new = add_to_list(old, "assessments", entry)
    y.write_bytes(new.encode("utf-8"))
    try:
        u = load_unit(y)
        ok = path.resolve() in {p.resolve() for p in u.doc_paths()}
    except Exception as e:  # never leave a broken unit.yaml behind
        y.write_bytes(old.encode("utf-8"))
        raise ValueError(f"could not add {path.name} to {y}: {e}") from e
    if not ok:
        y.write_bytes(old.encode("utf-8"))
        raise ValueError(f"could not add {path.name} to {y}; add it by hand")
    return True


def scaffold(unit: Union[str, Path, UnitSpec], stem: str, doc_type: str = "lesson",
             forms: Optional[list[str]] = None, title: Optional[str] = None, force: bool = False,
             log: Optional[Callable[[str], None]] = None) -> list[Path]:
    """Write a skeleton document, its figures/<stem>.py, and _temp/specs/<stem>/ handoff files.

    lesson: lessons/<stem>.yaml. assessment: assessments/<stem>.yaml, or one `<stem> <form>.yaml` per form
    (set/form/parallel_to filled; requirements.md is shared in _temp/specs/<stem>/). reference:
    assessments/<stem>.yaml with doc_type reference. Returns the files written (unit.yaml last, if changed).
    """
    if doc_type not in DOC_TYPES:
        raise ValueError(f"doc_type must be one of {DOC_TYPES}, not {doc_type!r}")
    if forms and doc_type != "assessment":
        raise ValueError("forms only apply to assessments")
    u = _unit(unit)
    forms = [f.strip() for f in forms or [] if f.strip()]
    written: list[Path] = []
    specs = u.dir / "_temp" / "specs"
    if doc_type == "lesson":
        docs = [(stem, u.dir / "lessons" / f"{stem}.yaml", lesson_yaml(u, stem, title))]
    elif doc_type == "reference":
        docs = [(stem, u.dir / "assessments" / f"{stem}.yaml", reference_yaml(u, stem, title))]
    elif forms:
        first = f"{stem} {forms[0]}"
        docs = [(f"{stem} {f}", u.dir / "assessments" / f"{stem} {f}.yaml",
                 assessment_yaml(u, f"{stem} {f}", title, stem, f, None if i == 0 else first))
                for i, f in enumerate(forms)]
    else:
        docs = [(stem, u.dir / "assessments" / f"{stem}.yaml", assessment_yaml(u, stem, title))]
    for s, path, text in docs:
        _write(path, text, force, written, log)
        rel = path.relative_to(u.dir).as_posix()
        _write(u.dir / "figures" / f"{s}.py", figures_py(s, doc_type, rel), force, written, log)
        _write(specs / s / "changes.md", changes_md(s), force, written, log)
    _write(specs / stem / "requirements.md", requirements_md(u, stem, doc_type, forms or None), force, written, log)
    changed = False
    for _, path, _ in docs:
        changed = _register(u, path, doc_type) or changed
        u = load_unit(u.dir)
    if changed:
        written.append(u.dir / "unit.yaml")
    return written


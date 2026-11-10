"""Unit litter: Word temp files, __pycache__, stale diff images (deletable), and source files nothing uses
(orphan assets, unused figures, unlisted YAML, figure files with no document, redundant `work:` lines),
which are only reported."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from .spec import Item, LessonSpec, Part, UnitSpec, load_lesson

DELETABLE = {"word_temp", "pycache", "stale_diff"}
KINDS = ("word_temp", "pycache", "stale_diff", "orphan_asset", "unused_figure", "unlisted_yaml",
         "orphan_figure_file", "redundant_work", "load_error")


@dataclass
class Finding:
    kind: str
    path: Path
    reason: str

    @property
    def deletable(self) -> bool:
        return self.kind in DELETABLE

    def __str__(self) -> str:
        return f"{'DELETE' if self.deletable else 'REPORT'} {self.kind}: {self.path} ({self.reason})"


def _docs(unit: UnitSpec, out: list[Finding]) -> list[LessonSpec]:
    docs = []
    for p in unit.doc_paths():
        try:
            docs.append(load_lesson(p))
        except Exception as e:
            out.append(Finding("load_error", p, f"did not load, so references from it are unknown: {e}"[:200]))
    return docs


def _refs(lesson: LessonSpec) -> set[str]:
    refs = set()
    for it in lesson.all_items():
        refs |= {it.figure, it.key_figure, it.draw.key_figure if it.draw else None}
    return refs - {None}


def _figure_files(unit: UnitSpec) -> dict[str, Path]:
    """{doc stem or "" for the shared file: figure file}."""
    out = {}
    shared = unit.dir / (unit.figures or "figures.py")
    if shared.is_file():
        out[""] = shared
    folder = unit.dir / "figures"
    if folder.is_dir():
        out.update({p.stem: p for p in sorted(folder.glob("*.py")) if not p.stem.startswith("_")})
    return out


def _word_temp(unit: UnitSpec) -> list[Finding]:
    out = unit.dir / "output"
    if not out.is_dir():
        return []
    found = {p for pat in ("mso*.tmp", "~$*.doc*", "~$*.ppt*", "~WRL*.tmp") for p in out.rglob(pat) if p.is_file()}
    return [Finding("word_temp", p, "Word temp file") for p in sorted(found)]


def _stale_diffs(unit: UnitSpec) -> list[Finding]:
    renders = unit.dir / "_temp" / "renders"
    out = []
    for d in sorted((renders / "diff").glob("*")) if (renders / "diff").is_dir() else []:
        if not d.is_dir():
            continue
        cur = [p.stat().st_mtime for p in (renders / "current" / d.name).glob("*.png")]
        newest = max(cur, default=None)
        for p in sorted(d.glob("*.png")):
            if newest is None:
                out.append(Finding("stale_diff", p, "no current renders for this document"))
            elif p.stat().st_mtime < newest:
                out.append(Finding("stale_diff", p, "older than the newest current render"))
    return out


def _assets(unit: UnitSpec, docs: list[LessonSpec], registered: set[str]) -> list[Finding]:
    folder = unit.dir / "assets"
    if not folder.is_dir():
        return []
    used = {(unit.dir / r).resolve() for d in docs for r in _refs(d) if r not in registered}
    code = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in
                     list(_figure_files(unit).values()) + sorted((unit.dir / "figures").glob("_*.py")))
    out = []
    files = [p for p in sorted(folder.rglob("*")) if p.is_file()]
    for p in files:
        if p.resolve() in used or p.name in code:
            continue
        if p.suffix.lower() in (".txt", ".md") and any(f.resolve() in used and p.name.startswith(f.stem)
                                                       for f in files if f != p):
            continue   # source note next to a used image
        out.append(Finding("orphan_asset", p, "not referenced by any document or figure file"))
    return out


def _unused_figures(unit: UnitSpec, docs: list[LessonSpec], out: list[Finding]) -> set[str]:
    """Registered names never placed by a document that can see them. Returns every registered name."""
    import inspect

    from .figures.core import load_module, registered
    files = _figure_files(unit)
    names = set()
    for stem, path in files.items():
        try:
            fns = registered(load_module(path))
        except Exception as e:
            out.append(Finding("load_error", path, f"figure file did not import: {e}"[:200]))
            continue
        names |= set(fns)
        seen = [d for d in docs if not stem or d.stem == stem]
        refs = set().union(*(_refs(d) for d in seen)) if seen else set()
        for name, fn in fns.items():
            if name not in refs:
                line = inspect.getsourcelines(fn)[1]
                out.append(Finding("unused_figure", path, f"figure '{name}' (line {line}) is registered but no "
                                   "document uses it"))
    return names


def _unlisted(unit: UnitSpec) -> list[Finding]:
    listed = {p.resolve() for p in unit.doc_paths()}
    out = []
    for sub in ("lessons", "assessments"):
        for p in sorted((unit.dir / sub).glob("*.y*ml")) if (unit.dir / sub).is_dir() else []:
            if p.resolve() not in listed:
                out.append(Finding("unlisted_yaml", p, "not covered by unit.yaml lessons/assessments"))
    return out


def _orphan_figure_files(unit: UnitSpec) -> list[Finding]:
    stems = {p.stem for p in unit.doc_paths()}
    return [Finding("orphan_figure_file", p, f"no document named '{s}'")
            for s, p in _figure_files(unit).items() if s and s not in stems]


def _get(node, key):
    if isinstance(node, yaml.MappingNode):
        for k, v in node.value:
            if k.value == key:
                return k, v
    return None, None


def _seq(node, key) -> list:
    _, v = _get(node, key)
    return v.value if isinstance(v, yaml.SequenceNode) else []


def _effective_work(it: Item | Part) -> float:
    """What render uses when `work:` is left out (render._work on a copy without the explicit value)."""
    from .render import _work
    c = it.model_copy(update={"work": type(it).model_fields["work"].default})
    c.__pydantic_fields_set__.discard("work")
    return _work(c)


def _redundant_work(lesson: LessonSpec) -> list[Finding]:
    try:
        root = yaml.compose(lesson.raw)
    except yaml.YAMLError:
        return []
    pairs = []   # (model, yaml node, label)
    for s, sn in zip(lesson.sections, _seq(root, "sections")):
        pairs += [(it, n, f"item {it.n or '(unnumbered)'}") for it, n in zip(s.items, _seq(sn, "items"))]
    if lesson.practice:
        _, pn = _get(root, "practice")
        for r, rn in zip(lesson.practice.rows, _seq(pn, "rows")):
            pairs += [(it, n, f"practice item {it.n}") for it, n in zip(r.cells, _seq(rn, "cells"))]
    pairs += [(p, n, f"{label} part {p.label}") for it, node, label in list(pairs)
              for p, n in zip(it.parts, _seq(node, "parts"))]
    out = []
    for m, node, label in pairs:
        k, _ = _get(node, "work")
        if k is not None and "work" in m.model_fields_set and m.work == _effective_work(m):
            out.append(Finding("redundant_work", lesson.path, f"line {k.start_mark.line + 1}: {label} "
                               f"`work: {m.work:g}` is the default; delete the line"))
    return out


def find_litter(unit: UnitSpec) -> list[Finding]:
    out: list[Finding] = []
    docs = _docs(unit, out)
    out += _word_temp(unit)
    out += [Finding("pycache", p, "Python bytecode cache") for p in sorted(unit.dir.rglob("__pycache__"))
            if p.is_dir()]
    out += _stale_diffs(unit)
    registered = _unused_figures(unit, docs, out)
    out += _assets(unit, docs, registered)
    out += _unlisted(unit)
    out += _orphan_figure_files(unit)
    for d in docs:
        out += _redundant_work(d)
    return sorted(out, key=lambda f: (KINDS.index(f.kind), str(f.path)))


def apply(findings: list[Finding], kinds=None) -> list[Path]:
    """Delete findings of the deletable kinds (Word temp files, __pycache__, stale diffs). Source files
    (assets, YAML, figure files) are never deleted, whatever `kinds` says. Returns what was removed."""
    allowed = DELETABLE & set(kinds or DELETABLE)
    removed = []
    for f in findings:
        if f.kind not in allowed or not f.path.exists():
            continue
        if f.path.is_dir():
            shutil.rmtree(f.path)
        else:
            f.path.unlink()
        removed.append(f.path)
    return removed


def summary(findings: list[Finding]) -> str:
    counts = {k: sum(f.kind == k for f in findings) for k in KINDS}
    return ", ".join(f"{n} {k}" for k, n in counts.items() if n) or "clean"

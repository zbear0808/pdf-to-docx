"""lesson-builder CLI: new-unit, ingest, build, check, packet."""
from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import List, Optional

import typer

from .spec import load_unit

app = typer.Typer(add_completion=False, help="Build lesson handouts, keys, practice sets, and packets from YAML.")
TEMPLATES = Path(__file__).resolve().parents[2] / "templates" / "unit"


def _out(msg: str):
    sys.stdout.write(msg + "\n")


def _figures(unit, force=False, docs=None) -> dict:
    """Shared figures.py plus figures/<doc stem>.py per document. Returns {doc stem or "": rendered}."""
    from .figures import render_all
    out = {"": {}}
    tmp = unit.dir / "_temp" / "figures"
    shared = unit.dir / (unit.figures or "figures.py")
    if shared.is_file():
        out[""] = render_all(shared, tmp, force=force)
    folder = unit.dir / "figures"
    if folder.is_dir():
        for p in sorted(folder.glob("*.py")):
            if p.stem.startswith("_"):  # shared helpers for this unit's figure files, not a document
                continue
            if docs is None or p.stem in docs:
                out[p.stem] = render_all(p, tmp / p.stem, force=force)
    return out


def _figs_for(figs: dict, lesson) -> dict:
    return {**figs.get("", {}), **figs.get(lesson.stem, {})}


def _lessons(unit, only: Optional[List[str]]):
    return unit.lesson_specs(only)


@app.command("new-unit")
def new_unit(dest: Path, course: str = typer.Option(...), unit: str = typer.Option(...),
             title: str = typer.Option(...), period: str = ""):
    """Start a unit folder from templates/unit."""
    if dest.exists() and any(dest.iterdir()):
        raise typer.BadParameter(f"{dest} already exists and is not empty")
    shutil.copytree(TEMPLATES, dest, dirs_exist_ok=True)
    y = dest / "unit.yaml"
    y.write_text(y.read_text(encoding="utf-8").format(course=course, unit=unit, title=title, period=period),
                 encoding="utf-8")
    for d in ("input", "output", "assets", "_temp"):
        (dest / d).mkdir(exist_ok=True)
    _out(f"created {dest}. Put sources in input/, then: lesson-builder ingest {dest / 'input'} -o {dest / '_temp/ingest'}")


@app.command()
def ingest(sources: List[Path], out: Path = typer.Option(..., "-o"), render: bool = True):
    """Source DOCX/PDF -> Markdown (math kept), images, and page renders."""
    from .ingest import ingest as run
    files = [f for s in sources for f in (sorted(s.glob("*.docx")) + sorted(s.glob("*.pdf")) if s.is_dir() else [s])]
    for md in run(files, out, render=render):
        _out(f"wrote {md}")


def _pairs(unit, l):
    hp = l.max_pages or unit.budget.handout_pages
    return [("handout", "key", hp), ("practice", "practice_key", unit.budget.practice_pages)]


@app.command()
def check(unit_dir: Path, lesson: Optional[List[str]] = typer.Option(None, "--lesson", "-l"),
          outputs: bool = typer.Option(True, help="also check rendered PDFs in output/")):
    """Spec checks (answers, blanks, refs, minutes, points, key figures) and output checks."""
    from .check import check_outputs, check_spec, summarize
    from .render import outputs as out_paths
    unit = load_unit(unit_dir)
    specs = _lessons(unit, lesson)
    figs = _figures(unit, docs={l.stem for l in specs})
    issues = []
    for l in specs:
        issues += check_spec(unit, l, _figs_for(figs, l))
        if outputs:
            o = {k: v.with_suffix(".pdf") for k, v in out_paths(unit, l).items()}
            for a, b, n in _pairs(unit, l):
                if a in o and b in o and o[a].exists() and o[b].exists():
                    issues += check_outputs(o[a], o[b], n)
    for i in issues:
        _out(i)
    e, w = summarize(issues)
    _out(f"{e} errors, {w} warnings")
    raise typer.Exit(1 if e else 0)


@app.command("check-pdfs")
def check_pdfs(student: Path, key: Path, max_pages: int = 3):
    """Output checks for any student/key PDF pair (also for documents not built from YAML)."""
    from .check import check_outputs, summarize
    issues = check_outputs(student, key, max_pages)
    for i in issues:
        _out(i)
    e, w = summarize(issues)
    _out(f"{e} errors, {w} warnings")
    raise typer.Exit(1 if e else 0)


@app.command()
def build(unit_dir: Path, lesson: Optional[List[str]] = typer.Option(None, "--lesson", "-l",
                                                                     help="file stem or id; repeatable"),
          fit: bool = True, strict: bool = False, packets: bool = True, force_figures: bool = False):
    """Figures -> DOCX -> PDF (fit to page budget) -> renders, diff, checks, packets."""
    from .check import check_outputs, check_spec, summarize
    from .diff import diff_renders, snapshot
    from .export import pdf_to_pngs
    from .fit import build_lesson
    from .render import Figures
    unit = load_unit(unit_dir)
    specs = _lessons(unit, lesson)
    if lesson and not specs:
        raise typer.BadParameter(f"no document matches {lesson}")
    figs = _figures(unit, force_figures, docs={l.stem for l in specs})
    issues = []
    tmp = unit.dir / "_temp"
    for l in specs:
        lf = _figs_for(figs, l)
        spec_issues = check_spec(unit, l, lf)
        issues += spec_issues
        if strict and summarize(spec_issues)[0]:
            _out(f"{l.id}: spec errors, not built (--strict)")
            continue
        docx, pdfs, pages = build_lesson(unit, l, Figures(unit, lf), fit=fit, log=_out)
        _out(f"{l.id}: " + ", ".join(f"{k} {n}p" for k, n in pages.items()))
        for a, b, n in _pairs(unit, l):
            if a in pdfs and b in pdfs:
                issues += check_outputs(pdfs[a], pdfs[b], n)
        cur = tmp / "renders" / "current" / l.stem
        if cur.exists():
            shutil.rmtree(cur)
        for p in pdfs.values():
            pdf_to_pngs(p, cur)
        prev = tmp / "renders" / "previous" / l.stem
        changed = diff_renders(cur, prev, tmp / "renders" / "diff" / l.stem) if prev.exists() else ["(first build)"]
        snapshot(cur, prev)
        _out(f"   pages to review ({cur}): {', '.join(changed) if changed else 'none changed'}")
    if packets and unit.packets and not lesson:
        _packets(unit)
    for i in issues:
        _out(i)
    e, w = summarize(issues)
    _out(f"{e} errors, {w} warnings. Renders: {tmp / 'renders' / 'current'}")
    raise typer.Exit(1 if e else 0)


def _packets(unit):
    """Duplex packets of the lessons (handout + practice; key + practice key). Assessments stay separate."""
    from .packet import docx_packet, pdf_packet
    from .render import outputs as out_paths
    out = unit.dir / "output"
    name = f"{unit.course} Unit {unit.unit}"
    lessons = [l for l in unit.lesson_specs() if l.doc_type == "lesson"]
    if not lessons:
        return
    for label, kinds in (("Student Packet", ("handout", "practice")), ("Key Packet", ("key", "practice_key"))):
        groups = []
        for l in lessons:
            o = out_paths(unit, l)
            groups.append([o[k] for k in kinds if k in o])
        missing = [p for g in groups for p in g if not p.with_suffix(".pdf").exists()]
        if missing:
            _out(f"{label}: skipped, not built yet: {', '.join(p.stem for p in missing)}")
            continue
        n, starts = pdf_packet([[p.with_suffix(".pdf") for p in g] for g in groups], out / f"{name} {label}.pdf")
        m = docx_packet(groups, out / f"{name} {label}.docx")
        _out(f"{name} {label}: PDF {n}p (lessons start {starts}), DOCX {m}p")


@app.command()
def figs(unit_dir: Path, lesson: Optional[List[str]] = typer.Option(None, "--lesson", "-l"),
         sheet: bool = typer.Option(True, help="write a contact sheet per document"), force: bool = False):
    """Figures only (seconds): render, lint labels, check printed text size, write contact sheets.
    Loop on this until it is clean, then run `build`."""
    from .check import check_figures, placed_widths, summarize
    from .figures.sheet import contact_sheet
    unit = load_unit(unit_dir)
    specs = _lessons(unit, lesson)
    rendered = _figures(unit, force, docs={l.stem for l in specs})
    issues = []
    for l in specs:
        lf = _figs_for(rendered, l)
        own = rendered.get(l.stem, {})
        issues += check_figures(l, lf)
        if sheet and own:
            widths = {n: max(w for _, w, _ in uses) for n, uses in placed_widths(l, lf).items() if n in own}
            out = contact_sheet(own, unit.dir / "_temp" / "figures" / f"{l.stem}_sheet.png", widths)
            _out(f"{l.id}: {len(own)} figures -> {out}")
    for i in issues:
        _out(i)
    e, w = summarize(issues)
    _out(f"{e} errors, {w} warnings")
    raise typer.Exit(1 if e else 0)


@app.command()
def packet(unit_dir: Path):
    """Rebuild the duplex student and key packets from existing outputs."""
    _packets(load_unit(unit_dir))


def main():
    app()

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


def _figures(unit, force=False) -> dict:
    if not unit.figures or not (unit.dir / unit.figures).exists():
        return {}
    from .figures import render_all
    return render_all(unit.dir / unit.figures, unit.dir / "_temp" / "figures", force=force)


def _lessons(unit, only: Optional[List[str]]):
    specs = unit.lesson_specs()
    return [l for l in specs if not only or l.id in only]


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


@app.command()
def check(unit_dir: Path, lesson: Optional[List[str]] = typer.Option(None, "--lesson", "-l"),
          outputs: bool = typer.Option(True, help="also check rendered PDFs in output/")):
    """Spec checks (answers, blanks, refs, minutes, key figures) and output checks."""
    from .check import check_outputs, check_spec, summarize
    from .render import outputs as out_paths
    unit = load_unit(unit_dir)
    figs = _figures(unit)
    issues = []
    for l in _lessons(unit, lesson):
        issues += check_spec(unit, l, figs)
        if outputs:
            o = {k: v.with_suffix(".pdf") for k, v in out_paths(unit, l).items()}
            pairs = [("handout", "key", unit.budget.handout_pages), ("practice", "practice_key", unit.budget.practice_pages)]
            for a, b, n in pairs:
                if a in o and o[a].exists() and o[b].exists():
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
def build(unit_dir: Path, lesson: Optional[List[str]] = typer.Option(None, "--lesson", "-l"),
          fit: bool = True, strict: bool = False, packets: bool = True, force_figures: bool = False):
    """Figures -> DOCX -> PDF (fit to page budget) -> renders, diff, checks, packets."""
    from .check import check_outputs, check_spec, summarize
    from .diff import diff_renders, snapshot
    from .export import pdf_to_pngs
    from .fit import build_lesson
    from .render import Figures
    unit = load_unit(unit_dir)
    figs = _figures(unit, force_figures)
    resolver = Figures(unit, figs)
    issues, built = [], []
    tmp = unit.dir / "_temp"
    for l in _lessons(unit, lesson):
        spec_issues = check_spec(unit, l, figs)
        issues += spec_issues
        if strict and summarize(spec_issues)[0]:
            _out(f"{l.id}: spec errors, not built (--strict)")
            continue
        docx, pdfs, pages = build_lesson(unit, l, resolver, fit=fit, log=_out)
        built.append((l, docx, pdfs))
        _out(f"{l.id}: " + ", ".join(f"{k} {n}p" for k, n in pages.items()))
        if "handout" in pdfs:
            issues += check_outputs(pdfs["handout"], pdfs["key"], unit.budget.handout_pages)
        if "practice" in pdfs:
            issues += check_outputs(pdfs["practice"], pdfs["practice_key"], unit.budget.practice_pages)
        cur = tmp / "renders" / "current" / l.id
        if cur.exists():
            shutil.rmtree(cur)
        for p in pdfs.values():
            pdf_to_pngs(p, cur)
        prev = tmp / "renders" / "previous" / l.id
        changed = diff_renders(cur, prev, tmp / "renders" / "diff" / l.id) if prev.exists() else ["(first build)"]
        snapshot(cur, prev)
        _out(f"   pages to review: {', '.join(changed) if changed else 'none changed'}")
    if packets and unit.packets and not lesson:
        _packets(unit)
    for i in issues:
        _out(i)
    e, w = summarize(issues)
    _out(f"{e} errors, {w} warnings. Renders: {tmp / 'renders' / 'current'}")
    raise typer.Exit(1 if e else 0)


def _packets(unit):
    from .packet import docx_packet, pdf_packet
    from .render import outputs as out_paths
    out = unit.dir / "output"
    name = f"{unit.course} Unit {unit.unit}"
    for label, kinds in (("Student Packet", ("handout", "practice")), ("Key Packet", ("key", "practice_key"))):
        groups = []
        for l in unit.lesson_specs():
            o = out_paths(unit, l)
            groups.append([o[k] for k in kinds if k in o])
        n, starts = pdf_packet([[p.with_suffix(".pdf") for p in g] for g in groups], out / f"{name} {label}.pdf")
        m = docx_packet(groups, out / f"{name} {label}.docx")
        _out(f"{name} {label}: PDF {n}p (lessons start {starts}), DOCX {m}p")


@app.command()
def packet(unit_dir: Path):
    """Rebuild the duplex student and key packets from existing outputs."""
    _packets(load_unit(unit_dir))


def main():
    app()

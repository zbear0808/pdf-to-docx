"""Render, export, and shrink workspace until each document fits its page budget."""
from __future__ import annotations

from pathlib import Path

from .export import docx_to_pdf
from .pagefill import mismatch, overflow, page_report, pinned, slack_list, summary_line, uneven
from .render import Figures, render_lesson
from .spec import LessonSpec, UnitSpec

STEP = 0.88       # workspace multiplier per round
FLOOR = 0.6       # never shrink workspace below 60%
GROUP = {"handout": "handout", "key": "handout", "practice": "practice", "practice_key": "practice"}
PAIRS = (("handout", "key"), ("practice", "practice_key"))


def _reports(pdfs: dict, log=print) -> dict:
    out = {}
    for k in GROUP:
        if k in pdfs:
            try:
                out[k] = page_report(pdfs[k])
            except Exception as e:  # a report must never break a build
                out[k] = []
                log(f"  page-fill report failed for {pdfs[k].name}: {e}")
    return out


def _summary(lesson: LessonSpec, rep: dict, budget: dict, scale: dict, log):
    for k, r in rep.items():
        if not r:
            continue
        log(f"  {lesson.id} " + summary_line(k, r, budget[k]))
        for w in uneven(k, r, shrunk=scale[GROUP[k]] < 1.0):
            log(f"  {lesson.id} {w}")
    for a, b in PAIRS:
        if rep.get(a) and rep.get(b):
            m = mismatch(b, rep[a], rep[b])
            if m:
                log(f"  {lesson.id} {m}")


def build_lesson(unit: UnitSpec, lesson: LessonSpec, figs: Figures, fit: bool = True, log=print,
                 reports: dict | None = None):
    """Returns (docx_paths, pdf_paths, page_counts), all keyed like render.outputs(). If `reports` is a dict,
    it is filled with the final page-fill report per document (pagefill.PageFill lists)."""
    hp = lesson.max_pages or unit.budget.handout_pages
    budget = {"handout": hp, "key": hp, "practice": unit.budget.practice_pages,
              "practice_key": unit.budget.practice_pages}
    scale = {"handout": 1.0, "practice": 1.0}
    while True:
        docx = render_lesson(unit, lesson, figs, scale)
        exported = docx_to_pdf(list(docx.values()))
        pdfs = {k: p for k, (p, _) in zip(docx, exported)}
        pages = {k: n for k, (_, n) in zip(docx, exported)}
        rep = _reports(pdfs, log)
        if reports is not None:
            reports.clear()
            reports.update(rep)
        over = {GROUP[k] for k in GROUP if k in pages and pages[k] > budget[k]}
        if not fit or not over:
            _summary(lesson, rep, budget, scale, log)
            return docx, pdfs, pages
        for k in GROUP:
            if GROUP[k] in over and rep.get(k):
                msg = overflow(rep[k], budget[k])
                if msg:
                    log(f"  {lesson.id} {k} OVER: {msg}; slack {slack_list(rep[k])}")
                hint = pinned(rep[k], budget[k])
                if hint:
                    log(f"  {lesson.id} {k}: {hint}; shrinking only helps if the pages before it merge")
        shrunk = False
        for grp in over:
            if scale[grp] * STEP >= FLOOR:
                scale[grp] *= STEP
                shrunk = True
                log(f"  {lesson.id} {grp}: over {budget[grp]} pages, workspace x{scale[grp]:.2f}")
        if not shrunk:
            log(f"  {lesson.id}: still over budget at minimum workspace; cut content (lesson-scope)")
            _summary(lesson, rep, budget, scale, log)
            return docx, pdfs, pages


def outputs_dir(unit: UnitSpec) -> Path:
    return unit.dir / "output"

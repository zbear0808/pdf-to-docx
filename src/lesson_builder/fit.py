"""Render, export, and shrink workspace until each document fits its page budget."""
from __future__ import annotations

from pathlib import Path

from .export import docx_to_pdf
from .render import Figures, render_lesson
from .spec import LessonSpec, UnitSpec

STEP = 0.88       # workspace multiplier per round
FLOOR = 0.6       # never shrink workspace below 60%


def build_lesson(unit: UnitSpec, lesson: LessonSpec, figs: Figures, fit: bool = True, log=print):
    """Returns (docx_paths, pdf_paths, page_counts), all keyed like render.outputs()."""
    hp = lesson.max_pages or unit.budget.handout_pages
    budget = {"handout": hp, "key": hp, "practice": unit.budget.practice_pages,
              "practice_key": unit.budget.practice_pages}
    scale = {"handout": 1.0, "practice": 1.0}
    while True:
        docx = render_lesson(unit, lesson, figs, scale)
        exported = docx_to_pdf(list(docx.values()))
        pdfs = {k: p for k, (p, _) in zip(docx, exported)}
        pages = {k: n for k, (_, n) in zip(docx, exported)}
        over = {grp for k, grp in (("handout", "handout"), ("key", "handout"), ("practice", "practice"),
                                   ("practice_key", "practice")) if k in pages and pages[k] > budget[k]}
        if not fit or not over:
            return docx, pdfs, pages
        shrunk = False
        for grp in over:
            if scale[grp] * STEP >= FLOOR:
                scale[grp] *= STEP
                shrunk = True
                log(f"  {lesson.id} {grp}: over {budget[grp]} pages, workspace x{scale[grp]:.2f}")
        if not shrunk:
            log(f"  {lesson.id}: still over budget at minimum workspace; cut content (lesson-scope)")
            return docx, pdfs, pages


def outputs_dir(unit: UnitSpec) -> Path:
    return unit.dir / "output"

---
name: visual-layout-checker
description: Read-only Audit step for lesson-builder documents. Runs `lesson-builder check`, then inspects built page renders and figure sheets for what scripts can't judge (legibility, figure fidelity to the problem, crowding, split items, room to write, B&W student copies, key matching the student layout, retained figures) and writes `_temp/specs/<stem>/audit.md` with Must fix / Should fix / Looks fine, each mapped to a YAML or figure-file fix. Never edits files.
---

# Visual layout checker (Audit step)

This skill is designed to run as a read-only subagent; it never edits files. It reports what to fix and where; the YAML or Figures step makes the fix. If subagents aren't available, run it in sequence in the same session, still without editing. Teaching quality (wording, MLL supports, rubrics, frames that give answers away) is judged by `assessment-builder`, `mll-literacy-scaffolding`, and `handout-release-check`. This skill covers how the pages look and whether the figures are right.

## Inputs

- Unit `units/<course>/<unit-slug>/` and document stem (YAML file stem).
- `_temp/specs/<stem>/requirements.md` (blueprint and figure plan) and `changes.md` (GAP lines, known workarounds).
- Built PDFs in `output/`, page renders in `_temp/renders/current/<stem>/` (`<pdf>_p<n>.png`), diffs in `_temp/renders/diff/<stem>/`.
- Figure contact sheet `_temp/figures/<stem>_sheet.png` and figure source `figures/<stem>.py`.
- Retained figures in `output/figures/<stem>/` with `README.md` (written and verified by the build).
- The build log's page-fill lines (`<kind> Np/budget: p1 0.4 in [1-3]; ...`, `OVER`, "empty while ... is full", key/student mismatch) when the orchestrator passes them. Don't rebuild to get them; without them, judge page fill from the renders.

All `_temp/` and `output/` paths are inside the unit folder.

## Procedure

1. Run `uv run lesson-builder check units/<course>/<unit-slug> -l <stem>`, `uv run lesson-builder figs units/<course>/<unit-slug> -l <stem>`, and `uv run lesson-builder retain units/<course>/<unit-slug> -l <stem> --verify-only`. For assessment forms, also `uv run lesson-builder integrity units/<course>/<unit-slug> --set "<set>*"` (add `--vs "<review>"` for a review). Copy every ERROR and WARN line into `audit.md` as written. Don't re-judge them by eye. `uv run lesson-builder status units/<course>/<unit-slug>` shows whether the outputs are stale against the YAML.
2. Open the pages listed under "pages to review" first, then the rest of the student copy and the key page by page. The build renders at 110 dpi; for a close look at small text, save a script in `_temp/build/` that calls `lesson_builder.export.pdf_to_pngs(pdf, out_dir, dpi=200)` with `out_dir` under `_temp/renders/audit/<stem>/`, and run it with `uv run python _temp/build/<script>.py`. Don't use `python -c`.
3. Open the contact sheet and compare each figure to its item and to the figure plan.
4. For a PDF not built from YAML, use `uv run lesson-builder check-pdfs <student.pdf> <key.pdf> --max-pages <n>` and render it with the same saved-script approach.
5. Work through the checklist, then write `audit.md`.

## Checklist

**Figures**
- Labels, numbers, and angle marks are readable at print size and don't touch lines, dots, or each other.
- The figure matches the problem: given lengths and angles look like their values, shapes the prompt calls equal or different look that way, points named in the prompt are on the figure, primes sit against the letter.
- No circles squashed or figures stretched. Background is white.
- Student copy is black and white with no red and no answer marks. Source images carry no colour and aren't blurry.
- Key figure shows the full answer in red on the same frame as the student figure.

**Page layout**
- No item, part list, or figure split across a page break; no heading stranded at the bottom of a page.
- Room to write matches the task: about 0 to 0.3 in for a choice or one number, 0.6 to 1.0 in for multi-step work, 1.0 to 1.5 in for a proof, construction, or drawing.
- Side-by-side figures don't crowd the prompt; wide figures are stacked. No large empty block on one page while another is crammed.
- Fill-in boxes and frames are labeled and wide enough; no `___` blanks.
- Page count is within budget; no trailing page with a few lines.

**Key and retention**
- Key has the same pages and item positions as the student copy; every item and part has an answer in red. Red appears only on the key. A page-fill line "item N is on key pX but student pY" is a Must fix.
- `retain --verify-only` is clean: the bundle matches the final DOCX images. Skim the README for an item with no figure source.

## Fix table

Recommend the fix in the source. Never the DOCX, never a font size change.

| Defect | Fix |
|---|---|
| Figure text small or label warning | Raise the item's `fig_w` (the check message gives the value for 9 pt); if the figure is crowded, enlarge `width_in`/`height_in` or move points apart in `figures/<stem>.py` |
| Label in the wrong place for the math | `direction=` on that label; `fixed=True` only if the auto spot is wrong |
| Figure doesn't match the problem | Change the points in `figures/<stem>.py` and add an assert for the value |
| Answer visible on the student copy | Move that ink to `layer="answer"` |
| Figure crowds the prompt | `layout: stacked` on the item, or smaller `fig_w` if text stays ≥ 9 pt |
| Wide figure squeezed beside text | `layout: stacked` |
| Too little room to write | Raise the item's `work:` |
| Item split or heading stranded | `page_break_after: true` on the item before, or `page_break_before: true` on the section or practice row |
| Over the page budget or blank space at the end | Cut content with `lesson-scope`; don't shrink fonts or `work` below what the task needs |
| Colour or blurry source image | Redraw it as an `@figure`, or replace with a B&W image at ≥ 150 dpi at `fig_w` |
| Key layout differs from student | Report as Must fix with page and item; it is a builder issue for the orchestrator (GAP line) |
| Retained figures stale or missing | Rebuild the document (`build` retains and verifies); don't copy PNGs by hand |
| Page-fill "p2 has 2 in empty while p1 is full; page break before ..." | Remove or move that `page_break_after` / `page_break_before`, or adjust `work:` on the items named |

## `audit.md` format

```markdown
# Audit: <stem>  (<date>)
Inputs: <PDFs, render folder, sheet>
Script results: <N errors, M warnings>, then each line as printed

## Must fix
- <student|key> p<n>, item <k>: <what is wrong> -> <fix from the table, file and field>

## Should fix
- ...

## Looks fine
- <short list of what was checked and passed>
```

Must fix: wrong or missing answers, figures that contradict the problem, unreadable text, answers or red on the student copy, split items, over budget. Should fix: tight work space, crowding, uneven pages, stale retained figures. Keep each line to one defect with its page, item, and fix.

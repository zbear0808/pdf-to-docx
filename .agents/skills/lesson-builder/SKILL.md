---
name: lesson-builder
description: Builds a unit's lesson handouts, lesson keys, practice sets, practice keys, teacher guides, assessments (progress checks, quizzes, tests, retakes, reviews), reference sheets, and duplex packets from one YAML file per document, for any math course. Use for any new or revised lesson or assessment; it replaces hand-written build scripts, draft.md, and worksheet-packer. Covers unit setup, source ingest, YAML, figures with answer layers, build, checks, review, figure retention, and how the orchestrator splits the work into subagent steps.
---

# Lesson builder

One YAML per document is the only copy of the content. Never write per-document layout code or edit a DOCX.

- **Orchestrating** a lesson, unit, or assessment set: follow `references/orchestration.md`. It splits the work into Plan, Figures, Write + build, Audit, Fix, and Release steps, each run by its own subagent with handoff files in `_temp/specs/<stem>/`.
- **Writing YAML or figures** (as a step subagent): read `references/api_cheatsheet.md` first. Field reference: `templates/unit/lessons/example.yaml` and `templates/unit/assessments/example.yaml`. Design reference: `docs/lesson_builder.md`. `src/lesson_builder/spec.py` is authoritative.

## Unit layout

```text
units/<course>/<unit-slug>/
  unit.yaml                 course, period, budget, lessons, assessments globs (orchestrator only)
  lessons/<id>.yaml         one per lesson: handout + key, practice + key, teacher guide
  assessments/<stem>.yaml   one per form (A, B, Retake); doc_type: assessment | reference
  figures/<stem>.py         @figure functions for that document (stem = YAML file stem)
  figures/_helpers.py       optional helpers shared by this unit's figure files
  assets/<stem>/            source images reused as-is
  input/                    source documents
  output/                   deliverables, including output/figures/<stem>/
  _temp/                    ingest, figures, renders, specs (handoff files), build scratch
```

A shared `figures.py` in the unit root still loads (Unit 2 uses it), but new units use `figures/<stem>.py`. Name figures `<stem>_<item>` so names never collide.

## Workflow

1. **Set up the unit:** `uv run lesson-builder new-unit units/<course>/<unit-slug> --course Geometry --unit 3 --title "..." --period "Period 4"`. Put sources in `input/`. Add `assessments: [assessments/*.yaml]` to `unit.yaml` if the unit has assessments.
2. **Read the sources:** `uv run lesson-builder ingest units/.../input -o units/.../_temp/ingest`. This keeps the math text and writes `_media/` images and `_pages/` renders. Read the `.md` files; open the page PNGs only to see the figures.
3. **Plan** (`_temp/specs/<stem>/requirements.md`): `lesson-scope` (40 min, every item gets `minutes:`), `lesson-assessment-designer` (targets, evidence, structure), `classroom-context` (period). Assessments: blueprint with `points:` and a version table (`assessment-builder`). For a rewrite, cut repeated items before writing.
4. **Figures** (`curriculum-visual-generator`): reuse clean source images from `assets/<stem>/`. Draw new ones, and every answer drawing, in `figures/<stem>.py` with `@figure`. Student work goes on `layer="answer"`. Use `lesson_builder.figures` helpers and assert the math.
   - Labels place themselves: give the preferred side (`direction=`). Don't nudge offsets by hand or write fix scripts; `fixed=True` keeps a spot as written.
   - **Loop on `uv run lesson-builder figs units/... -l <stem>`** (seconds, no Word) until it reports 0 errors and no label warnings. Check `_temp/figures/<stem>_sheet.png`: every figure at print size, student and key. A label that still touches something means the figure is too small: enlarge it or move points apart.
   - Printed text under 7 pt is an error; the message says which `fig_w` reaches 9 pt. Colour or low-resolution source images are flagged; redraw them.
5. **Write the YAML:** follow `authentic-writer`, `assessment-builder/references/item-rules.md`, and `handout-release-check` §1-2 as you write. Every item and part has an `answer:`. Write the file in pieces (150 lines or fewer per write).
6. **Build:** `uv run lesson-builder build units/... -l <stem>`. This renders the figures, writes the DOCX, exports PDF with Word, shrinks workspace until each document fits its page budget, checks, diffs, and renders pages. At most 4 builds per document; fix every ERROR. A full build (no `-l`) makes the packets.
7. **Review:** open only the pages listed under "pages to review" (`_temp/renders/current/<stem>/`, diffs in `_temp/renders/diff/<stem>/`), using `visual-layout-checker`. Fix the YAML or the figure file and rebuild. Stop after 3 rounds and report what's left.
8. **Retain the figures** (manual, see below), then report.

## Rules

- Answers come from the same place as the figure. If an image comes from a known motion or dilation, compute the correspondence or scale factor and use it in the answer.
- If a document still doesn't fit at the smallest workspace, the build says so. Cut content (`lesson-scope`); don't shrink fonts.
- Lesson YAML, assessment YAML, `figures/`, and `assets/` are the source. `output/` and `_temp/` are rebuilt.
- A layout feature the YAML can't express goes in `src/lesson_builder/render.py` with a field in `spec.py`, a test, and a line in the matching `example.yaml`. A figure helper goes in `src/lesson_builder/figures/<subject>.py` with a test. Only the orchestrator changes `src/`; a step subagent logs a `GAP:` line in `_temp/specs/<stem>/changes.md` and uses the closest existing field.
- When the teacher flags a problem in one document, fix every instance of it in the unit.

## Figure retention

After the final build, the editable figure bundle for each document lives in `output/figures/<stem>/`:
- the student and key PNGs the document uses, copied from `_temp/figures/<stem>/` (and `_temp/figures/` for shared `figures.py` figures);
- `README.md` mapping item number → registered figure name → function in `figures/<stem>.py` (path relative to the unit), helper files (`figures/_helpers.py`, `src/lesson_builder/figures/...`), any data or seeds, source images by `assets/` path and original page, and the command to regenerate: `uv run lesson-builder figs units/<course>/<unit-slug> -l "<stem>"` from the repo root.

Don't copy the figure source into `output/`; the README points to it. Before delivery, regenerate from the saved source, rebuild, and confirm the retained images match the final documents. Link the bundle and the figure file in the handoff. The build doesn't do this step yet.

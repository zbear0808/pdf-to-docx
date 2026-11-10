---
name: lesson-builder
description: Builds a unit's lesson handouts, lesson keys, practice sets, practice keys, teacher guides, assessments (progress checks, quizzes, tests, retakes, reviews), reference sheets, and duplex packets from one YAML file per document, for any math course. Use for any new or revised lesson or assessment; it replaces hand-written build scripts, draft.md, and worksheet-packer. Covers unit setup, source ingest, YAML, figures with answer layers, build, checks, review, figure retention, and how the orchestrator splits the work into subagent steps.
---

# Lesson builder

One YAML per document is the only copy of the content. Never write per-document layout code or edit a DOCX.

- **Orchestrating** a lesson, unit, or assessment set: follow `references/orchestration.md`. It splits the work into Plan, Figures, Write + build, Audit, Fix, and Release steps, each run by its own subagent with handoff files in `_temp/specs/<stem>/`.
- **Step subagent:** read `_temp/specs/<stem>/brief_<step>.md` first (`lesson-builder brief` writes it), then `references/api_cheatsheet.md`. Field reference: `templates/unit/lessons/example.yaml` and `templates/unit/assessments/example.yaml`. Design reference: `docs/lesson_builder.md`. `src/lesson_builder/spec.py` is authoritative.

## Unit layout

```text
units/<course>/<unit-slug>/
  unit.yaml                 course, period, budget, lessons, assessments globs, targets (orchestrator only)
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

Commands run from the repo root as `uv run lesson-builder ...`.

1. **Set up:** `new-unit units/<course>/<unit-slug> --course Geometry --unit 3 --title "..." --period "Period 4"`. Put sources in `input/`, then `ingest units/.../input -o units/.../_temp/ingest` (math text, `_media/` images, `_pages/` renders).
2. **Start each document:** `scaffold <unit> <stem> --type lesson|assessment|reference [--forms A,B,Retake]`. It writes a YAML that loads and builds (open spots say TODO), `figures/<stem>.py`, `requirements.md` and `changes.md`, and adds the file to `unit.yaml`. Don't hand-create these files.
3. **Plan** (`requirements.md`): `lesson-scope` (40 min, every item gets `minutes:`), `lesson-assessment-designer` (targets, evidence, structure), `classroom-context` (period). Assessments: blueprint and version table (`assessment-builder`). For a rewrite, cut repeated items before writing.
4. **Figures** (`curriculum-visual-generator`): draw in `figures/<stem>.py` with the library helpers and asserts; student work goes on `layer="answer"`. Loop on `figs <unit> -l <stem>` (seconds, no Word) until 0 errors and no label warnings, and check `_temp/figures/<stem>_sheet.png`.
5. **Write the YAML:** follow `authentic-writer`, `assessment-builder/references/item-rules.md`, and `handout-release-check` §1-2. Every item and part has an answer. Use `id` + `{ref:id}` instead of typed "Problem N", and leave `work:` at its default unless the task needs more. Write in pieces (150 lines or fewer per write).
6. **Build:** `build <unit> -l <stem>`. It renders figures, checks the spec, writes DOCX, exports PDF, shrinks workspace to the page budget, checks outputs, prints the page-fill lines, retains and verifies the figure bundle, and renders pages. At most 4 builds per document; fix every ERROR. A full build (no `-l`) makes the packets.
7. **Review:** read the page-fill lines (`OVER`, "empty while ... is full", key/student mismatch), then open only the pages under "pages to review" with `visual-layout-checker`. Fix the YAML or figure file and rebuild. Stop after 3 rounds and report what's left.
8. **Before release:** `tidy <unit>` (then `--apply` for temp files and caches), `integrity` for assessment forms, `status <unit>` for the whole unit.

## Rules

- Answers come from the same place as the figure. If an image comes from a known motion or dilation, compute the correspondence or scale factor and use it in the answer.
- For scaled-rectangle problems, put the givens in the item's `model: {kind: scaled_rectangles, ...}` and use `{value:id.fact}` in prompts, answers, and scoring notes. Figures read it with `model_for_figure(__file__, id)`. Run `resolve <unit> -l <stem>` to inspect exact facts before `figs` or `build`. See `docs/lesson_builder.md` for fields and formats; other problem families still use the existing figure workflow.
- If a document still doesn't fit at the smallest workspace, the build says so and names the overflowing item. Cut content (`lesson-scope`); don't shrink fonts.
- Lesson YAML, assessment YAML, `figures/`, and `assets/` are the source. `output/` and `_temp/` are rebuilt.
- A layout feature the YAML can't express goes in `src/lesson_builder/render.py` with a field in `spec.py`, a test, and a line in the matching `example.yaml`. A figure helper goes in `src/lesson_builder/figures/<subject>.py` with a test. Only the orchestrator changes `src/`; a step subagent logs a `GAP:` line in `_temp/specs/<stem>/changes.md` and uses the closest existing field.
- When the teacher flags a problem in one document, fix every instance of it in the unit.

## Figure retention

`build` copies the student and key PNGs each document uses to `output/figures/<stem>/` and writes `README.md` (item → figure name → `figures/<stem>.py:function`, helper files, asset paths, and the `figs` / `build` / `retain` commands), then verifies the copies against the images in the built DOCX. A missing source or mismatch is an ERROR.

Check the build's `figures retained: <dir> (N files)` line and skim the README. Rerun `retain <unit> -l <stem>` only after a `--no-retain` build; `retain --verify-only` re-checks without copying. Link the bundle and the figure file in the handoff.

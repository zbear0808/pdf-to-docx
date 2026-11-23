---
name: lesson-builder
description: Manual for the lesson-builder tool, which builds lesson handouts, lesson keys, practice sets, practice keys, teacher guides, assessments (progress checks, quizzes, tests, retakes, reviews), reference sheets, and duplex packets from one YAML file per document. Covers the unit layout, the CLI commands, the YAML and figure workflow, the build and its checks, and figure retention. For running a lesson or assessment request end to end, use `lesson-orchestrator`; step subagents use their step skill plus `references/api_cheatsheet.md`.
---

# Lesson builder (tool manual)

One YAML per document is the only copy of the content. Never write per-document layout code or edit a DOCX.

- **Running a request** (a new lesson, a rewrite, an assessment set, or a unit pass): load `lesson-orchestrator`. It dispatches the steps to subagents: `lesson-plan-step`, `curriculum-visual-generator`, `lesson-write-step`, and `lesson-audit-step`. All of them follow `lesson-style`.
- **Field and command reference:** `references/api_cheatsheet.md`. Field templates: `templates/unit/lessons/example.yaml` and `templates/unit/assessments/example.yaml`. Design notes: `docs/lesson_builder.md`. `src/lesson_builder/spec.py` is authoritative.

## Unit layout

```text
units/<course>/<unit-slug>/
  unit.yaml                 course, period, budget (minutes: 30), lessons, assessments globs, targets
  lessons/<id>.yaml         one per lesson: handout + key, practice + key, teacher guide
  assessments/<stem>.yaml   one per form (A, B, Retake); doc_type: assessment | reference
  figures/<stem>.py         @figure functions for that document (stem = YAML file stem)
  figures/_helpers.py       optional helpers shared by this unit's figure files
  assets/<stem>/            source images reused as-is
  input/                    source documents
  output/                   deliverables, including output/figures/<stem>/
  archive/<date> <reason>/  snapshots of earlier versions (never deleted)
  _temp/                    ingest, figures, renders, specs (handoff files), build scratch
```

A copy of a unit (`<unit>-v2`, `<unit>-extra-support`) is a sibling folder with the same layout. Name figures `<stem>_<item>`.

## Commands (repo root, `uv run lesson-builder ...`)

1. **Set up:** `new-unit units/<course>/<unit-slug> --course Geometry --unit 3 --title "..." --period "Period 4"`. Put the sources in `input/`, then run `ingest units/.../input -o units/.../_temp/ingest` (math text, `_media/` images, `_pages/` renders).
2. **Start a document:** `scaffold <unit> <stem> --type lesson|assessment|reference [--forms A,B,Retake]`. It writes a YAML that loads and builds (open spots say TODO, and the lesson shape follows `lesson-style`), `figures/<stem>.py`, `requirements.md`, and `changes.md`, and adds the file to `unit.yaml`.
3. **Briefs:** `brief <unit> <stem> --step plan|figures|write|audit` writes `_temp/specs/<stem>/brief_<step>.md` for that step's subagent.
4. **Figures:** `figs <unit> -l <stem>` (seconds, no Word): lint, printed size, `_temp/figures/<stem>_sheet.png`.
5. **Build:** `build <unit> -l <stem> [--no-packets]`. It renders figures, checks the spec, writes the DOCX, and exports the PDF (Word, else OnlyOffice, else LibreOffice; the build prints which). It then fits pages, checks the outputs, prints the page-fill lines, retains and verifies the figure bundle, and renders pages. A full build (no `-l`) also makes the packets.
6. **Checks:**
   - `check <unit> [-l <stem>] [--no-outputs]`: spec, answer cues, and rendered PDFs.
   - `integrity <unit> --set "<set>*" [--vs "<review>"]`: forms and reviews.
   - `status <unit>`: open Must fix lines, stale outputs, bundles.
   - `tidy <unit> [--apply]`: temp files, orphan assets, unused figures.
7. **Packets:** `packet <unit> [-l STEM]... [--order by-lesson|lessons-first] [--name PREFIX]`.

## Rules

- **Answers come from the same place as the figure.** If an image comes from a known motion or dilation, compute the correspondence or scale factor and use it in the answer. For scaled rectangles, use the item `model:` and `{value:id.fact}` (`docs/lesson_builder.md`).
- **The builder handles key formatting:** key answers print bold and red, student copies are black and white, and key layout matches the student copy.
- **If a document doesn't fit at the smallest workspace,** the build says so and names the overflowing item. Cut content (`lesson-style` §4); don't shrink fonts.
- **The YAML, `figures/`, and `assets/` are the source.** `output/` and `_temp/` are rebuilt.
- **New layout features:** a feature the YAML can't express goes in `src/lesson_builder/render.py` with a field in `spec.py`, a test, and a line in the matching `example.yaml`. A figure helper goes in `src/lesson_builder/figures/<subject>.py` with a test. Only the orchestrator changes `src/`; a step subagent logs a `GAP:` line in `_temp/specs/<stem>/changes.md` and uses the closest existing field.

## Figure retention

`build` copies the student and key PNGs each document uses to `output/figures/<stem>/` and writes `README.md` (item, figure name, `figures/<stem>.py:function`, helper files, asset paths, and the `figs` / `build` / `retain` commands). It then verifies the copies against the images in the built DOCX; a missing source or a mismatch is an ERROR. `retain <unit> -l <stem> --verify-only` re-checks without copying.

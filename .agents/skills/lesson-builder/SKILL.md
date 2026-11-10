---
name: lesson-builder
description: Builds a unit's lesson handouts, lesson keys, practice sets, practice keys, teacher guides, and duplex packets from one YAML file per lesson, for any math course. Use for any new or revised lesson worksheet; it replaces hand-written build scripts. Covers new-unit setup, source ingest, lesson YAML, figures with answer layers, build, checks, and review.
---

# Lesson builder

One YAML per lesson is the only copy of the content. Never write per-lesson layout code. Design reference: `docs/lesson_builder.md`. Field reference: `templates/unit/lessons/example.yaml`.

## Workflow

1. **Set up the unit:** `uv run lesson-builder new-unit units/<course>/<unit-slug> --course Geometry --unit 3 --title "..." --period "Period 4"`. Put sources in `input/`.
2. **Read the sources:** `uv run lesson-builder ingest units/.../input -o units/.../_temp/ingest`. This keeps the math text and writes images and page renders. Read the `.md` files; open the page PNGs only to see the figures.
3. **Plan:** `lesson-scope` (40 min, give each item `minutes:`), `lesson-assessment-designer` (pedagogy), `classroom-context` (period). For a rewrite, cut repeated items before writing.
4. **Write `lessons/<id>.yaml`:** follow `authentic-writer`, `item-rules.md`, and `handout-release-check` §1-2 as you write. Every item and part has an `answer:`.
5. **Figures:** reuse clear source images from `assets/`. Draw new ones and every answer drawing in `figures.py` with `@figure`. Put student work on `layer="answer"`, and use `lesson_builder.figures` helpers (rigid motions, `correspondence`, `needs_reflection`, `congruent_pair`, `rotation_build`). Assert the math. Other subjects add their own helpers to `src/lesson_builder/figures/` (for example `coordinate.py`, `stats.py`), not to unit files.
6. **Build:** `uv run lesson-builder build units/...`. This renders the figures, writes the DOCX, exports PDF with Word, shrinks workspace until each document fits its page budget, checks, diffs, and makes packets. Use `-l 2.1` for one lesson; packets need a full build.
7. **Review:** open only the pages listed under "pages to review" (diffs are in `_temp/renders/diff/`). Fix the YAML or `figures.py`, never the DOCX, and rebuild. Stop after 3 rounds and report what's left.

## Rules

- Answers come from the same place as the figure. If an image comes from a known motion, compute the correspondence and use it in the answer.
- If a lesson still doesn't fit at the smallest workspace, the build says so. Cut content (`lesson-scope`); don't shrink fonts.
- Outputs go to `units/.../output/` (gitignored). Lesson YAML, `figures.py`, and `assets/` are the source.
- After the final build, retain the actual student/key figure images used by each lesson and its practice set as final editable assets in `units/.../output/figures/<lesson-id>/`, not only the temporary render cache. Keep the canonical `figures.py` in the unit root; do not make per-lesson copies. Save all custom figure input data in the unit. If work is delegated, pass the unit path and these retention requirements to the agent.
- In each retained figure folder, add `README.md` mapping lesson/practice item numbers and image filenames to registered functions in `../../../figures.py` and the relevant lesson YAML. Record input data/seeds, shared helper paths/dependencies, and the exact command `uv run lesson-builder build <unit-path> -l <lesson-id>` run from the repository root. Identify reused assets by source path/page.
- Before delivery, verify regeneration from the saved source, inspect affected figures/pages, and refresh retained images to match the final documents. Link the lesson's figure folder and canonical `figures.py` in the handoff. Figure-retention checks are manual; the build does not perform this archival step automatically.
- A layout feature the YAML can't express goes in `src/lesson_builder/render.py` with a field in `spec.py`, a test, and a line in `example.yaml`. Don't work around it in one unit.

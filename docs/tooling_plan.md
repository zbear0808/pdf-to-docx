# Tooling and schema plan (Nov 2026)

Based on a review of `units/geometry/unit-2-congruent-triangles` and `units/geometry/unit-3-similarity`, the lesson-builder source, and `docs/workflow_painpoints.md`. Items already done in the pain-points list (label auto-placement, print-size and colour checks, `figs` contact sheets, box width, balanced `$`) are not repeated here.

## Status (Nov 9)

### Shared-data pilot implementation

The first follow-on milestone is implemented for `3.1-3.5 Progress Check A`, `B`, `Retake A`, and `Retake B`:

- The teacher chose to keep `/units*` ignored. The classroom unit remains local; a source-only snapshot of the
  four pilot forms is preserved in `tests/fixtures/shared_data_pilot/` so the regression suite runs in a clean checkout.
- Added schema version 1 and a checked `scaled_rectangles` item model using exact fractions. The pilot's item q3
  reads its givens once for figure dimensions, labels, prompt values, answers, and numerical scoring examples.
- Added `{value:item.fact|format}` resolution and `lesson-builder resolve` for inspecting intermediate data.
- Replaced the four copies of grid-dilation, rectangle, side-splitter, and line-family helpers with library calls.
- Added stable item IDs, auto numbering, structured keys, and set/form links to the four pilot YAMLs.
- Figure cache invalidation now includes the matching YAML and model/resolution code. Retention lists those
  helper imports. Tests cover all four forms and a numeric-only edit propagating through text, geometry, and PNGs.

This is a pilot adoption of T6, S1/S2, S8/S9 plus the shared-data extension. Full Unit 2/3 migration, model support
for the other item families, shared student/key layout planning, content-hash stage manifests, and automated
release remain subsequent milestones. The first-wave status table below is historical.

Pilot verification: all four strict builds and form-integrity/retention checks pass. Student and key copies
are two pages each, with one-page teacher notes. The migration preserves the resolved problem and answer text.
Visual audits record the existing small student/key vertical-position differences for the shared-layout milestone;
matching page counts alone does not close those findings.

| Item | Status | What remains |
|---|---|---|
| P0.1 gitignore | partial | `.gitignore` ignores only `input/`, `output/`, `_temp/`, `__pycache__/` under `units/`; Unit 3 is not committed yet |
| P0.2 Unit 3 Must fix | open | audit `SUMMARY.md` Must fix list not applied |
| T1 `retain` | done | build runs retain + verify (`--no-retain` skips); `retain --verify-only` |
| T2 MC + voice checks | done | `check.py` MC rules, `voice.py` banned list (keep in sync with `authentic-writer`); `check_draft.py` deleted |
| T3 `integrity` | done | heuristics; no district-exam comparison yet (needs S13 sources ingested) |
| T4 `scaffold` | done | |
| T5 `brief` | done | per step: `brief <unit> <stem> --step plan\|figures\|write\|audit` |
| T6 geometry helpers | partial | helpers, asserts, marks, templates done (`parallel_set` became `mark_parallel`); Unit 3 figure files not yet refactored onto them |
| T7 page-fill | partial | report, overflow, pinned-break, uneven and key/student mismatch lines done; per-page shrink and key pagination from the student layout need per-item scale in `render.py` |
| T8 other subjects | done | `coordinate`, `numberline`, `stats`, `cs` on `Figure.custom`; `pdf_to_docx/chart_generator.py` not retired |
| T9 `tidy` | done | |
| T10 kitchen-sink fixture | done | `tests/fixtures/kitchen_sink/` (lesson, Test A/B, Review, reference sheet; every field, template and figure module) built by `tests/test_kitchen_sink.py`, full `build` when Word is available. New fields land here first |
| T11 `status` | done | `wave.md` stays for session IDs |
| Small fixes | done | diff clearing, 3-digit labels, unknown figure ERROR, `$` message, money and block-prime WARNs, cache key, template `assessments:` line and `figures/example.py` |
| S1 ids and refs | done | `{ref:id}`, `{num:id}` everywhere, unknown id ERROR |
| S2 auto numbering | done | opt-in `numbering: auto` |
| S3 `work` default | partial | 0 for table/columns/draw, 0.2 for choices, `tidy` flags redundant lines; the figure-only `work: 0` default wasn't applied |
| S4 named frame rows | done | |
| S5 size words | partial | `fig: small\|medium\|wide`; no lint yet for `fig_w` far from the drawn width |
| S6 `selected: auto` | done | also bare numbers |
| S7 targets + metadata | done | coverage and all-procedural checks; blueprint in Teacher Notes |
| S8 forms | done | `set`, `form`, `parallel_to`, `do_not_reuse` |
| S9 `key` / `distractors` | done | distractor table in Teacher Notes |
| S10 `rubric` / `scoring: epi` | partial | rubric levels render on key and notes; no separate `communication` field |
| S11 QuickNotes blocks | done | |
| S12 `steps` / `bank` | done | |
| S13 `source` | done | listed in the retain README |
| S14 `columns: 2` | done | |
| S15 retire `header_right` | partial | only warns; fill `box_w` still per item |
| Figure core | done | `key_frame="union"`, prime-style lint, cache watches `_*.py`, library, `assets/` |

## What the two units show

| Finding | Evidence | Fix |
|---|---|---|
| Unit 3 isn't version controlled | `.gitignore:60` `units/*` ignores the whole unit; Unit 2 is tracked only because it was committed first | P0 below |
| Figure sources outlive their scripts | 4 Unit 2 assets were drawn by `unit2_congruent_triangles/_temp/build/figs.py`, an ignored folder, so they can't be regenerated | `retain` (T1), redraw in `figures/2.1.py` |
| Helpers copied between figure files | `_grid` ×8, `_parallel`/`_is_par` ×8, triangle-from-angles ×5, dilation task ×4, side splitter ×4, parallel marks reimplemented 3 ways; the 3.1-3.5 PC files are identical for ~118 lines | geometry helpers (T6) |
| One-off scripts in `_temp` | `3.9/build/fix1-4.py` (string-replace label nudges), `Unit 3 Test/sheet.py` (contact sheet) | mostly replaced by `figs`; the rest by T6 asserts |
| Same YAML noise everywhere | `work: 0` on 94 of 293 `work:` lines; 168 `fig_w`; 105 `box_w`; 18 unnamed 4th `frame` elements; 94 hard-coded "Problem N"; `selected` repeats item answers | schema S1-S6 |
| Audit fixes never applied | `_temp/specs/audit/SUMMARY.md` Must fix list; 23 spec errors still in Unit 3 (19 boxes under 0.9 in, 2 prints at 6.2 pt) | orchestration Fix step; `build --strict` at release |
| Exam integrity only by reading | 4 of 5 assessment audits: B mirrors A, Retake reuses A's letters, Notes print a Test answer | `integrity` (T3), schema S8 |
| Old-workflow litter | `output/Assessments/mso*.tmp`, `figures/__pycache__/`, orphan `assets/21_kite_orig.png`, stale `_temp/renders/diff/` | `tidy` (T9), `diff.py` clears old diffs |

## P0: before the next unit

1. Track unit sources: replace `units/*` in `.gitignore` with rules that ignore only `units/**/_temp/`, `units/**/output/`, `units/**/input/`, and `__pycache__/`, so `unit.yaml`, `lessons/`, `assessments/`, `figures/`, and `assets/` are committed. Then commit Unit 3.
2. Apply the Unit 3 audit Must fix list with the Fix step in `.agents/skills/lesson-builder/references/orchestration.md`.

## Reusable Python tools

Ranked by value per effort. Each new CLI command lives in `src/lesson_builder/cli.py` with a test.

| # | Tool | What it does | Replaces |
|---|---|---|---|
| T1 | `lesson-builder retain <unit> -l <stem>` (also run at the end of `build`) | Copies each figure the document uses (student and key PNG) to `output/figures/<stem>/` and writes `README.md`: item → figure name → `figures/<stem>.py:function` (via `inspect.getsourcelines`), helper modules imported, asset source paths, and the `figs` command. Fails if a used figure has no source or the retained PNG doesn't match the embedded one. | the manual retention step in 5 skills |
| T2 | MC and voice checks in `check.py` | Port `assessment-builder/scripts/check_draft.py`: key letter within `choices`, no letter on more than half the items, no run of 3, 3-4 choices, duplicate or empty choices, "all/none of the above", one choice much longer than the rest, banned words from `authentic-writer` (one shared list in `src/lesson_builder/voice.py`), dashes, exclamation points. Then delete `check_draft.py`. | `check_draft.py` (only reads `draft.md`) |
| T3 | `lesson-builder integrity <unit> --set "Unit 3 Test*" --vs "Unit 3 Review" ...` | Extracts per item: point letters, numbers, scale factors, side triples, angle measures, MC answer positions, and answers printed on figures (from figure labels in the JSON sidecars). ERROR on reuse across forms or between a test and its review/notes. | reading by hand (pain point 3) |
| T4 | `lesson-builder scaffold <unit> <stem> --type lesson\|assessment\|reference [--forms A,B,Retake]` | Writes a skeleton YAML (header, empty sections), `figures/<stem>.py` with `S = "<stem>"` and one example figure, and `_temp/specs/<stem>/requirements.md` with the five headings from orchestration.md. Adds the file to `unit.yaml` if a glob doesn't cover it. | the big first write that crashed 5 agents |
| T5 | `lesson-builder brief <unit> -l <stem>` | Writes `_temp/specs/<stem>/brief.md` for a step subagent: the schema subset for its doc type, one example per section kind, the ingested source text inline, page-image paths, figure names from the plan, and the files it owns. One read instead of ~30. | per-unit `brief.md` / `agent_instructions.md` written by hand |
| T6 | Geometry helpers (`figures/geometry.py`, tests in `tests/test_lesson_figures.py`) | Predicates: `is_parallel`, `collinear`, `on_ray`, `foot` (perpendicular), `extend` (ray or line to a box). Constructions: `triangle_from_angles(base, a1, a2)`, `triangle_sas`, `law_of_sines_side`. Asserts: `assert_dilation(center, src, img, k)`, `assert_lengths(fig, labels, tol=0.03)`, `assert_distinct(angles, min_deg=4)`. Marking: `mark_congruent(f, pairs, layer)` for ticks and arcs. Templates: `reflection_build`, `dilation_task(grid, center, pts, k, names)`, `side_splitter(tri, t, names)`, `parallel_set`. Export `dilate`/`similarity_ratio` in `geometry.__all__`. | the local copies listed above |
| T7 | Page-fill report in `fit.py` | Per page: slack in inches, items on the page (student and key), the item that overflows. Shrinks workspace per page instead of globally, and paginates the key from the student layout so "item numbers differ" can't happen. | 2-4 trial builds per document |
| T8 | Other-subject figure modules | `figures/coordinate.py` (axes with numbered ticks and arrows, points, lines, slope triangles), `numberline.py`, `stats.py` (dotplot, histogram, boxplot, scatter with line, two-way table, normal curve), `cs.py` (array boxes, reference diagrams, trace tables). Needs one core addition: `Figure.custom(fn, layer)` that gives a matplotlib axes in figure units, so charts still get layers, trimming, sidecars, and lint. | `pdf_to_docx/chart_generator.py` (no answer layer) |
| T9 | `lesson-builder tidy <unit>` | Lists or removes Word temp files (`mso*.tmp`, `~$*.docx`), `__pycache__/`, stale diff images, orphan assets (in `assets/` but not referenced), figures registered but never used, and YAML files not listed in `unit.yaml`. | manual cleanup |
| T10 | Kitchen-sink fixture | `tests/fixtures/kitchen_sink/` with one lesson and one assessment that use every field, built in pytest (DOCX only; PDF when Word is available). New fields land here first. | builder bugs found mid-wave |
| T11 | `lesson-builder status <unit>` | Reads `_temp/specs/*/` and the outputs: per document, which handoff files exist, last build result, error count, retained figures, open Must fix lines. The orchestrator's `wave.md` gets the same columns. | reading many files to see where a unit stands |

Also small fixes: `diff.py` clears `_temp/renders/diff/<stem>/` before writing; `check_outputs` label regex handles 3-digit numbers and parts past d; `check` reports an unresolved figure name as an ERROR instead of a `FileNotFoundError` at render; the odd-`$` error message stops suggesting `\$` (it isn't an escape, and `\$3 and \$5` crashes the build); new checks for `$` followed by a digit in prose and `''` inside block scalars (prints a double prime); the figure cache key includes `figures/_helpers.py` and `assets/`; `templates/unit/unit.yaml` gets an `assessments:` line and the template gets `figures/<stem>.py` for its example assessment (its `dilate_abc` figure doesn't exist today).

## YAML schema additions

All optional and backward compatible (current files keep loading). Each lands with a field in `spec.py`, renderer support, a check, a line in the matching `example.yaml`, and the kitchen-sink fixture.

| # | Addition | Example | Why |
|---|---|---|---|
| S1 | Item `id:` and `{ref:<id>}` in prompts, frames, `plan`, `guide_notes` | `id: arrow_table` … `'Use your table from {ref:arrow_table}.'` → "Problem 2" | 94 hard-coded references; cuts leave stale numbers; plan text isn't checked today |
| S2 | Auto numbering: omit `n:` and numbers follow the existing groups (restart at `notes`, practice separate) | | hand numbering in every file |
| S3 | Smarter `work` default. `render.py` already uses 0 when an item has `fill`, `frame`, `box`, or `parts` and `work` isn't set; extend that to `table`, `columns`, `draw`, and figure-only items, use 0.2 for `choices`, and have `tidy` flag `work:` lines that equal the default | | `work: 0` written 94 times, many of them redundant |
| S4 | Named frame rows, keeping the list form | `frame: [{before: 'Two pairs ... make a', answer: parallelogram, after: '.', w: 1.6}]` | the unnamed 4th element (18 uses) |
| S5 | Draw at print size. Without `fig_w` an image already prints at its natural (drawn) width, so most `fig_w` lines shrink figures drawn too big. Add size words for the common cases and a lint for `fig_w` far from the drawn width | `fig: small \| medium \| wide` | 168 hand-tuned `fig_w` lines; the print-size check already knows the drawn width |
| S6 | `practice.selected: auto` (or a list of item numbers) builds the selected-answers table from each item's `answer` | `selected: [1, 2, 7, 8]` | answers written twice and drifting |
| S7 | Item metadata for assessments and lessons: `target`, `type` (`sr`/`cr`/`performance`), `demand` (the four Smith & Stein levels), `standard`; document or unit `targets:` list | `targets: [{id: LT1, understand: '...', able_to: '...', standard: G.SRT.2}]`, item `target: LT1, type: cr, demand: pwc` | lets `check` verify target coverage and that the mix isn't all procedural; the teacher notes print the blueprint; replaces the hand-made blueprint table |
| S8 | Forms: `set`, `form`, `parallel_to`, `do_not_reuse` (globs) | `set: Unit 3 Test`, `form: B`, `parallel_to: Unit 3 Test A`, `do_not_reuse: ['Unit 3 Test*']` on the Review | input for `integrity` (T3); release can check every form exists |
| S9 | Structured MC key and distractor notes | `key: C`, `distractors: {A: 'added instead of multiplied', B: 'used the wrong pair'}` | letter checks without parsing `[C]`; distractor table generated into Teacher Notes instead of hand-written `guide_notes` |
| S10 | `rubric:` per item or part, and `scoring: epi` for AP Stats | `rubric: [{level: 4, desc: '...'}, ...]`, `communication: true` | rubric levels (3-6) and separate communication score become checkable and render into the key |
| S11 | Structured QuickNotes | `quicknotes: [{target: LT1, bullets: ['...', '...']}]` | flat Markdown strings with typed `**LT 1**` headings and `- ` bullets |
| S12 | `steps:` list and section `bank:` list | `steps: ['Trace ...', 'Rotate ...']`, `bank: [translate, reflect across a line, rotate around a point]` | "Step 1:" typed by hand; move banks pasted into prompts; literal `•` in Summary Notes |
| S13 | `source:` provenance per document and item | `source: 'Lesson 2.1 Practice p2 #3'` | rewrite tracking, `changes.md`, and integrity against the district exam |
| S14 | Two-column sections for assessments | `section: {columns: 2}` with `layout: cell` items | worksheet-packer's last unique feature; lets it retire for assessments |
| S15 | Retire `header_right` and the per-item `box_w` for frames once S4 lands | | the hand-written "Score ___" header fails its own blank check |

## Figure core changes

- **Key-only frame:** let the answer layer extend the canvas (`Figure(key_frame="union")`), so the 3.6 warm-up and nested figures don't need separate `_key` figures (and `_key_key.png` names).
- **Prime style:** one prime form in labels (`math_fix` already normalizes; add a lint that flags mixed forms in one file).
- **Cache:** covered in the small fixes above (`_helpers.py` and `assets/` in the cache key).

## Suggested order

1. P0 (gitignore, Unit 3 Must fix).
2. T1 `retain`, T2 MC/voice checks, S1-S4 (the biggest YAML noise), T10 fixture.
3. T6 geometry helpers, then refactor Unit 3 figure files onto them.
4. S7-S9 + T3 `integrity` before the next test set.
5. T4 `scaffold`, T5 `brief`, T11 `status` (orchestration speed).
6. T7 page-fill, T8 other subjects (before the first AP Stats or CSA unit), the rest.

When each lands, update `references/api_cheatsheet.md`, the matching skill step, and `docs/lesson_builder.md` in the same change.

---
name: assessment-builder
description: Orchestrates writing or rewriting a test, quiz, progress check, retake, review, or standalone worksheet for Franklin HS room 105 as lesson-builder YAML. Covers intake, a blueprint built with lesson-assessment-designer (targets, evidence, cognitive demand), exam integrity across forms (A, B, Retake), item and key rules, rubrics and scoring notes, MLL supports, figures, build, audit, and release. Each step runs as a subagent with handoff files. Use whenever the user asks to make, rewrite, adapt, or fix an assessment or worksheet.
---

# Assessment builder

Assessments are built with `lesson-builder` from one YAML per form: `units/<course>/<unit-slug>/assessments/<stem>.yaml` with `doc_type: assessment` (`reference` for notes sheets with no key). Start a set with `uv run lesson-builder scaffold <unit> "<set stem>" --type assessment --forms A,B,Retake`: one YAML per form with `set`, `form`, and `parallel_to` filled, and one shared `requirements.md`. The build writes `output/Assessments/<id>.docx`, `<id> Key.docx`, and `<id> Teacher Notes.docx` when there is a `plan`, `guide_notes`, distractor notes, or blueprint metadata. Lesson handouts go through `lesson-builder` directly.

You are the orchestrator. Run the steps in `.agents/skills/lesson-builder/references/orchestration.md` (Plan, Figures, Write + build, Audit, Fix, Release), one subagent per step and document. Give each subagent the sections of this skill its step needs, listed in the table. If subagents aren't available, run the steps in order in this session with the same files.

| Step | Give the subagent |
|---|---|
| 0. Intake (you) | "Intake" below, `classroom-context` (target period) |
| 1. Plan | "Exam integrity", "Blueprint", `lesson-assessment-designer` Steps 1-2 and its readings table, `mll-literacy-scaffolding` (Period 4 / MLLs), `course-content-extractor` (no source, or a new form is needed) |
| 2. Figures | `curriculum-visual-generator`, the figure plan and version table |
| 3. Write + build | "Writing the YAML", "Key, rubric, scoring notes", `references/item-rules.md`, `authentic-writer`, `handout-release-check` §1-2, `mll-literacy-scaffolding` (Period 4 / MLLs), `lesson-builder/references/api_cheatsheet.md` |
| 4. Audit | "Review checklist", `visual-layout-checker`, item-rules, `mll-literacy-scaffolding` checklist |
| 6. Release (you) | "Exam integrity", "Release" |

Handoff files live in `_temp/specs/<stem>/` (`requirements.md`, `changes.md`, `audit.md`). For a set of forms, one Plan subagent writes the version table for all of them, so use one shared folder, `_temp/specs/<set name>/`, and point every form at it.

## Exam integrity

If a source is a real exam that students have taken or will take, never copy an item verbatim into review, practice, or retake material. Keep the target, item type, cognitive demand, and points. Change the numbers, the figure's orientation and letters, the context, and the variable or method names. In Geometry, compare Form A to Form B first to see how much the district varies items.

- Form B and the Retake mirror A with new letters on every item, new numbers, and new MC answer positions. Record intended difficulty differences in `guide_notes`.
- The version table in `requirements.md` lists, per item and form: letters, numbers (scale factors, side triples, angle measures), motion types, and the MC answer position. Each form's YAML must match it.
- Reviews and summary notes are planned after the tests. The test YAMLs are their "do not reuse" list: no test numbers, figures, or answers (a 6-8-10 triple that answers Test A #5 can't appear in the notes).
- Record the links in YAML: `set: Unit 3 Test`, `form: B`, `parallel_to: Unit 3 Test A` on each form, and `do_not_reuse: ['Unit 3 Test*']` on a review or notes sheet.
- `uv run lesson-builder integrity <unit> --set "Unit 3 Test*" --vs "Unit 3 Review"` compares point letters, numbers (scale factors, side triples, angles), MC key positions, and figure labels between forms, and checks reviews and notes against the tests. Fix every ERROR. Then read for what it can't see: repeated contexts or motion types, a figure whose shape gives the answer away, difficulty drift between forms.

## Intake

Write the intake section of `_temp/specs/<stem>/requirements.md`:
- Mode: **rewrite** (improve an existing document) or **new** (build from targets or sources).
- Course and period, with the period profile in a few lines. Period 4 Geometry has many MLLs: item-rules §6 applies fully and `mll-literacy-scaffolding` is loaded in Plan, Write, and Audit. Period 5 AP Stats follows CED wording and E/P/I scoring. Period 6 AP CSA follows CodeHS Java style and uses tracing.
- Learning targets or standards, item types and counts, total points, page budget (`max_pages`), forms needed (A, B, Retake).
- Source files. Read them with `uv run lesson-builder ingest <unit>/input -o <unit>/_temp/ingest`.
- Anything the user said to keep or change.

Fill gaps from the sources and `classroom-context`. Ask the user only about things you can't infer and that change the output, such as the page budget or the points when no source gives them. Ask all questions at once. If the source's points don't add up to its stated total, scale to the total and log it in `changes.md`.

## Blueprint

Use `lesson-assessment-designer` Steps 1-2 before writing the table:
- Standards and learning targets in both forms (conceptual "understand that..." and skill "able to..."). Rewrite mode: recover them from the source and the unit's lesson YAMLs, and flag any missing ones. Assess what the lessons teach, in their notation, and don't test anything they cut.
- What evidence each target needs, and whether a selected-response, constructed-response, or performance item gives it. Performance tasks follow its Step 2 rules (purpose and audience, student-facing directions, criteria shared ahead, separate communication score).
- Standalone worksheets follow its Step 4 structure (warm-up, investigation, check for understanding, exit ticket).
- When you rely on a reading (Smith & Stein levels, T&N, Lotan), pull it from its readings table and cite only what the text says.

Table, one row per item: `n | target | type | demand (memorization / procedures without connections / procedures with connections / doing math) | points | figure name`. Check that it covers the targets and isn't all procedural. Rewrite mode: build it from the existing items and flag any item that doesn't fit a target. Then add the figure plan (coordinates, values to assert, answer layer) and the version table. The Write step copies the targets and each row's `target`, `type`, and `demand` into the YAML, where `check` verifies them and Teacher Notes print the blueprint.

## Writing the YAML

Start from `templates/unit/assessments/example.yaml`. Apply item-rules and `authentic-writer` while writing; don't plan a separate cleanup pass.

- Header fields: `id` (same as the file stem), `doc_type`, `title`, `directions`, `total_points` (the check errors if it doesn't equal the item and part points), `max_pages`, and for forms `set`, `form`, `parallel_to`, `do_not_reuse`. Leave `header_right` unset (check WARN); the builder prints Name, Per, and Score.
- `targets: [{id: LT1, understand: '...', able_to: '...', standard: G.SRT.2}]` (or the unit's `targets`). Each item gets `target`, `type` (`sr`/`cr`/`performance`), and `demand` (`mem`/`pwoc`/`pwc`/`dm`). The check errors on an unknown target and warns on a target with no items or an all-procedural mix.
- One `section` per target or part, with `target:` and the target in its `title`, so scores can be reported by target. `kind: plain` for no heading. `columns: 2` puts short items two per row.
- Set `numbering: auto` and leave out `n`; refer to items with `id` + `{ref:id}`. Every item gets `points` (or points on each part). Leave `work:` at its default (0 for boxes, frames, parts; 0.2 for choices) unless the task needs more room. Use `fill:` and `frame:` for answer space, never blank lines or `___`. Name, date, and period go only in the header.
- Each figure is a registered name from `figures/<stem>.py`, or an `assets/<stem>/` path. Variants redraw rather than reuse: the figure has to match the new numbers and letters.
- Period 4 / MLLs: apply the three Roberts enhancements (connect representations, unpack the language, build up the context), run the WIDA check (words, sentences, discourse) on directions and long stems, and add optional stems by language function on 1-3 explain items.
- Rewrite mode: keep the item order, numbering, points, figures, and math unless the user asked for changes or an item breaks a rule. Log each change in `changes.md`: `item: what changed | why (rule)`, for example `4: removed 'all of the above' | T&N7`.
- Standalone worksheet without points: `doc_type: assessment` with no `total_points` and no `points`.

## Key, rubric, scoring notes

- MC: `key: C` and a one-line reason in `answer:` (the key prints `[C]` first). `distractors: {A: 'added instead of multiplied', B: '...'}` per item; Teacher Notes build the distractor table from it. Select-all items: `key: 'B, D'` and `select_all: true`.
- Constructed response: a model answer in `answer:`, where each point comes from, acceptable alternatives, and "credit any valid method." AP Stats: `scoring: epi` on each part, with the E and P evidence in `answer:`.
- Rubrics: `rubric: [{level: 4, desc: '...'}, ...]` on the item or part, 3-6 specific levels. They print on the key and in Teacher Notes. Score communication on its own line (a separate rubric part) so English doesn't lower the content score.
- Period with MLLs: a short "Scoring notes" block in `guide_notes` (item-rules §8). Note which word problems to launch with 3-Reads if the teacher reviews them in class.
- Every item, part, and fill-in box has an answer. Drawing or marking items get an answer layer in the figure, not a description (`handout-release-check` §2).
- `lesson-builder check` handles the MC mechanics: key letter inside the choices and matching `[X]`, 3-4 choices, empty or duplicate choices, "all/none of the above", one choice much longer than the rest, a letter keying more than half the items, three of the same key in a row. Fix its warnings; judge distractor quality yourself.

## Review checklist

`lesson-builder build` and `check` catch missing answers, `___` blanks, narrow boxes, bad references, point totals, MC key letters and patterns, choice count and "all/none of the above", unknown targets and target coverage, banned words, dashes, and exclamation points, print size, and page budgets. `integrity` catches reuse across forms. Read for the rest:

- [ ] Every item matches a blueprint target, and the targets are covered.
- [ ] Each MC item has one defensible answer, distractors drawn from real errors, parallel options, 3-4 choices, and no "all/none of the above".
- [ ] Language load is down but the math is the same: math terms kept, dual-meaning words clear, visuals labeled, no idioms or insider contexts.
- [ ] Contexts are ordinary and every number has a purpose.
- [ ] It reads like a teacher wrote it: direct stems, nothing addressed to the reader at the start or end, no banned words from `authentic-writer`.
- [ ] Every fill-in is a labeled box under its problem, naming the figure it refers to.
- [ ] `lesson-assessment-designer` final check: real reasoning (not only recipes), every item measures a Stage 1 target, contexts do mathematical work.
- [ ] Period 4 / MLLs: the `mll-literacy-scaffolding` checklist passes, and the math goal and explain demand match what every other student gets.
- [ ] Forms follow the version table; nothing from a test appears in review or notes material.

## Release

1. `uv run lesson-builder check <unit> -l "<stem>"` for every form: 0 errors.
2. `uv run lesson-builder integrity <unit> --set "<set>*" [--vs "<review>"]`: 0 errors, then the reading pass in "Exam integrity".
3. Figure bundles: each form's build retained and verified `output/figures/<stem>/` (check the `figures retained` line).
4. Tell the user:
   - which files are in `output/Assessments/` and where the figure bundles are;
   - page count, point total, and how many items there are of each type, per form;
   - rewrite mode: the main changes from `changes.md`, grouped (e.g. "simplified 6 stems, replaced 2 'all of the above', added labels to 3 figures"), plus anything flagged but not changed;
   - any judgment calls the user should check and any Must fix items left in `audit.md`.

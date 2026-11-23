# Assessment pass: less is more, scaffolding, no headings (Nov 19)

Teacher: "We can also modify assessments. But for those we should go through our assessments skills." The teacher picked:
- **Apply:** less is more (cut items that repeat the same move), scaffold routine steps, cut extra wording, and fix existing check errors.
- **Section labels:** no headings. Items just run 1, 2, 3; targets show in the Teacher Notes blueprint.
- **Points:** let totals shrink. A cut item's points come off `total_points`.
- **Scope:** every assessment in Units 2, 3, and 4: progress checks, tests, retakes, reviews, summary notes, and the Trig Word Problems Practice.

Mode: **rewrite** (assessment-builder "Intake"). Keep each document's item order, numbers, figures, and math except where this pass changes them.

## 0. Load these skills first (required)

Use the `skill` tool, or read `.agents/skills/<name>/SKILL.md` in full:
- `assessment-builder`: all of it, especially "Exam integrity", "Blueprint", "Writing the YAML", the new "Less is more, and scaffold what isn't being measured", "Key, rubric, scoring notes", "Review checklist", and "Release". You are running its Plan and Write + build steps for your set; an independent Audit subagent follows.
- `.agents/skills/assessment-builder/references/item-rules.md`: all sections (§1 now says to scaffold steps outside the target; §6 language access for Period 4).
- `lesson-assessment-designer`: Steps 1-2 and the Final check.
- `lesson-scope`: "Less is more" and "Scaffold around the core idea" (the idea this pass carries over; on an assessment the "core" of an item is its blueprint target).
- `mll-literacy-scaffolding` (Period 4 has many MLLs), `authentic-writer` (including "Question stems and directions"), `handout-release-check` sections 1-2, `classroom-context` (Period 4 profile only).
- `curriculum-visual-generator` if you change a figure (moving routine labels or marks from the answer layer to the given layer counts).
- `.agents/skills/lesson-builder/references/api_cheatsheet.md`.

## 1. Plan (write it in the set's `requirements.md` before editing YAML)

Read every form's YAML and figure file, the set's `_temp/specs/<set or stem>/requirements.md`, `changes.md`, and `audit.md`, and the unit's lesson YAMLs. The lessons were revised on Nov 19 (core idea, no exit tickets), so test only what they still teach; don't test anything they cut. Then add a "## Nov 19 pass" section to `requirements.md`:
- **Blueprint** per form: `n | target | type | demand | points | figure | keep / cut / scaffold`. For each kept item add `measures = ... | scaffold = ...`: the target step the item measures, and the routine steps you will give students (computed values, labels, earlier-unit facts).
- **Cuts:** an item that makes the same move at the same demand as another item in the form, for the same target. Every target keeps at least one item per form (two when it carries most of the points). In a set of forms, the same item is cut in every form.
- **Version table:** update it for any cut, so forms still line up item for item. New `total_points` per form.

## 2. Write and build

- **No headings:** delete `title:` and `sub:` from every section of a test, progress check, review, or worksheet; keep `target:`; use `kind: plain`. Summary notes (`doc_type: reference`) keep one short heading per lesson, since they are a notes sheet organized by lesson; remove any subtitles.
- **Cuts:** remove the item, update `total_points`, `numbering`, `{ref:}` links, the plan or `guide_notes` scoring lines, and the version table.
- **Scaffold** the steps an item doesn't measure, the same way on every form. Never print the target step itself (if the item measures the scale factor, the scale factor isn't given).
- **Extra wording:** follow `units/geometry/_temp_lean_pass_instructions.md` and the assessment-builder rule. Drop all-caps warnings and exclamation points ("NO WORK = NO CREDIT!"); keep "Show your work." once in `directions` when work is scored.
- **Existing errors:** fix every `check` ERROR in your documents. Known one: Unit 3 Review key p1 "no answer for a. near y=1.6 in": item 1 writes parts a/b as prompt lines; make them real `parts:` with one answer each (3.4's changes.md has the same fix).
- `guide_notes`: add "**Nov 19: less is more, no headings.**" with one short paragraph: what was cut (with old item numbers), what was scaffolded, and the new total.
- `changes.md` (the set's folder): add "## Nov 19 pass", one line per change: `item: what changed | why (rule)`, ending with `points A -> B; items A -> B; pages A -> B` per form.
- Build each form: `uv run lesson-builder build <unit> -l "<stem>" --no-packets`, at most 4 builds per form, 0 errors. Other sets build at the same time; if the PDF export fails, rerun once.
- Then run `uv run lesson-builder integrity <unit> --set "<set>*"` for forms (add `--vs "<review or notes>"` for reviews and notes), and `uv run lesson-builder check <unit> -l "<stem>"` for each document. 0 errors. Do the reading pass from "Exam integrity".
- Look at every student and key page in `<unit>/_temp/renders/current/<stem>/`: no headings print, nothing is split from its figure, and the key matches the student layout.

## Files

Only the documents in your assignment: `assessments/<stem>.yaml`, `figures/<stem>.py`, `assets/<stem>/`, and `_temp/specs/<stem or set>/` inside the unit. Never edit `src/`, `templates/`, `.agents/`, `unit.yaml`, lessons, other assessments, or a DOCX. Unit 4 is not tracked in git: copy each YAML to `_temp/specs/<stem>/before_nov19/` before editing. Repo: `/Users/zubair/Documents/pdf-to-docx` (macOS, zsh, `uv run`); scratch scripts in `_temp/build/`. If the builder can't express something, use the closest field and log `GAP: ...` in `changes.md`.

## Reply (one block per document)

Items and points before -> after; what was cut (old numbers, why) and scaffolded; pages; check and integrity results. Then any judgment call the teacher should check.

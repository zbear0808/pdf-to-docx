# Assessment pass: Audit step (read-only)

You are the assessment-builder **Audit** step (`.agents/skills/lesson-builder/references/orchestration.md`, step 4) for one set of documents that was just rewritten under `units/geometry/_temp_assessment_pass_instructions.md` (read it: it has the teacher's decisions). You never edit lesson, assessment, figure, or source files.

## Load these skills first (required)

Use the `skill` tool, or read `.agents/skills/<name>/SKILL.md` in full: `assessment-builder` ("Exam integrity", the new "Less is more, and scaffold what isn't being measured", "Key, rubric, scoring notes", "Review checklist"), `.agents/skills/assessment-builder/references/item-rules.md`, `visual-layout-checker`, `handout-release-check`, `mll-literacy-scaffolding` (checklist), `lesson-assessment-designer` (Final check), `authentic-writer`.

## What to check

1. Run the read-only checks: `uv run lesson-builder check <unit> -l "<stem>"` for each document, and `uv run lesson-builder integrity <unit> --set "<set>*"` (add `--vs "<review or notes>"` for reviews and notes). Don't run `build`, `figs`, or `retain`.
2. Read each YAML against the set's `requirements.md` "Nov 19 pass" blueprint and version table, and `changes.md`:
   - The teacher's four decisions are carried out: repeats cut (and cut in every form), routine steps scaffolded the same way on every form, the target step not scaffolded, extra wording gone, no section headings on tests, progress checks, reviews, or worksheets (summary notes keep one short heading per lesson), totals reduced by the cut points.
   - Every target keeps at least one item per form, and the forms still line up item for item.
   - Keys: every item, part, and box has an answer; points add up; MC keys and distractors are sound; scoring notes match the new numbering.
   - Exam integrity reading pass: repeated contexts or motion types across forms, a figure whose shape gives an answer away, difficulty drift between forms, and items copied from the unit's lesson or practice YAMLs (`units/geometry/<unit>/lessons/*.yaml`).
3. Look at every student and key page in `<unit>/_temp/renders/current/<stem>/` (visual-layout-checker): legibility, figures with their items, room to write, key matching the student layout, no headings printing.

## Write

`_temp/specs/<stem>/audit.md` for each document (append a section "## Nov 19 pass audit"; keep older content): **Must fix** / **Should fix** / **Looks fine**, each line naming page, item, and the file and field to change. Must fix is for real problems (wrong answer or key, a rule broken, forms out of line, integrity error, a target with no item, something unreadable); taste goes under Should fix.

## Reply (6-10 lines)

Per document: counts of Must fix / Should fix, and the Must fix lines in short. Then anything across the set (integrity, drift).

# No exit tickets, Warm-up heading only (Nov 19, round 2)

Teacher: "I don't really want exit tickets. We don't really do those. And extra labels for sections aren't good."
Decisions the teacher picked:
- **Labels:** student pages keep a plain "Warm-up" heading. Problems 1, 2, 3 run down the page with no Together / With a partner headings and no subtitles ("on your own", "Problems 1-2"). Who works which problem stays in the teacher plan.
- **Exit tickets:** fold in or cut. If the exit item checks the core idea in a way the partner problems don't, it becomes the last numbered problem. Otherwise it's cut.
- Scope: only the lessons revised in the core-idea pass (2.7, 2.9, all of Unit 3, all of Unit 4). Don't touch 2.1, 2.5, 2.6, or any assessment.

Mode: a small edit on finished lessons. Don't redo the core-idea pass; keep everything else as it is.

## 0. Load these skills first (required)

Use the `skill` tool, or read `.agents/skills/<name>/SKILL.md` in full. They were just updated for this change:
- `lesson-scope`: "Labels", "Scaffolding by part of the lesson", "Budget", "What to cut first" (item 4), "After any cut or renumber".
- `lesson-assessment-designer`: Step 3, Step 4, and the Final check.
- `handout-release-check`: sections 1-2 ("Where scaffolds go": the last problem keeps the core step open).
- `authentic-writer`: for any wording you change.
- `mll-literacy-scaffolding`: the checklist (Period 4).
- `.agents/skills/lesson-builder/references/api_cheatsheet.md`: the new document field `headings: warmup`.

## 1. Headings

- Add `headings: warmup` at the top level of the lesson YAML, right after the `numbering:` line.
- Remove any `title:` or `sub:` on lesson sections. If a `plain` section's title names a reading box the task needs (for example 4.1's ADA ramp rules), make the name the bold first line of the box (`box: ['**The ADA ramp rules**', ...]`) and drop the title.
- Check the build: the handout and key print "Warm-up" and nothing else as a heading (the QuickNotes box keeps its own label).

## 2. Exit ticket: fold in or cut

Read the exit item, the partner problems, and the `Core idea:` line in `_temp/specs/<stem>/requirements.md`.
- **Fold in** when it checks the core idea in a way the partner problems don't (a new case, the "why" said on its own, a different representation). Move the item to the end of the partner section, so it is the last numbered problem. Keep its answer, box, figure, and minutes. Rewrite any wording that only made sense on an exit page ("Use your parallelogram proof." can now be `{ref:id}`). If the QuickNotes would now share a page with it and give its answer away, keep them on their own page.
- **Cut** when a partner problem or the practice already checks the same thing. A cut item is just cut: don't move it to the practice set or into the plan.
- Delete the `kind: exit` section. If a figure or asset is now used by nothing, remove it (`uv run lesson-builder tidy <unit>` lists it), but only in your own lesson's files.

## 3. Plan, notes, logs

- `plan`: remove the Exit ticket row and paragraph. The Quick look table names the parts (Warm-up, Together, With a partner, QuickNotes, Collect, assign practice); a folded-in item's minutes join the partner row; the table ends at the unit budget or less (30 for Unit 3, 40 for Units 2 and 4). Fix every sentence that mentions the exit ticket, "page 3 (QuickNotes and exit ticket)", "Collect exit ticket", or "before the exit ticket". If the exit item was folded in, move its "look for" notes into the partner paragraph.
- `guide_notes`: add one line: "**Nov 19 (round 2): no exit ticket.** The exit item is now Problem N (reason) / was cut (reason). The handout prints only the Warm-up heading." Rewrite older notes only where they describe the exit ticket as current.
- `_temp/specs/<stem>/requirements.md`: update the blueprint row and the Core vs routine line for the exit item (now Problem N, or cut).
- `_temp/specs/<stem>/changes.md`: add "## Nov 19 (round 2): no exit ticket, Warm-up heading only", one line per change: `item: what changed | why (rule)`, then `total item minutes A -> B; plan N min`.

## 4. Build and look

- `uv run lesson-builder build <unit> -l <stem> --no-packets`, at most 3 builds per lesson, 0 errors. Builds for other lessons run at the same time; if the PDF export fails, rerun once.
- Open every handout and key page in `<unit>/_temp/renders/current/<stem>/`: only the Warm-up heading prints, nothing is split from its figure, and no page is left mostly empty by a stale `page_break_after` or `page_break_before` (the QuickNotes can stay on the back page).

## Files

Only your assigned lessons: `lessons/<stem>.yaml`, `figures/<stem>.py`, `assets/<stem>/`, `_temp/specs/<stem>/` inside each lesson's unit folder (`units/geometry/unit-2-congruent-triangles/`, `unit-3-similarity/`, `unit-4-right-triangle-trig/`). Never edit `src/`, `templates/`, `.agents/`, `unit.yaml`, other lessons, assessments, or a DOCX. Repo: `/Users/zubair/Documents/pdf-to-docx` (macOS, zsh, `uv run`). Scratch scripts go in `_temp/build/`.

## Reply

One line per lesson: exit item folded in (now Problem N) or cut, and why; plan minutes before -> after; handout pages; build result. Then any judgment call the teacher should check.

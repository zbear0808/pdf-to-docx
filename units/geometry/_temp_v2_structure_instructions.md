# v2 pass: the new lesson structure (Nov 23)

Teacher (Nov 23):
- Lessons are 30 minutes everywhere.
- Mostly the same format, but with an in-class practice problem after the QuickNotes: 1-2 problems, done on their own, the least scaffolded part. Usually it shares a page with the QuickNotes.
- The default scaffolding is "a good amount of scaffolding, but not literally everything", slightly less toward the end.
- Warm-ups may use the intuition-check style where it fits (optional, not for every warm-up).
- Make new copies of Units 3-4. The originals stay as they are.

## Where you work

The copies are `units/geometry/unit-3-similarity-v2/` and `units/geometry/unit-4-right-triangle-trig-v2/`.
- Unit 3 v2's lessons started from the faded-scaffolding copies, which are already at the default level and within 30 minutes.
- Unit 4 v2 is a copy of the current Unit 4: 40-minute plans with standard scaffolding.

Edit only your assigned lessons in the v2 folder. Never edit `unit-3-similarity/`, `unit-3-similarity-faded/`, `unit-4-right-triangle-trig/`, `archive/`, `src/`, `.agents/`, `unit.yaml`, assessments, or a DOCX. Don't delete figures or assets (an unused figure is fine).

## 0. Load these skills first (required)

Use the `skill` tool, or read `.agents/skills/<name>/SKILL.md` in full:
- `lesson-style`: the whole thing. It's the new rule set: §1 shape and the 30-minute table, §3 default scaffolding and the fade, §4 less is more, §6 labels.
- `lesson-write-step` and its `references/item-rules.md`: how to write, key, and build.
- `lesson-plan-step` §3: how to write the plan changes in `requirements.md`.
- `warmup-design`: only if you change a warm-up; style B, the intuition check, is optional.
- `mll-literacy-scaffolding`, `authentic-writer`, and `.agents/skills/lesson-builder/references/api_cheatsheet.md` (it covers `kind: apply` and `numbering_after_notes`).

## 1. Plan the change (write it first)

In the v2 copy's `_temp/specs/<stem>/requirements.md`, add "## v2 (Nov 23)" with:
- **Timing:** the new item list with minutes. Item minutes add up to 30 or less, and the plan's table ends at 30 or less.
- **In-class practice:** which problem(s) and where they come from. Candidates, in order:
  1. The lesson's former exit-ticket or check-your-understanding item, written as a solo check of the core idea. For Unit 3, it's in git (`git show HEAD:units/geometry/unit-3-similarity/lessons/<stem>.yaml`, section `kind: exit` or `cyu`). For Unit 4, use the backups in the original unit's `_temp/specs/<stem>/` (`before_noexit/`, `before_nov19/`, `backup_nov19/`, `before_nov19/`). In 4.5 and 4.7, the former exit item is now the last partner problem; it can move after the QuickNotes.
  2. A homework practice item that applies today's core idea, moved into class (taken out of the practice set, not copied).
  3. A new problem in the same shape as the last partner problem, with new numbers.
  
  Use 1-2 problems, about 4-5 minutes, answerable using the QuickNotes. It's the least scaffolded part: an open box or work space, with routine values still given.
- **Scaffolding:**
  - Unit 3: already at the default level. Check that the fade runs warm-up → main problems → later problems → in-class practice.
  - Unit 4: apply the default level now (`lesson-style` §3). In the main problems, print the known steps (computed values, earlier-lesson moves, given facts), with maybe one repeated bit left open. Give the later partner problems a bit less. The new step stays open everywhere.
- **Cuts for 30 minutes** (Unit 4 mostly): follow `lesson-style` §4 and give each cut a reason. Cut a repeat before a core item, and scaffold routine steps before cutting anything.

## 2. Edit

- **Header:** set `numbering_after_notes: continue`, and keep `numbering: auto` and `headings: warmup`.
- **Order:** warmup, together, partner, notes, then `kind: apply` with the in-class practice. No titles, and no `cyu` or `exit`.
- **QuickNotes page:** the QuickNotes and the in-class practice usually share a page. The QuickNotes still must not share a page with a problem they answer. If they answer an earlier problem, keep them on the back page with the in-class practice under them.
- **References:** with continued numbering, `{ref:}` can point to any problem. Fix every "Problem N" and `{ref:}` after a move or cut.
- **Practice set:** if an item moved into class, remove it from the practice, renumber, and update `selected`. Otherwise leave the practice as it is.
- **Plan and notes:**
  - `plan`: the Quick look table gets an "In-class practice" row, and the Core idea paragraph gets one sentence about what the in-class practice checks.
  - `guide_notes`: add "**v2 (Nov 23).** ..." in one short paragraph.
  - `_temp/specs/<stem>/changes.md`: one line per change.

## 3. Build and look

- Build: `uv run lesson-builder build <v2 unit> -l <stem> --no-packets`. At most 4 builds per lesson, 0 errors. Other lessons build at the same time; if the PDF export fails, rerun once.
- Open every handout, key, and practice page in `<v2 unit>/_temp/renders/current/<stem>/` and check:
  - Only "Warm-up" prints as a heading.
  - The in-class practice has room to write.
  - Nothing is split from its figure.
  - No answer is visible on its own page.
  - The key matches the student copy.
  - Key answers print bold and red.

## Reply

One block per lesson:
- the in-class practice (what it is, and where it came from);
- what changed in the scaffolding;
- the cuts;
- item and plan minutes before -> after;
- pages;
- the build result.

Then any judgment calls.

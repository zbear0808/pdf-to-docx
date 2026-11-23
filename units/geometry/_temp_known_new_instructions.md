# Known content printed, new information blank (Nov 23)

Teacher (Nov 22-23): "I want the scaffolding basically to help do the work for the students in the places where they should already know the content. And then leave blank the sections that are new information." Make new versions of Lesson 2.9 and every Unit 3 lesson with this rule. "Don't delete anything."

**Don't delete anything:** the Nov 22 versions are saved in each unit's `archive/2026-11-22 before known-new pass/` (YAML, figure files, specs, built outputs). In this pass:
- Don't cut items, parts, figures, assets, QuickNotes bullets, or practice items.
- Don't delete files.
- Only change what is printed and what is blank, plus the plan and notes that describe it.

The Nov 22 build in `_temp/renders/current/<stem>/` shows the starting point.

## 0. Load these skills first (required)

Use the `skill` tool, or read `.agents/skills/<name>/SKILL.md` in full:
- `lesson-scope`: "Scaffold around the core idea", especially the new paragraph "Known content is done for them; new information is blank" (with its practice and review rule). Also "Scaffolding by part of the lesson" and "Labels".
- `handout-release-check`: §1-2 ("Where scaffolds go") and §2 (keys).
- `lesson-assessment-designer`: Step 4 and the Final check.
- `mll-literacy-scaffolding`, `authentic-writer`, and `.agents/skills/lesson-builder/references/api_cheatsheet.md`.

Finished model: `units/geometry/unit-2-congruent-triangles/lessons/2.8.yaml` (built Nov 22 under this rule). Read its handout and its `_temp/specs/2.8/requirements.md` Core vs routine list (each step marked known or new).

## 1. Sort every blank (write it down first)

In `_temp/specs/<stem>/requirements.md`, update the Core vs routine list. Mark every blank on the handout and the practice **known** or **new**:
- **Known:** taught before today. That means earlier lessons in this unit, earlier units (Unit 1 transformations, Unit 2 congruence for Unit 3), and earlier grades (arithmetic, solving one-step equations, the angle sum, the Pythagorean theorem). Read the earlier lessons' YAML to see what was taught: Unit 3 goes 3.1, 3.3, 3.4, 3.5, 3.6, 3.7, 3.9, 3.11, 3.13; Unit 2 goes 2.1, 2.5, 2.6, 2.7, 2.8, 2.9.
- **New:** what today teaches: the `Core idea:` line and the steps that carry it.
- Test each blank: could a student who missed today, but knows everything before it, fill it in? If yes, it's known.

## 2. Make the new version

- **Known steps are done for students:** print them complete, worked, or filled in (statement and reason in a proof; the computed value; the earlier-lesson move; the pre-filled table entry). A blank box becomes printed text, a frame row becomes a printed sentence, a `{ans: ...}` proof cell becomes plain text. If the answer is now printed, drop the `work:` space it had.
- **New steps stay blank,** with their boxes, frames, or open space. Every problem keeps at least one real blank: its new step. Don't frame a new step so tightly that the frame says it.
- **Warm-up:** keep it low demand. Its blank is the one skill it reviews.
- **Practice (homework):** the blanks are today's new content and, on a spaced-review item (SBA review, an earlier lesson's proof), the one skill being reviewed. Print the rest. A review item with nothing blank isn't practice.
- **No answer may print on a page that asks for it.** Printing a known step must not answer another item on the same page, the QuickNotes included (handout-release-check §2, the "No answer is visible" rule). `check` warns on some of these; read for the rest.
- **The key** still shows every answer, and the student and key layouts stay matched.
- **Keep the rest as it is:** titles, `headings: warmup`, numbering, figures, and item order.

## 3. Plan and notes

- `plan`: in the **Core idea.** paragraph, say which known steps are now printed. Update item minutes and the Quick look table (printing known steps usually saves time; don't add items to fill it).
- `guide_notes`: add "**Nov 23: known content printed.** ..." with one short paragraph saying what is now printed and what stays blank.
- `_temp/specs/<stem>/changes.md`: add "## Nov 23: known content printed, new information blank", one line per change: `item: printed X (known: lesson N) / kept blank Y (new)`. End it with `item minutes A -> B; plan N min; pages`.

## 4. Build and look

- Build: `uv run lesson-builder build <unit> -l <stem> --no-packets`, at most 3 builds per lesson, 0 errors. Builds for other lessons run at the same time; if the PDF export fails, rerun once.
- Open every handout, key, and practice page in `<unit>/_temp/renders/current/<stem>/`. Check that:
  - nothing is split from its figure;
  - no line is clipped (the key's added printed lines can run long);
  - no page is left mostly empty or over budget;
  - only "Warm-up" prints as a heading.

## Files

Only your assigned lessons: `lessons/<stem>.yaml`, `figures/<stem>.py` (only if a printed known value needs a label; don't delete figures), and `_temp/specs/<stem>/` inside the unit. Never edit `src/`, `templates/`, `.agents/`, `unit.yaml`, `archive/`, other lessons, assessments, or a DOCX. Repo: `/Users/zubair/Documents/pdf-to-docx` (macOS, zsh, `uv run`).

## Reply

One block per lesson: what is now printed (known, with the lesson it comes from), what stays blank (new), item minutes and plan minutes before -> after, pages, and the build result. Then any judgment call: a step that could go either way, or a print that might give away an answer.

# Faded-scaffolding version (Nov 23)

Teacher: "Make one other new version with slightly less scaffolding as we get to the end of the lesson. So the warm up is all review, but should need low cognitive load. The main lesson plan should have most of the review filled out already, maybe just a bit of old repeated stuff. And then the [later part] should have a bit more open space for students to figure it out. Make new versions of the docs and stuff, but almost everything should be the same." Also: "we don't need to add the labels. But maybe later sections can have a bit less scaffolding for the students."

## Where you work

The faded copies are separate unit folders: `units/geometry/unit-2-congruent-triangles-faded/` (lessons 2.8, 2.9) and `units/geometry/unit-3-similarity-faded/` (all nine Unit 3 lessons). They started as exact copies of the standard versions, which stay untouched in `unit-2-congruent-triangles/` and `unit-3-similarity/`. Edit only the faded copy. Never edit the standard unit folders or `archive/`.

## 0. Load these skills first (required)

Use the `skill` tool, or read `.agents/skills/<name>/SKILL.md` in full:
- `lesson-scope`: the new "Faded version (less scaffolding toward the end)" section, plus "Scaffold around the core idea" (its "Known content is done for them" paragraph is what the standard version follows), "Scaffolding by part of the lesson", and "Labels".
- `handout-release-check` §1-2
- `mll-literacy-scaffolding`
- `authentic-writer`
- `.agents/skills/lesson-builder/references/api_cheatsheet.md`

## 1. Plan the fade (write it first)

In the faded copy's `_temp/specs/<stem>/requirements.md`, add "## Faded version (Nov 23)": one line per handout item, saying what stays printed and what becomes blank or open space.
- **Warm-up:** unchanged. It's all review, with low cognitive load.
- **The main problems** (Together and the first partner problem): mostly as they are. Most of the review is filled out already. At most, leave blank one bit of old, repeated stuff: a known step students already did earlier on this handout, or a routine fact from the last lesson.
- **The later problems** (the last one or two partner problems): a bit less scaffolding and more open space for students to figure it out.
  - Known steps the standard version prints become blanks (proof cells become `{ans: ...}`, printed values become boxes) or open work space.
  - A tight frame becomes a sentence starter or an open `box:`.
  - Printed earlier steps can go, so students write the whole argument.
  - Add `work:` or `box:` height so there's room.
- **The fade runs one way:** each problem has the same or less scaffolding than the one before it.

## 2. Keep almost everything the same

- **Unchanged:** problems, item order, numbering, figures, the given values in the figures, QuickNotes, the practice set, titles, `headings: warmup`, and the page budget.
- **No new section labels** (no "Check your understanding" heading).
- **Keys:** every new blank needs its answer in the key, and drawing tasks keep their answer figures.
- **No answer on its own page:** a printed step must not answer another item on the same page (handout-release-check §2).
- **`plan`:** add one sentence to the Core idea paragraph: "Faded version: the later problems print less, so students carry the whole argument in Problem N."
- **Minutes:** if the later problems now take longer, adjust them. Keep the plan at or under the unit budget (Unit 2: 40, Unit 3: 30). If it runs over, trim open space before trimming content.
- **`guide_notes`:** add "**Faded version (Nov 23).** ..." in one short paragraph.
- **`changes.md`** (in the faded copy's `_temp/specs/<stem>/`): one line per change.

## 3. Build and look

- Build with `uv run lesson-builder build <faded unit> -l <stem> --no-packets`: at most 3 builds per lesson, 0 errors. Other lessons are building at the same time; if the PDF export fails, rerun once.
- Open every handout and key page in `<faded unit>/_temp/renders/current/<stem>/`:
  - Only "Warm-up" prints as a heading.
  - Nothing is split from its figure.
  - The later problems have room to write.
  - The key matches the student copy.

## Files

Only your assigned lessons in the **faded** unit folder: `lessons/<stem>.yaml`, `figures/<stem>.py` (only to move a printed label to the answer layer when that step becomes a blank; don't delete figures), and `_temp/specs/<stem>/`. Repo: `/Users/zubair/Documents/pdf-to-docx` (macOS, zsh, `uv run`).

## Reply

One block per lesson:
- what changed in the main problems (if anything) and in the later problems;
- item and plan minutes;
- pages;
- the build result.

Then any judgment call.

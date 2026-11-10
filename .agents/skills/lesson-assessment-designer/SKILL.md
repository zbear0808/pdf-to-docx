---
name: lesson-assessment-designer
description: Designs secondary math lesson plans, unit plans (UbD backward design), inquiry worksheets, and performance tasks for Franklin HS room 105, grounded in EDTEP 573/575/582/583 readings (Smith & Stein, UbD, Taylor & Nolen, Moschkovich, Roberts et al.). assessment-builder also loads its Steps 1-2 (targets, evidence, performance tasks), Step 4 (worksheet structure), readings table, and final check when building a test, quiz, or worksheet; assessment-builder runs the document pipeline.
---

# Lesson and unit designer

Run the steps in order. Steps 1-3 serve the **Plan** step and Step 4 the **Write+build** step; each step's subagent loads this skill (see `.agents/skills/lesson-builder/references/orchestration.md`). Without subagents, run the steps in sequence with the same files. Record Stage 1-2 decisions and the timing in `_temp/specs/<stem>/requirements.md` in the unit folder. For period profiles, load `classroom-context`. For item-level rules (MC, short answer, rubrics, language access, contexts), use `.agents/skills/assessment-builder/references/item-rules.md`. Don't restate those rules here. For voice, use `authentic-writer`.

## Readings and templates

Base path: `C:\Users\zubair\Documents\canvas-extractor\export\`. Files marked (scan) have no text layer and must be OCR'd into `_temp/` before quoting.

| Use | Reading | Path under base |
|---|---|---|
| Backward design | Wiggins & McTighe, UbD | `edtep-583-...-ii\files\ubd-backward-design.pdf` (scan); `edtep-583-...-ii\google_drive\Fall_2026\Week_4\UbD_Backward_Design.pdf` |
| Big ideas, units | Woodbury (2000) | `edtep-583-...-ii\files\woodbury(2000)_teachingtwrdsbigideasalg.pdf` |
| Cognitive demand | Smith & Stein (1998); Levels table | `edtep-582-...-i\files\smith-&-stein-(1998).pdf` (scan); `edtep-583-...-ii\google_drive\Spring_2026\Week_7\Levels_of_Cognitive_Demand_Table.pdf` |
| Group-worthy tasks, status | Lotan (2003) | `edtep-582-...-i\files\lotan-(2003).pdf` |
| Lesson scripts, productive struggle | Stigler & Hiebert (1998) | `edtep-582-...-i\files\stigler-&-hiebert-(1998)-teaching-is-a-cultural-activity.pdf` |
| Identity, who is "good at math" | Aguirre et al. (2013) Ch. 1 | `edtep-582-...-i\files\aguirre-et-al-2013-what-math-ch.-1.pdf` |
| Teachers' views of equity | Bartell & Meyer (2008) | `edtep-583-...-ii\files\equityprinciple_bartell2008.pdf` |
| Validity, performance tasks, items | Taylor & Nolen (2008) Ch. 1, 5, 7, 8 | `edtep-573-...\google_drive\readings\Taylor___Nolen_Chp{1,5,7,8}.pdf` (scan) |
| Culturally responsive items | Taylor (2022) Ch. 6 | `edtep-573-...\google_drive\readings\Taylor_2022.pdf` |
| SBG, retakes | Guskey & Jung (2006); Scriffiny (2008) | `edtep-573-...\google_drive\readings\SBG_resource_*` |
| Post-test error analysis | Chesbro (2010) | `edtep-573-...\google_drive\readings\Chesbro_2010.pdf` |
| Cultural validity, Indigenous students | Preston & Claypool (2021) | `edtep-573-...\google_drive\readings\Preston_and_Claypool_2022.pdf` |
| MLL supports | see `mll-literacy-scaffolding` | |
| Lesson template (Launch, Explore, Summarize) | | `edtep-583-...-ii\google_drive\Fall_2026\Week_3\MathLessonPlanTemplateFall2026.docx` |
| Unit template (UbD stages) | | `edtep-583-...-ii\google_drive\Fall_2026\Week_4\Backward_Planning_Template.docx` |
| Launch rubric | | `edtep-583-...-ii\google_drive\Spring_2026\Week_8\MT_LAUNCHrubricSpring2026.docx` |
| AP Stats CED | | `edtep-583-...-ii\standards\ap-statistics-course-and-exam-description.pdf` |

Folder names, written out in full:
- `edtep-573-...` is `edtep-573-a-au-26_-assessment-in-secondary-education`
- `edtep-582-...-i` is `edtep-582-a-sp-26_-teaching-mathematics-in-the-secondary-school-i`
- `edtep-583-...-ii` is `edtep-583-a-au-26_-teaching-mathematics-in-the-secondary-school-ii`

Only cite a reading for something it actually says. If you haven't checked the text, don't attach a page number.

## Step 1: Desired results (UbD Stage 1)

- Standards: the CCSS-M or AP CED codes. The `common-core-standards` skill in canvas-extractor can look these up.
- One or two essential questions. They should be open, worth arguing about, and tied to the unit's big idea (Woodbury). Example: "When does the mean hide what's going on in a neighborhood?"
- Two kinds of learning targets. Conceptual: "Students will understand that..." Skill: "Students will be able to...".

## Step 2: Assessment evidence (Stage 2)

- List which evidence shows each target: exit tickets, a quiz, a performance task.
- Performance task (T&N Ch. 5):
  - Real purpose and audience.
  - Directions written to the student, covering what to make, the constraints, and the criteria.
  - Scoring criteria shared ahead of time.
  - A rubric with 3-6 specific levels, with communication scored separately from math.
- To build the actual quiz or test document, hand off to `assessment-builder`. It brings these Stage 1-2 decisions into its blueprint (Step 2).

## Step 3: Lesson plan (Launch, Explore, Summarize)

Follow `MathLessonPlanTemplateFall2026.docx`. Periods are **40 minutes**; budget every part with `lesson-scope` and keep the plan's timing table at 40 or less.

1. **Launch (about 10 min, warm-up included):**
   - A low-floor entry: Notice and Wonder, Which One Doesn't Belong, or a short visual.
   - Make sure everyone understands the context before the math (for word problems, the 3-Reads routine in `mll-literacy-scaffolding`).
   - Set expectations without giving away a method.
2. **Explore (about 15-18 min):**
   - Pairs or trios on a task at the "procedures with connections" or "doing mathematics" level.
   - Use a group-worthy task (Lotan): several ways in, visuals, real interdependence, and an individual write-up at the end.
   - List anticipated strategies and errors.
   - Write assessing and advancing questions that don't break the task into tiny steps (Stigler & Hiebert).
3. **Summarize (about 12 min):**
   - Pick and order student work so it connects different methods.
   - Close with a 1-2 question exit ticket tied to the target.

Add MLL supports from `mll-literacy-scaffolding`, specific to this lesson's language demands.

## Step 4: Student worksheet

- Header: title, name/date/period, the learning target.
- Parts:
  - warm-up (accessible entry)
  - investigation (core task with guiding questions)
  - check for understanding
  - exit ticket
- Leave room to write (`work:` in inches, or `box:`). Use labeled diagrams and tables. Add a vocabulary callout only for dual-meaning words.
- Fill-ins and frames follow `handout-release-check` §1 (labeled boxes via `fill:` / `frame:`, clear referent).
- Teacher key: full solutions, anticipated difficulties, what to say. Every item and part has an `answer:`; drawing tasks get a labeled answer figure (`key_figure` drawn in `figures/<stem>.py`).
- To produce the DOCX/PDF, write the lesson as `lessons/<id>.yaml` in the unit folder and build it with `lesson-builder` (handout, key, practice, practice key, teacher guide, packets). Fix the YAML or figure file, never the DOCX.

## Final check

- [ ] Cognitive demand: is there real reasoning, or only following a recipe?
- [ ] Every assessment piece measures a Stage 1 target.
- [ ] MLL access is built into the task (visuals, a clear context, optional stems, talk in any language) without lowering the math.
- [ ] Contexts are familiar to students and do actual mathematical work.
- [ ] The lesson fits 40 minutes (`lesson-scope`), and `uv run lesson-builder check <unit> -l <stem>` passes (`handout-release-check`).

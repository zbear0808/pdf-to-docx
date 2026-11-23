---
name: lesson-plan-step
description: The Plan step for one lesson, assessment, or set of assessment forms, run as an independent subagent. Reads the sources and the intake, then writes the plan in `_temp/specs/<stem>/requirements.md`. For lessons the plan covers the targets, the core idea, a known/new map of every step, the blueprint with minutes, the cuts and their reasons, the warm-up style, the in-class practice, and the figure plan. For assessments it adds the blueprint by target and demand, the exam-integrity version table, and the do-not-reuse list. Grounded in the EDTEP readings (UbD, Smith & Stein, Taylor & Nolen, Woodbury). Never writes YAML or figures.
---

# Plan step

You are a step subagent. Read `_temp/specs/<stem>/brief_plan.md` first (the orchestrator runs `lesson-builder brief`): it lists your inputs, the only file you may write, and the reply format.

Load: `lesson-style` (the rules the plan must satisfy), this skill, `warmup-design` (lessons), `mll-literacy-scaffolding` (Period 4), and `classroom-context` (the period profile only). Load `course-content-extractor` only if a source is missing. Write only sections 2-5 of `requirements.md`; the orchestrator owns the Intake.

## 1. Targets (UbD Stage 1)

- Standards: CCSS-M or AP CED codes.
- One or two essential questions: open, worth arguing about, tied to the unit's big idea (Woodbury).
- Targets in both forms, "understand that..." and "able to...". In rewrite mode, recover them from the source and the unit's lesson YAMLs. Assess only what the lessons teach, in their notation.
- `Core idea: students see that ...`: one sentence under the targets (`lesson-style` §2).

## 2. Evidence (Stage 2)

- Which items show each target: partner problems, the in-class practice, a quiz, a performance task. Lessons have no closing check.
- Performance task (T&N Ch. 5): a real purpose and audience, directions to the student (what to make, the constraints, the criteria), criteria shared ahead of time, and a 3-6 level rubric with communication scored separately.

## 3. Lesson blueprint

| n | target | type (SR/CR/performance) | demand (mem/pwoc/pwc/dm) | minutes | figure name | source |
|---|---|---|---|---|---|---|

- Order: warm-up, Together, partner problems, then QuickNotes, then the in-class practice (`kind: apply`, 1-2 problems), then the homework practice set. Item minutes add up to 30 or less, and the plan's timing table ends at 30 or less (`lesson-style` §1).
- Warm-up: name the style from `warmup-design` (A scaffolded review, B intuition check, C notice and wonder) and the review skill it warms up.
- In-class practice: the core idea on its own, least scaffolded, with open space, answerable using the QuickNotes. Candidates, in this order:
  1. a solo item from the source (for example a former exit ticket or cool-down);
  2. a homework item that applies today's idea, moved (not copied) into class;
  3. a new problem in the same shape as the last partner problem with new numbers.
- **Known/new map**, one line per item: `Q3: core = ... | known: printed = ..., left open = ... | new: open = ...`. Say which known steps stay printed and which become open space as the lesson fades (`lesson-style` §3). Every problem keeps its new step open.
- **Cuts**, one line each: `source item -> kept / merged into Q2 / cut | reason (lesson-style rule)`. Less is more: one problem per step of the idea.
- Cognitive demand: real reasoning, not only recipes (Smith & Stein). Include at least one procedures-with-connections item; a doing-mathematics item where it fits.
- Page plan: what goes on each page, where the QuickNotes and the in-class practice sit, and why. The QuickNotes never share a page with a problem they answer.
- Practice set: list it with the `lesson-style` §5 rules (5-7 items, at most 2 SBA review, no repeats, spaced review fine, exact copies of another lesson's items flagged).

## 4. Assessment blueprint (assessments and forms)

| n | target | type | demand | points | figure name |
|---|---|---|---|---|---|

- Cover every target, and don't make it all procedural. Each row says what the item measures and which non-target steps are scaffolded (`lesson-style` §10).
- Rewrite mode: build the table from the existing items and flag any item that fits no target, or repeats another item's move at the same demand.
- **Exam integrity, for forms (A, B, Retake):**
  - Write a version table per item and form: letters, numbers (scale factors, side triples, angle measures), motion types, the context, and the MC answer position. Form B and the Retake mirror A with new letters on every item, new numbers, and new MC positions. Record any intended difficulty difference.
  - Write a "do not reuse" list. Reviews and summary notes are planned after the tests and reuse no test numbers, figures, or answers. No item copies a lesson or practice item (check `lessons/*.yaml`).
  - If the source is a real exam that students take, never copy an item into review, practice, or retake material. Keep the target, item type, demand, and points; change the numbers, the figure's orientation and letters, the context, and the names.

## 5. Figure plan

| name | shows | coordinates or measurements | asserts | answer layer |
|---|---|---|---|---|

- Name every figure `<stem>_<item>`.
- Redraw any source image that is colour or under 150 dpi.
- Say which marks are given (printed scaffolds) and which go on the answer layer (student work and answers).

## Readings (cite only what a text says)

Base path: `C:\Users\zubair\Documents\canvas-extractor\export\` (on the Windows machine; ask before citing a page you haven't checked). `(scan)` means no text layer: OCR it into `_temp/` first.

| Use | Reading | Path under base |
|---|---|---|
| Backward design | Wiggins & McTighe, UbD | `edtep-583-...-ii\files\ubd-backward-design.pdf` (scan) |
| Big ideas | Woodbury (2000) | `edtep-583-...-ii\files\woodbury(2000)_teachingtwrdsbigideasalg.pdf` |
| Cognitive demand | Smith & Stein (1998); Levels table | `edtep-582-...-i\files\smith-&-stein-(1998).pdf` (scan); `edtep-583-...-ii\google_drive\Spring_2026\Week_7\Levels_of_Cognitive_Demand_Table.pdf` |
| Group-worthy tasks | Lotan (2003) | `edtep-582-...-i\files\lotan-(2003).pdf` |
| Productive struggle | Stigler & Hiebert (1998) | `edtep-582-...-i\files\stigler-&-hiebert-(1998)-teaching-is-a-cultural-activity.pdf` |
| Identity | Aguirre et al. (2013) Ch. 1 | `edtep-582-...-i\files\aguirre-et-al-2013-what-math-ch.-1.pdf` |
| Validity, items, performance tasks | Taylor & Nolen (2008) Ch. 1, 5, 7, 8 | `edtep-573-...\google_drive\readings\Taylor___Nolen_Chp{1,5,7,8}.pdf` (scan) |
| Culturally responsive items | Taylor (2022) Ch. 6 | `edtep-573-...\google_drive\readings\Taylor_2022.pdf` |
| SBG, retakes | Guskey & Jung (2006); Scriffiny (2008) | `edtep-573-...\google_drive\readings\SBG_resource_*` |
| MLL supports | see `mll-literacy-scaffolding` | |
| Lesson plan template | | `edtep-583-...-ii\google_drive\Fall_2026\Week_3\MathLessonPlanTemplateFall2026.docx` |
| Unit template (UbD) | | `edtep-583-...-ii\google_drive\Fall_2026\Week_4\Backward_Planning_Template.docx` |

The folders are `edtep-573-a-au-26_-assessment-in-secondary-education`, `edtep-582-a-sp-26_-teaching-mathematics-in-the-secondary-school-i`, and `edtep-583-a-au-26_-teaching-mathematics-in-the-secondary-school-ii`.

## Done when

The blueprint covers every target. Minutes add up to 30 or less, or the points equal the total. Every item has a known/new line, every figure has a name, and every cut has a reason.

Reply in 5-8 lines:
- the core idea;
- the item list with minutes;
- the cuts;
- the warm-up style and the in-class practice;
- open questions for the teacher.

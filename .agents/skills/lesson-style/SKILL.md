---
name: lesson-style
description: The teacher's rules for how Franklin HS room 105 math lessons and assessments are built. Lesson shape (warm-up, Together, partner problems, QuickNotes, in-class practice, homework; 30 minutes; no closing check; only the Warm-up heading prints), the default scaffolding (a good amount that fades toward the end; known content done for students, new information open), the extra-support option, less is more, practice sets, labels, wording, page layout, and how all of it carries over to assessments. Every plan, write, and audit subagent loads this with its step skill; the orchestrator reads it to brief them.
---

# Lesson style

These rules come from the teacher. Apply them while planning and writing; the audit checks them. Step skills (`lesson-plan-step`, `lesson-write-step`, `lesson-audit-step`) say how to do each step; this file says what a finished lesson looks like.

## 1. Lesson shape (30 minutes)

| Part | Min | What it is | YAML |
|---|---|---|---|
| Warm-up | 3 | Review only, low cognitive load, the most scaffolded part (`warmup-design`) | `kind: warmup` |
| Together | 5 | 1-2 problems; the teacher models the core step under the doc camera | `kind: together` |
| With a partner | 10-12 | 2-3 problems on the core idea | `kind: partner` |
| QuickNotes | 3 | Printed notes, read together | `kind: notes` |
| In-class practice | 4-5 | 1-2 problems done on their own, using the notes; the least scaffolded part, with open space | `kind: apply` |
| Collect, assign practice | 2-3 | Homework is the practice set | |

- 30 minutes per lesson: `budget.minutes: 30` in `unit.yaml`. The plan's timing table ends at 30 or less, and item `minutes:` add up to 30 or less (`check` enforces both). Whole-class talk is at most about 10 minutes.
- No closing check: no exit ticket, cool-down, check-your-understanding, or reflection. No extension problems. Early finishers start the homework, and the page doesn't say so. A cut item is just cut; it doesn't move into the plan as an extension.
- The QuickNotes and the in-class practice usually share a page. The exact page doesn't matter much, but the QuickNotes must not share a page with a problem they answer, so they often go on the back page with the in-class practice under them.
- YAML header: `numbering: auto`, `headings: warmup`, `numbering_after_notes: continue` (the in-class practice keeps counting, Problem 5, 6).

Per-item minutes, estimated before writing:

| Item type | Min |
|---|---|
| True/false, one fill-in, read a statement | 1 |
| Short answer with a figure | 2-3 |
| Fill-in explanation (3-4 boxes) | 3 |
| Open "explain why" | 4 |
| Patty-paper move with written moves | 4 |
| Construction or drawing task | 6-8 |

## 2. Core idea first

During the lesson it can be hard to get through the main content, so narrow down what the "intuition" part of the lesson is: the core part students should learn that day. Structure the scaffolding around it, so that's the main work students do.
- Write it as one sentence: `Core idea: students see that ...` (usually the "understand that..." target).
- Sort every step of every problem into **known** (earlier lessons, units, or grades: arithmetic, given values, measuring, recalling a formula or an earlier lesson's result) and **new** (what today teaches). A skill that was the core of an earlier lesson is known now.
- The test for a step: could a student who missed today, but knows everything before it, do it? If yes, it's known.
- If a student gets stuck, they should be stuck on the core idea, not on the arithmetic, the reading, or redrawing a figure.

## 3. Scaffolding (default level)

A good amount of scaffolding, but not literally everything, and slightly less as the lesson goes on.

| Part | Scaffolding |
|---|---|
| Warm-up | All review, low cognitive load: values given, choices or a fill-in, a figure to look at |
| Together, first partner problem | Most of the review is filled out already: known steps printed, worked, or filled in. Maybe one bit of old, repeated work left blank (a step students just did on this handout) |
| Later partner problems | A bit less: some known steps become blanks or open space so students carry more of the argument; frames shrink to a starter |
| In-class practice | The least: an open box or work space, with the QuickNotes to lean on |

- **The fade runs one way.** Each problem has the same or less scaffolding than the one before it.
- **The core step stays open in every part.** No frame, word bank, figure label, or fill-in hands over the claim or the reason. A sentence starter is fine; the "because" is the student's.
- **Don't break the core step into tiny steps** (Stigler & Hiebert). The plan's advancing questions help a stuck pair without doing the step.
- **Routine steps students aren't learning today stay scaffolded everywhere.** Give computed values, given lengths, the formula or earlier fact, and pre-filled table rows, and allow a calculator. Use the lightest support that removes the step.
- **A routine fill-in should take seconds.** If it takes longer than the core step, print the value.

**Extra support (only on request).** Every known step is printed, worked, or filled in on every problem, and only the new information is blank. It's built as a separate copy of the unit (`units/<course>/<unit>-extra-support/`), so the default version stays as it is.

**Practice and review items.** The blanks are today's new content and, on a spaced-review item (SBA review, an earlier lesson's proof), the one skill being reviewed. Everything around them is printed. A review item with nothing left blank isn't practice.

## 4. Less is more

Less is more when first making lessons, so cut down on repetitive problems. A first draft is the shortest version that still teaches the idea.
- One problem per step of the idea. A second problem earns its spot only if it changes something the core idea depends on (a new case, a counterexample, a different representation). New numbers or letters don't count.
- Every item builds the core idea, practices it, or sets up the QuickNotes. Cut an item that does none of these.
- What to cut first: a repeat with new numbers; parts that repeat the first part; extra warm-up items; a closing-check section (keep its item only as the in-class practice, if it fits); anything the practice set already covers; items that don't touch the core idea.
- Before cutting a core item for time, scaffold the routine steps students are doing by hand instead.
- Keep the one "doing mathematics" task and the item that sets up the QuickNotes. Never cut an item another item depends on unless you cut both.
- After any cut or renumber, fix every "Problem N" and `{ref:id}` (`check` flags missing ones). A reference must point to work that actually supports the task.

## 5. Practice set (homework)

- 5-7 problems, at most 2 under an "SBA review" heading.
- No item repeats a handout item or another practice item with new numbers. Spaced review of earlier lessons is fine. An exact copy of another lesson's item gets cut from the later lesson; route it to that lesson's owner.
- Keep each distinct skill at least once and the hardest, most interesting item.
- Every practice set gets a full practice key; `selected` names only items that exist.

## 6. Labels

Extra labels for sections aren't good. Student pages print only a plain **Warm-up** heading; problems 1, 2, 3 then run down the page with no Together, With a partner, or In-class practice heading and no subtitle.
- No section `title:` or `sub:`, and no added layers (Activity 1, Synthesis, Launch / Explore / Summarize, "Part 1:", Cool-down, Reflection, Check your understanding).
- A reading box the task needs (for example the ADA ramp rules) carries its name as the bold first line of the box.
- The plan's timing table still names the parts, so the teacher knows the flow.

## 7. Wording

Follow `authentic-writer`. On student pages:
- **Cut:** boilerplate the layout already gives ("Fill in each box.", "Write your answer in the box."), hints and pep ("Hint:", "Think about..."), story sentences that do no math, and talk moves aimed at students (those go in the plan). Also cut a framing box that only restates the title.
- **Keep:** every given and constraint, the question itself, directions that change the answer ("Match the vertices in order."), the definitions students need, labeled boxes, and optional sentence starters (Period 4 MLLs).

## 8. Page layout

- Handout at most 3 pages; one double-sided sheet (2 pages) when it fits. Practice at most 2 pages.
- The key has the same pages and positions as the student copy (doc camera). Red appears only on keys. Answers on keys print bold and red (the builder does this).
- Nothing is split from its figure, and no page is left mostly empty by a stale page break.
- No answer is visible on the student page that asks for it: not on a figure, in a bank, in the QuickNotes, or in another item on the same page.
- Black-and-white images only; figure labels at least 8 pt at print size.

## 9. Multilingual learners (Period 4)

The goal is access to the same math. Lower the language load and keep the cognitive demand (`mll-literacy-scaffolding`): labeled visuals, the context understood before calculating (3-Reads), math terms kept and taught, talk in any language, and optional stems matched to the language function. The supports go heaviest on routine steps.

## 10. Assessments

The same ideas carry over to progress checks, tests, retakes, reviews, and worksheets. On an assessment, the "core" of each item is its blueprint target.
- **Less is more:** cut an item that makes the same move as another item for the same target at the same demand. Every target keeps at least one item per form. A cut item's points come off `total_points`, and in a set of forms the parallel item is cut in every form.
- **Scaffold what isn't being measured:** give computed values, labels, and earlier-unit facts when they aren't the target, so a wrong answer means the target skill is missing. Never scaffold the target step itself.
- **No section headings:** keep `target:` on each section for score reporting; the targets print in the Teacher Notes blueprint. Summary notes and other reference sheets may keep one short heading per lesson.
- **Directions:** only what changes the answer. "Show your work." goes once in `directions` when work is scored. No all-caps warnings.
- **Exam integrity:** forms (A, B, Retake) mirror each other with new letters, numbers, contexts, and MC positions. Reviews and notes reuse nothing from the tests. No item copies a lesson or practice item. `lesson-plan-step` and `lesson-audit-step` give the procedure.

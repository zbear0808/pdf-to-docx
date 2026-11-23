---
name: lesson-scope
description: Fits a lesson handout to a 40-minute period. Names the lesson's core idea (the intuition students must build), scaffolds everything around it so student effort goes to that idea, budgets minutes per item, cuts repeated problems, and keeps cross-references valid after cuts. Use before drafting or revising any lesson handout, worksheet, or lesson plan, when deciding how much scaffolding a warm-up or problem gets, and whenever a lesson "runs long."
---

# Lesson scope

A lesson is **40 minutes**, including the warm-up and QuickNotes. Write less. Students who finish early start the practice problems (homework). Don't write extension questions, and don't move cut items into the plan as extensions; a cut item is just cut. We don't use exit tickets or any other closing check.

Serves the **Plan** step (core idea, scaffold plan, budget, and cuts) and is reloaded by **Write+build** when a lesson runs long. See `.agents/skills/lesson-builder/references/orchestration.md`.

## Less is more

Less is more when initially making lessons, so cut down on repetitive problems. A first draft should be the shortest version that still teaches the idea. It is easier to add a problem later than to get through a crowded handout in 40 minutes.

- One problem per step of the idea. A second problem earns its spot only if it changes something the core idea depends on (a new case, a counterexample, a different representation). New numbers or new letters on the same problem don't count.
- Every item either builds the core idea, practices it, or sets up the QuickNotes. Cut an item that does none of these.
- When in doubt, cut it and let the practice set (homework) carry the repetition.

## Find the core idea first

During the lesson it can be hard to get through the main content. Before writing any items, narrow down what the "intuition" part of the lesson is: the core part we're trying to get the students to learn that day. Structure the scaffolding around that, so that's the main work students have to get through.

1. Write the core idea as one sentence in `requirements.md` under **2. Targets**: `Core idea: students see that ...`. It is usually the "understand that..." target, said as the thing students should notice or be able to explain. Example: "Core idea: students see that a dilation multiplies every distance from the center by the same k, so the image keeps its shape."
2. List the routine steps the lesson's problems also need: arithmetic, measuring, plotting given points, copying a figure, recalling a formula or a fact from an earlier lesson, setting up a table. These are **not** the core today. (A skill that was the core of an earlier lesson is routine now.)
3. Under the blueprint table, add a short **Core vs routine** list, one line per item: `Q3: core = explain why the ratios match | routine = side lengths, the division (given in the figure)`. Mark each step **known** (printed or worked for students) or **new** (left blank). The Write step scaffolds from this list.

## Scaffold around the core idea

Have more scaffolding around the steps to complete the problem that aren't the core of what we're supposed to be learning that day. That way students don't spend their time and mental effort on things like basic arithmetic they already know, and they spend their time on the actual intuition-building parts of the lesson.

**Known content is done for them; new information is blank.** Give lessons a decent amount of scaffolding. The scaffolding should basically do the work for the students in the places where they should already know the content, and leave blank the sections that are new information.
- Sort every step of every problem into **known** (earlier lessons, earlier units, earlier grades) or **new** (what today teaches). Known steps are printed, worked, or filled in, not just hinted at. New steps are the blanks.
- Test for each blank: could a student who missed today's lesson, but knows everything before it, fill it in? If yes, it's known content: print it.
- Two-column proofs: rows that use known facts (Given, reflexive, definitions, a theorem from an earlier lesson, CPCTC once it's been taught) print complete, statement and reason. Only the rows that carry today's new reasoning are blank.
- Multi-step problems: print the worked earlier-lesson steps (the computed values, the earlier moves, the setup) and leave the new step's line or box empty.
- Tables and fill-ins: pre-fill the entries that come from known content; blank only the entries that show today's idea.
- Don't go too far the other way: printing the new step, or framing it so tightly that the frame says it, takes away the lesson.
- Practice (homework) and review items: the blanks are today's new content and, on a spaced-review item (SBA review, an earlier lesson's proof), the one skill being reviewed. Everything around them is printed. A review item with nothing left blank isn't practice.

**Scaffold the routine steps.** Pick the lightest support that removes the step:
- Give the computed values (side lengths, the distances, the totals) in the prompt, the figure, or a filled table row.
- Pre-fill most of a table and leave blank only the cells that show the pattern.
- Draw the given parts of the figure; students add only the part that shows the idea.
- Print the formula, definition, or earlier fact in the item or a reference box instead of making students recall it.
- Use `fill:` / `frame:` boxes for the routine sentence parts (handout-release-check §1).
- Allow a calculator for arithmetic that isn't the point.

**Keep the core step open.** The core step is where students do the thinking:
- No frame, word bank, or fill-in that hands over the reasoning or the claim for the core step. A sentence starter is fine; the "because" part is the student's.
- Don't break the core step into tiny steps (Stigler & Hiebert). Advancing questions in the plan can help a stuck pair without doing the step for them.
- Test: if a student gets stuck, they should be stuck on the core idea, not on the arithmetic, the reading, or redrawing a figure.

## Scaffolding by part of the lesson

| Part | Cognitive demand | Scaffolding |
|---|---|---|
| Warm-up | Low. Recall or a quick look, answerable by nearly everyone in 4 minutes | More scaffolding than general questions: values given, choices or a fill-in, a figure to look at. Reviews a skill today's lesson needs; doesn't preview the new idea in a way that needs teaching |
| Together | Teacher models the core step out loud | Routine steps already done on the page so the talk is about the core step |
| With a partner | Highest. The core idea | Routine steps scaffolded; core step open. Fade across problems: the first may give more structure, the last gives the least, so the last problem is the core idea on its own |

Warm-ups should be low cognitive tasks, so they get more scaffolding than general questions. Spend the open, harder thinking on the core idea in the partner problems.

Put one line in the plan (`plan:` or `guide_notes`) naming the core idea, so the teacher knows where to spend whole-class time and which steps to move past quickly.

### Faded version (less scaffolding toward the end)

A lesson can also come in a faded version, with slightly less scaffolding as we get to the end of the lesson. Almost everything stays the same: same problems, figures, numbering, QuickNotes, and practice. Only what's printed versus blank, and the open space, change.
- **Warm-up:** all review, needing low cognitive load. Same as the standard version.
- **The main problems** (Together and the first partner problems): most of the review is filled out already, with maybe just a bit of old, repeated stuff left blank. That's a known step students have already done on this handout or in the last lesson.
- **The later problems** (the last partner problems): a bit less scaffolding, with more open space for students to figure it out. Known steps that the standard version prints become blanks or open work space, so students carry the whole argument. Frames shrink to a starter or go away, and the work space grows to match.
- The fade runs in one direction: each problem gets the same or less scaffolding than the one before it.
- No new labels: the student page still prints only the Warm-up heading.
- The faded copy lives in its own unit folder (for example `units/geometry/unit-3-similarity-faded/`), so the standard version stays as it is.

## Labels

Extra labels for sections aren't good. Student pages print only a plain **Warm-up** heading; after it, problems 1, 2, 3 run down the page with no Together or With a partner heading and no subtitle ("on your own", "Problems 1-2"). Set `headings: warmup` in the lesson YAML; the builder then prints nothing else. Which problems are Together and which are partner work lives in the plan, not on the student page.
- No section `title:` or `sub:` in the YAML, and no added layers (Activity 1, Synthesis, Launch / Explore / Summarize, "Part 1:", Cool-down, Reflection).
- A reading box the task needs (for example the ADA ramp rules) carries its name as the bold first line of the box, not as a section title.
- The plan's timing table still names the parts (Warm-up, Together, With a partner, QuickNotes) so the teacher knows the flow.

## Budget (Math Medic format)

| Part | Min | Items |
|---|---|---|
| Warm-up | 4 | 1 item, or 2-3 quick ones |
| Together | 6 | 1-2 problems, teacher works them |
| With a partner | 23 | 2-4 problems |
| QuickNotes | 4 | printed, read together |
| Collect, assign practice | 3 | |

These are the only parts. No exit ticket, check-your-understanding, cool-down, or reflection: we don't use closing checks. Spare minutes go to the partner problems, or the lesson just ends early.

Whole-class talk ≤ 14 min. The plan's timing table ends at 40 or less, and item `minutes:` add up to 40 or less (`lesson-builder check` enforces both).

## Per-item minutes (estimate before writing)

| Item type | Min |
|---|---|
| True/false, one fill-in, read-a-statement | 1 |
| Short answer with a figure | 2-3 |
| Patty-paper move with written moves | 4 |
| Fill-in explanation (3-4 boxes) | 3 |
| Construction or drawing task | 6-8 |
| Open "explain why" | 4 |

Put each item's minutes in its `minutes:` field in the lesson YAML, and in the blueprint table in `_temp/specs/<stem>/requirements.md`. If the total is over budget, cut before writing the YAML.

## What to cut first (new lessons and rewrites)

1. A second item that shows the same idea with new letters or numbers (keep the clearer one).
2. Extra parts in a multi-part item that repeat the first part.
3. Third and fourth warm-up items.
4. An exit ticket, check-your-understanding, or cool-down section. If its item checks the core idea in a way the partner problems don't, make it the last partner problem; otherwise cut it.
5. Anything the practice set (homework) already covers.
6. Items that don't touch the core idea.

Before cutting a core item for time, look for routine steps students are doing by hand (arithmetic, measuring, redrawing) and scaffold those instead. That often saves the minutes without losing the idea.

Keep: the one "doing mathematics" task and the item that sets up the QuickNotes. Never cut the item another item depends on unless you cut both.

## After any cut or renumber

- Search the lesson YAML (items, QuickNotes, `plan`, `guide_notes`, practice) for "Problem N" and fix every reference. `lesson-builder check` flags references to problems that don't exist.
- A reference must point to work that actually supports the task. "Use your claim from Problem 4" is only valid if Problem 4's claim is the reason needed. Otherwise name the fact directly.
- Log each cut in `_temp/specs/<stem>/changes.md`, one line each: item, reason, minutes saved.

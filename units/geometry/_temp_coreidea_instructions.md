# Unit 3 lessons: core-idea pass (Nov 19)

Teacher request (Nov 18-19): "Less is more when initially making lessons, so try to cut down on repetitive problems." Warm-ups "should be low cognitive tasks, so should have more scaffolding than general questions." "During the lesson it can be hard to get through the main content, so we can have more scaffolding around the steps to complete the problem that aren't the core of what we're supposed to be learning that day. That way the students don't have to spend their time and mental effort doing things like basic arithmetic that they already know, and they spend their time on the actual intuition building parts of the lesson." Narrow down what the "intuition" part of the lesson is and "structure our scaffolding around that, so that's the main work that students have to get through." Also: one closing check only (no cool-down or check-your-understanding next to the exit ticket), and no extra labels on every section.

Mode: revise, don't start over. Keep the lesson's topic, title, source problems, and figures where they still fit. Budget stays **30 minutes** (`unit.yaml`); landing under 30 is fine and good. Don't pad: no extension problems, and cut items are just cut (early finishers start the practice).

## 0. Load these skills first (required)

Use the `skill` tool to load each one, or read `.agents/skills/<name>/SKILL.md` in full. Follow them; they hold the rules this pass applies.

- `lesson-scope`: the main skill for this pass. Read "Less is more", "Find the core idea first", "Scaffold around the core idea", "Scaffolding by part of the lesson", "Labels", "What to cut first", and "After any cut or renumber".
- `lesson-assessment-designer`: Step 3 (lesson plan), Step 4 (student worksheet), and the Final check.
- `handout-release-check`: sections 1-2, including "Where scaffolds go" and the key rules.
- `mll-literacy-scaffolding`: Period 4 has many MLLs. Use the checklist; supports go heaviest on routine steps.
- `authentic-writer`: voice for every prompt, plan, and note you write.
- `curriculum-visual-generator`: only if you change a figure (moving routine marks or labels from `layer="answer"` to the given layer counts).
- Field reference: `.agents/skills/lesson-builder/references/api_cheatsheet.md`.

Finished model: Unit 2 lessons `units/geometry/unit-2-congruent-triangles/lessons/2.7.yaml` and `2.9.yaml` (and their `figures/` files). Read the plan's **Core idea.** paragraph and the "Nov 19: cut for the core idea" note in `guide_notes` to see the expected result.

## 1. Find the core idea

Read the lesson YAML, `figures/<stem>.py`, and `_temp/specs/<stem>/requirements.md`. Then, in `requirements.md`:
- Under **2. Targets**, add one line: `Core idea: students see that ...` (the one thing students should notice or explain today).
- Under the **3. Blueprint** table, add a **Core vs routine** list, one line per item: `Q3: core = ... | routine = ... (how it is scaffolded)`. Update the blueprint rows to match the new items and minutes.

Routine means steps the problem needs that aren't today's point: arithmetic, measuring, counting grid units, plotting given points, labeling or marking a figure, copying a figure, recalling a formula or a fact from an earlier lesson, and anything that was the core of an earlier Unit 3 lesson.

## 2. Revise the handout

- **Warm-up:** low cognitive demand, more scaffolded than the main problems (values given, choices or a fill-in, a figure to look at). About 3 minutes. Reviews a skill today's problems need.
- **Routine steps get scaffolded:** print the computed values, the labels and tick marks, the earlier-lesson steps, the formula or fact, or pre-fill table rows. Use the lightest support that removes the step.
- **The core step stays open:** no frame, bank, figure label, or fill-in hands over the claim or the reason. A sentence starter is fine. If a student gets stuck, they should be stuck on the core idea, not on arithmetic, reading, or redrawing.
- **Less is more:** one problem per step of the idea. Cut a second item that repeats the same move with new numbers or letters, and items that don't touch the core idea. Check across the lesson too (warm-up, partner work, and exit ticket shouldn't all ask for the same move).
- **One closing check:** the exit ticket. No `cyu` section.
- **No extra labels:** section names are the handout's own (Warm-up, Together, With a partner, QuickNotes, Exit ticket). No Launch/Explore/Summarize, "Part 1:", or subtitles added.
- After any cut or renumber, fix every reference. A `{ref:id}` in the exit ticket can't point to a problem before the QuickNotes (numbering restarts there; `check` errors). Name the work in words instead ("Use your parallelogram proof.").
- Every item, part, and box keeps an answer. Drawing tasks keep a red answer figure.

## 3. Practice (homework)

Cut practice items that repeat a handout item almost exactly, or repeat another practice item with new numbers. Keep each distinct skill at least once. Renumber and update `selected` so it names only items that exist. Don't add new problems. If you notice a practice item that duplicates another Unit 3 lesson's practice, list it in your reply; don't edit the other lesson.

## 4. Plan and notes

- `plan`: add a **Core idea.** paragraph after the Overview. It says what students should see, where to spend whole-class time, and which routine steps are printed so the teacher can move past them. The Quick look table ends at 30 or less, uses the handout's section names, and its minutes match the items. Paragraphs name only items that exist.
- `guide_notes`: add "**Nov 19: cut for the core idea.**" with one short paragraph saying what was scaffolded, cut, or merged. Rewrite or remove older notes that name problems that no longer exist (`check` warns on a "Problem N" that isn't there).
- `_temp/specs/<stem>/changes.md`: add a section "## Nov 19: core-idea pass", one line per change: `item: what changed | why (rule)`, then `total item minutes A -> B; plan N min`.

## 5. Figures and build

- Figures: if a routine mark (labels, ticks, given points) was on `layer="answer"`, move it to the given layer. Loop `uv run lesson-builder figs units/geometry/unit-3-similarity -l <stem>` until 0 errors and no label warnings. Look at the PNGs in `_temp/figures/<stem>/`. A label the lint moved to a misleading spot is worse than a warning: use `fixed=True`, `dist`, or a smaller `size` (printed size stays at least 8 pt).
- Build: `uv run lesson-builder build units/geometry/unit-3-similarity -l <stem> --no-packets`, at most 4 builds, 0 errors. Other lessons build at the same time; if the PDF export fails, rerun once.
- Look at every handout and key page in `_temp/renders/current/<stem>/`: nothing split from its figure, labels readable, no page left mostly empty by a stale `page_break_after` (a 2-page handout plus the QuickNotes page is fine).

## Files

You may write only: `lessons/<stem>.yaml`, `figures/<stem>.py`, `assets/<stem>/`, and `_temp/specs/<stem>/` (all under `units/geometry/unit-3-similarity/`). Never edit `src/`, `unit.yaml`, `.agents/`, another lesson, an assessment, or a DOCX. If the builder can't express something, use the closest field and log `GAP: <file>:<feature>: <symptom> | workaround` in `changes.md`.

Repo: `/Users/zubair/Documents/pdf-to-docx` (macOS, zsh, Python via `uv run`). Edit with the edit tool; scratch scripts go in `_temp/build/`.

## Reply (5-8 lines)

Core idea (one sentence); what was scaffolded; what was cut or merged; item minutes and plan minutes before -> after; handout and practice page counts; build result (errors, warnings); any open judgment call or cross-lesson duplicate.

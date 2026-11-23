# Plan: templates and less boilerplate for lesson-builder documents

Nov 19, 2026. Read-only review of the built lessons, practice sets, keys, guides, and assessments in Units 2-4. Finished models: 2.7, 2.9, 3.1, 3.3-3.7, 3.9, 3.11. "Before" examples: 3.13 and the Unit 4 lessons (mid-revision, so their counts may move). Counts come from read-only scripts in `_temp/build/templates_review/` and match text patterns, so they are rough.

Effort: S is under a day, M is one to three days, L is more. Every proposal keeps old YAML building unless its Risk line says otherwise.

**Update (Nov 19, after this review):** the teacher doesn't use exit tickets, and student pages should print only a Warm-up heading. `headings: warmup` now exists (spec, render, scaffold, example.yaml, test), `scaffold` and `example.yaml` no longer write `cyu` or `exit`, and the skills say "no closing check". Read the exit-ticket examples below (P1.2's checks, P2.3's `box: fill`) as "the last problem".

## 1. Findings

### What I looked at

| Source | Count |
|---|---|
| Lesson YAMLs | 19 (4,279 lines), 10 finished models |
| Assessment and reference YAMLs | 23 assessments and 3 summary-notes sheets (3,143 lines) |
| Figure files | 45 (8,426 lines): 330 figures, 108 helper functions (962 lines) |
| Handoff files | 45 `_temp/specs/*/` folders: 50 lines that mention a GAP, 24 `audit.md`, 15 Unit 3 audit reports |
| Built student PDFs | 64 PDFs, 142 pages measured with `pagefill.page_report` |
| Renders opened | 2.9 handout p1-3 and key p2; 3.3 p1; 3.4 handout p1-2, practice p1-2, guide p2; 4.7 p1-2; 4.6-4.7 Progress Check A p1 |
| Format source | `spec.py`, `render.py`, `scaffold.py`, `brief.py`, `docbuilder.py` (fill, frame, box, choices, `cell_problem`), both `example.yaml` files, `docs/lesson_builder.md`, `docs/plans/phase1-3.md`, `docs/plans/weak-model/shrink-authoring-surface.md` |
| Teacher sources | `units/*/input/`: Student Notes, Practice Problems, progress checks, reviews, tests, summary notes, one standalone practice set |

### Boilerplate that repeats

| Pattern | Rough count | Proposal |
|---|---|---|
| Plan "Quick look" tables typed by hand | 19 tables, 121 rows; 62 typed "Problem N" in plans; a row's minutes differ from its section's item minutes in 12 of 19 lessons (7 of 10 finished models) | P1.4 |
| Practice answers typed a second time in `selected: [[n, answer], ...]` | 71 answers in 14 lessons; `selected: auto` used 0 times | P1.4 |
| **Objectives.** and **Standards.** lines in `plan` that copy the targets | 15 plans | P1.4 |
| **Core idea.** paragraph in `plan`, plus `Core idea:` in requirements.md | 12 plans | P1.2 |
| Routine steps typed as prompt lines ("Step 1: ...") | 16 lines; 'Step N:' fill rows for the student's moves in 6 documents, including the student's own Step 3 after typed Steps 1-2 (2.9, 3.6) | P1.3 |
| A printed fact, theorem, or definition as a bold-led prompt line | 9 lesson lines in several spellings ("**Fact:**", "**Fact from Unit 1:**", "**Angle-Side-Angle (ASA) Triangle Congruence Theorem:**"), plus definition blocks faked as `n: '', minutes: 0, work: 0, no_answer: true` items (4.10.yaml:41-52) | P1.3 |
| "*Optional start:*" lines | 11 | P1.3 |
| "Scoring notes (MLL)" paragraph | 35 documents (17 lessons, 18 assessments); "Score the math, not ..." 40 times | P2.4 |
| Per-problem scoring typed in `guide_notes` ("Problem 2 (3 pts): ...") | 35 lines in 6 assessments; Unit 4 Test A writes "1 pt equation, 1 pt answer" inside each `answer` | P2.6 |
| Explicit `box_w` | 149 lines, 68 of them 0.9 (the default is 1.3); `fill_cols: 1`, the default, 25 lines | P2.4 |
| `work: 0` on reference-sheet items | 34 of 38 items | P2.5 |
| Bullets typed as "•" | 89 lines (two summary-notes sheets, the 4.1 ADA box) | P2.5 |
| `layout:` in practice cells and two-column sections | 50 lines, all ignored: `docbuilder.cell_problem` always stacks | P2.2 |
| Dated change-log paragraphs in `guide_notes` | 26 | P3.2 |
| Figure helpers copied between files | `_tri` in 10 files, `_parallel` in 7 (a copy of `is_parallel`), `_grid` in 6 (a copy of `f.grid`); the progress-check form sets copy `_split`, `_rects`, `_lines`, `_dilate_task` into every form; no unit uses `figures/_helpers.py` | P2.7 |

### Flexibility gaps

**GAP lines.** The 50 lines come to about 30 distinct gaps. About 11 are fixed in `src` (proof tables, half-printed proof cells, the selected-answers drift false alarm, arc ticks, the QuickNotes figure, `fill` on draw items, `\alpha` `\beta` `\sqrt[3]{}`, upright trig names, long fill labels in half-width cells). Four are prime and fraction glyph problems and three are tooling, both out of scope here. The open format gaps:

| Gap | Evidence | Proposal |
|---|---|---|
| A table is one header row plus one all-blank answer row, and the guide prints its answers as arrows | `spec.Table`; the 3.3 ratio table (`row_label: Value`) and its GAP; 4.6 GAP "no field for a TRUE/FALSE grid"; T/F faked as frame rows (4.7 practice 8) and fills (3.9 practice 4, Unit 3 Test Retake "TRUE or FALSE:") | P1.5 |
| `selected: auto` keeps only the first sentence of a long answer | 4.5 GAP ("shows BD = 5 but not AD") | P1.4 |
| One box per frame sentence; boxes in a multi-row frame start at different x; short labels wrap | 4.7 GAP: "tan(□°) = □/□" printed as text after the box; 3.1 GAP, closed only because the item was cut; 2.5 and 2.9 label wraps | P2.1 |
| A draw item can't print its own figure; its box can't go under 2.2 in; practice cells ignore `draw` and `layout`; the drawing box has no label | 3.13 changes.md:133 (three half-full pages); 3.9 GAP; 4.7 GAP; 2.6 GAP; Unit 2 Test audit ("Sketch in the box" with two boxes on the line). 3.9 and the current 3.13 revision both switched from `draw` to a plain figure item that students draw on | P2.2 |
| Assessment guides say "(labeled sample drawing on the lesson key)" | Trig Word Problems Practice audit #4 | P2.2 |
| `Part` has no `box`; a choice can't hold a line break | Unit 2 Test GAPs (#7a, #4) | P3.3 |

**Layouts.** 58 of 142 student pages have 3 in or more of empty paper. Some of it is on purpose: the QuickNotes answer the partner problem, so they go on the back with the exit ticket (7 plans tell the teacher to hold that page until then), and 3.1-3.5 Progress Check A starts its second target on a new page. The trouble is the tight space right next to the blank. Every finished Unit 3 handout's page 2 is 3.2 to 5.6 in empty, and on 3.4 p2 each exit-ticket part gets 0.6 in of work space above about 5 in of blank paper. 3.4 practice p2 holds one SBA item and the answer strip (7.4 in empty); 3.9 practice p2 is 7.7 in empty. Each of 2.9's three pages is 4.2 to 4.7 in empty. Audits already ask authors to raise `work` by hand to use the space (4.5, 4.7, Unit 4 Review).

**Teaching moves with no field.** From lesson-scope and handout-release-check: the core idea (typed in requirements.md, the plan, and `guide_notes`), printed routine steps that end with the student's step, a printed fact, an optional sentence starter, and a pre-filled table with only the pattern cells blank. None of the new rules is checked. The lessons that haven't had the core-idea pass (2.1, 2.5, 2.6, 4.7, 4.10) still carry 5 `cyu` sections and 7 extra section titles ("Tilted triangle", "Triangles from words", "Synthesis"), and 4.10's warm-up is an open "show it" item with no scaffold.

**The templates teach the old rules.** `templates/unit/lessons/example.yaml` has a `cyu` section (line 74), "Explain why. Fill in each box." (line 45), and a "CYU + exit ticket" plan row (line 139). `brief --step write` pastes those blocks into every Write brief (2.7's `brief_write.md` lines 273, 306, 382). `scaffold` writes "Look back at {ref:together_1}" (scaffold.py:59), which authentic-writer now cuts, uses minutes 5/7/16/4/6/2 instead of lesson-scope's 4/6/17/4/6/3, has no SBA review heading (18 of 19 lessons add one) and no Scoring notes, and writes a requirements.md with no `Core idea:` line or Core vs routine list, though orchestration.md asks the Plan step for both.

**Document types.** The teacher's sources map onto lesson, assessment, and reference, with two strains. The standalone Trig Word Problems Practice is an assessment with no points (output under `Assessments/`, "lesson key" wording). Summary notes are reference sheets with one `plain` section per lesson, usually holding one item; Unit 3's sheet repeats lesson QuickNotes in 33 of 47 lines, Unit 4's in none. The cheat sheet and curriculum-visual-generator say "two-way tables and trace tables are YAML tables", but the schema can express neither, so Periods 5 and 6 have no path yet. No source asks for a warm-up set or bell-ringer sheet.

**Plans this builds on.** phase1 G1, phase2 G2, and `weak-model/shrink-authoring-surface.md` sections 1-2 plan a pattern library and `scaffold --items`; phase2 A1 plans unit `defaults`; phase2 F11 plans automatic layout fixes; phase3 F8 plans `Grid`, `TF`, and `Frame.template`. None of these is built yet: there is no `templates/patterns/`, no `UnitSpec.defaults`, and no grid in `spec.py`. This plan adds the shapes the Nov 18-19 rules need, moves the grid up, and replaces `Frame.template` with segment frames.

## 2. Proposals

### P1.1 Templates and scaffold match the finished models (S)

Problem: see "The templates teach the old rules". Every new document starts from the old rules, and the Write step takes them out by hand.

Proposal: rewrite `lessons/example.yaml` from the shapes of 3.4, 2.9, and 3.6: no `cyu`; `numbering: auto`; a warm-up with a figure and two fills; a Together item with printed steps; a partner item with a fact, an optional start, and an open box; one exit ticket; practice with an SBA heading. `scaffold` writes the same skeleton with lesson-scope's minutes and one plan paragraph per part:

```yaml
plan: |
  **Overview.** TODO
  **Warm-up.** TODO
  **Together.** TODO
  **With a partner.** Assessing: TODO. Advancing: TODO. Watch for: TODO. MLL supports: TODO.
  **QuickNotes.** TODO
  **Exit ticket.** Look for: TODO
```

requirements.md gets the lines the Plan step now types by hand:

```markdown
Core idea: students see that TODO

| Item | Target | Type | Demand | Min | Figure |
Core vs routine:
- Warm-up: core = none | routine = TODO (how it is scaffolded)
- Q1: core = TODO | routine = TODO
```

- Files: `templates/unit/lessons/example.yaml`, `scaffold.py` (`lesson_yaml`, `LESSON_ROWS`, `requirements_md`), `brief.py` (the plan step's "Done when" requires the Core idea line; the write brief prints it first), `docs/lesson_builder.md`, one line in the lesson-builder skill.
- Tests: `tests/test_lesson_scaffold.py`: the scaffolded lesson loads, `check` shows only TODO warnings, it has no `cyu`, and requirements.md has `Core idea:` and one Core vs routine line per item. Update `test_yaml_blocks_split_template`.
- Risk: none for built units (templates only). The scaffold tests change.

### P1.2 Core idea as data, plus checks for the new lesson rules (S)

Problem: the core idea is typed in three places, and the new rules live only in the skills.

```yaml
core_idea: 'Students see that a dilation keeps angle measures, so a line that misses the center goes to a parallel line.'
...
      - id: jada_proof
        core: true          # the core step; it stays open
```

The guide prints **Core idea.** at the top of the plan, so authors stop typing it there. New lesson-only WARNs: no `core_idea` and no Core idea paragraph; a `cyu` section ("one closing check"); a section `title` or `sub` other than the handout's own name (a `plain` section with a `box`, like the 4.1 ADA rules, stays allowed); a warm-up item with no fill, frame, choices, table, or columns ("warm-ups are scaffolded"); a `core` item in a partner or exit section with two or more frame rows or a bank ("keep the core step open"); `start:` on more than 3 items (item-rules section 6). `status` gets a core column.

- Files: `spec.py` (`LessonSpec.core_idea`, `_Scored.core`), `render.guide_markdown`, `check.py`, `status.py`, `brief.py`, `example.yaml`, one line each in lesson-scope and handout-release-check.
- Tests: `tests/test_lesson_checks.py`: each WARN fires on a small document, and none fires on copies of 2.7, 2.9, 3.4, and 3.6.
- Risk: new WARNs on 2.1, 2.5, 2.6, 4.7, and 4.10 until their core-idea pass. They are WARNs, so builds pass unless run with `--strict`.

### P1.3 Fields for the scaffold moves: student steps, fact, start (S-M)

Problem: lesson-scope says to print the earlier steps, print the fact, and offer a starter. Authors type all three as prompt lines. `steps:` can't hold the student's step and always prints after the last prompt line, so 2.9 and 3.6 type Steps 1-2 and fake Step 3 as a fill (the 2.9 render shows bold printed steps next to a plain "Step 3:" label), and Unit 3 Test A/B #6 and 3.6 Problem 2a use 'Step N:' fill rows for the student's moves.

Before (2.9.yaml:41-48):

```yaml
prompt:
  - '... Finish the rigid motions that take $\triangle STU$ onto $\triangle GHJ$.'
  - 'Step 1: Translate $\triangle STU$ so that $S$ lands on $G$.'
  - 'Step 2: Rotate around $G$. $ST = GH$, so $T$ lands on $H$.'
fill: [['Step 3:', 'Reflect across $\overleftrightarrow{GH}$.']]
box_w: 3.6
```

After:

```yaml
prompt: '... Finish the rigid motions that take $\triangle STU$ onto $\triangle GHJ$.'
steps:
  - 'Translate $\triangle STU$ so that $S$ lands on $G$.'
  - 'Rotate around $G$. $ST = GH$, so $T$ lands on $H$.'
  - {ans: 'Reflect across $\overleftrightarrow{GH}$.', w: 3.6}   # the student writes Step 3
```

And 3.4.yaml:39-43, with the "**Fact:**" and "*Optional start:*" lines moved out of the prompt:

```yaml
prompt:
  - '$\triangle A''B''C''$ is the dilation of $\triangle ABC$ from the warm-up ... $E''$ is the image of $E$.'
  - 'Use the warm-up and the fact to explain why $\overline{BC} \parallel \overline{B''C''}$.'
fact: 'A transversal cuts two lines. If corresponding angles are congruent, then the two lines are parallel.'
start: '$\angle E''B''C''$ is the image of $\angle EBC$, so ...'
```

Printed steps look as they do now. A blank step is the bold label plus a box from the fill renderer: the same height on both copies, with the answer in red on the key. `fact` prints "**Fact:** ..." before the last prompt line; a fact that starts with `**` keeps its own lead, for a named theorem. `start` prints "*Optional start:* ..." last. A prompt line `'{steps}'` or `'{fact}'` puts them somewhere else (2.7 asks its question after the steps). `fact` and `start` also work on parts. Both count as student text for the voice checks and answer cues, so a printed fact that answers another item on the same page is a WARN (the case 3.4's `guide_notes` describes).

- Files: `spec.py` (`StepBlank`; `Item.steps` takes a string or a blank; `fact` and `start` on items and parts), `render._prompt_lines`, `_body`, `_answers_md`, `check._texts`, `integrity.answer_cues`, `example.yaml`, cheat sheet section 3.
- Tests: `tests/test_lesson_render_schema.py`: the 2.9 and 3.4 shapes give the same DOCX text as their typed form; blank steps are red only on the key and the same height on both copies; the placement tokens work; old string steps are unchanged.
- Risk: none. Nothing old changes meaning.

### P1.4 Generate what is typed twice: timing table, targets, answer strip (S-M)

Problem: see the first three rows of the boilerplate table. The plan rows and the item minutes are two copies of the timing with nothing tying them together; part of the gap is share time that the items don't carry. A typed `selected` list attaches answers by number, so a renumber silently moves them to the wrong items.

```yaml
sections:
  - kind: partner
    minutes: 10                      # plan minutes: items (8) plus the share; default = item minutes
    who: 'Students (pairs), 2 min share'
  - kind: notes
    minutes: 3
practice:
  rows:
    - cells:
        - prompt: 'Find the length of $\overline{DF}$. Show your work. Not drawn to scale.'
          answer: ['$\angle A\cong\angle D$ and ...', '... so $DF=24$.']
          short: '24'                # the answer strip and the guide's quick key
  selected: auto                     # or ids: [pr1, pr3]
```

When `plan` has no typed table, the guide inserts "**Quick look (N min).**" built from the sections: the handout's names, problem numbers from `_section_sub`, the `who` column (a default per kind), a QuickNotes row (default 4 minutes, scaled to the budget like `scaffold.lesson_minutes`), and a "Collect, assign practice" row (`collect_minutes`, default 3). When `plan` has no Objectives line, the guide prints a **Targets.** line from `targets`. `selected` uses `short` first and accepts ids. `check` applies the budget rule to the generated table and WARNs when a typed `[n, answer]` pair disagrees with its item.

- Files: `spec.py` (`Section.minutes`, `Section.who`, `LessonSpec.collect_minutes`, `_Scored.short`), `render.guide_markdown`, `_derive`, `selected_answers`, `check.py`, `scaffold.py`, `example.yaml`.
- Tests: table rows and end time come from section minutes; `short` beats the first sentence; ids work in `selected`; the mismatch WARN fires; a typed table suppresses the generated one.
- Risk: none for current plans. A lesson moves over when it is next edited.

### P1.5 Grid tables with printed and blank cells (M)

Problem: see the first row of the gap table. lesson-scope's "pre-fill most of a table and leave blank only the cells that show the pattern" has no field, and neither do trace tables or two-way tables.

```yaml
table:
  header: true                       # first row bold
  rows:
    - ['', 'Original', 'Image', 'Ratio']
    - ['$EF$', '3', {ans: '6'}, {ans: '2'}]
    - ['$FG$', '5', {ans: '10'}, {ans: '2'}]
  widths: [0.8, 1.2, 1.2, 1.2]       # optional
```

A cell is printed text or `{ans: ..., before: ...}`, the proof's `Blank`. Row heights come from the longer of the printed text and the answer and are set exactly on both copies (the `_proof` code, generalized). A T/F list or a sort is a grid with one answer column. The old `header`/`answers` form still renders as the arrow table. `proof` keeps its own field and shares the renderer. The guide prints answers by row, not with arrows, and integrity reads grid answers.

- Files: `spec.py` (`Table.rows`, `widths`, `header`, a validator that takes the old form or `rows`), `render.py` (`_grid`), `_answers_md`, `integrity.py`, cheat sheet, the curriculum-visual-generator line on tables, `example.yaml`, and a note in phase3.md that this replaces F8's `Grid` and `TF`.
- Tests: both copies with equal row heights; the old arrow table unchanged; guide text; a grid in a one-cell practice row (practice cells drop `table` today); integrity sees the answers.
- Risk: low, and additive.

### P2.1 Frames with several boxes in one sentence, and aligned boxes (M)

```yaml
frame:
  - ['The building is about', {ans: '817.7 m', w: 1.1}, 'tall because $\tan($', {ans: '73', w: 0.6},
     '$^\circ) =$', {ans: '$\frac{AB}{250}$', w: 0.9}, '.']
frame_align: true                    # the first box of every row starts at the same x
```

A row with any `{ans:}` cell reads as segments; old `[before, answer, after, w]` rows don't change. This replaces F8's `Frame.template` and closes the 4.7 and 3.1 GAPs. Files: `spec._frame_rows`, `docbuilder.frame`, `render._answers_md`, `check._box_issues`, `integrity`. Tests: each box holds its answer on the key; box x positions match with `frame_align`; old rows unchanged. Risk: low.

### P2.2 Draw items and practice cells (S-M)

A draw item's `figure` prints under its steps on the student copy (today `render._draw` uses it only for the key). `draw.label:` names the box. The box's minimum height comes from the key figure instead of a flat 2.2 in. `_cell_item` honors `draw` and `layout: side`. The guide says "key", not "lesson key", on assessments. Until `layout` works in cells, `tidy` reports those lines. A figure that students draw on (what 3.9 and 3.13 do now) stays a fine choice; this makes `draw` usable when students need open room. The before version of 3.13 would not have needed its unnumbered setup item:

```yaml
      - id: untangle
        figure: 3.13_hfe                  # now printed on the student copy
        draw: {height: 2.2, key_figure: 3.13_redraw, key_fig_w: 3.3, label: 'Draw here'}
```

Tests: each case on both copies; drift check clean. Files: `spec.Draw.label`, `render._draw`, `_cell_item`, `docbuilder.cell_problem`, `tidy.py`. Risk: documents change only when their YAML does, except the height rule, which can move items after a short draw box; recheck page fill on the 15 draw items now in Units 2 and 4.

### P2.3 Use the empty half pages (M)

```yaml
  - kind: exit
    items:
      - prompt: '...'
        box: fill                     # takes the page's free space on both copies, never less than 1.2 in
```

Add `spread: true` on an assessment section (the page's free space is shared among its items' `work`), and `practice.max_pages` so a short practice set can aim for one page. `fit.py` reads the page report after the fitted build, sets the heights, renders once more, and keeps the result only if the page count and every item's page stay the same. This extends phase2 F11. Files: `spec.py`, `render._work`, `fit.py`, `pagefill.py`, docs. Tests: a stub page report gives the expected heights; a change that moves an item is reverted; drift clean. Risk: one more render per document (about 20 s with Word).

### P2.4 Unit defaults for repeated settings (S)

```yaml
# unit.yaml, extending phase2 A1 `defaults`
defaults:
  box_w: 0.9
  scoring_notes: 'Score the math, not grammar or spelling. Accept home-language words, cognates, and a decimal comma (2,4 = 2.4).'
# lesson or assessment
accept: ['"same" or "equal" for congruent', '"corr. angles" for corresponding']
```

The guide prints "**Scoring notes (MLL).**" from the unit text plus "Also accept: ...". A document's own Scoring notes paragraph wins. `tidy` reports `fill_cols: 1` and `box_w` lines equal to the default, as it does for `work:`. Files: `spec.UnitSpec.defaults`, `LessonSpec.accept`, the `render` fallbacks for unset fields, `guide_markdown`, `tidy.py`, `scaffold.py`. Tests: the default applies; the document wins; guide text. Risk: none until a unit sets `defaults`.

### P2.5 Reference sheets and boxes (S)

`doc_type: reference` defaults `work` to 0. Section `box` lines and a prompt's first line take "- " bullets; prompt lines after the first already do (`docbuilder._line`), but the cheat sheet doesn't say so, hence the 89 typed "•". Files: `render._work`, `docbuilder.box`, `_problem_text`, cheat sheet section 3. Tests: the work default; box bullets. Risk: three Unit 2 Summary Notes items have no `work` and would lose 0.8 in; give them `work: 0.8` in the same change.

### P2.6 Scoring data on the item (S)

```yaml
      - points: 3
        credit: '1 pt for a proportion that uses the whole side 11, 1 pt for solving, 1 pt for $\frac{40}{11}$ or 3.64'
      - select_all: true
        penalty: 0.25                 # prints "Each wrong or missing choice loses 1/4 point." and the scoring line
```

Teacher Notes print a **Scoring** list with item numbers and points, so a renumber can't break it. Files: `spec._Scored` (`credit`, `penalty`), `render._prompt_lines`, `guide_markdown`, `check.py`. Tests: the guide list, the prompt sentence, a WARN when the points in `credit` don't add up to `points`. Risk: none.

### P2.7 Figure helpers (S-M)

Add `geometry.triangle(f, pts, names, right=None, arcs=None, sides=None, layer="given")` to replace the 10 `_tri` copies. `scaffold --forms` writes `figures/_<set>.py` and imports it in each form. `scaffold --figure triangle|grid|right|none` picks the starting example (today every figure file starts from a dilation, trig lessons included). `figs` lint WARNs on local `_parallel`, `_grid`, and `_on_ray` functions that copy library helpers. This pairs with the shrink plan's derived labels and `right_triangle` model. Files: `figures/geometry.py`, `scaffold.figures_py`, `figures/layout.py` (lint), cheat sheet section 4, curriculum-visual-generator. Tests: helper asserts; scaffolded forms import the shared file. Risk: none for existing figure files.

### P3 (small, later)

- P3.1 `doc_type: worksheet` (S-M): standalone practice is an assessment with no points today. The new type has no Score line, writes to `output/Worksheets/`, says "Key", and takes an optional plan; `scaffold --type worksheet` writes a warm-up, practice items, and a closing check (lesson-assessment-designer Step 4). Files: `spec.py`, `render.outputs`, `packet.py`, `scaffold.py`, `brief.py`. Tests: outputs and wording per type. Risk: output paths and packet grouping; Trig Word Problems Practice moves only if its `doc_type` changes.
- P3.2 `history:` (S): `[{date: 'Nov 19', note: '...'}]` prints last under "Changes" and is exempt from the "Problem N" WARN, so old notes stop being rewritten after each renumber. Files: `spec.py`, `render.guide_markdown`, `check.py`. Tests: guide order; no WARN on old numbers. Risk: none.
- P3.3 Small sugar (S each): an item's `target` defaults to its section's (Unit 4 Test A writes each target on the section and again on the item); `setup: true` for an unnumbered text or figure block (the before version of 3.13, 4.10's definitions, the Trig Word Problems vocabulary block); `Part.box`; a choice given as a list prints one line per entry. Files: `spec.py`, `render._body`, `docbuilder._choices`, `numbering.py`. Tests: one per item in `tests/test_lesson_render_schema.py`. Risk: none; each is opt-in.
- P3.4 `scaffold --like "<form>"` (S): copies a form's skeleton (points, target, type, demand, parts, fill labels) with TODO text and new figure names. The Unit 4 progress-check forms share one skeleton, and `integrity` still forces new letters and numbers. Files: `scaffold.py`, `cli.py`. Tests: `tests/test_lesson_scaffold.py` (skeleton copied, no source text left). Risk: none.

## 3. Don't do

- Derive Form B or a retake from Form A by renaming letters and numbers. Exam integrity wants new figures, orientations, contexts, and MC positions; a renamer makes look-alike forms that pass the letter check.
- Size boxes from the key answer. A box that fits its answer is an answer cue. A unit default does the job.
- Build summary notes by pasting QuickNotes. Unit 4's notes share no lines with its QuickNotes, QuickNotes point at lesson problems, and notes must avoid test numbers (the Unit 3 audit caught a 6-8-10 figure that answers Test A #5).
- Let `{ref:}` cross the QuickNotes boundary, or stop restarting numbers there. "Problem 3" next to an exit ticket numbered 1 confuses students; 2.7's "Use your parallelogram proof." reads better.
- A "given values" box. Prompt lines and figure labels already carry given values (3.3 prints the counts from $C$); another box adds reading for MLLs.
- Plan fields for assessing and advancing questions. Teacher prose reads better as Markdown. Generate only what is counted: timing, targets, scoring.
- New section kinds or label layers (Synthesis, Activity 1, Launch/Explore/Summarize). lesson-scope's labels rule forbids them.
- Removing `cyu` from the schema. Old units would stop loading; P1.2 warns in lessons instead.
- A yes/no field. "(yes or no)" in the label is short and clear.
- An expression language for answers (already turned down in shrink-authoring-surface.md).

## 4. Order of work

P1.1 and P1.2 first (templates and checks, no unit edits), then P1.3 and P1.4, then P1.5 with P2.1, which share the box and table code. Each change lands with its tests and a line in `example.yaml`, and `check` stays at 0 errors on all three units. Don't migrate built units in bulk or during a wave: a document picks up the new fields the next time it is revised, and its `changes.md` logs the swap.

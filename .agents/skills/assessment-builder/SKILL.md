---
name: assessment-builder
description: One-call workflow for writing or rewriting a test, quiz, retake, or worksheet for Franklin HS room 105. Runs requirements intake, source extraction, a fair and MLL-accessible draft in teacher voice, answer key and rubric, automated checks, Worksheet AST, figures, DOCX/LaTeX packing, and a visual audit. Use whenever the user asks to make, rewrite, adapt, or fix an assessment or worksheet.
---

# Assessment builder

Runs the whole job in order, in this session. Don't spawn subagents. Each step writes a file, and the next step reads it, so the work can resume after an interruption.

Load these only when the step that needs them comes up:

| Step | Load |
|---|---|
| 1 | `classroom-context` (only the section for the target period) |
| 1 | `course-content-extractor` (only if there's no source file, or a retake/variant is needed) |
| 2 | `lesson-scope` (lesson handouts and worksheets: 40-min budget, what to cut) |
| 3-8 | `lesson-builder` for lesson handouts (YAML instead of `draft.md`; replaces Steps 6-7 here) |
| 3-4 | `references/item-rules.md` (this folder), `authentic-writer`, `handout-release-check` §1-2 (fill-ins, keys) |
| 6 | `curriculum-visual-generator` |
| 7 | `worksheet-packer` |
| 8 | `visual-layout-checker`, `handout-release-check` (scripts, packets) |

Workspace (see AGENTS.md): sources in `input/`, final files in `output/`, everything else in `_temp/{specs,assets,renders,build}/`.

## Exam integrity

If a source is a real exam that students have taken or will take, never copy an item verbatim into review, practice, or retake material. Keep the target, item type, cognitive demand, and points. Change the numbers, the figure's orientation and letters, the context, and the variable or method names. In Geometry, compare Form A to Form B first to see how much the district varies items.

## Step 0: Requirements

Write `_temp/specs/requirements.md`:

- Mode: **rewrite** (improve an existing document) or **new** (build from targets or sources).
- Course and period, learning targets or standards, and item types and counts.
- Total points, page budget, and whether this is a retake or variant of an exam.
- Source files.
- Anything the user said to keep or change.

Fill gaps from the source document and `classroom-context`. Ask the user only about things you can't infer and that change the output: the page budget, or the points when no source gives them. Ask all questions at once.

## Step 1: Context and sources

- Note the period profile in a few lines at the top of `requirements.md`. Period 4 Geometry has many MLLs, so apply section 6 of item-rules fully. Period 5 AP Stats follows CED wording and E/P/I scoring. Period 6 AP CSA follows CodeHS Java style and uses tracing.
- Rewrite mode: get the source into an editable form.
  - `.docx` or `.pdf`: run `uv run worksheet-packer parse <src> -o _temp/specs/source_spec.json --workspace-dir _temp/assets` to collect text and figures.
  - Or read the file directly if parsing doesn't work well.
- New mode: use `course-content-extractor` to pull matching items, keys, and figures into `_temp/specs/extracted_content.md`.

## Step 2: Blueprint

Add a table to `requirements.md` with one row per item: item number, learning target, item type, cognitive demand level (memorization / procedures without connections / procedures with connections / doing math), and points. Check that it covers the targets and isn't all procedural. Rewrite mode: build the table from the existing items, then flag any item that doesn't fit a target.

Lesson handouts and worksheets: add a minutes column (estimates in `lesson-scope`). The total is 40 or less. Cut before drafting, not after.

## Step 3: Draft (one pass, rules applied while writing)

Write `_temp/specs/draft.md` with `references/item-rules.md` and `authentic-writer` open. Apply them as you write. Don't plan a separate cleanup pass.

Rewrite mode: keep the item order, numbering, points, figures, and math unless the user asked for changes or an item breaks a rule. For each change, add one line to `_temp/specs/changes.md`: item, what changed, and why (cite the rule, e.g. "T&N7: removed 'all of the above'").

Draft format, which the checker and the AST step both expect:

```markdown
# Unit 2 quiz: congruent triangles
**Course**: Geometry, Period 4 | **Total**: 20 pts | **Pages**: 2

### Part 1: Rigid motions (target G.CO.6)
Answer each question. Show your work on Part 2.

#### Problem 1 (Reflection) [2 pts]
Triangle $ABC$ is reflected over line $m$. Which figure shows the image?
- **Image**: `_temp/assets/fig_q1_reflection.png`
- **Layout**: side_by_side
- (A) Figure 1
- (B) Figure 2
- (C) Figure 3
- (D) Figure 4

#### Problem 5 (Explain congruence) [4 pts]
Explain why $\triangle PQR \cong \triangle STU$. Be sure to include:
- the rigid motion you used
- which parts match
- **Workspace**: 1.5 in
```

- Put each section's learning target in its heading so scores can be reported by target.
- Use workspace heights instead of blank lines. Name, date, and period go only in the header.
- Each figure gets an `**Image**` line with a planned path, even before it exists.

## Step 4: Key, rubric, scoring notes

Write `_temp/specs/key.md`:

- MC: `N. (X) one-line reason`. Under it, the error each distractor targets, one line per distractor.
- Constructed response: a model answer, where each point comes from, acceptable alternatives, and "credit any valid method." AP Stats uses E/P/I per part.
- If a rubric is needed, use 3-6 specific levels and score communication separately from content.
- Add a short "Scoring notes" block for MLL work (item-rules section 8) when the period has MLLs.
- Every item, part, and fill-in box has an answer. Drawing or marking items get a labeled answer figure (`- **Key image**: <path>`), not a description (`handout-release-check` §2).

## Step 5: Check and fix

```bash
uv run python .agents/skills/assessment-builder/scripts/check_draft.py _temp/specs/draft.md --key _temp/specs/key.md
```

Fix every ERROR. Fix WARNs unless there's a reason not to; a NOT stem that's really needed is one. Then read the draft once against this list and fix what fails:

- [ ] Every item matches a blueprint target, and the targets are covered.
- [ ] Each MC item has one defensible answer, distractors drawn from real errors, and parallel options.
- [ ] Language load is down but the math is the same: math terms kept, dual-meaning words clear, visuals labeled, no idioms or insider contexts.
- [ ] Contexts are ordinary and every number has a purpose.
- [ ] It reads like a teacher wrote it: direct stems, nothing addressed to the reader at the start or end.
- [ ] The page budget is plausible. Step 7 confirms it.
- [ ] No `___` blanks; every fill-in is a labeled box under its problem, naming the figure it refers to.
- [ ] Every "Problem N" exists and supports the task.

Lesson handouts: write a lesson YAML instead of `draft.md` and use `lesson-builder` for Steps 5-8 (it checks, renders, fits pages, and builds packets).

Rerun the script until it shows 0 errors.

## Step 6: AST and figures

Translate `draft.md` into `_temp/specs/worksheet_spec.json` using the `WorksheetSpec` schema in `src/worksheet_packer/worksheet_ast.py`. The key never goes in the student spec.

| Markdown | AST |
|---|---|
| `# title`, `**Course**` line | `title`, `subtitle` |
| `### Part ...` + first paragraph | `WorksheetSection(id, title, instructions, ordering="strict")` |
| `#### Problem N (T) [X pts]` + text | `Problem(id="qN", number=N, points=X, prompt_text=...)` |
| `- (A) ...` | `choices: [{label: "(A)", text: ...}]` |
| `**Workspace**: X in` | `workspace: {type: "blank", approx_height_in: X}` |
| `**Image**` / `**Layout**` | `image: {media_path, category, min/preferred/max_width_in, has_fine_text}`, `layout_hint` |

Use `layout_hint: "side_by_side"` for portrait or square figures and `"stacked"` for wide grids or plots. Set `default_columns`, margins, and font size for the page budget. Defaults: 2 columns, 0.5 in margins, 10-10.5 pt.

Figures: reuse the cropped figures in `_temp/assets/` from Step 1 where they fit. Make any others with `curriculum-visual-generator` (script in `_temp/build/`, 300 DPI, then `worksheet_packer.image_utils.auto_crop_image`). For variants, redraw rather than reuse: the figure has to match the new numbers and letters.

## Step 7: Pack and render

```bash
uv run worksheet-packer pack _temp/specs/worksheet_spec.json -o _temp/specs/render_plan.json
uv run worksheet-packer render _temp/specs/render_plan.json -o "output/<Name>.docx" --format docx
uv run worksheet-packer render _temp/specs/render_plan.json -o "output/<Name>.tex" --format pdf
```

If the user wants the key as a document, build a second spec from `key.md` and render it to `output/<Name> - Key.docx`. Otherwise copy `key.md` to `output/`.

## Step 8: Visual check

```bash
uv run worksheet-packer render-docx-pages "output/<Name>.docx" -o _temp/renders/docx --dpi 150
```

Look at every page using the `visual-layout-checker` checklist. Problems to catch:
- labels too small to read, or figures stretched
- uneven columns
- an item split across pages
- not enough room to write
- more pages than the budget allows

Fix the problem in `worksheet_spec.json` (workspace, widths, layout hints, columns, font), not in the DOCX. Then repack. Stop after 3 rounds and report what's left.

Then run `uv run lesson-builder check-pdfs <student.pdf> <key.pdf>` on the student/key pair and build duplex packets if the user prints sets (`handout-release-check` §4).

## Finish

Tell the user:
- Which files are in `output/`.
- The page count, point total, and how many items there are of each type.
- Rewrite mode: the main changes from `changes.md`, grouped (e.g. "simplified 6 stems, replaced 2 'all of the above', added labels to 3 figures"), plus anything you flagged but didn't change.
- Any judgment calls the user should check.

---
name: lesson-audit-step
description: The read-only Audit step for one lesson, assessment, or set of forms, run as an independent subagent. Runs the lesson-builder checks, then reads the built pages, figures, keys, and YAML for what scripts can't judge. That covers the teacher's lesson rules (lesson-style), key correctness, figure fidelity, layout, room to write, answer giveaways, MLL access, item quality, and exam integrity across forms. Writes `_temp/specs/<stem>/audit.md` with Must fix / Should fix / Looks fine, each line mapped to a YAML or figure-file fix. Never edits anything else.
---

# Audit step (read-only)

You are a step subagent. Read `_temp/specs/<stem>/brief_audit.md` first. You never edit lesson, assessment, figure, or source files. The only file you write is `audit.md`.

Load: `lesson-style` (the rules to check), this skill, `.agents/skills/lesson-write-step/references/item-rules.md`, the `mll-literacy-scaffolding` checklist, and `authentic-writer`.

## 1. Run the scripts (read-only)

- `uv run lesson-builder check <unit> -l <stem>` (add `--no-outputs` only if nothing is built).
- `uv run lesson-builder retain <unit> -l <stem> --verify-only`.
- Forms: `uv run lesson-builder integrity <unit> --set "<set>*"`. For reviews and notes, add `--vs "<review or notes>"`.
- `uv run lesson-builder status <unit>` shows whether the outputs are stale.
- Copy every ERROR and WARN line into `audit.md` as printed. `check` already measures label positions (0.5 pt), cut-off key text, and actual-size figure widths, so don't re-measure them.
- Don't run `build`, `figs`, or `retain` without `--verify-only`.

## 2. Look at every page

- Open the page renders in `<unit>/_temp/renders/current/<stem>/`: every student, key, and practice page, and the teacher guide.
- For small text, save a script in `_temp/build/` that calls `lesson_builder.export.pdf_to_pngs(pdf, out_dir, dpi=200)`, with `out_dir` under `_temp/renders/audit/<stem>/`. Don't use `python -c`.
- Open the figure sheet `_temp/figures/<stem>_sheet.png` and compare each figure with its problem and the figure plan.

## 3. Checklist

**Lesson rules (`lesson-style`)**
- There is one core idea, and most student time goes to it. A student who gets stuck is stuck on the core idea, not on arithmetic or reading.
- The scaffolding fades:
  - the warm-up is review with low load;
  - the main problems have most known content printed;
  - the later problems and the in-class practice are more open;
  - the new step is open in every problem;
  - no frame or bank gives away the core step.
- The warm-up matches its chosen style (`warmup-design`).
- Shape: warm-up, Together, partner, QuickNotes, then 1-2 in-class practice problems. There is no closing check or extension, and the plan is 30 minutes or less.
- No repeated problems: within the lesson, the practice set, or copies of another lesson's items.
- Only the Warm-up heading prints. There are no added labels and no extra wording (hints, pep, boilerplate).

**Keys**
- Every item, part, and box has a correct answer. Check the math yourself: the checker finds missing answers, not wrong ones.
- Drawing tasks have labeled answer figures.
- The key keeps the student layout. Red appears only on the key, and key answers are bold and red.
- No answer is visible on the student page that asks for it: in a figure, a bank, the QuickNotes, or another item on that page.

**Figures**
- Labels, numbers, and marks are readable at print size and don't touch lines or each other.
- Each figure matches its problem: given lengths and angles look like their values, shapes called equal look equal, points named in the prompt appear, and primes sit against the letter.
- Student copies are black and white with no answer marks.
- Each key figure shows the full answer on the same frame as the student figure.

**Layout**
- Nothing is split across a page break, and no heading is stranded.
- There is room to write: about 0-0.3 in for a choice or one number, 0.6-1.0 in for multi-step work, 1.0-1.5 in for a proof or drawing, and more for open in-class practice.
- No page is mostly empty while another is crammed. The page count is within budget.
- Fill-in boxes are labeled and at least 0.9 in wide, with no `___`.

**Items and MLL access** (`item-rules`)
- Each MC item has one defensible answer, distractors from real errors, parallel choices, and no "all/none of the above".
- Each constructed-response item asks exactly for what's scored.
- Language load is down but the math is the same: terms kept, dual-meaning words clear, visuals labeled, contexts ordinary.
- Optional stems match the language function and don't give the claim.

**Assessments and forms**
- Every item matches a blueprint target, the targets are covered, and points add up.
- Non-target steps are scaffolded, the target step isn't, and no section headings print.
- Integrity reading pass:
  - repeated contexts or motion types across forms;
  - a figure whose shape gives the answer away;
  - difficulty drift between forms;
  - items copied from the unit's lesson or practice YAMLs;
  - reviews or notes reusing test numbers.

## 4. Fix table (recommend the fix in the source, never the DOCX)

| Defect | Fix |
|---|---|
| Figure text small, or a label warning | Raise `fig_w`, enlarge the figure, or move points apart in `figures/<stem>.py` |
| Label in the wrong place for the math | `direction=`, or `fixed=True` if the auto spot is wrong |
| Figure contradicts the problem | Change the points and add an assert |
| Answer visible on the student copy | Move that ink to `layer="answer"`, or reword the prompt |
| Too little room | Raise `work:` / `box:` |
| Item split, or heading stranded | `page_break_after` on the item before, or `page_break_before` on the section or row |
| Over budget, or a mostly empty page | Cut content (`lesson-style` §4) or move a page break; never shrink fonts |
| Key layout differs from the student copy | Make the figure height the same on both copies, or move the text into the item's answer; otherwise report a builder GAP |
| Key text cut off | Raise that item's `box:` / `work:`, or shorten the answer |
| Scaffolding doesn't fade, or the core step is framed | Name the item and what to print or open, per the known/new map |

## 5. `audit.md`

Append a dated section and keep the older content:

```markdown
## <date> audit
Inputs: <PDFs, render folder, sheet>. Script results: <N errors, M warnings>, then each line as printed.

### Must fix
- <student|key|practice> p<n>, item <k>: <what is wrong> -> <file and field to change>

### Should fix
- ...

### Looks fine
- <what was checked and passed>
```

- **Must fix:** a wrong or missing answer, a figure that contradicts the problem, unreadable text, an answer or red on the student copy, a split item, over budget, a broken teacher rule, an integrity error, or forms out of line.
- **Should fix:** tight work space, crowding, uneven pages, matters of taste.

Keep each line to one defect, with its page, item, and fix. Reply with the Must and Should counts and the Must fix lines in short.

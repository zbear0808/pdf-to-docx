---
name: lesson-write-step
description: The Write + build step (and the Fix step) for one lesson or assessment, run as an independent subagent. Turns the plan in `_temp/specs/<stem>/requirements.md` into the lesson-builder YAML and builds it. Covers fill-ins and frames, keys and answer figures, MC items, rubrics and scoring notes, the MLL language rules, the build loop (at most 4 builds, 0 errors, page-fill lines, page review), logging in `changes.md` and GAP lines, and resuming to fix audit lines. Item-level rules are in `references/item-rules.md`.
---

# Write + build step

You are a step subagent. Read `_temp/specs/<stem>/brief_write.md` first: it lists your inputs, the schema subset and examples, the files you may write, the done condition, and the reply format.

Load: `lesson-style` (what the finished document looks like), this skill and `references/item-rules.md`, `authentic-writer`, `mll-literacy-scaffolding` (Period 4), `warmup-design` (when writing the warm-up), and `.agents/skills/lesson-builder/references/api_cheatsheet.md` (fields, commands, pitfalls).

## 1. Write the YAML

- Start from the scaffolded YAML (`lesson-builder scaffold` writes it) and `templates/unit/lessons/example.yaml` or `templates/unit/assessments/example.yaml`. Write it in pieces of 150 lines or fewer, using the edit tool.
- **Lesson header:** `numbering: auto`, `headings: warmup`, `numbering_after_notes: continue`, `framing` (one question; drop it if it only restates the title), `materials`, and `targets`.
- **Sections:** warmup, together, partner, notes, apply (the in-class practice), then practice. No `title:`/`sub:` on lesson sections, and no `cyu` or `exit` (`lesson-style` §6).
- **Scaffolding:** follow the plan's known/new map exactly. Known steps print complete: a proof cell is plain text, a computed value is in the prompt or figure, a table entry is pre-filled. Open steps are labeled boxes, `{ans: ...}` cells, or work space. The fade runs one way (`lesson-style` §3).
- **Fill-ins and frames:**
  - No `___` on student pages. Every blank is a labeled box (`fill:` or `frame:`) at least 0.9 in wide.
  - A frame sits under the problem it supports and names its referent ("In Problem 2, ∠ABC landed on ☐").
  - Fill in most of the sentence, with one box per idea. A word or move bank lists phrases, never blanks.
  - Each box has exactly one expected answer, written in the key. If the teacher can't fill it at a glance, students can't either.
  - A routine fill-in takes seconds. If it takes longer than the core step, print the value instead.
- **Cross-references:** use `id` + `{ref:id}` instead of typed "Problem N". Leave `work:` at its default unless the task needs more room.
- **Figures:** use the names from the figure plan. A drawing task uses `draw:` or a figure students draw on, with a key figure on the answer layer.
- **Plan (`plan:`):**
  - Overview.
  - A **Core idea.** paragraph naming which known steps are printed so the teacher moves past them, and where to spend whole-class time.
  - The Quick look table (parts named Warm-up, Together, With a partner, QuickNotes, In-class practice, Collect).
  - One paragraph per part with assessing and advancing questions, Watch for (common errors), and MLL supports.
- **`guide_notes`:** the source decisions and the scoring notes for MLLs (item-rules §8). Older dated notes are history; don't rewrite them unless they describe something as current that no longer is.

## 2. Keys

- Every item, part, and box gets an answer, including warm-ups (sample answers), Together problems, and "circle one" items. The builder prints key answers bold and red.
- **Drawing tasks** (draw, sketch, construct, mark, shade, plot): the key shows a labeled answer figure on the `answer` layer of `figures/<stem>.py`, with its geometry asserted in code. A text description isn't enough. When drawings vary, give the steps fixed letters ("call the image of B point D").
- **Layout:** the key keeps the student layout. QuickNotes print on both copies.
- **No answer visible on its own page:** none on the student page that asks for it, whether in a figure, a bank, the QuickNotes, or another item on that page.
- **Assessments:**
  - MC: `key: C` with a one-line reason, and `distractors: {A: '<the real error>', ...}`. Select-all: `select_all: true`, with a scoring rule where a blank or "choose everything" earns 0.
  - Constructed response: a model answer, where each point comes from, acceptable alternatives, and "credit any valid method". AP Stats uses `scoring: epi`.
  - Rubrics: 3-6 specific levels, with communication on its own line.
  - Every form gets `total_points`, `target`, `type`, `demand`, and `points`.

## 3. Build loop

1. `uv run lesson-builder check <unit> -l <stem> --no-outputs` while writing. Fix every ERROR. Each WARN is either fixed or justified in `changes.md`.
2. `uv run lesson-builder build <unit> -l <stem> --no-packets`: at most 4 builds per document, 0 errors. Builds for other documents may run at the same time; if the PDF export fails, rerun once.
3. Read the page-fill lines: `OVER`, "empty while ... is full", "item N is on key pX but student pY", and "the key answer needs ... in" (the slot grew on both copies).
4. Open every handout, key, and practice page in `<unit>/_temp/renders/current/<stem>/`:
   - only the Warm-up heading prints;
   - nothing is split from its figure;
   - no text is clipped;
   - there is room to write;
   - no red appears on student copies;
   - no page is mostly empty because of a stale page break.
5. **Fit:** if the document is over budget, cut content following the `lesson-style` §4 order. Don't shrink fonts. `max_pages: 2` lets the fitter shrink work space to fit one sheet; accept it only if the boxes stay usable.

## 4. Fix round (resumed by session ID)

Read `audit.md`. Fix every Must fix and the Should fix lines that are in scope and low risk. Mark each fixed line `- [x] ...` and list the rest for the teacher. Rebuild, then run `check` and, for forms, `integrity --set "<set>*" [--vs ...]`.

## 5. Files and logs

- **Your files:** only your document's YAML and `_temp/specs/<stem>/`. A figure file belongs to the Figures step unless the brief gives it to you.
- **Never touch:** `src/`, `templates/`, `.agents/`, `unit.yaml`, other documents, or a DOCX.
- **`changes.md`:** one line per change, `item: what changed | why (rule)`.
- **Builder gaps:** if the builder can't express something, use the closest field and log `GAP: <file>:<feature>: <symptom> | workaround`. The orchestrator fixes gaps in `src/`.
- **Reply:** the format in the brief. Include what is printed and what is open, the minutes or points, the pages, the build result, and any judgment calls.

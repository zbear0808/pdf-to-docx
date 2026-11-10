---
name: handout-release-check
description: Rules and checks that a lesson handout, key, and practice set must pass before release. Covers fill-in blanks and sentence frames (labeled boxes tied to a figure), complete keys (every item, part, and box; drawn answer figures for drawing tasks), valid cross-references, page layout, and duplex packets. Use when drafting scaffolds, building keys, or before handing any student document to the teacher.
---

# Handout release check

Each rule came from a real problem a teacher hit. Apply them while writing; `lesson-builder` checks what slips through. Serves the **Write+build** step (§1-2 while writing) and the **Audit** and **Release** steps (all sections), loaded by each step's subagent per `.agents/skills/lesson-builder/references/orchestration.md`. Without subagents, run the steps in sequence with the same files.

## 1. Fill-ins and sentence frames

- No `___` on student pages. Every blank is a labeled box (`fill:` or `frame:` in the lesson YAML), ≥ 0.9 in wide.
- A frame sits directly under the problem it supports. No floating "Talk frames" box for several problems.
- Every frame names its referent: the figure, triangle, or earlier problem ("In Problem 2, ∠ABC landed on ☐").
- Fill in most of the sentence; one box per idea. A word or move bank lists phrases, never blanks.
- Each box has exactly one expected answer, written in the key. If the teacher can't fill it at a glance, students can't either.

## 2. Keys

- Every item, part, and box gets a red answer, including warm-ups (samples), Together problems, and "circle one" items.
- Draw, sketch, construct, mark, shade, plot: the key shows a **labeled answer figure**, made in the document's `figures/<stem>.py` with an `answer` layer (given black, student work red), with the geometry asserted in code. A text description is not enough.
- When student drawings vary, give the steps fixed letters ("Label it ABC, AC longest; call the image of B point D") so the key matches.
- Every practice set gets a full practice key, not just "answers to selected problems."
- The key keeps the student layout (same pages and positions) for the doc camera.
- QuickNotes print on both the student copy and the key.
- No answer is visible on the student page that asks for it: not on a figure, in a word bank, in QuickNotes, or in another item on the same page.

## 3. Cross-references

After any cut or renumber, every "Problem N" exists and supports what the sentence claims (`lesson-scope`).

## 4. Layout and printing

- Student ≤ 3 pages, practice ≤ 2, key pages = student pages, no blank pages, red only on keys.
- Student copies use black-and-white images only. Colour or under-150-dpi source images in `assets/<stem>/` get redrawn in `figures/<stem>.py`.
- Printed figure labels are ≥ 7 pt at the item's `fig_w` (`lesson-builder figs` reports it).
- Packets: one student packet and one key packet, PDF and DOCX, duplex (each lesson starts on a front page; practice follows its lesson).

## 5. Editable figure handoff (automatic)

- `lesson-builder build` copies the student and key PNGs each document uses to `output/figures/<stem>/`, writes `README.md` (item → figure name → `figures/<stem>.py:function` or asset path, helper files, the `figs` / `build` / `retain` commands), and verifies the copies against the images in the built DOCX. A figure with no source or a stale copy is an ERROR.
- The source is `figures/<stem>.py` plus any reused images in `assets/<stem>/`; the README points to them. Render caches alone do not count.
- At release: confirm each document's last build printed `figures retained: ... (N files)` with 0 errors, or run `uv run lesson-builder retain <unit> -l <stem> --verify-only`. Link the bundle and figure file in the handoff.

## Run before release

```bash
uv run lesson-builder figs <unit> -l <stem>                     # figures only: lint, printed size, contact sheet
uv run lesson-builder check <unit> -l <stem>                    # spec + rendered PDFs
uv run lesson-builder integrity <unit> --set "<set>*" --vs "<review>"   # assessment forms and reviews
uv run lesson-builder tidy <unit>                               # temp files, orphan assets, unused figures
uv run lesson-builder status <unit>                             # open Must fix lines, stale outputs, bundles
uv run lesson-builder check-pdfs "<student.pdf>" "<key.pdf>"    # any pair not built from YAML
```

`lesson-builder build <unit> -l <stem>` runs the checks, fits pages, prints the page-fill lines, and retains the figures; a full build (no `-l`) also makes the packets. Fix every ERROR in the YAML or figure file, never the DOCX, then look at the pages it lists as changed. The checker finds missing answers and MC key-letter problems, not wrong answers: read those. Record findings in `_temp/specs/<stem>/audit.md`.

---
name: handout-release-check
description: Rules and checks that a lesson handout, key, and practice set must pass before release. Covers fill-in blanks and sentence frames (labeled boxes tied to a figure), complete keys (every item, part, and box; drawn answer figures for drawing tasks), valid cross-references, page layout, and duplex packets. Use when drafting scaffolds, building keys, or before handing any student document to the teacher.
---

# Handout release check

Each rule below came from a real problem a teacher hit. Apply them while drafting; the scripts catch what slips through.

## 1. Fill-ins and sentence frames

- No `___` on student pages. Every blank is a labeled box (`Handout.fill_boxes` or `Handout.frame` in `scripts/docbuilder.py`) big enough to write in (≥ 0.9 in wide, ≥ 0.34 in tall).
- A frame sits directly under the problem it supports. No floating "Talk frames" box for several problems.
- Every frame names its referent: the figure, triangle, or earlier problem ("In Problem 2, ∠ABC landed on ☐"). If a student can't tell what "it" or "___" refers to, rewrite.
- Fill in most of the sentence; leave 1 box per idea. A frame with 4 open blanks per line is a puzzle, not a scaffold.
- A word or move bank lists phrases, not blanks ("Translate one vertex onto its match"), so nothing in it looks like it needs an answer.
- Each box has exactly one expected answer, written in the key. If the teacher can't fill it in at a glance, students can't either.

## 2. Keys

- Every numbered item, every lettered part, and every box gets a red answer. That includes warm-ups (sample responses), Together problems, and "circle one" items.
- Draw, sketch, construct, mark, shade, plot: the key shows a **labeled figure** of a correct answer (given parts black, student work red). Generate it with Python (`curriculum-visual-generator`), assert the geometry in code, and add `- **Key image**: <path>` under the item in the draft. A text description alone is not enough.
- For tasks where student drawings will differ, give the steps fixed letters ("Label it ABC with AC longest; call the image of B point D") so the key figure matches.
- Each practice set gets a full practice key (every problem and part), not just "answers to selected problems."
- The key keeps the student layout: same pages and item positions, so the teacher can work it under the doc camera.

## 3. Cross-references

- After any cut or renumber, every "Problem N" still exists and supports what the sentence claims (see `lesson-scope`).

## 4. Layout

- Student copy ≤ 3 pages, practice ≤ 2. Key page count = student page count. No blank pages.
- Labels next to boxes stay on one line (measure label widths with the real fonts, not character counts).
- Red text only on keys.

## 5. Packets for printing

Teachers print double-sided. Build both a PDF and a DOCX packet; each lesson starts on a front page, and the practice set follows its lesson directly.

```bash
uv run python .agents/skills/handout-release-check/scripts/make_packet.py --out "<dir>/Unit N Student Packet.pdf" \
  --group "L1 Student Handout.pdf" "L1 Practice Problems.pdf" --group "L2 ..." "L2 ..."
pwsh -File .agents/skills/handout-release-check/scripts/make_packet_docx.ps1 -Out "<dir>/Unit N Student Packet.docx" `
  "L1 Student Handout.docx" "L1 Practice Problems.docx" "|" "L2 ..." "L2 ..."
```

Make a key packet the same way (lesson key + practice key).

## Run before release

```bash
S=.agents/skills/handout-release-check/scripts/check_lesson.py
uv run python $S draft --draft <draft.md> --minutes 40
uv run python $S outputs --student "<X Student Handout.pdf>" --key "<X Lesson Key.pdf>"
uv run python $S outputs --student "<X Practice Problems.pdf>" --key "<X Practice Key.pdf>" --max-pages 2
```

Fix every ERROR. Then look at each key page yourself: the script finds missing red text, not wrong answers.

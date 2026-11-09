---
name: handout-release-check
description: Rules and checks that a lesson handout, key, and practice set must pass before release. Covers fill-in blanks and sentence frames (labeled boxes tied to a figure), complete keys (every item, part, and box; drawn answer figures for drawing tasks), valid cross-references, page layout, and duplex packets. Use when drafting scaffolds, building keys, or before handing any student document to the teacher.
---

# Handout release check

Each rule came from a real problem a teacher hit. Apply them while writing; `lesson-builder` checks what slips through.

## 1. Fill-ins and sentence frames

- No `___` on student pages. Every blank is a labeled box (`fill:` or `frame:` in the lesson YAML), ≥ 0.9 in wide.
- A frame sits directly under the problem it supports. No floating "Talk frames" box for several problems.
- Every frame names its referent: the figure, triangle, or earlier problem ("In Problem 2, ∠ABC landed on ☐").
- Fill in most of the sentence; one box per idea. A word or move bank lists phrases, never blanks.
- Each box has exactly one expected answer, written in the key. If the teacher can't fill it at a glance, students can't either.

## 2. Keys

- Every item, part, and box gets a red answer, including warm-ups (samples), Together problems, and "circle one" items.
- Draw, sketch, construct, mark, shade, plot: the key shows a **labeled answer figure**, made in `figures.py` with an `answer` layer (given black, student work red), with the geometry asserted in code. A text description is not enough.
- When student drawings vary, give the steps fixed letters ("Label it ABC, AC longest; call the image of B point D") so the key matches.
- Every practice set gets a full practice key, not just "answers to selected problems."
- The key keeps the student layout (same pages and positions) for the doc camera.

## 3. Cross-references

After any cut or renumber, every "Problem N" exists and supports what the sentence claims (`lesson-scope`).

## 4. Layout and printing

- Student ≤ 3 pages, practice ≤ 2, key pages = student pages, no blank pages, red only on keys.
- Packets: one student packet and one key packet, PDF and DOCX, duplex (each lesson starts on a front page; practice follows its lesson).

## Run before release

```bash
uv run lesson-builder check <unit_dir>                          # spec + rendered PDFs
uv run lesson-builder check-pdfs "<student.pdf>" "<key.pdf>"    # any pair not built from YAML
```

`lesson-builder build` runs both, fits pages, and builds the packets. Fix every ERROR, then look at the pages it lists as changed. The checker finds missing answers, not wrong ones.

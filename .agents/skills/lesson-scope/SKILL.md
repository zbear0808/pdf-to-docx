---
name: lesson-scope
description: Fits a lesson handout to a 40-minute period. Budgets minutes per item, cuts repeated problems from older drafts, and keeps cross-references valid after cuts. Use before drafting or revising any lesson handout, worksheet, or lesson plan, and whenever a lesson "runs long."
---

# Lesson scope

A lesson is **40 minutes**, including the warm-up and exit ticket. Write less. Students who finish early get one extension question, not more pages.

## Budget (Math Medic format)

| Part | Min | Items |
|---|---|---|
| Warm-up | 4 | 1 item, or 2-3 quick ones |
| Together | 6 | 1-2 problems, teacher works them |
| With a partner | 15 | 2-4 problems |
| QuickNotes | 4 | printed, read together |
| Check your understanding + exit ticket | 8 | 2 items + 1 exit ticket |
| Collect, assign practice | 3 | |

Whole-class talk ≤ 14 min. The plan's timing table ends at 40 or less (`check_lesson.py draft` enforces this).

## Per-item minutes (estimate before writing)

| Item type | Min |
|---|---|
| True/false, one fill-in, read-a-statement | 1 |
| Short answer with a figure | 2-3 |
| Patty-paper move with written moves | 4 |
| Fill-in explanation (3-4 boxes) | 3 |
| Construction or drawing task | 6-8 |
| Open "explain why" | 4 |

Put the minutes in the blueprint table in `requirements.md`. If the total is over budget, cut before drafting.

## What to cut first (rewrite mode)

1. A second item that shows the same idea with new letters (keep the clearer one).
2. Extra parts in a multi-part item that repeat the first part.
3. Third and fourth warm-up items.
4. CYU items that the exit ticket already checks.
5. Anything the practice set (homework) already covers.

Keep: the one "doing mathematics" task, the item that sets up the QuickNotes, and the exit ticket. Never cut the item another item depends on unless you cut both.

## After any cut or renumber

- Search the handout, key, QuickNotes, and plan for "Problem N" and fix every reference.
- A reference must point to work that actually supports the task. "Use your claim from Problem 4" is only valid if Problem 4's claim is the reason needed. Otherwise name the fact directly.
- Log each cut in `changes.md`: item, reason, minutes saved.

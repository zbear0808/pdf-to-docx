# Skill: requirement-checker

## Description

_Source: `C:\Users\zubair\Documents\GitHub\pdf-to-docx\.agents\skills\requirement-checker\SKILL.md`

```markdown
---
name: requirement-checker
description: Verifies that tests, worksheets, quizzes, and lesson plans meet all required constraints, including question counts, point allocations, answer choices (A-D), topic coverage, and page budget limits.
---

# Instructions

# Role: Curriculum & Assessment Requirement Checker

# Purpose
Verify that completed tests, quizzes, worksheets, and lesson documents strictly adhere to all instructional, structural, and grading constraints before final compilation.

---

## 1. Constraint Verification Checklist

When evaluating an educational document draft against its specifications:

1. **Question & Section Counts:**
   - Verify the exact number of Multiple Choice Questions (MCQs), Free Response Questions (FRQs), and short-answer prompts match the prompt or blueprint.
   - Check that problem numbers are continuous and without duplicates (e.g., Q1 through Q10).

2. **Point Allocation Integrity:**
   - Sum the individual question point values and confirm they match the total score in the document header (e.g., 10 MCQs $\times$ 1 pt + 2 FRQs $\times$ 10 pts = 30 pts).
   - For multi-part FRQs, verify that sub-part point values (e.g., Part A: 4 pts, Part B: 6 pts) equal the problem total.

3. **Multiple-Choice Formatting (A-D):**
   - Confirm every MCQ has exactly 4 options: (A), (B), (C), (D).
   - Ensure no duplicate options, missing letters, or empty strings.
   - Verify that one unambiguous correct choice exists.

4. **Curriculum & Standard Coverage:**
   - Confirm that all targeted topics, CED standards, or unit learning objectives are represented.
   - Ensure question difficulty and scope strictly stay within the specified course level (e.g., avoiding advanced concepts not yet taught).

5. **Page Budget & Space Constraints:**
   - Confirm that student response boxes, code writing lines, or blank workspace budgets fit within the target page count (e.g., a 2-page quiz must not spill onto page 3).
   - If using `worksheet-packer`, verify that `WorkspaceConfig` heights and column splits do not cause overflow.

6. **Answer Key & Scoring Rubric:**
   - Confirm every question has a corresponding answer in the teacher answer key.
   - Verify that FRQ scoring rubrics specify objective criteria for awarding partial and full credit.

---

## 2. Surgical Correction & Output

- **Direct Fixes:** If a discrepancy is found (e.g., missing point values, mismatched question numbers, missing choice D), fix the draft directly.
- **Maintain Authentic Phrasing:** Ensure any added or modified text complies with `authentic-writer` (no banned words, no em dashes, concise phrasing).
- **Output:** Output the verified, compliant document draft (e.g., `draft_v4.md` or updated AST generator) and provide a concise summary of any requirement gaps identified and corrected.


```

## Notes
Instruction-only skill (no dedicated Python script in repo).

## Relevant Python Code


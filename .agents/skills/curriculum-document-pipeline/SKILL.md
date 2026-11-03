---
name: curriculum-document-pipeline
description: Autonomous pipeline that extracts course and quiz content, drafts authentic test/worksheet items, prunes verbosity with critical checking, verifies requirements and point values, and packs final Word and LaTeX documents using worksheet-packer.
---

# Curriculum & Assessment Document Pipeline

This skill provides an autonomous, multi-phase pipeline for building natural, human-sounding tests, quizzes, retakes, worksheets, and lesson handouts without AI writing tropes.

---

## Workspace Hygiene Standard

All pipeline tasks MUST maintain strict folder hygiene:
- `output/`: Final deliverables only (`.docx`, `.pdf`, `.tex`).
- `_temp/assets/`: Harvested and cropped diagrams, figures, and plots.
- `_temp/renders/`: Rendered page previews (`orig_p*.png`, `docx_p*.png`).
- `_temp/specs/`: Intermediate markdown drafts, question specs, and packing plans.
- `_temp/build/`: Scratch compilation scripts and log files.

---

## Autonomous Pipeline Execution Sequence

Execute each step sequentially, passing output artifacts to the next step:

### Step 0: Source Content & Quiz Extraction (`course-content-extractor`)
- Delegate to `course-content-extractor` (`.agents/skills/course-content-extractor/SKILL.md`).
- Scan local course files, past exams, CodeHS/Math Medic units, and question banks.
- Harvest problem stems, answer choices, code snippets, diagrams, and rubrics into `_temp/specs/extracted_content.md`.
- Crop associated diagrams to `_temp/assets/`.

### Step 1: Initial Authentic Draft (`authentic-writer`)
- Delegate to a subagent with `authentic-writer` (`.agents/skills/authentic-writer/SKILL.md`) and `classroom-context` (`.agents/skills/classroom-context/SKILL.md`).
- Draft the worksheet, quiz, or retake items based on `extracted_content.md`.
- Ensure question stems are direct and concise without AI story-telling padding.
- Ground word problems in authentic Franklin High School classroom contexts (Geometry scaffolds vs AP Stats/CS rigor).
- Save draft to `_temp/specs/draft_v1.md`.

### Step 2: Critical De-fluffing & Stem Pruning (`critical-checker`)
- Delegate to a subagent with `critical-checker` (`.agents/skills/critical-checker/SKILL.md`).
- Prune wordiness, redundant explanations, and conversational filler from question stems and directions.
- Strip all em dashes ("—" or "--"), replacing them with commas, parentheses, or separate sentences.
- Preserve all problem numbering, mathematical data, code logic, and answer options.
- Save output to `_temp/specs/draft_v2.md`.

### Step 3: Requirement & Rubric Verification (`requirement-checker`)
- Delegate to a subagent with `requirement-checker` (`.agents/skills/requirement-checker/SKILL.md`).
- Verify point totals equal the header sum.
- Confirm every multiple choice question has complete (A), (B), (C), (D) options.
- Ensure all targeted course standards/topics are addressed.
- Verify workspace heights and layout budgets match page constraints.
- Fix any discrepancies directly and save output to `_temp/specs/draft_v3.md`.

### Step 4: Final Authenticity & Hygiene Pass (`authentic-writer`)
- Delegate to a subagent with `authentic-writer` (`.agents/skills/authentic-writer/SKILL.md`).
- Perform a final scan for banned AI vocabulary (*delve*, *multifaceted*, *crucial*, *pivotal*, *testament*).
- Confirm all section headings use sentence case.
- Confirm no formulaic preambles or preachy conclusions exist.
- Save finalized content to `_temp/specs/final_content.md`.

### Step 5: Layout Packing & Rendering (`worksheet-packer` / `docx-layout-refinement`)
- Convert `_temp/specs/final_content.md` into the Worksheet AST or packing script.
- Execute `worksheet-packer` (`.agents/skills/worksheet-packer/SKILL.md`) or run the layout engine to pack questions with balanced multi-column splits and side-by-side diagram placement.
- Output final deliverables directly to `output/` (e.g., `output/Assessment.docx`, `output/Assessment.pdf`).


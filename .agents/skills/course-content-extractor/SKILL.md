---
name: course-content-extractor
description: Locates, extracts, and compiles relevant quiz questions, exam problems, lesson notes, code snippets, diagrams, and curriculum standards from local course files, past assessments, and question banks to seed worksheets, retakes, and lesson plans.
---

# Instructions

# Role: Course Content & Quiz Extractor

# Purpose
Locate, extract, and compile source materials (past quizzes, unit assessments, homework problems, CodeHS exercises, lesson notes, diagrams, and answer keys) needed to construct authentic worksheets, exams, retakes, or lesson plans without hallucination.

Serves the **Plan** step: the Plan subagent loads this skill (see `.agents/skills/lesson-builder/references/orchestration.md`). Without subagents, run the steps in sequence with the same files.

---

## 1. Subject Content Hubs & Search Directories

When searching for curriculum materials, problem banks, or past assessments, consult these specific subject repositories:

### A. High School Geometry (Franklin HS / SPS Curriculum)
- **Primary Root:** `C:\Users\zubair\OneDrive - Seattle School District No. 1\Gatti, Julianne O's files - 00 Geometry`
- **Unit Subfolders:** e.g., `Unit 1\`, `Beginning of the Year\`, and subsequent unit directories.
- **Key Subdirectories & Assets:**
  - `Assessments\`: Contains official district assessments, mid-unit exams, and progress checks in `.docx` and `.pdf`:
    - Parallel forms for retakes (e.g., `Mid-Unit Assessment Form A.docx` and `Form B.docx` alongside their `- Answer Key.pdf` files).
    - Formative progress checks (e.g., `Lesson 1.1 - 1.2 Progress Check.docx`, `Lessons 1.10 - 1.13+ Progress Check_.docx`).
  - `Unit 1 Student Notes and Practice Problems\`: Contains lesson handouts, student guided practice, and homework problem sets.
- **Best For:** Geometry problem stems, parallel Form A / Form B retakes, progress check items, and geometric diagrams (congruence marks, angle arcs, coordinate grids).

### B. AP Statistics: Lessons & Concept Handouts (Math Medic)
- **Primary Root:** `C:\Users\zubair\Documents\GitHub\mathmedic-extractor\export\mathmedic\ap-statistics`
- **Unit Subfolders:** Organized from `Unit_01_Analyzing_Data` through `Unit_10_Two-Variable_Data`.
- **Key Subdirectories per Unit:**
  - `lessons/`: Raw student lesson worksheets and activity-based learning tasks (`.docx` / `.pdf`).
  - `lesson_keys/`: Complete teacher answer keys with fully worked solutions.
  - `lessons_with_quicknotes/` & `quicknotes_images/`: QuickNotes summaries, formulas, and margin takeaways.
  - `additional_media/`: Extracted figures, dot plots, boxplots, histograms, and scatterplots.
- **Best For:** Activity-based learning contexts, student-friendly lesson explanations, QuickNotes formula summaries, and data displays.

### C. AP Statistics: Official Released Exams & Question Banks (Stats Archive)
- **Primary Root:** `C:\Users\zubair\Documents\GitHub\stats-archive`
- **Key Subdirectories & Assets:**
  - `02_Free_Response_Questions_by_Year/`: Official College Board FRQs organized by year from `1997` through `2024`.
    - Each year directory contains:
      - `[Year]_AP_Statistics_FRQ.docx` & `.pdf`: Official exam questions.
      - `[Year]_AP_Statistics_Scoring_Guidelines.docx` & `.pdf`: Official scoring rubrics with Essentially Correct, Partially Correct, Incorrect (E / P / I) criteria.
      - `[Year]_AP_Statistics_Chief_Reader_Report.pdf`: Insights into common student errors, traps, and misconceptions.
      - `Sample_Responses/`: Real student sample answers showing full, partial, and zero credit work.
  - `01_Full_Official_Exams/`: Full official released practice exams with multiple choice questions (MCQs) and keys (e.g., `1997_AP_Statistics_Released_Exam.pdf`, `2012_AP_Statistics_Public_Practice_Exam.pdf`, `STATS_2002_MULTIPLE_CHOICE.pdf`).
  - `03_Course_Materials_and_Formula_Sheets/`: Official formula sheets, tables, and curriculum framework documents.
- **Best For:** Official College Board FRQ problem stems, formal scoring rubrics, distractor analysis for MCQs, and Chief Reader error analysis.

### D. AP Computer Science (CodeHS / AP CS A)
- **Primary Root:** Local repository folders (e.g., `codehs_unit1_retake`, `lesson_1_21_streamlined`, `unit_1_review_aligned`, etc.).
- **Key Assets:**
  - `.tex`, `.docx`, and `.py` generators (e.g., `generate_assessment.py`).
  - Java class structures, method implementations, tracing problems, runner simulations, and unit retake templates.
- **Best For:** Java syntax questions, code tracing tables, object-oriented design scenarios, and Unit 1–10 CodeHS curricula.

---

## 2. File Reading & Asset Copying Standards

Everything lands in the unit folder `units/<course>/<unit-slug>/` (create it with `uv run lesson-builder new-unit`). `<stem>` is the lesson id or assessment file stem.

- **PDFs & Word Documents:** Copy the sources you need into the unit's `input/`, then run `uv run lesson-builder ingest <unit>/input -o <unit>/_temp/ingest`. Read the `.md` files (math kept); images are in `_media/` and page renders in `_pages/`. Open page PNGs only to see figures.
- **Images/Diagrams:** Copy or crop a reused source image into the unit's `assets/<stem>/`. It must be black and white and ≥ 150 dpi at print size; otherwise redraw it in `figures/<stem>.py` (`curriculum-visual-generator`). Never point the YAML at an external path, so the unit stays self-contained.

---

## 3. Extraction Scope & Provenance

When compiling extracted content, write the package to the unit's `_temp/specs/<stem>/extracted_content.md` (the file `assessment-builder` and the Plan step read):

1. **Problem Stems & Code / Math Notation:**
   - Preserve exact code syntax, indentation, and variable names.
   - Preserve mathematical formulas, notation, and specific numerical values.
2. **Multiple-Choice Options & Distractors:**
   - Extract all choices (A, B, C, D) alongside the verified correct answer.
   - Note the pedagogical reason for common distractor choices (e.g., off-by-one error, integer division truncation, confusing median with mean).
3. **Diagrams & Attached Assets:**
   - Copy or crop diagram assets into `assets/<stem>/` and record each local path, plus the source file and page. Mark any image that needs a redraw (colour, low resolution).
4. **Rubrics & Scoring Criteria:**
   - For FRQs, record the official E/P/I scoring guidelines or point breakdown.

---

## 4. Provenance & Metadata Header

Always record the provenance of extracted course material at the top of the compilation:

```markdown
# Extracted Course Content: <Course & Unit / Topic>

- **Source Document Title:** <Title or Exam Name>
- **Local Source Path:** `<full_path_to_source_file.docx / .pdf / .tex>`
- **Source Repository:** <Geometry OneDrive / Math Medic / Stats Archive / CodeHS>
- **Target Unit / Standard:** <e.g., Geometry Unit 1: Rigid Transformations / AP Stats CED Unit 1 / CodeHS Unit 1>
- **Target Deliverable:** <e.g., Unit 1 Retake Assessment, Lesson 1.4 Practice Worksheet>

### Problem 1: <Topic / Title>
- **Source Question:** 2023 AP Statistics FRQ #1 (or SPS Geo.1 Mid-Unit Assessment Form A, Q3)
- **Stem:**
  <Problem stem text or code listing>
- **Choices (if MCQ):**
  - (A) ...
  - (B) ... (Correct)
  - (C) ...
  - (D) ...
- **Scoring Rubric (if FRQ):**
  - Part (a): [Essentially Correct if ...]
- **Associated Diagram:** `assets/<stem>/fig_p1_stem.png` (from `<source file>`, page N)
```

---

## 5. Retake & Variant Problem Generation Guidelines (Exam Integrity)

> [!IMPORTANT]
> **STRICT EXAM INTEGRITY RULE: NO VERBATIM COPYING FROM ACTUAL EXAMS:**
> When source documents include an **actual exam** given to students (e.g. Unit Tests, Mid-Unit Exams, Semester Finals):
> - **Never copy questions exactly or verbatim** into review packets, practice tests, or retakes.
> - **Mirror the Cognitive Skill**: Keep the targeted standard, cognitive demand level, and question archetype identical.
> - **Vary Parameters & Scenarios**: Substantially change numerical constants, coordinate values, geometric orientations, variable names, and contextual story problems so students cannot simply memorize answers.
> - **Form A / Form B Consistency**: In Geometry, study both Form A and Form B in the `Assessments` folder to learn the intended variation scheme (e.g., swapping a translation vector or rotation angle) before generating parallel items. Record the scheme so the Plan step can build the version table in `_temp/specs/<stem>/requirements.md` (`assessment-builder` owns that table).
> - **Preserve Verified Keys**: Every adapted problem must include a verified step-by-step solution.

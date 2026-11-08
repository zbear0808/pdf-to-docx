# Skill: course-content-extractor

## Description

_Source: `C:\Users\zubair\Documents\GitHub\pdf-to-docx\.agents\skills\course-content-extractor\SKILL.md`

```markdown
---
name: course-content-extractor
description: Locates, extracts, and compiles relevant quiz questions, exam problems, lesson notes, code snippets, diagrams, and curriculum standards from local course files, past assessments, and question banks to seed worksheets, retakes, and lesson plans.
---

# Instructions

# Role: Course Content & Quiz Extractor

# Purpose
Locate, extract, and compile source materials (past quizzes, unit assessments, homework problems, CodeHS exercises, lesson notes, diagrams, and answer keys) needed to construct authentic worksheets, exams, retakes, or lesson plans without hallucination.

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

- **PDFs & Word Documents:** Read `.docx` files or read source `.pdf` files directly using native reading tools.
- **Workspace Hygiene for Images/Diagrams:** When extracting diagrams, charts, or images from these external folders, **ALWAYS copy or crop the image directly into the local `_temp/assets/` directory**. Never leave external paths hardcoded in local compiler scripts, so the document workspace remains completely self-contained.

---

## 3. Extraction Scope & Provenance

When compiling extracted content, write the package to `_temp/specs/extracted_course_content.md`:

1. **Problem Stems & Code / Math Notation:**
   - Preserve exact code syntax, indentation, and variable names.
   - Preserve mathematical formulas, notation, and specific numerical values.
2. **Multiple-Choice Options & Distractors:**
   - Extract all choices (A, B, C, D) alongside the verified correct answer.
   - Note the pedagogical reason for common distractor choices (e.g., off-by-one error, integer division truncation, confusing median with mean).
3. **Diagrams & Attached Assets:**
   - Copy or crop diagram assets directly into `_temp/assets/` and record their exact local paths.
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
- **Associated Diagram:** `_temp/assets/fig_p1_stem.png`
```

---

## 5. Retake & Variant Problem Generation Guidelines (Exam Integrity)

> [!IMPORTANT]
> **STRICT EXAM INTEGRITY RULE — NO VERBATIM COPYING FROM ACTUAL EXAMS:**
> When source documents include an **actual exam** given to students (e.g. Unit Tests, Mid-Unit Exams, Semester Finals):
> - **Never copy questions exactly or verbatim** into review packets, practice tests, or retakes.
> - **Mirror the Cognitive Skill**: Keep the targeted standard, cognitive demand level, and question archetype identical.
> - **Vary Parameters & Scenarios**: Substantially change numerical constants, coordinate values, geometric orientations, variable names, and contextual story problems so students cannot simply memorize answers.
> - **Form A / Form B Consistency**: In Geometry, study both Form A and Form B in the `Assessments` folder to learn the intended variation scheme (e.g., swapping a translation vector or rotation angle) before generating parallel items.
> - **Preserve Verified Keys**: Every adapted problem must include a verified step-by-step solution.

```

## Notes
Instruction skill; uses inspection/render/crop/extraction utilities to gather source material.

## Relevant Python Code


### .agents\skills\pdf-to-docx\scripts\inspect_pdf.py

_File not found in repo._

### .agents\skills\pdf-to-docx\scripts\render_pages.py

_File not found in repo._

### .agents\skills\pdf-to-docx\scripts\crop_asset.py

_File not found in repo._

### src\worksheet_packer\docx_extractor.py

```python
"""DOCX Extraction and Headless Rendering Utilities.

Enables existing Word (.docx) documents to be ingested into the Worksheet Packer pipeline:
1. Extracts embedded media assets directly from word/media/ within the DOCX zip archive.
2. Renders DOCX pages to high-resolution PNG images via LibreOffice or Windows Word COM
   so they can be analyzed by Gemini multimodal vision.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Dict, List, Optional
import pymupdf as fitz


def extract_docx_media(docx_path: str | Path, output_dir: str | Path) -> Dict[str, Path]:
    """Extracts all embedded images from the word/media/ folder of a .docx file.

    Returns:
        Dictionary mapping internal media filename (e.g. 'image1.png') to extracted Path.
    """
    docx_file = Path(docx_path).resolve()
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    extracted_map = {}
    if not zipfile.is_zipfile(docx_file):
        return extracted_map

    with zipfile.ZipFile(docx_file, "r") as z:
        for name in z.namelist():
            if name.startswith("word/media/"):
                filename = Path(name).name
                target_path = out_dir / filename
                with z.open(name) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)
                extracted_map[filename] = target_path

    return extracted_map


def convert_docx_to_pdf(docx_path: str | Path, output_pdf_path: Optional[str | Path] = None) -> Path:
    """Converts a DOCX document to PDF using headless LibreOffice or Windows Word COM.

    Raises:
        RuntimeError: If neither LibreOffice nor Word COM is available or conversion fails.
    """
    docx_file = Path(docx_path).resolve()
    if not docx_file.exists():
        raise FileNotFoundError(f"DOCX file not found: {docx_file}")

    if output_pdf_path is None:
        out_pdf = docx_file.with_suffix(".pdf")
    else:
        out_pdf = Path(output_pdf_path).resolve()

    out_pdf.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = out_pdf.parent / f".temp_pdf_{docx_file.stem}"
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Try LibreOffice CLI
    soffice_cmd = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice_cmd:
        candidates = [
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        ]
        for c in candidates:
            if c.exists():
                soffice_cmd = str(c)
                break

    if soffice_cmd:
        try:
            subprocess.run(
                [soffice_cmd, "--headless", "--convert-to", "pdf", str(docx_file), "--outdir", str(temp_dir)],
                check=True,
                capture_output=True,
                timeout=60,
            )
            candidate_pdf = temp_dir / f"{docx_file.stem}.pdf"
            if candidate_pdf.exists():
                shutil.move(str(candidate_pdf), str(out_pdf))
                shutil.rmtree(temp_dir, ignore_errors=True)
                return out_pdf
        except Exception:
            pass

    # 2. Try Windows MS Word COM
    if os.name == "nt":
        import time
        for attempt in range(3):
            try:
                import win32com.client  # type: ignore
                # Use DispatchEx for an isolated instance
                word = win32com.client.DispatchEx("Word.Application")
                word.Visible = False
                word.DisplayAlerts = 0  # wdAlertsNone
                try:
                    # Open read-only and unconfirmed
                    doc = word.Documents.Open(str(docx_file), ReadOnly=True, ConfirmConversions=False)
                    # 17 = wdFormatPDF
                    doc.SaveAs(str(out_pdf), FileFormat=17)
                    doc.Close(SaveChanges=False)
                    if out_pdf.exists() and out_pdf.stat().st_size > 0:
                        shutil.rmtree(temp_dir, ignore_errors=True)
                        return out_pdf
                finally:
                    word.Quit()
            except Exception as e:
                time.sleep(1.0)
                if attempt == 2:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    raise RuntimeError(f"Word COM conversion failed: {e}")

    shutil.rmtree(temp_dir, ignore_errors=True)
    raise RuntimeError(
        "Could not convert DOCX to PDF: neither LibreOffice CLI nor Windows MS Word COM automation succeeded."
    )


def render_docx_pages(
    docx_path: str | Path,
    output_dir: str | Path,
    dpi: int = 200,
) -> List[Path]:
    """Renders all pages of a Word document into high-resolution PNG images.

    Converts DOCX -> PDF, then renders each page using PyMuPDF.

    Returns:
        List of PNG paths for each page (1-indexed).
    """
    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    temp_pdf = out_dir / f"{Path(docx_path).stem}_rendered.pdf"
    convert_docx_to_pdf(docx_path, temp_pdf)

    rendered_pages = []
    doc = fitz.open(str(temp_pdf))
    try:
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            pix = page.get_pixmap(matrix=mat, alpha=False)
            page_png = out_dir / f"page_{page_idx + 1}.png"
            pix.save(str(page_png))
            rendered_pages.append(page_png)
    finally:
        doc.close()

    return rendered_pages


```

# Cleanup Plan 05: Document Workspaces Hygiene & Script Deduplication

This document details the audit of scripts across historical document task workspaces ([`unit1_test_repack/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/unit1_test_repack), [`unit_1_review_aligned/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/unit_1_review_aligned), [`lesson_1_21_streamlined/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/lesson_1_21_streamlined), and [`codehs_unit1_retake/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/codehs_unit1_retake)), resolving superseded iteration scripts and bringing all folders into compliance with the repository's workspace hygiene guidelines.

---

## 1. The Workspace Hygiene Standard

Both repository-level guidelines ([`AGENTS.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/AGENTS.md) and [`GEMINI.md`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/GEMINI.md)) and global user instructions mandate the following directory layout for any document conversion or repacking task:

```text
<document_workspace>/
├── input/                  # (Optional) Original source documents (.pdf, .docx)
├── output/                 # Final deliverables ONLY (.docx, .pdf, .tex, final reports)
└── _temp/                  # ALL transient, intermediate, and generated working files
    ├── assets/             # Extracted/cropped images, figures, diagrams, embedded media
    ├── renders/            # Page preview images (orig_p*.png, docx_p*.png, latex_p*.png)
    ├── specs/              # Intermediate JSON ASTs, extraction specs, packing plans
    └── build/              # Compiler logs, scratch scripts, figure generators (.py, .log)
```

**Cardinal Rule:** Never dump loose scripts, page renders, or intermediate ASTs into the workspace root. All task scripts belong in `_temp/build/`.

---

## 2. Workspace-by-Workspace Audit

### 2.1 Workspace: `unit1_test_repack/`
- **Hygiene Compliance:** **PASS** (all scripts correctly reside in `_temp/build/`).
- **Iteration Redundancy:** **FAIL** (12 scripts left over from iterative development).

#### Inventory & Status in `unit1_test_repack/_temp/build/`:
| Script | Size | Assessment |
| :--- | :---: | :--- |
| `run_repack_v1.py` | 4.5 KB | **Superseded** by `v2` and `build_final.py`. |
| `run_repack_v2.py` | 3.1 KB | **Superseded** by `build_final.py`. |
| `build_repack.py` | 2.3 KB | **Superseded** by `build_final.py`. |
| `step1_clean.py` | 2.6 KB | **Superseded** intermediate step. |
| `test_repack.py` | 0.6 KB | **Superseded** intermediate test. |
| `build_final.py` | 3.8 KB | **ACTIVE DRIVER** — Final render script that produced deliverables. |
| `check_anchors.py` | 1.0 KB | Diagnostic script (inspected image anchor properties). |
| `check_breaks.py` | 0.3 KB | Diagnostic script (inspected page breaks). |
| `check_table6.py` | 0.5 KB | Diagnostic script (inspected table 6 layout). |
| `dump_full_spec.py` | 1.7 KB | Diagnostic script (dumped spec AST). |
| `find_shape_properties.py` | 1.1 KB | Diagnostic script (found shape properties in Word). |
| `inspect_images.py` | 0.8 KB | Diagnostic script (inspected extracted image sizes). |

**Recommended Cleanup:** Delete the superseded generation files (`run_repack_v1.py`, `run_repack_v2.py`, `build_repack.py`, `step1_clean.py`, `test_repack.py`). Retain `build_final.py` as the reproducible task driver.

---

### 2.2 Workspace: `unit_1_review_aligned/`
- **Hygiene Compliance:** **FAIL** (7 loose Python scripts sitting in workspace root).
- **Iteration Redundancy:** **FAIL** (superseded figure generator script left in `_temp/build/`).

#### Root Directory Clutter:
The following 7 scripts sit directly in [`unit_1_review_aligned/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/unit_1_review_aligned) instead of `_temp/build/`:
1. `build_aligned_review.py` (10.5 KB)
2. `compile_and_render_all.py` (3.5 KB)
3. `compile_review_docx_2page.py` (23.8 KB)
4. `compile_review_latex_2page.py` (12.2 KB)
5. `generate_fresh_figures.py` (16.6 KB)
6. `inspect_plan.py` (0.6 KB)
7. `map_images.py` (1.2 KB)

#### Internal Duplicate in `_temp/build/`:
- `_temp/build/generate_new_figures.py` (5.3 KB, written at 8:00 AM) was superseded by root `generate_fresh_figures.py` (16.6 KB, written at 1:11 PM).

**Recommended Cleanup:**
1. Delete `unit_1_review_aligned/_temp/build/generate_new_figures.py`.
2. Move all 7 root `.py` scripts into `unit_1_review_aligned/_temp/build/`.

---

### 2.3 Workspace: `lesson_1_21_streamlined/`
- **Hygiene Compliance:** **FAIL** (5 loose Python scripts sitting in workspace root).
- **Iteration Redundancy:** **FAIL** (superseded multi-page compiler left behind).

#### Root Directory Clutter:
The following 5 scripts sit directly in [`lesson_1_21_streamlined/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/lesson_1_21_streamlined):
1. `clean_encoding.py` (0.6 KB)
2. `compile_latex.py` (6.1 KB, written at 10:23 AM)
3. `compile_latex_1page.py` (5.1 KB, written at 11:37 AM)
4. `compile_docx_1page.py` (11.4 KB, written at 11:37 AM)
5. `build_streamlined.py` (7.5 KB, written at 11:37 AM)

#### Version Supersession:
- `compile_latex.py` was the initial unconstrained compiler that produced an unwanted 2-page spill.
- It was superseded by `compile_latex_1page.py` which tightly packed the lesson into exactly 1 page.

**Recommended Cleanup:**
1. Delete superseded `compile_latex.py`.
2. Move `build_streamlined.py`, `compile_docx_1page.py`, `compile_latex_1page.py`, and `clean_encoding.py` into `lesson_1_21_streamlined/_temp/build/`.

---

### 2.4 Workspace: `codehs_unit1_retake/`
- **Hygiene Compliance:** **PASS** (exhibits gold-standard compliance).
- It houses its single task generator at [`codehs_unit1_retake/_temp/build/generate_assessment.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/codehs_unit1_retake/_temp/build/generate_assessment.py).
- No loose scripts in root, deliverables isolated in `output/`, and renders in `_temp/renders/`.

---

## 3. Step-by-Step Remediation Plan

### Step 1: Clean Up `unit1_test_repack/`
```powershell
$base = "unit1_test_repack/_temp/build"
Remove-Item "$base/run_repack_v1.py" -Force
Remove-Item "$base/run_repack_v2.py" -Force
Remove-Item "$base/build_repack.py" -Force
Remove-Item "$base/step1_clean.py" -Force
Remove-Item "$base/test_repack.py" -Force
```

### Step 2: Clean Up & Restructure `unit_1_review_aligned/`
```powershell
$target = "unit_1_review_aligned/_temp/build"
# 1. Delete superseded generator
Remove-Item "$target/generate_new_figures.py" -Force

# 2. Move loose root scripts into _temp/build
Get-ChildItem -Path unit_1_review_aligned -Filter *.py -File | Move-Item -Destination $target -Force
```

### Step 3: Clean Up & Restructure `lesson_1_21_streamlined/`
```powershell
$target = "lesson_1_21_streamlined/_temp/build"
New-Item -ItemType Directory -Path $target -Force

# 1. Delete superseded multi-page compiler
Remove-Item "lesson_1_21_streamlined/compile_latex.py" -Force

# 2. Move remaining root scripts into _temp/build
Get-ChildItem -Path lesson_1_21_streamlined -Filter *.py -File | Move-Item -Destination $target -Force
```

---

## 4. Verification Checklist

- [ ] Workspace roots for `unit_1_review_aligned/` and `lesson_1_21_streamlined/` contain zero `.py` scripts.
- [ ] All working scripts reside in their respective `_temp/build/` directories.
- [ ] Obsolete iterative files (`v1`, `v2`, multi-page spill scripts) are deleted.
- [ ] Workspace deliverables in `output/` remain intact and unimpacted.

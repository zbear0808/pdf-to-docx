# Cleanup Plan 04: Scratchpad, Batch Runner & Test Suite Sanitization

This document details the cleanup of ephemeral scratch scripts, machine-specific external batch runners, and non-test clutter within the [`tests/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests) directory to establish a clean, standard pytest test suite.

---

## 1. Background & Scope

During early development and iterative troubleshooting, multiple ad-hoc scripts and temporary test files were created across three locations:
1. Root-level external batch automation ([`batch_convert_stats_archive.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/batch_convert_stats_archive.py))
2. Ephemeral prototyping scratchpads in [`scratch/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scratch)
3. Non-pytest scripts stored inside [`tests/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests) (including an 807-line procedural manual converter)

---

## 2. Inventory of Target Files

### 2.1 Obsolete Root Batch Runner: `batch_convert_stats_archive.py`
- **Path:** [`batch_convert_stats_archive.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/batch_convert_stats_archive.py) (107 lines, 3.5 KB)
- **Analysis:**
  - Hardcoded to an external directory on your local workstation:
    ```python
    TARGET_DIR = Path(
        r"C:\Users\zubair\Documents\GitHub\stats-archive\02_Free_Response_Questions_by_Year"
    )
    ```
  - Subprocesses `python -m standalone_converter` with a 10-second delay between requests.
  - Depends on the deprecated `standalone_converter` package.
  - Not part of the reusable library or CLI toolchain.
- **Action:** Delete.

---

### 2.2 Scratch & Prototyping Directory: `scratch/`
The [`scratch/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/scratch) directory contains 8 Python files and 4 loose PNG image renders generated while diagnosing PyMuPDF vector drawing bounding boxes and image snapping for `"tests/stats merged quiz unit 1.pdf"`:

| File | Size | Description | Status |
| :--- | :---: | :--- | :--- |
| `check_docx_drawings.py` | 1.1 KB | Checks `doc.part.rels` in generated Word docs | Stale scratch |
| `compile_ast.py` | 0.8 KB | One-off AST compile verification | Stale scratch |
| `inspect_docx.py` | 2.6 KB | Prints Word document XML paragraph tags | Stale scratch |
| `test_asset_discovery.py` | 1.5 KB | Tests vector drawing bounding boxes | Stale scratch |
| `test_harvest_and_resolve.py` | 6.8 KB | Resolves drawing rectangles to images | Stale scratch |
| `test_parse.py` | 0.9 KB | Loads `.env` and tests layout parser | Stale scratch |
| `test_reconciliation.py` | 2.8 KB | Tests bounding box overlap reconciliation | Stale scratch |
| `test_whitespace_snapping.py` | 2.9 KB | Prototype for edge pixel snapping | Stale scratch |
| `raw_p6_embedded_img.png` | 2.4 KB | Test image output | Stale render |
| `test_p1_top_resolved.png` | 3.2 KB | Test image output | Stale render |
| `test_p6_resolved.png` | 2.4 KB | Test image output | Stale render |
| `test_p7_resolved.png` | 3.5 KB | Test image output | Stale render |

None of these files are imported by `src/` or executed by any test runner.
- **Action:** Delete the entire `scratch/` directory (or gitignore it as a transient scratchpad).

---

### 2.3 Non-Test Scripts Inside `tests/`
The [`tests/`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests) directory contains both genuine, high-value automated test suites and one-off procedural builder scripts that confuse test runners like `pytest`:

#### The Clutter Files:
1. **[`tests/convert_quiz.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/convert_quiz.py) (807 lines, 33 KB):**
   - A gigantic, manually coded procedural python-docx builder for `"stats merged quiz unit 1.pdf"`.
   - It contains zero `test_*` functions, zero assertions, and cannot be run by pytest.
   - It was created as an early reference prototype before `worksheet_packer` automated the process.
2. **[`tests/test_box.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/test_box.py) (64 lines, 1.8 KB):**
   - Standalone experimental script testing python-docx nested table border styling (`set_cell_margins`, `set_table_borders`).
   - Does not contain standard pytest test cases.
3. **[`tests/dump_page_blocks.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/dump_page_blocks.py) (24 lines, 0.6 KB):**
   - One-off utility dumping PyMuPDF text spans for pages 2 through 7 of `"stats merged quiz unit 1.pdf"`.
4. **[`tests/extract_all_assets.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/extract_all_assets.py) (46 lines, 1.4 KB):**
   - One-off utility dumping embedded images from `"tests/stats merged quiz unit 1.pdf"` into `./extracted_assets`.

#### The Legitimate, Active Test Suite:
When the non-test files are cleared out, the remaining test suite consists exclusively of robust, automated unit and integration tests:
- [`tests/test_worksheet_packer.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/test_worksheet_packer.py) (974 lines, 38 KB): Comprehensive tests for AST validation, 2D packing, column balancing, and image auto-crop.
- [`tests/test_subagent_pipeline.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/test_subagent_pipeline.py) (91 lines): Tests subagent CLI workflow (`parse-page`, `compile-pages`).
- [`tests/test_cli_options.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/test_cli_options.py) (236 lines): Tests CLI argument handling, independent workspaces, and `--save-ast`.
- [`tests/test_latex_pipeline.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/test_latex_pipeline.py) (227 lines): Tests LaTeX AST translation, preambles, and tables.
- [`tests/test_pipeline.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/test_pipeline.py) (100 lines): Verifies DOCX AST compiler.
- [`tests/create_sample_pdf.py`](file:///c:/Users/zubair/Documents/GitHub/pdf-to-docx/tests/create_sample_pdf.py) (96 lines): Programmatically creates the `sample.pdf` fixture.

---

## 3. Step-by-Step Remediation Plan

### Step 1: Remove `batch_convert_stats_archive.py`
```powershell
Remove-Item -Force batch_convert_stats_archive.py
```

### Step 2: Remove or Clear `scratch/`
```powershell
Remove-Item -Recurse -Force scratch
```

### Step 3: Purge Non-Test Scripts from `tests/`
```powershell
Remove-Item -Force tests/convert_quiz.py
Remove-Item -Force tests/test_box.py
Remove-Item -Force tests/dump_page_blocks.py
Remove-Item -Force tests/extract_all_assets.py
```

---

## 4. Verification Checklist

- [ ] `batch_convert_stats_archive.py` is removed.
- [ ] `scratch/` is deleted.
- [ ] `tests/` contains only test files (`test_*.py`) and fixture generators (`create_sample_pdf.py`).
- [ ] Running `uv run pytest` discovers and executes all valid tests with **zero errors and zero warnings**.

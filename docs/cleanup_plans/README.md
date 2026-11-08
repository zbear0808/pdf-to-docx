# Repository Scripts Cleanup & Refactoring Master Index

This directory contains standalone, in-depth documentation and step-by-step remediation plans for each distinct area of script redundancy, architectural deprecation, and workspace hygiene identified across the `pdf-to-docx` repository.

---

## Index of Cleanup Proposals

| # | Document | Target Area | Primary Action | Blast Radius |
| :---: | :--- | :--- | :--- | :---: |
| **01** | [01: Duplicate Scripts & CLI Wrappers](01_duplicate_scripts_and_cli_consolidation.md) | `scripts/` vs `.agents/skills/` | Consolidate scripts into root `scripts/pdf_to_docx/` & `scripts/pdf_to_latex/`; remove `.agents/skills/*/scripts/` | **Completed** |
| **02** | [02: Retiring `standalone_converter/`](02_retiring_standalone_converter.md) | `standalone_converter/` (12 files, ~112 KB) | Delete or archive monolithic cascade pipeline superseded by `src/pdf_to_docx` and `src/worksheet_packer` | **Zero** |
| **03** | [03: `audit_tools/` Deprecation & Migration](03_audit_tools_deprecation_and_heuristic_migration.md) | `audit_tools/` (7 files) | Port `ImageBoundaryAuditor` cutoff detection into `src/worksheet_packer/image_utils.py`; delete orphaned audit package | **Zero** (Enhancement) |
| **04** | [04: Scratch, Batch & Test Sanitization](04_scratch_batch_and_tests_sanitization.md) | `batch_convert_stats_archive.py`, `scratch/`, ad-hoc files in `tests/` | Delete hardcoded workstation runner, stale `scratch/` exploration scripts, and 807-line manual builder `tests/convert_quiz.py` | **Zero** |
| **05** | [05: Document Workspaces Hygiene](05_document_workspaces_hygiene_and_deduplication.md) | `unit1_test_repack/`, `unit_1_review_aligned/`, `lesson_1_21_streamlined/` | Move loose root scripts into `_temp/build/`; purge superseded intermediate iterations (`v1`, `v2`, multi-page spill scripts) | **Zero** |

---

## Recommended Execution Order

When you are ready to apply these changes, they can be safely executed in the numbered order:

1. **Step 1 (Proposal 01 & 04):** Consolidate helper scripts into `scripts/` and delete `.agents/skills/*/scripts/` (Proposal 01 completed); remove dead weight (`batch_convert_stats_archive.py`, `scratch/`, and ad-hoc scripts in `tests/`).
2. **Step 2 (Proposal 03):** Port image cutoff detection into `src/worksheet_packer/image_utils.py` with a unit test, then delete `audit_tools/`.
3. **Step 3 (Proposal 02):** Delete or archive `standalone_converter/`.
4. **Step 4 (Proposal 05):** Clean up document workspaces to adhere strictly to the `_temp/build/` directory hygiene standard.

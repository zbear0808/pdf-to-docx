# Document Processing & Workspace Hygiene Guidelines

This repository and all subagents working on document tasks (PDFs, Microsoft Word `.docx`, LaTeX `.tex`, etc.) must strictly follow these workspace organization and file hygiene rules.

---

## 1. Directory Structure Standard for Document Workflows

Whenever working on a new document task, conversion, packing, or audit (whether inside a dedicated subfolder or at the root), NEVER dump loose temporary files, intermediate renderings, cropped images, or compiler logs into the main folder.

Always structure the workspace into dedicated **Outputs** and **Temporary** subfolders:

```text
<document_workspace>/
├── input/                  # (Optional) Original raw source documents (.pdf, .docx)
├── output/                 # Final deliverables ONLY (.docx, .pdf, .tex, final reports)
└── _temp/                  # ALL transient, intermediate, and generated working files
    ├── assets/             # Extracted/cropped images, figures, diagrams, embedded media
    ├── renders/            # Page preview images (orig_p*.png, docx_p*.png, latex_p*.png)
    ├── specs/              # Intermediate JSON ASTs, extraction specs, packing plans
    └── build/              # Compiler logs/auxiliary files (.aux, .log, .fls), scratch scripts
```

### Alternative Flat Subfolder Naming (When not using `_temp/` nesting)
If creating flat subfolders directly under a document directory, ALWAYS prefix any transient or intermediate folder with `_temp_` or `temp_`:
- `_temp_assets/` (or `temp_assets/`)
- `_temp_renders/` (or `temp_renders/`)
- `_temp_specs/` (or `temp_specs/`)
- `_temp_build/` (or `temp_build/`)
- `output/` (final deliverables)

---

## 2. Universal Gitignore Convention

By consistently labeling temporary directories with `_temp/`, `.temp/`, `_temp_*`, or `temp_*`, all temporary assets and intermediate renderings are easily gitignored across any new project with the following standard block:

```gitignore
# Document Processing: Standardized Temporary & Intermediate Directories
**/_temp/
**/.temp/
**/temp/
**/_temp_*/
**/temp_*/
**/tmp/
**/tmp_*/

# Media extraction & page rendering artifacts
**/rendered_pages/
**/extracted_assets/
**/*_rendered_pages/
**/*_pages/
**/media_cropped/
**/.ws_*

# LaTeX build & compiler scratch files
**/*.aux
**/*.log
**/*.fls
**/*.fdb_latexmk
**/*.synctex.gz
**/*.out
**/*.toc
```

---

## 3. CLI & Subagent Tooling Rules

When running CLI commands or dispatching subagents, always route intermediate files to `_temp/` and final artifacts to `output/`:

1. **Page Rendering**:
   ```bash
   uv run python -m pdf_to_docx render-pages document.pdf -o _temp/renders
   ```
2. **Asset Cropping / Image Harvesting**:
   ```bash
   uv run python .agents/skills/pdf-to-docx/scripts/crop_asset.py document.pdf --page 1 --bbox 100,50,300,400 -o _temp/assets/fig1.png
   ```
3. **Spec Extraction & Planning**:
   ```bash
   uv run worksheet-packer parse document.pdf -o _temp/specs/spec.json --workspace-dir _temp/assets
   uv run worksheet-packer pack _temp/specs/spec.json -o _temp/specs/plan.json
   ```
4. **Final Compilation**:
   ```bash
   uv run worksheet-packer render _temp/specs/plan.json -o output/final_worksheet.docx --format docx
   ```
5. **LaTeX Compilation**:
   When invoking `pdflatex` or `latexmk`, pass `-output-directory=_temp/build` so that `.aux`, `.log`, `.fls`, and `.fdb_latexmk` do not pollute the root directory.

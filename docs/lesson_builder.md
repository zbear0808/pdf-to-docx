# lesson-builder

Builds a lesson's student handout, lesson key, practice set, practice key, and teacher guide from one YAML file.
The lesson YAML is the only copy of the content: answers, minutes, figures, and the plan live next to each prompt,
so the documents and the checks can't drift apart.

## Layout

```text
src/lesson_builder/
  cli.py          lesson-builder new-unit | ingest | build | check | check-pdfs | packet
  spec.py         UnitSpec / LessonSpec / Item (pydantic), YAML loading
  docbuilder.py   python-docx layout engine: Word equations, labeled boxes, frames, key-only answers
  render.py       LessonSpec -> five DOCX files
  fit.py          export, count pages, shrink workspace until the page budget fits
  check.py        spec checks (blanks, refs, minutes, answers, key figures) + output checks (PDF)
  export.py       DOCX -> PDF (one Word instance via pywin32; LibreOffice fallback), PDF -> PNG
  diff.py         compare page renders to the previous build; list changed pages
  packet.py       duplex PDF and DOCX packets
  ingest.py       source DOCX/PDF -> Markdown with math, images, page renders
  figures/
    core.py       Figure with "given" (black) and "answer" (red) layers; @figure registry
    geometry.py   rigid motions, correspondence checks, tick/arc marking helpers, templates
templates/unit/   starter unit.yaml, lessons/example.yaml (every field), figures.py
units/<course>/<unit>/
  unit.yaml       course, period, minutes, page budgets, print settings, lesson list
  lessons/2.1.yaml
  figures.py      @figure functions for this unit (student + key PNG from one function)
  assets/         reused PNGs from sources
  input/          source documents (gitignored)
  output/         deliverables (gitignored)
  _temp/          figures, renders, previous renders, logs (gitignored)
```

## Interfaces

### Figures (`lesson_builder.figures`)
```python
from lesson_builder.figures import Figure, figure

@figure("parallelogram")              # registered by name
def parallelogram() -> Figure:
    f = Figure(width_in=2.6, height_in=2.0)
    f.poly([A, B, C])                  # layer="given" (black) by default
    f.poly([C, D, A], layer="answer")  # red, key only
    f.ticks(A, B, 1, layer="answer"); f.arc(B, A, C, n=1, layer="answer")
    f.label(D, "D", layer="answer")
    return f
```
`render_all(module_or_path, out_dir) -> {name: {"student": Path, "key": Path | None, "meta": dict}}` writes `name.png`
(given layer only) and, if the figure has an answer layer, `name_key.png` (both layers). 300 DPI, trimmed.
`name.json` (`meta`) holds the drawn width, the smallest text size, and label lint.

**Label placement (`figures/layout.py`).** Every label (`label`, `label_poly`, `side_label`, `angle_label`, `text`)
carries candidate spots, the requested one first. `Figure.place()` draws all layers' ink once and keeps, per label,
the first candidate whose ink box (measured from the glyphs) clears lines ≥ 0.6 pt wide, dots, arrows, and earlier
labels, and (for point labels) is nearer its own point than any other. Student and key share the result. Labels with
no clear spot keep the least-bad one and become lint ("touches a line"). Deterministic; `fixed=True` opts out. Primes
in mathtext labels are set as U+2032 so they sit against the letter.

`lesson-builder figs <unit> [-l stem]` renders figures only and writes `_temp/figures/<stem>_sheet.png` (print-size
contact sheet) plus lint and printed-size checks (text under 7 pt at the item's `fig_w` is an error).

### Lesson YAML (see `templates/unit/lessons/example.yaml` for every field)
- Sections (`kind`): `warmup`, `together`, `partner`, `notes` (new page: header + printed QuickNotes), `cyu`, `exit`,
  `plain`. Optional `box` (move/word bank), `intro`, `page_break_before`.
- Items: `n`, `minutes`, `prompt` (string or list of lines), `figure` / `key_figure` (registered figure name or asset
  path), `fig_w`, `layout`, `choices`, `choice_cols`, `answer`, `work`, `fill` (labeled boxes), `frame` (sentence
  frame), `box` (write-in box), `table` (arrow table), `columns` (notice/wonder), `draw` (steps + drawing box),
  `parts` (a./b. with their own answers and boxes), `page_break_after`, `no_answer`.
- Practice: `rows` of 1-2 `cells` (items), optional `heading` / `page_break_before`, `selected` answers.
- `plan` (Markdown with a timing table) and `guide_notes` go into the teacher guide, after an answer key that is
  generated from the items.
- Every item and part needs an answer; drawing items need a key figure. `lesson-builder check` enforces both, plus
  fill/frame boxes ≥ 0.9 in, balanced `$`, figure lint and printed size, colour/resolution of image assets, and
  teacher-guide punctuation.

### Build
`lesson-builder build <unit>`: render figures (cached) → DOCX → PDF in one Word instance → shrink workspace ×0.88 per
round (floor 0.6) until each document fits → spec + PDF checks → page PNGs → diff against the last build → packets.

### Export / diff / ingest / packet
```python
export.docx_to_pdf(paths: list[Path]) -> list[tuple[Path, int]]   # (pdf, pages)
export.pdf_to_pngs(pdf: Path, out_dir: Path, dpi=110) -> list[Path]
diff.diff_renders(new_dir, prev_dir, out_dir=None) -> list[str]     # changed page names
ingest.ingest(files: list[Path], out_dir: Path, render=True) -> list[Path]
packet.pdf_packet(groups, out) -> (pages, starts); packet.docx_packet(groups, out) -> pages
```

### Adding a subject
Put figure helpers in `src/lesson_builder/figures/<subject>.py` (for example `coordinate.py`, `stats.py`), with
tests. Unit `figures.py` files only call helpers. New item layouts go in `render.py` plus a field in `spec.py`.

# lesson-builder

Builds a lesson's student handout, lesson key, practice set, practice key, and teacher guide, or an assessment's
student copy, key, and teacher notes, from one YAML file per document.
The YAML is the only copy of the content: answers, minutes, figures, and the plan live next to each prompt,
so the documents and the checks can't drift apart.

## Layout

```text
src/lesson_builder/
  cli.py          new-unit | scaffold | brief | ingest | figs | build | check | check-pdfs | retain | integrity |
                  tidy | status | packet
  spec.py         UnitSpec / LessonSpec / Item / Part / Target / NoteBlock (pydantic), YAML loading
  numbering.py    numbering groups, `numbering: auto`, {ref:id} / {num:id} (runs on the raw dict before validation)
  docbuilder.py   python-docx layout engine: Word equations, labeled boxes, frames, key-only answers
  render.py       LessonSpec -> DOCX files; work defaults, selected answers, teacher guide (key, rubric,
                  distractor table, blueprint)
  fit.py          export, count pages, shrink workspace until the page budget fits, page-fill log lines
  pagefill.py     per-page slack and items from the built PDFs; overflow, uneven, key/student mismatch
  check.py        spec checks (answers, MC, targets, refs, text, boxes, figures) + output checks (PDF)
  voice.py        banned words, dashes, exclamation points (code copy of the authentic-writer list)
  retain.py       figure bundle output/figures/<stem>/ + README; verify against the DOCX images
  integrity.py    letters, numbers, keys, and figure labels shared across forms or with a review
  tidy.py         unit litter and unused sources
  status.py       per-document table: handoffs, Must fix, GAPs, outputs, stale, retained
  scaffold.py     skeleton YAML, figures/<stem>.py, handoff files; registers the file in unit.yaml
  brief.py        one-file brief per step subagent (_temp/specs/<stem>/brief_<step>.md)
  export.py       DOCX -> PDF (one Word instance via pywin32; LibreOffice fallback), PDF -> PNG
  diff.py         compare page renders to the previous build; list changed pages (clears old diffs)
  packet.py       duplex PDF and DOCX packets
  ingest.py       source DOCX/PDF -> Markdown with math, images, page renders
  figures/
    core.py       Figure with "given" (black) and "answer" (red) layers, custom(), key_frame; @figure registry
    layout.py     label placement, prime-style lint
    geometry.py   motions, predicates, constructions, asserts, congruence marks, templates
    coordinate.py axes, points, lines, function graphs, slope triangles
    numberline.py number lines, points, intervals, rays
    stats.py      dot plot, histogram, box plot, scatter, normal curve
    cs.py         array boxes, reference (memory) diagrams
    sheet.py      print-size contact sheets
templates/unit/   unit.yaml, lessons/example.yaml, assessments/example.yaml (every field), figures/example.py
units/<course>/<unit>/
  unit.yaml       course, period, budget, lessons (teaching order), assessments globs, targets
  lessons/<id>.yaml
  assessments/<stem>.yaml   one per form (A, B, Retake); doc_type assessment | reference
  figures/<stem>.py         @figure functions for one document (stem = YAML file stem)
  figures/_helpers.py       optional shared helpers (`_` files are not documents)
  figures.py      legacy shared figures (Unit 2)
  assets/         reused images from sources
  input/          source documents (gitignored)
  output/         deliverables, output/figures/<stem>/ bundles (gitignored)
  _temp/          ingest, figures, renders, specs (handoff files), build scratch (gitignored)
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
`name.json` (`meta`) holds the drawn width, the smallest text size, label lint, the label texts (read by
`integrity`), and `key_width_in`. The cache is stale when the figure file, a `_*.py` sibling, any library file in
`figures/`, or a file in `assets/` is newer than the outputs.

- `Figure(key_frame="union")`: the student frame fits the given ink; the key keeps the scale and grows to the
  union of both layers, so an answer past the given drawing isn't cut off (no separate `_key` figures).
- `Figure.custom(fn, layer, extent=None, pad_pt=0)`: `fn(ax, color)` draws with matplotlib in data units. It keeps
  layers, trimming, sidecars, colour lint, and label obstacles. The subject modules (`coordinate`, `numberline`,
  `stats`, `cs`) are built on it.
- `geometry.py`: predicates (`is_parallel`, `collinear`, `on_ray`), constructions (`foot`, `extend`,
  `triangle_from_angles`, `triangle_sas`, `law_of_sines_side`), asserts (`assert_dilation`, `assert_similar`,
  `assert_lengths`, `assert_distinct`), marks (`mark_congruent`, `mark_parallel`), and templates that assert their
  own math (`congruent_pair`, `rotation_build`, `reflection_build`, `dilation_task`, `side_splitter`, `rect_pair`).
  Signatures: `.agents/skills/lesson-builder/references/api_cheatsheet.md`.

**Label placement (`figures/layout.py`).** Every label (`label`, `label_poly`, `side_label`, `angle_label`, `text`)
carries candidate spots, the requested one first. `Figure.place()` draws all layers' ink once and keeps, per label,
the first candidate whose ink box (measured from the glyphs) clears lines ≥ 0.6 pt wide, dots, arrows, and earlier
labels, and (for point labels) is nearer its own point than any other. Student and key share the result. Labels with
no clear spot keep the least-bad one and become lint ("touches a line"). Deterministic; `fixed=True` opts out. Primes
in mathtext labels are set as U+2032 so they sit against the letter; mixed prime styles in one figure are lint.

`lesson-builder figs <unit> [-l stem]` renders figures only and writes `_temp/figures/<stem>_sheet.png` (print-size
contact sheet) plus lint and printed-size checks (text under 7 pt at the item's `fig_w` is an error).

### Document YAML (see `templates/unit/lessons/example.yaml` and `templates/unit/assessments/example.yaml`)
- Sections (`kind`): `warmup`, `together`, `partner`, `notes` (new page: header + printed QuickNotes), `cyu`, `exit`,
  `plain`. Optional `box`, `bank` (word/move bank), `intro`, `target`, `columns: 2` (assessments: two items per
  row), `page_break_before`.
- Items: `n` (or `numbering: auto`), `id` (for `{ref:id}` / `{num:id}`), `minutes`, `points`, `prompt`, `steps`,
  `figure` / `key_figure`, `fig` (small / medium / wide) or `fig_w`, `layout`, `choices`, `key`, `select_all`,
  `distractors`, `answer`, `rubric`, `scoring: epi`, `target` / `type` / `demand` / `standard`, `source`, `work`,
  `fill`, `frame` (list or named rows), `box`, `table`, `columns`, `draw`, `parts`, `page_break_after`, `no_answer`.
- `work` default (`render._work`): explicit value wins; 0 with fill, frame, box, parts, table, columns, or draw;
  0.2 with choices; else 0.8 (parts 0.6).
- Document: `targets`, `set` / `form` / `parallel_to` / `do_not_reuse` (forms), `source`, `quicknotes` (strings or
  `{target, title, bullets}` blocks). `header_right` is deprecated (check WARN).
- Practice: `rows` of 1-2 `cells`, optional `heading` / `page_break_before`, `selected: auto`, a list of numbers
  (answers come from the items), or `[n, answer]` pairs.
- The teacher guide / Teacher Notes: an answer key generated from the items (key letter, rubric levels, E/P/I),
  a distractor table from `distractors`, a blueprint table (assessments with target/type/demand) with a demand count,
  then `plan` and `guide_notes`.
- `lesson-builder check` enforces answers and key figures, boxes ≥ 0.9 in, MC rules (choice count, duplicates,
  all/none of the above, long key, key letter range and patterns), voice (`voice.py`), targets, references, `$`
  and money, block-scalar primes, unknown figure names, `selected` numbers, TODO placeholders, figure lint and
  printed size, asset colour and resolution, and teacher-guide punctuation.

### Build
`lesson-builder build <unit>`: render figures (cached) → spec checks → DOCX → PDF in one Word instance → page-fill
report per PDF; shrink workspace ×0.88 per round (floor 0.6) while a document is over budget, logging which item
overflows and whether a page break pins it → PDF checks → page-fill summary (slack and items per page, uneven pages,
key/student page mismatch) → retain + verify the figure bundle (`--no-retain` skips) → page PNGs → diff against the
last build → packets (full build only).

### Workflow commands
```python
scaffold.scaffold(unit, stem, doc_type="lesson", forms=None, title=None, force=False) -> list[Path]
brief.brief(unit, stem, step="plan") -> Path            # _temp/specs/<stem>/brief_<step>.md; plan|figures|write|audit
retain.retain(unit, lesson, rendered) -> RetainResult    # output/figures/<stem>/ PNGs + README; .errors, .files
retain.verify(unit, lesson) -> list[str]                 # retained PNGs vs images embedded in the DOCX files
integrity.check_set(unit, globs, vs=(), rendered=None) -> list[str]   # pairs of forms, parallel_to, vs, do_not_reuse
tidy.find_litter(unit) -> list[Finding]; tidy.apply(findings) -> list[Path]   # deletes temp/cache/diff kinds only
status.unit_status(unit, with_checks=False) -> list[DocStatus]; status.format_table(statuses) -> str
pagefill.page_report(pdf) -> list[PageFill]; overflow / pinned / uneven / mismatch -> message or None
```

### Export / diff / ingest / packet
```python
export.docx_to_pdf(paths: list[Path]) -> list[tuple[Path, int]]   # (pdf, pages)
export.pdf_to_pngs(pdf: Path, out_dir: Path, dpi=110) -> list[Path]
diff.diff_renders(new_dir, prev_dir, out_dir=None) -> list[str]     # changed page names
ingest.ingest(files: list[Path], out_dir: Path, render=True) -> list[Path]
packet.pdf_packet(groups, out) -> (pages, starts); packet.docx_packet(groups, out) -> pages
```

### Adding a subject
Put figure helpers in `src/lesson_builder/figures/<subject>.py` (`coordinate.py`, `numberline.py`, `stats.py`,
`cs.py` exist), built on `Figure.custom` when they need matplotlib, with tests. Unit figure files only call
helpers. New item layouts go in `render.py` plus a field in `spec.py`, a check, and a line in the matching
`example.yaml`.

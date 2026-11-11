# Phase 2: formatting, converter, layout automation, full patterns, unit defaults

Goal: built during the next unit's planning and piloted on it. Moves errors from audit to `check`, and makes the output look consistent without per-doc fixes. Requires Phase 1 (timing, error codes, pattern test).

| # | Item | Effort | Depends on |
|---|---|---|---|
| 1 | F9 clean Word XML | S-M | none |
| 2 | F10 formatting defaults | M | 1 |
| 3 | F7 math converter coverage | M | P1 A3 |
| 4 | A1 unit defaults + `decide` | M | none |
| 5 | G2 full pattern library + brief selection + deviation warnings | M | P1 G1, 2, 3, 4 |
| 6 | A5 traps file | S | 5 |
| 7 | F11 automatic layout fixes | M | 2 |
| 8 | F2b keys exported once | M | P1 F2a, 7 |
| 9 | F3 figure manifest cache | S-M | none |
| 10 | B1 label placement check | M | none |
| 11 | B4 frame coverage check | S | 4 |
| 12 | A4 page estimate warning in `check` | M | 2 |
| 13 | C2 `explain` | M | P1 C4 codes |
| 14 | C3 `anchors`, `keytext`, `pages` | S | none |

F9 and F10 come first because every pattern and every fix after them should be written against the final formatting. Patterns (5) then lock that formatting in with tests.

---

## 1. F9 clean Word XML
**Change.** `docbuilder.py`: new `_set_child(parent, tag, order)` that removes an existing child and inserts in CT_TcPr / CT_TblPr schema order. Use it in `cell_margins`, `cell_bottom_border`, `table_borders`, `table_no_borders`, `table_inside_only`, `table_indent`, `row_height`, `row_cant_split`. `table_indent`: also reduce widths via `set_widths` so the table ends at the right margin.
**Tests.** `tests/test_docx_xml.py`: call each helper twice → one child, schema order; indented table total width ≤ text width. Add `check_docx_xml(path)` in `check.py` and run it in `check_outputs`.
**Accept.** Validator passes on all patterns and a rebuilt Unit 4.
**Risk.** Word renders differently once order is fixed; compare renders with `diff_renders`.

## 2. F10 formatting defaults
**Change.** Constants block at the top of `docbuilder.py`: `LABEL_PAD_TW = 120`, `LABEL_W_MIN = 0.3`, `BOX_W_TEXT = 1.6`, `BOX_W_NUM = 1.3`, `BOX_H_TEXT = 0.42`, `BOX_H_NUM = 0.38`, `ROW_GAP = 0.10`, `BOX_BEFORE_PT = 5`, `INDENT_1 / INDENT_2`, `MATH_LINE = 1.08`, key style (bold, darker red, body size), footer 9 pt, bank 10.5 pt.
- `Handout.fill_boxes` (≈ line 843) and frame code (≈ 882-905): one label width per problem = `LABEL_W_MIN + max(_measure_rich(label))`, padding from constants, fixed box widths.
- Header (≈ line 494): drop empty lesson label parts; wider title cell.
- Guide (`md_to_doc`): content-based column widths, keep-with-next on headers, warn on "□".
- Unit option `body_size` (A1) for 12 pt Period 4 handouts.
**Tests.** `tests/test_formatting.py`: frame rows in one problem share label width; label cell margin = 120; key run is bold. Pattern renders updated (expected diffs reviewed once).
**Accept.** Teacher spot-check of 5 renders; crowding/spacing audit findings down by half in the pilot.
**Risk.** Pages grow and push docs over budget; run all patterns and Unit 4 rebuild and adjust box heights before release.

## 3. F7 math converter coverage
**Change.** `docbuilder.latex_to_omml_inner` / `_read_group`: add `\mathrm \mathbf \vec \hat \widehat \bar \underline \overset \dots \cdots \because \rightarrow \lambda \omega \binom \sum \$`; superscript base = last group (closing paren or brace group) not last char; `\left( ... \right)` → `m:d` delimiters with grow; `cases`, `matrix`/`pmatrix`, `aligned`, `\\` → `m:eqArr`/`m:m`; unbraced single-token args for `\frac12`, `\sqrt x`. `add_rich`: `$` followed by a digit with no closing `$` is text.
**Tests.** `tests/test_math_convert.py`: one parametrized case per command; `(x+1)^2` base check; money string.
**Accept.** 0 `LB-MATH` in the pilot; no `\alpha`-style workarounds in new YAML.

## 4. A1 unit defaults + `decide`
**Change.** `spec.UnitSpec`: `defaults: UnitDefaults` (`practice_selected`, `key_label_side`, `fraction_box`, `body_size`, `math_allowed_extra`). `render.py` reads these where the per-doc field is unset (`render._explicit`). `brief.brief()`: "Unit decisions" section from `defaults` plus `<unit>/decisions.md`. `cli decide <unit> "<rule>"` appends to `decisions.md`.
**Tests.** default applied when doc omits field; doc override wins; brief contains the section.
**Accept.** Same finding in 3+ docs: 0 or 1 types in the pilot.

## 5. G2 full pattern library
**Change.**
- Add remaining patterns: `find-angle`, `mc-select-all`, `mc-fractions`, `sketch-solve`, `true-false` (workaround now; switch to `tf:` in Phase 3), `quicknotes`, `forms-a-retake` (two files + version table; test also runs `integrity.check_set`), `review-unscored`, `reference-sheet`, `actual-size-ruler` (test runs `actual_size_issues`), `similar-correspondence`. Confirm each against Unit 4 `_temp/specs/*/changes.md` and `audit.md`; add any trap seen twice.
- `brief.py`: `examples_md(doc_type)` → `examples_md(doc_type, wanted)`; `wanted` comes from the requirements blueprint item `type` and the figure plan (`planned_figures`), mapped to patterns by `patterns.match(item_types, figure_kinds)`; paste 3-5 matching patterns, fall back to today's example.
- `check.check_spec`: `patterns.deviations(lesson)` warns `LB-PATTERN` on known-trap shapes (draw/fill in a practice cell, `selected: auto`, frame with multiple blanks in one line without `template`, fraction in a box under `BOX_H_NUM`).
- Pattern test also rebuilds after F9/F10 so the expected 0/0 holds with final formatting.
**Tests.** `tests/test_patterns.py` covers all; `tests/test_brief.py` checks selection for a blueprint with fill+figure items.
**Accept.** ≥ 70% of pilot items from a pattern; first-build pass rate ≥ 80%.
**Risk.** Over-fitting a pattern to one lesson; keep each pattern generic (no unit content).

## 6. A5 traps file
**Change.** `.agents/skills/lesson-builder/references/traps.md` (skills change, done in this phase by the implementer): one line per trap, the error code, and the pattern that avoids it. `brief._extras` includes the lines for the doc type.
**Accept.** Every `LB-PATTERN` warning text links a trap line.

## 7. F11 automatic layout fixes
**Change.**
- Key height reserve: `render._body` measures key answer height (`answer_height`, calibrated from PDFs with `pagefill`) and sets the same fixed slot on both copies.
- QuickNotes: keep-with-next on the block and its heading; in `fit`, if the over page starts with QuickNotes after a break with ≥ 4 in slack, move QuickNotes or reduce its fixed height before shrinking.
- `render._cell_item`: stack figure above prompt when prompt column < 2.4 in or choices wrap.
- Boxes auto-grow to label width and math height (extends the tall-math growth).
- Fill/draw in half-width cells: `render._two_columns` returns False for that row (full width), with an info note.
**Tests.** stack threshold; QuickNotes rule with a stub page report; half-width fallback.
**Accept.** Drift in ≤ 3 docs per unit; 0 OVER triggers from a QuickNotes break.

## 8. F2b keys exported once
**Change.** `fit.build_lesson`: fit rounds export handout + practice only; keys render and export after the loop at the final scale; drift checks (`anchor_drift`, `frame_drift`) confirm match.
**Accept.** Exports per 2-round build ≤ 6; drift checks pass on all patterns.
**Risk.** Key overflows when student fits; key has same slot heights (F11 reserve), plus a fallback round on key overflow.

## 9. F3 figure manifest cache
**Change.** `figures/core.render_all` (≈ 512-532): manifest `{name: {src_hash, deps_hash, png, size}}` next to the PNGs; skip `load_module` and function calls on hit; hash instead of mtime.
**Accept.** Cached load ≤ 0.3 s on 4.7.

## 10. B1 label placement check
**Change.** `figures/core.py` label helpers record `(text, target, bbox, layer)` in the sidecar. `check.check_figures`: nearest segment to the label ≠ target → error `LB-LABEL`; overlapping bboxes or label over a line → warning; key label on the opposite side of the student label → error.
**Tests.** synthetic figure for each case.
**Accept.** Label-side + crowding findings ≤ 2 in the pilot (Unit 4: 11).

## 11. B4 frame coverage
**Change.** `check.check_spec`: planned frames from requirements (`brief.requirements_path`) vs present; MLL period (`brief._mll`) explain items with no frame → warning.

## 12. A4 page estimate warning
**Change.** `pagefill.estimate(lesson, figs)` from slot heights, figure sizes, text lines; `check` warns `LB-PAGE-EST` with the 3 biggest items. Calibrate against Phase 1 build events.
**Accept.** Page-budget build failures ≤ 2 in the pilot (Unit 4: 9).

## 13. C2 `explain`
**Change.** `src/lesson_builder/explain.py` table code → cause, how to locate, YAML fix, pattern; `cli explain <code> [--unit --stem]` fills in items from the last event.

## 14. C3 evidence commands
**Change.** `cli anchors` (`check._labels`, `_frames`, `anchor_drift`), `cli keytext` (`clipped_answers`), `cli pages` (`pagefill` report per item).
**Accept.** 0 scratch measurement scripts under the pilot's `_temp/build`.

---

## Verification
1. `uv run pytest`, including the Word-marked pattern builds.
2. Rebuild Unit 4 copy; review render diffs from F9/F10 once with the teacher.
3. Pilot: the full next unit.
4. Compare:

| Metric | Unit 4 | Phase 2 target |
|---|---|---|
| Builds per doc | ~5 | ≤ 3 |
| Failed builds | 26% | ≤ 10% |
| Fit-loop share of build time | 69% | ≤ 25% |
| Fix-round cost | +57% | ≤ +30% |
| Typical lesson build | ~40 s | ≤ 15 s |
| Items from a pattern | 0 | ≥ 70% |
| Audit share of findings | (from E4) | ≤ 40% |

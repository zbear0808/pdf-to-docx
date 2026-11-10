# lesson-builder API cheat sheet

Checked against `src/lesson_builder/` (Nov 9). If this sheet and the code disagree, the code wins. Field reference: `templates/unit/lessons/example.yaml`, `templates/unit/assessments/example.yaml`.

## 1. Commands (repo root, `uv run lesson-builder ...`)

| Command | What / flags |
|---|---|
| `new-unit DEST --course C --unit N --title T [--period P]` | unit folder from `templates/unit`; DEST empty or missing |
| `scaffold UNIT STEM [--type lesson\|assessment\|reference] [--forms A,B,Retake] [--title T] [--force]` | skeleton YAML (loads and builds; open spots say TODO), `figures/<stem>.py`, `_temp/specs/<stem>/requirements.md` + `changes.md`; adds the file to `unit.yaml` if no glob covers it. With `--forms`: one `<STEM> <form>.yaml` each (set/form/parallel_to filled), one shared `requirements.md` |
| `brief UNIT STEM --step plan\|figures\|write\|audit` | writes `_temp/specs/<stem>/brief_<step>.md`: inputs, files the step owns, schema subset, examples, done condition, reply format |
| `ingest SRC... -o OUT [--no-render]` | DOCX/PDF to Markdown with math, `_media/`, `_pages/` |
| `figs UNIT [-l STEM]... [--no-sheet] [--force]` | figures only (seconds): lint, print size, `_temp/figures/<stem>_sheet.png` |
| `build UNIT [-l STEM]... [--strict] [--force-figures] [--no-packets] [--no-fit] [--no-retain]` | figures, DOCX, PDF, fit, checks, page-fill report, **retain + verify**, renders, diff; packets only without `-l` |
| `check UNIT [-l STEM]... [--no-outputs]` | spec checks + PDF checks of existing output |
| `check-pdfs STUDENT.pdf KEY.pdf [--max-pages 3]` | any student/key pair |
| `retain UNIT [-l STEM]... [--verify-only]` | figure bundle `output/figures/<stem>/` + README (build runs it) |
| `integrity UNIT --set GLOB... [--vs GLOB...]` | forms share no letters, numbers, MC key positions; `--vs` docs (review, notes) reuse nothing from the set; also each doc's `do_not_reuse` |
| `tidy UNIT [--apply]` | lists Word temp files, `__pycache__`, stale diffs (deleted with `--apply`); reports orphan assets, unused figures, unlisted YAML, orphan figure files, redundant `work:` lines (never deleted) |
| `status UNIT [--checks]` | one row per document: handoffs (req/cha/aud), open Must fix, GAP lines, built x/y, PDFs, stale, figures retained (+ errors/warnings) |
| `packet UNIT` | rebuild duplex packets from existing outputs |

`-l` matches the file stem or `id`; repeatable. Exit code 1 means errors. Quote stems with spaces.

**Build log lines to read:** `<id> handout 3p/3: p1 0.4 in [1-3]; p2 ...` (slack and items per page), `WARN handout p2: 2.1 in empty while p1 is full; page break before ...`, `handout OVER: item 7 starts p4 (budget 3)`, `p4 starts after a page break` (shrinking won't help), `WARN key: item 5 is on key p2 but student p1`, `figures retained: <dir> (N files)`, `pages to review`. Page-fill lines are log lines, not counted errors.

## 2. Unit layout

```text
unit.yaml                 course, unit, unit_title, period, budget{minutes:40, handout_pages:3, practice_pages:2},
                          lessons: [3.1.yaml, ...], assessments: [assessments/*.yaml], targets: [...], figures: figures.py
lessons/<id>.yaml         one per lesson
assessments/<stem>.yaml   one per form (A, B, Retake); doc_type assessment | reference
figures/<stem>.py         per-document figures; <stem> = YAML file stem exactly ("Unit 3 Test A.py")
figures/_helpers.py       `_` files are not documents; `from _helpers import ...`
figures.py                legacy shared figures, seen by every document
assets/                   images; `figure: assets/x.png` (relative to the unit dir)
_temp/figures/<stem>/     <name>.png, <name>_key.png (answer layer only), <name>.json (meta + labels)
_temp/specs/<stem>/       requirements.md, changes.md, audit.md, brief_<step>.md
output/Lesson <id>/       Student Handout, Lesson Key, Practice Problems, Practice Key, Teacher Guide
output/Assessments/       <id>, <id> Key, <id> Teacher Notes (if plan, guide_notes, distractors, or blueprint)
output/Reference/         <id> (no key)
output/figures/<stem>/    retained PNGs + README (item -> figure -> file:function, helpers, regenerate commands)
```

A document sees `figures.py` names plus its own `figures/<stem>.py` (own file wins). Name figures `<stem>_<item>`.

## 3. YAML quick reference (unknown keys are errors)

**Document:** `id` | `doc_type` lesson*/assessment/reference | `title` | `notes_title`, `framing` (required for lessons) | `materials` | `directions` | `total_points` (= item + part points) | `max_pages` | `numbering: manual*|auto` | `targets: [{id, understand, able_to, standard}]` (adds to unit `targets`) | `set`, `form`, `parallel_to`, `do_not_reuse: [globs]` | `source` | `sections` | `quicknotes` | `notes_height` 2.2 | `practice` | `plan` | `guide_notes`. `header_right` is deprecated (WARN; the builder prints Name / Per / Score).

**Section:** `kind` warmup/together/partner/notes/cyu/exit/plain | `title` | `sub` | `intro` | `box` | `bank: [...]` (boxed, ` | ` separated) | `target` | `columns: 1|2` (2: items two per row; draw/table/columns items full width) | `items` | `page_break_before`. `notes` starts the QuickNotes page; numbering restarts after it.

**Item** (Part shares the starred fields):

| Field | Default | Notes |
|---|---|---|
| `n` | None | "1" prints "1."; `numbering: auto` fills it (warm-up stays unnumbered; `n: ''` skips one) |
| `id`* | None | `{ref:id}` prints "Problem 4", `{num:id}` prints "4" (parts: "4b") in any text, including `plan`; unknown id is an ERROR |
| `minutes` / `points`* | 0 / None | lessons: minutes ≤ budget; points print "(2 pts)" |
| `prompt`* / `steps` | "" / [] | `steps` print "Step 1: ..." under the prompt |
| `figure` / `key_figure` | None | registered name or path; an unknown name is a check ERROR |
| `fig` / `fig_w` | None | `fig: small\|medium\|wide` = 1.6 / 2.4 / 3.4 in; `fig_w` wins; neither = drawn width |
| `layout` | side | `stacked` = image under the text |
| `choices`* / `choice_cols`* | None / 1 | 3-4 choices, at most 10 |
| `key`* / `select_all`* / `distractors`* | None / false / {} | `key: C` (or `'B, C, E'`); prints `[C]` before `answer` unless it starts with `[`. `distractors: {A: 'added instead of multiplied'}` |
| `answer`* | None | str or list. MC without `key`: `'[B] reason'` |
| `rubric`* / `scoring`* | [] / None | `rubric: [{level: 4, desc: '...'}]` (3-6 levels) on the key and Teacher Notes; `scoring: epi` (AP Stats) |
| `target`* / `type`* / `demand`* / `standard`* | None | `type` sr/cr/performance; `demand` mem/pwoc/pwc/dm; assessments get a Blueprint table in Teacher Notes |
| `work`* | see below | blank inches |
| `fill`* / `fill_cols`* / `box_w`* | None / one row / 1.3 | `[['$x =$', '15']]` |
| `frame`* / `frame_box_w`* | None / 1.1 | rows `[before, answer, after(, w)]` or `{before, answer, after, w}` |
| `box` / `table` / `columns` / `draw` / `parts` | None | write-in box; arrow table; notice/wonder; steps + drawing box; a./b. |
| `source`* / `after` / `page_break_after` / `no_answer`* | | provenance; 0.08; false; false |

**`work` default** (render `_work`): explicit value wins; else 0 if the item has `fill`, `frame`, `box`, `parts`, `table`, `columns`, or `draw`; 0.2 with `choices`; else 0.8 (part 0.6). Don't write `work:` lines equal to the default (`tidy` reports them). Figure-only items still get 0.8.

**Table:** `header`, `answers` (one fewer), `row_label` "Lands on", `first_w` 1.45, `height` 0.42. **Columns:** `headers`, `answers` (list per column), `height` 0.85, `italic`. **Draw:** `height` 3.0, `steps_w` 3.05, `key_figure`, `key_fig_w` 2.5, `key_note`.
**Practice:** `title`, `rows: [{cells: [Item, Item?], heading?, page_break_before?}]`, `selected: auto | ['1', '4', '6a'] | [['1', 'D'], ...]` (bare numbers take the item's `key`/`answer`), `font_size` 10.5. Cells ignore `draw`, `table`, `columns`.
**QuickNotes:** strings, or blocks `{target: LT1, title: '...', bullets: ['...']}` (bold heading + bullets).

## 4. Figures API (`from lesson_builder.figures import ...`)

`Figure(width_in, height_in, name=None, key_frame="same")`: one x/y scale. `layer="given"` is black (student + key), `layer="answer"` red (key only). Tick/arc/right-angle sizes are data units; `offset_pt` and `size` are points.
`key_frame="same"`: student and key share one frame (blank room where the answer goes). `key_frame="union"`: the student frame fits the given ink; the key keeps the scale and grows to fit the answer ink (replaces separate `_key` figures; the key prints wider).

| Method | Signature (defaults) |
|---|---|
| `poly` | `(pts, closed=True, layer, lw=None, dashed=False, fill=None, hatch=None)` |
| `seg` / `dots` / `grid` | `(a, b, layer, lw, dashed)` / `(pts, layer, size=14)` / `(x0, x1, y0, y1, step=1, lw=0.3, layer)` |
| `label` | `(pt, text, layer, direction=None, center=None, offset_pt=10, size=None, italic=True, fixed=False)`; italic wraps in `$..$` |
| `label_poly` | `(pts, names, layer, overrides=None, offset_pt=10)`; names `"ABC"` or list (None skips); overrides `{name: direction}` |
| `side_label` / `angle_label` | `(a, b, text, center, layer, offset_pt=10, italic=False, size=None, fixed=False)` / `(vertex, p1, p2, text, dist=None, layer, size=None, fixed=False)` (raw text: `'$40^\circ$'`) |
| `text` / `arrow` | `(pt, s, layer, size=None, fixed=False)` / `(a, b, layer="answer", dashed=True)` (**default layer answer**) |
| `ticks` / `parallel_marks` | `(a, b, n=1, layer, size=0.12)` / `(a, b, n=1, layer, size=0.13)` |
| `arc` / `right_angle` | `(vertex, p1, p2, n=1, r=0.35, layer, gap=0.07)` / `(vertex, p1, p2, size=0.18, layer)` |
| `custom` | `(fn, layer="given", extent=None, pad_pt=0)`: `fn(ax, color)` draws with matplotlib in data units; pass `color` to every artist; frame from `extent=[(x0,y0),(x1,y1)]` or the data limits (text doesn't count); keeps layers, trim, sidecar, lint |

Labels place themselves (requested spot first, then rotated or farther spots); lines under 0.6 pt are not obstacles; `fixed=True` keeps the spot. Blocked labels and mixed prime styles (`A'` vs `A^{\prime}`) are `figs` WARN lint. Default label 13 pt. Printed pt = text pt × `fig_w` / drawn width: under 7 pt ERROR, under 8 WARN. The `.json` sidecar lists label texts (integrity reads them) and `key_width_in`.

**Geometry (`lesson_builder.figures`).** Transforms return `(N, 2)` arrays, even for one point.

| Helper | Returns |
|---|---|
| `P(*pts)` | `P((0,0),(4,0))` is (2,2); **`P((0,0))` is (1,2)**: use `P(0,0)` for one point |
| `rotate(pts, deg, about)` / `reflect(pts, p1, p2)` / `translate(pts, v)` / `dilate(pts, k, center=(0,0))` | (N,2); rotate is CCW degrees |
| `fit_rigid` / `is_rigid_image` / `needs_reflection` / `orientation` / `signed_area` | rigid copy / bool / bool / ±1 / float |
| `dist` / `midpoint` / `angle_deg(vertex, p1, p2)` / `cross2(u, v)` | float / (2,) / 0-180 / float |
| `similarity_ratio(src, img)` / `correspondence` / `congruence_statement` / `ssa_triangles` | k or None / dict / str / (long, short) |
| `is_parallel(a, b, c, d)` / `collinear(*pts)` / `on_ray(origin, through, p)` | bool (scale-free tolerances) |
| `foot(p, a, b)` / `extend(a, b, box, ray=True)` | (2,) / (2,2) clipped to `box=(x0, x1, y0, y1)` |
| `law_of_sines_side(known, opp_known, opp_want)` / `triangle_from_angles(A, B, angA, angB, above=True)` / `triangle_sas(a, b, ang_at_a, side_len, above=True)` | float / (3,2) [A, B, C] |
| `assert_dilation(center, src, img, k)` / `assert_similar(src, img, k=None)` / `assert_lengths([(a, b, label), ...], tol=0.03)` / `assert_distinct(angles, min_deg=4)` | AssertionError with the bad point or pair |
| `mark_congruent(f, groups, layer, size=0.12, r=0.35)` | ticks for segment groups `((a,b),(c,d))`, arcs for angle groups `((v,p1,p2),...)`; n counts up per group |
| `mark_parallel(f, segs, n=1, layer)` | chevrons on each `(a, b)` |
| `vertex_directions(pts)` | outward unit vector per vertex |

Templates (return `(Figure, info)` except `rotation_build`): `congruent_pair(src, names, motion, names_img, offset, marks)`, `rotation_build(tri, names, image_name)`, `reflection_build(tri, p1, p2, names, image_names=None, answer=True, marks=True, line_name=None)`, `dilation_task(pts, k, center, names, grid=None, rays=True, center_name="P", overrides=None, ray_past=0, lattice=None)`, `side_splitter(tri, t, names, split_names="DE", seg_labels=None, marks=False)`, `rect_pair(w, h, k, names=("M","N"), labels=None)`. Each asserts its own math; add `width_in`/`height_in` to size.

**Subject modules** (import from `lesson_builder.figures.<module>`; every helper takes `layer`):

| Module | Helpers |
|---|---|
| `coordinate` | `axes(f, x0, x1, y0, y1, step=1, labels_every=1, grid=True, arrows=True, names=("x","y"))` first, then `plot_points(f, pts, names, coords=False)`, `plot_line(f, m, b, x0, x1, dashed)`, `plot_fn(f, fn, x0, x1)`, `slope_triangle(f, p, q)` (returns slope), `num_label`, `fmt` |
| `numberline` | `number_line(f, lo, hi, step=1, label_every=1, y=0, minor=None)` first, then `point(f, x, open)`, `segment_interval(f, a, b, open_a, open_b)`, `ray(f, x, "left"\|"right", open)` |
| `stats` | `dotplot(f, data, lo, hi, step)`, `histogram(f, data, bins, counts)`, `boxplot(f, values, y, five=False, outliers=True)`, `scatter(f, xs, ys, line=(m, b))`, `normal_curve(f, mu, sigma, shade=(a, b))`, `five_number`, `nice_axis`, `chart_axes`, `Scale` (charts return their Scale for later marks) |
| `cs` | `array_boxes(f, values, index=True, answer={i: v}, name)`, `reference_diagram(f, vars, objects, answer=(...))` with `Ref("obj")` arrows |

Two-way tables and trace tables are YAML tables, not figures.

```python
"""3.4 figures. File stem must match lessons/3.4.yaml."""
from lesson_builder.figures import Figure, P, dilation_task, figure

S = "3.4"


@figure(f"{S}_q2")
def q2() -> Figure:
    f, info = dilation_task(P((1, 1), (3, 1), (1, 2)), 2, (0, 0), "ABC", grid=(0, 7, 0, 5))
    return f
```

## 5. What `check` catches (also run inside `build`)

| Area | ERROR | WARN |
|---|---|---|
| Answers | item/part without `answer`/`fill`/`frame`/`no_answer`; drawing prompt without key figure | |
| MC | empty or duplicate choice; "all/none of the above", "A and B"; key letter outside the choices; `key` disagrees with `[X]` in `answer` | not 3-4 choices (T/F and select-all exempt); one choice over twice the median length; a letter keys over half the items; same key 3 in a row |
| Voice (student text; list in `voice.py`) | | banned word (any form), dash in prose, exclamation point |
| Targets | unknown or duplicate target id | assessment target with no items; all `demand` mem/pwoc |
| Refs | unknown `{ref:x}`; "Problem N" missing in its group; `selected` number not a practice item | "Problem N" in `plan`/`guide_notes` not in the document |
| Text | odd `$`; `___` | `$3 and $5` money-as-math; `''` in a block scalar; `TODO` left in; `header_right` |
| Layout | box under 0.9 in; minutes over budget; points ≠ `total_points`; unknown figure name; print under 7 pt; pages over budget; student/key page count or item numbers differ; red on student copy | print under 8 pt; colour or under 150 dpi asset |
| Bundle | retained PNG missing or not matching the DOCX image (build/`retain`) | |

## 6. Math in document text (`$...$` to Word OMML)

Supported: `\overline{}` `\overleftrightarrow{}` `\overrightarrow{}` `\text{}` `\frac{}{}` `\dfrac` `\tfrac` `\sqrt{}`, `^` `_` `'`, and `\triangle \angle \cong \sim \parallel \perp \circ \to \leftrightarrow \ldots \cdot \times \div \pm \neq \approx \le \ge \infty \theta \pi \ell \square \sin \cos \tan \left \right \colon \prime \quad \, \ `. Anything else (`\alpha`, `\mathrm`, `\%`, `\$`, `\ne`, `\leq`) fails the build. Spaces in math are dropped: use `\ ` or `\text{two words}`. `^\circ` prints °. Outside math: `**bold**`, `*italic*`. Primes: write `A'` in the final string (superscript prime; figures print U+2032).

## 7. Pitfalls

- **YAML primes:** in `'single quotes'` write `''` for one `'` (`'$A''B''$'`). In `|`/`>` blocks and plain scalars `''` stays two marks and prints a double prime (check WARN); write `A'`.
- **Quoting:** single-quote anything with `\` (`"\frac"` becomes a form feed). Quote values with `: `, ` #`, or a leading `[ { * - & ! % @ | >` or backtick (`answer: [B] reason` fails to parse; use `key: B`).
- **Money:** write "3 dollars". `\$` is not an escape: it still counts as `$` and crashes the build (the check message no longer suggests it).
- `np.cross` on 2-D vectors raises in numpy 2.5: use `cross2(u, v)`. `rotate(B, 180, about=M)` is (1,2): take `[0]`.
- A figure function must return a `Figure`. No answer layer means no `_key.png`; the key shows the student image.
- The figure cache watches the figure file, its `_*.py` siblings, the library, and `assets/`. `figs --force` only after editing something else a figure reads.
- Writes ≤ ~150 lines per call; edit tool, not PowerShell `-replace`; scratch scripts in `_temp/build/`, not `python -c`.

---
name: curriculum-visual-generator
description: Draws figures for lesson-builder lessons and assessments (geometry diagrams, coordinate grids, number lines, simple stats and CS diagrams) as @figure functions in figures/<stem>.py, with a black given layer for students and a red answer layer for keys. Covers the figure plan, library helpers, the `lesson-builder figs` loop, source-image rules, and figure retention. Use for the Figures step of any lesson-builder document.
---

# Curriculum visual generator

Figures for lesson-builder documents are Python functions, not image files. One function draws the student copy (given layer) and the key (given + answer layer) on the same canvas, so they always line up. Design reference: `docs/lesson_builder.md`. Full signatures and pitfalls: `.agents/skills/lesson-builder/references/api_cheatsheet.md`.

## When to use

- The "Figures" step of a document (see `.agents/skills/lesson-builder/references/orchestration.md`). Input: the figure plan in `_temp/specs/<stem>/requirements.md` (items, coordinates, values to assert). Output: `figures/<stem>.py` and a clean `figs` run. No document builds in this step.
- Any time a lesson or assessment needs a new drawing, an answer drawing for a key, or a redraw of a weak source image.
- If subagents aren't available, run the same step in the same session with the same files.

## Where things live

- Unit folder: `units/<course>/<unit-slug>/`. Lessons `lessons/<id>.yaml`, assessments `assessments/<stem>.yaml`.
- Figures for one document: `figures/<stem>.py`, where stem is the YAML file stem. It loads only when that document is built or checked.
- Helpers used by several figure files in this unit: `figures/_helpers.py` (`from _helpers import ...`). Files starting with `_` are never treated as documents. A legacy shared `figures.py` in the unit root still loads for every document.
- Reused source images: copy from `_temp/ingest/<src>_media/` into `assets/<lesson-or-stem>/` and reference the path in the YAML (`figure: assets/3.4/fig2.png`). They must be black and white and at least 150 dpi at the printed `fig_w`; otherwise redraw them.

## Writing `figures/<stem>.py`

```python
"""Unit 3 Test A figures. Given layer = student copy, answer layer (red) = key."""
from lesson_builder.figures import Figure, P, dilate, figure, similarity_ratio

S = "Unit 3 Test A"

A, B, C = P((0, 0), (3, 0), (1, 2))
A2, B2, C2 = dilate([A, B, C], 2, center=(0, 0))
assert abs(similarity_ratio([A, B, C], [A2, B2, C2]) - 2) < 1e-9


@figure(f"{S}_q3")
def q3() -> Figure:
    f = Figure(width_in=2.6, height_in=2.0)
    f.poly([A, B, C])
    f.dots([A, B, C])
    f.label_poly([A, B, C], "ABC")
    f.poly([A2, B2, C2], layer="answer")
    f.label_poly([A2, B2, C2], ["A'", "B'", "C'"], layer="answer")
    return f
```

- Name every figure `f"{S}_<item>"` (`_q3`, `_warmup`). Names are global within a unit; the prefix prevents clashes with the shared `figures.py`. `scaffold` writes the file with `S` set.
- The YAML refers to the name: `figure: Unit 3 Test A_q3`, `key_figure:`, or `draw.key_figure:`. An unknown name is a check ERROR.
- Student work goes on `layer="answer"`. Every drawing task needs a key figure; `check` errors without one. When the answer reaches past the given drawing, use `Figure(..., key_frame="union")`: the key canvas grows to fit the answer at the same scale. Don't make a separate `_key` figure.
- Assert the math at module level or in the function: lengths match the labels, angles the key calls different look different, the image really is the motion's image. Derive answers from the same points the figure uses.
- Scaled rectangles can use checked YAML data directly: `from lesson_builder.resolve import model_for_figure` and `from lesson_builder.figures.comparison import scaled_rectangles`; return `scaled_rectangles(model_for_figure(__file__, item_id))`. The model computes dimensions and labels from the same givens used by the document's `{value:item_id.fact}` references. Its YAML is a cache dependency. Use shared `comparison.split_triangle`, `line_family`, and `parallel_names` for the corresponding comparison diagrams.
- Colours are fixed by the library: given is black, answer is red `#C00000` and appears only on keys. Do not pass colours or palettes. `fill=` and `hatch=` on `poly` are for gray or hatch shading only.
- One scale for x and y (equal aspect). `width_in` / `height_in` set the drawn size. Leave `fig_w` out of the YAML so the figure prints at its drawn size, or use `fig: small|medium|wide` (1.6 / 2.4 / 3.4 in).
- Output is 300 DPI and trimmed automatically. No `savefig`, cropping, or manual file paths.

## Labels

- Labels place themselves. Give the preferred side with `direction=` (or let `label_poly` use the outward direction). If that spot touches a line, dot, arrow, or label, the nearest clear spot is used, and student and key share the result.
- `fixed=True` keeps a spot exactly as written. Use it only when the auto spot is wrong for the math (for example a label that must sit inside a region).
- Never nudge offsets by hand or write fix scripts. A label that still touches something means the figure is too crowded: enlarge it, raise `fig_w`, or move points apart.
- Grid lines from `f.grid(...)` are thin enough that labels may sit on them.
- Use one prime style per file (`A'`); mixed styles are `figs` lint.

## The figure loop

1. `uv run lesson-builder figs units/<course>/<unit-slug> -l <stem>` (seconds, no Word).
2. Fix every ERROR and every label warning ("touches a line"). Printed text under 7 pt is an error; the message gives the `fig_w` that reaches 9 pt.
3. Open `_temp/figures/<stem>_sheet.png`: each figure at print size, student and key side by side, with its smallest text size. Check the student copy shows no answer and the key matches the problem.
4. Repeat until 0 errors and no label warnings. Then hand off to the YAML/build step.

The cache re-renders when the figure file, a `figures/_*.py` helper, the library, or a file in `assets/` changes. `--force` is rarely needed.

## Library helpers (use these, not local copies)

From `lesson_builder.figures` (`geometry.py`; signatures in the cheat sheet):

- Points and measures: `P`, `dist`, `midpoint`, `angle_deg`, `cross2`, `orientation`, `signed_area`, `vertex_directions`.
- Motions: `translate`, `rotate`, `reflect`, `dilate`, `fit_rigid`.
- Predicates and constructions: `is_parallel`, `collinear`, `on_ray`, `foot`, `extend` (ray or line clipped to a box), `triangle_from_angles`, `triangle_sas`, `law_of_sines_side`.
- Checks: `is_rigid_image`, `similarity_ratio`, `needs_reflection`, `correspondence`, `congruence_statement`, `ssa_triangles`.
- Asserts (fail `figs` with the bad point or pair): `assert_dilation(center, src, img, k)`, `assert_similar(src, img, k)`, `assert_lengths([(a, b, label), ...])`, `assert_distinct(angles, min_deg=4)`.
- Marks: `mark_congruent(f, groups)` (ticks for segment groups, arcs for angle groups), `mark_parallel(f, segs, n)`.
- Templates (each asserts its own math, returns `(Figure, info)`): `congruent_pair`, `reflection_build`, `dilation_task` (grid, rays, primed image on the answer layer), `side_splitter`, `rect_pair`; `rotation_build` returns a Figure.

`Figure` drawing methods: `poly`, `seg`, `dots`, `grid`, `label`, `label_poly`, `side_label`, `angle_label`, `text`, `ticks`, `parallel_marks`, `arc`, `right_angle`, `arrow` (defaults to `layer="answer"`, dashed), `custom`.

If a figure needs a reusable helper that doesn't exist, don't build a private version for one unit. Only the orchestrator edits `src/`. Log one line in `_temp/specs/<stem>/changes.md`:

`GAP: src/lesson_builder/figures/<subject>.py:<feature>: <symptom> | <workaround used>`

## Other subjects (coordinate planes, number lines, stats, CS)

Import from the subject module; every helper takes `layer`, so answers go red on the key:

- `lesson_builder.figures.coordinate`: `axes(f, x0, x1, y0, y1, step)` first, then `plot_points`, `plot_line(f, m, b)`, `plot_fn(f, fn)`, `slope_triangle(f, p, q)`.
- `lesson_builder.figures.numberline`: `number_line(f, lo, hi, step)` first, then `point(f, x, open)`, `segment_interval`, `ray(f, x, "right", open)`.
- `lesson_builder.figures.stats`: `dotplot`, `histogram`, `boxplot`, `scatter(f, xs, ys, line=(m, b))`, `normal_curve(f, mu, sigma, shade=(a, b))`, `five_number`. Charts return their `Scale`; use it for later marks. Record any random seed.
- `lesson_builder.figures.cs`: `array_boxes(f, values, answer={i: v})`, `reference_diagram(f, vars, objects, answer=...)` with `Ref("obj")` arrows. Keep code listings out of figures.
- Two-way tables and trace tables are YAML tables, not figures.

For anything else, `f.custom(fn, layer)` gives a matplotlib axes in data units: `fn(ax, color)` must pass `color` to every artist (keep given ink black or gray). It keeps layers, trimming, sidecars, and lint. Pass `extent=[(x0, y0), (x1, y1)]` if the drawing is only text. A chart that several units need still belongs in a subject module (GAP line).

## Retention

Automatic. `lesson-builder build` copies the PNGs each document uses (and reused `assets/` images) to `output/figures/<stem>/`, writes a README mapping item → figure → `figures/<stem>.py:function` with helpers and regeneration commands, and verifies the copies against the built DOCX. Check the build's `figures retained` line; an ERROR there means a figure has no source or the bundle is stale (rebuild).

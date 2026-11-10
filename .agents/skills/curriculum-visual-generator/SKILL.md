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

- Name every figure `f"{S}_<item>"` (`_q3`, `_q3_key`, `_warmup`). Names are global within a unit; the prefix prevents clashes with the shared `figures.py`.
- The YAML refers to the name: `figure: Unit 3 Test A_q3`, `key_figure:`, or `draw.key_figure:`.
- Student work goes on `layer="answer"`. Every drawing task needs a key figure; `check` errors without one.
- Assert the math at module level or in the function: lengths match the labels, angles the key calls different look different, the image really is the motion's image. Derive answers from the same points the figure uses.
- Colours are fixed by the library: given is black, answer is red `#C00000` and appears only on keys. Do not pass colours or palettes. `fill=` and `hatch=` on `poly` are for gray or hatch shading only.
- One scale for x and y (equal aspect). `width_in` / `height_in` set the drawn size; the YAML `fig_w` sets the printed size.
- Output is 300 DPI and trimmed automatically. No `savefig`, cropping, or manual file paths.

## Labels

- Labels place themselves. Give the preferred side with `direction=` (or let `label_poly` use the outward direction). If that spot touches a line, dot, arrow, or label, the nearest clear spot is used, and student and key share the result.
- `fixed=True` keeps a spot exactly as written. Use it only when the auto spot is wrong for the math (for example a label that must sit inside a region).
- Never nudge offsets by hand or write fix scripts. A label that still touches something means the figure is too crowded: enlarge it, raise `fig_w`, or move points apart.
- Grid lines from `f.grid(...)` are thin enough that labels may sit on them.

## The figure loop

1. `uv run lesson-builder figs units/<course>/<unit-slug> -l <stem>` (seconds, no Word).
2. Fix every ERROR and every label warning ("touches a line"). Printed text under 7 pt is an error; the message gives the `fig_w` that reaches 9 pt.
3. Open `_temp/figures/<stem>_sheet.png`: each figure at print size, student and key side by side, with its smallest text size. Check the student copy shows no answer and the key matches the problem.
4. Repeat until 0 errors and no label warnings. Then hand off to the YAML/build step.

Edits to `figures/_helpers.py` do not invalidate the figure cache; run `figs ... --force` (or `build ... --force-figures`) after changing helpers.

## Library helpers (use these, not local copies)

From `lesson_builder.figures` (`geometry.py`):

- Points and measures: `P`, `dist`, `midpoint`, `angle_deg`, `orientation`, `vertex_directions`.
- Motions: `translate`, `rotate`, `reflect`, `dilate`, `fit_rigid`.
- Checks: `is_rigid_image`, `similarity_ratio`, `needs_reflection`, `correspondence`, `congruence_statement`, `ssa_triangles`.
- Templates: `congruent_pair` (two marked congruent figures plus correspondence info), `rotation_build` (triangle to parallelogram by a 180° turn).

`Figure` drawing methods: `poly`, `seg`, `dots`, `grid`, `label`, `label_poly`, `side_label`, `angle_label`, `text`, `ticks`, `parallel_marks`, `arc`, `right_angle`, `arrow` (defaults to `layer="answer"`, dashed).

If a figure needs a reusable helper that doesn't exist (scale asserts, axes with tick numbers, a box plot), don't build a private version for one unit. Only the orchestrator edits `src/`. Log one line in `_temp/specs/<stem>/changes.md`:

`GAP: src/lesson_builder/figures/<subject>.py:<feature>: <symptom> | <workaround used>`

## Other subjects (stats, number lines, CS diagrams)

`Figure` has no public matplotlib axes; everything goes through its drawing methods. That is enough for simple visuals:

- Number line: `seg` for the line, `ticks` or short `seg`s for marks, `text` for numbers, `dots` for points, `arrow` with `layer="given", dashed=False` for ends.
- Dot plot, box plot, bar chart, histogram: `poly` boxes and bars, `seg` whiskers and axes, `text` for scale numbers and axis titles. Map data values to drawing units yourself (equal aspect), and assert the drawn values match the data. Record any random seed.
- Flowcharts and memory diagrams: `poly` boxes, `text` inside, `arrow(..., layer="given", dashed=False)`. Keep code listings out of figures.

Anything beyond that (real axes, many data points, scatterplot regression lines) needs a helper module `src/lesson_builder/figures/<subject>.py` with tests, which is an orchestrator task. Log a GAP line. A standalone matplotlib script does not work as a stopgap inside `figures/`: every non-`_` file there is loaded as a document's figure file and each `@figure` must return a `Figure`. If the orchestrator approves a temporary image, save the script in `_temp/build/`, write a B&W PNG at 300 DPI into `assets/<stem>/`, and reference it as an asset (it then gets the colour and resolution checks, but no answer layer).

## Retention

After the final build, copy the PNGs the document uses into `output/figures/<stem>/`:

- From `_temp/figures/<stem>/` (`<name>.png` student, `<name>_key.png` key) and from `_temp/figures/` for shared `figures.py` figures. Include reused `assets/` images.
- Add `README.md` mapping each item number to the registered figure name, the source file and function (`figures/<stem>.py`, `q3`), helper files (`figures/_helpers.py`, library modules), any data or seeds, and asset source paths/pages.
- Record the regeneration command, run from the repo root: `uv run lesson-builder figs units/<course>/<unit-slug> -l <stem>`.
- Refresh the copies after every figure fix so they match the final documents. This step is manual for now.

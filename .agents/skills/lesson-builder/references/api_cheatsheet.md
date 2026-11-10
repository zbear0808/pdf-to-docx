# lesson-builder API cheat sheet

Checked against `src/lesson_builder/` (spec, cli, check, docbuilder, render, figures/*). If this sheet and the code disagree, the code wins.

## 1. Commands (repo root, `uv run lesson-builder ...`)

| Command | Flags |
|---|---|
| `new-unit DEST --course C --unit N --title T [--period P]` | DEST must be empty or missing |
| `ingest SRC... -o OUT [--no-render]` | SRC = files or folders (*.docx, *.pdf) |
| `figs UNIT [-l STEM]... [--no-sheet] [--force]` | figures only, lint, print size, `_temp/figures/<stem>_sheet.png` |
| `build UNIT [-l STEM]... [--strict] [--force-figures] [--no-packets] [--no-fit]` | `--strict` skips docs with spec errors; packets only when no `-l` |
| `check UNIT [-l STEM]... [--no-outputs]` | spec checks + PDF checks of existing output |
| `check-pdfs STUDENT.pdf KEY.pdf [--max-pages 3]` | any student/key pair |
| `packet UNIT` | rebuild duplex packets from existing outputs |

`-l` matches the YAML file stem or the `id`, and you can repeat it. Exit code 1 means errors.

## 2. Unit layout

```text
unit.yaml                 course, unit, unit_title, period, budget{minutes:40, handout_pages:3, practice_pages:2},
                          lessons: [3.1.yaml, ...] (teaching order), assessments: [assessments/*.yaml], figures: figures.py
lessons/<id>.yaml         one per lesson
assessments/<stem>.yaml   one per version (A, B, Retake), doc_type assessment | reference
figures.py                shared figures (optional), seen by every document
figures/<stem>.py         per-document figures; <stem> = YAML file stem exactly ("Unit 3 Test A.py")
figures/_helpers.py       files starting with _ are not documents. Import with `from _helpers import ...`
assets/                   image files; reference as `figure: assets/x.png` (relative to the unit dir)
_temp/figures/<stem>/     <name>.png (student), <name>_key.png (only if there is an answer layer), <name>.json (meta)
output/Lesson <id>/       Student Handout, Lesson Key, Practice Problems, Practice Key, Teacher Guide (.docx/.pdf)
output/Assessments/       <id>.docx, <id> Key.docx, <id> Teacher Notes.docx (only if plan or guide_notes)
output/Reference/         <id>.docx (no key)
```

A document can use the names registered in `figures.py` plus the names in its own `figures/<stem>.py`. If both have the same name, its own file wins. Convention: `@figure("<stem>_name")`.

## 3. YAML quick reference (unknown keys are errors: `extra="forbid"`)

**LessonSpec:** `id` (str) | `doc_type` lesson*/assessment/reference | `title` | `notes_title`, `framing` (both REQUIRED for lessons) | `materials` | `directions` (bold line) | `header_right` | `total_points` (must equal the sum of item + part points) | `max_pages` | `sections` | `quicknotes: [str]` | `notes_height` 2.2 | `practice` | `plan` (md) | `guide_notes` (md)

**Section:** `kind` warmup/together/partner/notes/cyu/exit/plain | `title` | `sub` | `intro` | `box` (str or list: word/move bank) | `items` | `page_break_before`.
`notes` starts a new page with notes_title + QuickNotes. Its `items` are ignored, and numbering restarts after it. `plain` has no heading.

**Item** (default after `=`):

| Field | Default | Notes |
|---|---|---|
| `n` | None | "1" prints "1."; None = unnumbered |
| `minutes` / `points` | 0 / None | lessons: minutes sum must be ≤ budget; points print "(2 pts)" |
| `prompt` | "" | str or list; later lines starting `a. `, `[A] `, `Step 1: `, `- ` get a hanging indent or bullet |
| `figure` / `key_figure` / `fig_w` | None | registered name or path; key uses `key_figure` or the figure's answer layer; fig_w None = drawn width |
| `layout` | side | `stacked` = image under the text |
| `choices` / `choice_cols` | None / 1 | at most 10 (A-J) |
| `answer` | None | str or list. MC: `'[B] one-line reason'` |
| `work` | 0.8 | blank inches. Becomes 0 when fill/frame/box/parts is set and you don't set `work`. Set `work: 0` for MC or tables |
| `fill` / `fill_cols` / `box_w` | None / all in one row / 1.3 | `[['$x =$', '15'], ['Scale factor:', '2']]` |
| `frame` / `frame_box_w` | None / 1.1 | rows `[before, answer, after]` or `[before, answer, after, box_w]` |
| `box` | None | bordered write-in box height; the key prints the answer inside it |
| `table` / `columns` / `draw` | None | see below |
| `parts` | [] | each part needs its own answer |
| `after` / `page_break_after` / `no_answer` | 0.08 / false / false | |

**Part:** `label` ("a.") required | `prompt` required | `points` | `choices`, `choice_cols` | `answer` | `work` **0.6** | `fill`, `fill_cols`, `box_w` 1.3 | `frame`, `frame_box_w` 1.1 | `no_answer`.

**Table** (arrow table): `header: ['Vertex', '$A$', '$B$']`, `answers: ['$D$', '$E$']` (one fewer than header), `row_label` "Lands on", `first_w` 1.45, `height` 0.42.
**Columns:** `headers: [I notice..., I wonder...]`, `answers: [['..'], ['..']]` (a list per column), `height` 0.85, `italic` false.
**Draw:** `height` 3.0, `steps_w` 3.05, `key_figure`, `key_fig_w` 2.5, `key_note`. Steps go on the left and the drawing box on the right.
**Practice:** `title`, `rows: [{cells: [Item, Item?], heading?, page_break_before?}]`, `selected: [[1, Answer], ...]`, `font_size` 10.5. Practice cells render prompt, figure, choices, fill, frame, box, parts and answer. They ignore `draw`, `table` and `columns`.

## 4. Figures API (`from lesson_builder.figures import ...`)

`Figure(width_in, height_in, name=None)` sets the canvas size. x and y use one shared scale, so figures are drawn to scale. `layer="given"` draws black ink on the student copy and the key. `layer="answer"` draws red ink on the key only. Student and key images share the same frame. Sizes for ticks, arcs and right-angle marks are in **data units**. `offset_pt` and `size` are in points.

| Method | Signature (defaults) |
|---|---|
| `poly` | `(pts, closed=True, layer, lw=None, dashed=False, fill=None, hatch=None)` |
| `seg` / `dots` / `grid` | `(a, b, layer, lw, dashed)` / `(pts, layer, size=14)` / `(x0, x1, y0, y1, step=1, lw=0.3, layer)` |
| `label` | `(pt, text, layer, direction=None, center=None, offset_pt=10, size=None, italic=True, fixed=False)`. Text is wrapped in `$..$` when italic. With no direction and no center it goes up |
| `label_poly` | `(pts, names, layer, overrides=None, offset_pt=10)`. names is `"ABC"` or a list (None skips a vertex). overrides is `{name: direction}`. It points outward from each vertex |
| `side_label` | `(a, b, text, center, layer, offset_pt=10, italic=False, size=None, fixed=False)`. It sits on the side away from `center` |
| `angle_label` | `(vertex, p1, p2, text, dist=None, layer, size=None, fixed=False)`. Text is raw, so write `'$40^\circ$'`. Default size is 11 |
| `text` | `(pt, s, layer, size=None, fixed=False)` |
| `ticks` / `parallel_marks` | `(a, b, n=1, layer, size=0.12)` / `(a, b, n=1, layer, size=0.13)` |
| `arc` / `right_angle` | `(vertex, p1, p2, n=1, r=0.35, layer, gap=0.07)` / `(vertex, p1, p2, size=0.18, layer)` |
| `arrow` | `(a, b, layer="answer", dashed=True)`. **Default layer is answer** |

Label placement: the requested spot is tried first. If it touches a line, a dot, another label or the edge, the builder tries rotated or farther spots. Lines thinner than 0.6 (grid lines) are not obstacles. `fixed=True` keeps the requested spot. Labels that are still blocked show up as `figs`/`check` WARN lint. Default label size is 13 pt. Printed pt = text pt × `fig_w` / drawn width. Below 7 pt is an ERROR, below 8 pt a WARN.

**Geometry helpers.** The transforms always return an `(N, 2)` array, even for one point.

| Helper | Returns |
|---|---|
| `P(*pts)` | `P((0,0),(4,0))` gives (2,2). **`P((0,0))` gives (1,2), so use `P(0,0)` or `np.array((0,0), float)` for one point** |
| `rotate(pts, deg, about=(0,0))` / `reflect(pts, p1, p2)` / `translate(pts, v)` / `dilate(pts, k, center=(0,0))` | (N,2). rotate is counterclockwise in degrees; reflect is across line p1p2 |
| `fit_rigid(src, dst_approx, allow_reflection=True)` | (N,2) rigid copy closest to dst |
| `dist(a, b)` / `midpoint(a, b)` / `angle_deg(vertex, p1, p2)` | float / (2,) / float in 0-180 |
| `similarity_ratio(src, img, tol=1e-6)` | k or None |
| `is_rigid_image(src, img)` / `needs_reflection(src, img)` / `orientation(pts)` | bool / bool / ±1 |
| `correspondence("ABC", "DEF")` / `congruence_statement(src, img, order)` | `{'A':'D',..}` / e.g. `("ABC","FED","BCA")` gives `"EDF"` |
| `ssa_triangles(adj, opp, angle_deg)` | `(long, short)` triangles [V, W, U]. Raises ValueError if there is no ambiguous case |
| `vertex_directions(pts)` | outward unit vector at each vertex |
| `congruent_pair(src_pts, names_src, motion, names_img, offset=(0,0), marks=True, width_in=5.5, height_in=2.4)` | `(Figure, {image_pts, correspondence, needs_reflection})`. marks can be True, "answer" or False |
| `rotation_build(tri_pts, names="ABC", image_name="D", width_in=3.0)` | Figure (completes a parallelogram by a 180° turn) |

```python
"""3.4 figures. stem must match lessons/3.4.yaml."""
import numpy as np
from lesson_builder.figures import Figure, P, dilate, figure, similarity_ratio

ABC = P((0, 0), (2, 0), (0, 1))
IMG = dilate(ABC, 2, center=(-1, -1))
assert np.isclose(similarity_ratio(ABC, IMG), 2)      # check the math before drawing


@figure("3.4_dilate")
def dilate_fig() -> Figure:
    f = Figure(width_in=2.4, height_in=2.0)
    f.poly(ABC); f.dots(ABC); f.label_poly(ABC, "ABC")
    f.poly(IMG, layer="answer"); f.label_poly(IMG, ["A'", "B'", "C'"], layer="answer")
    return f
```

## 5. Math in document text (`$...$`, converted to Word OMML)

Supported commands: `\overline{}` `\overleftrightarrow{}` `\overrightarrow{}` `\text{}` `\frac{}{}` `\dfrac` `\tfrac` `\sqrt{}` (no index), plus `^` `_` `'` and these symbols:
`\triangle \angle \cong \sim \parallel \perp \circ \to \leftrightarrow \ldots \cdot \times \div \pm \neq \approx \le \ge \infty \theta \pi \ell \square \sin \cos \tan \left \right \colon \prime \quad \, \ `.
Any other command (`\alpha`, `\mathrm`, `\%`, `\{`, `\$`, `\ne`, `\leq`) raises `ValueError: unknown latex command` at build. Spaces inside math are dropped, so use `\ `, `\quad` or `\text{two words}`. `-` prints as a minus sign. `^\circ` and `^{\circ}` print as °. Outside math, `**bold**` and `*italic*` work.
Primes: write `A'` (or `A''` for a double prime) in the final string. It becomes a superscript prime, and a plain glyph under a bar. In figures, `$A'$` and `label(p, "A'")` print U+2032. A `'` outside `$..$` (for example a non-italic `side_label`) stays a straight apostrophe.
Figure labels use matplotlib mathtext, not this subset.

## 6. Pitfalls (each one checked against the code)

- **YAML primes:** in `'single quotes'` write `''` for one `'`: `'$\triangle A''B''C''$'`. In `|` or `>` block scalars and in plain scalars, `''` stays two characters and prints a **double prime**. Write `A'` there.
- **YAML quoting:** use single quotes for anything with `\`. In double quotes `"\frac"` becomes a form feed + `rac`, and `"\cong"` is a parse error. Quote any value that contains `: ` or ` #` (the rest becomes a comment), or that starts with `[`, `{`, `*` (`*italic*` reads as an alias), `-`, `&`, `!`, `%`, `@`, `|`, `>` or a backtick. An unquoted `answer: [B] reason` fails to parse.
- **Money:** an odd number of `$` in one string is a check ERROR. Two amounts (`$3 and $5`) pass the check but render as math. `\$` is **not** an escape: it still counts toward the `$` total and crashes the build (the check message wrongly suggests it). Write "3 dollars".
- **No `___` blanks** (ERROR). Use `fill`, `frame` or `box`. `box_w` and frame box widths must be ≥ 0.9 in (ERROR). The 4th frame element overrides the width for one row.
- **Every item/part needs** `answer`, `fill`, `frame`, `table`, `columns` answers, `draw` or `no_answer: true` (an item with parts only needs answers on its parts). Reference docs are exempt.
- A prompt that says draw/sketch/construct/mark/shade/plot/graph needs a key figure (`key_figure`, `draw.key_figure`, or a figure with an answer layer). The exception is a prompt that says "if it helps" or "optional".
- **"Problem N" in text** must exist in the same numbering group (before notes / after notes / practice).
- Lessons: item minutes must sum to ≤ `budget.minutes`, and the plan table rows `| a-b |` must end ≤ budget.
- `np.cross` on 2-D vectors raises ValueError (numpy 2.5). Use `u[0]*v[1] - u[1]*v[0]`.
- `rotate(B, 180, about=M)` returns (1,2), so take `[0]` before using it as a point. Passing `P((x,y))` to `label` crashes ("shape (N, 2)").
- The figure cache only compares the doc's figure file and the library. **Editing `_helpers.py` or `assets/` does not re-render:** use `figs --force` / `build --force-figures`.
- A figure function must return a `Figure` (TypeError otherwise). If there is no answer layer, no `_key.png` is written and the key shows the student image.
- Workspace: keep each file write ≤ ~150 lines (write in pieces; large single writes crashed agents). Edit files with the edit tool, never with PowerShell `-replace` or `Set-Content`. Put scratch scripts in `_temp/build/`, not in `python -c`.

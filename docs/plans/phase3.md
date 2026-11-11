# Phase 3: page estimate, Word pool, incremental builds, new item types, model checks

Goal: the costly or risky items, chosen using Phase 2 pilot data. Each item starts with a go/no-go check against that data; skip anything the data says isn't needed.

| # | Item | Effort | Go if (from Phase 2 data) |
|---|---|---|---|
| 1 | D2 incremental builds + builder freeze | M | full-unit rebuilds still > 5 min or any mid-wave breakage |
| 2 | D1 page estimate picks the scale | M-L | fit rounds per build still > 1.3 |
| 3 | F8 `grid`, `tf`, column widths, list styles, header fields, template frames | M | any "layout can't do this" finding |
| 4 | B3 computed answers (`answer_expr`, `values`) | M | any wrong-number finding or scratch math script |
| 5 | B2 correspondence check from figure models | M-L | any correspondence Must |
| 6 | F5b Word process pool | M-L | full-unit build > 300 s after 1-2 |
| 7 | E2 wave automation | M | orchestrator tokens per doc still high |

Order: D2 first (it guards the rest), D1 next (reuses A4's estimator), then the item-type and answer work (3-5, which add patterns), then the pool and automation, which are easiest to judge once everything else is stable.

---

## 1. D2 incremental builds + builder freeze
**Change.** `cli.build`: per-doc key = hash(YAML, figure file, unit defaults, `decisions.md`, builder version from `importlib.metadata`). Skip build when key matches the last passing `build` event; `--all` overrides. Wave freeze: `cli wave start|end` writes `_temp/specs/wave.lock` with the builder version; `build` errors if the version changed during a wave unless `--allow-builder-change`.
**Tests.** unchanged doc skipped; edited figure rebuilds; version change during a locked wave errors.
**Accept.** No full-unit failure from a mid-wave builder change.
**Risk.** Missed dependency (shared helper module); include all imported figure helper files in the hash.

## 2. D1 page estimate picks the scale
**Change.** `pagefill.estimate` (from Phase 2 A4) returns pages at a given scale; `fit.build_lesson` solves for the largest scale estimated to fit, starts there (unless F4 `fit.json` is newer), confirms with one export. Calibrate residuals per doc type from `events.jsonl`.
**Tests.** estimate within ±0.25 page on all patterns and the Unit 4 rebuild.
**Accept.** Average export rounds per build ≤ 1.2.
**Risk.** Estimate drift after F10 changes; recalibrate on each builder release.

## 3. F8 new item types
**Change.** `spec.py`: `Grid` (rows, cols, widths, blank cells, header), `TF` (statements, answers), `Columns.widths: list[float]`, `Part.list_style: "1)"|"i."|"a."`, `LessonSpec.header.fields`, `Frame.template` (e.g. `tan(□°) = □/□` mapped to blanks). Renderers in `render.py` (`_grid`, `_tf`) on `docbuilder` table helpers. Key and student share slot sizes. `check` validates sizes and answers per blank.
**Patterns.** Replace the `true-false` workaround; add `data-table`, `template-frame`.
**Tests.** render + drift checks for each; integrity fingerprints include grid answers.
**Accept.** 0 "layout can't do this" findings.

## 4. B3 computed answers
**Change.** `Part/Item.answer_expr` + `round`; safe evaluator (`ast` whitelist: numbers, + - * / **, sin cos tan asin acos atan in degrees, sqrt, figure values via `fig("name").value("x")` from sidecar). `check_spec`: compare to `answer` or fill it. `cli values <unit> <stem>` prints all.
**Patterns.** Update `find-side`, `find-angle`, `similar-correspondence`.
**Tests.** evaluator safety (no names, no attributes outside whitelist); rounding mismatch error.
**Accept.** 0 wrong-number findings; no scratch math scripts.

## 5. B2 correspondence check
**Change.** Figure sidecars declare points, right angles, and `similar`/`congruent` pairs (`figures/core.py` helpers). Key claims (`claim: {similar: [ABC, DEF]}`, `opposite: {angle: A, side: BC}`) checked in `check.check_figures` against coordinates; reuse `integrity.correspondences` to parse text claims.
**Tests.** right/wrong vertex order; opposite side.
**Accept.** 0 correspondence Musts.
**Risk.** Authoring overhead; claims optional, but required in the `similar-correspondence` pattern.

## 6. F5b Word process pool
**Change.** `export.py`: `WordPool(n=2..3)` of `WordSession`s, each in its own process (`multiprocessing`, spawn) with its own temp dir and owned PID; `cli build --jobs N`. Default stays 1.
**Tests.** Word-marked: 3 docs on 2 workers → same PDFs (hash) as serial.
**Accept.** Full-unit build ≤ 300 s; 0 COM failures over 3 full builds.
**Risk.** COM instability under load; keep `--jobs 1` as default and fall back on any COM error.

## 7. E2 wave automation
**Change.** `cli wave <unit> --step brief|figs|build|check`: runs the step for all ready docs (from `status.unit_status`), writes `_temp/specs/wave.md` (table: doc, result, next action, who), checkpoints via E3.
**Accept.** Orchestrator tokens per doc down 30% versus the Phase 2 pilot.

---

## Verification
1. `uv run pytest` with Word tests; all patterns (including new ones) build with 0/0.
2. Rebuild Unit 4 and the Phase 2 pilot unit from scratch with `--jobs 2`; compare PDFs to serial builds.
3. Pilot: the unit after the Phase 2 pilot.
4. Compare:

| Metric | Unit 4 | Phase 3 target |
|---|---|---|
| Builds per doc | ~5 | ≤ 2.5 |
| Failed builds | 26% | ≤ 5% |
| Fit-loop share of build time | 69% | ≤ 10% |
| Fix-round cost | +57% | ≤ +20% |
| Typical lesson build | ~40 s | ≤ 12 s |
| Full-unit build | 723 s | ≤ 300 s |

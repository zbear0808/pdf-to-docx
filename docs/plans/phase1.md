# Phase 1: stop the loops, faster builds, strict checks, first patterns

Goal: before the next unit, remove the biggest time sinks and silent failures, and give writers starting points that already pass. Everything is small (S) unless marked. Order is chosen so each item only depends on items above it.

| # | Item | Effort | Depends on |
|---|---|---|---|
| 1 | F6 phase timing + `events.py` | S | none |
| 2 | C1 fit loop stops when pinned | S | 1 |
| 3 | F2a export only what the fit needs (guide once, pymupdf count, final-round report, changed PNGs) | S | 2 |
| 4 | F1 one Word session, owned PID, build lock | S | 3 |
| 5 | F4 start at last good scale | S | 2 |
| 6 | F5a skip export for unchanged DOCX | S | 4 |
| 7 | A3 math dry run in `check` | S | none |
| 8 | A2 strict schema | S-M | none |
| 9 | B5 honest `figs` lint | S | none |
| 10 | G1 first 6 patterns + test + `pattern` CLI | S-M | 7, 8, 9 |
| 11 | E1 audit IDs in `status` | S | none |
| 12 | C4 build budgets | S | 1 |
| 13 | E3 checkpoint/resume | S | 1 |
| 14 | E4 `caught_by` telemetry | S | 1, 11 |

Speed items (1 to 6) come first because every later item is tested by building, so they make the rest of the phase cheaper.

---

## 1. F6 phase timing + `src/lesson_builder/events.py`
**Goal.** Measured build phases, and one place the CLI writes events (today `events.jsonl` is written only by the orchestrator).
**Change.** New `events.py`: `log_event(unit_dir, kind, **fields)` appends JSON to `<unit>/_temp/specs/events.jsonl`; `timer(name)` context manager. Wrap in `fit.build_lesson`: `render_lesson`, `docx_to_pdf`, `_reports`. In `export._word_export`: time `Documents.Open`, `ExportAsFixedFormat`. In `cli.build`: figures, checks, `pdf_to_pngs`, retain. One `build` event per lesson with `stem, ok, rounds, scale, phases, error_codes`.
**Tests.** `tests/test_events.py`: timer records, JSONL appends, doesn't crash if the dir is missing.
**Accept.** A 4.7 build writes one event whose phases add up to wall time within 10%.
**Risk.** Log noise; keep one line per build.

## 2. C1 fit loop stops when pinned
**Goal.** No more shrinking to 0.6 when shrinking can't help.
**Change.** `fit.build_lesson`: if `pagefill.pinned(rep[k], budget[k])` returns a hint for every over group, or the page count for a group didn't drop over 2 rounds, stop. Write `_temp/specs/<stem>/fit.md` with the overflow, `slack_list`, and the 3 largest items on the last page (from the `PageFill` report) as cut suggestions. Error code `LB-PAGE` in the message.
**Tests.** `tests/test_fit.py` with a stub `render_lesson`/`docx_to_pdf` (monkeypatch) that returns fixed page counts and a pinned report: loop runs 1 round, not 4; `fit.md` lists items.
**Accept.** Rebuild 4.5 from Unit 4: stops at round 1 or 2 with a named cut.
**Risk.** Stopping too early on a case where one more step would fit; require both "pinned" and no page drop before giving up on round 2+.

## 3. F2a export only what the fit needs (cheap parts)
**Goal.** Fewer exports and less work per round.
**Change.**
- `render.render_lesson` (≈ line 575): add `include_guide: bool`; `fit.build_lesson` passes False on fit rounds and renders `render_guide` once after the loop, exporting it once.
- `export._word_export`: drop `ComputeStatistics`; count pages with `fitz.open(pdf).page_count`.
- `fit.build_lesson`: call `_reports` and the overflow logs only when deciding (keep the report needed by `pinned`, skip `_summary`/`reports.update` on non-final rounds).
- `cli.build` (lines 169-173): hash each PDF; call `pdf_to_pngs` only for changed PDFs, keep previous PNGs otherwise.
- Build into `_temp/build/<stem>/`, move to `output/` only when no errors (keep current paths for `--no-fit` debugging).
**Tests.** Extend `tests/test_fit.py` stub: guide exported once for a 2-round build; page count from pymupdf on a fixture PDF.
**Accept.** 4.7 build: exports per build 10 → 7 or fewer; ≥ 4 s faster (from F6 timing).
**Risk.** Moving outputs changes paths agents expect; keep final names identical.

## 4. F1 one Word session, owned PID, build lock
**Goal.** Start Word once per `build` command, never leave orphans.
**Change.** `export.py`: `WordSession` class (context manager) that wraps `word_app()`, records the PID (`win32process.GetWindowThreadProcessId` on the app hwnd, or diff of WINWORD PIDs before/after start), and on exit calls `Quit`, then kills that PID if still alive. Log `Quit` failures instead of `except Exception: pass` (line 50). Replace the blind retry (lines 82-83) with: log reason, retry once; on `pywintypes.com_error` matching gen_py cache errors, delete `%LOCALAPPDATA%\Temp\gen_py` once and restart. `docx_to_pdf(paths, out_dir, session=None)`; `cli.build` opens one session for all lessons. Per-unit lock `_temp/build/.lock` (pid + time; stale after 30 min). Force UTF-8 stdout in `cli.main`.
**Tests.** `tests/test_export.py`: fake app object; session quits once for 3 calls; kills owned PID on exception; lock blocks a second holder. Word-only test marked `@pytest.mark.word`.
**Accept.** Unit-wide build leaves 0 WINWORD.exe; 2-4 s saved per lesson.
**Risk.** Killing a teacher's own Word; only ever kill the recorded PID.

## 5. F4 start at last good scale
**Change.** `fit.build_lesson`: after a passing build write `_temp/specs/<stem>/fit.json` `{spec_hash, builder_version, scale}`; next build starts from it if `builder_version` matches (spec hash may differ; it's a starting point). Confirm with one export; if under budget with slack > 1 page, try one step up.
**Tests.** stub test: second build uses 1 round.
**Accept.** Rebuild of a passing doc after a text edit: 1 round.
**Risk.** Starting too small leaves extra white space; the step-up rule handles it.

## 6. F5a skip export for unchanged DOCX
**Change.** `export.py`: `docx_hash(path)` hashes zip members with `docProps/core.xml` timestamps normalized; cache `{hash: pdf, pages}` in `_temp/build/export_cache.json`; `docx_to_pdf` reuses the PDF on a hit.
**Tests.** Two renders of the same spec give the same hash; edit changes it.
**Accept.** Rebuilding an unchanged doc does 0 Word exports.
**Risk.** Stale PDF if hash misses something; include builder version in the key.

## 7. A3 math dry run in `check`
**Change.** `check.check_spec`: for every math span in `_student_texts` and key texts, call `docbuilder.latex_to_omml_inner(s, SIZE)` in a try block; report `LB-MATH item 3b: unknown \foo` as an error. Add the cheap commands to the converter table now (`\leq \geq \ne \cot \sec \csc \degree \mu \sigma \Rightarrow \% \therefore`); the rest is F7 in Phase 2.
**Tests.** `tests/test_check_math.py`: bad command → error from `check_spec` without building; listed commands convert.
**Accept.** 0 math build failures in pilot.
**Risk.** None real.

## 8. A2 strict schema
**Change.** `spec.py`: per-layout allowed fields (`PRACTICE_CELL_FIELDS`, `DRAW_ITEM_FIELDS`, assessment top-level). `check.check_spec`: error `LB-FIELD` when a set field is ignored by the layout that will render it (use `render._explicit` to know what's set); error on `no_answer` + `answer`; warn when `selected: auto` (`render.selected_answers`) truncates, showing the kept text.
**Tests.** `tests/test_check_schema.py`: one case per ignored field.
**Accept.** Every Unit 4 audit finding caused by an ignored field would now fail `check` (replay the 4.x YAML from git history).
**Risk.** Existing units start failing; errors only on new builds, `--legacy` downgrades to warnings.

## 9. B5 honest `figs` lint
**Change.** `cli.figs`: count sidecar lint results in the summary; exit 1 on lint errors.
**Tests.** fixture figure with a lint error → exit 1.
**Accept.** `figs` summary equals the lint count.

## 10. G1 first 6 patterns + test + `pattern` CLI
**Goal.** Starting points that are guaranteed to pass, before more are added in Phase 2.
**Change.**
- `templates/patterns/<name>.yaml` and `templates/patterns/figures/<name>.py` for: `find-side`, `label-sides`, `practice-selected`, `practice-two-col`, `frame-fraction`, `agree-disagree`. Draw the YAML from the fixed Unit 4 docs (`units/geometry/unit-4-right-triangle-trig/` and the `_temp/specs/*/changes.md` that fixed each trap).
- Header block parsed by new `src/lesson_builder/patterns.py`:
  ```yaml
  # PATTERN: find-side
  # use: right triangle, find a missing side with sin/cos/tan
  # avoids: tight fraction box (4.3 audit), hand-copied answer
  # requires: figure, box, answer
  # forbids: selected: auto
  ```
  `patterns.load_all() -> list[Pattern]` (name, use, avoids, requires, forbids, path).
- `cli.py`: `pattern list`, `pattern show <name>`, `pattern new <unit> <stem> --from <name>` (reuse `scaffold.py` naming; rename ids and `@figure` names with the stem prefix).
- Each pattern is a valid one-item doc, so it renders as-is with a small test unit (`templates/patterns/unit.yaml`).
**Tests.** `tests/test_patterns.py`: for each pattern, `load_lesson` + `check_spec` → 0 errors and 0 warnings; render DOCX; with `@pytest.mark.word`, `build_lesson` + `check_outputs` → 0 issues. Header parse test. `pattern new` produces a doc that passes `check`.
**Accept.** All 6 pass; `pattern new` output passes `check` with no edits.
**Risk.** Patterns rot when the builder changes; the test is the guard and runs in CI.

## 11. E1 audit IDs in `status`
**Change.** `visual-layout-checker` format (documented in the skill later; for now parser only): `- [M1] ...` and `Closed: M1`. `status.must_fix_lines`: collect IDs, subtract any `Closed:` IDs anywhere in the file; fall back to today's logic when no IDs.
**Tests.** `tests/test_status.py`: closures in a later section close the Must; legacy file unchanged.
**Accept.** `status` matches a hand count on Unit 4 4.7 and Review audits.

## 12. C4 build budgets
**Change.** `cli.build`: read `events.jsonl`; if the stem has 3 failed builds in a row with the same error code, refuse unless `--force`, printing the escalation message and path for `stuck.md`. Requires error codes `LB-PAGE`, `LB-MATH`, `LB-FIELD`, `LB-DRIFT`, `LB-CLIP`, `LB-BLANK` on the messages from `check.check_outputs`.
**Tests.** 3 synthetic failure events → refusal; `--force` passes.
**Accept.** No stem in the pilot has > 3 same-code failures.

## 13. E3 checkpoint/resume
**Change.** `events.py`: `checkpoint(stem, step, session_id, command, result)` writes `_temp/specs/<stem>/step.json`. New `cli resume <unit>`: lists unfinished steps with session ID and next command.
**Tests.** checkpoint round-trip; resume lists only unfinished.
**Accept.** After a forced kill in the pilot, recovery under 5 min.

## 14. E4 `caught_by` telemetry
**Change.** `log_event(..., kind="finding", caught_by="check|build|audit|teacher", category=...)`: `check`/`build` log their own; `status` logs audit Musts by ID (from E1). Extend whatever produces `rework_report.txt` (orchestrator script) to sum by `caught_by`.
**Accept.** Pilot report shows the split.

---

## Verification
1. `uv run pytest` (Word tests on the Windows machine with Word).
2. Rebuild all of Unit 4 into a scratch copy: `uv run lesson-builder build <copy>`. Expect no new errors versus the Unit 4 final state and record times.
3. Pilot: the first 3 docs of the next unit (one lesson with practice, one progress check, the review), writers started from patterns.
4. Compare to Unit 4:

| Metric | Unit 4 | Phase 1 target |
|---|---|---|
| Typical lesson build | ~40 s | ≤ 20 s |
| Fit-loop share of build time | 69% | ≤ 35% |
| Builds per doc | ~5 | ≤ 4 |
| Failed builds | 26% | ≤ 15% |
| Fix-round cost | +57% | ≤ +45% |
| Orphan WINWORD.exe after run | 8 | 0 |
| Items started from a pattern | 0 | ≥ 40% |

# Lesson-builder workflow hardening plan

For teacher review. Nothing in this plan has been built yet. It is based on the Unit 4 run (right triangle trig: 14 docs, 122 min, $81) and the Unit 3 run (10.6 h, $388, mostly outages and audit loops).

## What went wrong, in short

- **Builds ate the clock.** Builds were 97% of command time (2,974 s over about 72 builds). Word export is about 90% of each build. 27 builds ran the page-fit loop, and those took 69% of build time.
- **The fit loop doesn't know when to stop.** `build_lesson` in `src/lesson_builder/fit.py` keeps shrinking workspace by 0.88 down to 0.6, with a full render and Word export each time. It does this even after `pinned()` logs "shrinking only helps if the pages before it merge." Lessons 4.1 and 4.5 hit the floor more than once.
- **One build in four failed.** 19 of 72 failed, which was 40% of command time. Causes: page budget 9 (4.5 failed 6 times), blank trailing page 4, box drift 3, cut-off key text 1, builder bug 1, unknown LaTeX `\beta` 1.
- **Audits found what checks should have found.** Practice answer strip from `selected: auto` (all 5 lessons), key labels beside the wrong segment (5 docs), crowded labels (6), wrong vertex correspondence (4.1, 2 Musts), missing frames (7). Fix rounds added about 57% on top of first-draft cost.
- **Each document found the same problem again.** Answer strip x5, label side x5, tight fraction boxes x2, `\alpha`/`\beta` workarounds. Unit decisions reached writers only through fix rounds.
- **Silent failures.** Some layouts ignore schema fields without saying so. The math converter rejects common commands, and only at build time. `figs` reports "0 warnings" while sidecar lint fails.
- **Bookkeeping drift.** `status` (`must_fix_lines` in `status.py`) counts closed Musts as open when the re-audit logs the closures in a later section (4.7, Review, Unit 3).

Already fixed this run (not proposed again): fixed-height workspace slots, label and box drift checks, clipped key text check, actual-size figures, answer-cue warnings, subscript-aware integrity, upright trig, Greek and `\sqrt[n]`, draw items keeping fill and parts, `no_answer` skip, tall-math box growth, trailing blank page trim.

Effort: **S** = under half a day, **M** = 1 to 2 days, **L** = 3 or more days.

---

## A. Prevent problems up front

### A1. Unit defaults that reach every writer
**Problem.** The answer-strip decision (`selected: auto` in practice) was made once for the unit, but writers heard about it only through fix rounds in all 5 lessons. Label-side and fraction-box rules were rediscovered the same way.
**Change.** Add a `defaults:` block to the unit YAML (`spec.py` `UnitSpec`): for example `practice.selected`, `key_labels.side`, `frames.fraction_box`, `math.allowed_extra`. The renderer applies these unless a document overrides them. `brief.py` `brief()` prints a "Unit decisions" section at the top of every brief. Add `lesson-builder decide <unit> "<rule>"` to append a decision to a `decisions.md` that every later brief includes.
**Why it helps.** A decision made once reaches every writer before drafting starts.
**Effort.** M. **Measure.** Repeated audit findings across docs (same finding in 3 or more docs) go from 4 types to 0 or 1.

### A2. Strict schema: no silently ignored fields
**Problem.** `draw`/`table`/`columns` in practice cells, `figure`/`choices`/`layout`/`box` on draw items, and `practice` on assessments are all dropped with no warning. `no_answer` plus `answer` still prints the answer. `selected: auto` keeps only the first sentence.
**Change.** In `spec.py`, give each layout a table of the fields it supports. `check_spec` in `check.py` errors on any field that the target layout ignores, and names the layout that does support it. `no_answer` with `answer` is an error. `selected: auto` warns when it cuts text, and shows the text it kept.
**Why it helps.** Turns "looks wrong in audit" into "fails in 1 s at check."
**Effort.** S to M. **Measure.** 0 audit findings caused by an ignored field.

### A3. Math dry run in `check`
**Problem.** The converter raises on `\leq \geq \ne \cot \sec \csc \degree \mu \sigma \Rightarrow \% \mathrm \widehat \vec \therefore` and others, and only at build time (1 failed build in Unit 4, plus workarounds).
**Change.** (1) Add these commands to the converter's table (full list in F7). (2) In `check_spec`, run every math string through the converter without writing a file, and report `item 3b: unknown \foo; use \bar`.
**Why it helps.** Math errors cost a 1 s check instead of a 40 s or longer build.
**Effort.** S. **Measure.** 0 builds fail on math.

### A4. Layout budget at spec time
**Problem.** Page budget failures were the biggest failure type (9). Writers can't tell a draft is too long until a build runs.
**Change.** `check` estimates height per item (fixed slot heights are already known, plus text lines and figure heights) and warns "estimated 4.6 pages, budget 4; biggest items: 7 (0.8 pg), 9 (0.6 pg)." This uses the same model as D1.
**Why it helps.** Writers cut before the first build, as `lesson-scope` intends.
**Effort.** M (shares work with D1). **Measure.** Page-budget build failures drop from 9 to 2 or fewer.

### A5. Briefs that teach the traps
**Problem.** Briefs teach the schema but not the traps: layout limits, physical-scale rules, workspace growth, and frames that can't hold a template like `tan(□°)=□/□` (4.7 needed 2 fix rounds).
**Change.** Add `references/traps.md`, made from audit history: one line per trap with the YAML fix. `brief.py` `_extras` includes the traps for the doc type. Add a frame `template:` form so blanks can sit inside an expression.
**Effort.** S for the traps file, M for template frames. **Measure.** Fix rounds per doc go from about 1.6 to 1.2 or fewer. No template-frame findings.

---

## B. Deterministic checks that replace audit judgment

### B1. Key label placement from figure metadata
**Problem.** Key labels sat beside the wrong segment in 5 docs, and labels crowded figures in 6. Only image inspection caught these.
**Change.** In `figures/core.py`, label helpers record `(label, target segment/vertex, bbox)` into the figure sidecar. A new check in `check_figures` flags (a) a label whose nearest segment isn't its target, (b) label bboxes that overlap each other or a line by more than a set margin, and (c) red key labels on the opposite side of the segment from the student label.
**Effort.** M. **Measure.** Label-side and crowding audit findings go from 11 to 2 or fewer.

### B2. Correspondence check against the figure model
**Problem.** 4.1 had wrong vertex correspondences in a key (2 Musts).
**Change.** Figures declare named points, right angles, and similar or congruent pairs in the sidecar. Key answers can mark a claim, for example `claim: {similar: [ABC, DEF]}` or `opposite: {angle: A, side: BC}`, and `check` verifies it against coordinates (angle order, side opposite, ratio values).
**Effort.** M to L. **Measure.** 0 correspondence Musts from audit.

### B3. Computed answers, not hand-copied
**Problem.** Agents wrote one-off math scripts (`plan_values`, `twp_values`, `mathcheck`) and copied values into YAML by hand.
**Change.** Add an `answer_expr:` field (a safe expression on figure values or given numbers) with a `round:` rule. `check` evaluates it and compares it to the printed `answer`, or fills the answer in. Add `lesson-builder values <stem>` to print every computed value.
**Effort.** M. **Measure.** No scratch math scripts in `_temp/`, and 0 wrong-number findings.

### B4. Scaffold and frame coverage check
**Problem.** Missing scaffolds or frames were found 7 times by audit.
**Change.** The requirements file lists planned frames per item (from `handout-release-check`). `check` compares planned and present, and flags explanation items in MLL periods that have no frame.
**Effort.** S. **Measure.** Missing-frame findings go from 7 to 1 or fewer.

### B5. Honest `figs` status
**Problem.** `figs` printed "0 warnings" while sidecar lint failed in 6 Unit 3 docs.
**Change.** Count sidecar lint in the `figs` summary and exit non-zero on lint errors.
**Effort.** S. **Measure.** Audit never finds a lint issue that `figs` passed.

---

## C. Tools for stuck agents

### C1. Fit loop that stops when pinned and names the cut
**Problem.** The `while True` loop in `fit.py` `build_lesson` keeps shrinking after `pinned()` says shrinking can't help (4.1 and 4.5 reached the 0.6 floor repeatedly; each step is a full Word export).
**Change.** If `pinned()` returns a hint, or two steps in a row don't lower the page count, stop at once. Print a cut list from the page-fill report: "over by 0.4 pg; cut item 9 (0.45 pg) or move 7 to practice." Write it to `_temp/specs/<stem>/fit.md`.
**Effort.** S. **Measure.** Fit-loop builds go from 27 to 10 or fewer. No build reaches the floor more than once per doc.

### C2. `lesson-builder explain <error>`
**Problem.** The same errors (page budget, blank page, box drift, clipped text, unknown LaTeX) cost a full investigation each time.
**Change.** Every check and build error gets a stable code (e.g. `LB-PAGE`, `LB-DRIFT`, `LB-MATH`). `lesson-builder explain LB-DRIFT --stem 4.3` prints the cause, the items involved, and the exact YAML change. Codes are listed in `api_cheatsheet.md`.
**Effort.** M. **Measure.** Median time from failed build to passing build is cut in half.

### C3. Evidence commands instead of one-off scripts
**Problem.** About 14 one-off anchor-measuring scripts in Unit 3.
**Change.** `lesson-builder anchors <stem>` prints student and key label/frame positions with the drift between them (built from `_labels`, `_frames`, `anchor_drift`). `lesson-builder keytext <stem>` lists each key answer and whether it shows in full (from `clipped_answers`). `lesson-builder pages <stem>` prints the page-fill per item.
**Effort.** S. **Measure.** 0 scratch measurement scripts in `_temp/build`.

### C4. Build budgets and escalation
**Problem.** 4.5 failed 6 times on the same page budget before anyone changed course.
**Change.** `events.jsonl` counts builds per stem. After 3 failed builds with the same error code, the CLI refuses a 4th unless `--force`, and prints: "stop; write `_temp/specs/<stem>/stuck.md` and escalate to the orchestrator." `orchestration.md` says what the orchestrator does then: cut, re-scope, or ask the teacher.
**Effort.** S. **Measure.** No stem has more than 3 failed builds with the same code.

---

## D. Speed

### D1. Estimate pages before exporting
**Problem.** Every fit step pays for a Word export (about 90% of build time).
**Change.** Use a height model from the DOCX (known slot heights, figure sizes, line counts, calibrated against past exports) to pick the scale first, then export once to confirm. Only fall back to the loop if the estimate is off by more than one step.
**Effort.** M to L. **Measure.** Average exports per build go from about 2.5 to 1.3 or fewer; mean build time drops 40%.

D1 also gives the starting scale for F4. Phase timing, Word sessions, parallel export, and export skipping are now in **F1 to F5**.

### D2. Incremental builds
**Problem.** Builder changes mid-run shifted 4.5 and the tests, so the first full build failed. Unchanged docs get rebuilt anyway.
**Change.** Hash the YAML, figure file, unit defaults, and builder version per document. `build` skips documents whose hash didn't change (F5 does the same per DOCX). Freeze the builder version during a wave (see E2), and run any builder change against all built docs before merging.
**Effort.** M. **Measure.** No full-unit build fails from a builder change made mid-wave.

---

## E. Orchestration

### E1. Status parser that reads closures
**Problem.** `must_fix_lines` counts closed Musts as open when closures are logged in a later section (4.7, Review, Unit 3).
**Change.** Give each audit item an ID (`M1`, `S2`). Re-audits write `Closed: M1` lines. `status` matches IDs across sections. `visual-layout-checker` sets the format.
**Effort.** S. **Measure.** `status` matches a hand count on every doc.

### E2. Wave automation
**Problem.** Waves (`wave.md`) are run by hand: brief, write, figs, build, audit, fix.
**Change.** `lesson-builder wave <unit> --step build` runs the step for every ready doc, writes results to `wave.md`, and lists which docs need an agent. The orchestrator spends its time on judgment, not on dispatch.
**Effort.** M. **Measure.** Orchestrator tokens per doc drop 30%.

### E3. Checkpoint and resume
**Problem.** AWS credential failures and server restarts stopped agents mid-task several times. Resuming by session ID worked, but it was manual.
**Change.** Each step writes `_temp/specs/<stem>/step.json` (step, session ID, last command, last result). `lesson-builder resume <unit>` lists the interrupted steps with the session ID and the next command. `orchestration.md` adds a "after an outage" checklist.
**Effort.** S. **Measure.** Outage recovery under 5 minutes per agent.

### E4. Telemetry that sorts catches
**Problem.** We can't tell how many problems checks caught compared to audits without reading every file by hand.
**Change.** Tag each finding in `events.jsonl` with `caught_by: check|build|audit|teacher` and a category. `rework_report.txt` shows the split and the top repeat categories.
**Effort.** S. **Measure.** The share caught by audit goes down unit over unit (target: audits catch under 30% of findings).

---

## F. Word export, speed, and formatting

**Measured.** One fit round of lesson 4.7 (5 docs) took 19.7 s: Word `ExportAsFixedFormat` 8.2 s, `Documents.Open` 2.7 s, Word start 1.2 to 2.5 s, cached figure load 1.3 s, python-docx render 1.0 s, page-fill report 1.0 s, page PNGs 0.9 s, output checks 0.6 s, `ComputeStatistics` 0.6 s, retain and verify 0.3 s. Word is about 70% of a round. A typical 40 s build is 2 rounds, and every round restarts Word and re-exports all 5 docs.

### F1. One Word session per build, with cleanup
**Problem.** `docx_to_pdf` starts and quits Word on every call (`export.py:42-52, 77`), so once per round. `Quit` errors are swallowed (`except Exception: pass`, `export.py:50`). We found 8 orphan WINWORD.exe processes hours later, two of them holding a DOCX open (PermissionError). The retry at `export.py:82-83` is blind and not logged. Word's gen_py COM cache got corrupted in Unit 3 (5 failed builds).
**Change.** A `WordSession` context manager in `export.py` opens Word once per build, records its PID, and kills only that PID on exit or crash. Retries are logged with the reason. On a COM error it clears the gen_py cache once and retries. Add a per-unit build lock file so two builds can't share a Word session or an output file. Console output is forced to UTF-8 (stops cp1252 crashes).
**Why it helps.** Saves 2 to 4 s per build, stops orphans and locked files.
**Effort.** S. **Measure.** 0 orphan WINWORD.exe after a unit run, 0 PermissionError, 0 COM cache failures.

### F2. Export only what the fit needs
**Problem.** The teacher guide is rendered and exported every round (`fit.py:53`, `render.py:587`) even though `GROUP` leaves it out of the fit. Keys are exported every round too, though the handout and practice decide the fit. `ComputeStatistics` counts pages where pymupdf `page_count` would do (`export.py:59`). The page-fill report and logs run on rounds that get thrown away (`fit.py:57, 66-73`). Every page of every PDF is rendered to PNG each build (`cli.py:169-173`).
**Change.** In `build_lesson`, fit rounds export only the handout and practice. The keys and guide render and export once, at the scale chosen. Count pages with pymupdf. Run `_reports` and the overflow logs only on the final round (and on a pinned stop, for C1). Render PNGs only for PDFs whose bytes changed. Render into `_temp/build/` and move files to `output/` only when the build passes, so a failed build never leaves half-new files.
**Why it helps.** Saves about 2 to 8 s for the guide, 5 to 7 s for keys, 1 to 2 s for counting and reports.
**Effort.** S for guide, counts, reports and PNGs. M for keys (they must still match the student layout; the drift checks already catch this). **Measure.** Exports per build go from about 10 to 6 or fewer (2 rounds).

### F3. Faster figure cache
**Problem.** The figure cache stats every dependency file and calls every figure function even when the PNG is cached (`figures/core.py:500-532`). It decides by mtime (`core.py:527`), which misses some edits and repeats others.
**Change.** Write a manifest per figure file: a content hash of the source and helpers mapped to PNG paths. On a hit, load PNG sizes from the manifest and skip calling the function.
**Effort.** S to M. **Measure.** Cached figure load goes from 1.3 s to under 0.3 s.

### F4. Start at the last good scale
**Problem.** Every rebuild starts at scale 1.0 and shrinks again, even when only one word changed.
**Change.** Save the final scale per document with its spec hash in `_temp/specs/<stem>/fit.json`. The next build starts there (or at the D1 estimate, or a LibreOffice `--draft` count) and confirms with one Word export.
**Why it helps.** Saves 10 to 20 s on most rebuilds.
**Effort.** S. **Measure.** Rebuilds of a passing doc use 1 round.

### F5. Skip export when the DOCX hasn't changed, then parallelize
**Problem.** Unchanged documents are exported again. Full-unit builds take 723 s in a row.
**Change.** Hash the DOCX contents with `docProps/core.xml` timestamps normalized; if it matches the last export, reuse the PDF. After F1 is stable, add an optional pool of 2 to 3 Word processes, each with its own temp folder and owned PID.
**Effort.** S for skipping. M to L for the pool (higher risk; do it last). **Measure.** Typical lesson build 10 to 15 s (from about 40 s); full unit under 300 s.

### F6. Phase timing
**Problem.** We had to profile by hand to learn Word was 70%.
**Change.** `fit.py` and `export.py` log time for each phase (render, open, export, report, PNG, checks) into `events.jsonl`. The rework report sums them.
**Effort.** S. **Measure.** Phase times appear for every build.

### F7. Math converter coverage
**Problem.** Builds out on A3. The converter raises on `\leq \geq \ne \% \$ \mathrm \mathbf \vec \hat \widehat \bar \underline \overset \dots \cdots \therefore \because \Rightarrow \rightarrow \lambda \mu \sigma \omega \binom \sum`. It has no matrices, cases, aligned, or line breaks. `\left \right` are stripped, so brackets don't auto-size. A superscript's base is only the last character, so `(x+1)^2` comes out wrong. `\frac12` and `\sqrt x` need braces. `$` always opens math, so money breaks.
**Change.** Add the commands to the converter table. Group the base for superscripts (closing paren, brace group). Map `\left( \right)` to OMML delimiters with growth. Support `cases`, `matrix`/`pmatrix`, `aligned`, and `\\`. Accept unbraced single-token arguments. Treat `\$` and `$` before a digit with no closing `$` as text. Add one test per command.
**Effort.** M. **Measure.** 0 math build failures, no `\alpha`-style workarounds in YAML.

### F8. Tables and lists the schema can't express
**Problem.** `table` is fixed at a header plus one answer row. There's no general N×M data table, no true/false grid, no 3-column or unequal columns, no plain "1)" or "i." sub-lists, no custom header fields, and no template inside a frame box (4.7).
**Change.** Add a `grid:` item (rows, columns, widths, which cells are blanks), a `tf:` item, `columns: [2, 1, 1]` widths, a `list_style:` on parts, and `header.fields`. Template frames are covered in A5.
**Effort.** M. **Measure.** No audit finding says "layout can't do this."

### F9. Clean Word XML
**Problem.** `tcPr` puts `tcBorders` after `tcMar`/`vAlign`, and `tblPr` adds `tblBorders`/`tblLayout`/`tblInd` after `tblLook`, both out of schema order. `row_height` and `row_cant_split` add duplicates when called twice. `cell_bottom_border` can duplicate `tcBorders`. Tables indented without a smaller width can run past the right margin. `answer_height` is estimated with PIL fonts, not measured.
**Change.** In `docbuilder.py`, one `_set_child(parent, tag)` helper that inserts in schema order and replaces any existing child. Indented tables subtract the indent from their width. Add a `check` step that validates each DOCX against the order rules and margins. Calibrate `answer_height` against measured heights from the final PDF.
**Effort.** S to M. **Measure.** The validator passes on all built docs, and no table crosses the margin.

### F10. Formatting defaults (from 27 Unit 4 renders)
**Problem and change.** Each row is one fix in `docbuilder.py`, using shared constants instead of scattered numbers.

| Issue | Where | Fix | Pages helped |
|---|---|---|---|
| Labels touch answer boxes (30-40 twips, about 0.02 in) | `fill_boxes` :843, frame :905 | 120 twips padding; label width = 0.3 in + measured text | ~80 |
| Ragged box edges, scattered indents (0.3 / 0.55 / +0.25) | frame :882 (width per row) | One label width per problem; fixed box widths 1.6 in text, 1.3 in numbers; `INDENT` constants | ~70 |
| Uneven row gaps (0.05-0.08 in), short boxes, boxes touching text above | fill and frame rows | `ROW_GAP = 0.10 in`; box height 0.42 text / 0.38 numbers; 5 pt before boxes | ~70 |
| Stacked fractions hit the line above | Normal style 1.0 spacing | 1.08 spacing, or extra space on math lines | ~25 |
| Header adds two spaces when label is empty; title wraps at 62% width | header :494 | Drop the empty part; wider title cell | ~20 |
| Narrow prompt beside big sketch boxes; dead space at page bottom | figure/sketch layout, QuickNotes, cantSplit | Auto-stack when prompt column < 2.4 in or choices wrap; see F11 | ~30 |
| Key answers 9-10.5 pt red, weak in grayscale; footer 8 pt, bank 9.5 pt | key and footer styles | Bold darker red at body size; footer 9 pt, bank 10.5 pt | all keys |
| Guide tables equal-width, orphan headers, "□" placeholders | guide renderer | Content-based widths, keep-with-next on headers, lint "□" | guides |

Also try 12 pt body text for Period 4 handouts (many MLLs), as a unit default (A1).
**Effort.** M overall (each row S). **Measure.** Audit findings for crowding, spacing, and weak keys drop by half. Teacher spot-check of 5 renders.

### F11. Automatic layout fixes for the recurring problems
**Problem.** Student/key drift is still the top recurring class (13 of 14 Unit 4 docs, 11 of 20 Unit 3). A QuickNotes page break left 6 to 8 in of slack and caused 6 of 13 over-budget triggers. Half-width practice cells ignore fill/draw, and the tallest cell sets the row height. Labels wrap, and boxes are too short for fractions.
**Change.** (1) Reserve the measured key height in both copies so the student and key layouts match by design. (2) When the fit report shows a break with known slack, pull a small block back or pad it (keep-with-next on QuickNotes) instead of shrinking. (3) Auto-size boxes to label and math height. (4) In half-width cells, convert fill/draw to full width or refuse them at `check` (A2).
**Effort.** M. **Measure.** Drift appears in 3 or fewer docs per unit; no OVER triggers from a QuickNotes break.

---

## G. Known-good YAML pattern library

**Problem.** Writers start from two broad examples: `templates/unit/lessons/example.yaml` (130 lines) and `templates/unit/assessments/example.yaml` (70 lines), plus `templates/unit/figures/example.py`. `brief.py` `examples_md` pastes the first section of each kind into every write brief, whether or not the document needs it. Nothing shows the right way to do the cases writers actually got wrong. The same mistakes came back in doc after doc: answer strip x5, label side x5, tight fraction boxes x2, template frames (4.7, 2 rounds), draw or fill inside half-width practice cells, `\alpha`/`\beta` workarounds, and wrong correspondences (4.1).
**Change.** Add a library of small patterns that are known to work: `templates/patterns/<name>.yaml`, plus `templates/patterns/figures/<name>.py` when the pattern has a figure. Each one is a single, self-contained use case. Writers start from these before they write anything.

| Pattern | Prevents |
|---|---|
| `find-side`: right triangle, fill box, computed answer (B3) | hand-copied values, tight boxes |
| `find-angle`: inverse trig, degree answer | `\degree`/`^\circ` errors, rounding mismatches |
| `label-sides`: opp/adj/hyp with answer layer | key labels beside the wrong segment, crowding |
| `mc-select-all` with key | missing key answers, key pattern warnings |
| `mc-fractions`: fraction choices | stacked fractions colliding, choices wrapping |
| `sketch-solve`: draw box + `h ≈` fill, key-only sketch | draw fields ignored, answers showing on the student copy |
| `frame-fraction`: equation frame with a stacked fraction | tight fraction boxes, the 4.7 template frame |
| `true-false`: current workaround, then the F8 `tf:` grid | ad hoc tables |
| `agree-disagree`: explain item with an MLL sentence frame | missing frames (7 findings) |
| `practice-two-col`: what a half-width cell can and can't hold | fill/draw dropped in cells |
| `practice-selected`: `selected: []` and explicit lists | `selected: auto` answer strip (5 lessons) |
| `quicknotes` block | QuickNotes page-break slack |
| `forms-a-retake`: Form A + Retake with version table | integrity failures, blank trailing page |
| `review-unscored` item | scored/unscored mix-ups |
| `reference-sheet` with a completed example | layout guesswork |
| `actual-size-ruler`: physical-size figure | width and size check failures |
| `similar-correspondence`: fill with vertex order | wrong correspondences |

Each file starts with a `# PATTERN:` header that the tools can read: name, when to use it, the traps it avoids (with the error code or audit finding), required fields, and forbidden fields.

**Guarantees.** A test renders every pattern to DOCX and runs `check_spec`. When Word is available, it also runs a full build and `check_outputs`, and expects 0 errors and 0 warnings. The patterns rebuild on every builder change, so a change that breaks a pattern fails the tests before it can break a unit mid-wave.

**Tools.** `lesson-builder pattern list`, `pattern show <name>`, and `pattern new <unit> <stem> --from <name>` (copies the pattern and renames ids and figure names). `brief()` picks the 3 to 5 patterns that match the document's planned item types and figure plan, and pastes those instead of the generic example. `check` warns when an item breaks its pattern in a known-trap way (for example a draw inside a practice cell).

**How it fits.** Patterns are the positive form of the A5 traps file: each trap points to the pattern that avoids it. They read A1 unit defaults instead of hard-coding them, use `answer_expr` once B3 exists, and are the first thing rebuilt to confirm F10 formatting changes.
**Why it helps.** Writers copy something that already passes, so most errors never get made.
**Effort.** M (S to start with the first 6 patterns). **Measure.** Share of items written from a pattern (target 70%), first-build pass rate (target 80%), fix rounds per doc.

---

## Ranked top 10

| # | Proposal | Effort | Why this rank |
|---|---|---|---|
| 1 | C1 + F2 Fit loop stops when pinned; fit rounds export only handout and practice | S-M | Biggest time sink (69% of build time); guide and keys re-exported for nothing |
| 2 | F1 One Word session per build, owned-PID cleanup, build lock | S | Word is 70% of a round; ends orphans and locked files |
| 3 | G Known-good pattern library (start with 6 patterns + test) | S-M | Stops errors before the first build; guards against breaking builder changes |
| 4 | A3 + F7 Math dry run in `check` and wider converter | S-M | Removes a whole failure type and the workarounds |
| 5 | A1 Unit defaults and decisions in every brief | M | Removes the most repeated fix rounds |
| 6 | A2 Strict schema, no ignored fields | S-M | Ends silent failures |
| 7 | F10 Formatting defaults (padding, widths, row gap, key style) | M | Improves about 250 pages of output across a unit |
| 8 | F4 + F5 Start at last good scale; skip unchanged exports | S | Rebuilds drop from about 40 s to 10-15 s |
| 9 | F11 + B1 Automatic layout fixes and label placement check | M | Drift is in 13 of 14 docs; 11 label findings |
| 10 | C4 + E1 Build budgets and status parser with audit IDs | S | Stops failure spirals and false "open Must" loops |

B3 (computed answers), C2 (`explain`), D1 (page estimate), and F8 (tables) come right after these.

## Rollout

Detailed implementation plans: `docs/plans/` (`phase1.md`, `phase2.md`, `phase3.md`).

**Phase 1 (about 1 week, before the next unit):** F6, C1, F2 (guide, counts, reports, PNGs), F1, A3, A2, G (first 6 patterns, the pattern test, `pattern list/show/new`), B5, E1, C4, F4, F5 skip, E3, E4. Almost all S. They stop the worst loops, cut a typical build from about 40 s toward 15 s, give writers starting points that already pass, and give us timing and catch data.

**Phase 2 (run the next unit with these):** G (remaining patterns, brief picks patterns, `check` warns on deviations), F7, F9, F10, F11, F2 keys-once, F3, A1, B1, B4, A5 traps file, C2, C3, A4. Then compare against Unit 4: build count, build time, failed builds, fix rounds per doc, share of items from a pattern, and the audit share of catches.

**Phase 3 (after Phase 2 data):** D1, D2, F5 Word pool, F8, B2, B3, E2, and template frames. These cost the most or carry the most risk, so we use Phase 2 data to decide which ones are worth it.

**Targets for the next unit compared to Unit 4:** builds per doc from about 5 to 3 or fewer; failed builds from 26% to under 10%; typical lesson build from about 40 s to 15 s or less; fit-loop share of build time from 69% to under 25%; 0 orphan Word processes; fix-round cost from +57% to under +30%.

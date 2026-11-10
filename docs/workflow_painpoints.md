# Workflow pain points and recommendations

Study of 58 OpenCode sessions in this repo (about $200, mostly the Unit 2 → lesson-builder → Unit 3 work), plus the 15 Unit 3 audits. Data and per-slice reports: `_temp/painpoints/` (`index.md`, `stats.json`, `findings/*.md`). Transcripts exported with `scripts/export_sessions.py`.

## Headline

- **Cost per lesson:** a finished lesson took one agent 45–60 min, 72–135 tool calls and $4–5.50.
  - About 40% of that was setup reading before the first write.
  - About 30–40% was nudging figure labels and rebuilding.
- **Checking by eye didn't work:** every document agent reported "0 errors, I looked at every page." The audits still found must-fix items in 11 of 14 documents. Most of those are figure problems a script can measure: label collisions, labels printing at 5 pt, figures not drawn to scale, hidden primes.
- **Orchestration waste:**
  - 22 launches were needed for 9 lessons, with crashes, duplicate launches and credential failures. That cost about $7 and 35+ minutes.
  - About 28 builder bugs were found by agents mid-wave and worked around 2–3 times each before being fixed.
- **Rules were missing until the user repeated them:**
  - The user had to ask 3 times before fill-in blanks became labeled boxes.
  - The user had to ask twice for complete keys with drawn answer figures.
  - The period length changed 3 times.

## Pain points, ranked

| # | Pain point | Evidence | Root cause |
|---|---|---|---|
| 1 | **Figure label loops** | Figure file is the most-edited file in 6/9 lessons (3.13: 15 edits; 3.6, 3.11: 13). One triangle moved 4 times in 3.9; `angle_dist` 2.7→3.6→2.2→3.0 in a progress check. Collisions still flagged in 13/14 audits. | Labels placed by hand offsets, with no overlap check. Feedback only after a full Word build. |
| 2 | **Print size and B&W are invisible on full-page renders** | Labels at 5–6 pt after `fig_w` scaling (7 audits). Colour source PNGs on student copies (4 audits). | Nobody computes printed size. Review is "open every page." |
| 3 | **Exam integrity checked only by prose** | Must-fix in 4/5 assessment audits: B mirrors A, Retake reuses A's letters, Review copies Test B's angles, Summary Notes print the 6-8-10 that answers Test A #5. | Rule exists only in instructions. Review, Test and Notes ran in parallel, so dependents couldn't see the Test. |
| 4 | **Agent crashes and duplicate launches** | 5/9 first-wave agents died writing a whole file in one call (`toolUse.input is invalid`). The orchestrator relaunched 3.1/3.3/3.9 twice, twice. AWS credential failures forced a third wave. | Huge single writes. No record of which agent owns which doc. Retry in the same turn as a tool error. |
| 5 | **Setup repeated by every agent** | 26–57 calls before the first write, 22 times. Nine agents rediscovered the same pitfalls: `P((0,0))`, `np.cross` on 2-D, `$33` in prose, `''` in block scalars. | 12+ files to read. No API cheat sheet. Pitfalls live in code. |
| 6 | **Builder bugs found by agents, fixed late** | Guide drops numbers and spaces, cropped key-only figures, choices > F dropped, `B_1`, header "Score ____" fails its own check, no bullets, stranded headings. | Features shipped without a test document. A "no shared-code changes mid-wave" freeze multiplied workarounds. |
| 7 | **Page-fit trial and error** | 2–4 builds per document; "item numbers differ between student and key" with no detail. A global workspace shrink (to 77–88%) left 1.5–3 in blank on one page and 0.3 in for answers elsewhere. | `fit.py` shrinks evenly. Key paginated separately from student. No per-item overflow report. |
| 8 | **Library-wide render defects** | Detached prime "A ′" (9 audits), "A/D/" inside `\frac`, off-baseline fraction choices (5), guide ".;" joins (4). | One-line bugs in `figures/core.py`, `docbuilder.py`, `render.py` that agents may not touch. |
| 9 | **Windows shell friction** | About 15 failed calls: `python -c` quoting, cp1252 crashes, PowerShell multi-line replaces that half-applied (22 degree signs corrupted in 3.9, a deleted function in `common.py`). | No Windows rules in AGENTS.md. Agents edit files through the shell. |
| 10 | **Missing or conflicting rules** | Fill-box rule only after 3 user requests. "Fix one lesson" instead of the unit. `assessment-builder` said "don't spawn subagents." A skill refactor dropped pedagogy content and needed a restore session. | Teacher preferences were not captured as checkable rules. Refactors had no old→new map. |

## Recommendations

### A. Scripts and checks (biggest wins first)

1. **Figure lint + auto-placement** (`figures/core.py`, runs in every figure render).
   - Measures each label's text box against segments, arcs, dots and other labels. ERROR with figure, label and what it hits.
   - `label(auto=True)` tries 8–16 directions × 3 offsets and keeps the first clear spot.
   - Fixes pain point 1 and most figure must-fixes.
2. **Printed-size and B&W checks** (in `check`).
   - Printed label pt = font pt × `fig_w` / drawn width. ERROR below 7 pt, with the `fig_w` needed for 9 pt.
   - ERROR on any non-gray pixel on student pages.
   - Flag low-resolution source images.
3. **Figure scale asserts** (`figures/core.py` helpers).
   - `assert_lengths(labels)` checks drawn lengths match labels within 3%.
   - `assert_distinct(angles, min_deg=4)` checks that angles the key calls different look different.
   - Would have caught the 3.3 exit figure and 3.13 practice 2.
4. **`lesson-builder figs <unit> -l <stem> --sheet`**.
   - Renders only one document's figures, student and key side by side at print size, on one PNG.
   - Seconds per loop instead of a full Word build.
   - Replaces about 20 one-off contact-sheet scripts.
5. **`lesson-builder integrity <unit> --set "Unit 3 Test*" --vs "Unit 3 Review" "Unit 3 Summary Notes"`**.
   - Compares versions and documents: letter sets, numbers, k values, side triples, MC answer positions, and answers printed on figures.
   - ERROR on reuse.
6. **Page-fill report** (in `fit.py`).
   - Per page: slack inches, items on the page (student and key), and the item that overflows.
   - Shrink workspace per page, not globally.
   - Paginate the key from the student layout, so "item numbers differ" can't happen.
7. **More `check` rules:**
   - Fill boxes narrower than 0.9 in.
   - Explain items with no box or frame.
   - `$` + digit in prose.
   - `''` in block scalars.
   - Problem references that don't resolve.
   - Guide text with ".;" or missing spaces.
8. **Problem references by id.** `{ref:arrow_table}` becomes "Problem 4" at render time, so cuts can't leave stale numbers.
9. **`lesson-builder brief <doc>`** writes one `packet.md` per document: the schema subset, one example per section type, the source text inline, the page-image list, the Math Medic excerpt and the files the agent owns. One read instead of about 30.
10. **`lesson-builder scaffold <doc>`** writes a skeleton YAML and figure file, so the first write is a small edit (avoids the crash in pain point 4).
11. **Wave tracking: `launch-plan` / `wave-status`.**
    - `wave.json` records doc, session id, status, last file write time and attempts.
    - The orchestrator reads it before every launch, and it flags agents idle more than 10 minutes.
12. **Kitchen-sink fixture** (`tests/fixtures/kitchen_sink.yaml`) uses every builder feature and is built in pytest before any wave. Most of pain point 6 would have failed here first.
13. **Fix once in `src/`:**
    - Prime glyph in figures, and `'` → `^{\prime}` inside `\frac`.
    - Fraction-choice baseline.
    - Guide answer joins.
    - Add pytest to dev dependencies.
    - Ingest always writes page PNGs.

### B. Skill changes

| Skill | Change |
|---|---|
| `lesson-builder` | **One-page API cheat sheet:** figure helper signatures, allowed math symbols, the known pitfalls. The reading list becomes brief + cheat sheet + one example. |
| `lesson-builder` | **Figures step:** run `figs --sheet` until lint is clean before the first full build. Never nudge labels by eye. |
| `lesson-builder` | **Review step:** look at crops and flagged items, not every page. Max 4 full builds. |
| `lesson-builder` | **New "Orchestrating a unit" section:** build the kitchen sink first. Launch only from `wave.json`. Never relaunch in the same turn as a tool error. Resume a failed agent's session before starting a new one. Fix a builder bug once 2+ agents report it. Relay results to the user in 5 lines or fewer. |
| `lesson-builder` | When the teacher flags a problem in one lesson, grep the whole unit and fix every instance before replying. |
| `handout-release-check` | Printed labels ≥ 7 pt. B&W images only. No answer visible on the same page (3.11, 3.13). QuickNotes on both student copy and key. |
| `assessment-builder` | Run `integrity` before reporting. B and Retake: new letters on every item, new answer positions. Record intended difficulty differences in the guide. If source points don't match its stated total, scale to the total and log it. Replace "don't spawn subagents" with "one subagent per document when asked; shared code only by the parent." |
| `classroom-context` | The default deliverable set: handout, lesson key, practice, practice key, guide, and duplex PDF and DOCX packets. |
| `AGENTS.md` | **Windows section:** set `PYTHONIOENCODING=utf-8`. Never edit files with PowerShell replace or `Set-Content`; use the edit tool. No `python -c` with nested quotes or heredocs; write a script in `_temp/build/`. Keep each write ≤ ~150 lines. |
| All skills | **Refactors:** keep a table mapping each old section to its new location, or "dropped (user approved)." |

### C. Split the work into smaller tasks

Per document (lesson or assessment version):

1. **Plan** (about 10 calls): `requirements.md` with the item list, timing, figure list with coordinates and values to assert, and for assessments a version table (move types, k, number types, answer positions).
2. **Figures** (about 20 calls): figure file only, looping on `figs --sheet` + lint + asserts. No document builds.
3. **YAML + fit** (about 20 calls): writes the YAML in pieces, at most 4 builds, page-fill report clean.
4. **Audit** (read-only): runs the scripts first, then spends its time on teaching quality (frames that give answers away, MLL wording, rubrics). Scripts can't judge these.

Scheduling:
- Run 3–4 agents at a time, not 9, so one connection failure costs less.
- Assessments go in waves:
  1. Test A/B/Retake.
  2. Review and Summary Notes, given the Test YAMLs as "do not reuse."
  3. `integrity` across all of them.
- The parent alone owns `src/`. Agents log builder gaps one line each in `changes.md` (`GAP: <file>:<feature>: <symptom> | workaround`) so they can be searched and deduplicated.

**Expected effect:** about 50 calls, 20–25 min and $2 per lesson (now 90–135 calls, 50 min, $4–5.50). Most figure must-fixes would turn into build errors caught before an audit.

## Suggested order of work

1. **Done (Nov 9):** render fixes (prime, fractions, guide joins) and check rules A7 (box width, balanced `$`, guide punctuation).
2. **Done (Nov 9):** figure lint + auto-placement + print-size and colour checks (A1–A2), plus `lesson-builder figs` contact sheets (A4). A3 scale asserts still open.
3. `figs --sheet` and the page-fill report (A4, A6).
4. `integrity` (A5), then apply the Unit 3 audit fixes (`units/geometry/unit-3-similarity/_temp/specs/audit/SUMMARY.md`).
5. `brief` / `scaffold` / cheat sheet / wave tracking (A9–A11), plus the skill and AGENTS.md edits, before the next unit.

# Orchestrating lessons and assessments with subagents

Read this when you are the orchestrator: the agent the teacher is talking to. Start a fresh subagent for each step below, so each one loads only what its step needs and hands off through files. The orchestrator keeps the plan, talks to the teacher, and owns shared files. It doesn't write lesson content.

If the environment can't start subagents (for example Microsoft Copilot), run the same steps in order in one session. Write the same files, and load each step's skills only when that step starts.

## Who owns what

| Owner | Files |
|---|---|
| Orchestrator | `unit.yaml`, `src/`, `templates/`, `.agents/`, `_temp/specs/wave.md`, packets, the reply to the teacher |
| Document subagent | its own `lessons/<id>.yaml` or `assessments/<stem>.yaml`, `figures/<stem>.py`, `assets/<stem>/`, `_temp/specs/<stem>/`, `output/figures/<stem>/` |
| Audit subagent | `_temp/specs/<stem>/audit.md` only (read-only otherwise) |

`<stem>` is the YAML file name without `.yaml` (for example `3.6` or `Unit 3 Test A`). Quote stems that contain spaces.

A subagent that needs a builder feature or a figure helper that doesn't exist uses the closest existing field and logs one line in `_temp/specs/<stem>/changes.md`:
`GAP: <file>:<feature>: <symptom> | workaround`.
After each wave, the orchestrator reads the GAP lines and fixes a gap in `src/` (with a test) once two documents report it, or once the teacher asks for it. Subagents never edit `src/`.

## Steps per document

| Step | Who | Loads | Reads | Writes | Done when |
|---|---|---|---|---|---|
| 0. Intake | orchestrator | `classroom-context` (target period only) | the request, `input/` | unit folder (`lesson-builder new-unit` if new), `_temp/ingest/` (`lesson-builder ingest`), intake section of `_temp/specs/<stem>/requirements.md`, `_temp/specs/wave.md` | questions asked once, all at the same time |
| 1. Plan | subagent | `lesson-assessment-designer` (Steps 1-2, 4 for lessons), `lesson-scope` (lessons), `mll-literacy-scaffolding` (Period 4 / MLLs), `course-content-extractor` (only if sources are missing), assessment-builder "Exam integrity" (forms) | requirements.md intake, `_temp/ingest/*.md`, page PNGs as needed | requirements.md: targets, blueprint table, figure plan, version table | blueprint covers the targets; minutes ≤ budget or points = total |
| 2. Figures | subagent | `curriculum-visual-generator`, `references/api_cheatsheet.md` | requirements.md figure plan | `figures/<stem>.py`, `assets/<stem>/` | `lesson-builder figs <unit> -l <stem>` shows 0 errors and no label warnings |
| 3. Write + build | subagent | `references/api_cheatsheet.md`, `authentic-writer`, `assessment-builder/references/item-rules.md`, `handout-release-check` §1-2, `mll-literacy-scaffolding` (Period 4 / MLLs) | requirements.md, figure names from step 2 | the YAML, `changes.md` | `lesson-builder build <unit> -l <stem>` shows 0 errors, at most 4 builds |
| 4. Audit | read-only subagent | `visual-layout-checker`, `handout-release-check`, item-rules, `mll-literacy-scaffolding` checklist, `lesson-assessment-designer` final check | built PDFs, `_temp/renders/current/<stem>/`, the YAML, requirements.md | `audit.md` (Must fix / Should fix / Looks fine) | every page and figure looked at |
| 5. Fix | the step 3 subagent, resumed by session ID | (already loaded) | `audit.md` | YAML, figure file, `changes.md` | Must fix list empty or reported; at most 2 rounds |
| 6. Release | orchestrator | `handout-release-check` §4-5 | outputs, all `changes.md` / `audit.md` | `output/figures/<stem>/` + README, packets (full unit build), the reply | checks clean, figure bundle matches the final documents |

Steps 2 and 3 can run in parallel when the plan fixes every figure name. Step 3 then writes the YAML first and builds only after step 2 reports.

Small jobs (one short item edit, a single label fix) don't need the full chain. Do them in one subagent, or directly, and still rebuild and check.

## Handoff files

`_temp/specs/<stem>/requirements.md`, in this order:
1. **Intake** (orchestrator): mode (new / rewrite), course and period profile, doc type, source files, page budget, minutes or total points, what the teacher said to keep or change, forms needed.
2. **Targets** (plan): standards and learning targets in both forms ("understand that..." and "able to...").
3. **Blueprint** (plan): one row per item: `n | target | type (SR/CR/performance) | demand | minutes or points | figure name`.
4. **Figure plan** (plan): per figure: name (`<stem>_<item>`), what it shows, coordinates or measurements, values the code must assert, answer layer contents.
5. **Version table** (assessment forms): per item and form: letters, numbers, scale factors or side triples, motion types, MC answer position. Plus a "do not reuse" list taken from documents built in earlier waves.

`changes.md`: one line per change: `item: what changed | why (rule)`, plus GAP lines.
`audit.md`: Must fix / Should fix / Looks fine, each line naming page, item, and the file and field to change.
`_temp/specs/wave.md` (orchestrator): `| doc | step | session ID | status | attempts | updated |`.

## Subagent prompt template

Write each prompt so it stands alone. The subagent has no other context.

```text
You are the <Step> step for <doc type> "<stem>" in unit <unit path> (repo C:\Users\zubair\Documents\GitHub\pdf-to-docx, Windows pwsh, Python via `uv run`).
Load only these skills/sections: <list>.
Read: <exact input files>.
Write only: <exact files>. Don't edit anything else. Never edit src/, unit.yaml, other documents, or a DOCX.
Done when: <exit condition from the table>.
Rules: write files in pieces of 150 lines or fewer; use the edit tool, not PowerShell replace; no `python -c` with nested quotes (save a script in _temp/build/).
Reply in 10 lines or fewer: files written, check results (errors/warnings), open questions, GAP lines. Details go in the handoff files, not the reply.
```

## Scheduling

- Run 3-4 subagents at a time. Record each one in `wave.md` before you launch it.
- A failed or stalled subagent is resumed with its session ID before a new one is started. Never relaunch in the same turn as a tool error. Check `wave.md` first so a document never has two owners.
- Word export can collide when builds run at the same time. On a COM error, rerun the build once.
- Lesson units: plan all the lessons first (one Plan subagent per lesson, or one for the unit when lessons depend on each other), then run figures/write/audit per lesson.
- Assessment sets go in waves:
  1. One Plan subagent for the whole set (Test A/B/Retake, progress check forms), so the version table is consistent.
  2. Figures and Write per form, in parallel.
  3. Review sheets and summary notes, given the finished test YAMLs as "do not reuse".
  4. One Audit subagent across the set for exam integrity, plus one per document for layout and teaching quality.
- When the teacher flags a problem in one document, grep the whole unit for the same pattern and fix every instance (one subagent per affected document) before replying.

## Release (step 6)

1. Run `uv run lesson-builder check <unit> -l <stem>` for each document; 0 errors.
2. Exam integrity across forms: compare the version tables and YAMLs by reading them (no script yet). Letters, numbers, contexts, and MC answer positions differ between forms. Review/notes don't print any test answer.
3. Figure bundle per document: copy the PNGs it uses from `_temp/figures/<stem>/` (and `_temp/figures/` for shared figures) into `output/figures/<stem>/`. Write a README mapping item number → figure name → function in `figures/<stem>.py`, listing helper files, data or seeds, and the command `uv run lesson-builder figs <unit> -l <stem>` (from the repo root). Source images are listed by `assets/` path and original page.
4. Lessons: full `uv run lesson-builder build <unit>` for packets.
5. Reply to the teacher in 5-10 lines: files in `output/`, pages, minutes or points, what changed (grouped), open judgment calls, and anything left on a Must fix list.

# Orchestrating lessons and assessments with subagents

Read this when you are the orchestrator: the agent the teacher is talking to. Start a fresh subagent for each step below, so each one loads only what its step needs and hands off through files. The orchestrator keeps the plan, talks to the teacher, and owns shared files. It doesn't write lesson content.

If the environment can't start subagents (for example Microsoft Copilot), run the same steps in order in one session. Write the same files, and load each step's skills only when that step starts.

## Who owns what

| Owner | Files |
|---|---|
| Orchestrator | `unit.yaml`, `src/`, `templates/`, `.agents/`, `_temp/specs/wave.md`, packets, the reply to the teacher |
| Document subagent | its own `lessons/<id>.yaml` or `assessments/<stem>.yaml`, `figures/<stem>.py`, `assets/<stem>/`, `_temp/specs/<stem>/` (`output/figures/<stem>/` is written by the build) |
| Audit subagent | `_temp/specs/<stem>/audit.md` only (read-only otherwise) |

`<stem>` is the YAML file name without `.yaml` (for example `3.6` or `Unit 3 Test A`). Quote stems that contain spaces.

A subagent that needs a builder feature or a figure helper that doesn't exist uses the closest existing field and logs one line in `_temp/specs/<stem>/changes.md`:
`GAP: <file>:<feature>: <symptom> | workaround`.
After each wave, the orchestrator reads the GAP lines and fixes a gap in `src/` (with a test) once two documents report it, or once the teacher asks for it. Subagents never edit `src/`.

## Steps per document

| Step | Who | Loads | Reads | Writes | Done when |
|---|---|---|---|---|---|
| 0. Intake | orchestrator | `classroom-context` (target period only) | the request, `input/` | unit folder (`lesson-builder new-unit` if new), `_temp/ingest/` (`lesson-builder ingest`), `lesson-builder scaffold <unit> <stem> --type ... [--forms ...]` (YAML, `figures/<stem>.py`, handoff files, `unit.yaml` entry), intake section of `requirements.md`, `_temp/specs/wave.md` | questions asked once, all at the same time |
| 1. Plan | subagent | `lesson-assessment-designer` (Steps 1-2, 4 for lessons), `lesson-scope` (lessons), `mll-literacy-scaffolding` (Period 4 / MLLs), `course-content-extractor` (only if sources are missing), assessment-builder "Exam integrity" (forms) | requirements.md intake, `_temp/ingest/*.md`, page PNGs as needed | requirements.md: targets, blueprint table, figure plan, version table | blueprint covers the targets; minutes ≤ budget or points = total |
| 2. Figures | subagent | `curriculum-visual-generator`, `references/api_cheatsheet.md` | requirements.md figure plan | `figures/<stem>.py`, `assets/<stem>/` | `lesson-builder figs <unit> -l <stem>` shows 0 errors and no label warnings |
| 3. Write + build | subagent | `references/api_cheatsheet.md`, `authentic-writer`, `assessment-builder/references/item-rules.md`, `handout-release-check` §1-2, `mll-literacy-scaffolding` (Period 4 / MLLs) | requirements.md, figure names from step 2 | the YAML, `changes.md` | `lesson-builder build <unit> -l <stem>` shows 0 errors, at most 4 builds |
| 4. Audit | read-only subagent | `visual-layout-checker`, `handout-release-check`, item-rules, `mll-literacy-scaffolding` checklist, `lesson-assessment-designer` final check | built PDFs, `_temp/renders/current/<stem>/`, the YAML, requirements.md | `audit.md` (Must fix / Should fix / Looks fine) | every page and figure looked at |
| 5. Fix | the step 3 subagent, resumed by session ID | (already loaded) | `audit.md` | YAML, figure file, `changes.md` | Must fix list empty or reported; at most 2 rounds |
| 6. Release | orchestrator | `handout-release-check` §4-5 | outputs, `lesson-builder status`, all `changes.md` / `audit.md` | packets (full unit build), the reply | checks clean, `integrity` clean for forms, bundle verified by the build |

Before launching steps 1-4, run `uv run lesson-builder brief <unit> "<stem>" --step plan|figures|write|audit`. The brief holds the inputs, the files the step owns, the schema subset and examples, the done condition, and the reply format, so the prompt stays short. Step 5 (Fix) resumes the step 3 session and needs no new brief.

Steps 2 and 3 can run in parallel when the plan fixes every figure name. Step 3 then writes the YAML first and builds only after step 2 reports.

Small jobs (one short item edit, a single label fix) don't need the full chain. Do them in one subagent, or directly, and still rebuild and check.

## Handoff files

`_temp/specs/<stem>/requirements.md` (`scaffold` writes the headings; a set of forms shares `_temp/specs/<set stem>/requirements.md`), in this order:
1. **Intake** (orchestrator): mode (new / rewrite), course and period profile, doc type, source files, page budget, minutes or total points, what the teacher said to keep or change, forms needed.
2. **Targets** (plan): standards and learning targets in both forms ("understand that..." and "able to...").
3. **Blueprint** (plan): one row per item: `n | target | type (SR/CR/performance) | demand | minutes or points | figure name`.
4. **Figure plan** (plan): per figure: name (`<stem>_<item>`), what it shows, coordinates or measurements, values the code must assert, answer layer contents.
5. **Version table** (assessment forms): per item and form: letters, numbers, scale factors or side triples, motion types, MC answer position. Plus a "do not reuse" list taken from documents built in earlier waves.

`changes.md`: one line per change: `item: what changed | why (rule)`, plus GAP lines.
`audit.md`: Must fix / Should fix / Looks fine, each line naming page, item, and the file and field to change. Mark a fixed line `- [x] ...` so `status` stops counting it.
`brief_<step>.md`: written by `lesson-builder brief`; the subagent's first read.
`_temp/specs/wave.md` (orchestrator): `| doc | step | session ID | status | attempts | updated |`. For where each document stands (handoffs, open Must fix, GAP lines, built, stale, figures retained), run `uv run lesson-builder status <unit> [--checks]` instead of opening files.

## Subagent prompt template

The brief carries the details. The prompt only points to it.

```text
You are the <Step> step for <doc type> "<stem>" in unit <unit path> (repo C:\Users\zubair\Documents\GitHub\pdf-to-docx, Windows pwsh, Python via `uv run`).
Read `_temp/specs/<stem>/brief_<step>.md` first (path inside the unit folder). It lists the skills to load, the files to read, the only files you may write, the done condition, and the reply format.
Never edit src/, unit.yaml, other documents, or a DOCX.
<anything the brief can't know: teacher notes from this turn, a GAP the orchestrator fixed>
```

## Scheduling

- Run 3-4 subagents at a time. Record each one in `wave.md` before you launch it. After each wave, `lesson-builder status <unit>` shows what is left.
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
2. Exam integrity across forms: `uv run lesson-builder integrity <unit> --set "Unit 3 Test*" [--vs "Unit 3 Review"]`; 0 errors. It compares letters (subscripts included), numbers, MC key positions, and figure labels between forms, and checks reviews and notes (plus each document's `do_not_reuse`) against the tests. `check` covers answer cues inside each document and student/key positions, cut-off key text, and actual-size figure widths in the PDFs; don't send audit agents to measure those. Then read for what it can't see: same contexts or motion types, a figure that gives away an answer by its shape, difficulty drift between forms.
3. Figure bundles: the build retained and verified them. Check each build's `figures retained` line, or `uv run lesson-builder retain <unit> -l <stem> --verify-only`.
4. `uv run lesson-builder tidy <unit>`: delete temp files and caches with `--apply`; act on orphan assets, unused figures, and redundant `work:` lines through the document owners.
5. `uv run lesson-builder status <unit>`: no open Must fix lines, nothing stale.
6. Lessons: full `uv run lesson-builder build <unit>` for packets.
7. Reply to the teacher in 5-10 lines: files in `output/`, pages, minutes or points, what changed (grouped), open judgment calls, and anything left on a Must fix list.

---
name: lesson-orchestrator
description: Entry point for any lesson, assessment, worksheet, or unit request for Franklin HS room 105 (lesson-builder documents). Runs intake (asks the teacher once), sets up the unit and documents, then dispatches each step (Plan, Figures, Write + build, Audit, Fix) to an independent subagent that loads only its step skill plus lesson-style. Owns scheduling (3-4 subagents at a time, resume after AWS errors), cross-document duplicates, builder GAP fixes in src/, versions and copies of units, release (checks, integrity, packets), and the Google Drive upload. For a change applied across many documents, use unit-revision-pass. The orchestrator writes no lesson content itself.
---

# Lesson orchestrator

You are the agent the teacher talks to. You plan the work, brief subagents, and own the shared files. You don't write lesson content: every document step runs in its own subagent, which loads at most 3-4 skills. Without subagents (for example in Copilot), run the same steps in order in one session, loading each step's skills only when that step starts.

## Skill map

| Who | Loads | For |
|---|---|---|
| You (orchestrator) | this skill, `lesson-style` (to brief), `classroom-context` (target period), `unit-revision-pass` (multi-document passes) | intake, dispatch, release |
| Plan subagent | `lesson-plan-step`, `lesson-style`, `warmup-design` (lessons), `mll-literacy-scaffolding` (Period 4), `classroom-context` | `requirements.md` sections 2-5 |
| Figures subagent | `curriculum-visual-generator`, lesson-builder `references/api_cheatsheet.md` | `figures/<stem>.py` |
| Write subagent (also Fix) | `lesson-write-step` (+ `references/item-rules.md`), `lesson-style`, `authentic-writer`, `mll-literacy-scaffolding`, api cheat sheet | the YAML, build |
| Audit subagent | `lesson-audit-step`, `lesson-style`, item-rules, `mll-literacy-scaffolding` checklist | `audit.md` (read-only) |

The tool itself (CLI, YAML fields, figures API) is documented in `lesson-builder` and its `references/api_cheatsheet.md`. `uv run lesson-builder brief <unit> "<stem>" --step plan|figures|write|audit` writes each subagent's brief with the skills to load, the inputs, the files it may write, and the done condition.

## 1. Intake (you)

- Read the request, the sources (`uv run lesson-builder ingest <unit>/input -o <unit>/_temp/ingest`), and the unit's existing lessons.
- Ask the teacher only what you can't infer and what changes the output, all questions at once. Typical questions: the page budget, the points, the forms needed, what to keep from the source, and the scaffolding level (default, or extra support on request).
- New unit: `uv run lesson-builder new-unit units/<course>/<unit-slug> --course ... --unit N --title "..." --period "Period 4"` (`budget.minutes: 30`).
- New document: `uv run lesson-builder scaffold <unit> <stem> --type lesson|assessment|reference [--forms A,B,Retake]`. It writes the YAML, `figures/<stem>.py`, `requirements.md`, and `changes.md`, and adds the document to `unit.yaml`. Fix the lesson order in `unit.yaml` if needed.
- Write the Intake section of `_temp/specs/<stem>/requirements.md`:
  - mode (new or rewrite);
  - course and period profile;
  - doc type;
  - source files;
  - page budget;
  - minutes (30) or total points;
  - what to keep or change;
  - forms;
  - the `lesson-style` rules that matter here (for example "cut the repeats in the practice", "the in-class practice comes from the old exit ticket").

## 2. Steps per document

| Step | Who | Writes | Done when |
|---|---|---|---|
| 1. Plan | subagent | `requirements.md` §2-5 | blueprint covers the targets; minutes ≤ 30 or points = total; known/new map and figure plan complete |
| 2. Figures | subagent | `figures/<stem>.py`, `assets/<stem>/` | `lesson-builder figs <unit> -l <stem>`: 0 errors, no label warnings |
| 3. Write + build | subagent | the YAML, `changes.md` | `build <unit> -l <stem> --no-packets`: 0 errors, at most 4 builds, every page checked |
| 4. Audit | read-only subagent | `audit.md` | every page and figure looked at |
| 5. Fix | the Write subagent, resumed by session ID (figure fixes: the Figures subagent, resumed) | YAML, figures, `changes.md` | Must fix list empty or reported; at most 2 rounds |
| 6. Release | you | packets, Drive, the reply | below |

- Steps 2 and 3 can run in parallel once the plan fixes every figure name: Write writes the YAML first and builds after Figures reports.
- Small jobs (one item edit, one label) don't need the chain: do them in one subagent, or directly, and still rebuild and check.
- Assessment sets: one Plan subagent for the whole set (so the version table is consistent), then Write per set (forms stay parallel). Reviews and summary notes come after the tests, with the tests as their `do_not_reuse` list.

## 3. Subagent prompts

The brief carries the details. The prompt names the step, the document, and the unit, and says:

```text
You are the <Step> step for <doc type> "<stem>" in unit <unit path> (repo /Users/zubair/Documents/pdf-to-docx, macOS zsh, Python via `uv run`).
Read `<unit>/_temp/specs/<stem>/brief_<step>.md` first. You must load and follow this repo's skills it lists (use the `skill` tool): <step skill>, lesson-style, ...
Your files: <list>. Never edit src/, unit.yaml, .agents/, other documents, or a DOCX.
<anything the brief can't know: teacher notes from this turn, a GAP you fixed, a cross-document duplicate to cut>
```

Always say "load and follow this repo's skills" by name. Pass teacher decisions word for word.

## 4. Scheduling and ownership

- **Owners:**
  - You: `unit.yaml`, `src/`, `templates/`, `.agents/`, `wave.md`, packets, the reply.
  - Each document subagent: its own YAML, figures, assets, and `_temp/specs/<stem>/`.
  - The audit subagent: `audit.md` only.
- **Concurrency:** run 3-4 building subagents at a time (PDF exports collide past that). Read-only audits can run alongside. Record each launch in `_temp/specs/wave.md` (`| doc | step | session ID | status | updated |`) before starting it. A document never has two owners.
- **AWS credential or token errors:**
  1. Check what the subagent had written (git diff or backups).
  2. Resume the same session with a short "continue from where you left off" prompt.
  3. Never start a duplicate.
  4. If several fail with "token expired", stop and ask the teacher to refresh the login.
- **Cross-document duplicates:** a subagent reports one; you route the fix to the owner of the later document (send it to the running session, or put it in the next prompt).
- **Builder gaps:** subagents log `GAP:` lines. Fix a gap in `src/` (with a test) once two documents report it, or when it blocks a teacher rule. Tell running subagents when a fix lands.
- **Fix everywhere:** when the teacher flags a problem in one document, grep the unit and fix every instance (through the owners).

## 5. Versions and copies

- **Default scaffolding:** a good amount, fading toward the end (`lesson-style` §3).
- **Extra support:** only on request. Make a separate copy of the unit folder, `units/<course>/<unit>-extra-support/`.
- **New copies of a unit** (for example `-v2`): copy `lessons/`, `assessments/`, `figures/`, `assets/`, `unit.yaml`, `figures.py`, and `_temp/specs/` to `units/<course>/<unit>-v2/`. The original stays untouched. Don't copy `output/`, `_temp/renders/`, or `archive/`.
- **Before changing finished documents in place,** snapshot them to `<unit>/archive/<date> <reason>/` (YAML, figures, specs, built outputs). Never delete earlier versions.
- On Drive, each copy goes to its own folder, for example "Geometry v2/Unit 3 Similarity" or "<unit folder>/Extra support".

## 6. Release (you)

1. `uv run lesson-builder check <unit> -l <stem>` for every document: 0 errors.
2. Forms: `uv run lesson-builder integrity <unit> --set "<set>*" [--vs "<review>" --vs "<notes>"]`: 0 errors. Then read for what it can't see: repeated contexts, a figure whose shape gives an answer away, difficulty drift.
3. `uv run lesson-builder status <unit>`: no open Must fix lines, nothing stale, figure bundles retained.
4. `uv run lesson-builder tidy <unit>`: report orphans. Delete only temp files and caches, and only with the teacher's OK.
5. Packets: `uv run lesson-builder build <unit>` (full build) or `uv run lesson-builder packet <unit>`. Custom packets: `packet <unit> -l 2.8 -l 2.9 --order lessons-first --name "Lessons 2.8-2.9"`. PDF packets are duplex-ready (each document starts on a front page). DOCX packets need Microsoft Word, which this Mac doesn't have: say so, and leave any older DOCX packet out of the upload.
6. Upload to Google Drive after every release: `references/drive-upload.md`.
7. Reply to the teacher in 5-12 lines:
   - what's where (local and Drive);
   - pages, minutes or points;
   - what changed, grouped;
   - judgment calls to check;
   - anything left on a Must fix list.
8. Commit when the teacher asks. Unit folders are ignored by `/units*`, so add their sources with `git add -f` (`lessons/`, `assessments/`, `figures/`, `assets/`, `unit.yaml`, `figures.py`). Never add `output/`, `_temp/`, `input/`, or `archive/`.

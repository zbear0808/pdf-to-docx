---
name: unit-revision-pass
description: Orchestrator recipe for applying one change across many lessons or assessments with parallel independent subagents. Covers snapshotting or copying the unit first (never deleting earlier versions), writing one shared instruction file that quotes the teacher and names the skills to load, grouping 2-4 documents per subagent and running 3-4 at a time, routing cross-document duplicates, resuming after AWS errors, fixing builder gaps, then the full builds, packets, and Google Drive upload. Use for requests like "do the same thing for every lesson in Unit 3", "remove exit tickets everywhere", or "make new copies of Units 3-4 with the new structure". Loaded by lesson-orchestrator, never by step subagents.
---

# Unit revision pass

You are the orchestrator (`lesson-orchestrator`). A pass applies one teacher request to many documents. Subagents do the document work; you set it up, route between them, and release.

## 1. Before anything changes

- **Scope:** which documents, which units. Ask all your questions at once. The common ones: which lessons; in place or a new copy; what counts as "the same thing" for assessments.
- **Protect what exists. Never delete earlier versions.**
  - In place: snapshot every affected document to `<unit>/archive/<YYYY-MM-DD> <reason>/` (`lessons/`, `figures/`, `specs/`, and the built `output/` folders and packets).
  - New copy: copy the unit's sources to `units/<course>/<unit>-<suffix>/` (`lessons/`, `assessments/`, `figures/`, `assets/`, `unit.yaml`, `figures.py`, `_temp/specs/`). Edit its `unit.yaml` (a title note, and the lesson list if it's a subset). Check that `lesson-builder check <copy> --no-outputs` matches the original before any edits.
  - Unit 4 isn't tracked in git, so a snapshot is the only undo.
- **Update the skills first** if the request is a new rule (it usually goes in `lesson-style`; warm-up ideas go in `warmup-design`). The subagents follow the skills, and the instruction file points to them.

## 2. One instruction file

Write `units/<course>/_temp_<pass>_instructions.md`. Its sections:
1. **The teacher's request**, quoted, and the decisions they picked.
2. **Mode:** what may change and what must not (for example "Don't delete anything", "only what's printed vs. blank changes").
3. **Load these skills first (required):** name each one, with the sections that matter: `lesson-style`, the step skill (`lesson-write-step` for an edit-and-build pass), `warmup-design` if warm-ups change, `mll-literacy-scaffolding`, `authentic-writer`, and the api cheat sheet. For assessments, add `lesson-plan-step` §4.
4. **Steps:** plan the change in `requirements.md` first, then edit, then the plan and notes, then build and look.
5. **Logs:** a dated section in `changes.md`, and a dated note in `guide_notes`.
6. **Files:** only the assigned documents' files. Never edit `src/`, `.agents/`, `unit.yaml`, `archive/`, other documents, or a DOCX.
7. **The finished model to copy,** if one exists.
8. **Reply format:** one block per document, then judgment calls.

## 3. Subagents

- **Grouping:** 2-4 documents per subagent, by unit order (neighbors share context). Forms of one assessment set always go to the same subagent.
- **Concurrency:** 3-4 subagents at a time; start the next group as each finishes. Read-only audits can run alongside.
- **Prompt:** the documents, the instruction file to read first, "You must load and follow this repo's skills" with the names, the file ownership, and the build command.
- **Tracking:** record each launch in the unit's `_temp/specs/wave.md`.
- **During the pass:**
  - **Cross-document duplicates:** a subagent reports one. Send the fix to the owner of the later document (the running session, or the next prompt). Same type with new numbers in a later lesson is spaced review; keep it.
  - **AWS errors:** check what was written, then resume the same session. Several "token expired" errors in a row: ask the teacher to refresh the login.
  - **Builder gaps:** fix them in `src/` with a test when two documents report one or a teacher rule needs it, then tell the running subagents.
  - **Teacher add-ons mid-pass:** update the skill, then send the change to every running session.
- **Assessment passes:** plan + write per set in one session, then an independent audit per set (`lesson-audit-step`), then fix (resume the writer), then release.

## 4. Release

1. Run `check` on every changed document, and `integrity` for every set (with `--vs` reviews and notes).
2. Run a full `build` per unit (this picks up builder fixes) or `packet`, then `status`: no open Must fix lines, nothing stale.
3. Upload to Drive (`lesson-orchestrator` `references/drive-upload.md`). A copy goes to its own Drive folder.
4. Reply to the teacher:
   - a table of documents with before and after minutes or points;
   - what changed, grouped;
   - judgment calls;
   - where everything is, local and on Drive.

## Passes we've run (models)

| Pass | Instruction file |
|---|---|
| Core idea, scaffolding, fewer repeats | `units/geometry/unit-3-similarity/_temp/specs/coreidea_instructions.md` |
| No exit tickets, Warm-up heading only | `units/geometry/_temp_no_exit_instructions.md` |
| Assessments: less is more, no headings | `units/geometry/_temp_assessment_pass_instructions.md`, plus `_temp_assessment_audit_instructions.md` |
| Known content printed, new blank | `units/geometry/_temp_known_new_instructions.md` |
| Faded scaffolding copy | `units/geometry/_temp_faded_instructions.md` |
| Cut extra wording | `units/geometry/_temp_lean_pass_instructions.md` |

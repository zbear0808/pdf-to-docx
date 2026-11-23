# Google Drive upload (release step 6)

The teacher's Drive is reached with `gdup` (project: `~/Documents/github/gdrive-upload`, installed as `~/.local/bin/gdup`, signed in with browser cookies in `~/.config/gdup/`). Account check: `gdup whoami`.

## Layout

```text
My Drive/Geometry/
  Unit 2 Congruent triangles/            <- units/geometry/unit-2-congruent-triangles/output/*
    Faded scaffolding/                    <- a copy's output (older name for the default level)
  Unit 3 Similarity/
  Unit 4 Right triangles and trig/
My Drive/Geometry v2/
  Unit 3 Similarity/                      <- units/geometry/unit-3-similarity-v2/output/*
```

- Each unit folder gets that unit's `output/` contents: `Lesson N/` folders, `Assessments/`, `Reference/`, `figures/` (the figure bundles), and the packets.
- A copy of a unit (`-v2`, `-extra-support`) goes to its own folder: a parallel top folder ("Geometry v2") or a subfolder of the unit.
- Ask the teacher the folder name once, then reuse it.

## Commands

```bash
gdup mkdir "Geometry/Unit 3 Similarity"                       # create if missing; prints the URL
gdup upload -n -d "Geometry/Unit 3 Similarity" units/geometry/unit-3-similarity/output/*   # dry run
gdup upload -d "Geometry/Unit 3 Similarity" units/geometry/unit-3-similarity/output/*      # upload
```

- **Order:** run the dry run first and compare its file count with `find <unit>/output -type f | wc -l`, then upload. The destination folder must exist before the dry run (`gdup mkdir`).
- **Re-uploading:** identical files are skipped (size + MD5) and changed files are updated in place, so re-running after a fix is safe.
- **Leave out stale files:** a DOCX packet from an older build (the PDF packet is rebuilt, the DOCX isn't without Word), Word lock files (`~$*`), and `.DS_Store`. Build the path list without them.
- **Archives:** never upload `archive/` or `_temp/` unless the teacher asks.
- **Logs:** send each upload's output to `_temp/build/gdup_<unit>.log`. Report "uploaded N, updated M, skipped K, failed F" per folder, with the folder URL.

## Errors

- **Cookie expired** (`gdup whoami` fails, or the upload says unauthorized): ask the teacher to export fresh cookies and run `gdup login <cookies.txt>`. Don't retry in a loop.
- **"folder not found" on a dry run:** run `gdup mkdir` first.

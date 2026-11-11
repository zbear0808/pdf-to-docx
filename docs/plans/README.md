# Implementation plans

The teacher-facing plan is `docs/workflow_hardening_plan.md`. These files turn it into work orders, one per phase. Item codes (C1, F2, G, ...) match that plan.

| File | Scope | When |
|---|---|---|
| `phase1.md` | Stop the loops, cut build time, strict checks, first patterns, telemetry | Before the next unit (about 1 week) |
| `phase2.md` | Formatting, converter, layout automation, full pattern library, unit defaults, label checks | Built during and piloted on the next unit |
| `phase3.md` | Page estimate, Word pool, incremental builds, new item types, model checks, wave automation | After Phase 2 data |

Unit 4 baseline that every phase compares against:

| Metric | Unit 4 |
|---|---|
| Builds per doc | ~5 (72 builds / 14 docs) |
| Failed builds | 26% (19 / 72) |
| Fit-loop share of build time | 69% |
| Fix-round cost on top of first draft | +57% |
| Typical lesson build | ~40 s (2 fit rounds of ~20 s) |
| Wall time / cost | 122 min / $81 |

Rules for all phases:
- Each item lands as its own commit, with tests, and the full test suite passes (`uv run pytest`).
- Rebuild every `templates/patterns/` file after any builder change (once G exists).
- Don't change the builder during a unit wave; queue changes until the wave ends.

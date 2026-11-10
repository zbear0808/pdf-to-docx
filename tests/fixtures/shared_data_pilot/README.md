# Shared-data progress-check pilot

Regression snapshot of the four Unit 3 `3.1-3.5 Progress Check` forms (A, B, Retake A, Retake B),
migrated to schema version 1. The working classroom unit remains under `units/geometry/unit-3-similarity`
and is intentionally gitignored. This fixture preserves the source needed to test the pipeline in a
clean checkout; it contains no source exams, outputs, or temporary renders.

Item q3's rectangle dimensions, labels, answers, and numerical scoring examples share a checked YAML
model. The other figures use shared construction helpers with their existing mathematical data.

Tests copy fixture sources into a temporary unit before rendering or changing givens. Update this
snapshot deliberately when the expected regression scenario changes. Classroom edits belong in the
working unit, not in the test fixture.

Run `uv run pytest tests/test_lesson_problem_models.py -q` from the repository root. The parameter-edit
test changes one given, checks text, answers, guide, diagram dimensions, PNG cache invalidation, and
DOCX compilation. It requires neither the ignored units nor their original input documents.

"""Where a unit stands: per document, handoff files, open Must fix lines, GAP lines, outputs built and stale,
retained figures, and (optionally) spec check counts."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from .render import outputs
from .spec import UnitSpec, load_lesson

HANDOFFS = ("requirements.md", "changes.md", "audit.md")
_NONE = re.compile(r"^\(?\s*(none|nothing)\b", re.I)


@dataclass
class DocStatus:
    stem: str
    doc_type: str = "?"
    handoffs: list[str] = field(default_factory=list)
    must_fix: int | None = None      # None: no audit.md
    gaps: int | None = None          # None: no changes.md
    built: list[str] = field(default_factory=list)   # outputs() kinds whose DOCX exists
    expected: int = 0
    pdfs: int = 0
    newest_output: float | None = None
    stale: bool = False              # an output is older than the YAML or a figure file it uses
    retained: bool = False
    errors: int | None = None
    warnings: int | None = None
    load_error: str | None = None


def must_fix_lines(text: str) -> list[str]:
    """Open bullets under a "Must fix" heading (until the next heading). `- none` and `- [x] ...` don't count."""
    out, inside = [], False
    for ln in text.splitlines():
        if ln.lstrip().startswith("#"):
            inside = bool(re.match(r"#+\s*must fix\b", ln.strip(), re.I))
            continue
        s = ln.strip()
        if inside and s.startswith("- "):
            body = s[2:].strip()
            if _NONE.match(body) or body.lower().startswith("[x]"):
                continue
            out.append(body)
    return out


def gap_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if re.match(r"^\s*(?:[-*]\s+)?GAP\b", ln)]


def _sources(unit: UnitSpec, path: Path) -> list[Path]:
    cands = [path, unit.dir / (unit.figures or "figures.py"), unit.dir / "figures" / f"{path.stem}.py",
             unit.dir / "figures" / "_helpers.py"]
    return [p for p in cands if p.is_file()]


def doc_status(unit: UnitSpec, path: Path, with_checks: bool = False, figs: dict | None = None) -> DocStatus:
    st = DocStatus(path.stem)
    specs = unit.dir / "_temp" / "specs" / path.stem
    st.handoffs = [h for h in HANDOFFS if (specs / h).is_file()]
    if "audit.md" in st.handoffs:
        st.must_fix = len(must_fix_lines((specs / "audit.md").read_text(encoding="utf-8", errors="replace")))
    if "changes.md" in st.handoffs:
        st.gaps = len(gap_lines((specs / "changes.md").read_text(encoding="utf-8", errors="replace")))
    st.retained = (unit.dir / "output" / "figures" / path.stem / "README.md").is_file()
    try:
        lesson = load_lesson(path)
    except Exception as e:
        st.load_error = str(e).splitlines()[0][:120]
        return st
    st.doc_type = lesson.doc_type
    o = outputs(unit, lesson)
    st.expected = len(o)
    st.built = [k for k, p in o.items() if p.is_file()]
    st.pdfs = sum(p.with_suffix(".pdf").is_file() for p in o.values())
    if st.built:
        times = [o[k].stat().st_mtime for k in st.built]
        st.newest_output = max(times)
        st.stale = min(times) < max(p.stat().st_mtime for p in _sources(unit, path))
    if with_checks:
        from .check import check_spec, summarize
        from .cli import _figs_for
        try:
            st.errors, st.warnings = summarize(check_spec(unit, lesson, _figs_for(figs or {}, lesson)))
        except Exception as e:
            st.errors, st.load_error = 1, f"check failed: {e}"[:120]
    return st


def unit_status(unit: UnitSpec, with_checks: bool = False) -> list[DocStatus]:
    figs = None
    if with_checks:
        from .cli import _figures
        figs = _figures(unit, docs={p.stem for p in unit.doc_paths()})
    return [doc_status(unit, p, with_checks, figs) for p in unit.doc_paths()]


def format_table(statuses: list[DocStatus]) -> str:
    checks = any(s.errors is not None for s in statuses)
    head = ["Document", "Type", "Handoffs", "Must fix", "GAPs", "Built", "PDF", "Stale", "Figures"]
    head += ["Errors", "Warnings"] if checks else []
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]

    def n(v):
        return "-" if v is None else str(v)
    for s in statuses:
        hand = " ".join(h.split(".")[0][:3] if h in s.handoffs else "-" for h in HANDOFFS)
        built = "load error" if s.load_error and not s.expected else f"{len(s.built)}/{s.expected}"
        cells = [s.stem, s.doc_type, hand, n(s.must_fix), n(s.gaps), built,
                 f"{s.pdfs}/{s.expected}" if s.expected else "-", "yes" if s.stale else "",
                 "yes" if s.retained else ""]
        cells += [n(s.errors), n(s.warnings)] if checks else []
        rows.append("| " + " | ".join(cells) + " |")
    errs = [s for s in statuses if s.load_error]
    rows += [f"\n{s.stem}: {s.load_error}" for s in errs]
    return "\n".join(rows)

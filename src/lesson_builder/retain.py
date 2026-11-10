"""Figure retention: copy the figures a document uses to output/figures/<stem>/ with a README that points to
their source, and verify the bundle against the images embedded in the built DOCX files."""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import shutil
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

from .render import outputs
from .spec import LessonSpec, UnitSpec

ROOT = Path(__file__).resolve().parents[2]
NOTE_SUFFIXES = (".source.txt", ".txt", ".md")


@dataclass
class Use:
    item: str      # "3", "Practice 2", "(unnumbered)"
    ref: str       # registered figure name or asset path
    copy: str      # "student" | "key"
    doc: str       # outputs() key of the DOCX it appears in: handout, key, practice, practice_key
    source: str = ""   # item `source:` field, if any


@dataclass
class Row:
    use: Use
    file: str      # file name in the bundle
    source: str


@dataclass
class RetainResult:
    out_dir: Path
    rows: list[Row] = field(default_factory=list)
    files: list[Path] = field(default_factory=list)
    removed: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def figure_uses(unit: UnitSpec, lesson: LessonSpec) -> list[Use]:
    """Every figure placement, as render.py places them (draw items show their figure on the key only)."""
    have = outputs(unit, lesson)
    uses = []

    def add(item, ref, copy, doc, src):
        if ref and doc in have:
            uses.append(Use(item, ref, copy, doc, src or ""))

    groups = [("handout", "key", "", [it for _, it in lesson.items()])]
    if lesson.practice:
        groups.append(("practice", "practice_key", "Practice ", [c for r in lesson.practice.rows for c in r.cells]))
    for sdoc, kdoc, prefix, items in groups:
        for it in items:
            label = prefix + (it.n or "(unnumbered)")
            if it.draw:
                add(label, it.draw.key_figure or it.key_figure or it.figure, "key", kdoc, it.source)
                continue
            add(label, it.figure, "student", sdoc, it.source)
            add(label, it.key_figure or it.figure, "key", kdoc, it.source)
    return uses


def figure_files(unit: UnitSpec, lesson: LessonSpec) -> list[Path]:
    """The figure files a document can draw from: shared figures.py first, then figures/<stem>.py (wins)."""
    shared = unit.dir / (unit.figures or "figures.py")
    own = unit.dir / "figures" / f"{lesson.stem}.py"
    return [p for p in (shared, own) if p.is_file()]


def _module(path: Path):
    from .figures import core
    return sys.modules.get(core._module_name(path.resolve())) or core.load_module(path)


def functions(unit: UnitSpec, lesson: LessonSpec) -> dict[str, tuple[Path, str, int]]:
    """{figure name: (figure file, function name, line of the def)}."""
    from .figures.core import registered
    out = {}
    for path in figure_files(unit, lesson):
        for name, fn in registered(_module(path)).items():
            lines, start = inspect.getsourcelines(fn)
            off = next((i for i, ln in enumerate(lines) if ln.lstrip().startswith("def ")), 0)
            out[name] = (path, fn.__name__, start + off)
    return out


def _rel(p: Path, base: Path) -> str:
    try:
        return Path(p).resolve().relative_to(Path(base).resolve()).as_posix()
    except ValueError:
        return Path(p).resolve().as_posix()


def helpers(path: Path) -> list[str]:
    """Helper modules a figure file imports: sibling `_x` modules and lesson_builder.figures.*."""
    tree = ast.parse(Path(path).read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            mods.add(node.module)
    out = []
    for m in sorted(mods):
        if m.startswith("_") and (Path(path).parent / f"{m.split('.')[0]}.py").is_file():
            out.append(_rel(Path(path).parent / f"{m.split('.')[0]}.py", ROOT))
        elif m == "lesson_builder.figures" or m.startswith("lesson_builder.figures."):
            spec = importlib.util.find_spec(m)
            out.append(_rel(Path(spec.origin), ROOT) if spec and spec.origin else m)
    return out


def asset_note(p: Path) -> str:
    """First line of a sibling note (`x.png.source.txt`, `x.png.txt`, `x.txt`, `x.md`), e.g. the source page."""
    for cand in [p.with_name(p.name + s) for s in NOTE_SUFFIXES] + [p.with_suffix(".txt"), p.with_suffix(".md")]:
        if cand.is_file():
            text = cand.read_text(encoding="utf-8").strip()
            if text:
                return text.splitlines()[0].strip()
    return ""


def bundle_names(unit: UnitSpec, uses: list[Use], registered_names) -> dict[tuple[str, str], str]:
    """{(ref, copy): file name in the bundle}. Registered: <name>.png / <name>_key.png. Assets keep their file
    name (prefixed with the parent folder when two assets share one)."""
    names, taken = {}, {}
    for u in uses:
        if u.ref in registered_names:
            names[(u.ref, u.copy)] = f"{u.ref}_key.png" if u.copy == "key" and registered_names[u.ref] else \
                f"{u.ref}.png"
            continue
        p = (unit.dir / u.ref).resolve()
        name = p.name
        if taken.get(name, p) != p:
            name = f"{p.parent.name}_{p.name}"
        taken[name] = p
        names[(u.ref, u.copy)] = name
    return names


def default_dir(unit: UnitSpec, lesson: LessonSpec) -> Path:
    return unit.dir / "output" / "figures" / lesson.stem


def retain(unit: UnitSpec, lesson: LessonSpec, rendered: dict, out_dir: Path | None = None) -> RetainResult:
    """Copy the student and key PNG of every figure the document uses (and every asset image) into out_dir,
    write README.md, and remove files there that the document no longer uses."""
    out = Path(out_dir) if out_dir else default_dir(unit, lesson)
    res = RetainResult(out)
    uses = figure_uses(unit, lesson)
    reg = {n: bool(r.get("key")) for n, r in rendered.items()}
    names = bundle_names(unit, uses, reg)
    try:
        fns = functions(unit, lesson) if any(u.ref in reg for u in uses) else {}
    except Exception as e:  # a figure file that no longer imports still gets its PNGs retained
        fns = {}
        res.errors.append(f"ERROR {lesson.id}: figure source did not load: {e}")
    out.mkdir(parents=True, exist_ok=True)
    copies: dict[str, Path] = {}
    for u in uses:
        name = names[(u.ref, u.copy)]
        if u.ref in reg:
            r = rendered[u.ref]
            src = r["key"] if u.copy == "key" and r.get("key") else r["student"]
            if u.ref in fns:
                path, fn, line = fns[u.ref]
                source = f"`{_rel(path, unit.dir)}:{fn}` (line {line})"
            else:
                source = "(no source function found)"
                res.errors.append(f"ERROR {lesson.id} item {u.item}: figure {u.ref} has no source function in "
                                  f"{', '.join(_rel(p, unit.dir) for p in figure_files(unit, lesson)) or 'figures/'}")
        else:
            src = (unit.dir / u.ref).resolve()
            note = asset_note(src) or u.source
            source = f"`{u.ref}`" + (f" ({note})" if note else "")
            if not src.is_file():
                res.errors.append(f"ERROR {lesson.id} item {u.item}: asset {u.ref} is missing")
                src = None
        if src is not None:
            copies[name] = Path(src)
        res.rows.append(Row(u, name, source))
    for name, src in copies.items():
        dest = out / name
        shutil.copyfile(src, dest)
        res.files.append(dest)
    for p in sorted(out.iterdir()):
        if p.is_file() and p.name != "README.md" and p.name not in copies:
            p.unlink()
            res.removed.append(p)
    (out / "README.md").write_text(readme(unit, lesson, res, fns), encoding="utf-8")
    return res


def readme(unit: UnitSpec, lesson: LessonSpec, res: RetainResult, fns: dict) -> str:
    unit_rel = _rel(unit.dir, ROOT)
    lines = [f"# Figures for {lesson.id}", "",
             f"Retained from the build of `{_rel(lesson.path, unit.dir) if lesson.path else lesson.stem}`. "
             "Edit the source, not these PNGs.", "",
             "| Item | Copy | File | Source |", "|---|---|---|---|"]
    lines += [f"| {r.use.item} | {r.use.copy} | {r.file} | {r.source} |" for r in res.rows]
    files = sorted({p for p, _, _ in fns.values()})
    if files:
        lines += ["", "## Figure files and helpers", ""]
        for p in files:
            hs = helpers(p)
            lines.append(f"- `{_rel(p, unit.dir)}`" + (f" imports {', '.join(f'`{h}`' for h in hs)}" if hs else ""))
    lines += ["", "## Regenerate (from the repo root)", "", "```",
              f'uv run lesson-builder figs {unit_rel} -l "{lesson.stem}"',
              f'uv run lesson-builder build {unit_rel} -l "{lesson.stem}"',
              f'uv run lesson-builder retain {unit_rel} -l "{lesson.stem}"', "```", ""]
    return "\n".join(lines)


def _media(docx: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(docx) as z:
        return {n: z.read(n) for n in z.namelist() if n.startswith("word/media/")}


def _pixels(data: bytes):
    import io

    from PIL import Image
    with Image.open(io.BytesIO(data)) as im:
        return im.convert("RGBA")


def _same_pixels(a: bytes, b: bytes) -> bool:
    from PIL import ImageChops
    try:
        x, y = _pixels(a), _pixels(b)
    except Exception:
        return False
    return x.size == y.size and ImageChops.difference(x, y).getbbox() is None


def verify(unit: UnitSpec, lesson: LessonSpec, out_dir: Path | None = None) -> list[str]:
    """Retained PNGs vs the images embedded in the built DOCX files (student copy vs student DOCX, key vs key).
    Bytes are compared by SHA-1; on a mismatch, decoded pixels (so a re-encoded image still matches)."""
    out = Path(out_dir) if out_dir else default_dir(unit, lesson)
    where = lesson.id
    uses = figure_uses(unit, lesson)
    if not uses:
        return []
    if not (out / "README.md").is_file():
        return [f"ERROR {where}: no retained figures in {out}; run retain"]
    try:
        fns = functions(unit, lesson)
    except Exception:
        fns = {}
    reg = {u.ref: (out / f"{u.ref}_key.png").is_file() for u in uses
           if u.ref in fns or (out / f"{u.ref}.png").is_file()}
    names = bundle_names(unit, uses, reg)
    docs = outputs(unit, lesson)
    issues = []
    for kind in dict.fromkeys(u.doc for u in uses):
        docx = docs[kind]
        if not docx.is_file():
            issues.append(f"WARN  {where} {kind}: not built ({docx.name}); retained figures not verified")
            continue
        media = _media(docx)
        hashes = {hashlib.sha1(b).hexdigest(): n for n, b in media.items()}
        matched = set()
        for u in [u for u in uses if u.doc == kind]:
            name = names[(u.ref, u.copy)]
            p = out / name
            if not p.is_file():
                issues.append(f"ERROR {where} item {u.item}: {name} is not in {out.name}/; run retain")
                continue
            data = p.read_bytes()
            hit = hashes.get(hashlib.sha1(data).hexdigest())
            if hit is None:
                hit = next((n for n, b in media.items() if _same_pixels(data, b)), None)
            if hit is None:
                issues.append(f"ERROR {where} item {u.item}: retained {name} doesn't match any image in "
                              f"{docx.name}; rebuild, then retain")
            else:
                matched.add(hit)
        extra = sorted(set(media) - matched)
        if extra:
            issues.append(f"WARN  {where} {kind}: {len(extra)} embedded image(s) not in the figure bundle "
                          f"({', '.join(Path(n).name for n in extra)})")
    return issues

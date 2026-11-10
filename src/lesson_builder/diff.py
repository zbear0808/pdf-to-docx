from __future__ import annotations

import shutil
from pathlib import Path

from PIL import Image, ImageChops


def _changed_fraction(a: Image.Image, b: Image.Image) -> float:
    diff = ImageChops.difference(a.convert("L"), b.convert("L")).point(lambda v: 255 if v > 40 else 0)
    return diff.histogram()[255] / (a.width * a.height)


def _side_by_side(prev: Image.Image | None, new: Image.Image, out: Path) -> None:
    new = new.convert("RGB")
    prev = prev.convert("RGB") if prev is not None else Image.new("RGB", new.size, "white")
    w, h = max(prev.width, new.width), max(prev.height, new.height)

    def pad(im):
        canvas = Image.new("RGB", (w, h), "white")
        canvas.paste(im, (0, 0))
        return canvas

    p, n = pad(prev), pad(new)
    mask = ImageChops.difference(p.convert("L"), n.convert("L")).point(lambda v: 255 if v > 40 else 0)
    faded = Image.blend(n, Image.new("RGB", (w, h), "white"), 0.7)
    faded.paste(Image.new("RGB", (w, h), (230, 0, 0)), (0, 0), mask)
    sheet = Image.new("RGB", (w * 3 + 20, h), (128, 128, 128))
    for i, im in enumerate((p, n, faded)):
        sheet.paste(im, (i * (w + 10), 0))
    sheet.save(out)


def diff_renders(new_dir: Path, prev_dir: Path, out_dir: Path | None = None, threshold: float = 0.00005) -> list[str]:
    new_dir, prev_dir = Path(new_dir), Path(prev_dir)
    if out_dir is not None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        for old in out_dir.glob("*_diff.png"):  # a page that stopped changing must not keep its old diff
            old.unlink()
    changed = []
    for new_path in sorted(new_dir.glob("*.png")):
        prev_path = prev_dir / new_path.name
        with Image.open(new_path) as im:
            new = im.copy()
        prev = None
        if prev_path.exists():
            with Image.open(prev_path) as im:
                prev = im.copy()
        if prev is not None and prev.size == new.size and _changed_fraction(prev, new) <= threshold:
            continue
        changed.append(new_path.name)
        if out_dir is not None:
            _side_by_side(prev, new, out_dir / f"{new_path.stem}_diff.png")
    return changed


def snapshot(render_dir: Path, prev_dir: Path) -> None:
    render_dir, prev_dir = Path(render_dir), Path(prev_dir)
    if prev_dir.exists():
        shutil.rmtree(prev_dir)
    prev_dir.mkdir(parents=True)
    for p in render_dir.glob("*.png"):
        shutil.copy2(p, prev_dir / p.name)

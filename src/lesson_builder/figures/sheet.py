"""Contact sheet: every figure of a document, student and key side by side, at print size, plus lint."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from .core import DPI

SHEET_DPI = 150   # figures are shown at their printed width at this resolution


def _font(size):
    for name in ("arial.ttf", "calibri.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def contact_sheet(rendered: dict, out: Path, widths: dict[str, float] | None = None, sheet_w_in: float = 8.0) -> Path:
    """rendered: {name: {"student": png, "key": png|None, "meta": {...}}}. widths: placed width (in) per figure,
    from the document YAML; defaults to the drawn width. Tiles flow left to right and wrap."""
    widths = widths or {}
    title_f, lint_f = _font(14), _font(13)
    tiles = []
    for name, r in rendered.items():
        ims = [Image.open(p).convert("RGB") for p in (r["student"], r.get("key")) if p]
        drawn_w = ims[0].width / DPI
        placed = widths.get(name, drawn_w)
        s = placed / drawn_w
        # each image at the placed width (fig_w) or its own drawn width, as the builder places it; with
        # key_frame="union" the key is wider, so with fig_w set it prints smaller than the student copy
        ims = [im.resize((max(1, round(w * SHEET_DPI)), max(1, round(im.height / im.width * w * SHEET_DPI))))
               for im in ims for w in [placed if name in widths else im.width / DPI]]
        meta = r.get("meta") or {}
        pt = (meta.get("min_text_pt") or 0) * s
        title = f"{name}  {placed:.2f} in, text {pt:.1f} pt"
        if name in widths and meta.get("key_width_in") and abs(meta["key_width_in"] - drawn_w) > 0.01:
            title += f" (key {(meta.get('min_text_pt') or 0) * placed / meta['key_width_in']:.1f} pt)"
        head = [title] + [f"! {m}" for m in meta.get("lint", [])]
        w = sum(im.width for im in ims) + 20 * (len(ims) - 1)
        w = max(w, max(int(lint_f.getlength(h)) for h in head) + 4)
        h = 18 * len(head) + 6 + max(im.height for im in ims)
        tiles.append((ims, head, w, h))
    W = int(sheet_w_in * SHEET_DPI)
    W = max([W] + [t[2] + 40 for t in tiles])
    rows, cur, x = [], [], 20
    for t in tiles:
        if cur and x + t[2] > W - 20:
            rows.append(cur)
            cur, x = [], 20
        cur.append(t)
        x += t[2] + 30
    if cur:
        rows.append(cur)
    H = sum(max(t[3] for t in r) + 30 for r in rows) + 20
    sheet = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(sheet)
    y = 15
    for r in rows:
        x = 20
        for ims, head, w, h in r:
            for k, ln in enumerate(head):
                d.text((x, y + 18 * k), ln, fill=(0, 0, 0) if k == 0 else (190, 0, 0), font=title_f if k == 0 else lint_f)
            ix, iy = x, y + 18 * len(head) + 4
            for im in ims:
                sheet.paste(im, (ix, iy))
                d.rectangle([ix - 1, iy - 1, ix + im.width, iy + im.height], outline=(205, 205, 205))
                ix += im.width + 20
            x += w + 30
        y += max(t[3] for t in r) + 30
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out

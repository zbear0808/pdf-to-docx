"""Item numbering groups, `numbering: auto`, and {ref:id} / {num:id} references.

Runs on the raw YAML dict before validation (spec.load_lesson), so render and check see final text.
Numbering restarts after a `notes` section (the QuickNotes page); practice items are their own group.
"""
from __future__ import annotations

import re

REF = re.compile(r"\{(ref|num):([^{}\s]+)\}")
UNNUMBERED_KINDS = {"warmup", "notes"}   # numbering: auto leaves warm-up items unnumbered unless `n` is given


def dict_groups(data: dict) -> list[list[dict]]:
    """Item dicts per numbering group: [before notes, after notes, ..., practice]."""
    groups, cur = [], []
    for s in data.get("sections", []) or []:
        if s.get("kind") == "notes":
            groups.append(cur)
            cur = []
            continue
        cur += [(s.get("kind"), it) for it in s.get("items", []) or []]
    groups.append(cur)
    pr = data.get("practice") or {}
    groups.append([("practice", it) for r in pr.get("rows", []) or [] for it in r.get("cells", []) or []])
    return groups


def spec_groups(lesson) -> list[list]:
    """Item models per numbering group (same grouping as dict_groups)."""
    groups, cur = [], []
    for s in lesson.sections:
        if s.kind == "notes":
            groups.append(cur)
            cur = []
            continue
        cur += list(s.items)
    groups.append(cur)
    if lesson.practice:
        groups.append([it for r in lesson.practice.rows for it in r.cells])
    return groups


def _auto_number(data: dict):
    for g in dict_groups(data):
        k = 0
        for kind, it in g:
            if it.get("n") not in (None, ""):
                if str(it["n"]).isdigit():
                    k = int(it["n"])
                continue
            if kind in UNNUMBERED_KINDS or it.get("n") == "":
                it["n"] = None
                continue
            k += 1
            it["n"] = str(k)


def id_map(data: dict) -> dict[str, str]:
    """{id: printed number} for items ("4") and parts ("4b")."""
    out = {}
    for g in dict_groups(data):
        for _, it in g:
            n = it.get("n")
            if it.get("id") and n:
                out[str(it["id"])] = str(n)
            for p in it.get("parts", []) or []:
                if p.get("id") and n:
                    out[str(p["id"])] = f"{n}{str(p.get('label', '')).rstrip('.').strip()}"
    return out


def resolve(text: str, ids: dict[str, str]) -> str:
    """{ref:x} -> "Problem 4", {num:x} -> "4". Unknown ids stay as written (check reports them)."""
    def sub(m):
        if m.group(2) not in ids:
            return m.group(0)
        return ("Problem " if m.group(1) == "ref" else "") + ids[m.group(2)]
    return REF.sub(sub, text)


def unresolved(text: str) -> list[str]:
    return [m.group(0) for m in REF.finditer(str(text))]


def _walk(v, ids):
    if isinstance(v, str):
        return resolve(v, ids) if "{" in v else v
    if isinstance(v, list):
        return [_walk(x, ids) for x in v]
    if isinstance(v, dict):
        return {k: (x if k in ("id", "figure", "key_figure") else _walk(x, ids)) for k, x in v.items()}
    return v


def number_and_resolve(data: dict) -> dict:
    """In place: auto-number (if `numbering: auto`), then resolve references in every string."""
    if data.get("numbering") == "auto":
        _auto_number(data)
    ids = id_map(data)
    seen = set()
    for g in dict_groups(data):
        for _, it in g:
            for x in [it] + list(it.get("parts", []) or []):
                if x.get("id"):
                    if x["id"] in seen:
                        raise ValueError(f"duplicate item id {x['id']!r}")
                    seen.add(x["id"])
    if ids:
        for k in list(data):
            if k not in ("id",):
                data[k] = _walk(data[k], ids)
    return data

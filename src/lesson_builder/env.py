"""Load KEY=VALUE lines from .env (cwd, then repo root) into os.environ without overriding what is already set."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ENV = Path(__file__).resolve().parents[2] / ".env"
_loaded = False


def parse_env(text: str) -> dict[str, str]:
    out = {}
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if s.startswith("export "):
            s = s[7:].lstrip()
        key, eq, val = s.partition("=")
        key, val = key.strip(), val.strip()
        if not eq or not key:
            continue
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        elif " #" in val:
            val = val.split(" #", 1)[0].rstrip()
        out[key] = val
    return out


def load_env(paths: list[Path] | None = None, force: bool = False) -> dict[str, str]:
    """Sets each non-empty value whose key isn't in os.environ yet; the first file to name a key wins.
    Runs once per process unless `paths` or `force` is given. Returns what it set."""
    global _loaded
    if _loaded and paths is None and not force:
        return {}
    if paths is None:
        _loaded = True
        paths = [Path.cwd() / ".env", REPO_ENV]
    seen, out = set(), {}
    for p in paths:
        p = Path(p)
        if p.resolve() in seen or not p.is_file():
            continue
        seen.add(p.resolve())
        try:
            values = parse_env(p.read_text(encoding="utf-8"))
        except OSError:
            continue
        for k, v in values.items():
            if v and k not in os.environ:
                os.environ[k] = v
                out[k] = v
    return out

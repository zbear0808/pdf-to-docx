"""Resolve {value:item_id.fact|format} from checked problem models before rendering.

This is value lookup, not an expression language. It never evaluates Python or writes source YAML.
"""
from __future__ import annotations

import re
from pathlib import Path

from .problem_models import ScaledRectangles, format_value

VALUE = re.compile(r"\{value:([^{}]+)\}")


def resolve_values(data: dict) -> dict:
    """Return a new document dict with value references filled. Reject missing IDs/facts/formats early."""
    models = {}

    def collect(v):
        if isinstance(v, dict):
            if v.get("model") is not None:
                name = v.get("id")
                if not isinstance(name, str) or not name:
                    raise ValueError("an item with model: needs a stable id:")
                if name in models:
                    raise ValueError(f"duplicate modeled item id {name!r}")
                models[name] = ScaledRectangles.model_validate(v["model"])
            for k, x in v.items():
                if k != "model":
                    collect(x)
        elif isinstance(v, list):
            for x in v:
                collect(x)
    collect(data)

    def walk(v, path="document"):
        if isinstance(v, str):
            def sub(m):
                ref, _, style = m.group(1).partition("|")
                item, dot, fact = ref.rpartition(".")
                if not dot or item not in models:
                    raise ValueError(f"{path}: unknown modeled item in {m.group(0)}")
                facts = models[item].facts()
                if fact not in facts:
                    raise ValueError(f"{path}: unknown fact {fact!r} for item {item!r}")
                try:
                    return format_value(facts[fact], style or "tex")
                except ValueError as e:
                    raise ValueError(f"{path}: {e}") from e
            result = VALUE.sub(sub, v)
            if "{value:" in result:
                raise ValueError(f"{path}: malformed value reference in {v!r}")
            return result
        if isinstance(v, list):
            return [walk(x, f"{path}[{i}]") for i, x in enumerate(v)]
        if isinstance(v, dict):
            return {k: x if k == "model" else walk(x, f"{path}.{k}") for k, x in v.items()}
        return v
    return walk(data)


def model_for_figure(figure_file: str | Path, item_id: str) -> ScaledRectangles:
    """Load the model of an item in the YAML matching figures/<stem>.py (no generated cache needed)."""
    from .spec import load_lesson
    p = Path(figure_file).resolve()
    unit = p.parent.parent if p.parent.name == "figures" else p.parent
    matches = [unit / d / f"{p.stem}.yaml" for d in ("lessons", "assessments")]
    matches = [m for m in matches if m.is_file()]
    if len(matches) != 1:
        raise ValueError(f"{p.name}: expected exactly one matching lesson/assessment YAML, found {len(matches)}")
    lesson = load_lesson(matches[0])
    for it in lesson.all_items():
        if it.id == item_id and it.model is not None:
            return it.model
    raise ValueError(f"{matches[0].name}: no model on item {item_id!r}")


def resolved_document(lesson) -> dict:
    """Inspectable intermediate: rendered text and exact facts (fractions serialized as n/d)."""
    return {"document": lesson.model_dump(mode="json"),
            "facts": {it.id: {k: str(v) for k, v in it.model.facts().items()}
                      for it in lesson.all_items() if it.model is not None}}

"""Unit and lesson specs (YAML). A lesson YAML is the only copy of a lesson's content."""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

Lines = Union[str, list[str]]


def as_list(v: Optional[Lines]) -> list[str]:
    if v is None:
        return []
    return [v] if isinstance(v, str) else list(v)


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Table(_M):
    """Arrow table: header row of parts, one answer row ("Lands on")."""
    header: list[str]
    row_label: str = "Lands on"
    answers: list[str]
    first_w: float = 1.45
    height: float = 0.42


class Columns(_M):
    """Bordered write-in columns (notice/wonder, must/could/can't)."""
    headers: list[str]
    answers: list[list[str]] = Field(default_factory=list)
    height: float = 0.85
    italic: bool = False


class Draw(_M):
    """Steps on the left, drawing box on the right. The key shows `key_figure` (or the item figure's key layer)."""
    height: float = 3.0
    steps_w: float = 3.05
    key_figure: Optional[str] = None
    key_fig_w: float = 2.5
    key_note: Optional[str] = None


class Part(_M):
    label: str                       # "a."
    prompt: str
    answer: Optional[Lines] = None
    work: float = 0.6
    fill: Optional[list[list[str]]] = None      # [[label, answer], ...]
    fill_cols: Optional[int] = None
    box_w: float = 1.3
    frame: Optional[list[list[Union[str, float]]]] = None   # [[before, answer, after(, box_w)], ...]
    no_answer: bool = False


class Item(_M):
    n: Optional[str] = None          # "1" (printed "1."); None for unnumbered (warm-up, example)
    minutes: float = 0
    prompt: Lines = ""
    figure: Optional[str] = None     # registered figure name or asset path
    fig_w: Optional[float] = None
    key_figure: Optional[str] = None
    layout: Literal["side", "stacked"] = "side"
    choices: Optional[list[str]] = None
    choice_cols: int = 1
    answer: Optional[Lines] = None
    work: float = 0.8
    fill: Optional[list[list[str]]] = None
    fill_cols: Optional[int] = None
    box_w: float = 1.3
    frame: Optional[list[list[Union[str, float]]]] = None
    frame_box_w: float = 1.1
    box: Optional[float] = None      # bordered write-in box of this height; answer prints inside on the key
    table: Optional[Table] = None
    columns: Optional[Columns] = None
    draw: Optional[Draw] = None
    parts: list[Part] = Field(default_factory=list)
    after: float = 0.08
    page_break_after: bool = False
    no_answer: bool = False          # e.g. a "Together" item whose answer is the class discussion


class Section(_M):
    kind: Literal["warmup", "together", "partner", "notes", "cyu", "exit", "plain"]
    title: Optional[str] = None
    sub: Optional[str] = None
    intro: Optional[str] = None      # one line under the section heading
    box: Optional[Lines] = None      # bordered box under the heading (move bank, word bank)
    items: list[Item] = Field(default_factory=list)
    page_break_before: bool = False


class PracticeRow(_M):
    cells: list[Item] = Field(default_factory=list)   # 1 or 2 items side by side
    heading: Optional[str] = None                     # e.g. "SBA review" above this row
    page_break_before: bool = False


class Practice(_M):
    title: str
    rows: list[PracticeRow]
    selected: list[list[str]] = Field(default_factory=list)   # [["1", "D"], ...] answers to selected problems
    font_size: float = 10.5


class LessonSpec(_M):
    id: str                          # "2.1"
    title: str                       # page-1 title
    notes_title: str                 # page-3 title (QuickNotes page)
    framing: str
    materials: Optional[str] = None
    sections: list[Section]
    quicknotes: list[str]
    notes_height: float = 2.2
    practice: Optional[Practice] = None
    plan: str = ""                   # teacher lesson plan (Markdown), timing table included
    guide_notes: str = ""            # extra teacher-guide Markdown (changes, notes)
    path: Optional[Path] = Field(default=None, exclude=True)

    def items(self):
        for s in self.sections:
            for it in s.items:
                yield s, it

    @property
    def minutes(self) -> float:
        return sum(it.minutes for _, it in self.items())


class Budget(_M):
    minutes: int = 40
    handout_pages: int = 3
    practice_pages: int = 2


class UnitSpec(_M):
    course: str                      # "Geometry"
    unit: str                        # "2"
    unit_title: str
    period: str = ""
    budget: Budget = Field(default_factory=Budget)
    lessons: list[str]               # lesson YAML files, relative to lessons/
    figures: Optional[str] = "figures.py"
    packets: bool = True
    dir: Optional[Path] = Field(default=None, exclude=True)

    @field_validator("unit", mode="before")
    @classmethod
    def _str(cls, v):
        return str(v)

    @field_validator("period", mode="before")
    @classmethod
    def _period(cls, v):
        return v or ""

    def footer(self, lesson_id: str, kind: str = "") -> str:
        parts = [self.course, f"Unit {self.unit}", f"Lesson {lesson_id}" + (f" {kind}" if kind else "")]
        return "  |  ".join(parts)

    def lesson_specs(self) -> list[LessonSpec]:
        return [load_lesson(self.dir / "lessons" / f) for f in self.lessons]


def _read(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_unit(path: Path) -> UnitSpec:
    path = Path(path)
    if path.is_dir():
        path = path / "unit.yaml"
    u = UnitSpec(**_read(path))
    u.dir = path.parent
    return u


def load_lesson(path: Path) -> LessonSpec:
    data = _read(Path(path))
    if "id" in data:
        data["id"] = str(data["id"])
    for s in data.get("sections", []):
        for it in s.get("items", []) or []:
            if it.get("n") is not None:
                it["n"] = str(it["n"])
    for r in (data.get("practice") or {}).get("rows", []):
        for it in r.get("cells", []) or []:
            if it.get("n") is not None:
                it["n"] = str(it["n"])
    for row in (data.get("practice") or {}).get("selected", []):
        row[:] = [str(x) for x in row]
    spec = LessonSpec(**data)
    spec.path = Path(path)
    return spec

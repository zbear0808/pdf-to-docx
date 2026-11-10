"""Unit and lesson specs (YAML). A lesson YAML is the only copy of a lesson's content."""
from __future__ import annotations

from pathlib import Path
from typing import Literal, Optional, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .problem_models import ScaledRectangles

Lines = Union[str, list[str]]


def as_list(v: Optional[Lines]) -> list[str]:
    if v is None:
        return []
    return [v] if isinstance(v, str) else list(v)


class _M(BaseModel):
    model_config = ConfigDict(extra="forbid")


Demand = Literal["mem", "pwoc", "pwc", "dm"]   # Smith & Stein: memorization, procedures without/with connections,
ItemType = Literal["sr", "cr", "performance"]  # doing mathematics. sr = selected response, cr = constructed response
FIG_SIZES = {"small": 1.6, "medium": 2.4, "wide": 3.4}   # `fig:` size words -> printed width in inches


def _frame_rows(v):
    """Frame rows may be [before, answer, after(, w)] lists or {before, answer, after, w} mappings; both become lists."""
    if v is None:
        return v
    out = []
    for r in v:
        if isinstance(r, dict):
            extra = set(r) - {"before", "answer", "after", "w"}
            if extra:
                raise ValueError(f"frame row has unknown keys {sorted(extra)}")
            row = [r.get("before", ""), r["answer"], r.get("after", "")]
            if r.get("w") is not None:
                row.append(float(r["w"]))
            out.append(row)
        else:
            out.append(r)
    return out


class Target(_M):
    """Learning target in both forms (lesson-assessment-designer Stage 1)."""
    id: str                          # "LT1"
    understand: Optional[str] = None  # "Students will understand that ..."
    able_to: Optional[str] = None     # "Students will be able to ..."
    standard: Optional[str] = None    # "G.SRT.2"


class RubricLevel(_M):
    level: Union[int, str]           # 4, or "E"
    desc: str


class NoteBlock(_M):
    """Structured QuickNotes block: a bold heading (target id and/or title) and bullets."""
    target: Optional[str] = None
    title: Optional[str] = None
    bullets: list[str] = Field(default_factory=list)


class _Scored(_M):
    """Fields shared by items and parts: ids for {ref:...}, blueprint metadata, MC key, rubric."""
    id: Optional[str] = None         # referenced as {ref:<id>} ("Problem 4") or {num:<id>} ("4") in any text
    target: Optional[str] = None     # a Target id from the document or unit `targets:`
    type: Optional[ItemType] = None
    demand: Optional[Demand] = None
    standard: Optional[str] = None
    key: Optional[str] = None        # MC answer letter(s): "C" or "B, C, E" (select all)
    select_all: bool = False         # "select all that apply": several keys, no 3-4 choice rule
    distractors: dict[str, str] = Field(default_factory=dict)   # {"A": "added instead of multiplied"}
    rubric: list[RubricLevel] = Field(default_factory=list)
    scoring: Optional[Literal["epi"]] = None   # AP Stats E/P/I per part
    source: Optional[str] = None     # provenance, e.g. "Lesson 2.1 Practice p2 #3"

    @field_validator("frame", mode="before", check_fields=False)
    @classmethod
    def _frame(cls, v):
        return _frame_rows(v)

    @field_validator("key", mode="before", check_fields=False)
    @classmethod
    def _key(cls, v):
        return None if v is None else str(v).strip().upper()


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


class Part(_Scored):
    label: str                       # "a."
    prompt: str
    points: Optional[float] = None
    choices: Optional[list[str]] = None
    choice_cols: int = 1
    answer: Optional[Lines] = None
    work: float = 0.6
    fill: Optional[list[list[str]]] = None      # [[label, answer], ...]
    fill_cols: Optional[int] = None
    box_w: float = 1.3
    frame: Optional[list[list[Union[str, float]]]] = None   # [[before, answer, after(, box_w)], ...] or mappings
    frame_box_w: float = 1.1
    no_answer: bool = False


class Item(_Scored):
    model: Optional[ScaledRectangles] = None  # checked givens shared by text ({value:id.fact}) and figures
    n: Optional[str] = None          # "1" (printed "1."); None for unnumbered (warm-up, example). numbering: auto
    minutes: float = 0
    points: Optional[float] = None   # printed after the prompt as "(2 pts)"; assessments
    prompt: Lines = ""
    steps: list[str] = Field(default_factory=list)   # numbered steps printed under the prompt ("Step 1: ...")
    figure: Optional[str] = None     # registered figure name or asset path
    fig_w: Optional[float] = None
    fig: Optional[Literal["small", "medium", "wide"]] = None   # size word instead of fig_w (FIG_SIZES)
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

    @property
    def width(self) -> Optional[float]:
        """Printed figure width: fig_w, else the `fig` size word, else None (natural width)."""
        return self.fig_w if self.fig_w is not None else FIG_SIZES.get(self.fig or "")


class Section(_M):
    kind: Literal["warmup", "together", "partner", "notes", "cyu", "exit", "plain"]
    title: Optional[str] = None
    sub: Optional[str] = None
    intro: Optional[str] = None      # one line under the section heading
    box: Optional[Lines] = None      # bordered box under the heading (move bank, word bank)
    bank: list[str] = Field(default_factory=list)   # word/move bank: printed in a box, separated by " | "
    target: Optional[str] = None     # Target id this section assesses (score reporting by target)
    columns: Literal[1, 2] = 1       # 2: items flow in two columns (assessments)
    items: list[Item] = Field(default_factory=list)
    page_break_before: bool = False


class PracticeRow(_M):
    cells: list[Item] = Field(default_factory=list)   # 1 or 2 items side by side
    heading: Optional[str] = None                     # e.g. "SBA review" above this row
    page_break_before: bool = False


class Practice(_M):
    title: str
    rows: list[PracticeRow]
    # [["1", "D"], ...] answers written out; "auto" = every numbered practice item, answer taken from the item;
    # ["1", "4", "7"] (bare numbers) = those items, answers taken from the items
    selected: Union[Literal["auto"], list[Union[str, list[str]]]] = Field(default_factory=list)
    font_size: float = 10.5


class LessonSpec(_M):
    schema_version: Literal[1] = 1    # omitted on legacy documents; unsupported versions fail validation
    id: str                          # "2.1", or an assessment name like "3.6 Progress Check A"
    doc_type: Literal["lesson", "assessment", "reference"] = "lesson"   # reference: notes sheet, no key
    title: str                       # page-1 title
    notes_title: Optional[str] = None  # page-3 title (QuickNotes page); lessons only
    framing: Optional[str] = None
    materials: Optional[str] = None
    directions: Optional[str] = None   # bold line under the header (assessments: "Show your work.")
    header_right: Optional[str] = None  # deprecated: the builder prints Name / Per / Score
    total_points: Optional[float] = None
    max_pages: Optional[int] = None    # overrides the unit's handout page budget
    numbering: Literal["manual", "auto"] = "manual"   # auto: items without `n` are numbered 1, 2, ... per group
    targets: list[Target] = Field(default_factory=list)   # adds to the unit's targets
    set: Optional[str] = None          # assessment set, e.g. "Unit 3 Test"
    form: Optional[str] = None         # "A", "B", "Retake"
    parallel_to: Optional[str] = None  # id or stem of the form this one mirrors
    do_not_reuse: list[str] = Field(default_factory=list)   # globs of document stems this one must not reuse from
    source: Optional[str] = None       # source document(s) this was built from
    sections: list[Section]
    quicknotes: list[Union[str, NoteBlock]] = Field(default_factory=list)
    notes_height: float = 2.2
    notes_figure: Optional[str] = None   # figure printed inside the QuickNotes box, right of the notes
    notes_fig_w: float = 1.8
    practice: Optional[Practice] = None
    plan: str = ""                   # teacher lesson plan (Markdown), timing table included
    guide_notes: str = ""            # extra teacher-guide Markdown (changes, notes)
    path: Optional[Path] = Field(default=None, exclude=True)
    raw: str = Field(default="", exclude=True)   # the YAML text as read (for text-level checks)

    def items(self):
        for s in self.sections:
            for it in s.items:
                yield s, it

    @property
    def minutes(self) -> float:
        return sum(it.minutes for _, it in self.items())

    @property
    def points(self) -> float:
        return sum((it.points or 0) + sum(p.points or 0 for p in it.parts) for _, it in self.items())

    @property
    def stem(self) -> str:
        return self.path.stem if self.path else self.id

    def all_items(self):
        """Section items, then practice cells."""
        for _, it in self.items():
            yield it
        if self.practice:
            for r in self.practice.rows:
                yield from r.cells

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
    lessons: list[str]               # lesson YAML files, relative to lessons/, in teaching order
    assessments: list[str] = Field(default_factory=list)   # globs relative to the unit dir, e.g. assessments/*.yaml
    figures: Optional[str] = "figures.py"   # a file, or a folder of <doc stem>.py files (one per document)
    packets: bool = True
    targets: list[Target] = Field(default_factory=list)   # unit learning targets, shared by every document
    dir: Optional[Path] = Field(default=None, exclude=True)

    @field_validator("unit", mode="before")
    @classmethod
    def _str(cls, v):
        return str(v)

    @field_validator("period", mode="before")
    @classmethod
    def _period(cls, v):
        return v or ""

    def footer(self, lesson_id: str, kind: str = "", doc_type: str = "lesson") -> str:
        doc = f"Lesson {lesson_id}" if doc_type == "lesson" else lesson_id
        parts = [self.course, f"Unit {self.unit}", doc + (f" {kind}" if kind else "")]
        return "  |  ".join(parts)

    def doc_paths(self) -> list[Path]:
        paths = [self.dir / "lessons" / f for f in self.lessons]
        for g in self.assessments:
            paths += sorted(self.dir.glob(g))
        return paths

    def lesson_specs(self, only: Optional[list[str]] = None) -> list[LessonSpec]:
        """Load specs in order. `only` matches file stems or ids; unmatched files aren't parsed, so one document
        can be built while another is mid-edit."""
        out = []
        for p in self.doc_paths():
            if only and p.stem not in only:
                try:
                    if str(_read(p).get("id", "")) not in only:
                        continue
                except Exception:
                    continue
            out.append(load_lesson(p))
        return out


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
    from .numbering import number_and_resolve
    from .resolve import resolve_values
    path = Path(path)
    raw = path.read_text(encoding="utf-8")
    data = resolve_values(yaml.safe_load(raw) or {})
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
    sel = (data.get("practice") or {}).get("selected")
    if isinstance(sel, list):
        data["practice"]["selected"] = [[str(x) for x in row] if isinstance(row, list) else str(row) for row in sel]
    number_and_resolve(data)
    spec = LessonSpec(**data)
    spec.path = path
    spec.raw = raw
    return spec

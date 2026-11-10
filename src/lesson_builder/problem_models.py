"""Checked problem data shared by document text and figures. Values are exact fractions."""
from __future__ import annotations

from decimal import Decimal, localcontext
from fractions import Fraction
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def format_value(value: Fraction | str, style: str = "tex") -> str:
    """TeX has no dollar delimiters. Decimal formats round, trim zeros, and never use binary floats."""
    if isinstance(value, str):
        if style != "tex":
            raise ValueError(f"cannot format text as {style}")
        return value
    if style == "tex":
        if value.denominator == 1:
            return str(value.numerator)
        sign = "-" if value < 0 else ""
        return rf"{sign}\frac{{{abs(value.numerator)}}}{{{value.denominator}}}"
    if style not in ("decimal1", "decimal2", "comma2"):
        raise ValueError(f"unknown value format {style!r}; use tex, decimal1, decimal2, or comma2")
    places = 1 if style == "decimal1" else 2
    with localcontext() as ctx:
        ctx.prec = max(28, len(str(abs(value.numerator))) + len(str(value.denominator)) + places + 2)
        number = Decimal(value.numerator) / Decimal(value.denominator)
        text = f"{number:.{places}f}".rstrip("0").rstrip(".")
    return text.replace(".", ",") if style == "comma2" else text


class ScaledRectangles(BaseModel):
    """Two rectangles with one known corresponding dimension and one given variable dimension.

    `given_on=image` asks students to divide to recover the original dimension. All dimensions,
    labels, and answers are derived from the three givens; no second answer is stored in Python.
    """
    model_config = ConfigDict(extra="forbid", frozen=True)
    kind: Literal["scaled_rectangles"]
    source_name: str = Field(min_length=1)
    image_name: str = Field(min_length=1)
    known_axis: Literal["width", "height"] = "height"
    source_known: Fraction = Field(gt=0)
    image_known: Fraction = Field(gt=0)
    given_other: Fraction = Field(gt=0)
    given_on: Literal["source", "image"] = "source"
    given_symbol: str = "x"
    unknown_symbol: str = "y"

    @field_validator("source_known", "image_known", "given_other", mode="before")
    @classmethod
    def _number(cls, v):
        if isinstance(v, bool):
            raise ValueError("a length must be a number, not a boolean")
        # Decimal YAML numbers are interpreted as written, not as their binary float expansion.
        try:
            return Fraction(str(v)) if isinstance(v, (float, int, str)) else v
        except ZeroDivisionError as e:
            raise ValueError("a length cannot have a zero denominator") from e

    @field_validator("source_name", "image_name", "given_symbol", "unknown_symbol")
    @classmethod
    def _name(cls, v):
        import re
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9]*", v):
            raise ValueError("names must be letters followed by optional letters or digits")
        return v

    @model_validator(mode="after")
    def _distinct(self):
        if self.source_name == self.image_name or self.given_symbol == self.unknown_symbol:
            raise ValueError("source/image names and given/unknown symbols must be distinct")
        return self

    @property
    def scale(self) -> Fraction:
        return self.image_known / self.source_known

    @property
    def source_other(self) -> Fraction:
        return self.given_other if self.given_on == "source" else self.given_other / self.scale

    @property
    def image_other(self) -> Fraction:
        return self.source_other * self.scale

    def dimensions(self) -> tuple[tuple[Fraction, Fraction], tuple[Fraction, Fraction]]:
        """Source and image (width, height), in mathematical units."""
        src, img = (self.source_known, self.source_other), (self.image_known, self.image_other)
        return (src, img) if self.known_axis == "width" else (src[::-1], img[::-1])

    def labels(self) -> tuple[str, str, str, str]:
        """Bottom/left label for each rectangle, with variable names instead of their answers."""
        s, i = ((self.given_symbol, self.unknown_symbol) if self.given_on == "source"
                else (self.unknown_symbol, self.given_symbol))
        src, img = (format_value(self.source_known), s), (format_value(self.image_known), i)
        pairs = (src, img) if self.known_axis == "width" else (src[::-1], img[::-1])
        return tuple(f"${label}$" for pair in pairs for label in pair)

    def facts(self) -> dict[str, Fraction | str]:
        return {
            "source_name": self.source_name, "image_name": self.image_name,
            "given_symbol": self.given_symbol, "unknown_symbol": self.unknown_symbol,
            "source_known": self.source_known, "image_known": self.image_known,
            "given_other": self.given_other, "scale": self.scale, "inverse_scale": 1 / self.scale,
            "source_other": self.source_other, "image_other": self.image_other,
            "answer": self.image_other if self.given_on == "source" else self.source_other,
            "multiply_given": self.given_other * self.scale,
        }

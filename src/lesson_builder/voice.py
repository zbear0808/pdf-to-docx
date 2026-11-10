"""Voice checks for student-facing text: AI vocabulary, dashes, exclamation points. Math ($...$) and code are skipped."""
from __future__ import annotations

import re

# The single code copy of the cut-word list. Source of truth: .agents/skills/authentic-writer/SKILL.md
# ("Words and phrases to cut"); keep the two in sync.
BANNED = {
    "delve", "tapestry", "vibrant", "testament", "unlock", "multifaceted", "navigate", "underscore",
    "comprehensive", "crucial", "pivotal", "dynamic", "robust", "intricate", "meticulous", "seamless", "foster",
    "garner", "leverage", "showcase", "embark", "journey", "realm", "landscape", "beacon",
    "it's important to note", "serves as", "plays a key role", "moreover", "furthermore", "additionally",
    "consequently", "in conclusion", "let's dive in", "explore the world of",
}
def _form(w: str) -> str:
    """A word and its -s/-ed/-ing forms ("navigate" -> navigates, navigated, navigating); phrases as written."""
    if " " in w:
        return re.escape(w)
    return re.escape(w[:-1]) + "(?:e|es|ed|ing)" if w.endswith("e") else re.escape(w) + "(?:s|es|ed|ing)?"


_WORDS = re.compile(r"\b(" + "|".join(_form(w) for w in sorted(BANNED, key=len, reverse=True)) + r")\b", re.I)
_MATH = re.compile(r"\$\$.*?\$\$|\$[^$]*\$|`[^`]*`", re.S)
_DASH = re.compile(r"[\u2014\u2013]|(?<=\S) --? (?=\S)")


def prose(text: str) -> str:
    """Text with $...$ math and `code` spans blanked out."""
    return _MATH.sub(" ", str(text)).replace("\u2019", "'")


def _ctx(text: str, i: int, j: int) -> str:
    return "..." + text[max(0, i - 20):j + 20].replace("\n", " ").strip() + "..."


def voice_issues(text: str) -> list[str]:
    t = prose(text)
    out = []
    for m in _WORDS.finditer(t):
        out.append(f"banned word '{m.group(1).lower()}' (authentic-writer): {_ctx(t, m.start(), m.end())}")
    for m in _DASH.finditer(t):
        if m.group(0).strip() == "-" and re.match(r"[\d)]", t[m.start() - 1]) and re.match(r"[\d(]", t[m.end():]):
            continue   # "3 - 2" written outside math
        out.append(f"dash in prose (use a comma, colon, or two sentences): {_ctx(t, m.start(), m.end())}")
    for m in re.finditer(r"!(?!=)", t):
        out.append(f"exclamation point: {_ctx(t, m.start(), m.end())}")
    return out

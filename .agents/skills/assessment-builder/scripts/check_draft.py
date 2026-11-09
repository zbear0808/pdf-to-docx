"""Mechanical checks for an assessment-builder Markdown draft.

Usage:
    python check_draft.py _temp/specs/draft.md [--key _temp/specs/key.md] [--voice-only]

Draft conventions (see assessment-builder SKILL.md):
    **Total**: 30 pts                      (optional header line)
    #### Problem 4 (Title) [3 pts]         (one per problem)
    - (A) ...  through  - (D) ...          (MC choices; "- [A]" also accepted)
Key conventions:
    4. (B) reason...    or    4a. 2 pts ...
Exit code 1 if any ERROR is found.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

BANNED = [
    "delve", "tapestry", "vibrant", "testament", "unlock", "multifaceted", "navigate",
    "underscore", "comprehensive", "crucial", "pivotal", "robust", "intricate", "meticulous",
    "seamless", "foster", "garner", "showcase", "embark", "realm", "landscape", "beacon",
    "moreover", "furthermore", "additionally", "consequently", "in conclusion",
    "it's important to note", "it is important to note", "serves as", "plays a key role",
    "let's dive", "dive into", "explore the world",
]
PROBLEM_RE = re.compile(r"^####\s+Problem\s+(\d+)\b.*?\[(\d+(?:\.\d+)?)\s*pts?\]", re.I)
CHOICE_RE = re.compile(r"^\s*-\s*[\[(]([A-Z])[\])]\s*(.*)$")
TOTAL_RE = re.compile(r"\*\*Total\*\*\s*:\s*(\d+(?:\.\d+)?)", re.I)
KEY_RE = re.compile(r"^\s*(\d+)\.\s*\(?([A-D])\)?(?:\s|$)")


def strip_code_and_math(text: str) -> str:
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    text = re.sub(r"\$\$.*?\$\$", "", text, flags=re.S)
    return re.sub(r"\$[^$\n]*\$", "", text)


def voice_checks(text: str, issues: list[str], label: str) -> None:
    for n, line in enumerate(strip_code_and_math(text).splitlines(), 1):
        if "\u2014" in line or "\u2013" in line or re.search(r"\s--\s", line):
            issues.append(f"ERROR {label}:{n} dash in prose: {line.strip()[:80]}")
        low = line.lower()
        for w in BANNED:
            if re.search(rf"\b{re.escape(w)}", low):
                issues.append(f"WARN  {label}:{n} banned phrase '{w}': {line.strip()[:80]}")
        if re.match(r"^#{2,3}\s", line):
            later = [w for w in re.sub(r"^#+\s*", "", line).split()[1:] if w.isalpha() and len(w) > 3]
            if len(later) >= 2 and all(w[0].isupper() for w in later):
                issues.append(f"WARN  {label}:{n} heading may be Title Case: {line.strip()[:80]}")
        if "!" in line and not line.lstrip().startswith(("|", "<!--")) and "!=" not in line:
            issues.append(f"WARN  {label}:{n} exclamation point: {line.strip()[:80]}")


def structure_checks(text: str, issues: list[str]) -> dict[int, int]:
    problems: list[tuple[int, float, list[tuple[str, str]], int]] = []
    current = None
    in_header = True
    for n, line in enumerate(text.splitlines(), 1):
        m = PROBLEM_RE.match(line)
        if m:
            in_header = False
            current = [int(m.group(1)), float(m.group(2)), [], n]
            problems.append(current)
            continue
        if line.startswith("#### ") and "problem" in line.lower() and not m:
            issues.append(f"ERROR draft:{n} problem heading missing '[N pts]': {line.strip()}")
        c = CHOICE_RE.match(line)
        if c and current is not None:
            current[2].append((c.group(1), c.group(2).strip()))
        if not in_header and re.search(r"_{4,}", line):
            issues.append(f"WARN  draft:{n} blank underline in problem text (use Workspace)")

    nums = [p[0] for p in problems]
    if nums and nums != list(range(nums[0], nums[0] + len(nums))):
        issues.append(f"ERROR problem numbers not continuous: {nums}")
    for num, cnt in Counter(nums).items():
        if cnt > 1:
            issues.append(f"ERROR problem {num} appears {cnt} times")

    mc_count = 0
    for num, _pts, choices, line_no in problems:
        if not choices:
            continue
        mc_count += 1
        labels = [c[0] for c in choices]
        expected = [chr(ord("A") + i) for i in range(len(labels))]
        if labels != expected:
            issues.append(f"ERROR problem {num} choice labels {labels}, expected {expected}")
        if len(labels) not in (3, 4):
            issues.append(f"WARN  problem {num} has {len(labels)} choices")
        texts = [c[1].lower() for c in choices]
        if len(set(texts)) != len(texts):
            issues.append(f"ERROR problem {num} has duplicate choices")
        if any(not t for t in texts):
            issues.append(f"ERROR problem {num} has an empty choice")
        for t in texts:
            if re.search(r"\b(all|none) of the above\b|\b[a-d] and [a-d]\b", t):
                issues.append(f"ERROR problem {num} uses all/none of the above or combined option")
        lengths = [len(c[1]) for c in choices if c[1]]
        if lengths and max(lengths) > 2.5 * max(1, sorted(lengths)[len(lengths) // 2]) and max(lengths) > 25:
            issues.append(f"WARN  problem {num} one choice is much longer than the others")

    total_pts = sum(p[1] for p in problems)
    tm = TOTAL_RE.search(text)
    if tm and abs(float(tm.group(1)) - total_pts) > 1e-6:
        issues.append(f"ERROR header total {tm.group(1)} pts but problems sum to {total_pts:g} pts")
    print(f"problems: {len(problems)}  multiple choice: {mc_count}  points: {total_pts:g}")
    return {p[0]: len(p[2]) for p in problems if p[2]}


def key_checks(key_text: str, mc: dict[int, int], issues: list[str]) -> None:
    answers: dict[int, str] = {}
    for line in key_text.splitlines():
        m = KEY_RE.match(line)
        if m and int(m.group(1)) in mc:
            answers[int(m.group(1))] = m.group(2)
    for num in mc:
        if num not in answers:
            issues.append(f"ERROR key missing answer for MC problem {num}")
        elif ord(answers[num]) - ord("A") >= mc[num]:
            issues.append(f"ERROR key answer {answers[num]} for problem {num} is not a listed choice")
    seq = [answers[k] for k in sorted(answers)]
    if seq:
        dist = Counter(seq)
        print("key positions: " + "  ".join(f"{k}={dist.get(k, 0)}" for k in "ABCD"))
        if len(seq) >= 4 and max(dist.values()) > 0.5 * len(seq):
            issues.append(f"WARN  key letter {dist.most_common(1)[0][0]} used for over half the MC items")
        run = 1
        for a, b in zip(seq, seq[1:]):
            run = run + 1 if a == b else 1
            if run == 3:
                issues.append(f"WARN  key has 3+ of the same letter in a row ({a})")
                break


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("draft", type=Path)
    ap.add_argument("--key", type=Path)
    ap.add_argument("--voice-only", action="store_true")
    a = ap.parse_args()
    text = a.draft.read_text(encoding="utf-8")
    issues: list[str] = []
    voice_checks(text, issues, a.draft.name)
    if not a.voice_only:
        mc = structure_checks(text, issues)
        if a.key:
            key_text = a.key.read_text(encoding="utf-8")
            voice_checks(key_text, issues, a.key.name)
            key_checks(key_text, mc, issues)
    for i in issues:
        print(i)
    errors = sum(i.startswith("ERROR") for i in issues)
    print(f"{errors} errors, {len(issues) - errors} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())

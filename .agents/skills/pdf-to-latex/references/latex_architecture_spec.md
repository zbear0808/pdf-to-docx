# LaTeX Architecture & Preamble Specification

This document details the architectural design, CTAN packages, and macro conventions utilized by the `pdf_to_latex` compilation engine.

---

## 1. Document Classes

The compiler natively supports four standard classes configured via `--doc-class`:

| Document Class | Use Case | Key Features |
| :--- | :--- | :--- |
| `article` | Research papers, technical summaries, multi-column briefs | Section hierarchy (`\section`, `\subsection`), standard title block |
| `exam` | Problem sets, quizzes, exams, worksheets | Points calculation, `\question`, `\part`, `choices` env, `\makeemptybox` |
| `report` | Lengthy reports, whitepapers, documentation | Supports `\chapter`, abstract, front matter |
| `scrartcl` | Modern European/KOMA-Script typography | High typographical refinement, sans-serif headings |

---

## 2. Preamble & Package Stack

The generated `.tex` files include a rock-solid, conflict-free package stack:

```latex
% Core Typography & Geometry
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage[letterpaper,margin=1.0in]{geometry}
\usepackage{microtype}

% Mathematics & Science
\usepackage{amsmath,amssymb,amsfonts,mathtools}
\usepackage{bm}

% Tables & Data Layout
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{tabularx}
\usepackage{multirow}
\usepackage{array}
\usepackage{colortbl}
\usepackage{caption}

% Colors & Framed Callout Boxes
\usepackage{xcolor}
\usepackage[most]{tcolorbox}

% Lists & Formatting
\usepackage{enumitem}
\usepackage{ulem}
\normalem

% Hyperlinks
\usepackage{hyperref}
```

---

## 3. Custom Environments

### Callout Box (`calloutbox`)
Used for warnings, notes, theorems, and definitions:
```latex
\newtcolorbox{calloutbox}[1][]{
    colback=CalloutBg,
    colframe=PrimaryColor,
    boxrule=1.5pt,
    arc=3pt,
    left=10pt,right=10pt,top=8pt,bottom=8pt,
    fonttitle=\bfseries,
    #1
}
```

### Student Response Box (`responsebox`)
Used for student fill-in areas or open-ended responses:
```latex
\newtcolorbox{responsebox}[1][]{
    colback=white,
    colframe=CalloutFrame,
    boxrule=1pt,
    arc=2pt,
    left=8pt,right=8pt,top=8pt,bottom=8pt,
    #1
}
```

---

## 4. Escaping Rules

The compiler implements selective escaping:
- Characters escaped in standard text: `&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`.
- Embedded inline math `$ ... $` and display equations `\[ ... \]` are detected and preserved unescaped.
- Backslashes in regular text are converted to `\textbackslash{}` unless part of intentional math or command sequences.

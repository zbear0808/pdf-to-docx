# Math, Tables & Exam Formatting Specification

Guidelines for representing mathematical formulas, complex tables, and exam worksheets in LaTeX.

---

## 1. Mathematical Formulas

### Inline Math
- Standard variables, symbols, and short expressions: `$z = \frac{x - \mu}{\sigma}$`, `$\bar{x}$`, `$\sigma = \sqrt{np(1-p)}$`.
- Greek letters: `$\alpha$`, `$\beta$`, `$\mu$`, `$\sigma$`, `$\chi^2$`.

### Display Equations
Numbered:
```latex
\begin{equation}
  P(X = k) = \binom{n}{k} p^k (1-p)^{n-k}
  \label{eq:binomial}
\end{equation}
```

Unnumbered:
```latex
\[
  t = \frac{\bar{x}_1 - \bar{x}_2}{\sqrt{\frac{s_1^2}{n_1} + \frac{s_2^2}{n_2}}}
\]
```

Multline / Aligned:
```latex
\begin{align*}
  \text{SSE} &= \sum (y_i - \hat{y}_i)^2 \\
  r &= \frac{\sum (x_i - \bar{x})(y_i - \bar{y})}{\sqrt{\sum (x_i - \bar{x})^2 \sum (y_i - \bar{y})^2}}
\end{align*}
```

---

## 2. Professional Tables (`booktabs`)

LaTeX tables should avoid vertical lines and double horizontal lines. Always use `booktabs`:

```latex
\begin{table}[htbp]
  \centering
  \caption{Sample Statistical Summary}
  \begin{tabular}{lrrr}
    \toprule
    \textbf{Group} & \textbf{Sample Size ($n$)} & \textbf{Mean ($\bar{x}$)} & \textbf{Std Dev ($s$)} \\
    \midrule
    Treatment A & 45 & 12.4 & 1.82 \\
    Treatment B & 48 & 14.1 & 2.05 \\
    Control     & 50 & 10.2 & 1.45 \\
    \bottomrule
  \end{tabular}
\end{table}
```

For full text-width tables with text wrapping in columns, use `tabularx`:
```latex
\begin{table}[htbp]
  \centering
  \caption{Diagnostic Rubric}
  \begin{tabularx}{\linewidth}{lX}
    \toprule
    \textbf{Score} & \textbf{Criteria} \\
    \midrule
    Essentially Correct (E) & Complete justification with correct numerical value. \\
    Partially Correct (P) & Correct formula applied but calculation error present. \\
    Incorrect (I) & Fundamentally flawed statistical reasoning. \\
    \bottomrule
  \end{tabularx}
\end{table}
```

---

## 3. Exam & Quiz Structure (`exam` class)

For AP Statistics quizzes, STEM tests, and worksheets:

```latex
\begin{questions}

\question[4]
A random sample of 25 students had a mean score of 82 with a standard deviation of 6.
Construct a 95\% confidence interval for the population mean score.

\begin{parts}
\part[2] Check the necessary conditions for inference.
\makeemptybox{1.5in}

\part[2] Compute the interval and interpret the result in context.
\makeemptybox{2.0in}
\end{parts}

\question[2]
Which of the following statistics is resistant to extreme outliers?
\begin{choices}
  \choice Mean
  \choice Standard Deviation
  \choice Median
  \choice Range
\end{choices}

\end{questions}
```

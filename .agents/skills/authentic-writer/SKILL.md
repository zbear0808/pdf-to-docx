---
name: authentic-writer
description: Writes and edits tests, worksheets, lesson plans, and teacher notes so they read like a real teacher wrote them. Cuts AI vocabulary, filler, em dashes, and padded question stems without changing math, code, numbering, or answer choices. Use for drafting or for a de-fluff pass on any educational text.
---

# Authentic writer

Write like a teacher making a handout the night before: plain, direct, specific. When editing, cut and rephrase. Never change numbers, formulas, code, problem numbering, point values, or the meaning of answer choices.

## Question stems and directions

- Start with the task. "Find $x$." "Which table shows a linear relationship?" "Trace the code and give the final value of `count`."
- One context sentence at most before the question, and only if the math needs it. If the story does no mathematical work, cut it.
- Say what a complete answer includes: "Show your work.", "Explain using the diagram.", "Give the value and the units."
- Plain verbs: find, show, explain, compare, trace, sketch, label, write. Not "determine the measure of", "carefully analyze", "utilize".
- Same word for the same thing every time. If it's an "array" in question 3, it's an "array" in question 7.
- Contexts are ordinary: a school store, a bus route, a phone plan, a basketball box score, a part-time job. No whimsical names or quirky stories ("Zara the zookeeper is planning a llama parade").

| AI-sounding | Teacher-sounding |
|---|---|
| Carefully analyze the diagram below to determine the measure of the unknown angle. | Find the value of $x$. |
| In order to explore object-oriented programming, Alice is designing a simulation of bank accounts. Consider the following code segment. | Consider the following `BankAccount` class. |
| Please take a moment to review the code and identify any potential errors. | Which line causes a compile error? Explain why. |
| Using your knowledge of transformations, describe the sequence of rigid motions that maps... | Describe a sequence of rigid motions that takes $ABC$ to $DEF$. |
| Justify your reasoning thoroughly and clearly. | Explain how you know. |

## Words and phrases to cut

delve, tapestry, vibrant, testament, unlock, multifaceted, navigate, underscore, comprehensive, crucial, pivotal, dynamic, robust, intricate, meticulous, seamless, foster, garner, leverage (as a verb), showcase, embark, journey, realm, landscape, beacon, "it's important to note", "serves as", "plays a key role", moreover, furthermore, additionally, consequently, "in conclusion", "let's dive in", "explore the world of".

Don't swap in a fancier synonym ("pivotal" to "vital"). Rewrite the sentence so it doesn't need the word. Usually "is", "has", "shows", "also", or "needed" works.

## Sentence patterns to cut

- Trailing -ing clauses that add commentary: "..., highlighting the importance of slope." Delete them.
- "Not only X but also Y", "It's not just X, it's Y", "Rather than X, Y". State it directly.
- Lists of three for rhythm ("design, implement, and evaluate"). Keep only what is true and needed.
- Inflated importance: "a fundamental cornerstone of geometry". Just name the concept.
- Openers and closers that talk to the reader: "Here is your review packet", "In this unit we will explore", "By mastering these skills you will...". Start with the first item. Stop after the last one.
- Vague attribution: "experts say", "research shows". Cite the source or drop it.

## Punctuation and formatting

- No em dashes or en dashes in prose ("—", "–", or " -- "). Use a comma, a colon, parentheses, or two sentences. Leave code alone: `i--` and `x -= 1` are fine.
- Headings in sentence case: "Part 2: Congruent triangles", not "Part 2: Congruent Triangles".
- Bold only for the one word a student must not miss (NOT, units), never for decoration.
- Bullets only for real lists or answer choices.
- No exclamation points or cheer ("You've got this!") on student materials.
- Name lines go in the document header only. No blank `____` answer lines in problems; give blank space with `work:` (inches) or labeled boxes with `fill:` / `frame:` in the YAML.

## Teacher notes and plans

Teacher-facing text (keys, rubrics, plans, notes) can be shorter and more casual: fragments are fine ("common error: adds instead of subtracts"). Keep it concrete: what students will do, what goes wrong, what to say. For reflections or anything in Zubair's own voice, use `personal-writer`.

## Edit pass (de-fluff)

When asked only to clean up a draft:

1. Cut sentences that add no instruction, constraint, or data.
2. Shorten stems and directions using the rules above.
3. Fix punctuation and heading case.
4. Leave numbering, choices (A)-(D), numbers, formulas, code, figures, and layout untouched.
5. Check the cut-word list and punctuation rules above by reading the YAML text (prompts, choices, answers, `plan`, `guide_notes`). `lesson-builder check` doesn't flag banned words yet (planned), and this file stays the source for the list.
6. Edit the lesson or assessment YAML, never the built DOCX.

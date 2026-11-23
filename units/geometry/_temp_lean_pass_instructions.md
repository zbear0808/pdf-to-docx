# Lean pass: cut extra instructions and flair (Nov 16, round 3)

Teacher: "We don't need to tell the students to do that [early finishers]. It's fine being less verbose. Get rid of anything that's extra instructions or flair that isn't needed."

Load `authentic-writer` (its "Question stems and directions" section was updated for this). Edit text only. Don't change the math, numbers, item order, numbering, answers, figures, boxes, frames, or minutes.

## Student-facing (handout, practice)

Cut:
- Boilerplate the layout already gives: "Fill in each box.", "Fill in the box.", "Write your answer in the box.", "Write each answer in its box.", "Show your work." (keep it only where the item has work space and the work is the point, and say it once, not on every item), "Use the figure.", "Answer without making the drawing." unless it changes the task.
- Pointers to earlier work that the student doesn't need ("Use your table from Problem 2." when the item is answerable without it). Keep a pointer when the item really depends on that work.
- Hints, pep, and flair: "Hint: ...", "Sum it up.", "Pretend...", "Think about...", cute lead-ins, a story sentence that does no math.
- Talk moves aimed at students ("Compare with the pair next to you.", "Turn and talk.") go into the plan if they're useful, off the handout.
- Framing box: cut it to the one question, with no "Today's question:" label and no recap of the last lesson. If the question just restates the title, delete `framing` entirely.
- Section `intro` lines and `box` text that repeat the prompt.

Keep:
- Sentence frames, labeled fill-in boxes, reason banks, vocabulary definitions students need (MLL supports for Period 4).
- Every given, every constraint, the question itself, and directions that change what the answer is (e.g. "Match the vertices in order.", "Explain how you know.").
- `materials`.

Shorten stems with authentic-writer's rules ("Start with the task").

## Teacher-facing (plan, guide_notes)

- Delete the "Early finishers: start the practice problems." line.
- Cut filler and repetition in `plan` paragraphs: keep the timing table, what the teacher does, the assessing/advancing questions, the common errors, and the MLL supports. Fragments are fine.
- `guide_notes`: keep the dated change-log lines as they are, plus a one-line "Nov 16 (round 3): cut extra instructions and flair." Don't rewrite the history.

## Check and build

After each lesson:
1. `uv run lesson-builder check <unit> -l <stem>` (0 errors).
2. `uv run lesson-builder build <unit> -l <stem> --no-packets` (up to 2 builds; the page fill may improve). Make sure the handout is still 2 pages where it was 2, and that the key matches.
3. Log one line per kind of cut in `_temp/specs/<stem>/changes.md` under "Round 3 (lean)", with counts, e.g. `prompts: removed "Fill in each box." x4`.

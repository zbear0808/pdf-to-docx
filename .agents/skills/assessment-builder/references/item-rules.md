# Item writing rules (verified against course readings)

Use this file while drafting and reviewing. Every rule was checked against the reading text. Citations are short: `T&N7 p5` = Taylor & Nolen (2008) Ch. 7, PDF page 5. Source paths are at the bottom. `lesson-builder check` automates the mechanical MC rules (§2) and the `authentic-writer` word, dash, and exclamation-point rules; the rest needs a reader.

## 1. Alignment and validity

- Map every item to one learning target before writing it. The most common item flaw is a mismatch with the objective (T&N7 p20).
- Only test what was taught, at the depth it was taught (T&N1 p29-32).
- Score only the target skill. No points for neatness, spelling, or nice writing unless that is the target (T&N1 p33; Taylor22 p123).
- If a student could show the same skill in a different format (oral, drawing, table), don't make the item depend on one format (T&N1 p33).
- Tell students the scoring criteria up front. "Students should not have to learn teacher expectations during the assessment event" (T&N1 p35-36).
- Test the standard, not the strategy used to teach it (a tape diagram, a specific organizer) (Taylor22 p159-160).
- Cognitive demand comes from what the item asks students to do, not surface features. A word problem, a diagram, or "explain your process" does not make an item high-level (Smith & Stein p2). Include some "procedures with connections" items (link representations: diagram + symbols + situation) and, where it fits, a "doing mathematics" item with no predictable path (Levels of Cognitive Demand table).

## 2. Multiple choice (T&N Ch. 7 rules)

- The stem poses a complete problem. A student should know what is being asked before reading the options (T&N7 p3).
- Options are parallel in length, grammar, and complexity. The key must not be the longest or most detailed option (T&N7 p4).
- No grammatical clues (a/an, singular/plural) and no repeating a stem word in the key (T&N7 p4-5).
- No "all of the above", "none of the above", "A and B", or similar (T&N7 p6).
- No overlapping or partially correct distractors. Exactly one defensible answer (T&N7 p6).
- No trick items (T&N7 p5).
- Avoid NOT/EXCEPT stems. They add cognitive load that is not the target (T&N7 p7). If one is truly needed, capitalize the negative (house rule).
- Each distractor comes from a real student error or misconception: a sign slip, a reversed operation, confusing independent with disjoint, an off-by-one loop. Write each distractor's error in the key with `distractors: {A: '...'}` (T&N7 p7; Taylor22 p123). Good source: Chief Reader reports and student work.
- Vary the position of the correct answer across the test. Never use a fixed pattern. Check the key for clues across items (T&N7 p5). `lesson-builder check` warns when one letter keys more than half the MC items or the same key appears three times in a row, and errors when a key letter is outside the choices or `key:` disagrees with the `[X]` in `answer:`. Across forms, `lesson-builder integrity` flags matching key positions; compare against the version table in `requirements.md`.
- House default is four options (A)-(D). Three good options beat four with a throwaway; if a fourth distractor would be silly, say so and use three (T&N7 p4). `check` warns on fewer than 3 or more than 4 (true/false and select-all exempt), errors on empty, duplicate, and "all/none of the above" or "A and B" choices, and warns when one choice is over twice the median length.
- MC items that need heavy reading or inference add bias. Prefer short constructed response for reasoning (Taylor22 p123-124, 135).

## 3. Short answer and constructed response (T&N Ch. 7 and 8)

- Ask for exactly what you want ("Give two reasons...", "Show your work and state the final angle measure") (T&N7 p9).
- Put expectations in a short "Be sure to include:" list instead of stacking many sub-questions in one prompt (T&N8 p3-4).
- Write the model answer before finalizing the prompt. Revise the prompt if the model answer shows it is unclear (T&N8 p5).
- For each item, the key lists: acceptable answers, where each point comes from, and a note to give credit for any valid strategy (T&N7 p9-12).
- Accept everyday wording that shows correct reasoning ("they never cross" for parallel lines) (Moschkovich p14 appendix; Woodbury).

## 4. Rubrics

- 3 to 6 levels. Each level is distinct and specific, so a student can see what moves them up (T&N5 p44).
- Criteria describe the knowledge shown, not task completion and not a restatement of the directions (T&N5 p36, 44).
- No vague level words like "partially correct", "somewhat accurate", or "developing understanding" without saying what is present or missing (Taylor22 p132, 135).
- Score math communication or writing on a separate line from content, so English does not lower the content score (T&N8 p6; Moschkovich p24-25).
- AP Statistics FRQs: use the College Board E / P / I format, with the specific evidence for E and P written out per part.
- Reuse the same rubric across similar tasks (T&N8 p6).

## 5. Directions

- Write directions to the student ("You will...", "Show..."), with familiar words and a low reading level (T&N5 p29-30).
- If several options are plausible, say "Choose the best answer" (T&N1 p35).
- State any fixed conventions (units, rounding, "leave answers in terms of pi").

## 6. Language access for multilingual learners

Goal: lower the language load without lowering the math. Same mathematical aim, same "explain" demand (Roberts p462-463).

- Use active voice and short declarative sentences. Split long sentences and relative clauses into two (Roberts Table 1 p464; T&N7 p20-22).
- Replace conditionals ("If a student were to...") with direct statements where the math allows. Name the subject instead of "they" or "it". Break up long noun phrases (Roberts Table 1 p464).
- Replace low-frequency non-math words ("perusing" -> "looking at") (Roberts p462).
- Keep the math terms. Removing them is "linguistic enabling" (Zwiers p102). Instead, flag dual-meaning words and make the math meaning clear from the diagram or context: similar, plane, product, square, odd, table, round, mean, range, independent, origin, scale (Zwiers Table 4.10 p104; Roberts p462; Taylor22 p159).
- Watch direction verbs and question forms: interpret, estimate, construct, justify, "which ratio represents" (Zwiers Table 4.11 p105).
- No idioms, figurative language, or culture-specific knowledge (batting average, Thanksgiving dinner, "over the hill") (T&N1 p22-33; T&N7 p20-22).
- Set the scene in one or two plain sentences, then put the data in a table or labeled diagram (Roberts p463).
- Pair key text with a visual: labeled diagram, table, or graph. Do not assume students see in a diagram what you see; label what matters (Roberts p460; Lotan p73-74).
- Leave white space. Math text packs many ideas per sentence, so break items into parts (Zwiers p102).
- Let students answer with drawings, tables, or labeled diagrams where the target allows (Moschkovich p24-25; T&N8 p14).
- Sentence starters, if used: optional, matched to the language function (explain, compare, justify), and they start the sentence without giving the claim. "I know the triangles are congruent because ___" is fine. A frame that contains the reasoning is not (Rodriguez-Mojica p399-401). Use them on 1-3 explain items, not every item. On the page, each blank is a labeled box under its own problem, naming the figure it refers to, with the answer in the key (`handout-release-check` §1).
- One version for everyone. Accommodations (extra time, dictionary, reading aloud, oral response) keep the same target. Changing the target is a modification and needs IEP or specialist input (T&N5 p70-71; Guskey & Jung p2; Stigler & Hiebert p4).

## 7. Contexts and fairness

- Use contexts students know or can picture: school, neighborhood, food, transit, games, sports stats, part-time jobs. Let students see themselves and their communities (Taylor22 p123; Aguirre p5-9).
- Check for stereotypes, negative portrayals, and assumed family or money situations (T&N5 p67-68).
- Every number in a context needs a believable purpose. Cut contrived setups (Taylor22 p158-161).
- Don't add a real-life story only to make an item cute. If the context does no mathematical work, cut it (Stigler & Hiebert p2-3).

## 8. Answer key notes for scoring MLL work

Add a short "Scoring notes" block to the key when the class has MLLs (SCASS EL review guide):

- Score understanding, not grammar, spelling, or full sentences. Read the response twice before judging (p2).
- Accept phonetic spelling, home-language words, and cognates when the math is right (p2-8).
- Accept other notation: decimal comma (3,5 = 3.5), other division layouts and algorithms, day/month dates (p12-14).
- Don't penalize answers that build up to the claim at the end (p9-11).
- Don't penalize Black Language or other non-dominant varieties when the math is correct (Baker-Bell).

## 9. Grading and retakes (SBG)

- Label each section with its learning target so scores can be reported by target (Scriffiny p72).
- Report achievement separately from effort and behavior (Guskey & Jung p2).
- Retakes and alternate versions measure the same target with no penalty for needing more time (Scriffiny p73-74).

## Sources

Base: `C:\Users\zubair\Documents\canvas-extractor\export\`

| Short | Path under base |
|---|---|
| T&N1, T&N5, T&N7, T&N8 | `edtep-573-a-au-26_-assessment-in-secondary-education\google_drive\readings\Taylor___Nolen_Chp{1,5,7,8}.pdf` (scanned, needs OCR) |
| Taylor22 | `edtep-573-...\google_drive\readings\Taylor_2022.pdf` (Ch. 6, book pages) |
| SCASS EL review | `edtep-573-...\google_drive\readings\reading___how_should_I_review_my_EL_student_responses.pdf` (scanned) |
| Guskey & Jung, Scriffiny | `edtep-573-...\google_drive\readings\SBG_resource_*` |
| Chesbro | `edtep-573-...\google_drive\readings\Chesbro_2010.pdf` (post-test error analysis) |
| Smith & Stein | `edtep-582-a-sp-26_-teaching-mathematics-in-the-secondary-school-i\files\smith-&-stein-(1998).pdf` (scanned) |
| Levels table | `edtep-583-a-au-26_-teaching-mathematics-in-the-secondary-school-ii\google_drive\Spring_2026\Week_7\Levels_of_Cognitive_Demand_Table.pdf` |
| Aguirre, Lotan, Stigler & Hiebert | `edtep-582-...\files\` |
| Woodbury | `edtep-583-...\files\woodbury(2000)_teachingtwrdsbigideasalg.pdf` |
| Moschkovich, Roberts, Zwiers, Rodriguez-Mojica, Baker-Bell | `edtep-575-a&b-su-26_-language-&-literacy-(l&l)\files\` |

Scanned PDFs have no text layer. To re-read one, OCR it into `_temp/`:
`uv run --no-project --with rapidocr_onnxruntime --with pymupdf python <ocr script>`

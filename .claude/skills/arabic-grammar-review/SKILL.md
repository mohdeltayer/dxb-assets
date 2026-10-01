---
name: arabic-grammar-review
description: >-
  The grammar-review stage for Digital Lounge Arabic posts (X text, Instagram
  captions, card and Reel lines). Reviews finished Arabic for required
  grammar, morphology, spelling and punctuation corrections, keeps optional
  style and uncertain cases apart, and returns a fixed four-part report. Use
  after the Arabic has been written with arabic-games-film-editor and before
  the DeepL back-check and queuing. Not for writing or rewriting copy.
---

# Arabic grammar review (Digital Lounge)

This stage checks Arabic that is already written. It corrects what is wrong
and leaves everything else exactly as written. It does not write, translate
or restyle.

## Sources, and how far to trust them

| Source | Used for | Path |
|---|---|---|
| House glossary | names, house terms, voice, text direction. Overrides everything below | `arabic/house-glossary.md` |
| perfect-arabic (alialsaudi, MIT, commit 78fdade) | نحو and صرف: agreement, case, النواسخ, numbers, ما لا ينصرف, verb mood | `.claude/skills/perfect-arabic/` (SKILL.md and `references/01` to `04`) |
| arabic-writing (ahmeddabak, MIT, commit 7001831) | إملاء and ترقيم: hamza, ة/ه, ى/ي, tanwin, Arabic punctuation and spacing | `.claude/skills/arabic-writing/references/orthography.md` (and `conventions.md` for numbers, dates, prices) |
| arabic-writing smell test | optional style only, never a required edit | `.claude/skills/arabic-writing/SKILL.md`, `translationese.md`, `collocations.md` |

All three outside sources are community-maintained summaries, not
authorities. perfect-arabic summarises النحو الوافي; it is not the book, and
nothing here has read the book. Several lines in its references are wrong or
self-contradictory: read `references/known-issues.md` before relying on any
line it lists, and never cite a listed line as support.

Do not claim to have read a file that was not opened in this run. Before the
review, open the house glossary, perfect-arabic `SKILL.md`, and
`orthography.md`; open a perfect-arabic reference file when the text raises
its topic.

## Policy

- Contemporary MSA for games news. Correct only against that standard.
- The smallest correction that fixes the error. A correct sentence comes back
  unchanged, and "no required edits" is a normal result.
- Preserve meaning, attribution («حسب …», «قال …», «يقول موقع …»),
  uncertainty and hedges («قد», «نحو», «تقريبًا», «حسب تقارير»), game, series,
  platform, company and people names, technical terms, numbers, units, dates,
  prices, links, line breaks and formatting. An edit that changes any of these
  is not a grammar edit; raise it as an uncertain case instead.
- A valid alternative is not an error. Where the references allow two forms
  (for example تذكير or تأنيث the verb before a broken plural or a separated
  subject, رفع or نصب after إلا in a negative complete exception), the writer's
  form stands. If one form is preferred (أرجح), that goes under optional
  suggestions, not required edits.
- Do not add full diacritics, and do not treat their normal absence as an
  error. The house writes the accusative tanwin alif (رسميًا، جدًا) and a
  meaning-distinctive shadda only. The alif is spelling; the mark on it is a
  diacritic, so «جدا» for «جدًا» is never a required edit (at most a
  consistency note under optional suggestions; the 1 Oct test run got this
  wrong). A missing alif («جدً») is a spelling error. A missing case ending cannot be "wrong" in
  undiacritized text; judge case only where it shows in the letters (sound
  plurals, duals, الأسماء الستة, الأفعال الخمسة, the accusative alif, ممنوع من
  الصرف with tanwin written in).
- Numbers written in Western digits (the house style) carry no visible
  gender; do not flag numeral polarity on a digit. Check it on numbers written
  as words (ثلاث فعاليات، سبع سنوات).
- Direct quotations: flag a problem inside «…» or a quoted line, do not
  rewrite it. It goes in `required_edits` with `"quotation": true` and is left
  out of `corrected_text`.
- House rules are required edits of their own kind (`house_rule`): game and
  series names take feminine agreement (تصدر Football Manager 27); company and
  people names as Arabic then the Latin in brackets at first mention, Arabic
  alone after; the glossary's spellings (نينتيندو، بانداي نامكو، تيك-تو);
  Western digits; no em dash; every paragraph and line starts with an Arabic
  word; no first person; X posts carry no hashtags, Instagram captions end on
  `#ألعاب #أخبار_الألعاب` plus two tags.
- Do not invent rules, book quotations, مسألة numbers or source references.
  When the opened files say nothing on a point, say so and give the general
  principle without a reference.
- When context is insufficient (who is speaking, what a pronoun refers to,
  whether a word is a name), flag it as uncertain. Do not guess.
- Dialect is not broken فصحى. Captions are MSA by house rule; if a dialect
  form appears, raise it as uncertain, not as a grammar error.

## The pass

1. Read the glossary rows that touch the text.
2. نحو and صرف, in perfect-arabic's order (its Step 2): sentence skeleton,
   agreement (verb and subject, adjective and noun, non-human plurals take
   feminine singular, pronouns and relatives against their antecedents),
   visible case, النواسخ, objects, الحال, التمييز, الاستثناء, prepositions,
   derivatives, numbers in words, verb mood after نواصب and جوازم.
3. إملاء and ترقيم, in orthography.md's order: hamza, ة/ه and ى/ي, tanwin,
   spacing, Arabic punctuation glyphs.
4. House rules.
5. Style, kept apart: the smell test and collocations. These never become
   required edits, never enter `corrected_text`, and are offered only when
   the gain is clear. The house's own approved wording (glossary) is never a
   style finding.
6. Build `corrected_text` by applying the required edits only (not quotation
   flags, not suggestions, not uncertain cases), then reread it to confirm
   nothing else moved.

## Output

Return one JSON object per text, in this shape. Explanations in English are
fine (Mohammad reads the report); Arabic terms and quoted wording stay in
Arabic.

```json
{
  "corrected_text": "the full text with required edits applied, otherwise identical",
  "required_edits": [
    {
      "original": "exact wording from the text",
      "proposed": "replacement",
      "class": "grammar_morphology | spelling_punctuation | house_rule",
      "category": "short label, for example تأنيث الفعل، العدد، همزة القطع، glossary spelling",
      "explanation": "one or two lines",
      "quotation": false,
      "reference": "file and section actually opened, for example perfect-arabic references/02-verbs-objects.md §الفاعل; omit when none was consulted"
    }
  ],
  "optional_style_suggestions": [
    {"original": "...", "suggestion": "...", "reason": "..."}
  ],
  "uncertain_cases": [
    {"text": "...", "issue": "...", "why_uncertain": "...", "options": ["..."]}
  ]
}
```

Empty arrays are fine and expected. `reference` names the file and section
that were opened in this run, never النحو الوافي itself and never a line
listed in `known-issues.md`.

## After the review

The report goes to Mohammad with the drafts. Required edits are applied
before he sees the pair; suggestions and uncertain cases are shown for his
call. Then the DeepL back-check confirms the meaning survived. This stage
never queues anything: queuing still needs his times and his "go".

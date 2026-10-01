# Arabic grammar-review stage: test run, 1 Oct 2026

The `arabic-grammar-review` stage was run blind over 39 Digital Lounge texts.
Four fresh reviewers took 10 texts each (the last took 9). Each one loaded the
skill, the glossary and the references from scratch. None of them knew which
texts had planted errors.

## The sample

- **22 approved posts, unchanged**, as published from `dxb-queue/queue/*-ar`.
  - Includes today's six (PUBG Black Budget, Gears, Octopath, Castlevania,
    Resident Evil, and the Football Manager 27 Instagram caption with hashtags).
  - These are the "correct sentences" check: any required edit on them counts
    as an unnecessary correction.
- **4 approved posts carrying slips found while choosing the sample**:
  - DW3 specs: نينتندو for the house نينتيندو.
  - Game Pass October: the first line opens on "Gears of War".
  - Pokémon leak: إيفريثينغ for the glossary's إفريثينغ.
  - Sonic in Fortnite, from 24 Sep, before the naming rules: names in Arabic
    that should be English, no Latin at first mention, and a first line that
    opens on a digit.
- **12 approved posts with planted problems**:
  - 13 required errors:
    - numeral polarity, three times
    - a dual subject and a dual object
    - a sound plural after a preposition
    - agreement with a singular subject
    - hamza
    - ة/ه
    - على/علي
    - a Latin comma
    - masculine agreement with a game name
    - a spelling slip inside a «…» quotation
  - 4 traps that must not become required edits:
    - «وأعلن الشركة», a valid masculine verb before a مؤنث مجازي
    - «مناطق جُدد», a valid broken-plural adjective
    - «حوالي»
    - «جدا» without the tanwin mark

## Results

**Missed errors: none.**
- All 13 planted errors were caught with the right fix and class.
- The quotation error («وبدى») was flagged with `quotation: true` and kept out
  of `corrected_text`.
- All four approved slips were caught as `house_rule` edits.
  - The exception: the Sonic post's digit-first line went to uncertain, not
    required. That is defensible, because the line's first letter is Arabic.

**Unnecessary corrections: one.**
- «جدا» became «جدًا» as a required spelling edit. Adding the diacritic is
  exactly what the policy forbids.
- SKILL.md now says the tanwin mark is a diacritic and «جدا» is never a
  required edit.
- A rerun of that text and three others with a fresh reviewer gave only the
  real fix (سيلتزمون → سيلتزم).
- The other three traps held:
  - «وأعلن الشركة» went to optional (feminine preferred, as the reference has
    it), twice.
  - «جُدد» drew nothing.
  - «حوالي» went to optional.
- The 22 unchanged approved posts drew no required edits.

**Changes to meaning: none.**
- Every `corrected_text` differs from its input only at the listed edits
  (checked by word diff).
- The one reorder, «تتصدر Gears of War: E-Day قائمة», keeps the sentence and
  its agreement.
- No attribution, hedge, name, number or date moved.

## Useful things it raised that were not errors

These went to optional suggestions or uncertain cases, which is where they
belong:

- **WARDOGS:** «بلغت مبيعات WARDOGS 3 ملايين» can read as a sequel called
  WARDOGS 3.
- **Ocarina of Time:** «لحنًا تعلّمه Link أمام ميكروفون الجهاز» can attach the
  microphone to Link's learning.
- **Pokémon leak:** the post says «من اللعبة» after naming two games.
- **PHYSINT:** «الـ400 مليون قد تكون» may want يكون.
- **Helldivers:** «بعد انسحاب جيسون موموا» may attach to the wrong clause.
- **DW3:** «عند توصيل الجهاز بالتلفاز» could use the glossary's وضع التلفاز.

## Limits of this test

- The planted errors are the kinds the tester thought of. These were not
  tested:
  - إن or كان with a sound plural
  - الأفعال الخمسة after a jussive or subjunctive particle
  - ممنوع من الصرف with written tanwin
  - long-distance agreement across a relative clause
- The reviewers are the same kind of model that writes the copy, so shared
  blind spots would not show here.
- 39 texts is a small sample. A second run on a new batch with fresh planted
  errors would tell more.
- Results: `scratchpad/grammar/` in the 1 Oct session (not kept in git).

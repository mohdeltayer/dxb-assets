# Test cases for the grammar-review stage

Rerun a sample of these, blind and with fresh reviewers, after any
change to SKILL.md, the glossary rules it enforces, or the vendored
references. The full first run is in
`notes/arabic-review-test-2026-10-01.md`.

## Must be corrected (required edits)

| Text | Expected | Class |
|---|---|---|
| بعد مرور سبعة سنوات | سبع سنوات | grammar_morphology (العدد) |
| ويضم العرض ستة شخصيات | ست شخصيات | grammar_morphology (العدد) |
| وتضم الإضافة أربعة سيارات | أربع سيارات | grammar_morphology (العدد) |
| وقال دركمان إن الاستوديو سيلتزمون الصمت | سيلتزم | grammar_morphology (agreement) |
| وأعلنت الشركتين أيضًا | الشركتان | grammar_morphology (dual subject) |
| خفّضت سعراهما | سعريهما | grammar_morphology (dual object) |
| ويمكن لمالكو نسخة | لمالكي | grammar_morphology (sound plural after a preposition) |
| صدرت اضافة Road Trip | إضافة | spelling_punctuation (hamza) |
| مع حزمه ترقية | حزمة | spelling_punctuation (ة/ه) |
| وهي متوفرة علي Steam | على | spelling_punctuation (ى/ي) |
| حسب شركة إس إن كيه (SNK), على أن | Arabic comma ، | spelling_punctuation |
| يصل Suri: The Seventh Note | تصل | house_rule (game names feminine) |
| لموقع نينتندو إفريثينغ | نينتيندو إفريثينغ | house_rule (glossary) |
| Gears of War: E-Day تتصدر قائمة … (first line of a post) | open on an Arabic word | house_rule (text direction) |

## Must be flagged, not changed

| Text | Expected |
|---|---|
| «عملية مضنية، وبدى أحيانًا بلا نهاية» | Required edit with `quotation: true`, left out of `corrected_text` |

## Must not become required edits

| Text | Why | Acceptable output |
|---|---|---|
| في مرحلة مبكرة جدا | Missing tanwin mark is an absent diacritic | Nothing, or an optional consistency note |
| وأعلن الشركة أيضًا | Masculine verb before a مؤنث مجازي is allowed | Optional (feminine preferred) |
| ومناطق جُدد | Broken-plural adjective for a non-human plural is valid | Nothing, or optional |
| منذ حوالي عامين | Wide news use | Optional at most |

## Meaning must not move (2 Oct 2026, all came back unchanged)

| Text | Trap |
|---|---|
| تستهدف نسخة Switch 2 من Monster Hunter Wilds معدل 30 إطارًا في الثانية، حسب ما قاله المنتج … | A target must not become «تعمل بثبات» |
| ويقول تحليل ديجيتال فاوندري (Digital Foundry) إن اللعبة تعمل داخليًا بدقة 720p قبل رفعها إلى 1440p … | An analysis must not become the company's spec |
| قد تصل Starfield إلى PS5 … حسب تقرير لموقع ويندوز سنترال (Windows Central) لم تؤكده بيثيسدا (Bethesda) بعد. | The hedge and the attribution stay |

## Approved posts that must come back unchanged

Pick any recent approved Digital Lounge posts from `dxb-queue/queue/*-ar`
and `*-ig`. On 1 Oct, 22 of them drew no required edits.

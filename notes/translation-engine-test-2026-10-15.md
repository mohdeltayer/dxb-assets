# Translation engine test, 15 Oct 2026

Mohammad asked whether another tool translates Arabic better than DeepL. The
published rankings are too thin for Arabic to settle it (see the chat of 15 Oct),
so this test uses our own material: 20 English sentences, each built on a term
he has corrected or approved in `arabic/house-glossary.md`. An engine passes a
sentence when its Arabic uses the approved term, fails when it uses the
rejected one, and misses when it uses neither.

Files: `translation-test/set.json` (sentences, approved and rejected patterns),
`score.py` (re-run with `python3 score.py Name=outputs.json ...`), one outputs
file per engine. Five patterns were tightened to the glossary's own wording after
the first outputs came in (physical edition, years after launch, service ends,
countdown, out today); the scores below use the tightened set.

## Engines

- DeepL (connector, Free plan), English to Arabic, 15 Oct 00:55Z.
- Claude blind: a fresh subagent told not to open the glossary or any file,
  translating for a Gulf games news outlet, 15 Oct 01:00Z.
- Microsoft Translator dictionary lookup: pending an Azure Translator key
  (free tier, 2 million characters a month). Arabic is in its dictionary scope
  (checked on the live languages endpoint, 15 Oct).

## Result

| | pass | fail | miss |
|---|---|---|---|
| DeepL | 12 | 4 | 4 |
| Claude blind | 13 | 5 | 2 |

Both fail the same three house terms: expansion (both wrote التوسعتين, the
glossary says إضافة), physical edition (DeepL النسخة المطبوعة, Claude النسخة
الفيزيائية), and Nintendo's spelling (both wrote نينتندو). DeepL also wrote
"10 ساعات مع" and كلا التوسعتين (should be كلتا), and spelled نفاذ for نفاد.
Claude wrote "يصل التحديث اليوم" and "بعد 7 سنوات من إطلاق", two phrasings the
glossary rejects, but got نفاد, التلفاز for docked and متجر Steam في الإمارات right.

## What it means

Neither engine knows the house terms; each misses about a quarter of them in a
different place. That is the case for keeping the glossary as the authority and
running both checks: the writer (Claude, with the glossary loaded) and DeepL both
ways, with every disagreement looked up rather than either engine trusted. Re-run
this set with Microsoft's dictionary lookup once the key exists, and add every new
correction he makes as a sentence here.

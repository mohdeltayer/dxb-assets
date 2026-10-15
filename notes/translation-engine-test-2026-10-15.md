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

## Round 2: whole stories (Mohammad, 15 Oct: "Add the full story in DeepL and not sentence by sentence")

The same 20 terms were placed in six short news stories in our usual shape
(`stories.json`) and each story was sent whole, to DeepL and to a blind Claude.

| | pass | fail | miss |
|---|---|---|---|
| DeepL, sentences | 12 | 4 | 4 |
| DeepL, stories | 8 | 5 | 7 |
| Claude blind, sentences | 13 | 5 | 2 |
| Claude blind, stories | 12 | 5 | 3 |

Read by hand, the gap narrows: most of DeepL's new misses in story mode are
acceptable wordings (وضع اللعب المحمول، بعد قضاء 10 ساعات في اللعب، يتوفر التحديث
اليوم، لم يتبق سوى 23 يومًا), so about 13 of 20 are usable against 14 in sentence mode.

What context fixed in DeepL: silent revision came back as تعديلاً خفيًّا (our term), and
"10 hours with" no longer became مع. What it broke: docked became وضع التوصيل بالقاعدة
(the literal the glossary already names), hands-on became تجربة لعب, Rainbow Six
Mobile "ستتوقف عن العمل" (the glossary wants تنتهي خدمة), and the whole-story runs
added errors the sentence runs did not have: Ubisoft spelled أوبيسبوت, and Nintendo
Switch 2 written in Arabic letters against the house rule. The real gain is flow:
the story reads as one connected news piece (وتأتي، لذا فإن، وفي الوقت نفسه).
Claude's two scores were similar; in both modes it wrote يصل التحديث اليوم and
ستتوقف عن العمل, which the scorer missed in story mode (counted here by hand).

Method from 15 Oct: the forward pass sends the whole story to DeepL (his
instruction; it shows how the post reads as one piece), and the short alternative
phrasings stay for stock phrases and retail terms only.

## Replay: the Ocarina foil cover post under the new method (15 Oct)

The English of the published caption, X post and Reel text went to DeepL whole.
All three came back with حتى نفاذ الكمية (to be spelled نفاد) where we published
ما دام المخزون متوفرًا and ما دام في المخزون, so the method would have caught it.
DeepL rendered "textured foil cover" as غلاف معدني مزخرف (decorated metallic), and
the blind Claude run had غلاف معدني لامع; we published غلاف فويل بارز الملمس. معدني is
the plainer Arabic for foil, but مزخرف shifts "textured" to "decorated", so the
candidate is غلاف معدني بارز الملمس, raised with Mohammad, not adopted. Nothing else
would change: DeepL's الطلبات المسبقة مفتوحة، النسخة المباعة في المتاجر and من الصفر say
what ours say, and its نينتندو spelling, IGN without the Arabic bracket and سيتم إطلاق
would not be taken.

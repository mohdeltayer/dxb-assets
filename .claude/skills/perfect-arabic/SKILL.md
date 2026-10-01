---
name: perfect-arabic
description: Check Arabic (فصحى) text for grammar (نحو) and morphology (صرف) errors against كتاب النحو الوافي by عباس حسن, and answer questions about specific Arabic grammar rules. Use when the user pastes Arabic text and asks to check, proofread, parse or correct it (دقّق، صحّح، راجع، أعرب، قوّم), asks whether a construction is valid (هل يصح أن نقول…؟), or asks for the ruling on a topic (الفاعل، الحال، التمييز، الاستثناء، النواسخ، العدد، النسب، ما لا ينصرف، إعراب المضارع، النداء، التصريف). Do not use for translation, Arabizi transliteration, stylistic rewriting, بلاغة, تجويد, or for correcting dialect (عامية) as though it were فصحى.
---

# Perfect Arabic — العربية السليمة

Arabic grammar checking grounded in **كتاب النحو الوافي** by **عباس حسن** (٤ مجلدات، ١٧٧ مسألة).

The four files in `references/` are the only authority for this skill. They are a condensed extraction of the book, not the book. Where they are silent, say so — do not fill the gap with a plausible-sounding rule and attribute it to النحو الوافي.

## Scope

**In scope**

- **نحو** — sentence skeleton, agreement, case, mood, النواسخ, المفاعيل, الحال, التمييز, الاستثناء, التوابع, إعراب المضارع, النداء.
- **صرف** — أبنية المصادر والمشتقات, العدد, النسب, التصغير, جمع التكسير, ما لا ينصرف, الإعلال والإبدال.

**Mentioned, but labelled separately**

- **إملاء** — همزة الوصل والقطع، التاء المربوطة والمفتوحة، الألف المقصورة والممدودة. Tag as «ملاحظة إملائية». It is not a grammar error.
- **أسلوب** — only when a construction is grammatically sound but genuinely weak, and only as a note. Never rewrite the user's prose.

**Out of scope** — translation, Arabizi conversion, تجويد, بلاغة as a subject, and treating regional dialect as broken فصحى.

## Step 1 — Classify the request

| What the user sent | What to do |
|---|---|
| Arabic text with a request to check, correct, or parse | Full checking pass (Step 2) |
| A question about one rule | Answer from the relevant reference file, cite the باب |
| Arabic text with no instruction | Ask once: «هل تريد فحص النص كاملاً أم السؤال عن قاعدة بعينها؟» |
| Clearly عامية | Do not flag dialect forms as errors. Ask: «النص أقرب إلى العامية. أتريد تحويله إلى الفصحى، أم مراجعة ما فيه من فصحى فقط؟» |
| Out of scope | Say so in one line and stop |

## Step 2 — The checking pass

Run in this order. Load a reference file only when the text actually raises that topic.

1. **هيكل الجملة** — اسمية or فعلية? Identify مبتدأ/خبر or فعل/فاعل. → `references/01-foundations.md`
2. **المطابقة** — verb↔subject gender (تأنيث الفعل) → `references/02-verbs-objects.md` §الفاعل; نعت↔منعوت in gender, number, definiteness and case → `references/03-derivatives-dependents.md` §التوابع; demonstratives, relatives and pronouns against their antecedents.
3. **الإعراب** — the correct حركة for each position → `references/01-foundations.md` §الإعراب والبناء; الممنوع من الصرف takes فتحة, not كسرة, when indefinite and unannexed → `references/04-morphology-special.md` §ما لا ينصرف; الأسماء الستة، المثنى، جمع المذكر السالم، الأفعال الخمسة take letters, not حركات.
4. **النواسخ** — with كان، إن، ظن، لا النافية للجنس، أفعال المقاربة, check the اسم/خبر pattern → `references/01-foundations.md` §النواسخ.
5. **المفاعيل وما يلحق بها** — مطلق، به، لأجله، معه، فيه، الحال، التمييز، الاستثناء → `references/02-verbs-objects.md`.
6. **حروف الجر** — is this the حرف the meaning calls for → `references/02-verbs-objects.md` §حروف الجر.
7. **المشتقات** — اسم الفاعل والمفعول، الصفة المشبهة، صيغ المبالغة، التعجب، أفعل التفضيل: وزن and agreement → `references/03-derivatives-dependents.md`.
8. **الصرف الخاص** — العدد، النسب، التصغير، جمع التكسير، الإعلال والإبدال → `references/04-morphology-special.md`.
9. **إعراب المضارع** — after النواصب or الجوازم → `references/04-morphology-special.md` §إعراب المضارع.
10. **النداء وما يلحق به** — الترخيم، الاستغاثة، الندبة، الاختصاص → `references/04-morphology-special.md` §النداء.

## Step 3 — The report

Reply in Arabic unless the user wrote in English, in which case reply in English and leave the Arabic terms and examples in Arabic. Use this structure:

```
## مراجعة النحو الوافي

### الأخطاء المكتشفة

1. **[العبارة الخاطئة]** ← **[الصواب]**
   - القاعدة: [الباب، والمسألة إن عُرفت]
   - التعليل: [سطر أو سطران]
   - درجة التصحيح: [واجب / أرجح / جائز مع ملاحظة]

### ملاحظات

- [إملاء أو أسلوب أو مسألة خلافية — عند وجودها فقط]

### النص بعد التصحيح

[النص كاملاً بعد تطبيق التصويبات الواجبة]
```

When the text is sound, reply: **«النص سليم نحوياً وفق أحكام النحو الوافي.»** Add a «ملاحظات» block only if there is something real to say. Do not manufacture observations to fill the section.

### درجة التصحيح

| الدرجة | متى |
|---|---|
| **واجب** | مخالفة صريحة لحكم في الكتاب — مثل رفع اسم إنّ، أو ترك تأنيث الفعل مع المؤنث الحقيقي الظاهر المتّصل |
| **أرجح** | الوجهان جائزان في الكتاب وأحدهما مقدَّم |
| **جائز مع ملاحظة** | صيغة المستخدم صحيحة وإن قلّ استعمالها — تُذكر خبراً لا خطأً |

## Step 4 — Citation

Cite the باب by name always, and the مسألة number only when the reference file gives it:

- «المسألة السادسة — الإعراب والبناء» (المجلد الأول)
- «المسألة ٦٥ — الفاعل» (المجلد الثاني)
- «المسألة ١٦٣ — العدد» (المجلد الرابع)

**Never invent a مسألة number.** If the rule is absent from `references/`, say: «لم أجد نصّاً صريحاً على هذه المسألة في المرجع المتاح؛ وما يلي هو القاعدة العامة.» — then give the general principle without attaching a citation to it.

## Invariants

1. **Do not invent rules.** An unsupported ruling attributed to the book is worse than no ruling.
2. **Do not correct عامية as if it were فصحى.** Ask which register the user wants reviewed.
3. **Keep the categories apart.** نحو، صرف، إملاء، أسلوب each get their own label.
4. **Respect the permitted alternatives.** النحو الوافي records more than one valid position in several باب — الاستثناء، التنازع، الحال الجامدة، العدد المركّب among them. A valid minority form is «جائز وإن كان الأرجح…»، never an error.
5. **Preserve the author's voice.** Correct what is wrong. Leave everything else exactly as written, including word choice, register and rhythm.
6. **Ask at most one clarifying question,** and only when the answer changes the review. If the request is clear, answer it.

## Reference files

| File | Contents |
|---|---|
| `references/01-foundations.md` | الكلام وأقسامه، الإعراب والبناء، الأسماء الستة، المثنى، الجموع السالمة، الأفعال الخمسة، النكرة والمعرفة، المبتدأ والخبر، كان وأخواتها، إن وأخواتها، ظن وأخواتها، لا النافية للجنس، الأحرف المشبهة بليس، أفعال المقاربة والشروع والرجاء |
| `references/02-verbs-objects.md` | الفاعل، نائب الفاعل، التنازع والاشتغال، التعدي واللزوم، أعلم وأرى، المفعول المطلق، المفعول لأجله، الظرف، المفعول معه، الاستثناء، الحال، التمييز، حروف الجر |
| `references/03-derivatives-dependents.md` | الإضافة، أبنية المصادر، اسم الفاعل والمفعول، الصفة المشبهة، اسم الآلة والمرة والهيئة والزمان والمكان، صيغ المبالغة، التعجب، أفعل التفضيل، التوابع الأربعة |
| `references/04-morphology-special.md` | النداء وأنواع المنادى، الترخيم، الاختصاص، الاستغاثة، الندبة، ما لا ينصرف، إعراب المضارع، العدد، جمع التكسير، النسب، التصغير، الإعلال والإبدال |

## Source

> **كتاب النحو الوافي** — ٤ مجلدات، ١٧٧ مسألة
> تأليف: **عباس حسن** (١٨٩٩–١٩٧٩)، عضو مجمع اللغة العربية بالقاهرة
> [shamela.ws/book/10641](https://shamela.ws/book/10641)

This skill is a derivative reference tool. The grammatical authority is the book's; any error of summary or transcription is the skill's own, and the book settles it.

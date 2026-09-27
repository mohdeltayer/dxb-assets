# Translationese & AI-Arabic tells; English→Arabic pitfalls

This is the most important reference for naturalness. "Translationese" (الترجمة الركيكة) is
Arabic that is grammatical yet obviously transferred from English. Below: first the giveaways
of machine/AI output with fixes, then the recurring English→Arabic grammar pitfalls.

Table of contents:
1. The fastest AI/MT tells (with fixes)
2. Passive voice
3. "There is / there are"
4. Possessives
5. Relative clauses
6. The verb "to be" (no present copula)
7. Tenses with no Arabic equivalent
8. Gender-neutral language
9. Pluralization traps
10. Anglicized sentence structure

---

## 1. The fastest AI/MT tells (with fixes)

| Tell | Machine version | Natural Arabic |
|---|---|---|
| **من قبل + passive** | تمت مراجعة الخطط من قبل اللجنة | راجعت اللجنةُ الخططَ (active) / رُوجِعت الخطط |
| **قام/قم بـ + verbal noun** | قام بزيارة المصنع | زار المصنعَ |
| same, imperative | قم بإدخال كلمة المرور | أدخِل كلمة المرور / إدخال كلمة المرور (label) |
| **detached الخاص بك** | الحساب الخاص بك | حسابك |
| **all-purpose يتم / تمّ** | يتم استخدام هذه الأداة | تُستخدَم هذه الأداة |
| **catch-all حيث** | الشركة حيث تنتج… | الشركة التي تنتج… / إذ تنتج… |
| **copular calque** | الهدف من البحث هو الوصول إلى… | يهدف البحث إلى الوصول إلى… |
| **يلعب دورًا** ("play a role") | يلعب دورًا مهمًا | يؤدّي دورًا مهمًا / يضطلع بدور / يسهم |
| **doubled كلما** | كلما تعطي، كلما تأخذ | كلما أعطيتَ، أخذت |
| **spurious preposition** | تحسين من مهارات الطلاب | تحسين مهارات الطلاب |
| **wrong preposition** | تؤثر على المستوى | تؤثر في المستوى (formal MSA) |

**Connector over-explicitation.** Translated Arabic stacks heavy connectors — بالإضافة إلى
ذلك، علاوة على ذلك، من ناحية أخرى، وبالتالي — at a density native prose never uses, compounded
by the AI "rule of three" (أولًا، ثانيًا، ثالثًا). Native Arabic mostly links clauses with و /
فـ / ثم and uses heavier connectors only where the logic genuinely calls for one. Thin them out.

**Agreement that drifts over distance.** Surface-fluent output defaults to masculine/unmarked
when the subject is feminine, plural, or far from its verb: ✗ المبادرات التي أطلقتها الوزارة…
يهدفُ → ✓ …تهدفُ. Re-check agreement across the whole sentence, not just locally.

**Register collapse / leakage.** Flattening everything to stiff MSA, or leaking colloquial
words into formal text, is itself a tell. Keep one consistent register (see register-and-style.md).

**Context-blind lexical choice.** Undiacritized homographs get the wrong sense (الفريق = "team"
vs the military rank "lieutenant general"; حمّام "bathroom" vs حمام "pigeon"). Resolve from
context; add a disambiguating ḥaraka only if truly needed.

## 2. Passive voice

Arabic prefers the **active** voice when the doer is known; the internal passive
(المبني للمجهول) is used precisely *because* the agent is suppressed, so an English-style "by"
phrase (من قبل / بواسطة / من طرف) is un-Arabic.

- ✗ كُتب هذا الكتاب من قبل مؤلف مشهور → ✓ كتب هذا الكتابَ مؤلفٌ مشهور (active).
- Legitimate internal passive when the agent is genuinely unknown: ارتُكبت أخطاء؛ سُرق المتجر.
- تمّ + verbal noun (تمّ توقيع الاتفاق) is an acceptable alternative but is overused as a
  crutch; prefer a real verb: وقّع الطرفان الاتفاق / وُقِّع الاتفاق.

## 3. "There is / there are"

Options, in rising formality: **هناك** (basic), **يوجد/توجد** (must agree — توجد for feminine
or non-human plural), **ثمّة** (literary). The most idiomatic fix is often a **fronted predicate
(الخبر المقدّم)** with no existential word at all:

- "There are many stars in the sky" → في السماءِ نجومٌ كثيرةٌ.
- Don't reach for هناك in every sentence — it reads as translated.

## 4. Possessives

Arabic has no apostrophe-s. Use **iḍāfa** or a **pronoun suffix**, never the heavy calque الخاص بـ:

- "the student's book" → كتابُ الطالبِ.
- "your car" → سيارتُك.
- "the company's policy" → سياسةُ الشركةِ (not السياسة الخاصة بالشركة).
- Remember: the first noun of an iḍāfa takes no ال, no tanwīn, no suffix (see grammar.md §5).

## 5. Relative clauses

The relative pronoun (الذي / التي / الذين / اللواتي / اللذان …) is used **only with a definite
antecedent**. With an **indefinite** antecedent it is obligatorily **omitted**:

- "a man who works in the factory" → رجلٌ يعمل في المصنع (no الذي).
- "the man who traveled to Egypt" → الرجلُ الذي سافر إلى مصر (definite → required).

Agree the pronoun in gender/number (dual اللذان/اللتان, fem. pl. اللواتي/اللاتي). A non-subject
antecedent needs a **resumptive pronoun (العائد)**: الكتابُ الذي قرأتُه ("the book that I read
**it**").

## 6. The verb "to be" (no present copula)

There is no present-tense "is/are." A present statement is a **nominal sentence**:

- "The house is big" → البيتُ كبيرٌ.
- Past "was/were" uses **كان** (+ accusative predicate): كان البيتُ كبيرًا.
- Inserting a present-tense copula (e.g. ✗ البيت هو كبير as a default) is a classic error;
  هو/هي as a copula is reserved for emphatic or equational sentences (محمدٌ هو المسؤول).

## 7. Tenses with no Arabic equivalent

Arabic is **aspectual** (completed الماضي vs incomplete المضارع), not tense-rich. Translate by
sense:

- Present perfect → **قد + past**: قد كتب الرسالة.
- Past perfect → **كان (قد) + past**: كان قد كتب الرسالة.
- Future perfect → **سيكون قد + past**: سيكون قد كتب الرسالة.
- Progressive → simple **المضارع**, optionally ما زال / لا يزال for "still": لا يزال يكتب.
- Don't mechanically match the English tense form.

## 8. Gender-neutral language

Arabic marks gender on verbs, adjectives, pronouns, and imperatives, so English neutral
"you / they / click here" has no direct equivalent. To avoid committing to a gender, **nominalize**:

- "Enter your password" → يُرجى إدخالُ كلمةِ المرور (gender-free) rather than أدخِل (m.) /
  أدخِلي (f.).
- Where a generic is unavoidable, the default convention is the generic masculine — but be
  consistent within a document.

## 9. Pluralization traps

1. **The dual (المثنى):** "two books" is كتابانِ / كتابينِ, never a plural.
2. **Broken plurals** are irregular and must be known: كتاب → كتب؛ رجل → رجال؛ مدينة → مدن.
3. **Non-human plurals take feminine-singular agreement** (the #1 rule): صدرت هذه المقالاتُ وهي
   ممتازةٌ. English-trained output wrongly makes these agree as plurals.

## 10. Anglicized sentence structure

- Forcing SVO/nominal order where VSO is natural (front the verb): ✗ الحكومةُ أعلنت → ✓ أعلنت
  الحكومةُ.
- Stacking English-style subordinate clauses. **Fix:** break into shorter clauses coordinated
  with و / فـ, and render an English infinitive/gerund subject as a **maṣdar**: "Achieving a
  just peace will bring prosperity" → إنّ تحقيقَ سلامٍ عادلٍ سيجلب الازدهار.
- Translate the **unit of meaning**, then read the Arabic aloud: if it only makes sense once you
  recall the English, it is translationese — rewrite it.

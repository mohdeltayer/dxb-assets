# Known issues in the outside references

Found on reading the files in full on 1 Oct 2026. Line numbers are for the
vendored copies (perfect-arabic commit 78fdade, arabic-writing commit
7001831). Do not cite these lines as support, and do not apply what they say
where it conflicts with the note.

## perfect-arabic

| File and line | What it says | The problem |
|---|---|---|
| `references/01-foundations.md` l.100 | «كلا الرجلين» رفع بالألف عندما تُضاف إلى ضمير … | The rule is muddled: كلا and كلتا are inflected like the dual (ألف/ياء) only when added to a pronoun, and with fixed alif (مقدّرة) when added to a noun. The line as written reads backwards. |
| `references/01-foundations.md` l.151 | «لم يذهبوا» بإثبات النون ⇐ الصواب «لم يذهبوا» | Both sides are printed the same; the wrong form («لم يذهبون») is missing. The rule meant (الأفعال الخمسة drop the nun when مجزوم) is right. |
| `references/02-verbs-objects.md` l.16 | مؤنث حقيقي example: «طلعت الشمس» | الشمس is مؤنث مجازي (l.18 itself uses it that way). The rule for the حقيقي row is right; the example is wrong. |
| `references/02-verbs-objects.md` l.401 to 402 | «أذهب للمدرسة» and «بسبب المرض» listed under خطأ شائع | Both are accepted in contemporary MSA; at most a style preference. Never a required edit. |
| `references/03-derivatives-dependents.md` l.183 to 184 | موعد given under both مَفعَل and مَفعِل | معتل الفاء (وعد) takes مَفعِل (مَوعِد); the مَفعَل line is wrong to include it. |
| `references/04-morphology-special.md` l.130 | موسى listed with ألف التأنيث المقصورة | موسى's alif is not an alif of تأنيث; the name is ممنوع من الصرف for العلمية والعجمة. |
| `references/04-morphology-special.md` l.245 | «إن اجتهدتَ تنجح بدون الفاء في الاسمية وهي جائزة …» | Self-contradictory: تنجح is a verb, not a nominal clause. The second half (a nominal جواب needs الفاء) is right. |
| `references/04-morphology-special.md` l.278 | «عشرين كتاباً» (إعراب المعطوف على المثنى بالياء) | The reason is wrong: العقود are ملحق بجمع المذكر السالم, hence the ياء in نصب and جر. The correction itself is right. |
| `references/04-morphology-special.md` l.363 | «الشافعيّ ⇐ الشافعيّ» | The example shows no change and does not illustrate the rule stated. |
| `references/04-morphology-special.md` l.391 | «تُقلب الألف واواً للثلاثي» for موسى | موسى is four letters, not three; the usual reason for موسويّ is the رابعة alif of a name, which may take واو. |

## arabic-writing

Prescriptive preferences that the file states as rules. In this stage they
are style suggestions at most, never required edits:

| Where | What it says | Treatment |
|---|---|---|
| `SKILL.md` checklist item 10, `collocations.md` | أثّر في, not أثّر على, in formal MSA | أثّر على is in wide news use; style note only. |
| `orthography.md` §9 | حوالي means "surrounding", use نحو | حوالي for an approximate number is in wide news use; style note only. The house already prefers نحو where it fits. |
| `orthography.md` §6 | tanwin mark on the letter before the alif | Both placements are attested; the house uses رسميًا. Do not flag the other placement as an error. |
